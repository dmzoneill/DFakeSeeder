# fmt: off
# isort: skip_file
"""
UDP Handler for the inbuilt BitTorrent tracker.

Implements BEP 15 (UDP Tracker Protocol).
"""

import random
import socket
import struct
import threading
import time
from typing import Any, Dict, Optional, Tuple

from d_fake_seeder.lib.logger import logger

# fmt: on

# UDP Tracker Protocol Constants (BEP 15)
MAGIC_CONNECTION_ID = 0x41727101980
ACTION_CONNECT = 0
ACTION_ANNOUNCE = 1
ACTION_SCRAPE = 2
ACTION_ERROR = 3

# Events
EVENT_NONE = 0
EVENT_COMPLETED = 1
EVENT_STARTED = 2
EVENT_STOPPED = 3


class UDPTrackerHandler:  # pylint: disable=too-many-instance-attributes
    """
    UDP request handler for BitTorrent tracker requests.

    Implements BEP 15 UDP Tracker Protocol.
    """

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        bind_address: str,
        port: int,
        peer_database: Any,
        torrent_registry: Any,
        announce_interval: int = 1800,
        private_mode: bool = False,
        log_announces: bool = False,
        security: Any = None,
    ) -> None:
        """
        Initialize the UDP handler.

        Args:
            bind_address: Address to bind to
            port: UDP port to listen on
            peer_database: Reference to peer database
            torrent_registry: Reference to torrent registry
            announce_interval: Announce interval in seconds
            private_mode: If True, only pre-registered torrents allowed
            log_announces: If True, log all announce requests
            security: TrackerSecurity instance for IP filtering and rate limiting
        """
        self.bind_address = bind_address
        self.port = port
        self.peer_database = peer_database
        self.torrent_registry = torrent_registry
        self.announce_interval = announce_interval
        self.private_mode = private_mode
        self.log_announces = log_announces
        self.security = security

        self._socket: Optional[socket.socket] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Connection ID cache (for connect protocol)
        self._connection_ids: Dict[Tuple[str, int], Tuple[int, float]] = {}
        self._connection_id_timeout = 120  # 2 minutes

        logger.debug(
            f"UDPTrackerHandler initialized on {bind_address}:{port}",
            extra={"class_name": self.__class__.__name__},
        )

    def start(self) -> bool:
        """Start the UDP handler."""
        if self._running:
            return False

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._socket.bind((self.bind_address, self.port))
            self._socket.settimeout(1.0)  # 1 second timeout for graceful shutdown

            self._running = True
            self._thread = threading.Thread(
                target=self._run,
                name="TrackerUDP",
                daemon=True,
            )
            self._thread.start()

            logger.info(
                f"UDP tracker started on {self.bind_address}:{self.port}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(
                f"Failed to start UDP tracker: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def stop(self) -> None:
        """Stop the UDP handler."""
        self._running = False

        if self._socket:
            try:
                self._socket.close()
            except Exception:  # pylint: disable=broad-exception-caught
                pass
            self._socket = None

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

        logger.info(
            "UDP tracker stopped",
            extra={"class_name": self.__class__.__name__},
        )

    def _run(self) -> None:
        """Main UDP handler loop."""
        while self._running and self._socket:
            try:
                data, addr = self._socket.recvfrom(65535)
                self._handle_request(data, addr)
            except socket.timeout:
                # Clean up expired connection IDs
                self._cleanup_connection_ids()
            except Exception as e:  # pylint: disable=broad-exception-caught
                if self._running:
                    logger.error(
                        f"UDP handler error: {e}",
                        extra={"class_name": self.__class__.__name__},
                        exc_info=True,
                    )

    def _handle_request(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle an incoming UDP request."""
        if len(data) < 16:
            return  # Invalid packet

        # Check security (IP filter and rate limit)
        if self.security:
            allowed, reason = self.security.check_request(addr[0])
            if not allowed:
                # Can't send error without transaction_id, just ignore
                logger.trace(
                    f"UDP request blocked from {addr[0]}: {reason}",
                    extra={"class_name": self.__class__.__name__},
                )
                return

        try:
            connection_id = struct.unpack(">Q", data[0:8])[0]
            action = struct.unpack(">I", data[8:12])[0]
            transaction_id = struct.unpack(">I", data[12:16])[0]

            if action == ACTION_CONNECT:
                self._handle_connect(data, addr, transaction_id)
            elif action == ACTION_ANNOUNCE:
                self._handle_announce(data, addr, connection_id, transaction_id)
            elif action == ACTION_SCRAPE:
                self._handle_scrape(data, addr, connection_id, transaction_id)
            else:
                self._send_error(addr, transaction_id, "Unknown action")

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning(
                f"Error handling UDP request from {addr}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _handle_connect(self, data: bytes, addr: Tuple[str, int], transaction_id: int) -> None:
        """Handle connect request (step 1 of UDP protocol)."""
        if len(data) < 16:
            return

        # Verify magic connection ID
        magic = struct.unpack(">Q", data[0:8])[0]
        if magic != MAGIC_CONNECTION_ID:
            return

        # Generate new connection ID
        connection_id = random.getrandbits(64)
        self._connection_ids[addr] = (connection_id, time.time())

        # Build response
        response = struct.pack(
            ">IIQ",
            ACTION_CONNECT,  # action
            transaction_id,  # transaction_id
            connection_id,  # connection_id
        )

        self._send(addr, response)

        if self.log_announces:
            logger.trace(
                f"UDP connect: {addr[0]}:{addr[1]}",
                extra={"class_name": self.__class__.__name__},
            )

    def _handle_announce(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        self,
        data: bytes,
        addr: Tuple[str, int],
        connection_id: int,
        transaction_id: int,
    ) -> None:
        """Handle announce request."""
        if len(data) < 98:
            self._send_error(addr, transaction_id, "Invalid announce request")
            return

        # Verify connection ID
        if not self._verify_connection_id(addr, connection_id):
            self._send_error(addr, transaction_id, "Invalid connection ID")
            return

        # Parse announce request
        # Format: 8 bytes connection_id, 4 bytes action, 4 bytes transaction_id
        #         20 bytes info_hash, 20 bytes peer_id
        #         8 bytes downloaded, 8 bytes left, 8 bytes uploaded
        #         4 bytes event, 4 bytes IP, 4 bytes key
        #         4 bytes num_want, 2 bytes port
        try:
            offset = 16
            info_hash = data[offset: offset + 20]
            offset += 20
            peer_id = data[offset: offset + 20]
            offset += 20
            downloaded = struct.unpack(">Q", data[offset: offset + 8])[0]
            offset += 8
            left = struct.unpack(">Q", data[offset: offset + 8])[0]
            offset += 8
            uploaded = struct.unpack(">Q", data[offset: offset + 8])[0]
            offset += 8
            event = struct.unpack(">I", data[offset: offset + 4])[0]
            offset += 4
            ip = struct.unpack(">I", data[offset: offset + 4])[0]
            offset += 4
            _ = struct.unpack(">I", data[offset: offset + 4])[0]  # key (unused)
            offset += 4
            num_want = struct.unpack(">i", data[offset: offset + 4])[0]
            offset += 4
            port = struct.unpack(">H", data[offset: offset + 2])[0]

        except struct.error:
            self._send_error(addr, transaction_id, "Invalid announce format")
            return

        # Use client IP if not specified
        if ip == 0:
            client_ip = addr[0]
        else:
            client_ip = socket.inet_ntoa(struct.pack(">I", ip))

        # Check if torrent is allowed
        if not self.torrent_registry.is_allowed(info_hash, self.private_mode):
            self._send_error(addr, transaction_id, "Torrent not registered")
            return

        # Handle event
        event_str = ""
        if event == EVENT_STARTED:
            event_str = "started"
        elif event == EVENT_STOPPED:
            event_str = "stopped"
        elif event == EVENT_COMPLETED:
            event_str = "completed"

        if event_str == "stopped":
            self.peer_database.remove_peer(info_hash, peer_id)
        else:
            self.peer_database.add_or_update_peer(
                info_hash=info_hash,
                peer_id=peer_id,
                ip=client_ip,
                port=port,
                uploaded=uploaded,
                downloaded=downloaded,
                left=left,
                is_internal=False,
            )

            # Register torrent if not in private mode
            if not self.private_mode:
                self.torrent_registry.register_torrent(
                    info_hash=info_hash,
                    is_internal=False,
                )

            # Update torrent stats
            self.torrent_registry.update_announce(
                info_hash=info_hash,
                uploaded=uploaded,
                downloaded=downloaded,
                completed=(event == EVENT_COMPLETED),
            )

        # Get peers to return
        if num_want < 0:
            num_want = 50
        else:
            num_want = min(num_want, 200)

        compact_peers, _ = self.peer_database.get_peers(
            info_hash=info_hash,
            max_peers=num_want,
            exclude_peer_id=peer_id,
            compact=True,
        )

        # Get stats
        stats = self.peer_database.get_stats(info_hash)

        # Build response
        # Format: 4 bytes action, 4 bytes transaction_id, 4 bytes interval
        #         4 bytes leechers, 4 bytes seeders, n*6 bytes peers
        response = struct.pack(
            ">IIIII",
            ACTION_ANNOUNCE,
            transaction_id,
            self.announce_interval,
            stats["incomplete"],  # leechers
            stats["complete"],  # seeders
        )
        response += compact_peers

        self._send(addr, response)

        if self.log_announces:
            logger.trace(
                f"UDP announce: {client_ip}:{port} for " f"{info_hash.hex()[:16]} event={event_str or 'periodic'}",
                extra={"class_name": self.__class__.__name__},
            )

    def _handle_scrape(
        self,
        data: bytes,
        addr: Tuple[str, int],
        connection_id: int,
        transaction_id: int,
    ) -> None:
        """Handle scrape request."""
        # Verify connection ID
        if not self._verify_connection_id(addr, connection_id):
            self._send_error(addr, transaction_id, "Invalid connection ID")
            return

        # Parse info hashes (20 bytes each after header)
        info_hashes = []
        offset = 16
        while offset + 20 <= len(data):
            info_hash = data[offset: offset + 20]
            info_hashes.append(info_hash)
            offset += 20

        # Build response
        response = struct.pack(">II", ACTION_SCRAPE, transaction_id)

        for info_hash in info_hashes:
            stats = self.peer_database.get_stats(info_hash)
            torrent = self.torrent_registry.get_torrent(info_hash)

            # Format per torrent: 4 bytes seeders, 4 bytes completed, 4 bytes leechers
            response += struct.pack(
                ">III",
                stats["complete"],  # seeders
                torrent.times_completed if torrent else 0,  # completed
                stats["incomplete"],  # leechers
            )

        self._send(addr, response)

        if self.log_announces:
            logger.trace(
                f"UDP scrape: {len(info_hashes)} torrents",
                extra={"class_name": self.__class__.__name__},
            )

    def _verify_connection_id(self, addr: Tuple[str, int], connection_id: int) -> bool:
        """Verify a connection ID is valid for this address."""
        if addr not in self._connection_ids:
            return False

        stored_id, timestamp = self._connection_ids[addr]
        if stored_id != connection_id:
            return False

        # Check if connection ID has expired
        if time.time() - timestamp > self._connection_id_timeout:
            del self._connection_ids[addr]
            return False

        return True

    def _cleanup_connection_ids(self) -> None:
        """Remove expired connection IDs."""
        now = time.time()
        expired = [
            addr
            for addr, (_, timestamp) in self._connection_ids.items()
            if now - timestamp > self._connection_id_timeout
        ]
        for addr in expired:
            del self._connection_ids[addr]

    def _send_error(self, addr: Tuple[str, int], transaction_id: int, message: str) -> None:
        """Send an error response."""
        response = struct.pack(">II", ACTION_ERROR, transaction_id)
        response += message.encode()
        self._send(addr, response)

    def _send(self, addr: Tuple[str, int], data: bytes) -> None:
        """Send data to address."""
        if self._socket:
            try:
                self._socket.sendto(data, addr)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(
                    f"Failed to send UDP response to {addr}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
