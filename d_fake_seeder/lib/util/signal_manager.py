#!/usr/bin/env python3
"""
Signal Manager Utility

Centralized management of GTK signal connections to prevent memory leaks.
Automatically tracks all signal connections and provides cleanup functionality.
"""

from typing import Any, Callable, Dict, List, Tuple

from lib.logger import logger


class SignalManager:
    """
    Manages GTK signal connections to ensure proper cleanup.

    Usage:
        class MyComponent:
            def __init__(self):
                self.signal_manager = SignalManager()
                self.signal_manager.connect(widget, "clicked", self.on_clicked)

            def cleanup(self):
                self.signal_manager.disconnect_all()
    """

    def __init__(self, component_name: str = None):
        """
        Initialize the signal manager.

        Args:
            component_name: Optional name for logging purposes
        """
        self._connections: List[Tuple[Any, int]] = []
        self._component_name = component_name or "Unknown"

    def connect(self, source: Any, signal: str, handler: Callable, *args, **kwargs) -> int:
        """
        Connect a signal and track it for later cleanup.

        Args:
            source: The object emitting the signal
            signal: The signal name
            handler: The handler function
            *args: Additional arguments to pass to handler
            **kwargs: Additional keyword arguments

        Returns:
            Connection ID
        """
        try:
            connection_id = source.connect(signal, handler, *args, **kwargs)
            self._connections.append((source, connection_id))
            logger.debug(
                f"Signal connected: {signal} -> {handler.__name__} (ID: {connection_id})",
                self._component_name,
            )
            return connection_id
        except Exception as e:
            logger.error(
                f"Failed to connect signal {signal}: {e}",
                self._component_name,
            )
            raise

    def connect_after(self, source: Any, signal: str, handler: Callable, *args, **kwargs) -> int:
        """
        Connect a signal after default handlers and track it for cleanup.

        Args:
            source: The object emitting the signal
            signal: The signal name
            handler: The handler function
            *args: Additional arguments to pass to handler
            **kwargs: Additional keyword arguments

        Returns:
            Connection ID
        """
        try:
            connection_id = source.connect_after(signal, handler, *args, **kwargs)
            self._connections.append((source, connection_id))
            logger.debug(
                f"Signal connected (after): {signal} -> {handler.__name__} (ID: {connection_id})",
                self._component_name,
            )
            return connection_id
        except Exception as e:
            logger.error(
                f"Failed to connect_after signal {signal}: {e}",
                self._component_name,
            )
            raise

    def disconnect(self, source: Any, connection_id: int) -> None:
        """
        Disconnect a specific signal connection.

        Args:
            source: The object that was connected
            connection_id: The connection ID to disconnect
        """
        try:
            source.disconnect(connection_id)
            self._connections.remove((source, connection_id))
            logger.debug(
                f"Signal disconnected (ID: {connection_id})",
                self._component_name,
            )
        except ValueError:
            logger.warning(
                f"Attempted to disconnect untracked connection (ID: {connection_id})",
                self._component_name,
            )
        except Exception as e:
            logger.error(
                f"Failed to disconnect signal (ID: {connection_id}): {e}",
                self._component_name,
            )

    def disconnect_all(self) -> None:
        """Disconnect all tracked signal connections."""
        disconnected_count = 0
        errors = []

        for source, connection_id in self._connections[:]:  # Copy list to avoid modification during iteration
            try:
                source.disconnect(connection_id)
                disconnected_count += 1
            except Exception as e:
                errors.append(f"ID {connection_id}: {e}")

        self._connections.clear()

        if errors:
            logger.warning(
                f"Disconnected {disconnected_count} signals with {len(errors)} errors: {', '.join(errors)}",
                self._component_name,
            )
        else:
            logger.debug(
                f"Disconnected all {disconnected_count} signals successfully",
                self._component_name,
            )

    def get_connection_count(self) -> int:
        """
        Get the number of active signal connections.

        Returns:
            Number of tracked connections
        """
        return len(self._connections)

    def is_connected(self, source: Any, connection_id: int) -> bool:
        """
        Check if a specific connection is tracked.

        Args:
            source: The object to check
            connection_id: The connection ID to check

        Returns:
            True if the connection is tracked
        """
        return (source, connection_id) in self._connections


class SignalManagerMixin:
    """
    Mixin class to add signal management capabilities to components.

    Usage:
        class MyComponent(SignalManagerMixin):
            def __init__(self):
                super().__init__()
                self.init_signal_manager()
                self.signal_manager.connect(widget, "clicked", self.on_clicked)

            def cleanup(self):
                self.cleanup_signals()
    """

    def init_signal_manager(self, component_name: str = None):
        """
        Initialize the signal manager for this component.

        Args:
            component_name: Optional name for logging
        """
        if not hasattr(self, "signal_manager"):
            name = component_name or self.__class__.__name__
            self.signal_manager = SignalManager(name)

    def cleanup_signals(self):
        """Cleanup all signals managed by this component."""
        if hasattr(self, "signal_manager"):
            self.signal_manager.disconnect_all()
