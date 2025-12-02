"""
Connection Manager

Centralized connection management for both incoming and outgoing peer connections.
Provides shared logic for connection counting, filtering, and lifetime management.
"""

# isort: skip_file

# fmt: off
import time
from typing import Dict, List, Tuple

import gi

gi.require_version("GLib", "2.0")

from gi.repository import GLib  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.domain.torrent.model.connection_peer import (  # noqa: E402
    ConnectionPeer,
)
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.constants import ConnectionConstants  # noqa: E402

# fmt: on


class ConnectionManager:
    """Shared connection management logic for incoming and outgoing connections"""

    def __init__(self):
        self.settings = AppSettings.get_instance()

        # Global connection storage
        self.all_incoming_connections: Dict[str, ConnectionPeer] = {}
        self.all_outgoing_connections: Dict[str, ConnectionPeer] = {}

        # Track when connections failed for timeout exclusion
        self.incoming_failed_times: Dict[str, float] = {}
        self.outgoing_failed_times: Dict[str, float] = {}

        # Track when connections were added for display time calculation
        self.incoming_display_timers: Dict[str, float] = {}
        self.outgoing_display_timers: Dict[str, float] = {}

        # Track when connections were created for age-based expiry
        self.incoming_creation_times: Dict[str, float] = {}
        self.outgoing_creation_times: Dict[str, float] = {}

        # Connection display settings (based on tickspeed)
        self.failed_connection_display_cycles = (
            ConnectionConstants.FAILED_CONNECTION_DISPLAY_CYCLES
        )  # Show failed connections for 1 cycle
        self.minimum_display_cycles = ConnectionConstants.MIN_DISPLAY_CYCLES  # Minimum cycles to show any connection
        self.failed_connection_timeout_cycles = (
            ConnectionConstants.TIMEOUT_CYCLES
        )  # Exclude failed connections after 3 cycles

        # Callbacks for UI updates
        self.update_callbacks: List[callable] = []

        # Throttling mechanism for callbacks
        self.last_callback_time = 0.0
        connection_manager_config = getattr(self.settings, "connection_manager", {})
        self.callback_throttle_delay = connection_manager_config.get("callback_throttle_delay_seconds", 1.0)
        self.pending_callback_timer = None

        # Single periodic cleanup timer instead of per-connection timers (O(1) instead of O(n))
        self.cleanup_timer_id = None
        self.cleanup_interval_seconds = connection_manager_config.get(
            "cleanup_interval_seconds", ConnectionConstants.CLEANUP_INTERVAL_SECONDS
        )
        self._start_cleanup_timer()

    def get_failed_connection_display_time(self) -> float:
        """Get failed connection display time based on current tickspeed"""
        return self.failed_connection_display_cycles * self.settings.tickspeed

    def get_minimum_display_time(self) -> float:
        """Get minimum connection display time based on current tickspeed"""
        return self.minimum_display_cycles * self.settings.tickspeed

    def get_failed_connection_timeout(self) -> float:
        """Get failed connection timeout based on current tickspeed"""
        return self.failed_connection_timeout_cycles * self.settings.tickspeed

    def add_update_callback(self, callback):
        """Add callback for connection count updates"""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)

    def remove_update_callback(self, callback):
        """Remove callback for connection count updates"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)

    def notify_update_callbacks(self):
        """Notify all registered callbacks of connection changes (throttled)"""
        current_time = time.time()

        # If enough time has passed since last callback, execute immediately
        if current_time - self.last_callback_time >= self.callback_throttle_delay:
            self._execute_callbacks()
            self.last_callback_time = current_time
        else:
            # Otherwise, schedule a delayed callback if none is pending
            if self.pending_callback_timer is None:
                delay_ms = int((self.callback_throttle_delay - (current_time - self.last_callback_time)) * 1000)
                self.pending_callback_timer = GLib.timeout_add(delay_ms, self._delayed_callback)

    def _execute_callbacks(self):
        """Execute all registered callbacks"""
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in connection update callback: {e}")

    def _delayed_callback(self):
        """GLib timeout callback for delayed execution"""
        self._execute_callbacks()
        self.last_callback_time = time.time()
        self.pending_callback_timer = None
        return False  # Don't repeat the timeout

    def _start_cleanup_timer(self):
        """Start the single periodic cleanup timer"""
        if self.cleanup_timer_id is None:
            self.cleanup_timer_id = GLib.timeout_add_seconds(self.cleanup_interval_seconds, self._periodic_cleanup)
            logger.debug("Started periodic connection cleanup timer")

    def _stop_cleanup_timer(self):
        """Stop the periodic cleanup timer"""
        if self.cleanup_timer_id is not None:
            GLib.source_remove(self.cleanup_timer_id)
            self.cleanup_timer_id = None
            logger.debug("Stopped periodic connection cleanup timer")

    def _periodic_cleanup(self):
        """Periodic cleanup of expired failed connections and enforcement of connection limits"""
        current_time = time.time()
        failed_display_time = self.get_failed_connection_display_time()

        # Get connection limits and expiry settings from config
        connection_manager_config = getattr(self.settings, "connection_manager", {})
        max_incoming = connection_manager_config.get("max_incoming_connections", 500)
        max_outgoing = connection_manager_config.get("max_outgoing_connections", 500)
        connection_expiry = connection_manager_config.get("connection_expiry_seconds", 600)

        # Cleanup expired incoming connections
        incoming_to_remove = []
        for connection_key, conn in self.all_incoming_connections.items():
            # Remove failed connections after display time
            if hasattr(conn, "status") and conn.status == "failed":
                failed_time = self.incoming_failed_times.get(connection_key, current_time)
                if current_time - failed_time >= failed_display_time:
                    incoming_to_remove.append(connection_key)
            # Remove old connections based on age (even if not failed)
            elif connection_key in self.incoming_creation_times:
                creation_time = self.incoming_creation_times[connection_key]
                if current_time - creation_time >= connection_expiry:
                    incoming_to_remove.append(connection_key)

        for connection_key in incoming_to_remove:
            self._remove_incoming_connection_by_key(connection_key)

        # Cleanup expired outgoing connections
        outgoing_to_remove = []
        for connection_key, conn in self.all_outgoing_connections.items():
            # Remove failed connections after display time
            if hasattr(conn, "status") and conn.status == "failed":
                failed_time = self.outgoing_failed_times.get(connection_key, current_time)
                if current_time - failed_time >= failed_display_time:
                    outgoing_to_remove.append(connection_key)
            # Remove old connections based on age (even if not failed)
            elif connection_key in self.outgoing_creation_times:
                creation_time = self.outgoing_creation_times[connection_key]
                if current_time - creation_time >= connection_expiry:
                    outgoing_to_remove.append(connection_key)

        for connection_key in outgoing_to_remove:
            self._remove_outgoing_connection_by_key(connection_key)

        # Enforce max connection limits using LRU eviction
        incoming_overflow = len(self.all_incoming_connections) - max_incoming
        if incoming_overflow > 0:
            # Remove oldest connections first
            sorted_incoming = sorted(self.incoming_creation_times.items(), key=lambda x: x[1])  # Sort by creation time
            for connection_key, _ in sorted_incoming[:incoming_overflow]:
                self._remove_incoming_connection_by_key(connection_key)
            logger.warning(
                f"Enforced incoming connection limit: removed {incoming_overflow} oldest connections "
                f"(max: {max_incoming})"
            )

        outgoing_overflow = len(self.all_outgoing_connections) - max_outgoing
        if outgoing_overflow > 0:
            # Remove oldest connections first
            sorted_outgoing = sorted(self.outgoing_creation_times.items(), key=lambda x: x[1])  # Sort by creation time
            for connection_key, _ in sorted_outgoing[:outgoing_overflow]:
                self._remove_outgoing_connection_by_key(connection_key)
            logger.warning(
                f"Enforced outgoing connection limit: removed {outgoing_overflow} oldest connections "
                f"(max: {max_outgoing})"
            )

        # Log if we cleaned up any connections
        total_removed = len(incoming_to_remove) + len(outgoing_to_remove)
        if total_removed > 0:
            logger.debug(
                f"Periodic cleanup removed {len(incoming_to_remove)} incoming "
                f"and {len(outgoing_to_remove)} outgoing expired connections"
            )

        return True  # Continue timer

    # Incoming connection management
    def add_incoming_connection(self, address: str, port: int, **kwargs) -> str:
        """Add a new incoming connection"""
        connection_key = f"{address}:{port}"

        if connection_key not in self.all_incoming_connections:
            connection_kwargs = {
                "address": address,
                "port": port,
                "direction": "incoming",
                **kwargs,
            }
            connection_peer = ConnectionPeer(**connection_kwargs)
            self.all_incoming_connections[connection_key] = connection_peer

            # Set timers
            current_time = time.time()
            self.incoming_display_timers[connection_key] = current_time
            self.incoming_creation_times[connection_key] = current_time

            logger.debug(f"Added incoming connection: {connection_key}")
            self.notify_update_callbacks()

        return connection_key

    def update_incoming_connection(self, address: str, port: int, **kwargs):
        """Update an existing incoming connection"""
        connection_key = f"{address}:{port}"

        if connection_key in self.all_incoming_connections:
            connection_peer = self.all_incoming_connections[connection_key]

            # Update properties
            for key, value in kwargs.items():
                if hasattr(connection_peer, key):
                    setattr(connection_peer, key, value)

            # Track when this connection failed (periodic cleanup will handle removal)
            if connection_peer.status == "failed":
                self.incoming_failed_times[connection_key] = time.time()

            self.notify_update_callbacks()

    def remove_incoming_connection(self, address: str, port: int):
        """Remove an incoming connection"""
        connection_key = f"{address}:{port}"
        self._remove_incoming_connection_by_key(connection_key)

    def _remove_incoming_connection_by_key(self, connection_key: str):
        """Remove an incoming connection by key"""
        if connection_key not in self.all_incoming_connections:
            return

        # Remove from storage
        del self.all_incoming_connections[connection_key]

        # Clean up all tracking dictionaries
        if connection_key in self.incoming_display_timers:
            del self.incoming_display_timers[connection_key]

        if connection_key in self.incoming_failed_times:
            del self.incoming_failed_times[connection_key]

        if connection_key in self.incoming_creation_times:
            del self.incoming_creation_times[connection_key]

        logger.debug(f"Removed incoming connection: {connection_key}")
        self.notify_update_callbacks()

    # Outgoing connection management
    def add_outgoing_connection(self, address: str, port: int, **kwargs) -> str:
        """Add a new outgoing connection"""
        connection_key = f"{address}:{port}"

        if connection_key not in self.all_outgoing_connections:
            connection_kwargs = {
                "address": address,
                "port": port,
                "direction": "outgoing",
                **kwargs,
            }
            connection_peer = ConnectionPeer(**connection_kwargs)
            self.all_outgoing_connections[connection_key] = connection_peer

            # Set timers
            current_time = time.time()
            self.outgoing_display_timers[connection_key] = current_time
            self.outgoing_creation_times[connection_key] = current_time

            logger.debug(f"Added outgoing connection: {connection_key}")
            self.notify_update_callbacks()

        return connection_key

    def update_outgoing_connection(self, address: str, port: int, **kwargs):
        """Update an existing outgoing connection"""
        connection_key = f"{address}:{port}"

        if connection_key in self.all_outgoing_connections:
            connection_peer = self.all_outgoing_connections[connection_key]

            # Update properties
            for key, value in kwargs.items():
                if hasattr(connection_peer, key):
                    setattr(connection_peer, key, value)

            # Track when this connection failed (periodic cleanup will handle removal)
            if connection_peer.status == "failed":
                self.outgoing_failed_times[connection_key] = time.time()

            self.notify_update_callbacks()

    def remove_outgoing_connection(self, address: str, port: int):
        """Remove an outgoing connection"""
        connection_key = f"{address}:{port}"
        self._remove_outgoing_connection_by_key(connection_key)

    def _remove_outgoing_connection_by_key(self, connection_key: str):
        """Remove an outgoing connection by key"""
        if connection_key not in self.all_outgoing_connections:
            return

        # Remove from storage
        del self.all_outgoing_connections[connection_key]

        # Clean up all tracking dictionaries
        if connection_key in self.outgoing_display_timers:
            del self.outgoing_display_timers[connection_key]

        if connection_key in self.outgoing_failed_times:
            del self.outgoing_failed_times[connection_key]

        if connection_key in self.outgoing_creation_times:
            del self.outgoing_creation_times[connection_key]

        logger.debug(f"Removed outgoing connection: {connection_key}")
        self.notify_update_callbacks()

    # Query functions for global statistics
    def get_global_connection_count(self) -> int:
        """Get total number of connections globally (incoming + outgoing)"""
        return len(self.all_incoming_connections) + len(self.all_outgoing_connections)

    def get_global_connection_count_excluding_old_failed(self) -> int:
        """Get total connections excluding failed connections that have timed out"""
        current_time = time.time()
        count = 0

        # Count incoming connections excluding old failed ones
        for connection_key, conn in self.all_incoming_connections.items():
            if hasattr(conn, "status") and conn.status == "failed":
                # Check if this failed connection has timed out
                failed_time = self.incoming_failed_times.get(connection_key, current_time)
                if current_time - failed_time < self.get_failed_connection_timeout():
                    count += 1  # Include recent failed connections
                # Exclude old failed connections from count
            else:
                count += 1  # Include all non-failed connections

        # Count outgoing connections excluding old failed ones
        for connection_key, conn in self.all_outgoing_connections.items():
            if hasattr(conn, "status") and conn.status == "failed":
                # Check if this failed connection has timed out
                failed_time = self.outgoing_failed_times.get(connection_key, current_time)
                if current_time - failed_time < self.get_failed_connection_timeout():
                    count += 1  # Include recent failed connections
                # Exclude old failed connections from count
            else:
                count += 1  # Include all non-failed connections

        return count

    def get_global_active_connection_count(self) -> int:
        """Get number of active/connected connections globally"""
        active_count = 0

        # Count active incoming connections
        for conn in self.all_incoming_connections.values():
            if hasattr(conn, "connected") and conn.connected:
                active_count += 1

        # Count active outgoing connections
        for conn in self.all_outgoing_connections.values():
            if hasattr(conn, "connected") and conn.connected:
                active_count += 1

        return active_count

    def get_global_incoming_count(self) -> int:
        """Get total number of incoming connections globally"""
        return len(self.all_incoming_connections)

    def get_global_outgoing_count(self) -> int:
        """Get total number of outgoing connections globally"""
        return len(self.all_outgoing_connections)

    def get_global_active_incoming_count(self) -> int:
        """Get number of active incoming connections globally"""
        active_count = 0
        for conn in self.all_incoming_connections.values():
            if hasattr(conn, "connected") and conn.connected:
                active_count += 1
        return active_count

    def get_global_active_outgoing_count(self) -> int:
        """Get number of active outgoing connections globally"""
        active_count = 0
        for conn in self.all_outgoing_connections.values():
            if hasattr(conn, "connected") and conn.connected:
                active_count += 1
        return active_count

    # Query functions for torrent-specific statistics
    def get_torrent_connection_count(self, torrent_hash: str) -> int:
        """Get total number of connections for a specific torrent"""
        incoming_count = sum(
            1 for conn in self.all_incoming_connections.values() if getattr(conn, "torrent_hash", "") == torrent_hash
        )
        outgoing_count = sum(
            1 for conn in self.all_outgoing_connections.values() if getattr(conn, "torrent_hash", "") == torrent_hash
        )
        return incoming_count + outgoing_count

    def get_torrent_active_connection_count(self, torrent_hash: str) -> int:
        """Get number of active connections for a specific torrent"""
        active_count = 0

        # Count active incoming connections for torrent
        for conn in self.all_incoming_connections.values():
            if getattr(conn, "torrent_hash", "") == torrent_hash and hasattr(conn, "connected") and conn.connected:
                active_count += 1

        # Count active outgoing connections for torrent
        for conn in self.all_outgoing_connections.values():
            if getattr(conn, "torrent_hash", "") == torrent_hash and hasattr(conn, "connected") and conn.connected:
                active_count += 1

        return active_count

    def get_torrent_incoming_connections(self, torrent_hash: str) -> List[Tuple[str, ConnectionPeer]]:
        """Get incoming connections for a specific torrent"""
        return [
            (key, conn)
            for key, conn in self.all_incoming_connections.items()
            if getattr(conn, "torrent_hash", "") == torrent_hash
        ]

    def get_torrent_outgoing_connections(self, torrent_hash: str) -> List[Tuple[str, ConnectionPeer]]:
        """Get outgoing connections for a specific torrent"""
        return [
            (key, conn)
            for key, conn in self.all_outgoing_connections.items()
            if getattr(conn, "torrent_hash", "") == torrent_hash
        ]

    def get_all_incoming_connections(self) -> Dict[str, ConnectionPeer]:
        """Get all incoming connections"""
        return self.all_incoming_connections.copy()

    def get_all_outgoing_connections(self) -> Dict[str, ConnectionPeer]:
        """Get all outgoing connections"""
        return self.all_outgoing_connections.copy()

    def clear_all_connections(self):
        """Clear all connections and stop cleanup timer"""
        # Stop the cleanup timer
        self._stop_cleanup_timer()

        # Clear all data
        self.all_incoming_connections.clear()
        self.all_outgoing_connections.clear()
        self.incoming_display_timers.clear()
        self.outgoing_display_timers.clear()
        self.incoming_failed_times.clear()
        self.outgoing_failed_times.clear()
        self.incoming_creation_times.clear()
        self.outgoing_creation_times.clear()

        logger.debug("Cleared all connections and stopped cleanup timer")
        self.notify_update_callbacks()

        # Restart the cleanup timer for future connections
        self._start_cleanup_timer()

    def shutdown(self):
        """Shutdown the connection manager - stop all timers permanently"""
        logger.info(
            "ConnectionManager shutting down",
            extra={"class_name": self.__class__.__name__},
        )

        # Stop the cleanup timer permanently (don't restart)
        self._stop_cleanup_timer()

        # Stop any pending callback timers
        if hasattr(self, "pending_callback_timer") and self.pending_callback_timer is not None:
            GLib.source_remove(self.pending_callback_timer)
            self.pending_callback_timer = None

        # Clear all data
        self.all_incoming_connections.clear()
        self.all_outgoing_connections.clear()
        self.incoming_display_timers.clear()
        self.outgoing_display_timers.clear()
        self.incoming_failed_times.clear()
        self.outgoing_failed_times.clear()
        self.incoming_creation_times.clear()
        self.outgoing_creation_times.clear()

        logger.info(
            "ConnectionManager shutdown complete",
            extra={"class_name": self.__class__.__name__},
        )

    def get_max_connections(self) -> Tuple[int, int, int]:
        """Get maximum connection limits (incoming, outgoing, total)"""
        max_incoming = getattr(
            self.settings,
            "max_incoming_connections",
            ConnectionConstants.MAX_INCOMING_CONNECTIONS,
        )
        max_outgoing = getattr(
            self.settings,
            "max_outgoing_connections",
            ConnectionConstants.MAX_OUTGOING_CONNECTIONS,
        )
        max_total = max_incoming + max_outgoing
        return max_incoming, max_outgoing, max_total


# Global instance
_connection_manager = None


def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager
