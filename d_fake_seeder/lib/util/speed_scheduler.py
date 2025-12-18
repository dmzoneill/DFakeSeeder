"""
Speed Scheduler - Automatic alternative speed switching based on time.

Implements time-based scheduling for alternative speed limits,
automatically enabling/disabling alternative speeds during configured time windows.
"""

from datetime import datetime
from typing import Optional

from gi.repository import GLib

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger


class SpeedScheduler:
    """
    Manages time-based alternative speed switching.

    Checks every 60 seconds if the current time falls within the configured
    schedule window and automatically enables/disables alternative speeds.
    """

    def __init__(self) -> None:
        """Initialize the speed scheduler."""
        self.settings = AppSettings.get_instance()
        self.timer_id: Optional[int] = None
        self.last_state: Optional[bool] = None
        self._running = False

        logger.trace(
            "SpeedScheduler initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def start(self) -> None:
        """Start the scheduler check timer (every 60 seconds)."""
        if self._running:
            return

        self._running = True
        # Check every 60 seconds
        self.timer_id = GLib.timeout_add_seconds(60, self._check_schedule)
        # Perform an immediate check on startup
        self._check_schedule()

        logger.info(
            "SpeedScheduler started",
            extra={"class_name": self.__class__.__name__},
        )

    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
        if self.timer_id:
            GLib.source_remove(self.timer_id)
            self.timer_id = None

        logger.info(
            "SpeedScheduler stopped",
            extra={"class_name": self.__class__.__name__},
        )

    def _check_schedule(self) -> bool:
        """
        Check if we should be in alternative speed mode.

        Returns:
            True to keep the timer running, False to stop it.
        """
        if not self._running:
            return False

        # Check if scheduler is enabled
        if not self.settings.get("scheduler.enabled", False):
            # Scheduler disabled - don't change anything, just keep timer running
            return True

        now = datetime.now()
        day_names = [
            "monday",
            "tuesday",
            "wednesday",
            "thursday",
            "friday",
            "saturday",
            "sunday",
        ]
        current_day = day_names[now.weekday()]

        # Check if today is enabled in the schedule
        days = self.settings.get("scheduler.days", {})
        if not days.get(current_day, True):
            # Today is not a scheduled day - disable alternative speeds
            self._set_alt_speeds(False)
            return True

        # Get the time window configuration
        start_hour = self.settings.get("scheduler.start_hour", 22)
        start_minute = self.settings.get("scheduler.start_minute", 0)
        end_hour = self.settings.get("scheduler.end_hour", 6)
        end_minute = self.settings.get("scheduler.end_minute", 0)

        # Check if current time is within the scheduled window
        in_window = self._is_in_time_window(now, start_hour, start_minute, end_hour, end_minute)
        self._set_alt_speeds(in_window)

        return True  # Keep timer running

    def _is_in_time_window(
        self,
        now: datetime,
        start_h: int,
        start_m: int,
        end_h: int,
        end_m: int,
    ) -> bool:
        """
        Check if current time is within the scheduled window.

        Handles time windows that cross midnight (e.g., 22:00 to 06:00).

        Args:
            now: Current datetime
            start_h: Start hour (0-23)
            start_m: Start minute (0-59)
            end_h: End hour (0-23)
            end_m: End minute (0-59)

        Returns:
            True if current time is within the window.
        """
        current_minutes = now.hour * 60 + now.minute
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        if start_minutes <= end_minutes:
            # Normal case: e.g., 09:00 to 17:00
            return start_minutes <= current_minutes < end_minutes
        else:
            # Crosses midnight: e.g., 22:00 to 06:00
            return current_minutes >= start_minutes or current_minutes < end_minutes

    def _set_alt_speeds(self, enabled: bool) -> None:
        """
        Enable or disable alternative speeds.

        Only changes the setting if the state is different from the last known state.

        Args:
            enabled: True to enable alternative speeds, False to disable.
        """
        if self.last_state != enabled:
            self.settings.set("speed.enable_alternative_speeds", enabled)
            self.last_state = enabled
            status = "enabled" if enabled else "disabled"
            logger.info(
                f"Scheduler: Alternative speeds {status}",
                extra={"class_name": self.__class__.__name__},
            )

    def force_check(self) -> None:
        """Force an immediate schedule check."""
        self._check_schedule()

    def get_status(self) -> dict:
        """
        Get the current scheduler status.

        Returns:
            Dictionary with scheduler status information.
        """
        enabled = self.settings.get("scheduler.enabled", False)
        return {
            "running": self._running,
            "enabled": enabled,
            "last_state": self.last_state,
            "start_time": f"{self.settings.get('scheduler.start_hour', 22):02d}:"
            f"{self.settings.get('scheduler.start_minute', 0):02d}",
            "end_time": f"{self.settings.get('scheduler.end_hour', 6):02d}:"
            f"{self.settings.get('scheduler.end_minute', 0):02d}",
        }


# Convenience function to get a singleton instance
_instance: Optional[SpeedScheduler] = None


def get_speed_scheduler() -> SpeedScheduler:
    """Get or create the SpeedScheduler singleton instance."""
    global _instance
    if _instance is None:
        _instance = SpeedScheduler()
    return _instance
