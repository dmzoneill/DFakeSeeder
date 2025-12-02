"""
D-Bus Client for DFakeSeeder

Handles communication with the main DFakeSeeder application via D-Bus.
"""

# isort: skip_file

# fmt: off
import json
from typing import Any, Dict, Optional

import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class DBusClient:
    """D-Bus client for communication with main DFakeSeeder application"""

    SERVICE_NAME = "ie.fio.dfakeseeder"
    OBJECT_PATH = "/ie/fio/dfakeseeder"
    INTERFACE_NAME = "ie.fio.dfakeseeder.Settings"

    def __init__(self):
        self.connection = None
        self.proxy = None
        self.connected = False
        self._connect()

    def _connect(self) -> bool:
        """Connect to D-Bus service and verify main app is actually running"""
        try:
            self.connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            if not self.connection:
                return False

            # First check if the service is actually available on the bus
            try:
                name_owner = self.connection.call_sync(
                    "org.freedesktop.DBus",
                    "/org/freedesktop/DBus",
                    "org.freedesktop.DBus",
                    "GetNameOwner",
                    GLib.Variant("(s)", (self.SERVICE_NAME,)),
                    None,
                    Gio.DBusCallFlags.NONE,
                    1000,  # 1 second timeout
                    None,
                )
            except Exception as e:
                # Service not found - this is normal when main app isn't running
                logger.debug(
                    f"Service not available on D-Bus: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                self.connected = False
                return False

            if not name_owner:
                logger.debug(
                    "Main application service not available on D-Bus",
                    extra={"class_name": self.__class__.__name__},
                )
                self.connected = False
                return False

            self.proxy = Gio.DBusProxy.new_sync(
                self.connection,
                Gio.DBusProxyFlags.NONE,
                None,
                self.SERVICE_NAME,
                self.OBJECT_PATH,
                self.INTERFACE_NAME,
                None,
            )

            # Test the connection by calling GetSettings directly
            # (don't use self.get_settings which checks self.connected)
            logger.debug(
                "Testing D-Bus connection with GetSettings call",
                extra={"class_name": self.__class__.__name__},
            )
            try:
                test_result = self.proxy.call_sync(
                    "GetSettings", None, Gio.DBusCallFlags.NONE, 5000, None
                )  # 5 second timeout
                if test_result:
                    self.connected = True
                    logger.info(
                        "Connected to D-Bus service",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return True
                else:
                    self.connected = False
                    logger.warning(
                        "Service found but GetSettings returned None",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return False
            except Exception as e:
                self.connected = False
                logger.warning(
                    f"Service found but not responding: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

        except Exception as e:
            logger.info(
                f"Main application not running (D-Bus connection failed): {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self.connected = False
            return False

    def get_settings(self) -> Optional[str]:
        """Get settings from main application"""
        try:
            if not self.connected:
                logger.debug(
                    "get_settings called but not connected",
                    extra={"class_name": self.__class__.__name__},
                )
                return None

            logger.debug(
                "Calling GetSettings via D-Bus proxy",
                extra={"class_name": self.__class__.__name__},
            )
            result = self.proxy.call_sync("GetSettings", None, Gio.DBusCallFlags.NONE, 5000, None)  # 5 second timeout
            logger.debug(
                f"GetSettings result type: {type(result)}",
                extra={"class_name": self.__class__.__name__},
            )

            if result:
                unpacked = result.unpack()[0]
                logger.debug(
                    f"GetSettings returned {len(unpacked)} bytes",
                    extra={"class_name": self.__class__.__name__},
                )
                return unpacked
            else:
                logger.warning(
                    "GetSettings returned None result",
                    extra={"class_name": self.__class__.__name__},
                )
                return None

        except Exception as e:
            logger.error(
                f"Failed to get settings: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return None

    def update_settings(self, changes: Dict[str, Any]) -> bool:
        """Update settings in main application"""
        try:
            if not self.connected:
                return False

            changes_json = json.dumps(changes)
            result = self.proxy.call_sync(
                "UpdateSettings",
                GLib.Variant("(s)", (changes_json,)),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
            return result.unpack()[0] if result else False

        except Exception as e:
            logger.error(
                f"Failed to update settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def subscribe(self, signal_name: str, callback):
        """Subscribe to D-Bus signal"""
        try:
            if not self.connected:
                return False

            self.connection.signal_subscribe(
                self.SERVICE_NAME,
                self.INTERFACE_NAME,
                signal_name,
                self.OBJECT_PATH,
                None,
                Gio.DBusSignalFlags.NONE,
                callback,
                None,
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to subscribe to signal {signal_name}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def ping(self) -> bool:
        """Ping main application to check if it's alive"""
        try:
            if not self.connected:
                return False

            result = self.proxy.call_sync("Ping", None, Gio.DBusCallFlags.NONE, 1000, None)  # 1 second timeout
            return result.unpack()[0] if result else False

        except Exception as e:
            logger.debug(f"Ping failed: {e}", extra={"class_name": self.__class__.__name__})
            return False

    def reconnect(self) -> bool:
        """Attempt to reconnect to D-Bus service"""
        logger.debug(
            "Attempting to reconnect to D-Bus",
            extra={"class_name": self.__class__.__name__},
        )
        # Clean up old connection state
        self.connected = False
        self.proxy = None
        # Try to connect again
        return self._connect()

    def cleanup(self):
        """Clean up D-Bus connection"""
        self.connected = False
        self.proxy = None
        self.connection = None
