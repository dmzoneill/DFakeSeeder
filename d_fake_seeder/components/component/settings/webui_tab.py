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

    # Note: Most WebUI settings use manual loading/saving due to nested structure
    # and complex dependency logic
    WIDGET_MAPPINGS: list = []

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

        except Exception as e:
            self.logger.error(f"Error loading Web UI tab settings: {e}")

    def _load_webui_settings(self) -> None:
        """Load Web UI settings using nested keys."""
        try:
            # Main settings
            enable_webui = self.get_widget("enable_webui")
            if enable_webui:
                self.set_switch_state(enable_webui, self.app_settings.webui_enabled)

            webui_port = self.get_widget("webui_port")
            if webui_port:
                webui_port.set_value(self.app_settings.webui_port)

            webui_https = self.get_widget("webui_https_enabled")
            if webui_https:
                self.set_switch_state(webui_https, self.app_settings.webui_https_enabled)

            webui_localhost = self.get_widget("webui_localhost_only")
            if webui_localhost:
                self.set_switch_state(webui_localhost, self.app_settings.webui_localhost_only)

            webui_interface = self.get_widget("webui_interface")
            if webui_interface:
                webui_interface.set_text(self.app_settings.webui_interface)

            # Authentication
            webui_auth = self.get_widget("webui_auth_enabled")
            if webui_auth:
                self.set_switch_state(webui_auth, self.app_settings.webui_auth_enabled)

            webui_username = self.get_widget("webui_username")
            if webui_username:
                webui_username.set_text(self.app_settings.webui_username)

            webui_password = self.get_widget("webui_password")
            if webui_password:
                webui_password.set_text(self.app_settings.webui_password)

            webui_session = self.get_widget("webui_session_timeout")
            if webui_session:
                webui_session.set_value(self.app_settings.webui_session_timeout)

            # Security
            webui_csrf = self.get_widget("webui_csrf_protection")
            if webui_csrf:
                self.set_switch_state(webui_csrf, self.app_settings.webui_csrf_protection)

            webui_clickjacking = self.get_widget("webui_clickjacking_protection")
            if webui_clickjacking:
                self.set_switch_state(webui_clickjacking, self.app_settings.webui_clickjacking_protection)

            webui_secure_headers = self.get_widget("webui_secure_headers")
            if webui_secure_headers:
                self.set_switch_state(webui_secure_headers, self.app_settings.webui_secure_headers)

            webui_host_header = self.get_widget("webui_host_header_validation")
            if webui_host_header:
                self.set_switch_state(webui_host_header, self.app_settings.webui_host_header_validation)

            webui_ban = self.get_widget("webui_ban_after_failures")
            if webui_ban:
                webui_ban.set_value(self.app_settings.webui_ban_after_failures)

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

        except Exception as e:
            self.logger.error(f"Error updating Web UI dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from WebUI tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: Dict[str, Any] = {}

        # Collect WebUI settings with proper nested key prefixes
        settings.update(self._collect_webui_settings())

        self.logger.trace(f"Collected {len(settings)} settings from WebUI tab")
        return settings

    def _collect_webui_settings(self) -> Dict[str, Any]:
        """Collect Web UI settings with nested keys."""
        settings: Dict[str, Any] = {}

        try:
            # Main settings
            enable_webui = self.get_widget("enable_webui")
            if enable_webui:
                settings["webui.enabled"] = enable_webui.get_active()

            webui_port = self.get_widget("webui_port")
            if webui_port:
                settings["webui.port"] = int(webui_port.get_value())

            webui_https = self.get_widget("webui_https_enabled")
            if webui_https:
                settings["webui.https_enabled"] = webui_https.get_active()

            webui_localhost = self.get_widget("webui_localhost_only")
            if webui_localhost:
                settings["webui.localhost_only"] = webui_localhost.get_active()

            webui_interface = self.get_widget("webui_interface")
            if webui_interface:
                settings["webui.interface"] = webui_interface.get_text()

            # Authentication
            webui_auth = self.get_widget("webui_auth_enabled")
            if webui_auth:
                settings["webui.auth_enabled"] = webui_auth.get_active()

            webui_username = self.get_widget("webui_username")
            if webui_username:
                settings["webui.username"] = webui_username.get_text()

            webui_password = self.get_widget("webui_password")
            if webui_password:
                settings["webui.password"] = webui_password.get_text()

            webui_session = self.get_widget("webui_session_timeout")
            if webui_session:
                settings["webui.session_timeout_minutes"] = int(webui_session.get_value())

            # Security
            webui_csrf = self.get_widget("webui_csrf_protection")
            if webui_csrf:
                settings["webui.csrf_protection"] = webui_csrf.get_active()

            webui_clickjacking = self.get_widget("webui_clickjacking_protection")
            if webui_clickjacking:
                settings["webui.clickjacking_protection"] = webui_clickjacking.get_active()

            webui_secure_headers = self.get_widget("webui_secure_headers")
            if webui_secure_headers:
                settings["webui.secure_headers"] = webui_secure_headers.get_active()

            webui_host_header = self.get_widget("webui_host_header_validation")
            if webui_host_header:
                settings["webui.host_header_validation"] = webui_host_header.get_active()

            webui_ban = self.get_widget("webui_ban_after_failures")
            if webui_ban:
                settings["webui.ban_after_failures"] = int(webui_ban.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting Web UI settings: {e}")

        return settings

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Web UI tab settings."""
        errors = {}  # type: ignore[var-annotated]

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
                self._update_url_label()
        except Exception as e:
            self.logger.error(f"Error changing Web UI port: {e}")

    def on_webui_https_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle HTTPS toggle change."""
        if self._loading_settings:
            return
        try:
            self._update_url_label()
            message = "HTTPS will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except Exception as e:
            self.logger.error(f"Error changing HTTPS setting: {e}")

    def on_webui_localhost_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle localhost only toggle change."""
        if self._loading_settings:
            return
        try:
            self.update_dependencies()
            message = "Localhost only will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except Exception as e:
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
        except Exception as e:
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

            webui_https = self.get_widget("webui_https_enabled")
            if webui_https:
                self.set_switch_state(webui_https, False)

            webui_localhost = self.get_widget("webui_localhost_only")
            if webui_localhost:
                self.set_switch_state(webui_localhost, True)

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

            webui_session = self.get_widget("webui_session_timeout")
            if webui_session:
                webui_session.set_value(60)

            # Reset security settings
            webui_csrf = self.get_widget("webui_csrf_protection")
            if webui_csrf:
                self.set_switch_state(webui_csrf, True)

            webui_clickjacking = self.get_widget("webui_clickjacking_protection")
            if webui_clickjacking:
                self.set_switch_state(webui_clickjacking, True)

            webui_secure_headers = self.get_widget("webui_secure_headers")
            if webui_secure_headers:
                self.set_switch_state(webui_secure_headers, True)

            webui_host_header = self.get_widget("webui_host_header_validation")
            if webui_host_header:
                self.set_switch_state(webui_host_header, True)

            webui_ban = self.get_widget("webui_ban_after_failures")
            if webui_ban:
                webui_ban.set_value(5)

            self.update_dependencies()
            self._update_url_label()
            self.show_notification("Web UI settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting Web UI tab to defaults: {e}")

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
