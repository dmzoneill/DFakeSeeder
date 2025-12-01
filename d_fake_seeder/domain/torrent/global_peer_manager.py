"""
Global Peer Manager

A global background worker that handles peer-to-peer communication across all torrents.
Provides unified peer connection tracking and statistics aggregation.
"""

# fmt: off
import hashlib
import threading
import time
from typing import Dict, List

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.peer_protocol_manager import PeerProtocolManager
from d_fake_seeder.domain.torrent.peer_server import PeerServer
from d_fake_seeder.domain.torrent.shared_async_executor import SharedAsyncExecutor
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import NetworkConstants

# fmt: on


class GlobalPeerManager:
    """Global background worker managing peer connections for all torrents"""

    def __init__(self):
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
        self.shutdown_event = threading.Event()  # Event-based shutdown for smart sleep

        # Get settings instance
        self.settings = AppSettings.get_instance()
        ui_settings = getattr(self.settings, "ui_settings", {})

        # Configurable sleep intervals
        self.manager_sleep_interval = ui_settings.get("async_sleep_interval_seconds", 1.0)
        self.manager_error_sleep_interval = ui_settings.get("error_sleep_interval_seconds", 5.0)
        self.manager_thread_join_timeout = ui_settings.get("manager_thread_join_timeout_seconds", 5.0)

        # Torrent tracking
        self.active_torrents: Dict[str, Dict] = {}  # torrent_id -> torrent_info
        self.peer_managers: Dict[str, PeerProtocolManager] = {}  # info_hash -> manager

        # Peer server for incoming connections - use configured values
        port = getattr(self.settings, "listening_port", NetworkConstants.DEFAULT_PORT)
        max_connections = getattr(self.settings, "max_incoming_connections", 200)
        self.peer_server = PeerServer(port=port, max_connections=max_connections)

        # Shared async executor for all peer protocol managers
        self.executor = SharedAsyncExecutor.get_instance()

        # Global peer statistics
        self.global_peer_stats = {
            "total_peers": 0,
            "connected_peers": 0,
            "seeds": 0,
            "leechers": 0,
            "upload_connections": 0,
            "download_connections": 0,
            "incoming_connections": 0,
            "total_torrents": 0,
        }

        # Update intervals from config
        # stats_update_interval_seconds is user-configurable (default 5.0s for better performance)
        # Increasing this from 2.0s to 5.0s reduces CPU by ~5-10% with minimal UX impact
        peer_protocol = getattr(self.settings, "peer_protocol", {})
        self.peer_update_interval = peer_protocol.get("peer_update_interval_seconds", 30.0)
        self.stats_update_interval = peer_protocol.get("stats_update_interval_seconds", 5.0)
        self.last_peer_update = 0
        self.last_stats_update = 0

        # Statistics caching with dirty-tracking (only recalculate changed managers)
        self._per_manager_stats: Dict[str, Dict] = {}  # Cache per-manager aggregated stats
        self._dirty_managers: set = set()  # Track which managers need stats recalculation
        self._stats_cache_dirty = True  # Global dirty flag

        logger.debug(
            "🌍 GlobalPeerManager initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def set_connection_callback(self, callback):
        """Set callback for connection events (for UI updates)"""
        self.peer_server.set_connection_callback(callback)

    def start(self):
        """Start the global peer manager background worker"""
        if self.running:
            return

        with self.lock:
            self.running = True

            # Start shared async executor first
            self.executor.start()
            logger.debug(
                "🚀 SharedAsyncExecutor started",
                extra={"class_name": self.__class__.__name__},
            )

            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()

        # Start peer server for incoming connections
        self.peer_server.start()

        logger.info(
            "🚀 Global peer manager started",
            extra={"class_name": self.__class__.__name__},
        )

    def stop(self, shutdown_tracker=None):
        """Stop the global peer manager and cleanup all connections"""
        with self.lock:
            if not self.running:
                return

            self.running = False

            # Signal shutdown event for immediate worker thread wake
            self.shutdown_event.set()

            # Stop all peer managers
            peer_manager_count = len(self.peer_managers)
            logger.debug(
                f"Stopping {peer_manager_count} peer managers",
                extra={"class_name": self.__class__.__name__},
            )

            for manager in self.peer_managers.values():
                manager.stop()
                # Update progress tracker
                if shutdown_tracker:
                    shutdown_tracker.mark_completed("peer_managers", 1)

            self.peer_managers.clear()

            # Clear torrent tracking
            self.active_torrents.clear()

        # Stop peer server
        logger.debug("Stopping peer server", extra={"class_name": self.__class__.__name__})
        self.peer_server.stop()
        if shutdown_tracker:
            shutdown_tracker.mark_completed("network_connections", 1)

        # Stop shared async executor
        logger.debug(
            "Stopping SharedAsyncExecutor",
            extra={"class_name": self.__class__.__name__},
        )
        self.executor.stop()
        if shutdown_tracker:
            shutdown_tracker.mark_completed("async_executor", 1)

        # Stop ConnectionManager (stop all GLib timers)
        logger.debug("Stopping ConnectionManager", extra={"class_name": self.__class__.__name__})
        from d_fake_seeder.domain.torrent.connection_manager import (
            get_connection_manager,
        )

        connection_manager = get_connection_manager()
        connection_manager.shutdown()

        # Wait for worker thread to finish with aggressive timeout
        if self.worker_thread and self.worker_thread.is_alive():
            join_timeout = 1.0  # Max 1 second for aggressive shutdown
            logger.debug(
                f"⏱️ Waiting for worker thread to finish (timeout: {join_timeout}s)",
                extra={"class_name": self.__class__.__name__},
            )
            self.worker_thread.join(timeout=join_timeout)

            # Log if thread is still alive after timeout
            if self.worker_thread.is_alive():
                logger.warning(
                    "⚠️ GlobalPeerManager worker thread still alive after timeout - forcing shutdown",
                    extra={"class_name": self.__class__.__name__},
                )
                if shutdown_tracker:
                    shutdown_tracker.mark_component_timeout("background_workers")
            else:
                logger.debug(
                    "✅ Worker thread stopped cleanly",
                    extra={"class_name": self.__class__.__name__},
                )
                if shutdown_tracker:
                    shutdown_tracker.mark_completed("background_workers", 1)
        else:
            # No worker thread to stop
            if shutdown_tracker:
                shutdown_tracker.mark_completed("background_workers", 1)

        logger.info(
            "🛑 Global peer manager stopped",
            extra={"class_name": self.__class__.__name__},
        )

    def add_torrent(self, torrent):
        """Add a torrent to be tracked by the global peer manager"""
        if not torrent or not hasattr(torrent, "id"):
            return

        torrent_id = str(torrent.id)

        # Debug: Log the actual type of object we received
        logger.debug(
            f"🔍 Adding torrent {torrent_id}: type={type(torrent).__name__}, "
            f"has_get_torrent_file={hasattr(torrent, 'get_torrent_file')}",
            extra={"class_name": self.__class__.__name__},
        )

        try:
            # Extract torrent info
            torrent_file = torrent.get_torrent_file()
            if not torrent_file:
                logger.warning(f"❌ No torrent file returned for {torrent_id}")
                return

            # Debug: Check what attributes the torrent file has
            attrs = [attr for attr in dir(torrent_file) if not attr.startswith("_")]
            logger.debug(
                f"🔍 Torrent file for {torrent_id}: "
                f"type={type(torrent_file).__name__}, "
                f"has_info_hash={hasattr(torrent_file, 'info_hash')}, "
                f"attributes={attrs}",
                extra={"class_name": self.__class__.__name__},
            )

            # Try different ways to get the info hash
            info_hash = None
            if hasattr(torrent_file, "info_hash"):
                info_hash = torrent_file.info_hash
            elif hasattr(torrent_file, "get_info_hash_hex"):
                info_hash_hex = torrent_file.get_info_hash_hex()
                if info_hash_hex:
                    try:
                        info_hash = bytes.fromhex(info_hash_hex)
                    except ValueError:
                        logger.warning(f"Invalid hex info_hash for {torrent_id}: " f"{info_hash_hex}")
                        return

            if not info_hash:
                logger.warning(f"Could not get info_hash for {torrent_id} - " f"no valid method found")
                return
            if isinstance(info_hash, str):
                info_hash = info_hash.encode()

            info_hash_hex = info_hash.hex()

            with self.lock:
                # Store torrent info
                self.active_torrents[torrent_id] = {
                    "torrent": torrent,
                    "info_hash": info_hash,
                    "info_hash_hex": info_hash_hex,
                    "name": getattr(torrent_file, "name", f"Torrent {torrent_id}"),
                    "added_time": time.time(),
                }

                # Create peer manager if not exists
                if info_hash_hex not in self.peer_managers:
                    # Generate our peer ID
                    our_peer_id = self._generate_peer_id()

                    # Use configured max connections
                    max_peer_connections = getattr(self.settings, "max_connections_per_torrent", 50)
                    manager = PeerProtocolManager(
                        info_hash,
                        our_peer_id,
                        max_connections=max_peer_connections,
                        connection_callback=self.peer_server.connection_callback,
                    )
                    manager.start()  # Start the connection manager
                    self.peer_managers[info_hash_hex] = manager

                    # Register info hash with peer server for incoming connections
                    self.peer_server.add_info_hash(info_hash)

                    # Add peers from seeder if available
                    seeder = torrent.get_seeder()
                    if seeder and hasattr(seeder, "peers"):
                        peer_addresses = [str(peer) for peer in seeder.peers]
                        if peer_addresses:
                            manager.add_peers(peer_addresses)

                    logger.debug(
                        f"🎯 Added torrent {torrent_id} " f"({info_hash_hex[:12]}...) with {len(peer_addresses)} peers",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    logger.debug(
                        f"🔄 Torrent {torrent_id} already tracked (shared info_hash)",
                        extra={"class_name": self.__class__.__name__},
                    )

        except Exception as e:
            logger.error(
                f"Failed to add torrent {torrent_id}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def remove_torrent(self, torrent_id: str):
        """Remove a torrent from tracking"""
        torrent_id = str(torrent_id)

        with self.lock:
            if torrent_id not in self.active_torrents:
                return

            torrent_info = self.active_torrents.pop(torrent_id)
            info_hash_hex = torrent_info["info_hash_hex"]

            # Check if other torrents are using this info_hash
            still_used = any(t["info_hash_hex"] == info_hash_hex for t in self.active_torrents.values())

            if not still_used and info_hash_hex in self.peer_managers:
                # Stop and remove peer manager
                self.peer_managers[info_hash_hex].stop()
                del self.peer_managers[info_hash_hex]

                logger.debug(
                    f"🗑️ Removed torrent {torrent_id} and stopped peer manager",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.debug(
                    f"🔄 Removed torrent {torrent_id} " f"(peer manager still used by other torrents)",
                    extra={"class_name": self.__class__.__name__},
                )

    def _invalidate_manager_stats(self, info_hash_hex: str):
        """Mark a peer manager's stats as dirty for recalculation"""
        self._dirty_managers.add(info_hash_hex)
        self._stats_cache_dirty = True

    def update_torrent_peers(self, torrent_id: str, peer_addresses: List[str]):
        """Update peer list for a specific torrent"""
        torrent_id = str(torrent_id)

        with self.lock:
            if torrent_id not in self.active_torrents:
                return

            info_hash_hex = self.active_torrents[torrent_id]["info_hash_hex"]
            if info_hash_hex in self.peer_managers:
                self.peer_managers[info_hash_hex].add_peers(peer_addresses)
                # Mark this manager's stats as dirty
                self._invalidate_manager_stats(info_hash_hex)

                logger.debug(
                    f"🔄 Updated {len(peer_addresses)} peers for " f"torrent {torrent_id}",
                    extra={"class_name": self.__class__.__name__},
                )

    def get_global_stats(self) -> Dict:
        """Get global peer statistics"""
        with self.lock:
            return self.global_peer_stats.copy()

    def get_torrent_peers(self, torrent_id: str) -> List[Dict]:
        """Get peer information for a specific torrent"""
        torrent_id = str(torrent_id)

        with self.lock:
            if torrent_id not in self.active_torrents:
                return []

            info_hash_hex = self.active_torrents[torrent_id]["info_hash_hex"]
            if info_hash_hex not in self.peer_managers:
                return []

            peer_stats = self.peer_managers[info_hash_hex].get_peer_stats()

            # Convert to list format for UI
            peer_list = []
            for peer_id, stats in peer_stats.items():
                peer_list.append(
                    {
                        "address": stats.get("address", peer_id),
                        "client": stats.get("client", "Unknown"),
                        "connected": stats.get("connected", False),
                        "is_seed": stats.get("is_seed", False),
                        "upload_rate": stats.get("upload_rate", 0.0),
                        "download_rate": stats.get("download_rate", 0.0),
                        "progress": stats.get("progress", 0.0),
                    }
                )

            return peer_list

    def _worker_loop(self):
        """Main worker loop that runs in background thread"""
        logger.debug(
            "🔄 Global peer manager worker loop started",
            extra={"class_name": self.__class__.__name__},
        )

        while not self.shutdown_event.is_set():
            try:
                current_time = time.time()

                # Update peer connections periodically
                if current_time - self.last_peer_update > self.peer_update_interval:
                    self._update_peer_connections()
                    self.last_peer_update = current_time

                # Update statistics more frequently
                if current_time - self.last_stats_update > self.stats_update_interval:
                    self._update_global_stats()
                    self.last_stats_update = current_time

                # Calculate intelligent sleep interval - wait until next event
                next_peer_update = self.last_peer_update + self.peer_update_interval
                next_stats_update = self.last_stats_update + self.stats_update_interval
                next_event_time = min(next_peer_update, next_stats_update)
                sleep_time = max(self.manager_sleep_interval, next_event_time - time.time())

                # Use event-based sleep for immediate wake on shutdown
                if self.shutdown_event.wait(timeout=sleep_time):
                    break  # Shutdown event was set

            except Exception as e:
                logger.error(
                    f"Error in global peer manager worker: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                # Back off on error with event-based sleep
                if self.shutdown_event.wait(timeout=self.manager_error_sleep_interval):
                    break

        logger.debug(
            "🛑 Global peer manager worker loop stopped",
            extra={"class_name": self.__class__.__name__},
        )

    def _update_peer_connections(self):
        """Update peer connections for all active torrents"""
        with self.lock:
            if not self.peer_managers:
                return

            for info_hash_hex, manager in self.peer_managers.items():
                try:
                    # Find torrents using this manager
                    using_torrents = [t for t in self.active_torrents.values() if t["info_hash_hex"] == info_hash_hex]

                    if using_torrents:
                        # Update peers from seeder data
                        for torrent_info in using_torrents:
                            torrent = torrent_info["torrent"]
                            seeder = torrent.get_seeder()
                            if seeder and hasattr(seeder, "peers"):
                                peer_addresses = [str(peer) for peer in seeder.peers]
                                if peer_addresses:
                                    manager.add_peers(peer_addresses)
                                    # Mark this manager's stats as dirty
                                    self._invalidate_manager_stats(info_hash_hex)

                except Exception as e:
                    logger.error(
                        f"Error updating peers for {info_hash_hex}: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

    def _update_global_stats(self):
        """Update global statistics from all peer managers (with dirty-tracking cache)"""
        with self.lock:
            # Only recalculate if something changed
            if not self._stats_cache_dirty:
                return

            # Recalculate stats only for dirty managers
            for info_hash_hex in self._dirty_managers:
                if info_hash_hex not in self.peer_managers:
                    # Manager was removed, clear its cache
                    if info_hash_hex in self._per_manager_stats:
                        del self._per_manager_stats[info_hash_hex]
                    continue

                manager = self.peer_managers[info_hash_hex]
                try:
                    peer_stats = manager.get_peer_stats()

                    # Aggregate stats for this manager
                    manager_totals = {
                        "total_peers": 0,
                        "connected_peers": 0,
                        "seeds": 0,
                        "leechers": 0,
                        "upload_connections": 0,
                        "download_connections": 0,
                    }

                    for stats in peer_stats.values():
                        manager_totals["total_peers"] += 1
                        if stats.get("connected", False):
                            manager_totals["connected_peers"] += 1
                            if stats.get("is_seed", False):
                                manager_totals["seeds"] += 1
                            else:
                                manager_totals["leechers"] += 1
                            if stats.get("upload_rate", 0) > 0:
                                manager_totals["upload_connections"] += 1
                            if stats.get("download_rate", 0) > 0:
                                manager_totals["download_connections"] += 1

                    # Cache the aggregated stats for this manager
                    self._per_manager_stats[info_hash_hex] = manager_totals

                except Exception as e:
                    logger.debug(f"Error getting stats from manager {info_hash_hex}: {e}")

            # Clear dirty set
            self._dirty_managers.clear()

            # Sum up all cached manager stats
            total_peers = 0
            connected_peers = 0
            seeds = 0
            leechers = 0
            upload_connections = 0
            download_connections = 0

            for manager_stats in self._per_manager_stats.values():
                total_peers += manager_stats["total_peers"]
                connected_peers += manager_stats["connected_peers"]
                seeds += manager_stats["seeds"]
                leechers += manager_stats["leechers"]
                upload_connections += manager_stats["upload_connections"]
                download_connections += manager_stats["download_connections"]

            # Get incoming connection stats from peer server
            server_stats = self.peer_server.get_stats()
            incoming_connections = server_stats.get("active_connections", 0)

            # Update global stats
            self.global_peer_stats.update(
                {
                    "total_peers": total_peers,
                    "connected_peers": connected_peers,
                    "seeds": seeds,
                    "leechers": leechers,
                    "upload_connections": upload_connections,
                    "download_connections": download_connections,
                    "incoming_connections": incoming_connections,
                    "total_torrents": len(self.active_torrents),
                }
            )

            # Mark cache as clean
            self._stats_cache_dirty = False

    def _generate_peer_id(self) -> bytes:
        """Generate a unique peer ID for this client"""
        import uuid

        unique_id = str(uuid.uuid4()).encode()
        return hashlib.sha1(unique_id).digest()[:20]
