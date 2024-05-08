import uuid

from gi.repository import GObject


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
    progress = GObject.Property(type=GObject.TYPE_LONG, default=0)
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

    def __init__(self):
        super().__init__()
        self.uuid = str(uuid.uuid4())
