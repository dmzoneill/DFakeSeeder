#!/usr/bin/env python3
"""
D-Bus Unifier - Inter-process communication bridge for DFakeSeeder

Provides D-Bus service for communication between main application and tray application.
Integrates directly with AppSettings for settings management and signal forwarding.
"""
# isort: skip_file

# fmt: off
import json
import time
from typing import Any

import gi

gi.require_version("Gio", "2.0")

from gi.repository import Gio, GLib  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class DBusUnifier:
    """
    Enhanced D-Bus communication manager for DFakeSeeder

    Provides settings-driven communication between main app and tray application.
    Integrates directly with AppSettings singleton for automatic signal forwarding.
    """

    # D-Bus service configuration
    SERVICE_NAME = "ie.fio.dfakeseeder"
    OBJECT_PATH = "/ie/fio/dfakeseeder"
    INTERFACE_NAME = "ie.fio.dfakeseeder.Settings"

    # D-Bus interface XML definition
    INTERFACE_XML = """
    <node>
        <interface name="ie.fio.dfakeseeder.Settings">
            <!-- Core settings methods -->
            <method name="GetSettings">
                <arg type="s" name="settings_json" direction="out"/>
            </method>
            <method name="UpdateSettings">
                <arg type="s" name="changes_json" direction="in"/>
                <arg type="b" name="success" direction="out"/>
            </method>

            <!-- UI control methods -->
            <method name="ShowPreferences">
                <arg type="b" name="success" direction="out"/>
            </method>
            <method name="ShowAbout">
                <arg type="b" name="success" direction="out"/>
            </method>

            <!-- Health monitoring methods -->
            <method name="Ping">
                <arg type="b" name="alive" direction="out"/>
            </method>
            <method name="GetConnectionStatus">
                <arg type="s" name="status_json" direction="out"/>
            </method>
            <method name="GetDebugInfo">
                <arg type="s" name="debug_json" direction="out"/>
            </method>

            <!-- Signals -->
            <signal name="SettingsChanged">
                <arg type="s" name="changes_json"/>
            </signal>
        </interface>
    </node>
    """

    def __init__(self):
        """Initialize D-Bus unifier with AppSettings integration"""
        logger.debug("Initializing DBusUnifier", extra={"class_name": self.__class__.__name__})

        # Get AppSettings singleton instance
        self.app_settings = AppSettings.get_instance()

        # D-Bus connection state
        self._connection = None
        self._registration_id = None
        self._is_service_owner = False

        # Health monitoring
        self._message_count = 0
        self._error_count = 0
        self._last_ping = None

        # Initialize D-Bus connection
        self._initialize_dbus()

        # Setup connection health monitoring
        self._setup_connection_health_monitoring()

    def _initialize_dbus(self) -> bool:
        """Initialize D-Bus connection and register service"""
        try:
            logger.debug(
                "Connecting to D-Bus session bus",
                extra={"class_name": self.__class__.__name__},
            )

            # Get session bus connection
            self._connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            if not self._connection:
                logger.error(
                    "Failed to connect to D-Bus session bus",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Parse interface XML
            introspection_data = Gio.DBusNodeInfo.new_for_xml(self.INTERFACE_XML)
            interface_info = introspection_data.lookup_interface(self.INTERFACE_NAME)

            # Register object with method handlers
            self._registration_id = self._connection.register_object(
                self.OBJECT_PATH,
                interface_info,
                self._handle_method_call,
                None,  # property get handler
                None,  # property set handler
            )

            if self._registration_id == 0:
                logger.error(
                    "Failed to register D-Bus object",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Own the service name
            name_owner_id = Gio.bus_own_name(
                Gio.BusType.SESSION,
                self.SERVICE_NAME,
                Gio.BusNameOwnerFlags.NONE,
                self._on_bus_acquired,
                self._on_name_acquired,
                self._on_name_lost,
            )

            if name_owner_id == 0:
                logger.error(
                    "Failed to own D-Bus service name",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            logger.debug(
                "D-Bus service registered successfully",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to initialize D-Bus: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _handle_method_call(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        method_name,
        parameters,
        invocation,
    ):
        """Handle incoming D-Bus method calls"""
        try:
            self._message_count += 1
            logger.debug(
                f"D-Bus method call received: {method_name}",
                extra={"class_name": self.__class__.__name__},
            )

            if method_name == "GetSettings":
                result = self._handle_get_settings()
                invocation.return_value(GLib.Variant("(s)", (result,)))

            elif method_name == "UpdateSettings":
                changes_json = parameters.unpack()[0]
                # Return success immediately to avoid blocking the D-Bus caller
                invocation.return_value(GLib.Variant("(b)", (True,)))
                # Process settings update asynchronously to allow D-Bus response to complete first
                # IMPORTANT: Must explicitly return False, not use 'or False' since function returns True
                GLib.idle_add(lambda: (self._handle_update_settings(changes_json), False)[1])

            elif method_name == "Ping":
                result = self._handle_ping()
                invocation.return_value(GLib.Variant("(b)", (result,)))

            elif method_name == "GetConnectionStatus":
                result = self._handle_get_connection_status()
                invocation.return_value(GLib.Variant("(s)", (result,)))

            elif method_name == "GetDebugInfo":
                result = self._handle_get_debug_info()
                invocation.return_value(GLib.Variant("(s)", (result,)))

            elif method_name == "ShowPreferences":
                result = self._handle_show_preferences()
                invocation.return_value(GLib.Variant("(b)", (result,)))

            elif method_name == "ShowAbout":
                result = self._handle_show_about()
                invocation.return_value(GLib.Variant("(b)", (result,)))

            else:
                invocation.return_error_literal(
                    Gio.dbus_error_quark(),
                    Gio.DBusError.UNKNOWN_METHOD,
                    f"Unknown method: {method_name}",
                )

        except Exception as e:
            self._error_count += 1
            logger.error(
                f"Error handling D-Bus method {method_name}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            invocation.return_error_literal(
                Gio.dbus_error_quark(),
                Gio.DBusError.FAILED,
                f"Internal error: {str(e)}",
            )

    def _handle_get_settings(self) -> str:
        """Get complete AppSettings serialization from merged user+default settings"""
        try:
            # Access merged user+default settings via _settings attribute
            settings_dict = self.app_settings._settings
            # Handle None case explicitly
            if settings_dict is None:
                return "{}"
            return json.dumps(settings_dict, default=str)
        except Exception as e:
            logger.error(
                f"Failed to get settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return "{}"

    def _handle_update_settings(self, changes_json: str) -> bool:
        """Update AppSettings directly with validation (triggers automatic signals)"""
        try:
            logger.debug(
                "_handle_update_settings starting",
                extra={"class_name": self.__class__.__name__},
            )
            changes = json.loads(changes_json)

            validation_errors = []
            applied_changes = {}

            # Validate all changes before applying any
            for path, value in changes.items():
                if not self._validate_setting_value(path, value):
                    validation_errors.append(f"Invalid value for {path}: {value}")
                else:
                    applied_changes[path] = value

            # Only apply if all validations pass
            if validation_errors:
                logger.warning(
                    f"Settings validation failed: {validation_errors}",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Apply validated changes to AppSettings
            logger.debug(
                f"Applying {len(applied_changes)} changes",
                extra={"class_name": self.__class__.__name__},
            )
            for path, value in applied_changes.items():
                # Special handling for application_quit_requested to ensure signal is always emitted
                if path == "application_quit_requested" and value:
                    logger.debug(
                        "Forcing application quit signal emission",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # First set to False to ensure the value changes
                    logger.debug(
                        "Setting application_quit_requested=False",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.app_settings.set("application_quit_requested", False)
                    logger.debug(
                        "Setting application_quit_requested=True",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Then set to True to trigger the signal
                    self.app_settings.set("application_quit_requested", True)
                    logger.debug(
                        "Quit signal emitted",
                        extra={"class_name": self.__class__.__name__},
                    )
                elif "." in path:
                    # Handle nested settings using internal helper method
                    self.app_settings._set_nested_value(self.app_settings._settings, path, value)
                    self.app_settings.save_settings()  # Save and emit signals
                else:
                    # Handle top-level settings using public method
                    self.app_settings.set(path, value)

            # NOTE: D-Bus signals are automatically sent by _on_app_setting_changed()
            # which is connected to AppSettings signals. No need to emit manually here
            # to avoid duplicate signal emissions.

            logger.debug(
                f"✅ Updated {len(applied_changes)} settings via D-Bus - COMPLETE",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to update settings: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def _handle_ping(self) -> bool:
        """Ping method for connection health checks"""
        self._last_ping = time.time()
        return True

    def _handle_get_connection_status(self) -> str:
        """Get detailed connection status"""
        try:
            status = {
                "connected": self._connection is not None,
                "is_service_owner": self._is_service_owner,
                "last_ping": self._last_ping or 0,
                "message_count": self._message_count,
                "error_count": self._error_count,
                "uptime": (time.time() - (self._last_ping or time.time()) if self._last_ping else 0),
            }
            return json.dumps(status)
        except Exception as e:
            logger.error(
                f"Failed to get connection status: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return "{}"

    def _handle_get_debug_info(self) -> str:
        """Get comprehensive debug information"""
        try:
            debug_info = {
                "service_name": self.SERVICE_NAME,
                "object_path": self.OBJECT_PATH,
                "interface_name": self.INTERFACE_NAME,
                "connection_status": json.loads(self._handle_get_connection_status()),
                "registration_id": self._registration_id,
                "app_settings_available": self.app_settings is not None,
                "settings_count": (len(self.app_settings._settings) if self.app_settings else 0),
            }
            return json.dumps(debug_info, indent=2)
        except Exception as e:
            logger.error(
                f"Failed to get debug info: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return "{}"

    def _handle_show_preferences(self) -> bool:
        """
        Show preferences dialog by setting show_preferences flag.

        This triggers the View's settings change handler which opens the dialog.
        Also ensures main window is visible.
        """
        try:
            logger.debug(
                "ShowPreferences D-Bus method called",
                extra={"class_name": self.__class__.__name__},
            )

            # Set window visible first
            logger.debug(
                "Setting window_visible=True",
                extra={"class_name": self.__class__.__name__},
            )
            self.app_settings.set("window_visible", True)

            # Force preferences dialog trigger by setting to False first, then True
            # This ensures the value changes and signals are emitted even if it was already True
            self.app_settings.set("show_preferences", False)
            logger.debug(
                "Setting show_preferences=True",
                extra={"class_name": self.__class__.__name__},
            )
            self.app_settings.set("show_preferences", True)

            # Verify the value was set
            current_value = self.app_settings.get("show_preferences")
            logger.debug(
                f"Preferences dialog triggered via D-Bus (current value: {current_value})",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to show preferences: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def _handle_show_about(self) -> bool:
        """
        Show about dialog by setting show_about flag.

        This triggers the View's settings change handler which opens the dialog.
        Also ensures main window is visible.
        """
        try:
            logger.debug(
                "ShowAbout D-Bus method called",
                extra={"class_name": self.__class__.__name__},
            )

            # Set window visible first
            logger.debug(
                "Setting window_visible=True",
                extra={"class_name": self.__class__.__name__},
            )
            self.app_settings.set("window_visible", True)

            # Force about dialog trigger by setting to False first, then True
            # This ensures the value changes and signals are emitted even if it was already True
            self.app_settings.set("show_about", False)
            logger.debug("Setting show_about=True", extra={"class_name": self.__class__.__name__})
            self.app_settings.set("show_about", True)

            # Verify the value was set
            current_value = self.app_settings.get("show_about")
            logger.debug(
                f"About dialog triggered via D-Bus (current value: {current_value})",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to show about dialog: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def _validate_setting_value(self, path: str, value: Any) -> bool:
        """Validate setting value before applying"""
        try:
            # Speed validation
            if path in [
                "upload_speed",
                "download_speed",
                "alternative_upload_speed",
                "alternative_download_speed",
            ]:
                return isinstance(value, (int, float)) and 0 <= value <= 10000

            # Boolean validation
            if path in [
                "alternative_speed_enabled",
                "seeding_paused",
                "window_visible",
                "close_to_tray",
                "minimize_to_tray",
                "application_quit_requested",
            ]:
                return isinstance(value, bool)

            # Profile validation
            if path == "current_seeding_profile":
                return isinstance(value, str) and value in [
                    "conservative",
                    "balanced",
                    "aggressive",
                ]

            # Language validation
            if path == "language":
                return isinstance(value, str) and len(value) >= 2

            # Default: allow if we don't have specific validation
            return True

        except Exception as e:
            logger.error(
                f"Validation error for {path}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _emit_settings_changed_signal(self, changes: dict):
        """Emit D-Bus signal for settings changes (including language changes)"""
        try:
            if not self._connection:
                return

            changes_json = json.dumps(changes)
            # Emit D-Bus signal that tray applications are listening for
            self._connection.emit_signal(
                None,  # destination (broadcast)
                self.OBJECT_PATH,
                self.INTERFACE_NAME,
                "SettingsChanged",
                GLib.Variant("(s)", (changes_json,)),
            )
            logger.debug(
                f"Emitted D-Bus SettingsChanged signal: {changes}",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Failed to emit D-Bus settings changed signal: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def setup_settings_signal_forwarding(self):
        """Setup forwarding of AppSettings signals to D-Bus signals"""
        try:
            # Connect to AppSettings signals to forward them over D-Bus
            # Use the new preferred signal name from AppSettings
            self.app_settings.connect("settings-value-changed", self._on_app_setting_changed)
            logger.debug(
                "DBusUnifier connected to AppSettings signals",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Failed to setup settings signal forwarding: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_app_setting_changed(self, app_settings, key, value):
        """Forward AppSettings changes to D-Bus signals"""
        try:
            # Create changes dictionary
            changes = {key: value}

            # Special handling for language changes
            if key == "language":
                logger.debug(
                    f"Language change detected in DBusUnifier: {value}",
                    extra={"class_name": self.__class__.__name__},
                )

            # Emit D-Bus signal
            self._emit_settings_changed_signal(changes)

        except Exception as e:
            logger.error(
                f"Error forwarding settings change to D-Bus: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _setup_connection_health_monitoring(self):
        """Setup connection health monitoring and debugging tools"""
        try:
            # Health monitoring is built into the existing methods
            logger.debug(
                "D-Bus connection health monitoring enabled",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Failed to setup connection health monitoring: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_bus_acquired(self, connection, name):
        """Callback when D-Bus connection is acquired"""
        logger.debug(f"D-Bus bus acquired: {name}", extra={"class_name": self.__class__.__name__})

    def _on_name_acquired(self, connection, name):
        """Callback when service name is acquired"""
        self._is_service_owner = True
        logger.debug(
            f"D-Bus service name acquired: {name}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_name_lost(self, connection, name):
        """Callback when service name is lost"""
        self._is_service_owner = False
        logger.warning(
            f"D-Bus service name lost: {name}",
            extra={"class_name": self.__class__.__name__},
        )

    def cleanup(self):
        """Clean up D-Bus connection and resources"""
        try:
            if self._registration_id and self._connection:
                self._connection.unregister_object(self._registration_id)
                self._registration_id = None

            self._connection = None
            self._is_service_owner = False

            logger.debug("DBusUnifier cleaned up", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(
                f"Error during DBusUnifier cleanup: {e}",
                extra={"class_name": self.__class__.__name__},
            )
