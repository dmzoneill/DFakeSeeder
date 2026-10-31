"""
Outgoing Connections Component

Manages the UI for displaying outgoing peer connections, showing information
about peers that we've initiated connections to.
"""

from typing import Any

from .connections_tab_base import ConnectionsTabBase


class OutgoingConnectionsTab(ConnectionsTabBase):
    """Component for managing outgoing connections display."""

    DIRECTION = "outgoing"
    LOG_NAME = "OutgoingConnections"
    TAB_TITLE = "Outgoing Connections"
    BOOL_PROPERTIES = ("handshake_complete", "am_interested", "peer_choking")
    BYTES_PROPERTY = "bytes_downloaded"
    RATE_PROPERTY = "download_rate"
    COUNT_PROPERTIES = ("requests_sent", "pieces_received")
    COLUMNS = (
        ("address", "IP Address"),
        ("status", "Connection Status"),
        ("client", "Client"),
        ("connection_time", "Connected At"),
        ("handshake_complete", "Handshake"),
        ("am_interested", "Interested"),
        ("peer_choking", "Peer Choking"),
        ("bytes_downloaded", "Downloaded"),
        ("download_rate", "Download Rate"),
        ("requests_sent", "Requests"),
        ("pieces_received", "Pieces Received"),
        ("failure_reason", "Failure Reason"),
    )

    def add_outgoing_connection(self, address: str, port: int, torrent_hash: str = "", **kwargs: Any) -> None:
        """Add a new outgoing connection"""
        self.add_connection(address, port, torrent_hash, **kwargs)

    def update_outgoing_connection(self, address: str, port: int, **kwargs: Any) -> None:
        """Update an existing outgoing connection"""
        self.update_connection(address, port, **kwargs)

    def remove_outgoing_connection(self, address: str, port: int) -> None:
        """Remove an outgoing connection"""
        self.remove_connection(address, port)
