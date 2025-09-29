"""
D-Bus Service Manager for DFakeSeeder

Provides clean D-Bus IPC service with singleton pattern and observer pattern
for communication with external processes (like tray applications).

Maintains clear separation of concerns - no UI dependencies.
"""

import threading
from typing import Callable, Optional

import gi

gi.require_version("GObject", "2.0")

from gi.repository import GObject  # noqa: E402
from lib.component.dbus_tray_server_simple import TrayDBusServer  # noqa: E402
from lib.logger import logger  # noqa: E402


class DBusService(GObject.Object):
    """
    Singleton D-Bus service manager with observer pattern.

    Provides clean separation of concerns for D-Bus communication,
    allowing external processes to interact with the main application.
    """

    _instance: Optional["DBusService"] = None
    _lock = threading.Lock()

    # GObject signals for observer pattern
    __gsignals__ = {
        "show-window-requested": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "quit-requested": (GObject.SIGNAL_RUN_FIRST, None, ()),
        "status-update": (GObject.SIGNAL_RUN_FIRST, None, (str,)),
        "torrent-count-update": (GObject.SIGNAL_RUN_FIRST, None, (int, int)),
    }

    def __init__(self):
        """Initialize D-Bus service (private - use get_instance())."""
        super().__init__()
        self.dbus_server: Optional[TrayDBusServer] = None
        self.is_active = False

        logger.info("D-Bus service manager initialized", extra={"class_name": self.__class__.__name__})

    @classmethod
    def get_instance(cls) -> "DBusService":
        """
        Get singleton instance of D-Bus service.

        Returns:
            DBusService: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.debug("D-Bus service singleton created", extra={"class_name": cls.__name__})
        return cls._instance

    def start_service(self) -> bool:
        """
        Start the D-Bus service.

        Returns:
            bool: True if service started successfully, False otherwise
        """
        logger.info("Starting D-Bus service", extra={"class_name": self.__class__.__name__})

        try:
            # Create D-Bus server
            self.dbus_server = TrayDBusServer()

            # Set up callbacks that emit GObject signals
            self.dbus_server.set_callbacks(
                show_window_callback=self._on_show_window_requested,
                quit_callback=self._on_quit_requested,
                get_status_callback=self._get_current_status,
            )

            self.is_active = True
            logger.info("D-Bus service started successfully", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to start D-Bus service: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            return False

    def stop_service(self):
        """Stop the D-Bus service."""
        logger.info("Stopping D-Bus service", extra={"class_name": self.__class__.__name__})

        try:
            if self.dbus_server:
                self.dbus_server.notify_application_closing()
                self.dbus_server.cleanup()
                self.dbus_server = None

            self.is_active = False
            logger.info("D-Bus service stopped", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error stopping D-Bus service: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def is_service_active(self) -> bool:
        """
        Check if D-Bus service is active.

        Returns:
            bool: True if service is active, False otherwise
        """
        return self.is_active and self.dbus_server is not None

    def broadcast_status_update(self, status_text: str):
        """
        Broadcast status update to all D-Bus clients.

        Args:
            status_text: New status text to broadcast
        """
        if self.is_service_active():
            try:
                self.dbus_server.update_tray_status(status_text)
                self.emit("status-update", status_text)
                logger.debug(f"Status broadcasted: {status_text}", extra={"class_name": self.__class__.__name__})
            except Exception as e:
                logger.error(
                    f"Error broadcasting status: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
                )

    def broadcast_torrent_count(self, active_count: int, total_count: int):
        """
        Broadcast torrent count update to all D-Bus clients.

        Args:
            active_count: Number of active torrents
            total_count: Total number of torrents
        """
        if self.is_service_active():
            try:
                self.dbus_server.update_torrent_count(active_count, total_count)
                self.emit("torrent-count-update", active_count, total_count)
                logger.debug(
                    f"Torrent count broadcasted: {active_count}/{total_count}",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.error(
                    f"Error broadcasting torrent count: {e}",
                    extra={"class_name": self.__class__.__name__},
                    exc_info=True,
                )

    def _on_show_window_requested(self):
        """Handle show window request from D-Bus client."""
        logger.debug("Show window requested via D-Bus", extra={"class_name": self.__class__.__name__})
        self.emit("show-window-requested")

    def _on_quit_requested(self):
        """Handle quit request from D-Bus client."""
        logger.debug("Quit requested via D-Bus", extra={"class_name": self.__class__.__name__})
        self.emit("quit-requested")

    def _get_current_status(self) -> str:
        """
        Get current application status.

        Returns:
            str: Current status text
        """
        # This could be enhanced to return actual application status
        # For now, return a simple status
        return "Running" if self.is_active else "Inactive"

    def connect_observer(self, signal_name: str, callback: Callable):
        """
        Connect an observer to a D-Bus service signal.

        Args:
            signal_name: Name of the signal to observe
            callback: Function to call when signal is emitted
        """
        try:
            self.connect(signal_name, callback)
            logger.debug(f"Observer connected to signal: {signal_name}", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(
                f"Error connecting observer to {signal_name}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def disconnect_observer(self, signal_name: str, callback: Callable):
        """
        Disconnect an observer from a D-Bus service signal.

        Args:
            signal_name: Name of the signal to disconnect from
            callback: Function that was previously connected
        """
        try:
            self.disconnect_by_func(callback)
            logger.debug(
                f"Observer disconnected from signal: {signal_name}", extra={"class_name": self.__class__.__name__}
            )
        except Exception as e:
            logger.error(
                f"Error disconnecting observer from {signal_name}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )


# Register GObject type
GObject.type_register(DBusService)
