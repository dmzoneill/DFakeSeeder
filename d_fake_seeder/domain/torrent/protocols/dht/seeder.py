"""
DHT Seeder Integration

Integrates DHT functionality with the seeding system.
Provides DHT-based peer discovery and announcement for torrents.
"""

# fmt: off
import time
from typing import Any, Dict, List, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

from .node import DHTNode

# fmt: on


class DHTSeeder:
    """DHT seeder for torrent peer discovery and announcement"""

    def __init__(self, port: int = 6881) -> None:
        """
        Initialize DHT seeder

        Args:
            port: UDP port for DHT communication
        """
        self.port = port
        self.settings = AppSettings.get_instance()
        self.dht_node = DHTNode(port=port)

        # DHT state
        self.enabled = True
        self.running = False

        # Torrent tracking
        self.active_torrents: Dict[bytes, Dict] = {}
        self.last_announce: Dict[bytes, float] = {}

        logger.trace(
            f"DHT Seeder initialized on port {port}",
            extra={"class_name": self.__class__.__name__},
        )

    async def start(self) -> bool:
        """
        Start DHT seeder

        Returns:
            True if started successfully
        """
        if not self.enabled:
            logger.info("DHT seeder disabled", extra={"class_name": self.__class__.__name__})
            return False

        try:
            logger.trace("Starting DHT seeder", extra={"class_name": self.__class__.__name__})

            # Start DHT node
            await self.dht_node.start()

            if self.dht_node.running:
                self.running = True
                logger.trace(
                    "DHT seeder started successfully",
                    extra={"class_name": self.__class__.__name__},
                )
                return True
            else:
                logger.error(
                    "Failed to start DHT node",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

        except Exception as e:
            logger.error(
                f"DHT seeder start failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def stop(self) -> Any:
        """Stop DHT seeder"""
        logger.info("Stopping DHT seeder", extra={"class_name": self.__class__.__name__})

        self.running = False
        self.active_torrents.clear()
        self.last_announce.clear()

        if self.dht_node:
            await self.dht_node.stop()

    async def add_torrent(self, info_hash: bytes, torrent_data: Dict) -> bool:
        """
        Add torrent to DHT seeding

        Args:
            info_hash: 20-byte torrent info hash
            torrent_data: Torrent metadata and configuration

        Returns:
            True if torrent was added successfully
        """
        if not self.running:
            return False

        try:
            # Store torrent info
            self.active_torrents[info_hash] = {
                "name": torrent_data.get("name", "Unknown"),
                "added_at": time.time(),
                "announce_port": torrent_data.get("port", self.port),
                "last_peers_count": 0,
                "total_announcements": 0,
            }

            # Initial announcement
            success = await self.announce_torrent(info_hash)

            if success:
                logger.trace(
                    f"Added torrent {info_hash.hex()[:16]} to DHT seeding",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    f"Failed initial DHT announcement for {info_hash.hex()[:16]}",
                    extra={"class_name": self.__class__.__name__},
                )

            return True

        except Exception as e:
            logger.error(
                f"Failed to add torrent to DHT: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def remove_torrent(self, info_hash: bytes) -> None:
        """
        Remove torrent from DHT seeding

        Args:
            info_hash: 20-byte torrent info hash
        """
        if info_hash in self.active_torrents:
            del self.active_torrents[info_hash]

        if info_hash in self.last_announce:
            del self.last_announce[info_hash]

        logger.trace(
            f"Removed torrent {info_hash.hex()[:16]} from DHT seeding",
            extra={"class_name": self.__class__.__name__},
        )

    async def announce_torrent(self, info_hash: bytes) -> bool:
        """
        Announce torrent to DHT network

        Args:
            info_hash: 20-byte torrent info hash

        Returns:
            True if announcement was successful
        """
        if not self.running or info_hash not in self.active_torrents:
            return False

        try:
            torrent_info = self.active_torrents[info_hash]
            announce_port = torrent_info.get("announce_port", self.port)

            # Announce to DHT
            success = await self.dht_node.announce_peer(info_hash, announce_port)

            # Update statistics
            current_time = time.time()
            self.last_announce[info_hash] = current_time

            if success:
                torrent_info["total_announcements"] += 1
                logger.trace(
                    f"DHT announcement successful for {info_hash.hex()[:16]}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.trace(
                    f"DHT announcement failed for {info_hash.hex()[:16]}",
                    extra={"class_name": self.__class__.__name__},
                )

            return success

        except Exception as e:
            logger.error(
                f"DHT announcement error for {info_hash.hex()[:16]}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def discover_peers(self, info_hash: bytes, max_peers: int = 50) -> List[Tuple[str, int]]:
        """
        Discover peers for torrent via DHT

        Args:
            info_hash: 20-byte torrent info hash
            max_peers: Maximum number of peers to return

        Returns:
            List of (IP, port) tuples for discovered peers
        """
        if not self.running:
            return []

        try:
            peers = await self.dht_node.get_peers(info_hash)

            # Update peer count statistics
            if info_hash in self.active_torrents:
                self.active_torrents[info_hash]["last_peers_count"] = len(peers)

            logger.trace(
                f"DHT discovered {len(peers)} peers for {info_hash.hex()[:16]}",
                extra={"class_name": self.__class__.__name__},
            )

            return peers[:max_peers]

        except Exception as e:
            logger.error(
                f"DHT peer discovery error for {info_hash.hex()[:16]}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return []

    def get_torrent_stats(self, info_hash: bytes) -> Dict:
        """
        Get DHT statistics for a torrent

        Args:
            info_hash: 20-byte torrent info hash

        Returns:
            Dictionary with DHT statistics
        """
        if info_hash not in self.active_torrents:
            return {}

        torrent_info = self.active_torrents[info_hash]
        current_time = time.time()

        stats = {
            "dht_enabled": self.running,
            "total_announcements": torrent_info.get("total_announcements", 0),
            "last_peers_count": torrent_info.get("last_peers_count", 0),
            "added_at": torrent_info.get("added_at", 0),
            "time_active": current_time - torrent_info.get("added_at", current_time),
        }

        # Last announce time
        if info_hash in self.last_announce:
            stats["last_announce"] = self.last_announce[info_hash]
            stats["time_since_announce"] = current_time - self.last_announce[info_hash]
        else:
            stats["last_announce"] = 0
            stats["time_since_announce"] = 0

        return stats

    def get_global_stats(self) -> Dict:
        """
        Get global DHT statistics

        Returns:
            Dictionary with global DHT statistics
        """
        if not self.dht_node or not self.running:
            return {
                "enabled": False,
                "running": False,
                "active_torrents": 0,
                "routing_table_nodes": 0,
            }

        # Routing table statistics
        routing_stats = {
            "total_nodes": self.dht_node.routing_table.get_node_count(),
            "bucket_info": self.dht_node.routing_table.get_bucket_info(),
        }

        return {
            "enabled": self.enabled,
            "running": self.running,
            "active_torrents": len(self.active_torrents),
            "node_id": self.dht_node.node_id.hex()[:16],
            "port": self.port,
            "routing_table": routing_stats,
            "total_announcements": sum(
                torrent.get("total_announcements", 0) for torrent in self.active_torrents.values()
            ),
        }

    async def periodic_maintenance(self) -> Any:
        """
        Perform periodic DHT maintenance

        This should be called periodically to:
        - Re-announce active torrents
        - Clean up stale data
        - Update routing table
        """
        if not self.running:
            return

        try:
            current_time = time.time()
            announcement_interval = (
                getattr(self.settings, "protocols", {}).get("dht", {}).get("announcement_interval", 1800)
            )

            # Re-announce torrents that need it
            for info_hash in list(self.active_torrents.keys()):
                last_announce_time = self.last_announce.get(info_hash, 0)

                if current_time - last_announce_time >= announcement_interval:
                    await self.announce_torrent(info_hash)

            logger.trace(
                f"DHT maintenance completed for {len(self.active_torrents)} torrents",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"DHT maintenance error: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def is_enabled(self) -> bool:
        """Check if DHT seeder is enabled"""
        return self.enabled

    def is_running(self) -> bool:
        """Check if DHT seeder is running"""
        return self.running

    def get_active_torrent_count(self) -> int:
        """Get number of active torrents in DHT"""
        return len(self.active_torrents)

    def enable(self) -> Any:
        """Enable DHT seeder"""
        self.enabled = True
        logger.info("DHT seeder enabled", extra={"class_name": self.__class__.__name__})

    def disable(self) -> Any:
        """Disable DHT seeder"""
        self.enabled = False
        logger.info("DHT seeder disabled", extra={"class_name": self.__class__.__name__})
