"""
Simple D-Bus Client without GLib Main Loop

Provides D-Bus client functionality without GLib integration to avoid
GTK version conflicts in the main GTK4 process.
"""

from typing import Any, Optional

import dbus
from lib.logger import logger


class SimpleDBusClient:
    """
    Simple D-Bus client without GLib main loop integration.

    Designed for use in the main GTK4 process to avoid GTK version conflicts.
    """

    def __init__(self, service_name: str, object_path: str, interface_name: str):
        """
        Initialize simple D-Bus client.

        Args:
            service_name: Target D-Bus service name
            object_path: Target D-Bus object path
            interface_name: Target D-Bus interface name
        """
        self.service_name = service_name
        self.object_path = object_path
        self.interface_name = interface_name
        self.remote_object = None

        self.connect()

    def connect(self) -> bool:
        """
        Connect to the D-Bus service.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Connect to session bus without GLib main loop
            self.bus = dbus.SessionBus()

            # Get remote object
            self.remote_object = self.bus.get_object(self.service_name, self.object_path)

            logger.info(
                f"Connected to D-Bus service: {self.service_name} at {self.object_path}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to connect to D-Bus service: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            return False

    def call_method(self, method_name: str, *args) -> Optional[Any]:
        """
        Call a method on the remote D-Bus object.

        Args:
            method_name: Name of the method to call
            *args: Arguments to pass to the method

        Returns:
            Method return value or None if call failed
        """
        try:
            if not self.remote_object:
                if not self.connect():
                    return None

            method = getattr(self.remote_object, method_name)
            result = method(*args, dbus_interface=self.interface_name)

            logger.debug(
                f"Called D-Bus method: {method_name} with args: {args}", extra={"class_name": self.__class__.__name__}
            )
            return result

        except Exception as e:
            logger.error(
                f"Failed to call D-Bus method {method_name}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return None

    def is_service_available(self) -> bool:
        """
        Check if the D-Bus service is available.

        Returns:
            bool: True if service is available, False otherwise
        """
        try:
            if not self.remote_object:
                return False

            # Try a simple ping to test availability
            self.call_method("ping")
            return True
        except Exception:
            return False

    def disconnect(self):
        """Disconnect from the D-Bus service."""
        try:
            self.remote_object = None
            logger.info("Disconnected from D-Bus service", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(
                f"Error during D-Bus disconnect: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
