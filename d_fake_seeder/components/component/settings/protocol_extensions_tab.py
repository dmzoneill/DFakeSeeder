"""
Protocol Extensions Settings Tab

Provides configuration interface for BitTorrent protocol extensions including
Extension Protocol (BEP-010), Peer Exchange (PEX), Metadata Exchange, and other extensions.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")

from .base_tab import BaseSettingsTab  # noqa: E402

# fmt: on


class ProtocolExtensionsTab(BaseSettingsTab):
    """Protocol Extensions configuration tab"""

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Protocol Extensions"

    def _init_widgets(self):
        """Initialize Protocol Extensions widgets"""
        # Extension Protocol (BEP-010) Settings
        self._widgets["extensions_enabled"] = self.builder.get_object("extensions_enabled_switch")
        self._widgets["ut_metadata"] = self.builder.get_object("ut_metadata_check")
        self._widgets["ut_pex"] = self.builder.get_object("ut_pex_check")
        self._widgets["lt_donthave"] = self.builder.get_object("lt_donthave_check")
        self._widgets["fast_extension"] = self.builder.get_object("fast_extension_check")
        self._widgets["ut_holepunch"] = self.builder.get_object("ut_holepunch_check")

        # Peer Exchange (PEX) Settings
        self._widgets["pex_interval"] = self.builder.get_object("pex_interval_spin")
        self._widgets["pex_max_peers"] = self.builder.get_object("pex_max_peers_spin")
        self._widgets["pex_max_dropped"] = self.builder.get_object("pex_max_dropped_spin")
        self._widgets["pex_synthetic_peers"] = self.builder.get_object("pex_synthetic_peers_check")
        self._widgets["pex_synthetic_count"] = self.builder.get_object("pex_synthetic_count_spin")

        # Metadata Extension Settings
        self._widgets["metadata_enabled"] = self.builder.get_object("metadata_enabled_check")
        self._widgets["metadata_piece_size"] = self.builder.get_object("metadata_piece_size_spin")
        self._widgets["metadata_timeout"] = self.builder.get_object("metadata_timeout_spin")
        self._widgets["metadata_synthetic"] = self.builder.get_object("metadata_synthetic_check")

        # Transport Protocol Settings
        self._widgets["utp_enabled"] = self.builder.get_object("utp_enabled_check")
        self._widgets["tcp_fallback"] = self.builder.get_object("tcp_fallback_check")
        self._widgets["connection_timeout"] = self.builder.get_object("ext_connection_timeout_spin")
        self._widgets["keep_alive_interval"] = self.builder.get_object("ext_keep_alive_spin")

        # Advanced Extension Settings
        self._widgets["nagle_algorithm"] = self.builder.get_object("nagle_algorithm_check")
        self._widgets["tcp_keepalive"] = self.builder.get_object("tcp_keepalive_check")
        self._widgets["extension_timeout"] = self.builder.get_object("extension_timeout_spin")
        self._widgets["max_extension_msg_size"] = self.builder.get_object("max_extension_msg_size_spin")

        # Extension Statistics
        self._widgets["track_extension_stats"] = self.builder.get_object("track_extension_stats_check")
        self._widgets["stats_update_interval"] = self.builder.get_object("ext_stats_interval_spin")

        # Security Settings
        self._widgets["validate_extensions"] = self.builder.get_object("validate_extensions_check")
        self._widgets["limit_extension_msgs"] = self.builder.get_object("limit_extension_msgs_check")
        self._widgets["max_msgs_per_second"] = self.builder.get_object("max_ext_msgs_per_sec_spin")

        self.logger.debug(
            "Protocol Extensions tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _connect_signals(self):
        """Connect Protocol Extensions signals"""
        # Extension Protocol Enable/Disable
        if self._widgets["extensions_enabled"]:
            self._widgets["extensions_enabled"].connect("state-set", self._on_extensions_enabled_changed)

        # Individual Extension Toggles
        extension_toggles = [
            "ut_metadata",
            "ut_pex",
            "lt_donthave",
            "fast_extension",
            "ut_holepunch",
        ]
        for toggle in extension_toggles:
            if self._widgets[toggle]:
                self._widgets[toggle].connect("toggled", getattr(self, f"_on_{toggle}_toggled"))

        # PEX Settings
        if self._widgets["pex_interval"]:
            self._widgets["pex_interval"].connect("value-changed", self._on_pex_interval_changed)

        if self._widgets["pex_max_peers"]:
            self._widgets["pex_max_peers"].connect("value-changed", self._on_pex_max_peers_changed)

        if self._widgets["pex_max_dropped"]:
            self._widgets["pex_max_dropped"].connect("value-changed", self._on_pex_max_dropped_changed)

        if self._widgets["pex_synthetic_peers"]:
            self._widgets["pex_synthetic_peers"].connect("toggled", self._on_pex_synthetic_peers_toggled)

        if self._widgets["pex_synthetic_count"]:
            self._widgets["pex_synthetic_count"].connect("value-changed", self._on_pex_synthetic_count_changed)

        # Metadata Extension Settings
        if self._widgets["metadata_enabled"]:
            self._widgets["metadata_enabled"].connect("toggled", self._on_metadata_enabled_toggled)

        if self._widgets["metadata_piece_size"]:
            self._widgets["metadata_piece_size"].connect("value-changed", self._on_metadata_piece_size_changed)

        if self._widgets["metadata_timeout"]:
            self._widgets["metadata_timeout"].connect("value-changed", self._on_metadata_timeout_changed)

        if self._widgets["metadata_synthetic"]:
            self._widgets["metadata_synthetic"].connect("toggled", self._on_metadata_synthetic_toggled)

        # Transport Settings
        if self._widgets["utp_enabled"]:
            self._widgets["utp_enabled"].connect("toggled", self._on_utp_enabled_toggled)

        if self._widgets["tcp_fallback"]:
            self._widgets["tcp_fallback"].connect("toggled", self._on_tcp_fallback_toggled)

        if self._widgets["connection_timeout"]:
            self._widgets["connection_timeout"].connect("value-changed", self._on_connection_timeout_changed)

        if self._widgets["keep_alive_interval"]:
            self._widgets["keep_alive_interval"].connect("value-changed", self._on_keep_alive_interval_changed)

        # Advanced Settings
        if self._widgets["nagle_algorithm"]:
            self._widgets["nagle_algorithm"].connect("toggled", self._on_nagle_algorithm_toggled)

        if self._widgets["tcp_keepalive"]:
            self._widgets["tcp_keepalive"].connect("toggled", self._on_tcp_keepalive_toggled)

        if self._widgets["extension_timeout"]:
            self._widgets["extension_timeout"].connect("value-changed", self._on_extension_timeout_changed)

        if self._widgets["max_extension_msg_size"]:
            self._widgets["max_extension_msg_size"].connect("value-changed", self._on_max_extension_msg_size_changed)

        # Statistics Settings
        if self._widgets["track_extension_stats"]:
            self._widgets["track_extension_stats"].connect("toggled", self._on_track_extension_stats_toggled)

        if self._widgets["stats_update_interval"]:
            self._widgets["stats_update_interval"].connect("value-changed", self._on_stats_update_interval_changed)

        # Security Settings
        if self._widgets["validate_extensions"]:
            self._widgets["validate_extensions"].connect("toggled", self._on_validate_extensions_toggled)

        if self._widgets["limit_extension_msgs"]:
            self._widgets["limit_extension_msgs"].connect("toggled", self._on_limit_extension_msgs_toggled)

        if self._widgets["max_msgs_per_second"]:
            self._widgets["max_msgs_per_second"].connect("value-changed", self._on_max_msgs_per_second_changed)

        self.logger.debug(
            "Protocol Extensions tab signals connected",
            extra={"class_name": self.__class__.__name__},
        )

    def _load_settings(self) -> None:
        """Load Protocol Extensions settings from configuration (implements abstract method)."""
        self.load_settings()

    def _setup_dependencies(self) -> None:
        """Set up dependencies between UI elements (implements abstract method)."""
        # No complex dependencies in this tab
        pass

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from UI widgets (implements abstract method)."""
        # Return empty dict - save_settings() method handles the actual saving
        return {}

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.debug(
            "Protocol Extensions tab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.debug(
            "Protocol Extensions tab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "Protocol Extensions tab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "Protocol Extensions tab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def load_settings(self):
        """Load Protocol Extensions settings from configuration"""
        try:
            protocols_config = getattr(self.app_settings, "protocols", {})

            # Extension Protocol Settings
            extensions_config = protocols_config.get("extensions", {})

            # Overall extensions enabled
            extensions_enabled = any(extensions_config.values()) if extensions_config else True
            if self._widgets["extensions_enabled"]:
                self._widgets["extensions_enabled"].set_state(extensions_enabled)

            # Individual extensions
            if self._widgets["ut_metadata"]:
                self._widgets["ut_metadata"].set_active(extensions_config.get("ut_metadata", True))

            if self._widgets["ut_pex"]:
                self._widgets["ut_pex"].set_active(extensions_config.get("ut_pex", True))

            if self._widgets["lt_donthave"]:
                self._widgets["lt_donthave"].set_active(extensions_config.get("lt_donthave", True))

            if self._widgets["fast_extension"]:
                self._widgets["fast_extension"].set_active(extensions_config.get("fast_extension", True))

            if self._widgets["ut_holepunch"]:
                self._widgets["ut_holepunch"].set_active(extensions_config.get("ut_holepunch", False))

            # PEX Settings
            pex_config = protocols_config.get("pex", {})

            if self._widgets["pex_interval"]:
                self._widgets["pex_interval"].set_value(pex_config.get("interval", 60))

            if self._widgets["pex_max_peers"]:
                self._widgets["pex_max_peers"].set_value(pex_config.get("max_peers_per_message", 50))

            if self._widgets["pex_max_dropped"]:
                self._widgets["pex_max_dropped"].set_value(pex_config.get("max_dropped_peers", 20))

            if self._widgets["pex_synthetic_peers"]:
                self._widgets["pex_synthetic_peers"].set_active(pex_config.get("generate_synthetic_peers", True))

            if self._widgets["pex_synthetic_count"]:
                self._widgets["pex_synthetic_count"].set_value(pex_config.get("synthetic_peer_count", 20))

            # Transport Settings
            transport_config = protocols_config.get("transport", {})

            if self._widgets["utp_enabled"]:
                self._widgets["utp_enabled"].set_active(transport_config.get("utp_enabled", False))

            if self._widgets["tcp_fallback"]:
                self._widgets["tcp_fallback"].set_active(transport_config.get("tcp_fallback", True))

            if self._widgets["connection_timeout"]:
                self._widgets["connection_timeout"].set_value(transport_config.get("connection_timeout", 30))

            if self._widgets["keep_alive_interval"]:
                self._widgets["keep_alive_interval"].set_value(transport_config.get("keep_alive_interval", 120))

            if self._widgets["nagle_algorithm"]:
                self._widgets["nagle_algorithm"].set_active(transport_config.get("nagle_algorithm", False))

            if self._widgets["tcp_keepalive"]:
                self._widgets["tcp_keepalive"].set_active(transport_config.get("tcp_keepalive", True))

            # Extended settings
            extended_config = protocols_config.get("extended", {})

            if self._widgets["metadata_enabled"]:
                self._widgets["metadata_enabled"].set_active(extended_config.get("metadata_enabled", True))

            if self._widgets["metadata_piece_size"]:
                self._widgets["metadata_piece_size"].set_value(extended_config.get("metadata_piece_size", 16384))

            if self._widgets["metadata_timeout"]:
                self._widgets["metadata_timeout"].set_value(extended_config.get("metadata_timeout", 60))

            if self._widgets["metadata_synthetic"]:
                self._widgets["metadata_synthetic"].set_active(extended_config.get("metadata_synthetic", True))

            if self._widgets["extension_timeout"]:
                self._widgets["extension_timeout"].set_value(extended_config.get("extension_timeout", 30))

            if self._widgets["max_extension_msg_size"]:
                self._widgets["max_extension_msg_size"].set_value(
                    extended_config.get("max_extension_msg_size", 1048576)
                )

            if self._widgets["track_extension_stats"]:
                self._widgets["track_extension_stats"].set_active(extended_config.get("track_extension_stats", True))

            if self._widgets["stats_update_interval"]:
                self._widgets["stats_update_interval"].set_value(extended_config.get("stats_update_interval", 60))

            if self._widgets["validate_extensions"]:
                self._widgets["validate_extensions"].set_active(extended_config.get("validate_extensions", True))

            if self._widgets["limit_extension_msgs"]:
                self._widgets["limit_extension_msgs"].set_active(extended_config.get("limit_extension_msgs", True))

            if self._widgets["max_msgs_per_second"]:
                self._widgets["max_msgs_per_second"].set_value(extended_config.get("max_msgs_per_second", 50))

            self.logger.debug(
                "Protocol Extensions settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load Protocol Extensions settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def save_settings(self):
        """Save Protocol Extensions settings to configuration"""
        try:
            # Get current protocols config
            protocols_config = getattr(self.app_settings, "protocols", {})

            # Extension Protocol Settings
            extensions_config = protocols_config.setdefault("extensions", {})

            if self._widgets["ut_metadata"]:
                extensions_config["ut_metadata"] = self._widgets["ut_metadata"].get_active()

            if self._widgets["ut_pex"]:
                extensions_config["ut_pex"] = self._widgets["ut_pex"].get_active()

            if self._widgets["lt_donthave"]:
                extensions_config["lt_donthave"] = self._widgets["lt_donthave"].get_active()

            if self._widgets["fast_extension"]:
                extensions_config["fast_extension"] = self._widgets["fast_extension"].get_active()

            if self._widgets["ut_holepunch"]:
                extensions_config["ut_holepunch"] = self._widgets["ut_holepunch"].get_active()

            # PEX Settings
            pex_config = protocols_config.setdefault("pex", {})

            if self._widgets["pex_interval"]:
                pex_config["interval"] = int(self._widgets["pex_interval"].get_value())

            if self._widgets["pex_max_peers"]:
                pex_config["max_peers_per_message"] = int(self._widgets["pex_max_peers"].get_value())

            if self._widgets["pex_max_dropped"]:
                pex_config["max_dropped_peers"] = int(self._widgets["pex_max_dropped"].get_value())

            if self._widgets["pex_synthetic_peers"]:
                pex_config["generate_synthetic_peers"] = self._widgets["pex_synthetic_peers"].get_active()

            if self._widgets["pex_synthetic_count"]:
                pex_config["synthetic_peer_count"] = int(self._widgets["pex_synthetic_count"].get_value())

            # Transport Settings
            transport_config = protocols_config.setdefault("transport", {})

            if self._widgets["utp_enabled"]:
                transport_config["utp_enabled"] = self._widgets["utp_enabled"].get_active()

            if self._widgets["tcp_fallback"]:
                transport_config["tcp_fallback"] = self._widgets["tcp_fallback"].get_active()

            if self._widgets["connection_timeout"]:
                transport_config["connection_timeout"] = int(self._widgets["connection_timeout"].get_value())

            if self._widgets["keep_alive_interval"]:
                transport_config["keep_alive_interval"] = int(self._widgets["keep_alive_interval"].get_value())

            if self._widgets["nagle_algorithm"]:
                transport_config["nagle_algorithm"] = self._widgets["nagle_algorithm"].get_active()

            if self._widgets["tcp_keepalive"]:
                transport_config["tcp_keepalive"] = self._widgets["tcp_keepalive"].get_active()

            # Extended Settings
            extended_config = protocols_config.setdefault("extended", {})

            if self._widgets["metadata_enabled"]:
                extended_config["metadata_enabled"] = self._widgets["metadata_enabled"].get_active()

            if self._widgets["metadata_piece_size"]:
                extended_config["metadata_piece_size"] = int(self._widgets["metadata_piece_size"].get_value())

            if self._widgets["metadata_timeout"]:
                extended_config["metadata_timeout"] = int(self._widgets["metadata_timeout"].get_value())

            if self._widgets["metadata_synthetic"]:
                extended_config["metadata_synthetic"] = self._widgets["metadata_synthetic"].get_active()

            if self._widgets["extension_timeout"]:
                extended_config["extension_timeout"] = int(self._widgets["extension_timeout"].get_value())

            if self._widgets["max_extension_msg_size"]:
                extended_config["max_extension_msg_size"] = int(self._widgets["max_extension_msg_size"].get_value())

            if self._widgets["track_extension_stats"]:
                extended_config["track_extension_stats"] = self._widgets["track_extension_stats"].get_active()

            if self._widgets["stats_update_interval"]:
                extended_config["stats_update_interval"] = int(self._widgets["stats_update_interval"].get_value())

            if self._widgets["validate_extensions"]:
                extended_config["validate_extensions"] = self._widgets["validate_extensions"].get_active()

            if self._widgets["limit_extension_msgs"]:
                extended_config["limit_extension_msgs"] = self._widgets["limit_extension_msgs"].get_active()

            if self._widgets["max_msgs_per_second"]:
                extended_config["max_msgs_per_second"] = int(self._widgets["max_msgs_per_second"].get_value())

            # Save back to settings
            self.app_settings.set("protocols", protocols_config)

            self.logger.debug(
                "Protocol Extensions settings saved successfully",
                extra={"class_name": self.__class__.__name__},
            )

            # Return the settings dict (required by base class)
            return {"protocols": protocols_config}

        except Exception as e:
            self.logger.error(
                f"Failed to save Protocol Extensions settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {}

    def validate_settings(self) -> Dict[str, Any]:
        """Validate Protocol Extensions settings"""
        validation_result: Dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        try:
            # Validate PEX interval
            if self._widgets["pex_interval"]:
                interval = self._widgets["pex_interval"].get_value()
                if interval < 30:
                    validation_result["warnings"].append("PEX interval below 30 seconds may cause high network load")
                elif interval > 300:
                    validation_result["warnings"].append(
                        "PEX interval above 5 minutes may reduce peer discovery effectiveness"
                    )

            # Validate metadata piece size
            if self._widgets["metadata_piece_size"]:
                piece_size = self._widgets["metadata_piece_size"].get_value()
                if piece_size < 1024 or piece_size > 65536:
                    validation_result["errors"].append("Metadata piece size must be between 1KB and 64KB")
                    validation_result["valid"] = False

            # Validate connection timeout
            if self._widgets["connection_timeout"]:
                timeout = self._widgets["connection_timeout"].get_value()
                if timeout < 5:
                    validation_result["warnings"].append(
                        "Connection timeout below 5 seconds may cause frequent timeouts"
                    )
                elif timeout > 120:
                    validation_result["warnings"].append(
                        "Connection timeout above 2 minutes may cause slow connection establishment"
                    )

            # Validate extension message size
            if self._widgets["max_extension_msg_size"]:
                max_size = self._widgets["max_extension_msg_size"].get_value()
                if max_size < 1024:
                    validation_result["errors"].append("Maximum extension message size cannot be less than 1KB")
                    validation_result["valid"] = False
                elif max_size > 10485760:  # 10MB
                    validation_result["warnings"].append(
                        "Maximum extension message size above 10MB may cause memory issues"
                    )

            # Check for conflicting settings
            if (
                self._widgets["utp_enabled"]
                and self._widgets["utp_enabled"].get_active()
                and self._widgets["tcp_fallback"]
                and not self._widgets["tcp_fallback"].get_active()
            ):
                validation_result["warnings"].append("µTP enabled without TCP fallback may cause connection issues")

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
            self.logger.error(
                f"Protocol Extensions settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return validation_result

    # Signal handlers
    def _on_extensions_enabled_changed(self, switch, state):
        """Handle overall extensions enable/disable"""
        self.logger.debug(
            f"Extensions enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )

        # Enable/disable all extension-related widgets
        extension_widgets = [
            "ut_metadata",
            "ut_pex",
            "lt_donthave",
            "fast_extension",
            "ut_holepunch",
            "pex_interval",
            "pex_max_peers",
            "metadata_enabled",
        ]

        for widget_name in extension_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(state)

    def _on_ut_metadata_toggled(self, check_button):
        """Handle ut_metadata toggle"""
        enabled = check_button.get_active()
        # Enable/disable metadata-related widgets
        metadata_widgets = [
            "metadata_piece_size",
            "metadata_timeout",
            "metadata_synthetic",
        ]
        for widget_name in metadata_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(enabled)
        self.logger.debug(f"ut_metadata: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_ut_pex_toggled(self, check_button):
        """Handle ut_pex toggle"""
        enabled = check_button.get_active()
        # Enable/disable PEX-related widgets
        pex_widgets = [
            "pex_interval",
            "pex_max_peers",
            "pex_max_dropped",
            "pex_synthetic_peers",
            "pex_synthetic_count",
        ]
        for widget_name in pex_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(enabled)
        self.logger.debug(f"ut_pex: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_lt_donthave_toggled(self, check_button):
        """Handle lt_donthave toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"lt_donthave: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_fast_extension_toggled(self, check_button):
        """Handle fast_extension toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"fast_extension: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_ut_holepunch_toggled(self, check_button):
        """Handle ut_holepunch toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"ut_holepunch: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_pex_interval_changed(self, spin_button):
        """Handle PEX interval changes"""
        interval = spin_button.get_value()
        self.logger.debug(f"PEX interval: {interval}", extra={"class_name": self.__class__.__name__})

    def _on_pex_max_peers_changed(self, spin_button):
        """Handle PEX max peers changes"""
        max_peers = spin_button.get_value()
        self.logger.debug(f"PEX max peers: {max_peers}", extra={"class_name": self.__class__.__name__})

    def _on_pex_max_dropped_changed(self, spin_button):
        """Handle PEX max dropped changes"""
        max_dropped = spin_button.get_value()
        self.logger.debug(
            f"PEX max dropped: {max_dropped}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_pex_synthetic_peers_toggled(self, check_button):
        """Handle PEX synthetic peers toggle"""
        enabled = check_button.get_active()
        if self._widgets["pex_synthetic_count"]:
            self._widgets["pex_synthetic_count"].set_sensitive(enabled)
        self.logger.debug(
            f"PEX synthetic peers: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_pex_synthetic_count_changed(self, spin_button):
        """Handle PEX synthetic count changes"""
        count = spin_button.get_value()
        self.logger.debug(
            f"PEX synthetic count: {count}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_enabled_toggled(self, check_button):
        """Handle metadata enabled toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Metadata enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_piece_size_changed(self, spin_button):
        """Handle metadata piece size changes"""
        size = spin_button.get_value()
        self.logger.debug(
            f"Metadata piece size: {size}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_timeout_changed(self, spin_button):
        """Handle metadata timeout changes"""
        timeout = spin_button.get_value()
        self.logger.debug(
            f"Metadata timeout: {timeout}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_synthetic_toggled(self, check_button):
        """Handle metadata synthetic toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Metadata synthetic: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_utp_enabled_toggled(self, check_button):
        """Handle µTP enabled toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"µTP enabled: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_tcp_fallback_toggled(self, check_button):
        """Handle TCP fallback toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"TCP fallback: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_connection_timeout_changed(self, spin_button):
        """Handle connection timeout changes"""
        timeout = spin_button.get_value()
        self.logger.debug(
            f"Connection timeout: {timeout}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_keep_alive_interval_changed(self, spin_button):
        """Handle keep alive interval changes"""
        interval = spin_button.get_value()
        self.logger.debug(
            f"Keep alive interval: {interval}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_nagle_algorithm_toggled(self, check_button):
        """Handle Nagle algorithm toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"Nagle algorithm: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_tcp_keepalive_toggled(self, check_button):
        """Handle TCP keepalive toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"TCP keepalive: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_extension_timeout_changed(self, spin_button):
        """Handle extension timeout changes"""
        timeout = spin_button.get_value()
        self.logger.debug(
            f"Extension timeout: {timeout}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_max_extension_msg_size_changed(self, spin_button):
        """Handle max extension message size changes"""
        size = spin_button.get_value()
        self.logger.debug(
            f"Max extension message size: {size}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_track_extension_stats_toggled(self, check_button):
        """Handle track extension stats toggle"""
        enabled = check_button.get_active()
        if self._widgets["stats_update_interval"]:
            self._widgets["stats_update_interval"].set_sensitive(enabled)
        self.logger.debug(
            f"Track extension stats: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_stats_update_interval_changed(self, spin_button):
        """Handle stats update interval changes"""
        interval = spin_button.get_value()
        self.logger.debug(
            f"Stats update interval: {interval}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_validate_extensions_toggled(self, check_button):
        """Handle validate extensions toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Validate extensions: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_limit_extension_msgs_toggled(self, check_button):
        """Handle limit extension messages toggle"""
        enabled = check_button.get_active()
        if self._widgets["max_msgs_per_second"]:
            self._widgets["max_msgs_per_second"].set_sensitive(enabled)
        self.logger.debug(
            f"Limit extension messages: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_max_msgs_per_second_changed(self, spin_button):
        """Handle max messages per second changes"""
        max_msgs = spin_button.get_value()
        self.logger.debug(
            f"Max messages per second: {max_msgs}",
            extra={"class_name": self.__class__.__name__},
        )
