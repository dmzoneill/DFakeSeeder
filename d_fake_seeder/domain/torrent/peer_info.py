"""
BitTorrent Peer Information

Represents information about a peer including connection state and statistics.
"""

# fmt: off
from dataclasses import dataclass
from typing import Optional

# fmt: on


@dataclass
class PeerInfo:
    """Information about a peer"""

    ip: str
    port: int
    peer_id: Optional[bytes] = None
    client_name: Optional[str] = None
    last_seen: float = 0
    last_connected: float = 0
    connection_attempts: int = 0
    choked: bool = True
    interested: bool = False
    has_pieces: Optional[bytes] = None  # Bitfield
    download_speed: float = 0.0
    upload_speed: float = 0.0
    progress: float = 0.0
    is_seed: bool = False
