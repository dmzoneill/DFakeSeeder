# fmt: off
import uuid

import gi

gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402

# fmt: on


class Attributes(GObject.Object):
    # Hidden attributes
    active = GObject.Property(type=GObject.TYPE_BOOLEAN, default=True)

    # Viewable attributes
    id = GObject.Property(type=GObject.TYPE_LONG, default=0)
    announce_interval = GObject.Property(type=GObject.TYPE_LONG, default=0)
    download_speed = GObject.Property(type=GObject.TYPE_LONG, default=300)
    filepath = GObject.Property(type=GObject.TYPE_STRING, default="")
    leechers = GObject.Property(type=GObject.TYPE_LONG, default=0)
    name = GObject.Property(type=GObject.TYPE_STRING, default="")
    next_update = GObject.Property(type=GObject.TYPE_LONG, default=0)
    progress = GObject.Property(type=GObject.TYPE_FLOAT, default=0.0)
    seeders = GObject.Property(type=GObject.TYPE_LONG, default=0)
    session_downloaded = GObject.Property(type=GObject.TYPE_LONG, default=0)
    session_uploaded = GObject.Property(type=GObject.TYPE_LONG, default=0)
    small_torrent_limit = GObject.Property(type=GObject.TYPE_LONG, default=0)
    threshold = GObject.Property(type=GObject.TYPE_LONG, default=0)
    total_downloaded = GObject.Property(type=GObject.TYPE_LONG, default=0)
    total_size = GObject.Property(type=GObject.TYPE_LONG, default=0)
    total_uploaded = GObject.Property(type=GObject.TYPE_LONG, default=0)
    upload_speed = GObject.Property(type=GObject.TYPE_LONG, default=30)
    uploading = GObject.Property(type=GObject.TYPE_BOOLEAN, default=False)

    # New attributes for enhanced functionality
    label = GObject.Property(type=GObject.TYPE_STRING, default="")
    priority = GObject.Property(type=GObject.TYPE_STRING, default="normal")  # low, normal, high
    upload_limit = GObject.Property(type=GObject.TYPE_LONG, default=0)  # 0 = unlimited (uses global)
    download_limit = GObject.Property(type=GObject.TYPE_LONG, default=0)  # 0 = unlimited (uses global)
    super_seeding = GObject.Property(type=GObject.TYPE_BOOLEAN, default=False)
    sequential_download = GObject.Property(type=GObject.TYPE_BOOLEAN, default=False)
    force_start = GObject.Property(type=GObject.TYPE_BOOLEAN, default=False)

    # Torrent metadata properties
    creation_date = GObject.Property(type=GObject.TYPE_LONG, default=0)  # Unix timestamp
    comment = GObject.Property(type=GObject.TYPE_STRING, default="")
    created_by = GObject.Property(type=GObject.TYPE_STRING, default="")
    piece_length = GObject.Property(type=GObject.TYPE_LONG, default=0)  # Bytes per piece
    piece_count = GObject.Property(type=GObject.TYPE_LONG, default=0)  # Total number of pieces

    def __init__(self):
        super().__init__()
        self.uuid = str(uuid.uuid4())
