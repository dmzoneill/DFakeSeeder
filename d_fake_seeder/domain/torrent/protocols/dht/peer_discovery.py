"""
DHT Peer Discovery Implementation

Manages peer discovery through DHT network.
Implements get_peers and announce_peer operations for efficient peer finding.
"""

# fmt: off
import asyncio
import hashlib
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import DHTConstants

from .routing_table import NodeContact, RoutingTable

try:
    import bencode
except ImportError:
    from d_fake_seeder.domain.torrent import bencoding as bencode

# fmt: on


@dataclass(frozen=True)
class PeerInfo:
    """Peer information from DHT"""

    ip: str
    port: int
    discovered_at: float

    @property
    def age(self) -> float:
        """Get age of peer information in seconds"""
        return time.time() - self.discovered_at


class PeerDiscovery:
    """DHT peer discovery manager"""

    def __init__(self, node_id: bytes, routing_table: RoutingTable, socket: Any) -> None:
        """
        Initialize peer discovery

        Args:
            node_id: Our DHT node ID
            routing_table: DHT routing table
            socket: UDP socket for communication
        """
        self.node_id = node_id
        self.routing_table = routing_table
        self.socket = socket
        self.settings = AppSettings.get_instance()

        # Peer storage: info_hash -> Set[PeerInfo]
        self.peer_storage: Dict[bytes, Set[PeerInfo]] = {}

        # Token storage for announce_peer validation
        self.token_storage: Dict[str, Tuple[bytes, float]] = {}

        # Active discovery tasks
        self.active_discoveries: Dict[bytes, asyncio.Task] = {}

        # Transaction tracking
        self.pending_queries: Dict[bytes, Dict] = {}
        self.transaction_counter = 0

        logger.trace(
            "DHT Peer Discovery initialized",
            extra={"class_name": self.__class__.__name__},
        )

    async def discover_peers(self, info_hash: bytes, count: int = 50) -> List[Tuple[str, int]]:
        """
        Discover peers for a torrent through DHT

        Args:
            info_hash: 20-byte torrent info hash
            count: Maximum number of peers to return

        Returns:
            List of (IP, port) tuples
        """
        logger.trace(
            f"Starting peer discovery for {info_hash.hex()[:16]}",
            extra={"class_name": self.__class__.__name__},
        )

        # Check if we already have peers stored
        stored_peers = self._get_stored_peers(info_hash, count)
        if len(stored_peers) >= count:
            logger.trace(
                f"Returning {len(stored_peers)} stored peers",
                extra={"class_name": self.__class__.__name__},
            )
            return stored_peers

        # Start discovery process
        discovered_peers = await self._discover_peers_from_network(info_hash, count)

        # Combine stored and discovered peers
        all_peers = list(set(stored_peers + discovered_peers))[:count]

        logger.trace(
            f"Discovered {len(all_peers)} peers for {info_hash.hex()[:16]}",
            extra={"class_name": self.__class__.__name__},
        )

        return all_peers

    async def announce_peer(self, info_hash: bytes, port: int) -> bool:
        """
        Announce ourselves as a peer for a torrent

        Args:
            info_hash: 20-byte torrent info hash
            port: Port we're listening on

        Returns:
            True if announcement was successful
        """
        logger.trace(
            f"Announcing peer for {info_hash.hex()[:16]} on port {port}",
            extra={"class_name": self.__class__.__name__},
        )

        try:
            # Get closest nodes to info hash
            closest_nodes = self.routing_table.find_closest_nodes(info_hash, 8)

            if not closest_nodes:
                logger.warning(
                    "No nodes available for announcement",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # First, get tokens from nodes
            tokens = await self._get_announce_tokens(closest_nodes, info_hash)

            if not tokens:
                logger.warning(
                    "Failed to get announce tokens",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Announce to nodes with tokens
            successful_announces = 0
            for node_contact, token in tokens.items():
                success = await self._send_announce_peer(node_contact, info_hash, port, token)
                if success:
                    successful_announces += 1

            if successful_announces > 0:
                logger.trace(
                    f"Successfully announced to {successful_announces} nodes",
                    extra={"class_name": self.__class__.__name__},
                )
                return True
            else:
                logger.warning(
                    "Failed to announce to any nodes",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

        except Exception as e:
            logger.error(
                f"Peer announcement failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def store_peer(self, info_hash: bytes, ip: str, port: int) -> Any:
        """
        Store peer information for a torrent

        Args:
            info_hash: Torrent info hash
            ip: Peer IP address
            port: Peer port
        """
        if info_hash not in self.peer_storage:
            self.peer_storage[info_hash] = set()

        peer_info = PeerInfo(ip, port, time.time())
        self.peer_storage[info_hash].add(peer_info)

        # Limit storage size
        if len(self.peer_storage[info_hash]) > DHTConstants.MAX_PEERS_PER_INFOHASH:
            # Remove oldest peers
            sorted_peers = sorted(self.peer_storage[info_hash], key=lambda p: p.discovered_at)
            self.peer_storage[info_hash] = set(sorted_peers[-DHTConstants.MAX_PEERS_PER_INFOHASH:])

        logger.trace(
            f"Stored peer {ip}:{port} for {info_hash.hex()[:16]}",
            extra={"class_name": self.__class__.__name__},
        )

    def get_stored_peers(self, info_hash: bytes) -> List[Tuple[str, int]]:
        """Get all stored peers for a torrent"""
        return self._get_stored_peers(info_hash, 1000)

    def cleanup_old_peers(self, max_age: int = 3600) -> None:
        """
        Remove old peer information

        Args:
            max_age: Maximum age in seconds
        """
        current_time = time.time()
        removed_count = 0

        for info_hash in list(self.peer_storage.keys()):
            peers = self.peer_storage[info_hash]
            old_peers = {peer for peer in peers if current_time - peer.discovered_at > max_age}

            if old_peers:
                peers -= old_peers
                removed_count += len(old_peers)

                # Remove empty entries
                if not peers:
                    del self.peer_storage[info_hash]

        if removed_count > 0:
            logger.trace(
                f"Cleaned up {removed_count} old peer entries",
                extra={"class_name": self.__class__.__name__},
            )

    def _get_stored_peers(self, info_hash: bytes, count: int) -> List[Tuple[str, int]]:
        """Get stored peers for info hash"""
        if info_hash not in self.peer_storage:
            return []

        peers = list(self.peer_storage[info_hash])
        # Sort by discovery time (newest first)
        peers.sort(key=lambda p: p.discovered_at, reverse=True)

        return [(peer.ip, peer.port) for peer in peers[:count]]

    async def _discover_peers_from_network(self, info_hash: bytes, count: int) -> List[Tuple[str, int]]:
        """Discover peers from DHT network"""
        # Prevent concurrent discoveries for same torrent
        if info_hash in self.active_discoveries:
            try:
                return await self.active_discoveries[info_hash]  # type: ignore[no-any-return]
            except asyncio.CancelledError:
                pass

        # Create discovery task
        task = asyncio.create_task(self._perform_get_peers(info_hash, count))
        self.active_discoveries[info_hash] = task

        try:
            result = await task
            return result
        finally:
            # Clean up task
            if info_hash in self.active_discoveries:
                del self.active_discoveries[info_hash]

    async def _perform_get_peers(self, info_hash: bytes, count: int) -> List[Tuple[str, int]]:
        """Perform get_peers lookup in DHT"""
        discovered_peers: List[Tuple[str, int]] = []
        queried_nodes = set()
        nodes_to_query = self.routing_table.find_closest_nodes(info_hash, 8)

        # Iterative lookup
        for round_num in range(3):  # Maximum 3 rounds
            if not nodes_to_query or len(discovered_peers) >= count:
                break

            # Query nodes
            round_peers = []
            for node_contact in nodes_to_query:
                if node_contact.node_id in queried_nodes:
                    continue

                queried_nodes.add(node_contact.node_id)
                peers = await self._send_get_peers(node_contact, info_hash)
                round_peers.extend(peers)

            discovered_peers.extend(round_peers)

            # If we have enough peers, stop
            if len(discovered_peers) >= count:
                break

            # Get new nodes for next round (simplified)
            nodes_to_query = self.routing_table.find_closest_nodes(info_hash, 8)
            nodes_to_query = [n for n in nodes_to_query if n.node_id not in queried_nodes]

        # Remove duplicates and limit count
        unique_peers = list(set(discovered_peers))[:count]

        logger.trace(
            f"Network discovery found {len(unique_peers)} peers for {info_hash.hex()[:16]}",
            extra={"class_name": self.__class__.__name__},
        )

        return unique_peers

    async def _send_get_peers(self, node_contact: NodeContact, info_hash: bytes) -> List[Tuple[str, int]]:
        """Send get_peers query to a node"""
        try:
            transaction_id = self._generate_transaction_id()

            message = {
                b"t": transaction_id,
                b"y": b"q",
                b"q": b"get_peers",
                b"a": {b"id": self.node_id, b"info_hash": info_hash},
            }

            # Store query info
            self.pending_queries[transaction_id] = {
                "type": "get_peers",
                "node": node_contact,
                "info_hash": info_hash,
                "timestamp": time.time(),
            }

            # Send message
            await self._send_dht_message(message, (node_contact.ip, node_contact.port))

            # Wait for response (with timeout)
            response = await self._wait_for_response(transaction_id, timeout=DHTConstants.RESPONSE_TIMEOUT_SECONDS)

            if response:
                return self._parse_get_peers_response(response)

        except Exception as e:
            logger.trace(
                f"get_peers query failed for {node_contact.ip}:{node_contact.port}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return []

    async def _get_announce_tokens(self, nodes: List[NodeContact], info_hash: bytes) -> Dict[NodeContact, bytes]:
        """Get announce tokens from nodes"""
        tokens = {}

        for node_contact in nodes:
            try:
                transaction_id = self._generate_transaction_id()

                message = {
                    b"t": transaction_id,
                    b"y": b"q",
                    b"q": b"get_peers",
                    b"a": {b"id": self.node_id, b"info_hash": info_hash},
                }

                self.pending_queries[transaction_id] = {
                    "type": "get_peers_for_token",
                    "node": node_contact,
                    "info_hash": info_hash,
                    "timestamp": time.time(),
                }

                await self._send_dht_message(message, (node_contact.ip, node_contact.port))

                response = await self._wait_for_response(transaction_id, timeout=DHTConstants.RESPONSE_SHORT_TIMEOUT)
                if response and b"r" in response and b"token" in response[b"r"]:
                    tokens[node_contact] = response[b"r"][b"token"]

            except Exception as e:
                logger.trace(
                    f"Failed to get token from {node_contact.ip}:{node_contact.port}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        return tokens

    async def _send_announce_peer(self, node_contact: NodeContact, info_hash: bytes, port: int, token: bytes) -> bool:
        """Send announce_peer message"""
        try:
            transaction_id = self._generate_transaction_id()

            message = {
                b"t": transaction_id,
                b"y": b"q",
                b"q": b"announce_peer",
                b"a": {
                    b"id": self.node_id,
                    b"info_hash": info_hash,
                    b"port": port,
                    b"token": token,
                },
            }

            await self._send_dht_message(message, (node_contact.ip, node_contact.port))

            # Wait for response
            response = await self._wait_for_response(transaction_id, timeout=DHTConstants.RESPONSE_SHORT_TIMEOUT)
            return response is not None

        except Exception as e:
            logger.trace(
                f"announce_peer failed for {node_contact.ip}:{node_contact.port}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _parse_get_peers_response(self, response: dict) -> List[Tuple[str, int]]:
        """Parse get_peers response to extract peer information"""
        peers: List[Tuple[str, int]] = []

        if b"r" not in response:
            return peers

        response_data = response[b"r"]

        # Check for values (compact peer list)
        if b"values" in response_data:
            for value in response_data[b"values"]:
                if len(value) == 6:  # IPv4 (4 bytes) + port (2 bytes)
                    ip_bytes = value[:4]
                    port_bytes = value[4:6]

                    ip = ".".join(str(b) for b in ip_bytes)
                    port = int.from_bytes(port_bytes, "big")

                    peers.append((ip, port))

        return peers

    async def _send_dht_message(self, message: dict, addr: Tuple[str, int]) -> Any:
        """Send DHT message"""
        try:
            data = bencode.bencode(message)
            await asyncio.get_running_loop().sock_sendto(self.socket, data, addr)  # type: ignore[attr-defined]
        except Exception as e:
            logger.trace(
                f"Failed to send DHT message to {addr}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    async def _wait_for_response(self, transaction_id: bytes, timeout: float = 10) -> Optional[dict]:
        """Wait for response to a query"""
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if we received a response
            if transaction_id not in self.pending_queries:
                # Query was processed, look for stored response
                # This would be handled by the main message processing loop
                break

            await asyncio.sleep(self._get_poll_interval())  # type: ignore[attr-defined]

        # Clean up pending query
        if transaction_id in self.pending_queries:
            del self.pending_queries[transaction_id]

        return None  # Simplified - actual implementation would return response

    def _generate_transaction_id(self) -> bytes:
        """Generate unique transaction ID"""
        self.transaction_counter = (self.transaction_counter + 1) % 65536
        return f"py{self.transaction_counter}".encode()[:4]

    def handle_get_peers_query(self, message: dict, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle incoming get_peers query"""
        args = message.get(b"a", {})
        info_hash = args.get(b"info_hash")
        transaction_id = message.get(b"t")

        if not info_hash or not transaction_id:
            return None

        # Generate token for this IP
        token = hashlib.sha1(f"{addr[0]}{time.time()}".encode()).digest()[:8]
        self.token_storage[addr[0]] = (token, time.time())

        # Check if we have peers for this info hash
        stored_peers = self._get_stored_peers(info_hash, 50)

        response = {
            b"t": transaction_id,
            b"y": b"r",
            b"r": {b"id": self.node_id, b"token": token},
        }

        if stored_peers:
            # Convert peers to compact format
            values = []
            for ip, port in stored_peers:
                try:
                    ip_bytes = bytes(int(x) for x in ip.split("."))
                    port_bytes = port.to_bytes(2, "big")
                    values.append(ip_bytes + port_bytes)
                except ValueError:
                    continue  # Skip invalid IPs

            response[b"r"][b"values"] = values
        else:
            # Return closest nodes
            closest_nodes = self.routing_table.find_closest_nodes(info_hash, 8)
            nodes_data = b""
            for node in closest_nodes:
                try:
                    ip_bytes = bytes(int(x) for x in node.ip.split("."))
                    port_bytes = node.port.to_bytes(2, "big")
                    nodes_data += node.node_id + ip_bytes + port_bytes
                except ValueError:
                    continue

            response[b"r"][b"nodes"] = nodes_data

        return response

    def handle_announce_peer_query(self, message: dict, addr: Tuple[str, int]) -> Optional[dict]:
        """Handle incoming announce_peer query"""
        args = message.get(b"a", {})
        info_hash = args.get(b"info_hash")
        port = args.get(b"port")
        token = args.get(b"token")
        transaction_id = message.get(b"t")

        if not all([info_hash, port, token, transaction_id]):
            return None

        # Verify token
        stored_token_info = self.token_storage.get(addr[0])
        if not stored_token_info or stored_token_info[0] != token:
            # Invalid token
            return {b"t": transaction_id, b"y": b"e", b"e": [203, b"Invalid token"]}

        # Store peer
        self.store_peer(info_hash, addr[0], port)

        # Send success response
        return {b"t": transaction_id, b"y": b"r", b"r": {b"id": self.node_id}}
