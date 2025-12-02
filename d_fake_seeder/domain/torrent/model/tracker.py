"""
Tracker Model

Enhanced GObject model for tracking live tracker information including
announce URLs, status, response data, statistics, and real-time updates.
Integrates with the seeding system to provide live tracker monitoring.
"""

# isort: skip_file

# fmt: off
import time
from typing import Any, Dict, Optional

import gi

gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class Tracker(GObject.Object):
    """Enhanced model for tracking live tracker data with real-time updates"""

    # Basic tracker info (static from torrent file)
    url = GObject.Property(type=str, default="")
    tier = GObject.Property(type=int, default=0)  # Tracker tier (0 = primary)

    # Dynamic status tracking
    status = GObject.Property(type=str, default="unknown")  # "working", "failed", "unknown", "announcing"
    enabled = GObject.Property(type=bool, default=True)  # Can be disabled by user

    # Announce timing
    last_announce = GObject.Property(type=float, default=0.0)
    last_scrape = GObject.Property(type=float, default=0.0)
    announce_interval = GObject.Property(type=int, default=1800)  # Default 30 minutes
    next_announce = GObject.Property(type=float, default=0.0)
    min_announce_interval = GObject.Property(type=int, default=60)  # Minimum interval

    # Peer statistics (from tracker responses)
    seeders = GObject.Property(type=int, default=0)
    leechers = GObject.Property(type=int, default=0)
    downloaded = GObject.Property(type=int, default=0)  # Completed downloads

    # Performance metrics
    last_response_time = GObject.Property(type=float, default=0.0)  # Response time in seconds
    average_response_time = GObject.Property(type=float, default=0.0)
    consecutive_failures = GObject.Property(type=int, default=0)
    total_announces = GObject.Property(type=int, default=0)
    successful_announces = GObject.Property(type=int, default=0)

    # Error information
    error_message = GObject.Property(type=str, default="")
    last_error_time = GObject.Property(type=float, default=0.0)

    # Extended tracker info (if available)
    tracker_name = GObject.Property(type=str, default="")  # Human-readable name
    warning_message = GObject.Property(type=str, default="")  # Non-fatal warnings

    def __init__(self, url: str = "", tier: int = 0, **kwargs):
        """
        Initialize tracker model

        Args:
            url: Tracker announce URL
            tier: Tracker tier (0 = primary, higher = backup)
            **kwargs: Additional GObject properties
        """
        super().__init__(**kwargs)
        self.set_property("url", url)
        self.set_property("tier", tier)

        # Initialize timing
        current_time = time.time()
        if self.get_property("last_announce") == 0.0:
            self.set_property("last_announce", current_time)

        # Performance tracking
        self._response_times = []  # Keep last 10 response times for averaging
        self._last_update_time = current_time

        logger.debug(
            f"Tracker model initialized: {url} (tier {tier})",
            extra={"class_name": self.__class__.__name__},
        )

    @property
    def time_since_last_announce(self) -> float:
        """Get time since last announce in seconds"""
        if self.get_property("last_announce") > 0:
            return time.time() - self.get_property("last_announce")
        return 0.0

    @property
    def time_until_next_announce(self) -> float:
        """Get time until next announce in seconds"""
        next_announce = self.get_property("next_announce")
        if next_announce > 0:
            remaining = next_announce - time.time()
            return max(0, remaining)
        return 0.0

    @property
    def success_rate(self) -> float:
        """Get announce success rate as percentage"""
        total = self.get_property("total_announces")
        if total == 0:
            return 0.0
        successful = self.get_property("successful_announces")
        return (successful / total) * 100.0

    @property
    def is_healthy(self) -> bool:
        """Check if tracker is considered healthy"""
        return (
            self.get_property("status") == "working"
            and self.get_property("consecutive_failures") < 3
            and self.get_property("enabled")
        )

    def update_announce_response(self, response_data: Dict[str, Any], response_time: float) -> None:
        """
        Update tracker with successful announce response

        Args:
            response_data: Dictionary containing tracker response data
            response_time: Time taken for the announce request in seconds
        """
        try:
            current_time = time.time()

            # Update basic status
            self.set_property("status", "working")
            self.set_property("last_announce", current_time)
            self.set_property("total_announces", self.get_property("total_announces") + 1)
            self.set_property("successful_announces", self.get_property("successful_announces") + 1)
            self.set_property("consecutive_failures", 0)
            self.set_property("error_message", "")

            # Update timing
            self.set_property("last_response_time", response_time)
            self._update_average_response_time(response_time)

            # Update intervals if provided
            if "interval" in response_data:
                self.set_property("announce_interval", response_data["interval"])
            if "min interval" in response_data:
                self.set_property("min_announce_interval", response_data["min interval"])

            # Calculate next announce time
            interval = self.get_property("announce_interval")
            self.set_property("next_announce", current_time + interval)

            # Update peer statistics
            if "complete" in response_data:
                self.set_property("seeders", response_data["complete"])
            if "incomplete" in response_data:
                self.set_property("leechers", response_data["incomplete"])
            if "downloaded" in response_data:
                self.set_property("downloaded", response_data["downloaded"])

            # Handle warnings
            if "warning message" in response_data:
                self.set_property("warning_message", response_data["warning message"])
            else:
                self.set_property("warning_message", "")

            # Extract tracker name if available
            if "tracker_name" in response_data:
                self.set_property("tracker_name", response_data["tracker_name"])

            logger.debug(
                f"Tracker {self.get_property('url')} updated successfully: "
                f"S:{self.get_property('seeders')} L:{self.get_property('leechers')} "
                f"RT:{response_time:.2f}s",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Error updating tracker announce response: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def update_announce_failure(self, error_message: str, response_time: Optional[float] = None) -> None:
        """
        Update tracker with failed announce attempt

        Args:
            error_message: Description of the failure
            response_time: Time taken for the failed request (if applicable)
        """
        try:
            current_time = time.time()

            # Update failure status
            self.set_property("status", "failed")
            self.set_property("last_error_time", current_time)
            self.set_property("error_message", error_message)
            self.set_property("total_announces", self.get_property("total_announces") + 1)
            self.set_property("consecutive_failures", self.get_property("consecutive_failures") + 1)

            # Update timing if we have response time
            if response_time is not None:
                self.set_property("last_response_time", response_time)
                self._update_average_response_time(response_time)

            # Exponential backoff for next announce
            consecutive = self.get_property("consecutive_failures")
            base_interval = self.get_property("announce_interval")
            backoff_interval = min(base_interval * (2 ** min(consecutive - 1, 5)), 3600)  # Max 1 hour
            self.set_property("next_announce", current_time + backoff_interval)

            # Log at DEBUG for first 2 attempts, WARNING for persistent failures
            if consecutive <= 2:
                logger.debug(
                    f"Tracker {self.get_property('url')} failed (attempt {consecutive}): {error_message}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    f"Tracker {self.get_property('url')} failed (attempt {consecutive}): {error_message}",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Error updating tracker failure: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def update_scrape_response(self, scrape_data: Dict[str, Any]) -> None:
        """
        Update tracker with scrape response data

        Args:
            scrape_data: Dictionary containing scrape response data
        """
        try:
            current_time = time.time()
            self.set_property("last_scrape", current_time)

            # Update statistics from scrape
            if "complete" in scrape_data:
                self.set_property("seeders", scrape_data["complete"])
            if "incomplete" in scrape_data:
                self.set_property("leechers", scrape_data["incomplete"])
            if "downloaded" in scrape_data:
                self.set_property("downloaded", scrape_data["downloaded"])

            logger.debug(
                f"Tracker {self.get_property('url')} scrape updated: "
                f"S:{self.get_property('seeders')} L:{self.get_property('leechers')}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Error updating tracker scrape response: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def set_announcing(self) -> None:
        """Mark tracker as currently announcing"""
        self.set_property("status", "announcing")

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable this tracker"""
        self.set_property("enabled", enabled)
        if not enabled:
            self.set_property("status", "disabled")

    def get_status_summary(self) -> str:
        """Get a human-readable status summary"""
        status = self.get_property("status")

        if not self.get_property("enabled"):
            return "Disabled"
        elif status == "working":
            seeders = self.get_property("seeders")
            leechers = self.get_property("leechers")
            return f"Working (S:{seeders} L:{leechers})"
        elif status == "failed":
            error = self.get_property("error_message")
            return f"Failed: {error}" if error else "Failed"
        elif status == "announcing":
            return "Announcing..."
        else:
            return "Unknown"

    def get_timing_summary(self) -> str:
        """Get a human-readable timing summary"""
        if self.get_property("last_announce") == 0:
            return "Never announced"

        time_since = self.time_since_last_announce
        if time_since < 60:
            return f"{int(time_since)}s ago"
        elif time_since < 3600:
            return f"{int(time_since / 60)}m ago"
        else:
            return f"{int(time_since / 3600)}h ago"

    def _update_average_response_time(self, response_time: float) -> None:
        """Update running average of response times"""
        self._response_times.append(response_time)

        # Keep only last 10 response times
        if len(self._response_times) > 10:
            self._response_times.pop(0)

        # Calculate average
        if self._response_times:
            avg_time = sum(self._response_times) / len(self._response_times)
            self.set_property("average_response_time", avg_time)

    def can_announce_now(self) -> bool:
        """Check if tracker can be announced to now (respecting intervals)"""
        if not self.get_property("enabled"):
            return False

        if self.get_property("status") == "announcing":
            return False

        # Check minimum interval
        time_since = self.time_since_last_announce
        min_interval = self.get_property("min_announce_interval")

        return time_since >= min_interval

    def should_announce_now(self) -> bool:
        """Check if tracker should be announced to now (respecting schedule)"""
        if not self.can_announce_now():
            return False

        # Check if it's time for scheduled announce
        next_announce = self.get_property("next_announce")
        if next_announce > 0:
            return time.time() >= next_announce

        # If no schedule set, check normal interval
        time_since = self.time_since_last_announce
        interval = self.get_property("announce_interval")

        return time_since >= interval
