"""
Torrent Peer Manager

Manages peer protocol communication in the context of torrent selection.
Starts/stops peer communication when torrents are selected/deselected.
"""

# fmt: off
import threading
import time
from typing import Dict, List, Optional

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.peer_protocol_manager import PeerProtocolManager
from d_fake_seeder.lib.logger import logger

# fmt: on


class TorrentPeerManager:
    """Manages peer communication for the currently selected torrent"""

    def __init__(self):
        self.current_torrent_id: Optional[str] = None
        self.current_manager: Optional[PeerProtocolManager] = None
        self.lock = threading.Lock()

        # Get settings instance for configurable values
        self.settings = AppSettings.get_instance()
        torrent_peer_manager_config = getattr(self.settings, "torrent_peer_manager", {})

        # Statistics tracking
        self.peer_stats_cache: Dict[str, Dict] = {}
        self.last_stats_update = 0
        self.stats_update_interval = torrent_peer_manager_config.get("stats_update_interval_seconds", 2.0)

        logger.debug(
            "🎯 TorrentPeerManager initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def select_torrent(self, torrent):
        """Called when a torrent is selected in the UI"""
        if not torrent or not hasattr(torrent, "id"):
            self.deselect_torrent()
            return

        torrent_id = str(torrent.id)

        with self.lock:
            # If same torrent, do nothing
            if self.current_torrent_id == torrent_id:
                return

            # Stop current manager if any
            if self.current_manager:
                logger.info(
                    f"🛑 Stopping peer communication for {self.current_torrent_id}",
                    extra={"class_name": self.__class__.__name__},
                )
                self.current_manager.stop()
                self.current_manager = None

            # Start new manager for selected torrent
            self.current_torrent_id = torrent_id

            try:
                # Get torrent info hash and our peer ID
                info_hash = torrent.torrent_file.get_info_hash()
                our_peer_id = self._get_our_peer_id(torrent)

                # Create new peer protocol manager
                max_connections = getattr(self.settings, "max_connections_per_torrent", 50)
                self.current_manager = PeerProtocolManager(
                    info_hash=info_hash,
                    our_peer_id=our_peer_id,
                    max_connections=max_connections,
                )

                # Add peers from the torrent's seeder
                if hasattr(torrent, "get_seeder") and torrent.get_seeder():
                    seeder = torrent.get_seeder()
                    if hasattr(seeder, "peers"):
                        peer_addresses = seeder.peers
                        if peer_addresses:
                            self.current_manager.add_peers(peer_addresses)
                            logger.debug(
                                f"➕ Added {len(peer_addresses)} peers for {torrent_id}",
                                extra={"class_name": self.__class__.__name__},
                            )

                # Start the peer protocol manager
                self.current_manager.start()

                logger.info(
                    f"🚀 Started peer communication for {torrent_id} ({torrent.name})",
                    extra={"class_name": self.__class__.__name__},
                )

            except Exception as e:
                logger.error(
                    f"❌ Failed to start peer communication for torrent {torrent_id}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                self.current_manager = None
                self.current_torrent_id = None

    def deselect_torrent(self):
        """Called when no torrent is selected"""
        with self.lock:
            if self.current_manager:
                logger.info(
                    f"🛑 Stopping peer communication for {self.current_torrent_id}",
                    extra={"class_name": self.__class__.__name__},
                )
                self.current_manager.stop()
                self.current_manager = None

            self.current_torrent_id = None
            self.peer_stats_cache.clear()

    def update_peers(self, peer_addresses: List[str]):
        """Update the peer list for the current torrent"""
        with self.lock:
            if self.current_manager:
                self.current_manager.add_peers(peer_addresses)
                logger.debug(
                    f"🔄 Updated {len(peer_addresses)} peers for current torrent",
                    extra={"class_name": self.__class__.__name__},
                )

    def get_peer_stats(self) -> Dict[str, Dict]:
        """Get current peer statistics"""
        current_time = time.time()

        # Update cache if needed
        if current_time - self.last_stats_update > self.stats_update_interval:
            with self.lock:
                if self.current_manager:
                    try:
                        self.peer_stats_cache = self.current_manager.get_peer_stats()
                        self.last_stats_update = current_time

                        # Log summary statistics
                        total_peers = len(self.peer_stats_cache)
                        connected_peers = sum(1 for stats in self.peer_stats_cache.values() if stats["connected"])
                        seeds = sum(1 for stats in self.peer_stats_cache.values() if stats["is_seed"])

                        if total_peers > 0:
                            logger.debug(
                                f"📊 Peer stats: {total_peers} total, " f"{connected_peers} connected, {seeds} seeds",
                                extra={"class_name": self.__class__.__name__},
                            )

                    except Exception as e:
                        logger.error(
                            f"❌ Error getting peer stats: {e}",
                            extra={"class_name": self.__class__.__name__},
                        )

        return self.peer_stats_cache.copy()

    def get_connection_summary(self) -> Dict[str, int]:
        """Get summary of connection statistics"""
        stats = self.get_peer_stats()

        summary = {
            "total_peers": len(stats),
            "connected_peers": sum(1 for s in stats.values() if s["connected"]),
            "seeds": sum(1 for s in stats.values() if s["is_seed"]),
            "leechers": sum(1 for s in stats.values() if not s["is_seed"]),
            "unchoked_peers": sum(1 for s in stats.values() if s["connected"] and not s["choked"]),
        }

        return summary

    def _get_our_peer_id(self, torrent) -> bytes:
        """Get our peer ID for this torrent"""
        try:
            # Try to get peer ID from torrent's seeder
            if hasattr(torrent, "get_seeder") and torrent.get_seeder():
                seeder = torrent.get_seeder()
                if hasattr(seeder, "peer_id"):
                    peer_id_str = str(seeder.peer_id)
                    # Ensure it's 20 bytes
                    if len(peer_id_str) >= 20:
                        return peer_id_str[:20].encode("utf-8", errors="ignore")
                    else:
                        # Pad to 20 bytes
                        return (peer_id_str + "0" * 20)[:20].encode("utf-8", errors="ignore")

            # Fallback: generate a peer ID
            import random
            import string

            # Use a format similar to what we see in the existing code
            prefix = "-DF0100-"  # DFakeSeeder version 1.0.0
            suffix = "".join(random.choices(string.ascii_letters + string.digits, k=12))
            peer_id = (prefix + suffix)[:20]

            logger.debug(
                f"🆔 Generated peer ID: {peer_id}",
                extra={"class_name": self.__class__.__name__},
            )

            return peer_id.encode("utf-8")

        except Exception as e:
            logger.error(
                f"❌ Error generating peer ID: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            # Final fallback
            return b"-DF0100-abcdef123456"

    def shutdown(self):
        """Shutdown the peer manager"""
        logger.info(
            "🛑 Shutting down TorrentPeerManager",
            extra={"class_name": self.__class__.__name__},
        )
        self.deselect_torrent()


# Global instance
_torrent_peer_manager: Optional[TorrentPeerManager] = None


def get_torrent_peer_manager() -> TorrentPeerManager:
    """Get the global torrent peer manager instance"""
    global _torrent_peer_manager
    if _torrent_peer_manager is None:
        _torrent_peer_manager = TorrentPeerManager()
    return _torrent_peer_manager


def shutdown_torrent_peer_manager():
    """Shutdown the global torrent peer manager"""
    global _torrent_peer_manager
    if _torrent_peer_manager:
        _torrent_peer_manager.shutdown()
        _torrent_peer_manager = None
