"""
Reusable D-Bus Manager for IPC Communication

Provides a clean abstraction for D-Bus services and clients with automatic
error handling, reconnection, and signal management.
"""

from typing import Any, Callable, Dict, Optional

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from lib.logger import logger

# Global flag to prevent multiple D-Bus main loop initialization
_dbus_mainloop_initialized = False


def _ensure_dbus_mainloop():
    """Ensure D-Bus main loop is initialized only once."""
    global _dbus_mainloop_initialized
    if not _dbus_mainloop_initialized:
        try:
            DBusGMainLoop(set_as_default=True)
            _dbus_mainloop_initialized = True
            logger.debug("D-Bus main loop initialized", extra={"class_name": "DBusManager"})
        except Exception as e:
            logger.warning(f"D-Bus main loop initialization failed: {e}", extra={"class_name": "DBusManager"})


class DBusServiceManager(dbus.service.Object):
    """
    Reusable D-Bus service manager for creating IPC servers.

    Handles service registration, method exposure, and signal emission
    with automatic error handling and logging.
    """

    def __init__(self, service_name: str, object_path: str, interface_name: str):
        """
        Initialize D-Bus service.

        Args:
            service_name: D-Bus service name (e.g., 'ie.fio.dfakeseeder')
            object_path: D-Bus object path (e.g., '/ie/fio/dfakeseeder/tray')
            interface_name: D-Bus interface name (e.g., 'ie.fio.dfakeseeder.Tray')
        """
        self.service_name = service_name
        self.object_path = object_path
        self.interface_name = interface_name
        self._method_handlers: Dict[str, Callable] = {}

        try:
            # Initialize D-Bus main loop if not already done
            _ensure_dbus_mainloop()

            # Create service on session bus
            self.bus = dbus.SessionBus()
            self.bus_name = dbus.service.BusName(service_name, self.bus)

            # Initialize the service object
            super().__init__(self.bus_name, object_path)

            logger.info(
                f"D-Bus service started: {service_name} at {object_path}", extra={"class_name": self.__class__.__name__}
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize D-Bus service: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            raise

    def register_method_handler(self, method_name: str, handler: Callable):
        """Register a handler function for a D-Bus method call."""
        self._method_handlers[method_name] = handler
        logger.debug(f"Registered method handler: {method_name}", extra={"class_name": self.__class__.__name__})

    def emit_signal(self, signal_name: str, *args):
        """Emit a D-Bus signal with the given arguments."""
        try:
            # This will be overridden by specific signal methods
            logger.debug(
                f"Signal emitted: {signal_name} with args: {args}", extra={"class_name": self.__class__.__name__}
            )
        except Exception as e:
            logger.error(
                f"Failed to emit signal {signal_name}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def cleanup(self):
        """Clean up D-Bus service resources."""
        try:
            if hasattr(self, "bus_name"):
                del self.bus_name
            logger.info("D-Bus service cleaned up", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(
                f"Error during D-Bus cleanup: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )


class DBusClientManager:
    """
    Reusable D-Bus client manager for connecting to IPC services.

    Handles connection management, method calls, and signal reception
    with automatic reconnection and error handling.
    """

    def __init__(self, service_name: str, object_path: str, interface_name: str):
        """
        Initialize D-Bus client.

        Args:
            service_name: Target D-Bus service name
            object_path: Target D-Bus object path
            interface_name: Target D-Bus interface name
        """
        self.service_name = service_name
        self.object_path = object_path
        self.interface_name = interface_name
        self.remote_object = None
        self._signal_handlers: Dict[str, Callable] = {}

        self.connect()

    def connect(self) -> bool:
        """
        Connect to the D-Bus service.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Initialize D-Bus main loop if not already done
            _ensure_dbus_mainloop()

            # Connect to session bus
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

    def register_signal_handler(self, signal_name: str, handler: Callable):
        """
        Register a handler for a D-Bus signal.

        Args:
            signal_name: Name of the signal to listen for
            handler: Function to call when signal is received
        """
        try:
            self._signal_handlers[signal_name] = handler

            self.bus.add_signal_receiver(
                handler,
                signal_name=signal_name,
                dbus_interface=self.interface_name,
                bus_name=self.service_name,
                path=self.object_path,
            )

            logger.debug(f"Registered signal handler: {signal_name}", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Failed to register signal handler {signal_name}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def disconnect(self):
        """Disconnect from the D-Bus service."""
        try:
            # Remove signal handlers
            for signal_name, handler in self._signal_handlers.items():
                try:
                    self.bus.remove_signal_receiver(
                        handler,
                        signal_name=signal_name,
                        dbus_interface=self.interface_name,
                        bus_name=self.service_name,
                        path=self.object_path,
                    )
                except Exception:
                    pass  # Handler may already be removed

            self._signal_handlers.clear()
            self.remote_object = None

            logger.info("Disconnected from D-Bus service", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error during D-Bus disconnect: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
