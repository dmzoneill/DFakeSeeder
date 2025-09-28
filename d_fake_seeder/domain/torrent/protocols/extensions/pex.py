"""
Peer Exchange Extension (BEP-011)

Implements the Peer Exchange extension that allows peers to exchange
information about other peers in the swarm without relying on trackers.
"""

import random
import socket
import struct
import time
from typing import List, Set, Tuple

from domain.app_settings import AppSettings
from lib.logger import logger

try:
    import bencode
except ImportError:
    from domain.torrent.bencoding import bencode


class PeerExchangeExtension:
    """Peer Exchange (PEX) extension implementation"""

    def __init__(self, extension_manager, peer_connection):
        """
        Initialize PEX extension

        Args:
            extension_manager: ExtensionManager instance
            peer_connection: PeerConnection instance
        """
        self.extension_manager = extension_manager
        self.peer_connection = peer_connection
        self.settings = AppSettings.get_instance()

        # PEX configuration
        pex_config = getattr(self.settings, "protocols", {}).get("pex", {})
        self.pex_interval = pex_config.get("interval", 60)  # Send PEX every 60 seconds
        self.max_peers_per_message = pex_config.get("max_peers_per_message", 50)
        self.max_dropped_peers = pex_config.get("max_dropped_peers", 20)

        # PEX state
        self.known_peers: Set[Tuple[str, int]] = set()
        self.sent_peers: Set[Tuple[str, int]] = set()
        self.last_pex_time = 0
        self.peer_flags = {}  # Store peer flags (encryption support, etc.)

        # Synthetic peer generation for fake seeding
        self.generate_synthetic_peers = pex_config.get("generate_synthetic_peers", True)
        self.synthetic_peer_count = pex_config.get("synthetic_peer_count", 20)

        logger.debug(
            "PEX extension initialized",
            extra={"class_name": self.__class__.__name__, "pex_interval": self.pex_interval},
        )

    def initialize(self):
        """Initialize PEX extension after handshake"""
        # Start PEX message sending
        self.last_pex_time = time.time()

        # Generate initial synthetic peers for fake seeding
        if self.generate_synthetic_peers:
            self._generate_synthetic_peers()

        logger.debug("PEX extension initialized and ready", extra={"class_name": self.__class__.__name__})

    def handle_message(self, payload: bytes):
        """
        Handle incoming PEX message

        Args:
            payload: PEX message payload
        """
        try:
            pex_data = bencode.bdecode(payload)

            # Extract peer data
            peers_data = pex_data.get(b"added", b"")
            peers_flags = pex_data.get(b"added.f", b"")
            dropped_peers = pex_data.get(b"dropped", b"")

            # Process added peers
            added_peers = self._decode_peers(peers_data)
            if added_peers:
                self._process_added_peers(added_peers, peers_flags)

            # Process dropped peers
            dropped_peer_list = []
            if dropped_peers:
                dropped_peer_list = self._decode_peers(dropped_peers)
                self._process_dropped_peers(dropped_peer_list)

            logger.debug(
                f"Processed PEX message: {len(added_peers)} added, " f"{len(dropped_peer_list)} dropped",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(f"Failed to handle PEX message: {e}", extra={"class_name": self.__class__.__name__})

    def send_pex_message(self, force: bool = False):
        """
        Send PEX message to peer

        Args:
            force: Force sending even if interval hasn't elapsed
        """
        current_time = time.time()

        # Check if it's time to send PEX
        if not force and current_time - self.last_pex_time < self.pex_interval:
            return

        try:
            # Select peers to send
            peers_to_send = self._select_peers_to_send()
            dropped_peers = self._select_dropped_peers()

            if not peers_to_send and not dropped_peers:
                return  # Nothing to send

            # Build PEX message
            pex_data = {}

            if peers_to_send:
                peers_data, flags_data = self._encode_peers(peers_to_send)
                pex_data[b"added"] = peers_data
                if flags_data:
                    pex_data[b"added.f"] = flags_data

            if dropped_peers:
                dropped_data, _ = self._encode_peers(dropped_peers)
                pex_data[b"dropped"] = dropped_data

            # Encode and send
            payload = bencode.bencode(pex_data)
            success = self.extension_manager.send_extended_message("ut_pex", payload)

            if success:
                self.last_pex_time = current_time
                # Update sent peers tracking
                self.sent_peers.update(peers_to_send)

                logger.debug(
                    f"Sent PEX message: {len(peers_to_send)} added, " f"{len(dropped_peers)} dropped",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.debug("Failed to send PEX message", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(f"Failed to send PEX message: {e}", extra={"class_name": self.__class__.__name__})

    def add_peer(self, ip: str, port: int, flags: int = 0):
        """
        Add a peer to the known peers list

        Args:
            ip: Peer IP address
            port: Peer port
            flags: Peer flags (encryption support, etc.)
        """
        peer_tuple = (ip, port)
        if peer_tuple not in self.known_peers:
            self.known_peers.add(peer_tuple)
            self.peer_flags[peer_tuple] = flags

            logger.debug(f"Added peer to PEX: {ip}:{port}", extra={"class_name": self.__class__.__name__})

    def remove_peer(self, ip: str, port: int):
        """
        Remove a peer from known peers

        Args:
            ip: Peer IP address
            port: Peer port
        """
        peer_tuple = (ip, port)
        self.known_peers.discard(peer_tuple)
        self.peer_flags.pop(peer_tuple, None)

        logger.debug(f"Removed peer from PEX: {ip}:{port}", extra={"class_name": self.__class__.__name__})

    def _decode_peers(self, peers_data: bytes) -> List[Tuple[str, int]]:
        """
        Decode compact peer format

        Args:
            peers_data: Compact peer data (6 bytes per peer)

        Returns:
            List of (IP, port) tuples
        """
        peers = []
        try:
            for i in range(0, len(peers_data), 6):
                if i + 6 <= len(peers_data):
                    ip_bytes = peers_data[i : i + 4]
                    port_bytes = peers_data[i + 4 : i + 6]

                    ip = socket.inet_ntoa(ip_bytes)
                    port = struct.unpack(">H", port_bytes)[0]

                    peers.append((ip, port))

        except Exception as e:
            logger.error(f"Failed to decode peers: {e}", extra={"class_name": self.__class__.__name__})

        return peers

    def _encode_peers(self, peers: List[Tuple[str, int]]) -> Tuple[bytes, bytes]:
        """
        Encode peers in compact format

        Args:
            peers: List of (IP, port) tuples

        Returns:
            Tuple of (peers_data, flags_data)
        """
        peers_data = b""
        flags_data = b""

        try:
            for ip, port in peers:
                # Encode IP and port
                ip_bytes = socket.inet_aton(ip)
                port_bytes = struct.pack(">H", port)
                peers_data += ip_bytes + port_bytes

                # Add flags
                flags = self.peer_flags.get((ip, port), 0)
                flags_data += struct.pack("B", flags)

        except Exception as e:
            logger.error(f"Failed to encode peers: {e}", extra={"class_name": self.__class__.__name__})

        return peers_data, flags_data

    def _process_added_peers(self, peers: List[Tuple[str, int]], flags_data: bytes):
        """
        Process newly added peers from PEX message

        Args:
            peers: List of (IP, port) tuples
            flags_data: Peer flags data
        """
        for i, (ip, port) in enumerate(peers):
            # Extract flags if available
            flags = 0
            if flags_data and i < len(flags_data):
                flags = flags_data[i]

            # Add to known peers
            self.add_peer(ip, port, flags)

            # Optionally connect to new peers (for real client behavior)
            # In fake seeding, we just track them
            logger.debug(f"Learned about peer via PEX: {ip}:{port}", extra={"class_name": self.__class__.__name__})

    def _process_dropped_peers(self, peers: List[Tuple[str, int]]):
        """
        Process dropped peers from PEX message

        Args:
            peers: List of (IP, port) tuples that were dropped
        """
        for ip, port in peers:
            self.remove_peer(ip, port)

    def _select_peers_to_send(self) -> List[Tuple[str, int]]:
        """
        Select peers to send in PEX message

        Returns:
            List of (IP, port) tuples to send
        """
        # Find peers we haven't sent yet
        unsent_peers = self.known_peers - self.sent_peers

        # Limit to max peers per message
        peers_to_send = list(unsent_peers)[: self.max_peers_per_message]

        return peers_to_send

    def _select_dropped_peers(self) -> List[Tuple[str, int]]:
        """
        Select dropped peers to send in PEX message

        Returns:
            List of (IP, port) tuples that were dropped
        """
        # For simplicity, we don't track dropped peers in fake seeding
        # Real implementation would track peers that disconnected
        return []

    def _generate_synthetic_peers(self):
        """Generate synthetic peers for realistic PEX behavior"""
        if not self.generate_synthetic_peers:
            return

        try:
            # Generate realistic-looking peer IP addresses
            for _ in range(self.synthetic_peer_count):
                # Generate realistic IP ranges (avoid private/reserved ranges)
                # Use common ISP IP ranges
                first_octet = random.choice(
                    [
                        random.randint(1, 126),  # Class A (avoid 127.x.x.x)
                        random.randint(128, 191),  # Class B
                        random.randint(192, 223),  # Class C (avoid 192.168.x.x)
                    ]
                )

                if first_octet == 192:
                    # Avoid 192.168.x.x private range
                    second_octet = random.choice([random.randint(0, 167), random.randint(169, 255)])
                else:
                    second_octet = random.randint(1, 254)

                third_octet = random.randint(1, 254)
                fourth_octet = random.randint(1, 254)

                ip = f"{first_octet}.{second_octet}.{third_octet}.{fourth_octet}"

                # Generate realistic port (common BitTorrent ports)
                port = random.choice(
                    [
                        random.randint(6881, 6889),  # Traditional BT ports
                        random.randint(49152, 65535),  # Dynamic/ephemeral ports
                    ]
                )

                # Random flags (encryption support, etc.)
                flags = random.randint(0, 3)

                self.add_peer(ip, port, flags)

            logger.debug(
                f"Generated {self.synthetic_peer_count} synthetic peers for PEX",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(f"Failed to generate synthetic peers: {e}", extra={"class_name": self.__class__.__name__})

    def get_statistics(self) -> dict:
        """
        Get PEX statistics

        Returns:
            Dictionary with PEX statistics
        """
        return {
            "known_peers": len(self.known_peers),
            "sent_peers": len(self.sent_peers),
            "last_pex_time": self.last_pex_time,
            "pex_interval": self.pex_interval,
            "synthetic_peers_enabled": self.generate_synthetic_peers,
        }

    def cleanup(self):
        """Clean up PEX extension"""
        self.known_peers.clear()
        self.sent_peers.clear()
        self.peer_flags.clear()

        logger.debug("PEX extension cleaned up", extra={"class_name": self.__class__.__name__})
