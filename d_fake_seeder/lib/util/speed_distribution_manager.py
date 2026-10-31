"""
Speed Distribution Manager for DFakeSeeder.

Coordinates the application of speed distribution algorithms across all torrents.
Upload and download are handled by the same code, parameterised by direction.
"""

import time
from dataclasses import dataclass
from secrets import SystemRandom
from typing import Any

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.gi_base import GLib
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.speed_distribution import (
    create_distributor,
    format_debug_output,
)

LOG = "SpeedDistributionManager"
# Randomised spread of simulated bandwidth (OS entropy; no seeding needed)
_RANDOM = SystemRandom()
DIRECTIONS = ("upload", "download")
HEADLINES = {"upload": "🔄 REDISTRIBUTING UPLOAD SPEEDS", "download": "⬇️  REDISTRIBUTING DOWNLOAD SPEEDS"}

# Errors a redistribution pass may raise from settings, model data or the distributor;
# logged so a bad pass never breaks the tick loop.
REDISTRIBUTION_ERRORS = (AttributeError, TypeError, ValueError, KeyError, ArithmeticError)
DISCONNECT_ERRORS = (AttributeError, TypeError, ValueError, RuntimeError)


@dataclass
class BandwidthPlan:
    """Bandwidth to distribute in one pass."""

    base: float
    total: float
    low: float = 0.0
    high: float = 0.0


def _set_speed(torrent: Any, direction: str, speed: float) -> None:
    setattr(torrent, f"{direction}_speed", int(speed))


class SpeedDistributionManager:
    """
    Manages speed distribution across all torrents.

    Handles periodic redistribution based on user-configured settings and algorithms.
    """

    def __init__(self, model: Any) -> None:
        """
        Initialize the Speed Distribution Manager.

        Args:
            model: The application model containing torrents
        """
        self.model = model
        self.settings = AppSettings.get_instance()

        # Last redistribution time and custom interval timer per direction
        self.last_redistribution = dict.fromkeys(DIRECTIONS, 0.0)
        self.timer_ids: dict[str, int | None] = dict.fromkeys(DIRECTIONS)

        self._settings_handler_id = self.settings.connect("attribute-changed", self.on_settings_changed)
        logger.info("SpeedDistributionManager initialized", LOG)

    # Backwards-compatible per-direction views of the state above
    @property
    def last_upload_redistribution(self) -> float:
        """Time of the last upload redistribution."""
        return self.last_redistribution["upload"]

    @property
    def last_download_redistribution(self) -> float:
        """Time of the last download redistribution."""
        return self.last_redistribution["download"]

    @property
    def upload_timer_id(self) -> int | None:
        """GLib source id of the custom-interval upload timer."""
        return self.timer_ids["upload"]

    @property
    def download_timer_id(self) -> int | None:
        """GLib source id of the custom-interval download timer."""
        return self.timer_ids["download"]

    def _setting(self, direction: str, name: str) -> Any:
        """``settings.<direction>_distribution_<name>``."""
        return getattr(self.settings, f"{direction}_distribution_{name}")

    def on_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle settings changes."""
        if "distribution" in key and "redistribution_mode" in key:
            logger.debug(f"Redistribution mode changed: {key} = {value}", LOG)
            self._restart_timers()
        elif "distribution" in key and "custom_interval" in key:
            logger.debug(f"Custom interval changed: {key} = {value}", LOG)
            self._restart_timers()

    def _cancel_timers(self) -> None:
        for direction, timer_id in self.timer_ids.items():
            if timer_id:
                GLib.source_remove(timer_id)
                self.timer_ids[direction] = None

    def _restart_timers(self) -> None:
        """Restart custom interval timers if needed."""
        self._cancel_timers()
        for direction in DIRECTIONS:
            if self._setting(direction, "redistribution_mode") != "custom":
                continue
            interval_minutes = self._setting(direction, "custom_interval_minutes")
            self.timer_ids[direction] = GLib.timeout_add_seconds(
                interval_minutes * 60, self._redistribute_timer, direction
            )
            logger.debug(f"Started {direction} redistribution timer ({interval_minutes} minutes)", LOG)

    def _redistribute_timer(self, direction: str) -> bool:
        """Timer callback: redistribute one direction and keep the timer running."""
        self.redistribute_speeds(direction)
        return True

    def check_redistribution(self, event_type: str = "tick") -> None:
        """
        Check if redistribution should occur based on event type.

        Args:
            event_type: Type of event ("tick", "announce")
        """
        for direction in DIRECTIONS:
            mode = self._setting(direction, "redistribution_mode")
            if mode in ("tick", "announce") and mode == event_type:
                self.redistribute_speeds(direction)

    def redistribute_upload_speeds(self) -> None:
        """Redistribute upload speeds across all torrents."""
        self.redistribute_speeds("upload")

    def redistribute_download_speeds(self) -> None:
        """Redistribute download speeds across all torrents."""
        self.redistribute_speeds("download")

    def redistribute_speeds(self, direction: str) -> None:
        """Redistribute ``direction`` ("upload"/"download") speeds across all active torrents."""
        try:
            self._redistribute(direction)
        except REDISTRIBUTION_ERRORS as e:
            logger.error(f"Error redistributing {direction} speeds: {e}", LOG, exc_info=True)

    def _plan_bandwidth(self, direction: str, torrents: list[Any], percentage: float) -> BandwidthPlan:
        """Randomised total within the spread around the configured limit, else the current speed sum."""
        base = self._get_total_bandwidth(direction)
        title = direction.capitalize()
        if base > 0:
            # Example: 6000 KB/s with 50% spread = 3000 to 9000 KB/s
            low = base * (1.0 - percentage / 100.0)
            high = base * (1.0 + percentage / 100.0)
            plan = BandwidthPlan(base, _RANDOM.uniform(low, high), low, high)
            logger.debug(
                f"{title} bandwidth randomized: {base:.1f} KB/s ±{percentage}% "
                f"= {low:.1f} to {high:.1f} KB/s, using {plan.total:.1f} KB/s",
                LOG,
            )
            return plan
        total = sum(getattr(t, f"{direction}_speed") for t in torrents)
        logger.debug(f"No {direction} limit defined, using sum of current speeds: {total:.1f} KB/s", LOG)
        return BandwidthPlan(base, total)

    def _redistribute(self, direction: str) -> None:
        algorithm = self._setting(direction, "algorithm")
        if algorithm == "off":
            return
        percentage = self._setting(direction, "spread_percentage")
        torrents = self._get_active_torrents()
        if not torrents:
            return
        plan = self._plan_bandwidth(direction, torrents, percentage)
        if plan.total <= 0:
            logger.debug(f"No {direction} bandwidth to distribute", LOG)
            return

        self._log_header(direction, algorithm, percentage, plan, len(torrents))
        stopped_min = self._setting(direction, "stopped_min_percentage")
        stopped_max = self._setting(direction, "stopped_max_percentage")
        stopped_percentage = _RANDOM.uniform(stopped_min, stopped_max)
        logger.debug(
            f"{direction.capitalize()} stopped torrents: {stopped_percentage:.1f}% "
            f"(range: {stopped_min}-{stopped_max}%)",
            LOG,
        )
        distributor = create_distributor(algorithm, percentage, stopped_percentage)
        distribution = distributor.distribute(plan.total, [t.file_path for t in torrents])

        speed_values = {}
        for torrent in torrents:
            new_speed = distribution.get(torrent.file_path, 0.0)
            _set_speed(torrent, direction, new_speed)
            speed_values[torrent.file_path] = new_speed
            category = distribution.get(f"{torrent.file_path}_category")
            self._log_torrent(torrent.name, new_speed, str(category) if category else None)
            logger.debug(
                format_debug_output(
                    torrent.name, distributor.get_algorithm_name(), new_speed, str(category) if category else None
                ),
                "SpeedDist",
            )
        self._log_summary(list(speed_values.values()))

        self.last_redistribution[direction] = time.time()
        # Store current state in settings (saved via debounced save)
        self.settings.set(f"speed_distribution.{direction}.current_speed", plan.total)
        self.settings.set(f"speed_distribution.{direction}.current_values", speed_values)
        logger.debug(
            f"Redistributed {direction} speeds: {algorithm} algorithm, "
            f"{len(torrents)} torrents, {plan.total:.1f} KB/s total",
            LOG,
        )

    @staticmethod
    def _log_header(direction: str, algorithm: str, percentage: float, plan: BandwidthPlan, count: int) -> None:
        logger.debug("=" * 80, LOG)
        logger.debug(HEADLINES[direction], LOG)
        logger.debug("=" * 80, LOG)
        logger.debug(f"Algorithm: {algorithm.upper()}", LOG)
        logger.debug(f"Spread: {percentage}%", LOG)
        if plan.base > 0:
            logger.debug(f"Base Bandwidth: {plan.base:.1f} KB/s", LOG)
            logger.debug(f"Randomized Total: {plan.total:.1f} KB/s ({plan.low:.1f} - {plan.high:.1f})", LOG)
        else:
            logger.debug(f"Total Bandwidth: {plan.total:.1f} KB/s (sum of current speeds)", LOG)
        logger.debug(f"Torrents: {count}", LOG)
        logger.debug("-" * 80, LOG)

    @staticmethod
    def _log_torrent(name: str, speed: float, category: str | None) -> None:
        torrent_name = name[:50] + "..." if len(name) > 50 else name
        category_str = f" [{category}]" if category else ""
        logger.debug(f"  📁 {torrent_name:53} → {speed:7.2f} KB/s{category_str}", LOG)

    @staticmethod
    def _log_summary(speeds: list[float]) -> None:
        if speeds:
            logger.debug("-" * 80, LOG)
            logger.debug("📊 Distribution Stats:", LOG)
            logger.debug(f"   Min: {min(speeds):.2f} KB/s", LOG)
            logger.debug(f"   Max: {max(speeds):.2f} KB/s", LOG)
            logger.debug(f"   Avg: {sum(speeds) / len(speeds):.2f} KB/s", LOG)
            logger.debug(f"   Total: {sum(speeds):.2f} KB/s", LOG)
            stopped_count = sum(1 for s in speeds if s == 0)
            if stopped_count > 0:
                logger.debug(f"   Stopped: {stopped_count}/{len(speeds)} torrents", LOG)
        logger.debug("=" * 80, LOG)

    def _get_active_torrents(self) -> list[Any]:
        """Get list of active torrents."""
        if not self.model:
            return []
        return [t for t in self.model.get_torrents() if getattr(t, "active", True)]

    def _get_total_bandwidth(self, direction: str) -> float:
        """Total bandwidth for a direction: alternative limit, else global limit, else legacy setting."""
        if self.settings.get("speed.enable_alternative_speeds", False):
            return float(self.settings.get(f"speed.alt_{direction}_limit_kbps", 0))
        limit = self.settings.get(f"speed.{direction}_limit_kbps", 0)
        if limit > 0:
            return float(limit)
        return float(getattr(self.settings, f"total_{direction}_speed", 0))

    def _get_total_upload_bandwidth(self) -> float:
        """Get total upload bandwidth from global settings."""
        return self._get_total_bandwidth("upload")

    def _get_total_download_bandwidth(self) -> float:
        """Get total download bandwidth from global settings."""
        return self._get_total_bandwidth("download")

    def start(self) -> None:
        """Start the speed distribution manager."""
        logger.info("SpeedDistributionManager started", LOG)
        self._restart_timers()

    def stop(self) -> None:
        """Stop the speed distribution manager."""
        if self._settings_handler_id:
            try:
                self.settings.disconnect(self._settings_handler_id)
            except DISCONNECT_ERRORS as e:
                logger.debug(f"Settings handler already disconnected: {e}", LOG)
            self._settings_handler_id = None
        self._cancel_timers()
        logger.info("SpeedDistributionManager stopped", LOG)
