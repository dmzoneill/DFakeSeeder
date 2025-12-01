# fmt: off
import uuid

import gi

gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402

# fmt: on


class TorrentState(GObject.Object):
    tracker = GObject.Property(type=GObject.TYPE_STRING, default="")
    count = GObject.Property(type=GObject.TYPE_INT, default=0)

    def __init__(self, tracker, count):
        super().__init__()
        self.uuid = str(uuid.uuid4())
        self.tracker = tracker
        self.count = count
