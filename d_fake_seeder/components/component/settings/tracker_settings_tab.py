"""
Tracker Settings Tab

Provides configuration interface for the inbuilt BitTorrent tracker.
Manages tracker server settings, self-tracking options, and security settings.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")

from .base_tab import BaseSettingsTab  # noqa: E402

# fmt: on


class TrackerSettingsTab(BaseSettingsTab):
    """Tracker configuration tab"""

    # Note: Tracker settings use manual loading/saving due to nested structure
    WIDGET_MAPPINGS: list = []

    @property
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        return "Tracker"

    def _init_widgets(self) -> None:
        """Initialize tracker-specific widgets"""
        # Main enable switch
        self._widgets["tracker_enabled"] = self.builder.get_object("tracker_enabled_switch")

        # HTTP Server Settings
        self._widgets["http_enabled"] = self.builder.get_object("tracker_http_enabled_switch")
        self._widgets["http_port"] = self.builder.get_object("tracker_http_port_spin")
        self._widgets["bind_address"] = self.builder.get_object("tracker_bind_address_entry")

        # UDP Server Settings
        self._widgets["udp_enabled"] = self.builder.get_object("tracker_udp_enabled_switch")
        self._widgets["udp_port"] = self.builder.get_object("tracker_udp_port_spin")

        # Announce Settings
        self._widgets["announce_interval"] = self.builder.get_object("tracker_announce_interval_spin")
        self._widgets["peer_timeout_multiplier"] = self.builder.get_object("tracker_peer_timeout_multiplier_spin")
        self._widgets["max_peers_per_announce"] = self.builder.get_object("tracker_max_peers_spin")

        # Features
        self._widgets["enable_scrape"] = self.builder.get_object("tracker_enable_scrape_switch")
        self._widgets["private_mode"] = self.builder.get_object("tracker_private_mode_switch")
        self._widgets["log_announces"] = self.builder.get_object("tracker_log_announces_switch")

        # Self-Tracking Settings
        self._widgets["self_tracking_enabled"] = self.builder.get_object("tracker_self_tracking_switch")
        self._widgets["announce_with_seeders"] = self.builder.get_object("tracker_announce_seeders_switch")
        self._widgets["sync_on_add"] = self.builder.get_object("tracker_sync_on_add_switch")
        self._widgets["sync_on_remove"] = self.builder.get_object("tracker_sync_on_remove_switch")

        # Security Settings
        self._widgets["rate_limit"] = self.builder.get_object("tracker_rate_limit_spin")
        self._widgets["ip_whitelist"] = self.builder.get_object("tracker_ip_whitelist_textview")
        self._widgets["ip_blacklist"] = self.builder.get_object("tracker_ip_blacklist_textview")

        self.logger.info("Tracker tab widgets initialized", extra={"class_name": self.__class__.__name__})

    def _connect_signals(self) -> None:
        """Connect tracker-specific signals"""
        # Main enable switch
        if self._widgets["tracker_enabled"]:
            self._widgets["tracker_enabled"].connect("state-set", self._on_tracker_enabled_changed)

        # HTTP enable switch (has dependencies)
        if self._widgets["http_enabled"]:
            self._widgets["http_enabled"].connect("state-set", self._on_http_enabled_changed)

        # UDP enable switch (has dependencies)
        if self._widgets["udp_enabled"]:
            self._widgets["udp_enabled"].connect("state-set", self._on_udp_enabled_changed)

        # Self-tracking switch (has dependencies)
        if self._widgets["self_tracking_enabled"]:
            self._widgets["self_tracking_enabled"].connect("state-set", self._on_self_tracking_changed)

        self.logger.trace("Tracker tab signals connected", extra={"class_name": self.__class__.__name__})

    def _load_settings(self) -> None:
        """Load tracker settings from configuration."""
        try:
            # Main enable
            if self._widgets["tracker_enabled"]:
                value = self.app_settings.get("tracker_settings.enabled", False)
                self._widgets["tracker_enabled"].set_active(value)

            # HTTP Settings
            if self._widgets["http_enabled"]:
                value = self.app_settings.get("tracker_settings.http_enabled", True)
                self._widgets["http_enabled"].set_active(value)

            if self._widgets["http_port"]:
                value = self.app_settings.get("tracker_settings.http_port", 6969)
                self._widgets["http_port"].set_value(value)

            if self._widgets["bind_address"]:
                value = self.app_settings.get("tracker_settings.bind_address", "0.0.0.0")
                self._widgets["bind_address"].set_text(value)

            # UDP Settings
            if self._widgets["udp_enabled"]:
                value = self.app_settings.get("tracker_settings.udp_enabled", False)
                self._widgets["udp_enabled"].set_active(value)

            if self._widgets["udp_port"]:
                value = self.app_settings.get("tracker_settings.udp_port", 6969)
                self._widgets["udp_port"].set_value(value)

            # Announce Settings
            if self._widgets["announce_interval"]:
                value = self.app_settings.get("tracker_settings.announce_interval_seconds", 1800)
                self._widgets["announce_interval"].set_value(value)

            if self._widgets["peer_timeout_multiplier"]:
                value = self.app_settings.get("tracker_settings.peer_timeout_multiplier", 3)
                self._widgets["peer_timeout_multiplier"].set_value(value)

            if self._widgets["max_peers_per_announce"]:
                value = self.app_settings.get("tracker_settings.max_peers_per_announce", 50)
                self._widgets["max_peers_per_announce"].set_value(value)

            # Features
            if self._widgets["enable_scrape"]:
                value = self.app_settings.get("tracker_settings.enable_scrape", True)
                self._widgets["enable_scrape"].set_active(value)

            if self._widgets["private_mode"]:
                value = self.app_settings.get("tracker_settings.private_mode", False)
                self._widgets["private_mode"].set_active(value)

            if self._widgets["log_announces"]:
                value = self.app_settings.get("tracker_settings.log_announces", False)
                self._widgets["log_announces"].set_active(value)

            # Self-Tracking
            if self._widgets["self_tracking_enabled"]:
                value = self.app_settings.get("tracker_settings.self_tracking.enabled", True)
                self._widgets["self_tracking_enabled"].set_active(value)

            if self._widgets["announce_with_seeders"]:
                value = self.app_settings.get("tracker_settings.self_tracking.announce_with_seeders", True)
                self._widgets["announce_with_seeders"].set_active(value)

            if self._widgets["sync_on_add"]:
                value = self.app_settings.get("tracker_settings.self_tracking.sync_on_add", True)
                self._widgets["sync_on_add"].set_active(value)

            if self._widgets["sync_on_remove"]:
                value = self.app_settings.get("tracker_settings.self_tracking.sync_on_remove", True)
                self._widgets["sync_on_remove"].set_active(value)

            # Security
            if self._widgets["rate_limit"]:
                value = self.app_settings.get("tracker_settings.security.rate_limit_per_minute", 60)
                self._widgets["rate_limit"].set_value(value)

            if self._widgets["ip_whitelist"]:
                buffer = self._widgets["ip_whitelist"].get_buffer()
                whitelist = self.app_settings.get("tracker_settings.security.ip_whitelist", [])
                buffer.set_text("\n".join(whitelist))

            if self._widgets["ip_blacklist"]:
                buffer = self._widgets["ip_blacklist"].get_buffer()
                blacklist = self.app_settings.get("tracker_settings.security.ip_blacklist", [])
                buffer.set_text("\n".join(blacklist))

            self.logger.trace(
                "Tracker settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current tracker settings from UI widgets."""
        settings: Dict[str, Any] = {}

        try:
            # Main enable
            if self._widgets.get("tracker_enabled"):
                settings["tracker_settings.enabled"] = self._widgets["tracker_enabled"].get_active()

            # HTTP Settings
            if self._widgets.get("http_enabled"):
                settings["tracker_settings.http_enabled"] = self._widgets["http_enabled"].get_active()

            if self._widgets.get("http_port"):
                settings["tracker_settings.http_port"] = int(self._widgets["http_port"].get_value())

            if self._widgets.get("bind_address"):
                settings["tracker_settings.bind_address"] = self._widgets["bind_address"].get_text().strip()

            # UDP Settings
            if self._widgets.get("udp_enabled"):
                settings["tracker_settings.udp_enabled"] = self._widgets["udp_enabled"].get_active()

            if self._widgets.get("udp_port"):
                settings["tracker_settings.udp_port"] = int(self._widgets["udp_port"].get_value())

            # Announce Settings
            if self._widgets.get("announce_interval"):
                settings["tracker_settings.announce_interval_seconds"] = int(
                    self._widgets["announce_interval"].get_value()
                )

            if self._widgets.get("peer_timeout_multiplier"):
                settings["tracker_settings.peer_timeout_multiplier"] = int(
                    self._widgets["peer_timeout_multiplier"].get_value()
                )

            if self._widgets.get("max_peers_per_announce"):
                settings["tracker_settings.max_peers_per_announce"] = int(
                    self._widgets["max_peers_per_announce"].get_value()
                )

            # Features
            if self._widgets.get("enable_scrape"):
                settings["tracker_settings.enable_scrape"] = self._widgets["enable_scrape"].get_active()

            if self._widgets.get("private_mode"):
                settings["tracker_settings.private_mode"] = self._widgets["private_mode"].get_active()

            if self._widgets.get("log_announces"):
                settings["tracker_settings.log_announces"] = self._widgets["log_announces"].get_active()

            # Self-Tracking
            if self._widgets.get("self_tracking_enabled"):
                settings["tracker_settings.self_tracking.enabled"] = self._widgets["self_tracking_enabled"].get_active()

            if self._widgets.get("announce_with_seeders"):
                settings["tracker_settings.self_tracking.announce_with_seeders"] = self._widgets[
                    "announce_with_seeders"
                ].get_active()

            if self._widgets.get("sync_on_add"):
                settings["tracker_settings.self_tracking.sync_on_add"] = self._widgets["sync_on_add"].get_active()

            if self._widgets.get("sync_on_remove"):
                settings["tracker_settings.self_tracking.sync_on_remove"] = self._widgets["sync_on_remove"].get_active()

            # Security
            if self._widgets.get("rate_limit"):
                settings["tracker_settings.security.rate_limit_per_minute"] = int(
                    self._widgets["rate_limit"].get_value()
                )

            if self._widgets.get("ip_whitelist"):
                buffer = self._widgets["ip_whitelist"].get_buffer()
                start, end = buffer.get_bounds()
                text = buffer.get_text(start, end, False)
                ips = [line.strip() for line in text.split("\n") if line.strip()]
                settings["tracker_settings.security.ip_whitelist"] = ips

            if self._widgets.get("ip_blacklist"):
                buffer = self._widgets["ip_blacklist"].get_buffer()
                start, end = buffer.get_bounds()
                text = buffer.get_text(start, end, False)
                ips = [line.strip() for line in text.split("\n") if line.strip()]
                settings["tracker_settings.security.ip_blacklist"] = ips

            self.logger.trace(f"Collected {len(settings)} settings from Tracker tab")
            return settings

        except Exception as e:
            self.logger.error(
                f"Failed to collect tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {}

    def _setup_dependencies(self, tracker_enabled_override: Any = None) -> None:
        """Set up dependencies between UI elements.

        Args:
            tracker_enabled_override: If provided, use this value instead of reading
                                      from the widget (needed during state-set signal
                                      when get_active() still returns old value)
        """
        try:
            # Main tracker enabled controls all other widgets
            if tracker_enabled_override is not None:
                tracker_enabled = tracker_enabled_override
            else:
                tracker_enabled = self._widgets.get("tracker_enabled") and self._widgets["tracker_enabled"].get_active()

            # All dependent widgets
            dependent_widgets = [
                "http_enabled",
                "http_port",
                "bind_address",
                "udp_enabled",
                "udp_port",
                "announce_interval",
                "peer_timeout_multiplier",
                "max_peers_per_announce",
                "enable_scrape",
                "private_mode",
                "log_announces",
                "self_tracking_enabled",
                "announce_with_seeders",
                "sync_on_add",
                "sync_on_remove",
                "rate_limit",
                "ip_whitelist",
                "ip_blacklist",
            ]

            for widget_name in dependent_widgets:
                if self._widgets.get(widget_name):
                    self._widgets[widget_name].set_sensitive(tracker_enabled)

            # HTTP port depends on HTTP enabled
            if self._widgets.get("http_enabled") and self._widgets.get("http_port"):
                http_enabled = tracker_enabled and self._widgets["http_enabled"].get_active()
                self._widgets["http_port"].set_sensitive(http_enabled)

            # UDP port depends on UDP enabled
            if self._widgets.get("udp_enabled") and self._widgets.get("udp_port"):
                udp_enabled = tracker_enabled and self._widgets["udp_enabled"].get_active()
                self._widgets["udp_port"].set_sensitive(udp_enabled)

            # Self-tracking sub-options depend on self-tracking enabled
            if self._widgets.get("self_tracking_enabled"):
                self_tracking = tracker_enabled and self._widgets["self_tracking_enabled"].get_active()
                for widget_name in [
                    "announce_with_seeders",
                    "sync_on_add",
                    "sync_on_remove",
                ]:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(self_tracking)

            self.logger.trace(
                f"Tracker tab dependencies set up (tracker_enabled={tracker_enabled})",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to set up tracker dependencies: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate tracker settings."""
        errors: Dict[str, str] = {}

        try:
            # Validate ports
            if self._widgets.get("http_port"):
                port = int(self._widgets["http_port"].get_value())
                if port < 1 or port > 65535:
                    errors["http_port"] = "HTTP port must be between 1 and 65535"
                elif port < 1024:
                    errors["http_port"] = "Ports below 1024 require root privileges"

            if self._widgets.get("udp_port"):
                port = int(self._widgets["udp_port"].get_value())
                if port < 1 or port > 65535:
                    errors["udp_port"] = "UDP port must be between 1 and 65535"
                elif port < 1024:
                    errors["udp_port"] = "Ports below 1024 require root privileges"

            # Validate announce interval
            if self._widgets.get("announce_interval"):
                interval = int(self._widgets["announce_interval"].get_value())
                if interval < 60:
                    errors["announce_interval"] = "Announce interval should be at least 60 seconds"

            # Validate IP lists
            for ip_widget_name in ["ip_whitelist", "ip_blacklist"]:
                if self._widgets.get(ip_widget_name):
                    buffer = self._widgets[ip_widget_name].get_buffer()
                    start, end = buffer.get_bounds()
                    text = buffer.get_text(start, end, False)
                    lines = [line.strip() for line in text.split("\n") if line.strip()]

                    for line in lines:
                        # Basic IP validation (could be enhanced)
                        parts = line.split(".")
                        if len(parts) != 4:
                            errors[ip_widget_name] = f"Invalid IP format: {line}"
                            break
                        try:
                            for part in parts:
                                num = int(part)
                                if num < 0 or num > 255:
                                    raise ValueError
                        except ValueError:
                            errors[ip_widget_name] = f"Invalid IP format: {line}"
                            break

        except Exception as e:
            errors["general"] = f"Validation error: {str(e)}"
            self.logger.error(
                f"Tracker settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return errors

    # Signal handlers
    def _on_tracker_enabled_changed(self, switch: Any, state: bool) -> None:
        """Handle tracker enable/disable toggle"""
        self.logger.trace(
            f"Tracker enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        # Pass the new state directly since get_state() returns old value during signal
        self._setup_dependencies(tracker_enabled_override=state)

    def _on_http_enabled_changed(self, switch: Any, state: Any) -> None:
        """Handle HTTP enable toggle"""
        self.logger.trace(
            f"HTTP enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        if self._widgets.get("http_port"):
            tracker_enabled = self._widgets.get("tracker_enabled") and self._widgets["tracker_enabled"].get_active()
            self._widgets["http_port"].set_sensitive(tracker_enabled and state)

    def _on_udp_enabled_changed(self, switch: Any, state: Any) -> None:
        """Handle UDP enable toggle"""
        self.logger.trace(
            f"UDP enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        if self._widgets.get("udp_port"):
            tracker_enabled = self._widgets.get("tracker_enabled") and self._widgets["tracker_enabled"].get_active()
            self._widgets["udp_port"].set_sensitive(tracker_enabled and state)

    def _on_self_tracking_changed(self, switch: Any, state: Any) -> None:
        """Handle self-tracking enable toggle"""
        self.logger.trace(
            f"Self-tracking enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        tracker_enabled = self._widgets.get("tracker_enabled") and self._widgets["tracker_enabled"].get_active()
        for widget_name in ["announce_with_seeders", "sync_on_add", "sync_on_remove"]:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(tracker_enabled and state)
