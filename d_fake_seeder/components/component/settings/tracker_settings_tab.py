"""
Tracker Settings Tab

Provides configuration interface for the inbuilt BitTorrent tracker.
Manages tracker server settings, self-tracking options, and security settings.
"""

from typing import Any, ClassVar

from d_fake_seeder.lib.gi_gtk4 import GLib

from .base_tab import BaseSettingsTab


class TrackerSettingsTab(BaseSettingsTab):
    """Tracker configuration tab"""

    # Note: Tracker settings use manual loading/saving due to nested structure
    WIDGET_MAPPINGS: ClassVar[list] = []

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

        self.logger.info(
            "Tracker tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

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

        self.logger.trace(
            "Tracker tab signals connected",
            extra={"class_name": self.__class__.__name__},
        )

    def _load_settings(self) -> None:
        """Load tracker settings from configuration."""
        try:
            self._load_toggle_settings()
            self._load_numeric_settings()
            self._load_address_settings()
            self.logger.trace(
                "Tracker settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(
                f"Failed to load tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _load_toggle_settings(self) -> None:
        """Load the on/off switch widgets."""
        toggles = [
            ("tracker_enabled", "tracker_settings.enabled", False),
            ("http_enabled", "tracker_settings.http_enabled", True),
            ("udp_enabled", "tracker_settings.udp_enabled", False),
            ("enable_scrape", "tracker_settings.enable_scrape", True),
            ("private_mode", "tracker_settings.private_mode", False),
            ("log_announces", "tracker_settings.log_announces", False),
            ("self_tracking_enabled", "tracker_settings.self_tracking.enabled", True),
            ("announce_with_seeders", "tracker_settings.self_tracking.announce_with_seeders", True),
            ("sync_on_add", "tracker_settings.self_tracking.sync_on_add", True),
            ("sync_on_remove", "tracker_settings.self_tracking.sync_on_remove", True),
        ]
        self.apply_widget_settings(toggles, "set_active")

    def _load_numeric_settings(self) -> None:
        """Load the spin-button widgets."""
        numerics = [
            ("http_port", "tracker_settings.http_port", 6969),
            ("udp_port", "tracker_settings.udp_port", 6969),
            ("announce_interval", "tracker_settings.announce_interval_seconds", 1800),
            ("peer_timeout_multiplier", "tracker_settings.peer_timeout_multiplier", 3),
            ("max_peers_per_announce", "tracker_settings.max_peers_per_announce", 50),
            ("rate_limit", "tracker_settings.security.rate_limit_per_minute", 60),
        ]
        self.apply_widget_settings(numerics, "set_value")

    def _load_address_settings(self) -> None:
        """Load the bind-address entry and the IP whitelist/blacklist buffers."""
        if self._widgets["bind_address"]:
            value = self.app_settings.get("tracker_settings.bind_address", "0.0.0.0")
            self._widgets["bind_address"].set_text(value)

        ip_lists = [
            ("ip_whitelist", "tracker_settings.security.ip_whitelist"),
            ("ip_blacklist", "tracker_settings.security.ip_blacklist"),
        ]
        for widget_id, key in ip_lists:
            if self._widgets[widget_id]:
                buffer = self._widgets[widget_id].get_buffer()
                buffer.set_text("\n".join(self.app_settings.get(key, [])))

    def _collect_settings(self) -> dict[str, Any]:
        """Collect current tracker settings from UI widgets."""
        settings: dict[str, Any] = {}

        try:
            self._collect_toggle_settings(settings)
            self._collect_numeric_settings(settings)
            self._collect_address_settings(settings)
            self.logger.trace(f"Collected {len(settings)} settings from Tracker tab")
            return settings
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(
                f"Failed to collect tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {}

    def _collect_toggle_settings(self, settings: dict[str, Any]) -> None:
        """Collect the on/off switch values into ``settings``."""
        toggles = [
            ("tracker_enabled", "tracker_settings.enabled"),
            ("http_enabled", "tracker_settings.http_enabled"),
            ("udp_enabled", "tracker_settings.udp_enabled"),
            ("enable_scrape", "tracker_settings.enable_scrape"),
            ("private_mode", "tracker_settings.private_mode"),
            ("log_announces", "tracker_settings.log_announces"),
            ("self_tracking_enabled", "tracker_settings.self_tracking.enabled"),
            ("announce_with_seeders", "tracker_settings.self_tracking.announce_with_seeders"),
            ("sync_on_add", "tracker_settings.self_tracking.sync_on_add"),
            ("sync_on_remove", "tracker_settings.self_tracking.sync_on_remove"),
        ]
        for widget_id, key in toggles:
            if self._widgets.get(widget_id):
                settings[key] = self._widgets[widget_id].get_active()

    def _collect_numeric_settings(self, settings: dict[str, Any]) -> None:
        """Collect the integer spin-button values into ``settings``."""
        numerics = [
            ("http_port", "tracker_settings.http_port"),
            ("udp_port", "tracker_settings.udp_port"),
            ("announce_interval", "tracker_settings.announce_interval_seconds"),
            ("peer_timeout_multiplier", "tracker_settings.peer_timeout_multiplier"),
            ("max_peers_per_announce", "tracker_settings.max_peers_per_announce"),
            ("rate_limit", "tracker_settings.security.rate_limit_per_minute"),
        ]
        for widget_id, key in numerics:
            if self._widgets.get(widget_id):
                settings[key] = int(self._widgets[widget_id].get_value())

    def _collect_address_settings(self, settings: dict[str, Any]) -> None:
        """Collect the bind address and IP whitelist/blacklist into ``settings``."""
        if self._widgets.get("bind_address"):
            settings["tracker_settings.bind_address"] = self._widgets["bind_address"].get_text().strip()

        ip_lists = [
            ("ip_whitelist", "tracker_settings.security.ip_whitelist"),
            ("ip_blacklist", "tracker_settings.security.ip_blacklist"),
        ]
        for widget_id, key in ip_lists:
            if self._widgets.get(widget_id):
                settings[key] = self._read_ip_lines(self._widgets[widget_id])

    @staticmethod
    def _read_ip_lines(widget: Any) -> list[str]:
        """Return the non-empty, stripped lines from a text-view widget."""
        buffer = widget.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, False)
        return [line.strip() for line in text.split("\n") if line.strip()]

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

        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(
                f"Failed to set up tracker dependencies: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _validate_tab_settings(self) -> dict[str, str]:
        """Validate tracker settings."""
        errors: dict[str, str] = {}

        try:
            self._validate_ports(errors)
            self._validate_announce_interval(errors)
            self._validate_ip_lists(errors)
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            errors["general"] = f"Validation error: {e}"
            self.logger.error(
                f"Tracker settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return errors

    def _validate_ports(self, errors: dict[str, str]) -> None:
        """Validate the HTTP and UDP port widgets."""
        ports = [("http_port", "HTTP port"), ("udp_port", "UDP port")]
        for widget_id, label in ports:
            if not self._widgets.get(widget_id):
                continue
            port = int(self._widgets[widget_id].get_value())
            if port < 1 or port > 65535:
                errors[widget_id] = f"{label} must be between 1 and 65535"
            elif port < 1024:
                errors[widget_id] = "Ports below 1024 require root privileges"

    def _validate_announce_interval(self, errors: dict[str, str]) -> None:
        """Validate the announce-interval widget."""
        if self._widgets.get("announce_interval"):
            interval = int(self._widgets["announce_interval"].get_value())
            if interval < 60:
                errors["announce_interval"] = "Announce interval should be at least 60 seconds"

    def _validate_ip_lists(self, errors: dict[str, str]) -> None:
        """Validate the whitelist/blacklist IP widgets."""
        for widget_id in ("ip_whitelist", "ip_blacklist"):
            if not self._widgets.get(widget_id):
                continue
            for line in self._read_ip_lines(self._widgets[widget_id]):
                if not self._is_valid_ipv4(line):
                    errors[widget_id] = f"Invalid IP format: {line}"
                    break

    @staticmethod
    def _is_valid_ipv4(line: str) -> bool:
        """Return whether ``line`` is a dotted-quad IPv4 address (0-255 per octet)."""
        parts = line.split(".")
        if len(parts) != 4:
            return False
        for part in parts:
            try:
                num = int(part)
            except ValueError:
                return False
            if num < 0 or num > 255:
                return False
        return True

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
