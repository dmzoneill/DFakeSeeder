"""
Web UI settings tab for the settings dialog.

Handles web interface configuration, authentication, and security settings.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import (  # noqa: E402
    TranslationMixin,
    UtilityMixin,
    ValidationMixin,
)

# fmt: on


class WebUITab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """
    Web UI settings tab component.

    Manages:
    - Web interface enable/disable
    - Port configuration
    - Authentication settings
    - Security configuration
    """

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS = [
        # Security settings
        {
            "id": "settings_webui_https_enabled",
            "name": "webui_https_enabled",
            "setting_key": "webui.https_enabled",
            "type": bool,
            "on_change": lambda self, value: self.show_notification(
                f"HTTPS {'enabled' if value else 'disabled'}", "success"
            ),
        },
        {
            "id": "settings_webui_csrf_protection",
            "name": "webui_csrf_protection",
            "setting_key": "webui.csrf_protection",
            "type": bool,
            "on_change": lambda self, value: self.show_notification(
                f"CSRF protection {'enabled' if value else 'disabled'}", "success"
            ),
        },
        {
            "id": "settings_webui_host_header_validation",
            "name": "webui_host_header_validation",
            "setting_key": "webui.host_header_validation",
            "type": bool,
            "on_change": lambda self, value: self.show_notification(
                f"Host header validation {'enabled' if value else 'disabled'}", "success"
            ),
        },
        # Access control
        {
            "id": "settings_webui_ban_after_failures",
            "name": "webui_ban_after_failures",
            "setting_key": "webui.ban_after_failures",
            "type": int,
        },
        {
            "id": "settings_webui_session_timeout",
            "name": "webui_session_timeout",
            "setting_key": "webui.session_timeout_minutes",
            "type": int,
        },
        # Main settings
        {
            "id": "settings_webui_interface",
            "name": "webui_interface",
            "setting_key": "webui.interface",
            "type": str,
        },
        # Authentication
        {
            "id": "settings_webui_username",
            "name": "webui_username",
            "setting_key": "webui.username",
            "type": str,
        },
        {
            "id": "settings_webui_password",
            "name": "webui_password",
            "setting_key": "webui.password",
            "type": str,
        },
    ]

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
                # Main settings
                "enable_webui": self.builder.get_object("settings_enable_webui"),
                "webui_port": self.builder.get_object("settings_webui_port"),
                "webui_interface": self.builder.get_object("settings_webui_interface"),
                # Authentication
                "webui_auth_enabled": self.builder.get_object("settings_webui_auth_enabled"),
                "webui_username": self.builder.get_object("settings_webui_username"),
                "webui_password": self.builder.get_object("settings_webui_password"),
                "webui_generate_password": self.builder.get_object("settings_webui_generate_password"),
                # Security
                "webui_https_enabled": self.builder.get_object("settings_webui_https_enabled"),
                "webui_csrf_protection": self.builder.get_object("settings_webui_csrf_protection"),
                "webui_host_header_validation": self.builder.get_object("settings_webui_host_header_validation"),
                # Access control
                "webui_ban_after_failures": self.builder.get_object("settings_webui_ban_after_failures"),
                "webui_session_timeout": self.builder.get_object("settings_webui_session_timeout"),
            }
        )

    def _connect_signals(self) -> None:
        """Connect signal handlers for Web UI tab."""
        # Simple widgets (webui_https_enabled, webui_csrf_protection, webui_host_header_validation,
        # webui_ban_after_failures, webui_session_timeout, webui_interface, webui_username, webui_password)
        # are now auto-connected via WIDGET_MAPPINGS

        # Main enable switch (has dependencies - controls all other widgets)
        enable_webui = self.get_widget("enable_webui")
        if enable_webui:
            self.track_signal(
                enable_webui,
                enable_webui.connect("state-set", self.on_enable_webui_changed),
            )

        # Port setting (has validation logic)
        webui_port = self.get_widget("webui_port")
        if webui_port:
            self.track_signal(
                webui_port,
                webui_port.connect("value-changed", self.on_webui_port_changed),
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
            # Load Web UI settings
            webui_settings = getattr(self.app_settings, "webui", {})
            self._load_webui_settings(webui_settings)

            # Update widget dependencies after loading (enable/disable based on loaded state)
            self.update_dependencies()

            self.logger.info("Web UI tab settings loaded")

        except Exception as e:
            self.logger.error(f"Error loading Web UI tab settings: {e}")

    def _load_webui_settings(self, webui_settings: Dict[str, Any]) -> None:
        """Load Web UI settings."""
        try:
            # Main settings
            enable_webui = self.get_widget("enable_webui")
            if enable_webui:
                self.set_switch_state(enable_webui, webui_settings.get("enabled", False))

            webui_port = self.get_widget("webui_port")
            if webui_port:
                webui_port.set_value(webui_settings.get("port", 8080))

            webui_interface = self.get_widget("webui_interface")
            if webui_interface:
                webui_interface.set_text(webui_settings.get("interface", "127.0.0.1"))

            # Authentication
            webui_auth = self.get_widget("webui_auth_enabled")
            if webui_auth:
                self.set_switch_state(webui_auth, webui_settings.get("auth_enabled", True))

            webui_username = self.get_widget("webui_username")
            if webui_username:
                webui_username.set_text(webui_settings.get("username", "admin"))

            webui_password = self.get_widget("webui_password")
            if webui_password:
                webui_password.set_text(webui_settings.get("password", ""))

            # Security
            webui_https = self.get_widget("webui_https_enabled")
            if webui_https:
                self.set_switch_state(webui_https, webui_settings.get("https_enabled", False))

            webui_csrf = self.get_widget("webui_csrf_protection")
            if webui_csrf:
                self.set_switch_state(webui_csrf, webui_settings.get("csrf_protection", True))

            webui_host_header = self.get_widget("webui_host_header_validation")
            if webui_host_header:
                self.set_switch_state(webui_host_header, webui_settings.get("host_header_validation", True))

            # Access control
            webui_ban = self.get_widget("webui_ban_after_failures")
            if webui_ban:
                webui_ban.set_value(webui_settings.get("ban_after_failures", 5))

            webui_session = self.get_widget("webui_session_timeout")
            if webui_session:
                webui_session.set_value(webui_settings.get("session_timeout_minutes", 60))

        except Exception as e:
            self.logger.error(f"Error loading Web UI settings: {e}")

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

            # Main settings (already enabled via parent box above)
            self.update_widget_sensitivity("webui_port", webui_enabled)
            self.update_widget_sensitivity("webui_interface", webui_enabled)

            # Authentication section
            self.update_widget_sensitivity("webui_auth_enabled", webui_enabled)

            # Authentication-specific controls
            webui_auth = self.get_widget("webui_auth_enabled")
            auth_enabled = webui_enabled and webui_auth and webui_auth.get_active()

            self.update_widget_sensitivity("webui_username", auth_enabled)
            self.update_widget_sensitivity("webui_password", auth_enabled)
            self.update_widget_sensitivity("webui_generate_password", auth_enabled)

            # Security settings
            self.update_widget_sensitivity("webui_https_enabled", webui_enabled)
            self.update_widget_sensitivity("webui_csrf_protection", webui_enabled)
            self.update_widget_sensitivity("webui_host_header_validation", webui_enabled)

            # Access control
            self.update_widget_sensitivity("webui_ban_after_failures", webui_enabled)
            self.update_widget_sensitivity("webui_session_timeout", webui_enabled)

        except Exception as e:
            self.logger.error(f"Error updating Web UI dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from WebUI tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        # Collect from WIDGET_MAPPINGS
        settings = self._collect_mapped_settings()

        # Collect WebUI settings with proper key prefixes
        webui_settings = self._collect_webui_settings()
        for key, value in webui_settings.items():
            settings[f"webui.{key}"] = value

        self.logger.trace(f"Collected {len(settings)} settings from WebUI tab")
        return settings

    def _collect_webui_settings(self) -> Dict[str, Any]:
        """Collect Web UI settings."""
        webui_settings = {}

        try:
            # Main settings
            enable_webui = self.get_widget("enable_webui")
            if enable_webui:
                webui_settings["enabled"] = enable_webui.get_active()

            webui_port = self.get_widget("webui_port")
            if webui_port:
                webui_settings["port"] = int(webui_port.get_value())

            webui_interface = self.get_widget("webui_interface")
            if webui_interface:
                webui_settings["interface"] = webui_interface.get_text()

            # Authentication
            webui_auth = self.get_widget("webui_auth_enabled")
            if webui_auth:
                webui_settings["auth_enabled"] = webui_auth.get_active()

            webui_username = self.get_widget("webui_username")
            if webui_username:
                webui_settings["username"] = webui_username.get_text()

            webui_password = self.get_widget("webui_password")
            if webui_password:
                webui_settings["password"] = webui_password.get_text()

            # Security
            webui_https = self.get_widget("webui_https_enabled")
            if webui_https:
                webui_settings["https_enabled"] = webui_https.get_active()

            webui_csrf = self.get_widget("webui_csrf_protection")
            if webui_csrf:
                webui_settings["csrf_protection"] = webui_csrf.get_active()

            webui_host_header = self.get_widget("webui_host_header_validation")
            if webui_host_header:
                webui_settings["host_header_validation"] = webui_host_header.get_active()

            # Access control
            webui_ban = self.get_widget("webui_ban_after_failures")
            if webui_ban:
                webui_settings["ban_after_failures"] = int(webui_ban.get_value())

            webui_session = self.get_widget("webui_session_timeout")
            if webui_session:
                webui_settings["session_timeout_minutes"] = int(webui_session.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting Web UI settings: {e}")

        return webui_settings

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Web UI tab settings."""
        errors = {}

        try:
            # Only validate WebUI settings when WebUI is actually enabled
            enable_webui = self.get_widget("enable_webui")
            webui_enabled = enable_webui and enable_webui.get_active()

            if not webui_enabled:
                # Skip all validation when WebUI is disabled
                return errors

            # Validate port (only when WebUI is enabled)
            webui_port = self.get_widget("webui_port")
            if webui_port:
                port_errors = self.validate_port(webui_port.get_value())
                errors.update(port_errors)

            # Validate interface (basic IP validation, only when WebUI is enabled)
            webui_interface = self.get_widget("webui_interface")
            if webui_interface:
                interface = webui_interface.get_text().strip()
                if interface and interface != "0.0.0.0" and interface != "127.0.0.1":
                    # Basic IP validation
                    parts = interface.split(".")
                    if len(parts) != 4:
                        errors["webui_interface"] = "Invalid IP address format"
                    else:
                        try:
                            for part in parts:
                                num = int(part)
                                if num < 0 or num > 255:
                                    errors["webui_interface"] = "Invalid IP address"
                                    break
                        except ValueError:
                            errors["webui_interface"] = "Invalid IP address"

            # Validate authentication (only when WebUI AND auth are both enabled)

            webui_auth = self.get_widget("webui_auth_enabled")
            if webui_enabled and webui_auth and webui_auth.get_active():
                webui_username = self.get_widget("webui_username")
                if webui_username:
                    username = webui_username.get_text().strip()
                    if not username:
                        errors["webui_username"] = "Username cannot be empty when authentication is enabled"

                webui_password = self.get_widget("webui_password")
                if webui_password:
                    password = webui_password.get_text()
                    if not password:
                        errors["webui_password"] = "Password cannot be empty when authentication is enabled"

        except Exception as e:
            self.logger.error(f"Error validating Web UI tab settings: {e}")
            errors["general"] = str(e)

        return errors

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
        except Exception as e:
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
        except Exception as e:
            self.logger.error(f"Error changing Web UI port: {e}")

    def on_webui_auth_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle Web UI authentication toggle."""
        if self._loading_settings:
            return
        try:
            self.update_dependencies()
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Web UI authentication will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except Exception as e:
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
                self.show_notification("Secure password generated", "success")

        except Exception as e:
            self.logger.error(f"Error generating password: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset Web UI tab to default values."""
        try:
            # Reset main settings
            enable_webui = self.get_widget("enable_webui")
            if enable_webui:
                self.set_switch_state(enable_webui, False)

            webui_port = self.get_widget("webui_port")
            if webui_port:
                webui_port.set_value(8080)

            webui_interface = self.get_widget("webui_interface")
            if webui_interface:
                webui_interface.set_text("127.0.0.1")

            # Reset authentication
            webui_auth = self.get_widget("webui_auth_enabled")
            if webui_auth:
                self.set_switch_state(webui_auth, True)

            webui_username = self.get_widget("webui_username")
            if webui_username:
                webui_username.set_text("admin")

            webui_password = self.get_widget("webui_password")
            if webui_password:
                webui_password.set_text("")

            # Reset security settings
            webui_https = self.get_widget("webui_https_enabled")
            if webui_https:
                self.set_switch_state(webui_https, False)

            webui_csrf = self.get_widget("webui_csrf_protection")
            if webui_csrf:
                self.set_switch_state(webui_csrf, True)

            webui_host_header = self.get_widget("webui_host_header_validation")
            if webui_host_header:
                self.set_switch_state(webui_host_header, True)

            # Reset access control
            webui_ban = self.get_widget("webui_ban_after_failures")
            if webui_ban:
                webui_ban.set_value(5)

            webui_session = self.get_widget("webui_session_timeout")
            if webui_session:
                webui_session.set_value(60)

            self.update_dependencies()
            self.show_notification("Web UI settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting Web UI tab to defaults: {e}")

    def update_view(self, model, torrent, attribute):
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
