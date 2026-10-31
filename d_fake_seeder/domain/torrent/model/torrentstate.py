"""
Torrent State Model.

This module defines the TorrentState class which represents the current
runtime state of a torrent including progress, upload/download stats,
and connection status.
"""

import uuid
from typing import Any

from gi.repository import GObject


class TorrentState(GObject.Object):
    """GObject representing aggregated state for torrents by tracker."""

    tracker = GObject.Property(type=GObject.TYPE_STRING, default="")
    count = GObject.Property(type=GObject.TYPE_INT, default=0)

    def __init__(self, tracker: Any, count: Any) -> None:
        super().__init__()
        self.uuid = str(uuid.uuid4())
        self.tracker = tracker
        self.count = count
