"""
BitTorrent Peer Protocol (Compatibility Module)

Imports classes from separate files for backward compatibility.
This module serves as a central import point for peer protocol components.

References:
- BEP-003: The BitTorrent Protocol Specification
- BEP-010: Extension Protocol
"""

# Import all components from separate files
# fmt: off
from d_fake_seeder.domain.torrent.bittorrent_message import BitTorrentMessage
from d_fake_seeder.domain.torrent.peer_connection import PeerConnection
from d_fake_seeder.domain.torrent.peer_info import PeerInfo
from d_fake_seeder.domain.torrent.peer_protocol_manager import PeerProtocolManager

# Export all classes for backward compatibility
__all__ = [
    "BitTorrentMessage",
    "PeerConnection",
    "PeerInfo",
    "PeerProtocolManager",
]

# fmt: on
