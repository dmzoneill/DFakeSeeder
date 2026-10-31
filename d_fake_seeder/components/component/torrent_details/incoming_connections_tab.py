"""
Incoming Connections Component

Manages the UI for displaying incoming peer connections, showing information
about peers that have connected to our peer server.
"""

from typing import Any

from .connections_tab_base import ConnectionsTabBase


class IncomingConnectionsTab(ConnectionsTabBase):
    """Component for managing incoming connections display."""

    DIRECTION = "incoming"
    LOG_NAME = "IncomingConnections"
    TAB_TITLE = "Incoming Connections"
    SELECTION_SIGNAL_ON_UPDATE = True
    BOOL_PROPERTIES = ("handshake_complete", "peer_interested", "am_choking")
    BYTES_PROPERTY = "bytes_uploaded"
    RATE_PROPERTY = "upload_rate"
    COUNT_PROPERTIES = ("requests_received", "pieces_sent")
    COLUMNS = (
        ("address", "Address"),
        ("status", "Status"),
        ("client", "Client"),
        ("connection_time", "Connected At"),
        ("handshake_complete", "Handshake"),
        ("peer_interested", "Interested"),
        ("am_choking", "Choking"),
        ("bytes_uploaded", "Uploaded"),
        ("upload_rate", "Upload Rate"),
        ("requests_received", "Requests"),
        ("pieces_sent", "Pieces Sent"),
        ("failure_reason", "Failure Reason"),
    )

    def add_incoming_connection(self, address: str, port: int, torrent_hash: str = "", **kwargs: Any) -> None:
        """Add a new incoming connection"""
        self.add_connection(address, port, torrent_hash, **kwargs)

    def update_incoming_connection(self, address: str, port: int, **kwargs: Any) -> None:
        """Update an existing incoming connection"""
        self.update_connection(address, port, **kwargs)

    def remove_incoming_connection(self, address: str, port: int) -> None:
        """Remove an incoming connection"""
        self.remove_connection(address, port)
