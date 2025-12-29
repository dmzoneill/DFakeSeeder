"""
Torrent Peer Model.

This module defines the TorrentPeer class which represents a peer connected
to a torrent. It stores peer information such as IP address, port, client
identifier, and connection state.
"""

# fmt: off
import uuid
from typing import Any

import gi

gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402

# fmt: on


class TorrentPeer(GObject.Object):  # pylint: disable=too-many-instance-attributes
    """GObject representing a connected peer with address, client, and stats."""

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

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        address: Any = "",
        client: Any = "",
        country: Any = "",
        progress: Any = 0.0,
        down_speed: Any = 0.0,
        up_speed: Any = 0.0,
        seed: Any = False,
        peer_id: Any = "",
    ) -> None:  # noqa: E501
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
