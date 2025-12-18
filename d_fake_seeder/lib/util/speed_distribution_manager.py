"""
Speed Distribution Manager for DFakeSeeder.

Coordinates the application of speed distribution algorithms across all torrents.
"""

import random
import time
from typing import Any, List

from gi.repository import GLib

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.speed_distribution import create_distributor, format_debug_output


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

        # Track last redistribution time
        self.last_upload_redistribution = 0.0
        self.last_download_redistribution = 0.0

        # Track custom interval timers
        self.upload_timer_id = None
        self.download_timer_id = None

        # Subscribe to settings changes
        self.settings.connect("attribute-changed", self.on_settings_changed)

        logger.info("SpeedDistributionManager initialized", "SpeedDistributionManager")

    def on_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle settings changes."""
        # Restart timers if redistribution mode or interval changed
        if "distribution" in key and "redistribution_mode" in key:
            logger.debug(f"Redistribution mode changed: {key} = {value}", "SpeedDistributionManager")
            self._restart_timers()
        elif "distribution" in key and "custom_interval" in key:
            logger.debug(f"Custom interval changed: {key} = {value}", "SpeedDistributionManager")
            self._restart_timers()

    def _restart_timers(self) -> Any:
        """Restart custom interval timers if needed."""
        # Cancel existing timers
        if self.upload_timer_id:
            GLib.source_remove(self.upload_timer_id)
            self.upload_timer_id = None

        if self.download_timer_id:
            GLib.source_remove(self.download_timer_id)
            self.download_timer_id = None

        # Start new timers if mode is custom
        if self.settings.upload_distribution_redistribution_mode == "custom":
            interval_minutes = self.settings.upload_distribution_custom_interval_minutes
            interval_seconds = interval_minutes * 60
            self.upload_timer_id = GLib.timeout_add_seconds(
                interval_seconds,
                self._redistribute_upload_speeds_timer,
            )
            logger.debug(
                f"Started upload redistribution timer ({interval_minutes} minutes)", "SpeedDistributionManager"
            )

        if self.settings.download_distribution_redistribution_mode == "custom":
            interval_minutes = self.settings.download_distribution_custom_interval_minutes
            interval_seconds = interval_minutes * 60
            self.download_timer_id = GLib.timeout_add_seconds(
                interval_seconds,
                self._redistribute_download_speeds_timer,
            )
            logger.debug(
                f"Started download redistribution timer ({interval_minutes} minutes)", "SpeedDistributionManager"
            )

    def _redistribute_upload_speeds_timer(self) -> bool:
        """Timer callback for upload speed redistribution."""
        self.redistribute_upload_speeds()
        return True  # Keep timer running

    def _redistribute_download_speeds_timer(self) -> bool:
        """Timer callback for download speed redistribution."""
        self.redistribute_download_speeds()
        return True  # Keep timer running

    def check_redistribution(self, event_type: str = "tick") -> Any:
        """
        Check if redistribution should occur based on event type.

        Args:
            event_type: Type of event ("tick", "announce")
        """
        # Upload redistribution
        upload_mode = self.settings.upload_distribution_redistribution_mode
        if upload_mode == "tick" and event_type == "tick":
            self.redistribute_upload_speeds()
        elif upload_mode == "announce" and event_type == "announce":
            self.redistribute_upload_speeds()

        # Download redistribution
        download_mode = self.settings.download_distribution_redistribution_mode
        if download_mode == "tick" and event_type == "tick":
            self.redistribute_download_speeds()
        elif download_mode == "announce" and event_type == "announce":
            self.redistribute_download_speeds()

    def redistribute_upload_speeds(self) -> Any:
        """Redistribute upload speeds across all torrents."""
        try:
            algorithm = self.settings.upload_distribution_algorithm
            if algorithm == "off":
                return  # Distribution disabled

            percentage = self.settings.upload_distribution_spread_percentage

            # Get active torrents
            torrents = self._get_active_torrents()
            if not torrents:
                return

            # Calculate total bandwidth
            base_bandwidth = self._get_total_upload_bandwidth()

            if base_bandwidth > 0:
                # Apply spread percentage to create a range
                # Example: 6000 KB/s with 50% spread = 3000 to 9000 KB/s
                min_bandwidth = base_bandwidth * (1.0 - percentage / 100.0)
                max_bandwidth = base_bandwidth * (1.0 + percentage / 100.0)
                total_bandwidth = random.uniform(min_bandwidth, max_bandwidth)
                logger.debug(
                    f"Upload bandwidth randomized: {base_bandwidth:.1f} KB/s ±{percentage}% "
                    f"= {min_bandwidth:.1f} to {max_bandwidth:.1f} KB/s, using {total_bandwidth:.1f} KB/s",
                    "SpeedDistributionManager",
                )
            else:
                # No defined limit, use sum of current torrent speeds
                total_bandwidth = sum(t.upload_speed for t in torrents)
                logger.debug(
                    f"No upload limit defined, using sum of current speeds: {total_bandwidth:.1f} KB/s",
                    "SpeedDistributionManager",
                )

            if total_bandwidth <= 0:
                logger.debug("No upload bandwidth to distribute", "SpeedDistributionManager")
                return

            logger.debug("=" * 80, "SpeedDistributionManager")
            logger.debug("🔄 REDISTRIBUTING UPLOAD SPEEDS", "SpeedDistributionManager")
            logger.debug("=" * 80, "SpeedDistributionManager")
            logger.debug(f"Algorithm: {algorithm.upper()}", "SpeedDistributionManager")
            logger.debug(f"Spread: {percentage}%", "SpeedDistributionManager")
            if base_bandwidth > 0:
                logger.debug(f"Base Bandwidth: {base_bandwidth:.1f} KB/s", "SpeedDistributionManager")
                logger.debug(
                    f"Randomized Total: {total_bandwidth:.1f} KB/s ({min_bandwidth:.1f} - {max_bandwidth:.1f})",
                    "SpeedDistributionManager",
                )
            else:
                logger.debug(
                    f"Total Bandwidth: {total_bandwidth:.1f} KB/s (sum of current speeds)", "SpeedDistributionManager"
                )
            logger.debug(f"Torrents: {len(torrents)}", "SpeedDistributionManager")
            logger.debug("-" * 80, "SpeedDistributionManager")

            # Create distributor and get speed distribution
            # Randomize stopped percentage within configured range
            stopped_min = self.settings.upload_distribution_stopped_min_percentage
            stopped_max = self.settings.upload_distribution_stopped_max_percentage
            stopped_percentage = random.uniform(stopped_min, stopped_max)
            logger.debug(
                f"Upload stopped torrents: {stopped_percentage:.1f}% (range: {stopped_min}-{stopped_max}%)",
                "SpeedDistributionManager",
            )
            distributor = create_distributor(algorithm, percentage, stopped_percentage)
            torrent_ids = [t.file_path for t in torrents]
            speed_distribution = distributor.distribute(total_bandwidth, torrent_ids)

            # Apply speeds to torrents
            speeds_list = []
            speed_values = {}  # Track current speeds for transient storage
            for torrent in torrents:
                new_speed = speed_distribution.get(torrent.file_path, 0.0)

                # Update torrent upload speed
                torrent.upload_speed = int(new_speed)

                # Store speed value for transient state
                speed_values[torrent.file_path] = new_speed

                # Get category for display
                category = speed_distribution.get(f"{torrent.file_path}_category", None)

                # Log torrent info
                torrent_name = torrent.name[:50] + "..." if len(torrent.name) > 50 else torrent.name
                category_str = f" [{category}]" if category else ""
                logger.debug(
                    f"  📁 {torrent_name:53} → {new_speed:7.2f} KB/s{category_str}", "SpeedDistributionManager"
                )

                speeds_list.append(new_speed)

                # Debug output
                debug_msg = format_debug_output(
                    torrent.name,
                    distributor.get_algorithm_name(),
                    new_speed,
                    category,  # type: ignore[arg-type]
                )
                logger.debug(debug_msg, "SpeedDist")

            # Log summary
            if speeds_list:
                logger.debug("-" * 80, "SpeedDistributionManager")
                logger.debug("📊 Distribution Stats:", "SpeedDistributionManager")
                logger.debug(f"   Min: {min(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                logger.debug(f"   Max: {max(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                logger.debug(f"   Avg: {sum(speeds_list)/len(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                logger.debug(f"   Total: {sum(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                stopped_count = sum(1 for s in speeds_list if s == 0)
                if stopped_count > 0:
                    logger.debug(f"   Stopped: {stopped_count}/{len(speeds_list)} torrents", "SpeedDistributionManager")
            logger.debug("=" * 80, "SpeedDistributionManager")

            self.last_upload_redistribution = time.time()

            # Store current state in settings (will be saved via debounced save)
            self.settings.set("speed_distribution.upload.current_speed", total_bandwidth)
            self.settings.set("speed_distribution.upload.current_values", speed_values)

            logger.debug(
                f"Redistributed upload speeds: {algorithm} algorithm, "
                f"{len(torrents)} torrents, {total_bandwidth:.1f} KB/s total",
                "SpeedDistributionManager",
            )

        except Exception as e:
            logger.error(f"Error redistributing upload speeds: {e}", "SpeedDistributionManager", exc_info=True)

    def redistribute_download_speeds(self) -> Any:
        """Redistribute download speeds across all torrents."""
        try:
            algorithm = self.settings.download_distribution_algorithm
            if algorithm == "off":
                return  # Distribution disabled

            percentage = self.settings.download_distribution_spread_percentage

            # Get active torrents
            torrents = self._get_active_torrents()
            if not torrents:
                return

            # Calculate total bandwidth
            base_bandwidth = self._get_total_download_bandwidth()

            if base_bandwidth > 0:
                # Apply spread percentage to create a range
                # Example: 6000 KB/s with 50% spread = 3000 to 9000 KB/s
                min_bandwidth = base_bandwidth * (1.0 - percentage / 100.0)
                max_bandwidth = base_bandwidth * (1.0 + percentage / 100.0)
                total_bandwidth = random.uniform(min_bandwidth, max_bandwidth)
                logger.debug(
                    f"Download bandwidth randomized: {base_bandwidth:.1f} KB/s ±{percentage}% "
                    f"= {min_bandwidth:.1f} to {max_bandwidth:.1f} KB/s, using {total_bandwidth:.1f} KB/s",
                    "SpeedDistributionManager",
                )
            else:
                # No defined limit, use sum of current torrent speeds
                total_bandwidth = sum(t.download_speed for t in torrents)
                logger.debug(
                    f"No download limit defined, using sum of current speeds: {total_bandwidth:.1f} KB/s",
                    "SpeedDistributionManager",
                )

            if total_bandwidth <= 0:
                logger.debug("No download bandwidth to distribute", "SpeedDistributionManager")
                return

            logger.debug("=" * 80, "SpeedDistributionManager")
            logger.debug("⬇️  REDISTRIBUTING DOWNLOAD SPEEDS", "SpeedDistributionManager")
            logger.debug("=" * 80, "SpeedDistributionManager")
            logger.debug(f"Algorithm: {algorithm.upper()}", "SpeedDistributionManager")
            logger.debug(f"Spread: {percentage}%", "SpeedDistributionManager")
            if base_bandwidth > 0:
                logger.debug(f"Base Bandwidth: {base_bandwidth:.1f} KB/s", "SpeedDistributionManager")
                logger.debug(
                    f"Randomized Total: {total_bandwidth:.1f} KB/s ({min_bandwidth:.1f} - {max_bandwidth:.1f})",
                    "SpeedDistributionManager",
                )
            else:
                logger.debug(
                    f"Total Bandwidth: {total_bandwidth:.1f} KB/s (sum of current speeds)", "SpeedDistributionManager"
                )
            logger.debug(f"Torrents: {len(torrents)}", "SpeedDistributionManager")
            logger.debug("-" * 80, "SpeedDistributionManager")

            # Create distributor and get speed distribution
            # Randomize stopped percentage within configured range
            stopped_min = self.settings.download_distribution_stopped_min_percentage
            stopped_max = self.settings.download_distribution_stopped_max_percentage
            stopped_percentage = random.uniform(stopped_min, stopped_max)
            logger.debug(
                f"Download stopped torrents: {stopped_percentage:.1f}% (range: {stopped_min}-{stopped_max}%)",
                "SpeedDistributionManager",
            )
            distributor = create_distributor(algorithm, percentage, stopped_percentage)
            torrent_ids = [t.file_path for t in torrents]
            speed_distribution = distributor.distribute(total_bandwidth, torrent_ids)

            # Apply speeds to torrents
            speeds_list = []
            speed_values = {}  # Track current speeds for transient storage
            for torrent in torrents:
                new_speed = speed_distribution.get(torrent.file_path, 0.0)

                # Update torrent download speed
                torrent.download_speed = int(new_speed)

                # Store speed value for transient state
                speed_values[torrent.file_path] = new_speed

                # Get category for display
                category = speed_distribution.get(f"{torrent.file_path}_category", None)

                # Log torrent info
                torrent_name = torrent.name[:50] + "..." if len(torrent.name) > 50 else torrent.name
                category_str = f" [{category}]" if category else ""
                logger.debug(
                    f"  📁 {torrent_name:53} → {new_speed:7.2f} KB/s{category_str}", "SpeedDistributionManager"
                )

                speeds_list.append(new_speed)

                # Debug output
                debug_msg = format_debug_output(
                    torrent.name,
                    distributor.get_algorithm_name(),
                    new_speed,
                    category,  # type: ignore[arg-type]
                )
                logger.debug(debug_msg, "SpeedDist")

            # Log summary
            if speeds_list:
                logger.debug("-" * 80, "SpeedDistributionManager")
                logger.debug("📊 Distribution Stats:", "SpeedDistributionManager")
                logger.debug(f"   Min: {min(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                logger.debug(f"   Max: {max(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                logger.debug(f"   Avg: {sum(speeds_list)/len(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                logger.debug(f"   Total: {sum(speeds_list):.2f} KB/s", "SpeedDistributionManager")
                stopped_count = sum(1 for s in speeds_list if s == 0)
                if stopped_count > 0:
                    logger.debug(f"   Stopped: {stopped_count}/{len(speeds_list)} torrents", "SpeedDistributionManager")
            logger.debug("=" * 80, "SpeedDistributionManager")

            self.last_download_redistribution = time.time()

            # Store current state in settings (will be saved via debounced save)
            self.settings.set("speed_distribution.download.current_speed", total_bandwidth)
            self.settings.set("speed_distribution.download.current_values", speed_values)

            logger.debug(
                f"Redistributed download speeds: {algorithm} algorithm, "
                f"{len(torrents)} torrents, {total_bandwidth:.1f} KB/s total",
                "SpeedDistributionManager",
            )

        except Exception as e:
            logger.error(f"Error redistributing download speeds: {e}", "SpeedDistributionManager", exc_info=True)

    def _get_active_torrents(self) -> List:
        """Get list of active torrents."""
        if not self.model:
            return []

        torrents = self.model.get_torrents()
        # Filter to only active torrents
        return [t for t in torrents if getattr(t, "active", True)]

    def _get_total_upload_bandwidth(self) -> float:
        """Get total upload bandwidth from global settings."""
        # Check if alternative speeds are enabled
        alt_enabled = self.settings.get("speed.enable_alternative_speeds", False)
        if alt_enabled:
            return float(self.settings.get("speed.alt_upload_limit_kbps", 0))

        # Use global upload speed setting
        upload_limit = self.settings.get("speed.upload_limit_kbps", 0)
        if upload_limit > 0:
            return float(upload_limit)

        # Fallback to legacy settings
        return float(getattr(self.settings, "total_upload_speed", 0))

    def _get_total_download_bandwidth(self) -> float:
        """Get total download bandwidth from global settings."""
        # Check if alternative speeds are enabled
        alt_enabled = self.settings.get("speed.enable_alternative_speeds", False)
        if alt_enabled:
            return float(self.settings.get("speed.alt_download_limit_kbps", 0))

        # Use global download speed setting
        download_limit = self.settings.get("speed.download_limit_kbps", 0)
        if download_limit > 0:
            return float(download_limit)

        # Fallback to legacy settings
        return float(getattr(self.settings, "total_download_speed", 0))

    def start(self) -> Any:
        """Start the speed distribution manager."""
        logger.info("SpeedDistributionManager started", "SpeedDistributionManager")
        self._restart_timers()

    def stop(self) -> Any:
        """Stop the speed distribution manager."""
        # Cancel timers
        if self.upload_timer_id:
            GLib.source_remove(self.upload_timer_id)
            self.upload_timer_id = None

        if self.download_timer_id:
            GLib.source_remove(self.download_timer_id)
            self.download_timer_id = None

        logger.info("SpeedDistributionManager stopped", "SpeedDistributionManager")
