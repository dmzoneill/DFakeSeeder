"""
Connection Peer Model

GObject model for tracking individual peer connections with their
status, statistics, and protocol information.
"""

# fmt: off
import time

import gi

gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402

# fmt: on


class ConnectionPeer(GObject.Object):
    """Model for tracking peer connection data"""

    address = GObject.Property(type=str, default="")
    port = GObject.Property(type=int, default=0)
    peer_id = GObject.Property(type=str, default="")
    client = GObject.Property(type=str, default="")
    direction = GObject.Property(type=str, default="")  # "incoming" or "outgoing"
    torrent_hash = GObject.Property(type=str, default="")  # Hash of the torrent this connection belongs to

    # Connection status
    connected = GObject.Property(type=bool, default=False)
    handshake_complete = GObject.Property(type=bool, default=False)
    connection_time = GObject.Property(type=float, default=0.0)
    last_message_time = GObject.Property(type=float, default=0.0)
    status = GObject.Property(type=str, default="connecting")  # "connecting", "connected", "failed", "disconnected"
    failure_reason = GObject.Property(type=str, default="")  # Reason for failure if status is "failed"

    # Protocol state
    am_choking = GObject.Property(type=bool, default=True)
    am_interested = GObject.Property(type=bool, default=False)
    peer_choking = GObject.Property(type=bool, default=True)
    peer_interested = GObject.Property(type=bool, default=False)

    # Statistics
    bytes_uploaded = GObject.Property(type=int, default=0)
    bytes_downloaded = GObject.Property(type=int, default=0)
    upload_rate = GObject.Property(type=float, default=0.0)
    download_rate = GObject.Property(type=float, default=0.0)

    # Piece information
    pieces_sent = GObject.Property(type=int, default=0)
    pieces_received = GObject.Property(type=int, default=0)
    requests_sent = GObject.Property(type=int, default=0)
    requests_received = GObject.Property(type=int, default=0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.connection_time == 0.0:
            self.connection_time = time.time()

    @property
    def connection_duration(self):
        """Get connection duration in seconds"""
        if self.connected:
            return time.time() - self.connection_time
        return 0.0

    @property
    def last_activity_age(self):
        """Get time since last message in seconds"""
        if self.last_message_time > 0:
            return time.time() - self.last_message_time
        return 0.0

    def update_rates(self, upload_bytes_delta: int, download_bytes_delta: int, time_delta: float):
        """Update transfer rates based on deltas"""
        if time_delta > 0:
            self.upload_rate = upload_bytes_delta / time_delta
            self.download_rate = download_bytes_delta / time_delta

    def get_status_summary(self) -> str:
        """Get a summary of connection status"""
        status_parts = []

        if not self.connected:
            return "Disconnected"

        if not self.handshake_complete:
            status_parts.append("Handshaking")
        else:
            status_parts.append("Connected")

        if self.peer_interested and not self.am_choking:
            status_parts.append("Uploading")
        elif self.am_interested and not self.peer_choking:
            status_parts.append("Downloading")

        return " | ".join(status_parts) if status_parts else "Connected"
