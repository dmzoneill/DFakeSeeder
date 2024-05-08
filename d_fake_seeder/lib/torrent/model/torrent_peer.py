import uuid

from gi.repository import GObject


class TorrentPeer(GObject.Object):
    peer = GObject.Property(type=GObject.TYPE_STRING, default="")
    client = GObject.Property(type=GObject.TYPE_STRING, default="")
    x1 = GObject.Property(type=GObject.TYPE_FLOAT, default=0.0)
    x2 = GObject.Property(type=GObject.TYPE_FLOAT, default=0.0)
    x3 = GObject.Property(type=GObject.TYPE_FLOAT, default=0.0)

    def __init__(self, peer, client, x1, x2, x3):
        super().__init__()
        self.uuid = str(uuid.uuid4())
        self.peer = peer
        self.client = client
        self.x1 = x1
        self.x2 = x2
        self.x3 = x3
