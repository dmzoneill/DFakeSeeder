"""
DHT Node Implementation (BEP-005)

Implements a Kademlia-based DHT node for BitTorrent peer discovery.
Supports trackerless operation and distributed peer storage.
"""

import asyncio
import hashlib
import random
import socket
import struct
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from domain.app_settings import AppSettings
from lib.logger import logger

from .peer_discovery import PeerDiscovery
from .routing_table import RoutingTable

try:
    import bencode
except ImportError:
    from domain.torrent.bencoding import bencode


class DHTNode:
    """DHT node implementation for peer discovery and announcement"""

    def __init__(self, node_id: Optional[bytes] = None, port: int = 6881):
        """
        Initialize DHT node

        Args:
            node_id: 20-byte node identifier (auto-generated if None)
            port: UDP port for DHT communication
        """
        self.node_id = node_id or self._generate_node_id()
        self.port = port
        self.settings = AppSettings.get_instance()

        # DHT configuration from settings
        dht_config = getattr(self.settings, "protocols", {}).get("dht", {})
        self.enabled = dht_config.get("enabled", True)
        self.routing_table_size = dht_config.get("routing_table_size", 160)
        self.announcement_interval = dht_config.get("announcement_interval", 1800)

        # Network state
        self.socket = None
        self.running = False
        self.bootstrap_nodes = [
            ("router.bittorrent.com", 6881),
            ("dht.transmissionbt.com", 6881),
            ("router.utorrent.com", 6881),
        ]

        # DHT data structures
        self.routing_table = RoutingTable(self.node_id)
        self.peer_discovery = None  # Will be initialized after socket creation
        self.token_storage: Dict[str, Tuple[bytes, float]] = {}  # IP -> (token, timestamp) mapping for announce_peer
        self.pending_queries: Dict[bytes, Dict[str, Any]] = {}  # Transaction ID -> query info

        # Transaction ID counter
        self.transaction_id = 0

        # Active announcements
        self.announced_torrents: Set[bytes] = set()

        logger.info(
            "DHT Node initialized",
            extra={"class_name": self.__class__.__name__, "node_id": self.node_id.hex()[:16], "port": self.port},
        )

    def _generate_node_id(self) -> bytes:
        """Generate a random 20-byte node ID"""
        return hashlib.sha1(str(random.getrandbits(160)).encode()).digest()

    async def start(self):
        """Start the DHT node"""
        if not self.enabled:
            logger.info("DHT disabled in settings", extra={"class_name": self.__class__.__name__})
            return

        logger.info("Starting DHT node", extra={"class_name": self.__class__.__name__})

        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.setblocking(False)

            self.running = True

            # Initialize peer discovery with socket
            self.peer_discovery = PeerDiscovery(self.node_id, self.routing_table, self.socket)

            # Start background tasks
            asyncio.create_task(self._listen_loop())
            asyncio.create_task(self._bootstrap())
            asyncio.create_task(self._maintenance_loop())

            logger.info("DHT node started successfully", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(f"Failed to start DHT node: {e}", extra={"class_name": self.__class__.__name__})
            self.running = False

    async def stop(self):
        """Stop the DHT node"""
        logger.info("Stopping DHT node", extra={"class_name": self.__class__.__name__})
        self.running = False

        if self.socket:
            self.socket.close()
            self.socket = None

    async def announce_peer(self, info_hash: bytes, port: int) -> bool:
        """
        Announce ourselves as a peer for a torrent

        Args:
            info_hash: 20-byte torrent info hash
            port: Port we're listening on for this torrent

        Returns:
            True if announcement was successful
        """
        if not self.running:
            return False

        logger.info(
            f"Announcing peer for torrent {info_hash.hex()[:16]}", extra={"class_name": self.__class__.__name__}
        )

        try:
            # Use peer discovery for announcement
            if not self.peer_discovery:
                return False
            success = await self.peer_discovery.announce_peer(info_hash, port)

            if success:
                self.announced_torrents.add(info_hash)
                logger.info(
                    f"Successfully announced peer for {info_hash.hex()[:16]}",
                    extra={"class_name": self.__class__.__name__},
                )
                return True
            else:
                logger.warning("Failed to announce to DHT nodes", extra={"class_name": self.__class__.__name__})
                return False

        except Exception as e:
            logger.error(f"DHT announcement failed: {e}", extra={"class_name": self.__class__.__name__})
            return False

    async def get_peers(self, info_hash: bytes) -> List[Tuple[str, int]]:
        """
        Find peers for a torrent via DHT

        Args:
            info_hash: 20-byte torrent info hash

        Returns:
            List of (IP, port) tuples for peers
        """
        if not self.running:
            return []

        logger.debug(f"Finding peers for torrent {info_hash.hex()[:16]}", extra={"class_name": self.__class__.__name__})

        try:
            # Use peer discovery for finding peers
            if not self.peer_discovery:
                return []
            peers = await self.peer_discovery.discover_peers(info_hash, 50)

            logger.debug(f"Found {len(peers)} peers via DHT", extra={"class_name": self.__class__.__name__})

            return peers

        except Exception as e:
            logger.error(f"DHT peer query failed: {e}", extra={"class_name": self.__class__.__name__})
            return []

    async def _listen_loop(self):
        """Main listening loop for DHT messages"""
        while self.running:
            try:
                # Receive DHT message
                data, addr = await asyncio.get_event_loop().sock_recvfrom(self.socket, 1024)

                # Process message in background
                asyncio.create_task(self._handle_message(data, addr))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"DHT listen error: {e}", extra={"class_name": self.__class__.__name__})
                await asyncio.sleep(1)

    async def _handle_message(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming DHT message"""
        try:
            message = bencode.bdecode(data)

            if b"y" not in message:
                return

            message_type = message[b"y"]

            if message_type == b"q":  # Query
                await self._handle_query(message, addr)
            elif message_type == b"r":  # Response
                await self._handle_response(message, addr)
            elif message_type == b"e":  # Error
                await self._handle_error(message, addr)

        except Exception as e:
            logger.debug(
                f"Failed to decode DHT message from {addr}: {e}", extra={"class_name": self.__class__.__name__}
            )

    async def _handle_query(self, message: dict, addr: Tuple[str, int]):
        """Handle DHT query message"""
        try:
            query_type = message.get(b"q")
            transaction_id = message.get(b"t")

            if not transaction_id:
                return

            if query_type == b"ping":
                await self._send_ping_response(transaction_id, addr)
            elif query_type == b"find_node":
                await self._send_find_node_response(message, transaction_id, addr)
            elif query_type == b"get_peers":
                if self.peer_discovery:
                    response = self.peer_discovery.handle_get_peers_query(message, addr)
                    if response:
                        await self._send_message(response, addr)
            elif query_type == b"announce_peer":
                if self.peer_discovery:
                    response = self.peer_discovery.handle_announce_peer_query(message, addr)
                    if response:
                        await self._send_message(response, addr)

        except Exception as e:
            logger.debug(f"Failed to handle DHT query: {e}", extra={"class_name": self.__class__.__name__})

    async def _send_ping_response(self, transaction_id: bytes, addr: Tuple[str, int]):
        """Send ping response"""
        response = {b"t": transaction_id, b"y": b"r", b"r": {b"id": self.node_id}}
        await self._send_message(response, addr)

    async def _send_message(self, message: dict, addr: Tuple[str, int]):
        """Send DHT message"""
        try:
            if not self.socket:
                return
            data = bencode.bencode(message)
            await asyncio.get_event_loop().sock_sendto(self.socket, data, addr)
        except Exception as e:
            logger.debug(f"Failed to send DHT message to {addr}: {e}", extra={"class_name": self.__class__.__name__})

    async def _bootstrap(self):
        """Bootstrap the DHT by connecting to known nodes"""
        logger.info("Bootstrapping DHT", extra={"class_name": self.__class__.__name__})

        for host, port in self.bootstrap_nodes:
            try:
                # Resolve hostname and ping
                addr = (socket.gethostbyname(host), port)
                await self._send_ping(addr)
                await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                logger.debug(f"Bootstrap failed for {host}:{port}: {e}", extra={"class_name": self.__class__.__name__})

    async def _send_ping(self, addr: Tuple[str, int]):
        """Send ping query to a node"""
        transaction_id = self._get_transaction_id()
        message = {b"t": transaction_id, b"y": b"q", b"q": b"ping", b"a": {b"id": self.node_id}}
        await self._send_message(message, addr)

    def _get_transaction_id(self) -> bytes:
        """Generate unique transaction ID"""
        self.transaction_id = (self.transaction_id + 1) % 65536
        return struct.pack(">H", self.transaction_id)

    async def _maintenance_loop(self):
        """Periodic maintenance tasks"""
        while self.running:
            try:
                # Re-announce torrents
                for info_hash in list(self.announced_torrents):
                    await self.announce_peer(info_hash, self.port)

                # Clean up old data
                self._cleanup_old_data()
                self.routing_table.cleanup_stale_nodes()
                self.peer_discovery.cleanup_old_peers()

                # Wait for next maintenance cycle
                await asyncio.sleep(self.announcement_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"DHT maintenance error: {e}", extra={"class_name": self.__class__.__name__})

    def _cleanup_old_data(self):
        """Clean up old DHT data"""
        current_time = time.time()

        # Clean up old tokens (expire after 10 minutes)
        expired_tokens = [ip for ip, (token, timestamp) in self.token_storage.items() if current_time - timestamp > 600]
        for ip in expired_tokens:
            del self.token_storage[ip]

    async def _find_nodes(self, target_id: bytes) -> List[Tuple[str, int]]:
        """Find nodes closest to target ID"""
        # Simplified implementation - in real DHT this would be more complex
        return [(node[0], node[1]) for node in self.bootstrap_nodes]

    async def _query_peers(self, info_hash: bytes) -> List[Tuple[str, int]]:
        """Query DHT for peers of a torrent"""
        # Simplified implementation - return empty list for now
        # In real implementation, this would query closest nodes
        return []

    async def _send_announce_peer(self, node_addr: Tuple[str, int], info_hash: bytes, port: int) -> bool:
        """Send announce_peer message to a DHT node"""
        try:
            transaction_id = self._get_transaction_id()

            # Generate token (simplified)
            token = hashlib.sha1(f"{node_addr[0]}{time.time()}".encode()).digest()[:8]

            message = {
                b"t": transaction_id,
                b"y": b"q",
                b"q": b"announce_peer",
                b"a": {b"id": self.node_id, b"info_hash": info_hash, b"port": port, b"token": token},
            }

            await self._send_message(message, node_addr)
            return True

        except Exception as e:
            logger.debug(
                f"Failed to send announce_peer to {node_addr}: {e}", extra={"class_name": self.__class__.__name__}
            )
            return False

    async def _handle_response(self, message: dict, addr: Tuple[str, int]):
        """Handle DHT response message"""
        # Add to routing table
        response_data = message.get(b"r", {})
        node_id = response_data.get(b"id")
        if node_id:
            self.routing_table.add_node(node_id, addr[0], addr[1])
            self.routing_table.mark_node_good(node_id)

    async def _handle_error(self, message: dict, addr: Tuple[str, int]):
        """Handle DHT error message"""
        error_info = message.get(b"e", [])
        if len(error_info) >= 2:
            error_code, error_msg = error_info[0], error_info[1]
            logger.debug(
                f"DHT error from {addr}: {error_code} - {error_msg}", extra={"class_name": self.__class__.__name__}
            )

    def _add_node_to_routing_table(self, node_id: bytes, addr: Tuple[str, int]):
        """Add node to routing table"""
        # Simplified routing table - just store recent nodes
        if self.routing_table.get_node_count() < 100:  # Limit size
            self.routing_table.add_node(node_id, addr[0], addr[1])

    async def _send_find_node_response(self, message: dict, transaction_id: bytes, addr: Tuple[str, int]):
        """Send find_node response"""
        # Simplified implementation
        response = {b"t": transaction_id, b"y": b"r", b"r": {b"id": self.node_id, b"nodes": b""}}  # Empty nodes list
        await self._send_message(response, addr)

    async def _send_get_peers_response(self, message: dict, transaction_id: bytes, addr: Tuple[str, int]):
        """Send get_peers response"""
        # Generate token for potential announce_peer
        token = hashlib.sha1(f"{addr[0]}{time.time()}".encode()).digest()[:8]
        self.token_storage[addr[0]] = (token, time.time())

        response = {
            b"t": transaction_id,
            b"y": b"r",
            b"r": {b"id": self.node_id, b"token": token, b"nodes": b""},  # Empty nodes list - no peers stored
        }
        await self._send_message(response, addr)

    async def _handle_announce_peer(self, message: dict, transaction_id: bytes, addr: Tuple[str, int]):
        """Handle announce_peer query"""
        # Send success response
        response = {b"t": transaction_id, b"y": b"r", b"r": {b"id": self.node_id}}
        await self._send_message(response, addr)
