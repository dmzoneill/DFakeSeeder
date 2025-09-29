"""
Simple D-Bus Tray Server for DFakeSeeder Main Process

Provides IPC interface for GTK3 tray subprocess to communicate with
the main GTK4 application process WITHOUT GLib main loop integration.
"""

from typing import Callable, Optional

import dbus
import dbus.service
from lib.logger import logger


class TrayDBusServer(dbus.service.Object):
    """
    Simple D-Bus server for tray communication without GLib main loop.

    Designed for use in the main GTK4 process to avoid GTK version conflicts.
    """

    # D-Bus configuration
    SERVICE_NAME = "ie.fio.dfakeseeder"
    OBJECT_PATH = "/ie/fio/dfakeseeder/tray"
    INTERFACE_NAME = "ie.fio.dfakeseeder.Tray"

    def __init__(self):
        """Initialize D-Bus tray server."""
        self.show_window_callback: Optional[Callable] = None
        self.quit_callback: Optional[Callable] = None
        self.get_status_callback: Optional[Callable] = None

        try:
            # Create service on session bus (without GLib main loop)
            self.bus = dbus.SessionBus()
            self.bus_name = dbus.service.BusName(self.SERVICE_NAME, self.bus)

            # Initialize the service object
            super().__init__(self.bus_name, self.OBJECT_PATH)

            logger.info(
                f"D-Bus tray server started: {self.SERVICE_NAME} at {self.OBJECT_PATH}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize D-Bus tray server: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            raise

    def set_callbacks(self, show_window_callback: Callable, quit_callback: Callable, get_status_callback: Callable):
        """
        Set callback functions for handling requests.

        Args:
            show_window_callback: Function to call when showing window
            quit_callback: Function to call when quitting
            get_status_callback: Function to call for status requests
        """
        self.show_window_callback = show_window_callback
        self.quit_callback = quit_callback
        self.get_status_callback = get_status_callback

        logger.debug("D-Bus tray server callbacks configured", extra={"class_name": self.__class__.__name__})

    @dbus.service.method(INTERFACE_NAME, in_signature="", out_signature="")
    def show_window(self):
        """D-Bus method to show the main window."""
        logger.debug("D-Bus show_window method called", extra={"class_name": self.__class__.__name__})
        try:
            if self.show_window_callback:
                self.show_window_callback()
        except Exception as e:
            logger.error(
                f"Error in show_window callback: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    @dbus.service.method(INTERFACE_NAME, in_signature="", out_signature="")
    def quit_application(self):
        """D-Bus method to quit the application."""
        logger.debug("D-Bus quit_application method called", extra={"class_name": self.__class__.__name__})
        try:
            if self.quit_callback:
                self.quit_callback()
        except Exception as e:
            logger.error(
                f"Error in quit_application callback: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    @dbus.service.method(INTERFACE_NAME, in_signature="", out_signature="s")
    def get_status(self):
        """D-Bus method to get current status."""
        logger.debug("D-Bus get_status method called", extra={"class_name": self.__class__.__name__})
        try:
            if self.get_status_callback:
                return self.get_status_callback()
            return "Unknown"
        except Exception as e:
            logger.error(
                f"Error in get_status callback: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            return "Error"

    @dbus.service.method(INTERFACE_NAME, in_signature="", out_signature="")
    def ping(self):
        """D-Bus method for testing connectivity."""
        logger.debug("D-Bus ping method called", extra={"class_name": self.__class__.__name__})
        # Just return, no response needed

    @dbus.service.signal(INTERFACE_NAME, signature="s")
    def status_changed(self, status):
        """D-Bus signal emitted when status changes."""
        logger.debug(f"D-Bus status_changed signal emitted: {status}", extra={"class_name": self.__class__.__name__})

    @dbus.service.signal(INTERFACE_NAME, signature="ii")
    def torrent_count_changed(self, active_count, total_count):
        """D-Bus signal emitted when torrent count changes."""
        logger.debug(
            f"D-Bus torrent_count_changed signal emitted: {active_count}/{total_count}",
            extra={"class_name": self.__class__.__name__},
        )

    @dbus.service.signal(INTERFACE_NAME, signature="")
    def application_closing(self):
        """D-Bus signal emitted when application is closing."""
        logger.debug("D-Bus application_closing signal emitted", extra={"class_name": self.__class__.__name__})

    def update_tray_status(self, status_text: str):
        """Update tray status and emit signal."""
        try:
            self.status_changed(status_text)
            logger.debug(f"Tray status updated via D-Bus: {status_text}", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(
                f"Error updating tray status: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def update_torrent_count(self, active_count: int, total_count: int):
        """Update torrent count and emit signal."""
        try:
            self.torrent_count_changed(active_count, total_count)
            logger.debug(
                f"Torrent count updated via D-Bus: {active_count}/{total_count}",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Error updating torrent count: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def notify_application_closing(self):
        """Notify clients that application is closing."""
        try:
            self.application_closing()
            logger.debug(
                "Application closing notification sent via D-Bus", extra={"class_name": self.__class__.__name__}
            )
        except Exception as e:
            logger.error(
                f"Error notifying application closing: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def cleanup(self):
        """Clean up D-Bus service resources."""
        try:
            if hasattr(self, "bus_name"):
                del self.bus_name
            logger.info("D-Bus tray server cleaned up", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(
                f"Error during D-Bus tray server cleanup: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
