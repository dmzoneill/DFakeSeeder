# fmt: off
# isort: skip_file
"""
Peer Database for the inbuilt BitTorrent tracker.

Stores peer information with automatic expiry based on last announce time.
"""

import socket
import struct
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from d_fake_seeder.lib.logger import logger

# fmt: on


@dataclass
class PeerInfo:  # pylint: disable=too-many-instance-attributes
    """Information about a peer in the swarm."""

    peer_id: bytes  # 20-byte peer identifier
    ip: str  # IP address
    port: int  # Listening port
    info_hash: bytes  # 20-byte torrent info hash
    uploaded: int = 0  # Total bytes uploaded
    downloaded: int = 0  # Total bytes downloaded
    left: int = 0  # Bytes remaining (0 = seeder)
    last_seen: float = field(default_factory=time.time)
    is_internal: bool = False  # True if this is DFakeSeeder's own peer

    @property
    def is_seeder(self) -> bool:
        """Check if this peer is a seeder (has complete file)."""
        return self.left == 0

    @property
    def compact_ipv4(self) -> bytes:
        """Return compact 6-byte representation (4 bytes IP + 2 bytes port)."""
        try:
            ip_bytes = socket.inet_aton(self.ip)
            port_bytes = struct.pack(">H", self.port)
            return ip_bytes + port_bytes
        except (socket.error, struct.error):
            return b""

    def to_dict(self) -> Dict[bytes, Any]:
        """Convert to dictionary for non-compact response."""
        return {
            b"peer id": self.peer_id,
            b"ip": self.ip.encode(),
            b"port": self.port,
        }


class PeerDatabase:
    """
    Thread-safe peer database for the tracker.

    Stores peers indexed by info_hash for fast lookup.
    Automatically expires peers that haven't announced recently.
    """

    def __init__(self, peer_timeout_seconds: int = 5400) -> None:
        """
        Initialize the peer database.

        Args:
            peer_timeout_seconds: Time after which peers are considered expired.
                                  Default is 5400 (3 * 1800 announce interval).
        """
        self._lock = threading.RLock()
        self._peers: Dict[bytes, Dict[bytes, PeerInfo]] = {}  # info_hash -> peer_id -> PeerInfo
        self._peer_timeout = peer_timeout_seconds
        self._stats = {
            "total_announces": 0,
            "total_peers_added": 0,
            "total_peers_removed": 0,
        }

        logger.debug(
            f"PeerDatabase initialized with {peer_timeout_seconds}s timeout",
            extra={"class_name": self.__class__.__name__},
        )

    def add_or_update_peer(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        info_hash: bytes,
        peer_id: bytes,
        ip: str,
        port: int,
        uploaded: int = 0,
        downloaded: int = 0,
        left: int = 0,
        is_internal: bool = False,
    ) -> None:
        """
        Add a new peer or update an existing one.

        Args:
            info_hash: 20-byte torrent info hash
            peer_id: 20-byte peer identifier
            ip: Peer IP address
            port: Peer listening port
            uploaded: Total bytes uploaded
            downloaded: Total bytes downloaded
            left: Bytes remaining to download
            is_internal: True if this is DFakeSeeder's own peer
        """
        with self._lock:
            if info_hash not in self._peers:
                self._peers[info_hash] = {}

            is_new = peer_id not in self._peers[info_hash]

            self._peers[info_hash][peer_id] = PeerInfo(
                peer_id=peer_id,
                ip=ip,
                port=port,
                info_hash=info_hash,
                uploaded=uploaded,
                downloaded=downloaded,
                left=left,
                last_seen=time.time(),
                is_internal=is_internal,
            )

            self._stats["total_announces"] += 1
            if is_new:
                self._stats["total_peers_added"] += 1

            logger.trace(
                f"Peer {'added' if is_new else 'updated'}: " f"{ip}:{port} for {info_hash.hex()[:16]}",
                extra={"class_name": self.__class__.__name__},
            )

    def remove_peer(self, info_hash: bytes, peer_id: bytes) -> bool:
        """
        Remove a peer from the database.

        Args:
            info_hash: 20-byte torrent info hash
            peer_id: 20-byte peer identifier

        Returns:
            True if peer was removed, False if not found
        """
        with self._lock:
            if info_hash in self._peers and peer_id in self._peers[info_hash]:
                del self._peers[info_hash][peer_id]
                self._stats["total_peers_removed"] += 1

                # Clean up empty torrent entry
                if not self._peers[info_hash]:
                    del self._peers[info_hash]

                logger.trace(
                    f"Peer removed for {info_hash.hex()[:16]}",
                    extra={"class_name": self.__class__.__name__},
                )
                return True
            return False

    def get_peers(
        self,
        info_hash: bytes,
        max_peers: int = 50,
        exclude_peer_id: Optional[bytes] = None,
        compact: bool = True,
    ) -> Tuple[bytes, List[Dict[bytes, Any]]]:
        """
        Get peers for a torrent.

        Args:
            info_hash: 20-byte torrent info hash
            max_peers: Maximum number of peers to return
            exclude_peer_id: Peer ID to exclude (requesting peer)
            compact: If True, return compact format

        Returns:
            Tuple of (compact_peers_bytes, non_compact_peers_list)
            One will be empty based on compact flag.
        """
        with self._lock:
            if info_hash not in self._peers:
                return b"", []

            peers = list(self._peers[info_hash].values())

            # Exclude requesting peer
            if exclude_peer_id:
                peers = [p for p in peers if p.peer_id != exclude_peer_id]

            # Limit to max_peers (random selection if more)
            if len(peers) > max_peers:
                import random

                peers = random.sample(peers, max_peers)

            if compact:
                compact_data = b"".join(p.compact_ipv4 for p in peers if p.compact_ipv4)
                return compact_data, []
            return b"", [p.to_dict() for p in peers]

    def get_stats(self, info_hash: bytes) -> Dict[str, int]:
        """
        Get statistics for a torrent.

        Args:
            info_hash: 20-byte torrent info hash

        Returns:
            Dict with 'complete' (seeders), 'incomplete' (leechers), 'downloaded'
        """
        with self._lock:
            if info_hash not in self._peers:
                return {"complete": 0, "incomplete": 0, "downloaded": 0}

            peers = self._peers[info_hash].values()
            complete = sum(1 for p in peers if p.is_seeder)
            incomplete = sum(1 for p in peers if not p.is_seeder)

            return {
                "complete": complete,
                "incomplete": incomplete,
                "downloaded": 0,  # TODO: Track completed downloads  # pylint: disable=fixme
            }

    def get_all_info_hashes(self) -> List[bytes]:
        """Get list of all tracked info hashes."""
        with self._lock:
            return list(self._peers.keys())

    def get_total_peers(self) -> int:
        """Get total number of peers across all torrents."""
        with self._lock:
            return sum(len(peers) for peers in self._peers.values())

    def get_total_torrents(self) -> int:
        """Get total number of tracked torrents."""
        with self._lock:
            return len(self._peers)

    def expire_old_peers(self) -> int:
        """
        Remove peers that haven't announced recently.

        Returns:
            Number of peers removed
        """
        removed = 0
        now = time.time()
        cutoff = now - self._peer_timeout

        with self._lock:
            for info_hash in list(self._peers.keys()):
                for peer_id in list(self._peers[info_hash].keys()):
                    peer = self._peers[info_hash][peer_id]
                    if peer.last_seen < cutoff:
                        del self._peers[info_hash][peer_id]
                        removed += 1

                # Clean up empty torrent entries
                if not self._peers[info_hash]:
                    del self._peers[info_hash]

        if removed > 0:
            self._stats["total_peers_removed"] += removed
            logger.debug(
                f"Expired {removed} peers",
                extra={"class_name": self.__class__.__name__},
            )

        return removed

    def get_database_stats(self) -> Dict[str, Any]:
        """Get overall database statistics."""
        with self._lock:
            return {
                "total_torrents": len(self._peers),
                "total_peers": self.get_total_peers(),
                "total_announces": self._stats["total_announces"],
                "total_peers_added": self._stats["total_peers_added"],
                "total_peers_removed": self._stats["total_peers_removed"],
            }

    def clear(self) -> None:
        """Clear all peers from the database."""
        with self._lock:
            self._peers.clear()
            logger.debug(
                "PeerDatabase cleared",
                extra={"class_name": self.__class__.__name__},
            )
