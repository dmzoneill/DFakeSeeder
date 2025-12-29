# fmt: off
# isort: skip_file
"""
Torrent Registry for the inbuilt BitTorrent tracker.

Tracks torrent metadata and statistics.
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from d_fake_seeder.lib.logger import logger

# fmt: on


@dataclass
class TrackedTorrent:  # pylint: disable=too-many-instance-attributes
    """Information about a tracked torrent."""

    info_hash: bytes  # 20-byte info hash
    name: Optional[str] = None  # Torrent name if known
    total_size: int = 0  # Total size in bytes
    created_at: float = field(default_factory=time.time)
    last_announce: float = field(default_factory=time.time)
    times_completed: int = 0  # Number of times downloaded completely
    total_uploaded: int = 0  # Total bytes uploaded across all peers
    total_downloaded: int = 0  # Total bytes downloaded across all peers
    is_internal: bool = False  # True if tracked by DFakeSeeder itself

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for UI/API."""
        return {
            "info_hash": self.info_hash.hex(),
            "name": self.name or self.info_hash.hex()[:16] + "...",
            "total_size": self.total_size,
            "created_at": self.created_at,
            "last_announce": self.last_announce,
            "times_completed": self.times_completed,
            "total_uploaded": self.total_uploaded,
            "total_downloaded": self.total_downloaded,
            "is_internal": self.is_internal,
        }


class TorrentRegistry:
    """
    Thread-safe registry of tracked torrents.

    Stores torrent metadata and statistics.
    """

    def __init__(self) -> None:
        """Initialize the torrent registry."""
        self._lock = threading.RLock()
        self._torrents: Dict[bytes, TrackedTorrent] = {}

        logger.debug(
            "TorrentRegistry initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def register_torrent(
        self,
        info_hash: bytes,
        name: Optional[str] = None,
        total_size: int = 0,
        is_internal: bool = False,
    ) -> TrackedTorrent:
        """
        Register a new torrent or update existing one.

        Args:
            info_hash: 20-byte torrent info hash
            name: Torrent name (optional)
            total_size: Total size in bytes (optional)
            is_internal: True if this is DFakeSeeder's own torrent

        Returns:
            The TrackedTorrent object
        """
        with self._lock:
            if info_hash in self._torrents:
                torrent = self._torrents[info_hash]
                # Update metadata if provided
                if name and not torrent.name:
                    torrent.name = name
                if total_size and not torrent.total_size:
                    torrent.total_size = total_size
                if is_internal:
                    torrent.is_internal = True
                torrent.last_announce = time.time()
            else:
                torrent = TrackedTorrent(
                    info_hash=info_hash,
                    name=name,
                    total_size=total_size,
                    is_internal=is_internal,
                )
                self._torrents[info_hash] = torrent

                logger.debug(
                    f"Registered torrent: {name or info_hash.hex()[:16]}",
                    extra={"class_name": self.__class__.__name__},
                )

            return torrent

    def unregister_torrent(self, info_hash: bytes) -> bool:
        """
        Remove a torrent from the registry.

        Args:
            info_hash: 20-byte torrent info hash

        Returns:
            True if removed, False if not found
        """
        with self._lock:
            if info_hash in self._torrents:
                torrent = self._torrents[info_hash]
                del self._torrents[info_hash]

                logger.debug(
                    f"Unregistered torrent: {torrent.name or info_hash.hex()[:16]}",
                    extra={"class_name": self.__class__.__name__},
                )
                return True
            return False

    def get_torrent(self, info_hash: bytes) -> Optional[TrackedTorrent]:
        """
        Get a tracked torrent by info hash.

        Args:
            info_hash: 20-byte torrent info hash

        Returns:
            TrackedTorrent or None if not found
        """
        with self._lock:
            return self._torrents.get(info_hash)

    def update_announce(
        self,
        info_hash: bytes,
        uploaded: int = 0,
        downloaded: int = 0,
        completed: bool = False,
    ) -> None:
        """
        Update torrent statistics from an announce.

        Args:
            info_hash: 20-byte torrent info hash
            uploaded: Bytes uploaded in this announce
            downloaded: Bytes downloaded in this announce
            completed: True if this was a "completed" event
        """
        with self._lock:
            if info_hash in self._torrents:
                torrent = self._torrents[info_hash]
                torrent.last_announce = time.time()
                torrent.total_uploaded += uploaded
                torrent.total_downloaded += downloaded
                if completed:
                    torrent.times_completed += 1

    def is_allowed(self, info_hash: bytes, private_mode: bool = False) -> bool:
        """
        Check if a torrent is allowed to be tracked.

        Args:
            info_hash: 20-byte torrent info hash
            private_mode: If True, only pre-registered torrents are allowed

        Returns:
            True if allowed, False otherwise
        """
        if not private_mode:
            return True
        with self._lock:
            return info_hash in self._torrents

    def get_all_torrents(self) -> List[TrackedTorrent]:
        """Get list of all tracked torrents."""
        with self._lock:
            return list(self._torrents.values())

    def get_internal_torrents(self) -> List[TrackedTorrent]:
        """Get list of torrents tracked by DFakeSeeder itself."""
        with self._lock:
            return [t for t in self._torrents.values() if t.is_internal]

    def get_external_torrents(self) -> List[TrackedTorrent]:
        """Get list of torrents from external clients."""
        with self._lock:
            return [t for t in self._torrents.values() if not t.is_internal]

    def get_count(self) -> int:
        """Get total number of tracked torrents."""
        with self._lock:
            return len(self._torrents)

    def clear(self) -> None:
        """Clear all torrents from the registry."""
        with self._lock:
            self._torrents.clear()
            logger.debug(
                "TorrentRegistry cleared",
                extra={"class_name": self.__class__.__name__},
            )
