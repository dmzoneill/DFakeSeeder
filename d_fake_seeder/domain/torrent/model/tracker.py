"""
Tracker Model

GObject model for tracking tracker information including
announce URLs, status, response data, and statistics.
"""

import time  # isort: skip
from gi.repository import GObject


class Tracker(GObject.Object):
    """Model for tracking tracker data"""

    # Basic tracker info
    url = GObject.Property(type=str, default="")
    tier = GObject.Property(type=int, default=0)  # Tracker tier (0 = primary)
    status = GObject.Property(type=str, default="unknown")  # "working", "failed", "unknown"

    # Announce statistics
    last_announce = GObject.Property(type=float, default=0.0)
    last_scrape = GObject.Property(type=float, default=0.0)
    announce_interval = GObject.Property(type=int, default=0)
    next_announce = GObject.Property(type=float, default=0.0)

    # Response data
    seeders = GObject.Property(type=int, default=0)
    leechers = GObject.Property(type=int, default=0)
    downloaded = GObject.Property(type=int, default=0)

    # Error information
    error_message = GObject.Property(type=str, default="")

    # Response times
    last_response_time = GObject.Property(type=float, default=0.0)  # seconds

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.last_announce == 0.0:
            self.last_announce = time.time()

    @property
    def time_since_last_announce(self):
        """Get time since last announce in seconds"""
        if self.last_announce > 0:
            return time.time() - self.last_announce
        return 0.0

    @property
    def time_until_next_announce(self):
        """Get time until next announce in seconds"""
        if self.next_announce > 0:
            remaining = self.next_announce - time.time()
            return max(0, remaining)
        return 0.0

    def get_status_summary(self) -> str:
        """Get a summary of tracker status"""
        if self.status == "working":
            return f"Working (S:{self.seeders} L:{self.leechers})"
        elif self.status == "failed":
            return f"Failed: {self.error_message}" if self.error_message else "Failed"
        else:
            return "Unknown"
