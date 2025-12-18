"""
Local Peer Discovery (BEP-014) Implementation.

Discovers peers on the local network via multicast announcements.
This allows finding peers without relying on trackers or DHT.
"""

import asyncio
import re
import socket
import struct
from typing import Any, Callable, Dict, Optional, Set, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

# BEP-014 constants
LPD_MULTICAST_ADDR_V4 = "239.192.152.143"
LPD_MULTICAST_ADDR_V6 = "ff15::efc0:988f"
LPD_PORT = 6771
LPD_ANNOUNCE_INTERVAL = 300  # 5 minutes between announcements per torrent

# BEP-014 message format
LPD_MESSAGE_TEMPLATE = (
    "BT-SEARCH * HTTP/1.1\r\n"
    "Host: {addr}:{port}\r\n"
    "Port: {listen_port}\r\n"
    "Infohash: {infohash}\r\n"
    "\r\n"
)


class LocalPeerDiscovery:
    """
    Discovers peers on the local network via multicast.

    Implements BEP-014 for local peer discovery, allowing
    peers on the same network to find each other without
    external resources.
    """

    def __init__(
        self,
        port: int = 6881,
        peer_callback: Optional[Callable[[str, int, bytes], None]] = None,
    ) -> None:
        """
        Initialize Local Peer Discovery.

        Args:
            port: Our listening port for incoming connections.
            peer_callback: Callback when a peer is discovered.
                          Receives (ip, port, info_hash).
        """
        self.settings = AppSettings.get_instance()
        self.port = port
        self.peer_callback = peer_callback
        self.socket: Optional[socket.socket] = None
        self.running = False
        self._listen_task: Optional[asyncio.Task] = None
        self._announce_task: Optional[asyncio.Task] = None

        # Track announced torrents and their last announcement time
        self.announced_hashes: Dict[bytes, float] = {}

        # Track discovered peers: info_hash -> set of (ip, port)
        self.discovered_peers: Dict[bytes, Set[Tuple[str, int]]] = {}

        logger.trace(
            "LocalPeerDiscovery initialized",
            extra={"class_name": self.__class__.__name__, "port": port},
        )

    async def start(self) -> bool:
        """
        Start LPD listener and announcer.

        Returns:
            True if started successfully.
        """
        if not self.settings.get("bittorrent.enable_lpd", True):
            logger.debug(
                "LPD disabled in settings",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        if self.running:
            return True

        try:
            # Create UDP socket for multicast
            self.socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
            )
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Try to set SO_REUSEPORT if available (Linux)
            try:
                self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except (AttributeError, OSError):
                pass  # Not available on all platforms

            # Bind to the LPD port
            self.socket.bind(("", LPD_PORT))

            # Join the multicast group
            mreq = struct.pack(
                "4sl", socket.inet_aton(LPD_MULTICAST_ADDR_V4), socket.INADDR_ANY
            )
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            # Set multicast TTL (1 = local network only)
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)

            # Don't receive our own multicast messages
            self.socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 0)

            # Set non-blocking for async operation
            self.socket.setblocking(False)

            self.running = True

            # Start listener task
            self._listen_task = asyncio.create_task(self._listen_loop())

            logger.info(
                "Local Peer Discovery started",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"LPD start failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self._cleanup_socket()
            return False

    async def stop(self) -> None:
        """Stop LPD listener and announcer."""
        if not self.running:
            return

        self.running = False

        # Cancel tasks
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            self._listen_task = None

        if self._announce_task:
            self._announce_task.cancel()
            try:
                await self._announce_task
            except asyncio.CancelledError:
                pass
            self._announce_task = None

        self._cleanup_socket()

        logger.info(
            "Local Peer Discovery stopped",
            extra={"class_name": self.__class__.__name__},
        )

    def _cleanup_socket(self) -> None:
        """Clean up the socket."""
        if self.socket:
            try:
                # Leave multicast group
                mreq = struct.pack(
                    "4sl", socket.inet_aton(LPD_MULTICAST_ADDR_V4), socket.INADDR_ANY
                )
                self.socket.setsockopt(
                    socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq
                )
            except Exception:
                pass

            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

    async def announce(self, info_hash: bytes) -> None:
        """
        Announce a torrent to the local network.

        Args:
            info_hash: 20-byte torrent info hash.
        """
        if not self.running or not self.socket:
            return

        # Rate limit announcements
        import time

        current_time = time.time()
        last_announce = self.announced_hashes.get(info_hash, 0)
        if current_time - last_announce < LPD_ANNOUNCE_INTERVAL:
            return

        try:
            message = LPD_MESSAGE_TEMPLATE.format(
                addr=LPD_MULTICAST_ADDR_V4,
                port=LPD_PORT,
                listen_port=self.port,
                infohash=info_hash.hex().upper(),
            ).encode("utf-8")

            self.socket.sendto(message, (LPD_MULTICAST_ADDR_V4, LPD_PORT))
            self.announced_hashes[info_hash] = current_time

            logger.debug(
                f"LPD: Announced {info_hash.hex()[:16]}...",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.warning(
                f"LPD announce failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    async def announce_all(self, info_hashes: list) -> None:
        """
        Announce multiple torrents.

        Args:
            info_hashes: List of 20-byte info hashes.
        """
        for info_hash in info_hashes:
            await self.announce(info_hash)
            # Small delay between announcements
            await asyncio.sleep(0.1)

    async def _listen_loop(self) -> None:
        """Main listening loop for LPD announcements."""
        loop = asyncio.get_event_loop()

        while self.running and self.socket:
            try:
                # Wait for data with timeout
                data, addr = await asyncio.wait_for(
                    loop.sock_recvfrom(self.socket, 1024),
                    timeout=1.0,
                )
                self._parse_announcement(data, addr)

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                if self.running:
                    logger.warning(
                        f"LPD listen error: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )
                await asyncio.sleep(0.1)

    def _parse_announcement(self, data: bytes, addr: Tuple[str, int]) -> None:
        """
        Parse an incoming LPD announcement.

        Args:
            data: Raw announcement data.
            addr: Sender address (ip, port).
        """
        try:
            message = data.decode("utf-8", errors="ignore")

            # Check if it's a BT-SEARCH message
            if not message.startswith("BT-SEARCH"):
                return

            # Parse the message headers
            peer_port = None
            info_hash_hex = None

            for line in message.split("\r\n"):
                if line.lower().startswith("port:"):
                    try:
                        peer_port = int(line.split(":", 1)[1].strip())
                    except ValueError:
                        pass
                elif line.lower().startswith("infohash:"):
                    info_hash_hex = line.split(":", 1)[1].strip()

            if not peer_port or not info_hash_hex:
                return

            # Convert info hash from hex
            try:
                info_hash = bytes.fromhex(info_hash_hex)
                if len(info_hash) != 20:
                    return
            except ValueError:
                return

            peer_ip = addr[0]

            # Skip our own announcements
            if self._is_own_address(peer_ip):
                return

            # Store the discovered peer
            if info_hash not in self.discovered_peers:
                self.discovered_peers[info_hash] = set()
            self.discovered_peers[info_hash].add((peer_ip, peer_port))

            # Notify callback
            if self.peer_callback:
                try:
                    self.peer_callback(peer_ip, peer_port, info_hash)
                except Exception as e:
                    logger.warning(
                        f"LPD peer callback error: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

            logger.debug(
                f"LPD: Discovered peer {peer_ip}:{peer_port} for "
                f"{info_hash_hex[:16]}...",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.warning(
                f"LPD parse error: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _is_own_address(self, ip: str) -> bool:
        """Check if an IP address belongs to this machine."""
        try:
            # Get all local addresses
            hostname = socket.gethostname()
            local_ips = socket.gethostbyname_ex(hostname)[2]
            local_ips.append("127.0.0.1")
            return ip in local_ips
        except Exception:
            return ip == "127.0.0.1"

    def get_peers(self, info_hash: bytes) -> Set[Tuple[str, int]]:
        """
        Get discovered peers for a torrent.

        Args:
            info_hash: 20-byte torrent info hash.

        Returns:
            Set of (ip, port) tuples.
        """
        return self.discovered_peers.get(info_hash, set()).copy()

    def get_status(self) -> dict:
        """
        Get the current LPD status.

        Returns:
            Dictionary with LPD status information.
        """
        return {
            "enabled": self.settings.get("bittorrent.enable_lpd", True),
            "running": self.running,
            "port": self.port,
            "announced_torrents": len(self.announced_hashes),
            "discovered_peers": sum(len(peers) for peers in self.discovered_peers.values()),
        }

    def is_running(self) -> bool:
        """Check if LPD is running."""
        return self.running


# Singleton instance
_instance: Optional[LocalPeerDiscovery] = None


def get_lpd_manager(
    port: int = 6881,
    peer_callback: Optional[Callable[[str, int, bytes], None]] = None,
) -> LocalPeerDiscovery:
    """Get or create the LocalPeerDiscovery singleton instance."""
    global _instance
    if _instance is None:
        _instance = LocalPeerDiscovery(port, peer_callback)
    return _instance

