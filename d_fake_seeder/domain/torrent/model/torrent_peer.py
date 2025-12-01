# fmt: off
import uuid

import gi

gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402

# fmt: on


class TorrentPeer(GObject.Object):
    # Core peer information
    address = GObject.Property(type=GObject.TYPE_STRING, default="")
    client = GObject.Property(type=GObject.TYPE_STRING, default="")
    country = GObject.Property(type=GObject.TYPE_STRING, default="")

    # Download/Upload progress
    progress = GObject.Property(type=GObject.TYPE_FLOAT, default=0.0)

    # Speed information (in bytes/sec)
    down_speed = GObject.Property(type=GObject.TYPE_FLOAT, default=0.0)
    up_speed = GObject.Property(type=GObject.TYPE_FLOAT, default=0.0)

    # Connection information
    seed = GObject.Property(type=GObject.TYPE_BOOLEAN, default=False)

    # Raw peer ID for debugging
    peer_id = GObject.Property(type=GObject.TYPE_STRING, default="")

    def __init__(
        self,
        address="",
        client="",
        country="",
        progress=0.0,
        down_speed=0.0,
        up_speed=0.0,
        seed=False,
        peer_id="",
    ):
        super().__init__()
        self.uuid = str(uuid.uuid4())
        self.address = address
        self.client = client
        self.country = country
        self.progress = progress
        self.down_speed = down_speed
        self.up_speed = up_speed
        self.seed = seed
        self.peer_id = peer_id
