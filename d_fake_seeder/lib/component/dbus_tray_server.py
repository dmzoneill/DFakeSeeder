"""
D-Bus Tray Server for DFakeSeeder Main Process

Provides IPC interface for GTK3 tray subprocess to communicate with
the main GTK4 application process.
"""

from typing import Callable, Optional

import dbus.service
from lib.component.dbus_manager import DBusServiceManager
from lib.logger import logger


class TrayDBusServer(DBusServiceManager):
    """
    D-Bus server for tray communication in the main application process.

    Exposes methods for tray actions and signals for status updates.
    Maintains complete separation from GTK code for maximum reusability.
    """

    # D-Bus configuration constants
    SERVICE_NAME = "ie.fio.dfakeseeder"
    OBJECT_PATH = "/ie/fio/dfakeseeder/tray"
    INTERFACE_NAME = "ie.fio.dfakeseeder.Tray"

    def __init__(self):
        """Initialize the tray D-Bus server."""
        super().__init__(self.SERVICE_NAME, self.OBJECT_PATH, self.INTERFACE_NAME)

        # Callback handlers (set by main application)
        self._show_window_callback: Optional[Callable] = None
        self._quit_callback: Optional[Callable] = None
        self._status_update_callback: Optional[Callable] = None

        logger.info("Tray D-Bus server initialized", extra={"class_name": self.__class__.__name__})

    def set_callbacks(self, show_window: Callable, quit_app: Callable, status_update: Optional[Callable] = None):
        """
        Set callback functions for tray actions.

        Args:
            show_window: Function to call when showing main window
            quit_app: Function to call when quitting application
            status_update: Optional function to call when status is requested
        """
        self._show_window_callback = show_window
        self._quit_callback = quit_app
        self._status_update_callback = status_update

        logger.debug("Tray server callbacks configured", extra={"class_name": self.__class__.__name__})

    @dbus.service.method(INTERFACE_NAME, out_signature="s")
    def show_window(self):
        """
        D-Bus method: Show the main application window.

        Returns:
            str: Status message
        """
        logger.info("Show window requested via D-Bus", extra={"class_name": self.__class__.__name__})

        try:
            if self._show_window_callback:
                self._show_window_callback()
                return "OK"
            else:
                logger.warning("No show window callback registered", extra={"class_name": self.__class__.__name__})
                return "ERROR: No callback registered"

        except Exception as e:
            logger.error(f"Error showing window: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)
            return f"ERROR: {str(e)}"

    @dbus.service.method(INTERFACE_NAME, out_signature="s")
    def quit_application(self):
        """
        D-Bus method: Quit the main application.

        Returns:
            str: Status message
        """
        logger.info("Quit application requested via D-Bus", extra={"class_name": self.__class__.__name__})

        try:
            if self._quit_callback:
                self._quit_callback()
                return "OK"
            else:
                logger.warning("No quit callback registered", extra={"class_name": self.__class__.__name__})
                return "ERROR: No callback registered"

        except Exception as e:
            logger.error(
                f"Error quitting application: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            return f"ERROR: {str(e)}"

    @dbus.service.method(INTERFACE_NAME, out_signature="s")
    def get_status(self):
        """
        D-Bus method: Get current application status.

        Returns:
            str: Current status text
        """
        logger.debug("Status requested via D-Bus", extra={"class_name": self.__class__.__name__})

        try:
            if self._status_update_callback:
                status = self._status_update_callback()
                return status if status else "Running"
            else:
                return "Running"

        except Exception as e:
            logger.error(f"Error getting status: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)
            return "Error"

    @dbus.service.method(INTERFACE_NAME, in_signature="s", out_signature="s")
    def ping(self, message):
        """
        D-Bus method: Ping test for connection verification.

        Args:
            message: Test message to echo back

        Returns:
            str: Echo of the message
        """
        logger.debug(f"Ping received: {message}", extra={"class_name": self.__class__.__name__})
        return f"Pong: {message}"

    @dbus.service.signal(INTERFACE_NAME, signature="s")
    def status_changed(self, new_status):
        """
        D-Bus signal: Emitted when application status changes.

        Args:
            new_status: New status text
        """
        logger.debug(f"Emitting status_changed signal: {new_status}", extra={"class_name": self.__class__.__name__})

    @dbus.service.signal(INTERFACE_NAME, signature="s")
    def torrent_count_changed(self, count_info):
        """
        D-Bus signal: Emitted when torrent count changes.

        Args:
            count_info: Formatted string with torrent count information
        """
        logger.debug(
            f"Emitting torrent_count_changed signal: {count_info}", extra={"class_name": self.__class__.__name__}
        )

    @dbus.service.signal(INTERFACE_NAME)
    def application_closing(self):
        """D-Bus signal: Emitted when application is closing."""
        logger.debug("Emitting application_closing signal", extra={"class_name": self.__class__.__name__})

    def update_tray_status(self, status_text: str):
        """
        Update tray status and notify connected clients.

        Args:
            status_text: New status text to display
        """
        try:
            self.status_changed(status_text)
            logger.debug(f"Tray status updated: {status_text}", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error updating tray status: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def update_torrent_count(self, active_count: int, total_count: int):
        """
        Update torrent count and notify connected clients.

        Args:
            active_count: Number of active torrents
            total_count: Total number of torrents
        """
        try:
            count_info = f"{active_count}/{total_count} torrents"
            self.torrent_count_changed(count_info)
            logger.debug(f"Torrent count updated: {count_info}", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error updating torrent count: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def notify_application_closing(self):
        """Notify connected clients that application is closing."""
        try:
            self.application_closing()
            logger.info("Notified tray clients of application closing", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error notifying application closing: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def cleanup(self):
        """Clean up server resources and notify clients."""
        try:
            self.notify_application_closing()
            super().cleanup()

        except Exception as e:
            logger.error(
                f"Error during tray server cleanup: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
