# fmt: off
# isort: skip_file
"""
Local Announcer for the inbuilt BitTorrent tracker.

Allows DFakeSeeder's seeders to announce directly to the inbuilt tracker
without network overhead.
"""

from dataclasses import dataclass
from typing import Optional

from d_fake_seeder.lib.logger import logger

# fmt: on


@dataclass
class LocalAnnounce:  # pylint: disable=too-many-instance-attributes
    """Data structure for a local announce."""

    info_hash: bytes  # 20-byte SHA1 hash
    peer_id: bytes  # 20-byte peer identifier
    port: int  # Listening port
    uploaded: int  # Total bytes uploaded
    downloaded: int  # Total bytes downloaded
    left: int  # Bytes remaining (0 = seeder)
    event: str  # "started", "stopped", "completed", ""
    ip: Optional[str] = None  # Override IP (defaults to local)
    torrent_name: Optional[str] = None  # Torrent name for registration


class LocalAnnouncer:
    """
    Local announcer for DFakeSeeder's own seeders.

    Provides direct in-process communication with the inbuilt tracker,
    avoiding network overhead for self-announce.
    """

    _instance: Optional["LocalAnnouncer"] = None

    def __init__(self, enabled: bool = True) -> None:
        """
        Initialize the local announcer.

        Args:
            enabled: Whether local announcing is enabled
        """
        self.enabled = enabled
        self._local_ip = "127.0.0.1"

        LocalAnnouncer._instance = self

        logger.debug(
            f"LocalAnnouncer initialized (enabled={enabled})",
            extra={"class_name": self.__class__.__name__},
        )

    @classmethod
    def get_instance(cls) -> Optional["LocalAnnouncer"]:
        """Get the singleton instance."""
        return cls._instance

    def announce(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        info_hash: bytes,
        peer_id: bytes,
        port: int,
        uploaded: int = 0,
        downloaded: int = 0,
        left: int = 0,
        event: str = "",
        torrent_name: Optional[str] = None,
    ) -> bool:
        """
        Announce to the inbuilt tracker.

        Args:
            info_hash: 20-byte torrent info hash
            peer_id: 20-byte peer identifier
            port: Listening port
            uploaded: Total bytes uploaded
            downloaded: Total bytes downloaded
            left: Bytes remaining (0 = seeder)
            event: Event type (started, stopped, completed, or empty)
            torrent_name: Torrent name for registration

        Returns:
            True if announced successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Import here to avoid circular imports
            from d_fake_seeder.domain.tracker.tracker_server import TrackerServer

            tracker = TrackerServer.get_instance()
            if not tracker or not tracker.is_running:
                logger.trace(
                    "Inbuilt tracker not running, skipping local announce",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Register torrent if this is a "started" event or first announce
            if event in ("started", ""):
                tracker.register_torrent(
                    info_hash=info_hash,
                    name=torrent_name,
                    is_internal=True,
                )

            # Announce peer
            tracker.announce_peer(
                info_hash=info_hash,
                peer_id=peer_id,
                ip=self._local_ip,
                port=port,
                uploaded=uploaded,
                downloaded=downloaded,
                left=left,
                event=event,
                is_internal=True,
            )

            logger.trace(
                f"Local announce: {info_hash.hex()[:16]} event={event or 'periodic'}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning(
                f"Local announce failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def announce_started(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        info_hash: bytes,
        peer_id: bytes,
        port: int,
        total_size: int = 0,
        torrent_name: Optional[str] = None,
    ) -> bool:
        """
        Announce torrent started seeding.

        Args:
            info_hash: 20-byte torrent info hash
            peer_id: 20-byte peer identifier
            port: Listening port
            total_size: Total torrent size
            torrent_name: Torrent name

        Returns:
            True if announced successfully
        """
        return self.announce(
            info_hash=info_hash,
            peer_id=peer_id,
            port=port,
            uploaded=0,
            downloaded=0,
            left=0,  # We're seeding, so left=0
            event="started",
            torrent_name=torrent_name,
        )

    def announce_stopped(
        self,
        info_hash: bytes,
        peer_id: bytes,
        port: int,
    ) -> bool:
        """
        Announce torrent stopped seeding.

        Args:
            info_hash: 20-byte torrent info hash
            peer_id: 20-byte peer identifier
            port: Listening port

        Returns:
            True if announced successfully
        """
        return self.announce(
            info_hash=info_hash,
            peer_id=peer_id,
            port=port,
            event="stopped",
        )

    def announce_periodic(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        info_hash: bytes,
        peer_id: bytes,
        port: int,
        uploaded: int = 0,
        downloaded: int = 0,
        left: int = 0,
    ) -> bool:
        """
        Periodic announce (update stats).

        Args:
            info_hash: 20-byte torrent info hash
            peer_id: 20-byte peer identifier
            port: Listening port
            uploaded: Total bytes uploaded
            downloaded: Total bytes downloaded
            left: Bytes remaining

        Returns:
            True if announced successfully
        """
        return self.announce(
            info_hash=info_hash,
            peer_id=peer_id,
            port=port,
            uploaded=uploaded,
            downloaded=downloaded,
            left=left,
            event="",
        )

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable local announcing."""
        self.enabled = enabled
        logger.debug(
            f"LocalAnnouncer {'enabled' if enabled else 'disabled'}",
            extra={"class_name": self.__class__.__name__},
        )
