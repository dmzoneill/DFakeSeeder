"""
Connection settings tab for the settings dialog.

Handles network connection settings like listening port, connection limits,
proxy configuration, and UPnP settings.
"""

# isort: skip_file

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from d_fake_seeder.lib.util.constants import NetworkConstants  # noqa: E402

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import TranslationMixin  # noqa: E402
from .settings_mixins import UtilityMixin, ValidationMixin  # noqa: E402

# fmt: on


class ConnectionTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """
    Connection settings tab component.

    Manages:
    - Listening port configuration
    - Connection limits (global, per-torrent, upload slots)
    - UPnP/NAT-PMP port mapping
    - Proxy settings (type, server, port, authentication)
    """

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Connection"

    def _init_widgets(self) -> None:
        """Initialize Connection tab widgets."""
        # Cache commonly used widgets
        self._widgets.update(
            {
                # Port settings
                "listening_port": self.builder.get_object("settings_listening_port"),
                "random_port_button": self.builder.get_object("settings_random_port_button"),
                "upnp_enabled": self.builder.get_object("settings_upnp_enabled"),
                # Connection limits
                "max_global_connections": self.builder.get_object("settings_max_global_connections"),
                "max_per_torrent": self.builder.get_object("settings_max_per_torrent"),
                "max_upload_slots": self.builder.get_object("settings_max_upload_slots"),
                # Proxy settings
                "proxy_type": self.builder.get_object("settings_proxy_type"),
                "proxy_server": self.builder.get_object("settings_proxy_server"),
                "proxy_port": self.builder.get_object("settings_proxy_port"),
                "proxy_auth_enabled": self.builder.get_object("settings_proxy_auth_enabled"),
                "proxy_username": self.builder.get_object("settings_proxy_username"),
                "proxy_password": self.builder.get_object("settings_proxy_password"),
            }
        )

    def _connect_signals(self) -> None:
        """Connect signal handlers for Connection tab."""
        # Listening port
        listening_port = self.get_widget("listening_port")
        if listening_port:
            self.track_signal(
                listening_port,
                listening_port.connect("value-changed", self.on_listening_port_changed),
            )

        # Random port button
        random_port_button = self.get_widget("random_port_button")
        if random_port_button:
            self.track_signal(
                random_port_button,
                random_port_button.connect("clicked", self.on_random_port_clicked),
            )

        # UPnP toggle
        upnp_enabled = self.get_widget("upnp_enabled")
        if upnp_enabled:
            self.track_signal(upnp_enabled, upnp_enabled.connect("state-set", self.on_upnp_changed))

        # Connection limits
        max_global = self.get_widget("max_global_connections")
        if max_global:
            self.track_signal(
                max_global,
                max_global.connect("value-changed", self.on_connection_limit_changed),
            )

        max_per_torrent = self.get_widget("max_per_torrent")
        if max_per_torrent:
            self.track_signal(
                max_per_torrent,
                max_per_torrent.connect("value-changed", self.on_connection_limit_changed),
            )

        max_upload_slots = self.get_widget("max_upload_slots")
        if max_upload_slots:
            self.track_signal(
                max_upload_slots,
                max_upload_slots.connect("value-changed", self.on_connection_limit_changed),
            )

        # Proxy settings
        proxy_type = self.get_widget("proxy_type")
        if proxy_type:
            self.track_signal(
                proxy_type,
                proxy_type.connect("notify::selected", self.on_proxy_type_changed),
            )

        proxy_auth = self.get_widget("proxy_auth_enabled")
        if proxy_auth:
            self.track_signal(proxy_auth, proxy_auth.connect("state-set", self.on_proxy_auth_changed))

        # Proxy server/port (for validation)
        proxy_server = self.get_widget("proxy_server")
        if proxy_server:
            self.track_signal(
                proxy_server,
                proxy_server.connect("changed", self.on_proxy_server_changed),
            )

        proxy_port = self.get_widget("proxy_port")
        if proxy_port:
            self.track_signal(
                proxy_port,
                proxy_port.connect("value-changed", self.on_proxy_port_changed),
            )

    def _load_settings(self) -> None:
        """Load current settings into Connection tab widgets."""
        try:
            # Get connection settings
            connection_settings = getattr(self.app_settings, "connection", {})

            # Listening port
            listening_port = self.get_widget("listening_port")
            if listening_port:
                port = connection_settings.get("listening_port", NetworkConstants.DEFAULT_PORT)
                listening_port.set_value(port)

            # UPnP setting
            upnp_enabled = self.get_widget("upnp_enabled")
            if upnp_enabled:
                upnp_enabled.set_active(connection_settings.get("upnp_enabled", True))

            # Connection limits
            max_global = self.get_widget("max_global_connections")
            if max_global:
                max_global.set_value(connection_settings.get("max_global_connections", 200))

            max_per_torrent = self.get_widget("max_per_torrent")
            if max_per_torrent:
                max_per_torrent.set_value(connection_settings.get("max_per_torrent", 50))

            max_upload_slots = self.get_widget("max_upload_slots")
            if max_upload_slots:
                max_upload_slots.set_value(connection_settings.get("max_upload_slots", 4))

            # Proxy settings
            proxy_settings = getattr(self.app_settings, "proxy", {})
            self._load_proxy_settings(proxy_settings)

            self.logger.debug("Connection tab settings loaded")

        except Exception as e:
            self.logger.error(f"Error loading Connection tab settings: {e}")

    def _load_proxy_settings(self, proxy_settings: Dict[str, Any]) -> None:
        """Load proxy settings into widgets."""
        try:
            # Proxy type
            proxy_type = self.get_widget("proxy_type")
            if proxy_type:
                proxy_type_value = proxy_settings.get("type", "none")
                # Map proxy type to dropdown index
                type_mapping = {"none": 0, "http": 1, "socks4": 2, "socks5": 3}
                proxy_type.set_selected(type_mapping.get(proxy_type_value, 0))

            # Proxy server and port
            proxy_server = self.get_widget("proxy_server")
            if proxy_server:
                proxy_server.set_text(proxy_settings.get("server", ""))

            proxy_port = self.get_widget("proxy_port")
            if proxy_port:
                proxy_port.set_value(proxy_settings.get("port", 8080))

            # Authentication
            proxy_auth = self.get_widget("proxy_auth_enabled")
            if proxy_auth:
                proxy_auth.set_active(proxy_settings.get("auth_enabled", False))

            proxy_username = self.get_widget("proxy_username")
            if proxy_username:
                proxy_username.set_text(proxy_settings.get("username", ""))

            proxy_password = self.get_widget("proxy_password")
            if proxy_password:
                proxy_password.set_text(proxy_settings.get("password", ""))

        except Exception as e:
            self.logger.error(f"Error loading proxy settings: {e}")

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Connection tab."""
        self._update_proxy_dependencies()

    def _update_tab_dependencies(self) -> None:
        """Update Connection tab dependencies."""
        self._update_proxy_dependencies()

    def _update_proxy_dependencies(self) -> None:
        """Update proxy-related widget dependencies."""
        try:
            proxy_type = self.get_widget("proxy_type")
            if not proxy_type:
                return

            # Check if proxy is enabled (not 'none')
            proxy_enabled = proxy_type.get_selected() > 0

            # Enable/disable proxy-related widgets
            self.update_widget_sensitivity("proxy_server", proxy_enabled)
            self.update_widget_sensitivity("proxy_port", proxy_enabled)
            self.update_widget_sensitivity("proxy_auth_enabled", proxy_enabled)

            # Authentication-specific widgets
            proxy_auth = self.get_widget("proxy_auth_enabled")
            auth_enabled = proxy_enabled and proxy_auth and proxy_auth.get_active()

            self.update_widget_sensitivity("proxy_username", auth_enabled)
            self.update_widget_sensitivity("proxy_password", auth_enabled)

        except Exception as e:
            self.logger.error(f"Error updating proxy dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Connection tab widgets."""
        settings = {}

        try:
            # Connection settings
            connection_settings = {}

            listening_port = self.get_widget("listening_port")
            if listening_port:
                connection_settings["listening_port"] = int(listening_port.get_value())

            upnp_enabled = self.get_widget("upnp_enabled")
            if upnp_enabled:
                connection_settings["upnp_enabled"] = upnp_enabled.get_active()

            max_global = self.get_widget("max_global_connections")
            if max_global:
                connection_settings["max_global_connections"] = int(max_global.get_value())

            max_per_torrent = self.get_widget("max_per_torrent")
            if max_per_torrent:
                connection_settings["max_per_torrent"] = int(max_per_torrent.get_value())

            max_upload_slots = self.get_widget("max_upload_slots")
            if max_upload_slots:
                connection_settings["max_upload_slots"] = int(max_upload_slots.get_value())

            settings["connection"] = connection_settings

            # Proxy settings
            settings["proxy"] = self._collect_proxy_settings()

        except Exception as e:
            self.logger.error(f"Error collecting Connection tab settings: {e}")

        return settings

    def _collect_proxy_settings(self) -> Dict[str, Any]:
        """Collect proxy settings from widgets."""
        proxy_settings: Dict[str, Any] = {}

        try:
            proxy_type = self.get_widget("proxy_type")
            if proxy_type:
                type_mapping = {0: "none", 1: "http", 2: "socks4", 3: "socks5"}
                proxy_settings["type"] = type_mapping.get(proxy_type.get_selected(), "none")

            proxy_server = self.get_widget("proxy_server")
            if proxy_server:
                proxy_settings["server"] = proxy_server.get_text()

            proxy_port = self.get_widget("proxy_port")
            if proxy_port:
                proxy_settings["port"] = int(proxy_port.get_value())

            proxy_auth = self.get_widget("proxy_auth_enabled")
            if proxy_auth:
                proxy_settings["auth_enabled"] = proxy_auth.get_active()

            proxy_username = self.get_widget("proxy_username")
            if proxy_username:
                proxy_settings["username"] = proxy_username.get_text()

            proxy_password = self.get_widget("proxy_password")
            if proxy_password:
                proxy_settings["password"] = proxy_password.get_text()

        except Exception as e:
            self.logger.error(f"Error collecting proxy settings: {e}")

        return proxy_settings

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Connection tab settings."""
        errors = {}

        try:
            # Validate listening port
            listening_port = self.get_widget("listening_port")
            if listening_port:
                port_errors = self.validate_port(listening_port.get_value())
                errors.update(port_errors)

            # Validate proxy port if proxy is enabled
            proxy_type = self.get_widget("proxy_type")
            proxy_port = self.get_widget("proxy_port")
            if proxy_type and proxy_port and proxy_type.get_selected() > 0:
                proxy_port_errors = self.validate_port(proxy_port.get_value())
                if proxy_port_errors:
                    errors["proxy_port"] = proxy_port_errors.get("port", "Invalid proxy port")

        except Exception as e:
            self.logger.error(f"Error validating Connection tab settings: {e}")
            errors["general"] = str(e)

        return errors

    # Signal handlers
    def on_listening_port_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle listening port change."""
        try:
            port = int(spin_button.get_value())
            validation_errors = self.validate_port(port)

            if validation_errors:
                self.show_notification(validation_errors["port"], "error")
            else:
                self.app_settings.set("connection.listening_port", port)
                self.logger.debug(f"Listening port changed to: {port}")

        except Exception as e:
            self.logger.error(f"Error changing listening port: {e}")

    def on_random_port_clicked(self, button: Gtk.Button) -> None:
        """Generate and set a random port."""
        try:
            # Get configured port range or use defaults
            ui_settings = getattr(self.app_settings, "ui_settings", {})
            min_port = ui_settings.get("random_port_range_min", 49152)
            max_port = ui_settings.get("random_port_range_max", 65535)

            random_port = self.generate_random_port(min_port, max_port)

            listening_port = self.get_widget("listening_port")
            if listening_port:
                listening_port.set_value(random_port)
                self.show_notification("Random port generated: {}".format(random_port), "success")

        except Exception as e:
            self.logger.error(f"Error generating random port: {e}")

    def on_upnp_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle UPnP setting change."""
        try:
            self.app_settings.set("connection.upnp_enabled", state)
            message = "UPnP enabled" if state else "UPnP disabled"
            self.show_notification(message, "success")

        except Exception as e:
            self.logger.error(f"Error changing UPnP setting: {e}")

    def on_connection_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle connection limit changes."""
        self.on_setting_changed(spin_button)

    def on_proxy_type_changed(self, dropdown: Gtk.DropDown, param) -> None:
        """Handle proxy type change."""
        try:
            self.update_dependencies()

            type_mapping = {0: "none", 1: "http", 2: "socks4", 3: "socks5"}
            proxy_type = type_mapping.get(dropdown.get_selected(), "none")

            self.app_settings.set("proxy.type", proxy_type)
            self.logger.debug(f"Proxy type changed to: {proxy_type}")

        except Exception as e:
            self.logger.error(f"Error changing proxy type: {e}")

    def on_proxy_auth_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle proxy authentication toggle."""
        try:
            self.update_dependencies()
            self.app_settings.set("proxy.auth_enabled", state)

        except Exception as e:
            self.logger.error(f"Error changing proxy authentication: {e}")

    def on_proxy_server_changed(self, entry: Gtk.Entry) -> None:
        """Handle proxy server change."""
        try:
            server = entry.get_text()
            self.app_settings.set("proxy.server", server)

        except Exception as e:
            self.logger.error(f"Error changing proxy server: {e}")

    def on_proxy_port_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle proxy port change."""
        try:
            port = int(spin_button.get_value())
            validation_errors = self.validate_port(port)

            if validation_errors:
                self.show_notification(validation_errors["port"], "error")
            else:
                self.app_settings.set("proxy.port", port)

        except Exception as e:
            self.logger.error(f"Error changing proxy port: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset Connection tab to default values."""
        try:
            # Reset to default connection values
            listening_port = self.get_widget("listening_port")
            if listening_port:
                listening_port.set_value(NetworkConstants.DEFAULT_PORT)

            upnp_enabled = self.get_widget("upnp_enabled")
            if upnp_enabled:
                upnp_enabled.set_active(True)

            max_global = self.get_widget("max_global_connections")
            if max_global:
                max_global.set_value(200)

            max_per_torrent = self.get_widget("max_per_torrent")
            if max_per_torrent:
                max_per_torrent.set_value(50)

            max_upload_slots = self.get_widget("max_upload_slots")
            if max_upload_slots:
                max_upload_slots.set_value(4)

            # Reset proxy settings
            proxy_type = self.get_widget("proxy_type")
            if proxy_type:
                proxy_type.set_selected(0)  # None

            proxy_auth = self.get_widget("proxy_auth_enabled")
            if proxy_auth:
                proxy_auth.set_active(False)

            self.update_dependencies()
            self.show_notification("Connection settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting Connection tab to defaults: {e}")

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.debug(
            "ConnectionTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "ConnectionTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "ConnectionTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.debug(
            "ConnectionTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()
