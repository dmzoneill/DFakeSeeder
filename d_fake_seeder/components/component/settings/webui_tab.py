"""
Web UI settings tab for the settings dialog.

Handles web interface configuration, authentication, and security settings.
"""

from typing import Any, ClassVar

from d_fake_seeder.lib.gi_gtk4 import GLib, Gtk

from .base_tab import BaseSettingsTab
from .settings_mixins import (
    NotificationMixin,
    TranslationMixin,
    UtilityMixin,
    ValidationMixin,
)


class WebUITab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """
    Web UI settings tab component.

    Manages:
    - Web interface enable/disable
    - Port configuration
    - Authentication settings
    - Security configuration
    """

    # Note: Most WebUI settings use manual loading/saving due to nested structure
    # and complex dependency logic
    WIDGET_MAPPINGS: ClassVar[list] = []

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Web UI"

    def _init_widgets(self) -> None:
        """Initialize Web UI tab widgets."""
        # Cache commonly used widgets
        self._widgets.update(
            {
                # Section containers (these are hardcoded to sensitive=False in XML)
                "webui_config_box": self.builder.get_object("settings_webui_config_box"),
                "webui_auth_box": self.builder.get_object("settings_webui_auth_box"),
                "webui_security_box": self.builder.get_object("settings_webui_security_box"),
                "webui_auth_settings_box": self.builder.get_object("settings_webui_auth_settings_box"),
                "webui_interface_box": self.builder.get_object("settings_webui_interface_box"),
                # Main settings
                "enable_webui": self.builder.get_object("settings_enable_webui"),
                "webui_port": self.builder.get_object("settings_webui_port"),
                "webui_url_label": self.builder.get_object("settings_webui_url_label"),
                "webui_https_enabled": self.builder.get_object("settings_webui_https_enabled"),
                "webui_localhost_only": self.builder.get_object("settings_webui_localhost_only"),
                "webui_interface": self.builder.get_object("settings_webui_interface"),
                # Authentication
                "webui_auth_enabled": self.builder.get_object("settings_webui_auth_enabled"),
                "webui_username": self.builder.get_object("settings_webui_username"),
                "webui_password": self.builder.get_object("settings_webui_password"),
                "webui_generate_password": self.builder.get_object("settings_webui_generate_password"),
                "webui_session_timeout": self.builder.get_object("settings_webui_session_timeout"),
                # Security
                "webui_csrf_protection": self.builder.get_object("settings_webui_csrf_protection"),
                "webui_clickjacking_protection": self.builder.get_object("settings_webui_clickjacking_protection"),
                "webui_secure_headers": self.builder.get_object("settings_webui_secure_headers"),
                "webui_host_header_validation": self.builder.get_object("settings_webui_host_header_validation"),
                "webui_ban_after_failures": self.builder.get_object("settings_webui_ban_after_failures"),
            }
        )

    def _connect_signals(self) -> None:
        """Connect signal handlers for Web UI tab."""
        # Main enable switch (has dependencies - controls all other widgets)
        enable_webui = self.get_widget("enable_webui")
        if enable_webui:
            self.track_signal(
                enable_webui,
                enable_webui.connect("state-set", self.on_enable_webui_changed),
            )

        # Port setting (has validation logic and updates URL label)
        webui_port = self.get_widget("webui_port")
        if webui_port:
            self.track_signal(
                webui_port,
                webui_port.connect("value-changed", self.on_webui_port_changed),
            )

        # HTTPS toggle (updates URL label)
        webui_https = self.get_widget("webui_https_enabled")
        if webui_https:
            self.track_signal(
                webui_https,
                webui_https.connect("state-set", self.on_webui_https_changed),
            )

        # Localhost only toggle (controls interface entry visibility)
        webui_localhost = self.get_widget("webui_localhost_only")
        if webui_localhost:
            self.track_signal(
                webui_localhost,
                webui_localhost.connect("state-set", self.on_webui_localhost_changed),
            )

        # Authentication enable (has dependencies - controls username/password/generate)
        webui_auth = self.get_widget("webui_auth_enabled")
        if webui_auth:
            self.track_signal(webui_auth, webui_auth.connect("state-set", self.on_webui_auth_changed))

        # Password generation button (complex logic)
        gen_password = self.get_widget("webui_generate_password")
        if gen_password:
            self.track_signal(
                gen_password,
                gen_password.connect("clicked", self.on_generate_password_clicked),
            )

    def _load_settings(self) -> None:
        """Load current settings into Web UI tab widgets."""
        try:
            # Load Web UI settings using nested keys
            self._load_webui_settings()

            # Update widget dependencies after loading (enable/disable based on loaded state)
            self.update_dependencies()

            # Update URL label after loading
            self._update_url_label()

            self.logger.info("Web UI tab settings loaded")

        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error loading Web UI tab settings: {e}")

    def _load_webui_settings(self) -> None:
        """Load Web UI settings using nested keys."""
        try:
            self._load_webui_switches()
            self._load_webui_values()
            self._load_webui_texts()
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error loading Web UI settings: {e}")

    def _load_webui_switches(self) -> None:
        """Load the Web UI on/off switch widgets from app settings."""
        switches = [
            ("enable_webui", "webui_enabled"),
            ("webui_https_enabled", "webui_https_enabled"),
            ("webui_localhost_only", "webui_localhost_only"),
            ("webui_auth_enabled", "webui_auth_enabled"),
            ("webui_csrf_protection", "webui_csrf_protection"),
            ("webui_clickjacking_protection", "webui_clickjacking_protection"),
            ("webui_secure_headers", "webui_secure_headers"),
            ("webui_host_header_validation", "webui_host_header_validation"),
        ]
        for widget_id, attr in switches:
            widget = self.get_widget(widget_id)
            if widget:
                self.set_switch_state(widget, getattr(self.app_settings, attr))

    def _load_webui_values(self) -> None:
        """Load the Web UI spin-button widgets from app settings."""
        values = [
            ("webui_port", "webui_port"),
            ("webui_session_timeout", "webui_session_timeout"),
            ("webui_ban_after_failures", "webui_ban_after_failures"),
        ]
        for widget_id, attr in values:
            widget = self.get_widget(widget_id)
            if widget:
                widget.set_value(getattr(self.app_settings, attr))

    def _load_webui_texts(self) -> None:
        """Load the Web UI text-entry widgets from app settings."""
        texts = [
            ("webui_interface", "webui_interface"),
            ("webui_username", "webui_username"),
            ("webui_password", "webui_password"),
        ]
        for widget_id, attr in texts:
            widget = self.get_widget(widget_id)
            if widget:
                widget.set_text(getattr(self.app_settings, attr))

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Web UI tab."""
        self._update_webui_dependencies()

    def _update_tab_dependencies(self) -> None:
        """Update Web UI tab dependencies."""
        self._update_webui_dependencies()

    def _update_webui_dependencies(self) -> None:
        """Update Web UI-related widget dependencies."""
        try:
            # Enable/disable all Web UI controls based on main enable switch
            enable_webui = self.get_widget("enable_webui")
            webui_enabled = enable_webui and enable_webui.get_active()

            # IMPORTANT: Enable all three main section containers that are hardcoded to sensitive=False in XML
            self.update_widget_sensitivity("webui_config_box", webui_enabled)  # Connection Settings
            self.update_widget_sensitivity("webui_auth_box", webui_enabled)  # Authentication
            self.update_widget_sensitivity("webui_security_box", webui_enabled)  # Security Options

            # Main settings
            self.update_widget_sensitivity("webui_port", webui_enabled)
            self.update_widget_sensitivity("webui_https_enabled", webui_enabled)
            self.update_widget_sensitivity("webui_localhost_only", webui_enabled)

            # Interface entry is only enabled when localhost_only is False
            webui_localhost = self.get_widget("webui_localhost_only")
            localhost_only = webui_localhost and webui_localhost.get_active()
            interface_enabled = webui_enabled and not localhost_only
            self.update_widget_sensitivity("webui_interface_box", interface_enabled)
            self.update_widget_sensitivity("webui_interface", interface_enabled)

            # Authentication section
            self.update_widget_sensitivity("webui_auth_enabled", webui_enabled)

            # Authentication-specific controls
            webui_auth = self.get_widget("webui_auth_enabled")
            auth_enabled = webui_enabled and webui_auth and webui_auth.get_active()
            self.update_widget_sensitivity("webui_auth_settings_box", auth_enabled)
            self.update_widget_sensitivity("webui_username", auth_enabled)
            self.update_widget_sensitivity("webui_password", auth_enabled)
            self.update_widget_sensitivity("webui_generate_password", auth_enabled)
            self.update_widget_sensitivity("webui_session_timeout", auth_enabled)

            # Security settings
            self.update_widget_sensitivity("webui_csrf_protection", webui_enabled)
            self.update_widget_sensitivity("webui_clickjacking_protection", webui_enabled)
            self.update_widget_sensitivity("webui_secure_headers", webui_enabled)
            self.update_widget_sensitivity("webui_host_header_validation", webui_enabled)
            self.update_widget_sensitivity("webui_ban_after_failures", webui_enabled)

        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error updating Web UI dependencies: {e}")

    def _collect_settings(self) -> dict[str, Any]:
        """Collect current settings from WebUI tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: dict[str, Any] = {}

        # Collect WebUI settings with proper nested key prefixes
        settings.update(self._collect_webui_settings())

        self.logger.trace(f"Collected {len(settings)} settings from WebUI tab")
        return settings

    def _collect_webui_settings(self) -> dict[str, Any]:
        """Collect Web UI settings with nested keys."""
        settings: dict[str, Any] = {}

        try:
            self._collect_webui_bools(settings)
            self._collect_webui_ints(settings)
            self._collect_webui_texts(settings)
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error collecting Web UI settings: {e}")

        return settings

    def _collect_webui_bools(self, settings: dict[str, Any]) -> None:
        """Collect the Web UI switch states into ``settings``."""
        bools = [
            ("enable_webui", "webui.enabled"),
            ("webui_https_enabled", "webui.https_enabled"),
            ("webui_localhost_only", "webui.localhost_only"),
            ("webui_auth_enabled", "webui.auth_enabled"),
            ("webui_csrf_protection", "webui.csrf_protection"),
            ("webui_clickjacking_protection", "webui.clickjacking_protection"),
            ("webui_secure_headers", "webui.secure_headers"),
            ("webui_host_header_validation", "webui.host_header_validation"),
        ]
        for widget_id, key in bools:
            widget = self.get_widget(widget_id)
            if widget:
                settings[key] = widget.get_active()

    def _collect_webui_ints(self, settings: dict[str, Any]) -> None:
        """Collect the Web UI integer spin values into ``settings``."""
        integers = [
            ("webui_port", "webui.port"),
            ("webui_session_timeout", "webui.session_timeout_minutes"),
            ("webui_ban_after_failures", "webui.ban_after_failures"),
        ]
        for widget_id, key in integers:
            widget = self.get_widget(widget_id)
            if widget:
                settings[key] = int(widget.get_value())

    def _collect_webui_texts(self, settings: dict[str, Any]) -> None:
        """Collect the Web UI text-entry values into ``settings``."""
        texts = [
            ("webui_interface", "webui.interface"),
            ("webui_username", "webui.username"),
            ("webui_password", "webui.password"),
        ]
        for widget_id, key in texts:
            widget = self.get_widget(widget_id)
            if widget:
                settings[key] = widget.get_text()

    def _validate_tab_settings(self) -> dict[str, str]:
        """Validate Web UI tab settings."""
        errors: dict[str, str] = {}

        try:
            # Only validate WebUI settings when WebUI is actually enabled
            enable_webui = self.get_widget("enable_webui")
            webui_enabled = enable_webui and enable_webui.get_active()
            if not webui_enabled:
                # Skip all validation when WebUI is disabled
                return errors

            self._validate_webui_port(errors)
            self._validate_webui_interface(errors)
            self._validate_webui_auth(errors)
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error validating Web UI tab settings: {e}")
            errors["general"] = str(e)

        return errors

    def _validate_webui_port(self, errors: dict[str, str]) -> None:
        """Validate the Web UI port widget."""
        webui_port = self.get_widget("webui_port")
        if webui_port:
            errors.update(self.validate_port(webui_port.get_value()))

    def _validate_webui_interface(self, errors: dict[str, str]) -> None:
        """Validate the Web UI bind-interface, skipping loopback and all-zeros."""
        webui_interface = self.get_widget("webui_interface")
        if not webui_interface:
            return
        interface = webui_interface.get_text().strip()
        # Skip empty, loopback, and the all-zeros (bind-all) interface.
        if not interface or interface == "127.0.0.1" or interface.split(".") == ["0", "0", "0", "0"]:
            return
        message = self._interface_error(interface)
        if message:
            errors["webui_interface"] = message

    @staticmethod
    def _interface_error(interface: str) -> str | None:
        """Return an error message for a malformed IPv4 interface, else ``None``."""
        parts = interface.split(".")
        if len(parts) != 4:
            return "Invalid IP address format"
        for part in parts:
            try:
                num = int(part)
            except ValueError:
                return "Invalid IP address"
            if num < 0 or num > 255:
                return "Invalid IP address"
        return None

    def _validate_webui_auth(self, errors: dict[str, str]) -> None:
        """Validate that username and password are set when auth is enabled."""
        webui_auth = self.get_widget("webui_auth_enabled")
        if not (webui_auth and webui_auth.get_active()):
            return
        webui_username = self.get_widget("webui_username")
        if webui_username and not webui_username.get_text().strip():
            errors["webui_username"] = "Username cannot be empty when authentication is enabled"
        webui_password = self.get_widget("webui_password")
        if webui_password and not webui_password.get_text():
            errors["webui_password"] = "Password cannot be empty when authentication is enabled"

    # Signal handlers
    def on_enable_webui_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle Web UI enable/disable."""
        if self._loading_settings:
            return
        try:
            self.update_dependencies()
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Web UI will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error changing Web UI enable setting: {e}")

    def on_webui_port_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle Web UI port change."""
        try:
            port = int(spin_button.get_value())
            validation_errors = self.validate_port(port)

            if validation_errors:
                self.show_notification(validation_errors["port"], "error")
            else:
                # NOTE: Setting will be saved in batch via _collect_settings()
                self.logger.trace(f"Web UI port changed to: {port}")
                self._update_url_label()
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error changing Web UI port: {e}")

    def on_webui_https_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle HTTPS toggle change."""
        if self._loading_settings:
            return
        try:
            self._update_url_label()
            message = "HTTPS will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error changing HTTPS setting: {e}")

    def on_webui_localhost_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle localhost only toggle change."""
        if self._loading_settings:
            return
        try:
            self.update_dependencies()
            message = "Localhost only will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error changing localhost setting: {e}")

    def _update_url_label(self) -> None:
        """Update the URL label based on current settings."""
        try:
            url_label = self.get_widget("webui_url_label")
            if not url_label:
                return

            webui_port = self.get_widget("webui_port")
            webui_https = self.get_widget("webui_https_enabled")

            port = int(webui_port.get_value()) if webui_port else 8080
            https = webui_https.get_active() if webui_https else False

            protocol = "https" if https else "http"
            url_label.set_text(f"URL: {protocol}://localhost:{port}")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error updating URL label: {e}")

    def on_webui_auth_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle Web UI authentication toggle."""
        if self._loading_settings:
            return
        try:
            self.update_dependencies()
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Web UI authentication will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error changing Web UI authentication: {e}")

    def on_generate_password_clicked(self, button: Gtk.Button) -> None:
        """Generate a secure password for Web UI."""
        try:
            # Get configured password length or use default
            ui_settings = getattr(self.app_settings, "ui_settings", {})
            password_length = ui_settings.get("password_length", 16)

            new_password = self.generate_secure_password(password_length)

            webui_password = self.get_widget("webui_password")
            if webui_password:
                webui_password.set_text(new_password)
                self.show_notification(self._("Secure password generated"), "success")

        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error generating password: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset Web UI tab to default values."""
        try:
            self._reset_webui_main()
            self._reset_webui_auth()
            self._reset_webui_security()
            self.update_dependencies()
            self._update_url_label()
            self.show_notification(self._("Web UI settings reset to defaults"), "success")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(f"Error resetting Web UI tab to defaults: {e}")

    def _reset_webui_main(self) -> None:
        """Reset the main Web UI connection settings to defaults."""
        enable_webui = self.get_widget("enable_webui")
        if enable_webui:
            self.set_switch_state(enable_webui, False)
        webui_port = self.get_widget("webui_port")
        if webui_port:
            webui_port.set_value(8080)
        webui_https = self.get_widget("webui_https_enabled")
        if webui_https:
            self.set_switch_state(webui_https, False)
        webui_localhost = self.get_widget("webui_localhost_only")
        if webui_localhost:
            self.set_switch_state(webui_localhost, True)
        webui_interface = self.get_widget("webui_interface")
        if webui_interface:
            webui_interface.set_text("127.0.0.1")

    def _reset_webui_auth(self) -> None:
        """Reset the Web UI authentication settings to defaults."""
        webui_auth = self.get_widget("webui_auth_enabled")
        if webui_auth:
            self.set_switch_state(webui_auth, True)
        webui_username = self.get_widget("webui_username")
        if webui_username:
            webui_username.set_text("admin")
        webui_password = self.get_widget("webui_password")
        if webui_password:
            webui_password.set_text("")
        webui_session = self.get_widget("webui_session_timeout")
        if webui_session:
            webui_session.set_value(60)

    def _reset_webui_security(self) -> None:
        """Reset the Web UI security settings to defaults."""
        for widget_id in (
            "webui_csrf_protection",
            "webui_clickjacking_protection",
            "webui_secure_headers",
            "webui_host_header_validation",
        ):
            widget = self.get_widget(widget_id)
            if widget:
                self.set_switch_state(widget, True)
        webui_ban = self.get_widget("webui_ban_after_failures")
        if webui_ban:
            webui_ban.set_value(5)

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace(
            "WebUITab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()
