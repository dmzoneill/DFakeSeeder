"""
DHT (Distributed Hash Table) Manager

Implements BitTorrent DHT (BEP 5) for decentralized peer discovery.
Uses a background thread with UDP socket for DHT protocol communication.
"""

# fmt: off
import hashlib
import random
import socket
import struct
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    import bencodepy
except ImportError:
    bencodepy = None

from d_fake_seeder.lib.logger import logger

# fmt: on


class DHTManager:
    """
    Manages DHT peer discovery for torrents.

    Threading Model:
    - Single background thread with UDP socket select() loop
    - Thread-safe torrent registration/unregistration
    - Callback to add discovered peers to torrents
    """

    # DHT Bootstrap nodes (public DHT routers)
    BOOTSTRAP_NODES = [
        ("router.bittorrent.com", 6881),
        ("dht.transmissionbt.com", 6881),
        ("router.utorrent.com", 6881),
    ]

    # DHT Protocol constants
    DHT_PORT = 6881
    NODE_ID_LENGTH = 20
    ROUTING_TABLE_K = 8  # K-bucket size
    TOKEN_LENGTH = 4

    def __init__(self, port: int = DHT_PORT, peer_callback: Optional[Callable] = None) -> None:
        """
        Initialize DHT manager.

        Args:
            port: UDP port for DHT communication
            peer_callback: Callback function(info_hash, peers) when peers are discovered
        """
        self.port = port
        self.peer_callback = peer_callback

        # Generate random node ID
        self.node_id = self._generate_node_id()

        # Registered torrents (info_hash -> torrent object)
        self.torrents: Dict[bytes, object] = {}
        self.lock = threading.Lock()

        # DHT routing table (simplified - store all nodes in one bucket)
        self.routing_table: List[Tuple[bytes, str, int]] = []  # (node_id, ip, port)
        self.routing_table_lock = threading.Lock()

        # UDP socket
        self.socket: Optional[socket.socket] = None

        # Thread management
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # DHT state
        self.transaction_id_counter = 0
        self.pending_transactions: Dict[bytes, dict] = {}  # transaction_id -> request_info

        # Timing
        self.last_bootstrap = 0.0
        self.bootstrap_interval = 300.0  # Re-bootstrap every 5 minutes
        self.last_announce = 0.0
        self.announce_interval = 600.0  # Announce every 10 minutes

        logger.trace(f"DHT Manager initialized on port {port} with node ID: {self.node_id.hex()[:16]}...")

    def _get_poll_interval(self) -> Any:
        """Get poll interval from settings."""
        dht_config = getattr(self.settings, "dht_manager", {})  # type: ignore[attr-defined]
        if isinstance(dht_config, dict):
            return dht_config.get("poll_interval_seconds", 0.1)
        return 0.1

    def _get_error_retry_interval(self) -> Any:
        """Get error retry interval from settings."""
        dht_config = getattr(self.settings, "dht_manager", {})  # type: ignore[attr-defined]
        if isinstance(dht_config, dict):
            return dht_config.get("error_retry_interval_seconds", 1.0)
        return 1.0

    def _generate_node_id(self) -> bytes:
        """Generate random 20-byte node ID"""
        return hashlib.sha1(str(random.random()).encode()).digest()

    def start(self) -> Any:
        """Start DHT manager background thread"""
        if self.running:
            logger.warning("DHT Manager already running")
            return

        if not bencodepy:
            logger.warning("bencodepy not available, DHT disabled")
            return

        try:
            # Create UDP socket
            from d_fake_seeder.lib.util.network import get_bind_tuple

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(get_bind_tuple(self.port))
            self.socket.settimeout(1.0)  # 1 second timeout for select()

            self.running = True
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._dht_loop, name="DHTManager", daemon=True)
            self.thread.start()

            logger.info(f"DHT Manager started on port {self.port}")

        except Exception as e:
            logger.error(f"Failed to start DHT Manager: {e}", exc_info=True)
            self.running = False

    def stop(self) -> Any:
        """Stop DHT manager background thread"""
        if not self.running:
            return

        logger.info("Stopping DHT Manager...")
        self.running = False
        self.stop_event.set()

        # Join thread with timeout
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
            if self.thread.is_alive():
                logger.warning("DHT Manager thread still alive after timeout")

        # Close socket
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass

        logger.info("DHT Manager stopped")

    def register_torrent(self, info_hash: bytes, torrent: object) -> None:
        """
        Register a torrent for DHT peer discovery.

        Args:
            info_hash: 20-byte torrent info hash
            torrent: Torrent object
        """
        with self.lock:
            self.torrents[info_hash] = torrent
            logger.trace(f"Registered torrent {info_hash.hex()[:16]}... for DHT discovery")

    def unregister_torrent(self, info_hash: bytes) -> None:
        """Unregister a torrent from DHT discovery"""
        with self.lock:
            if info_hash in self.torrents:
                del self.torrents[info_hash]
                logger.trace(f"Unregistered torrent {info_hash.hex()[:16]}... from DHT")

    def _dht_loop(self) -> Any:
        """Main DHT thread loop"""
        logger.trace("DHT loop started")

        while self.running and not self.stop_event.is_set():
            try:
                current_time = time.time()

                # Bootstrap DHT if needed
                if current_time - self.last_bootstrap >= self.bootstrap_interval:
                    self._bootstrap()
                    self.last_bootstrap = current_time

                # Announce torrents periodically
                if current_time - self.last_announce >= self.announce_interval:
                    self._announce_torrents()
                    self.last_announce = current_time

                # Receive DHT messages
                self._receive_messages()

                # Small sleep to prevent CPU spinning
                time.sleep(self._get_poll_interval())

            except Exception as e:
                logger.error(f"Error in DHT loop: {e}", exc_info=True)
                time.sleep(self._get_error_retry_interval())

        logger.trace("DHT loop stopped")

    def _bootstrap(self) -> Any:
        """Bootstrap DHT by contacting known nodes"""
        logger.trace("Bootstrapping DHT...")

        for host, port in self.BOOTSTRAP_NODES:
            try:
                # Send find_node query for our own ID (to discover nearby nodes)
                self._send_find_node(host, port, self.node_id)
            except Exception as e:
                logger.trace(f"Failed to bootstrap from {host}:{port}: {e}")

    def _announce_torrents(self) -> Any:
        """Announce all registered torrents to DHT"""
        with self.lock:
            torrent_count = len(self.torrents)

        if torrent_count > 0:
            logger.trace(f"Announcing {torrent_count} torrents to DHT")

        # For now, just log - full implementation would send get_peers/announce_peer messages

    def _receive_messages(self) -> Any:
        """Receive and process DHT messages"""
        if not self.socket:
            return

        try:
            data, addr = self.socket.recvfrom(4096)
            self._handle_message(data, addr)
        except socket.timeout:
            pass  # Normal timeout, continue loop
        except Exception as e:
            logger.trace(f"Error receiving DHT message: {e}")

    def _handle_message(self, data: bytes, addr: Tuple[str, int]) -> None:
        """Handle incoming DHT message"""
        if not bencodepy:
            return

        try:
            message = bencodepy.decode(data)
            logger.trace(f"Received DHT message from {addr}: {message}")

            # Handle different message types (query, response, error)
            msg_type = message.get(b"y", b"")

            if msg_type == b"r":
                # Response message
                self._handle_response(message, addr)
            elif msg_type == b"q":
                # Query message
                self._handle_query(message, addr)
            elif msg_type == b"e":
                # Error message
                logger.trace(f"DHT error from {addr}: {message.get(b'e', b'')}")

        except Exception as e:
            logger.trace(f"Failed to parse DHT message from {addr}: {e}")

    def _handle_response(self, message: dict, addr: Tuple[str, int]) -> None:
        """Handle DHT response message"""
        # Add responding node to routing table
        if b"r" in message and b"id" in message[b"r"]:
            node_id = message[b"r"][b"id"]
            self._add_node(node_id, addr[0], addr[1])

        # Handle get_peers response
        if b"r" in message and b"values" in message[b"r"]:
            peers = message[b"r"][b"values"]
            logger.trace(f"Received {len(peers)} peers from DHT")

            # TODO: Parse peer addresses and call peer_callback

    def _handle_query(self, message: dict, addr: Tuple[str, int]) -> None:
        """Handle DHT query message"""
        # Respond to ping, find_node, get_peers queries
        # For now, just acknowledge
        pass

    def _send_find_node(self, host: str, port: int, target: bytes) -> Any:
        """Send find_node query"""
        if not bencodepy or not self.socket:
            return

        transaction_id = self._get_transaction_id()

        query = {
            b"t": transaction_id,
            b"y": b"q",
            b"q": b"find_node",
            b"a": {
                b"id": self.node_id,
                b"target": target,
            },
        }

        try:
            data = bencodepy.encode(query)
            self.socket.sendto(data, (host, port))
            logger.trace(f"Sent find_node to {host}:{port}")
        except Exception as e:
            logger.trace(f"Failed to send find_node to {host}:{port}: {e}")

    def _add_node(self, node_id: bytes, ip: str, port: int) -> Any:
        """Add node to routing table"""
        with self.routing_table_lock:
            # Simple implementation: keep last N nodes
            node_tuple = (node_id, ip, port)

            if node_tuple not in self.routing_table:
                self.routing_table.append(node_tuple)

                # Limit routing table size
                if len(self.routing_table) > 100:
                    self.routing_table.pop(0)

                logger.trace(f"Added DHT node: {node_id.hex()[:16]}... at {ip}:{port}")

    def _get_transaction_id(self) -> bytes:
        """Generate transaction ID for DHT messages"""
        self.transaction_id_counter += 1
        return struct.pack("!H", self.transaction_id_counter % 65536)

    def get_stats(self) -> dict:
        """Get DHT statistics"""
        with self.routing_table_lock:
            routing_table_size = len(self.routing_table)

        with self.lock:
            torrent_count = len(self.torrents)

        return {
            "running": self.running,
            "port": self.port,
            "node_id": self.node_id.hex(),
            "routing_table_size": routing_table_size,
            "registered_torrents": torrent_count,
        }
