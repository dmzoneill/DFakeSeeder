# fmt: off
# isort: skip_file
"""
BitTorrent Tracker Server.

Main server that handles HTTP (and optionally UDP) tracker requests.
"""

import threading
import time
from http.server import ThreadingHTTPServer
from typing import Any, List, Optional

from d_fake_seeder.domain.tracker.http_handler import TrackerHTTPHandler
from d_fake_seeder.domain.tracker.peer_database import PeerDatabase
from d_fake_seeder.domain.tracker.security import TrackerSecurity
from d_fake_seeder.domain.tracker.torrent_registry import TorrentRegistry
from d_fake_seeder.lib.logger import logger

# fmt: on


class TrackerServer:  # pylint: disable=too-many-instance-attributes
    """
    BitTorrent Tracker Server.

    Provides HTTP announce/scrape endpoints for BitTorrent clients.
    Manages peer database and torrent registry.
    """

    _instance: Optional["TrackerServer"] = None

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
        self,
        bind_address: str = "0.0.0.0",
        http_port: int = 6969,
        udp_enabled: bool = False,
        udp_port: int = 6969,
        announce_interval: int = 1800,
        peer_timeout_multiplier: int = 3,
        max_peers_per_announce: int = 50,
        private_mode: bool = False,
        enable_scrape: bool = True,
        log_announces: bool = False,
        ip_whitelist: Optional[List[str]] = None,
        ip_blacklist: Optional[List[str]] = None,
        rate_limit_per_minute: int = 60,
    ) -> None:
        """
        Initialize the tracker server.

        Args:
            bind_address: Address to bind to
            http_port: HTTP port to listen on
            udp_enabled: If True, enable UDP tracker protocol
            udp_port: UDP port to listen on
            announce_interval: Announce interval in seconds
            peer_timeout_multiplier: Multiply interval for peer timeout
            max_peers_per_announce: Max peers to return per announce
            private_mode: If True, only pre-registered torrents allowed
            enable_scrape: If True, enable /scrape endpoint
            log_announces: If True, log all announce requests
            ip_whitelist: List of allowed IP addresses
            ip_blacklist: List of blocked IP addresses
            rate_limit_per_minute: Max requests per minute per IP
        """
        self.bind_address = bind_address
        self.http_port = http_port
        self.udp_enabled = udp_enabled
        self.udp_port = udp_port
        self.announce_interval = announce_interval
        self.peer_timeout_multiplier = peer_timeout_multiplier
        self.max_peers_per_announce = max_peers_per_announce
        self.private_mode = private_mode
        self.enable_scrape = enable_scrape
        self.log_announces = log_announces

        # Calculate peer timeout
        peer_timeout = announce_interval * peer_timeout_multiplier

        # Initialize components
        self.peer_database = PeerDatabase(peer_timeout_seconds=peer_timeout)
        self.torrent_registry = TorrentRegistry()
        self.security = TrackerSecurity(
            ip_whitelist=ip_whitelist,
            ip_blacklist=ip_blacklist,
            rate_limit_per_minute=rate_limit_per_minute,
        )

        # Server state
        self._http_server: Optional[ThreadingHTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None
        self._udp_handler: Optional[Any] = None  # UDPTrackerHandler when UDP enabled
        self._expiry_thread: Optional[threading.Thread] = None
        self._running = False
        self._start_time: Optional[float] = None

        # Statistics
        self._announces_sent = 0  # Track local announces sent
        self._stats = {
            "announces_per_minute": 0,
            "last_minute_announces": 0,
            "last_stats_time": time.time(),
        }

        # Set singleton
        TrackerServer._instance = self

        protocols = "HTTP"
        if udp_enabled:
            protocols += "+UDP"
        logger.info(
            f"TrackerServer initialized ({protocols}) on {bind_address}:{http_port}",
            extra={"class_name": self.__class__.__name__},
        )

    @classmethod
    def get_instance(cls) -> Optional["TrackerServer"]:
        """Get the singleton instance."""
        return cls._instance

    def start(self) -> bool:
        """
        Start the tracker server.

        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            logger.warning(
                "Tracker already running",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            # Create HTTP handler class with reference to this server
            handler_class = type(
                "BoundTrackerHandler",
                (TrackerHTTPHandler,),
                {"tracker_server": self},
            )

            # Create HTTP server
            self._http_server = ThreadingHTTPServer(
                (self.bind_address, self.http_port),
                handler_class,
            )

            # Start HTTP server thread
            self._http_thread = threading.Thread(
                target=self._run_http_server,
                name="TrackerHTTP",
                daemon=True,
            )
            self._http_thread.start()

            # Start peer expiry thread
            self._expiry_thread = threading.Thread(
                target=self._run_expiry_loop,
                name="TrackerExpiry",
                daemon=True,
            )
            self._expiry_thread.start()

            # Start UDP handler if enabled
            if self.udp_enabled:
                from d_fake_seeder.domain.tracker.udp_handler import UDPTrackerHandler

                self._udp_handler = UDPTrackerHandler(
                    bind_address=self.bind_address,
                    port=self.udp_port,
                    peer_database=self.peer_database,
                    torrent_registry=self.torrent_registry,
                    announce_interval=self.announce_interval,
                    private_mode=self.private_mode,
                    log_announces=self.log_announces,
                    security=self.security,
                )
                if not self._udp_handler.start():
                    logger.warning(
                        "Failed to start UDP tracker",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self._udp_handler = None

            self._running = True
            self._start_time = time.time()

            protocols = f"http://{self.bind_address}:{self.http_port}/announce"
            if self._udp_handler:
                protocols += f", udp://{self.bind_address}:{self.udp_port}"

            logger.info(
                f"Tracker started on {protocols}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                f"Failed to start tracker: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def stop(self) -> None:
        """Stop the tracker server."""
        if not self._running:
            return

        self._running = False

        # Stop UDP handler
        if self._udp_handler:
            self._udp_handler.stop()
            self._udp_handler = None

        # Stop HTTP server
        if self._http_server:
            self._http_server.shutdown()
            self._http_server = None

        # Wait for threads
        if self._http_thread and self._http_thread.is_alive():
            self._http_thread.join(timeout=5)

        if self._expiry_thread and self._expiry_thread.is_alive():
            self._expiry_thread.join(timeout=5)

        logger.info(
            "Tracker stopped",
            extra={"class_name": self.__class__.__name__},
        )

    def _run_http_server(self) -> None:
        """Run the HTTP server loop."""
        if self._http_server:
            try:
                self._http_server.serve_forever()
            except Exception as e:  # pylint: disable=broad-exception-caught
                if self._running:
                    logger.error(
                        f"HTTP server error: {e}",
                        extra={"class_name": self.__class__.__name__},
                        exc_info=True,
                    )

    def _run_expiry_loop(self) -> None:
        """Periodically expire old peers."""
        while self._running:
            try:
                # Sleep for half the announce interval
                time.sleep(self.announce_interval / 2)

                if not self._running:
                    break

                # Expire old peers
                expired = self.peer_database.expire_old_peers()
                if expired > 0:
                    logger.debug(
                        f"Expired {expired} old peers",
                        extra={"class_name": self.__class__.__name__},
                    )

            except Exception as e:  # pylint: disable=broad-exception-caught
                if self._running:
                    logger.error(
                        f"Expiry loop error: {e}",
                        extra={"class_name": self.__class__.__name__},
                        exc_info=True,
                    )

    @property
    def is_running(self) -> bool:
        """Check if the tracker is running."""
        return self._running

    @property
    def uptime(self) -> float:
        """Get uptime in seconds."""
        if self._start_time:
            return time.time() - self._start_time
        return 0

    @property
    def announce_url(self) -> str:
        """Get the full announce URL."""
        return f"http://{self.bind_address}:{self.http_port}/announce"

    def get_stats(self) -> dict:
        """Get tracker statistics."""
        db_stats = self.peer_database.get_database_stats()

        # Get torrent counts from registry (not peer_database which only has active peers)
        all_torrents = self.torrent_registry.get_all_torrents()
        internal_torrents = self.torrent_registry.get_internal_torrents()
        external_torrents = self.torrent_registry.get_external_torrents()

        # Count internal peers - one peer per internal torrent (ourselves)
        internal_peer_count = len(internal_torrents)

        return {
            "running": self._running,
            "uptime": self.uptime,
            "bind_address": self.bind_address,
            "http_port": self.http_port,
            "announce_url": self.announce_url,
            "total_torrents": len(all_torrents),
            "total_peers": db_stats["total_peers"] + internal_peer_count,
            "total_announces": db_stats["total_announces"],
            "announces_sent": self._announces_sent,  # Track local announces
            "internal_torrents": len(internal_torrents),
            "external_torrents": len(external_torrents),
        }

    def register_torrent(
        self,
        info_hash: bytes,
        name: Optional[str] = None,
        total_size: int = 0,
        is_internal: bool = True,
    ) -> None:
        """
        Register a torrent with the tracker.

        Args:
            info_hash: 20-byte torrent info hash
            name: Torrent name
            total_size: Total size in bytes
            is_internal: True if this is DFakeSeeder's own torrent
        """
        self.torrent_registry.register_torrent(
            info_hash=info_hash,
            name=name,
            total_size=total_size,
            is_internal=is_internal,
        )

    def unregister_torrent(self, info_hash: bytes) -> None:
        """
        Unregister a torrent from the tracker.

        Args:
            info_hash: 20-byte torrent info hash
        """
        self.torrent_registry.unregister_torrent(info_hash)
        # Also remove all peers for this torrent
        # pylint: disable=protected-access
        for peer_id in list(self.peer_database._peers.get(info_hash, {}).keys()):
            self.peer_database.remove_peer(info_hash, peer_id)

    def announce_peer(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        info_hash: bytes,
        peer_id: bytes,
        ip: str,
        port: int,
        uploaded: int = 0,
        downloaded: int = 0,
        left: int = 0,
        event: str = "",
        is_internal: bool = True,
    ) -> None:
        """
        Announce a peer directly (for LocalAnnouncer).

        Args:
            info_hash: 20-byte torrent info hash
            peer_id: 20-byte peer identifier
            ip: Peer IP address
            port: Peer listening port
            uploaded: Total bytes uploaded
            downloaded: Total bytes downloaded
            left: Bytes remaining
            event: Event type (started, stopped, completed, or empty)
            is_internal: True if this is DFakeSeeder's own peer
        """
        # Track announce count for all announces (internal or external)
        self._announces_sent += 1

        if event == "stopped":
            self.peer_database.remove_peer(info_hash, peer_id)
        else:
            self.peer_database.add_or_update_peer(
                info_hash=info_hash,
                peer_id=peer_id,
                ip=ip,
                port=port,
                uploaded=uploaded,
                downloaded=downloaded,
                left=left,
                is_internal=is_internal,
            )

            # Update torrent stats
            self.torrent_registry.update_announce(
                info_hash=info_hash,
                uploaded=uploaded,
                downloaded=downloaded,
                completed=(event == "completed"),
            )
