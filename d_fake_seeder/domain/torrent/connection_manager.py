"""
Connection Manager

Centralized connection management for both incoming and outgoing peer connections.
Provides shared logic for connection counting, filtering, and lifetime management.
"""

import time
from typing import Dict, List, Tuple

from domain.app_settings import AppSettings
from domain.torrent.model.connection_peer import ConnectionPeer
from gi.repository import GLib
from lib.logger import logger


class ConnectionManager:
    """Shared connection management logic for incoming and outgoing connections"""

    def __init__(self):
        self.settings = AppSettings.get_instance()

        # Global connection storage
        self.all_incoming_connections: Dict[str, ConnectionPeer] = {}
        self.all_outgoing_connections: Dict[str, ConnectionPeer] = {}

        # Connection timers for cleanup
        self.incoming_removal_timers: Dict[str, int] = {}
        self.outgoing_removal_timers: Dict[str, int] = {}
        self.incoming_display_timers: Dict[str, float] = {}
        self.outgoing_display_timers: Dict[str, float] = {}

        # Track when connections failed for timeout exclusion
        self.incoming_failed_times: Dict[str, float] = {}
        self.outgoing_failed_times: Dict[str, float] = {}

        # Connection display settings (based on tickspeed)
        self.failed_connection_display_cycles = 1  # Show failed connections for 1 cycle
        self.minimum_display_cycles = 1  # Minimum cycles to show any connection
        self.failed_connection_timeout_cycles = 3  # Exclude failed connections after 3 cycles

        # Callbacks for UI updates
        self.update_callbacks: List[callable] = []

        # Throttling mechanism for callbacks
        self.last_callback_time = 0.0
        connection_manager_config = getattr(self.settings, "connection_manager", {})
        self.callback_throttle_delay = connection_manager_config.get("callback_throttle_delay_seconds", 1.0)
        self.pending_callback_timer = None

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

            # Set display timer
            self.incoming_display_timers[connection_key] = time.time()

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

            # Schedule removal if connection failed
            if connection_peer.status == "failed":
                # Track when this connection failed for timeout exclusion
                self.incoming_failed_times[connection_key] = time.time()
                self._schedule_incoming_removal(connection_key)

            self.notify_update_callbacks()

    def remove_incoming_connection(self, address: str, port: int):
        """Remove an incoming connection"""
        connection_key = f"{address}:{port}"
        self._remove_incoming_connection_by_key(connection_key)

    def _schedule_incoming_removal(self, connection_key: str):
        """Schedule removal of a failed incoming connection after display time"""
        if connection_key in self.incoming_removal_timers:
            GLib.source_remove(self.incoming_removal_timers[connection_key])

        def remove_connection():
            self._remove_incoming_connection_by_key(connection_key)
            return False

        timer_id = GLib.timeout_add_seconds(int(self.get_failed_connection_display_time()), remove_connection)
        self.incoming_removal_timers[connection_key] = timer_id

    def _remove_incoming_connection_by_key(self, connection_key: str):
        """Remove an incoming connection by key"""
        if connection_key not in self.all_incoming_connections:
            return

        # Cancel removal timer
        if connection_key in self.incoming_removal_timers:
            GLib.source_remove(self.incoming_removal_timers[connection_key])
            del self.incoming_removal_timers[connection_key]

        # Remove from storage
        del self.all_incoming_connections[connection_key]

        # Clean up display timer
        if connection_key in self.incoming_display_timers:
            del self.incoming_display_timers[connection_key]

        # Clean up failed time tracking
        if connection_key in self.incoming_failed_times:
            del self.incoming_failed_times[connection_key]

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

            # Set display timer
            self.outgoing_display_timers[connection_key] = time.time()

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

            # Schedule removal if connection failed
            if connection_peer.status == "failed":
                # Track when this connection failed for timeout exclusion
                self.outgoing_failed_times[connection_key] = time.time()
                self._schedule_outgoing_removal(connection_key)

            self.notify_update_callbacks()

    def remove_outgoing_connection(self, address: str, port: int):
        """Remove an outgoing connection"""
        connection_key = f"{address}:{port}"
        self._remove_outgoing_connection_by_key(connection_key)

    def _schedule_outgoing_removal(self, connection_key: str):
        """Schedule removal of a failed outgoing connection after display time"""
        if connection_key in self.outgoing_removal_timers:
            GLib.source_remove(self.outgoing_removal_timers[connection_key])

        def remove_connection():
            self._remove_outgoing_connection_by_key(connection_key)
            return False

        timer_id = GLib.timeout_add_seconds(int(self.get_failed_connection_display_time()), remove_connection)
        self.outgoing_removal_timers[connection_key] = timer_id

    def _remove_outgoing_connection_by_key(self, connection_key: str):
        """Remove an outgoing connection by key"""
        if connection_key not in self.all_outgoing_connections:
            return

        # Cancel removal timer
        if connection_key in self.outgoing_removal_timers:
            GLib.source_remove(self.outgoing_removal_timers[connection_key])
            del self.outgoing_removal_timers[connection_key]

        # Remove from storage
        del self.all_outgoing_connections[connection_key]

        # Clean up display timer
        if connection_key in self.outgoing_display_timers:
            del self.outgoing_display_timers[connection_key]

        # Clean up failed time tracking
        if connection_key in self.outgoing_failed_times:
            del self.outgoing_failed_times[connection_key]

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
        """Clear all connections and timers"""
        # Cancel all timers
        for timer_id in self.incoming_removal_timers.values():
            GLib.source_remove(timer_id)
        for timer_id in self.outgoing_removal_timers.values():
            GLib.source_remove(timer_id)

        # Clear all data
        self.all_incoming_connections.clear()
        self.all_outgoing_connections.clear()
        self.incoming_removal_timers.clear()
        self.outgoing_removal_timers.clear()
        self.incoming_display_timers.clear()
        self.outgoing_display_timers.clear()
        self.incoming_failed_times.clear()
        self.outgoing_failed_times.clear()

        logger.debug("Cleared all connections")
        self.notify_update_callbacks()

    def get_max_connections(self) -> Tuple[int, int, int]:
        """Get maximum connection limits (incoming, outgoing, total)"""
        max_incoming = getattr(self.settings, "max_incoming_connections", 200)
        max_outgoing = getattr(self.settings, "max_outgoing_connections", 50)
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
