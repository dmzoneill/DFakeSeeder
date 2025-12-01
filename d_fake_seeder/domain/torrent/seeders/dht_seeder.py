"""
DHT Seeder Implementation

Implements trackerless seeding using DHT (Distributed Hash Table) protocol.
Extends BaseSeeder to provide DHT-based peer discovery and announcement.
"""

# fmt: off
import asyncio
import hashlib
import time
from typing import Optional

from d_fake_seeder.domain.torrent.protocols.dht.node import DHTNode
from d_fake_seeder.domain.torrent.seeders.base_seeder import BaseSeeder
from d_fake_seeder.lib.logger import logger

# fmt: on


class DHTSeeder(BaseSeeder):
    """DHT-based seeder for trackerless torrents"""

    def __init__(self, torrent):
        """
        Initialize DHT seeder

        Args:
            torrent: Torrent instance to seed
        """
        super().__init__(torrent)

        self.dht_node: Optional[DHTNode] = None
        self.info_hash = self._calculate_info_hash()
        self.announce_task = None
        self.last_announce_time = 0

        # DHT-specific configuration
        dht_config = getattr(self.settings, "protocols", {}).get("dht", {})
        self.dht_enabled = dht_config.get("enabled", True)
        base_interval = dht_config.get("announcement_interval", 1800)
        # Apply jitter to announce interval to prevent request storms
        self.announce_interval = self._apply_announce_jitter(base_interval)

        logger.debug(
            "DHT Seeder initialized",
            extra={
                "class_name": self.__class__.__name__,
                "info_hash": self.info_hash.hex()[:16] if self.info_hash else "None",
            },
        )

    def _calculate_info_hash(self) -> Optional[bytes]:
        """Calculate torrent info hash for DHT operations"""
        try:
            if hasattr(self.torrent, "info_hash"):
                return self.torrent.info_hash

            # Calculate from torrent file if not available
            if hasattr(self.torrent, "torrent_file") and self.torrent.torrent_file:
                torrent_data = self.torrent.torrent_file.get_data()
                if b"info" in torrent_data:
                    import bencode

                    info_data = bencode.bencode(torrent_data[b"info"])
                    return hashlib.sha1(info_data).digest()

            logger.warning(
                "Could not calculate info hash for DHT",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        except Exception as e:
            logger.error(
                f"Failed to calculate info hash: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    async def start(self):
        """Start DHT seeding"""
        if not self.dht_enabled:
            logger.info("DHT seeding disabled", extra={"class_name": self.__class__.__name__})
            return False

        if not self.info_hash:
            logger.error(
                "Cannot start DHT seeding without info hash",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            logger.debug("Starting DHT seeder", extra={"class_name": self.__class__.__name__})

            # Initialize DHT node
            self.dht_node = DHTNode(port=self.port)
            await self.dht_node.start()

            # Start announcement loop
            self.announce_task = asyncio.create_task(self._announce_loop())

            self.active = True
            logger.info(
                "DHT seeder started successfully",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to start DHT seeder: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def stop(self):
        """Stop DHT seeding"""
        logger.info("Stopping DHT seeder", extra={"class_name": self.__class__.__name__})

        self.active = False
        self.shutdown_requested = True

        # Cancel announcement task
        if self.announce_task:
            self.announce_task.cancel()
            try:
                await self.announce_task
            except asyncio.CancelledError:
                pass

        # Stop DHT node
        if self.dht_node:
            await self.dht_node.stop()
            self.dht_node = None

    async def _announce_loop(self):
        """Periodic DHT announcement loop"""
        while self.active and not self.shutdown_requested:
            try:
                current_time = time.time()

                # Check if it's time to announce
                if current_time - self.last_announce_time >= self.announce_interval:
                    await self._announce_to_dht()
                    self.last_announce_time = current_time

                # Wait before next check
                await asyncio.sleep(60)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"DHT announce loop error: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                await asyncio.sleep(60)

    async def _announce_to_dht(self):
        """Announce this torrent to the DHT network"""
        if not self.dht_node or not self.info_hash:
            return

        try:
            logger.debug(
                f"Announcing torrent {self.info_hash.hex()[:16]} to DHT",
                extra={"class_name": self.__class__.__name__},
            )

            success = await self.dht_node.announce_peer(self.info_hash, self.port)

            if success:
                logger.debug(
                    "DHT announcement successful",
                    extra={"class_name": self.__class__.__name__},
                )

                # Update statistics
                self._update_stats("dht_announce", True)
            else:
                logger.warning(
                    "DHT announcement failed",
                    extra={"class_name": self.__class__.__name__},
                )
                self._update_stats("dht_announce", False)

        except Exception as e:
            logger.error(
                f"DHT announcement error: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self._update_stats("dht_announce", False)

    async def find_peers(self) -> list:
        """Find peers for this torrent via DHT"""
        if not self.dht_node or not self.info_hash:
            return []

        try:
            peers = await self.dht_node.get_peers(self.info_hash)

            logger.debug(
                f"Found {len(peers)} peers via DHT",
                extra={"class_name": self.__class__.__name__},
            )

            return peers

        except Exception as e:
            logger.error(
                f"DHT peer discovery error: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return []

    def _update_stats(self, operation: str, success: bool):
        """Update DHT operation statistics"""
        try:
            # Get current stats from settings
            dht_stats = getattr(self.settings, "dht_stats", {})

            # Initialize if needed
            if operation not in dht_stats:
                dht_stats[operation] = {"success": 0, "failure": 0}

            # Update counter
            if success:
                dht_stats[operation]["success"] += 1
            else:
                dht_stats[operation]["failure"] += 1

            # Store back to settings
            setattr(self.settings, "dht_stats", dht_stats)

        except Exception as e:
            logger.debug(
                f"Failed to update DHT stats: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def get_status(self) -> dict:
        """Get DHT seeder status information"""
        status = {
            "type": "DHT",
            "active": self.active,
            "info_hash": self.info_hash.hex() if self.info_hash else None,
            "dht_enabled": self.dht_enabled,
            "last_announce": self.last_announce_time,
            "next_announce": self.last_announce_time + self.announce_interval,
            "node_id": self.dht_node.node_id.hex() if self.dht_node else None,
        }

        # Add DHT statistics
        dht_stats = getattr(self.settings, "dht_stats", {})
        status["stats"] = dht_stats

        return status

    def handle_settings_changed(self, source, key, value):
        """Handle settings changes"""
        super().handle_settings_changed(source, key, value)

        # Handle DHT-specific settings
        if key.startswith("protocols.dht"):
            logger.debug(
                f"DHT setting changed: {key} = {value}",
                extra={"class_name": self.__class__.__name__},
            )

            if key == "protocols.dht.enabled":
                self.dht_enabled = value
                if not value and self.active:
                    # Stop if DHT was disabled
                    asyncio.create_task(self.stop())
            elif key == "protocols.dht.announcement_interval":
                # Apply jitter to new interval to prevent request storms
                self.announce_interval = self._apply_announce_jitter(value)

    # Implement required BaseSeeder methods for compatibility
    def request_status(self):
        """Request status from DHT network (compatibility method)"""
        # DHT doesn't have traditional tracker status
        return {"status": "DHT active" if self.active else "DHT inactive"}

    def set_announce_url(self, url):
        """Set announce URL (not applicable for DHT)"""
        logger.debug(
            "DHT seeder ignoring announce URL setting",
            extra={"class_name": self.__class__.__name__},
        )
