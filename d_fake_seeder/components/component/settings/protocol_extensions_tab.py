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

    # Note: Protocol Extensions settings use manual loading/saving with nested keys
    WIDGET_MAPPINGS: list = []

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Protocol Extensions"

    def _init_widgets(self) -> None:
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

        self.logger.trace(
            "Protocol Extensions tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _connect_signals(self) -> None:
        """Connect Protocol Extensions signals"""
        # Simple widgets (lt_donthave, fast_extension, ut_holepunch) are now auto-connected via WIDGET_MAPPINGS

        # Extension Protocol Enable/Disable (has dependencies - controls child widget sensitivity)
        if self._widgets["extensions_enabled"]:
            self._widgets["extensions_enabled"].connect("state-set", self._on_extensions_enabled_changed)

        # Individual Extension Toggles (have dependencies - control related widget sensitivity)
        if self._widgets["ut_metadata"]:
            self._widgets["ut_metadata"].connect("toggled", self._on_ut_metadata_toggled)

        if self._widgets["ut_pex"]:
            self._widgets["ut_pex"].connect("toggled", self._on_ut_pex_toggled)

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

        self.logger.trace(
            "Protocol Extensions tab signals connected",
            extra={"class_name": self.__class__.__name__},
        )

    def _load_settings(self) -> None:
        """Load Protocol Extensions settings from configuration (implements abstract method)."""
        self.load_settings()

    def _setup_dependencies(self) -> None:
        """Set up dependencies between UI elements (implements abstract method)."""
        try:
            # Set up initial state based on extensions_enabled
            if self._widgets.get("extensions_enabled"):
                enabled = self._widgets["extensions_enabled"].get_state()
                # Control ALL extension widgets based on extensions_enabled state
                extension_widgets = [
                    # Extension Protocol toggles
                    "ut_metadata",
                    "ut_pex",
                    "lt_donthave",
                    "fast_extension",
                    "ut_holepunch",
                    # PEX settings
                    "pex_interval",
                    "pex_max_peers",
                    "pex_max_dropped",
                    "pex_synthetic_peers",
                    "pex_synthetic_count",
                    # Metadata settings
                    "metadata_enabled",
                    "metadata_piece_size",
                    "metadata_timeout",
                    "metadata_synthetic",
                    # Transport protocol settings
                    "utp_enabled",
                    "tcp_fallback",
                    "connection_timeout",
                    "keep_alive_interval",
                    # Advanced extension settings
                    "nagle_algorithm",
                    "tcp_keepalive",
                    "extension_timeout",
                    "max_extension_msg_size",
                    # Extension statistics
                    "track_extension_stats",
                    "stats_update_interval",
                    # Security settings
                    "validate_extensions",
                    "limit_extension_msgs",
                    "max_msgs_per_second",
                ]
                for widget_name in extension_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(enabled)

            # Set up PEX-specific dependencies (only if extensions are enabled AND ut_pex is enabled)
            if self._widgets.get("ut_pex"):
                pex_enabled = self._widgets["ut_pex"].get_active()
                extensions_enabled = (
                    self._widgets.get("extensions_enabled") and self._widgets["extensions_enabled"].get_state()
                )
                pex_widgets = [
                    "pex_interval",
                    "pex_max_peers",
                    "pex_max_dropped",
                    "pex_synthetic_peers",
                    "pex_synthetic_count",
                ]
                for widget_name in pex_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(extensions_enabled and pex_enabled)

            # Set up metadata-specific dependencies (only if extensions are enabled AND ut_metadata is enabled)
            if self._widgets.get("ut_metadata"):
                metadata_enabled = self._widgets["ut_metadata"].get_active()
                extensions_enabled = (
                    self._widgets.get("extensions_enabled") and self._widgets["extensions_enabled"].get_state()
                )
                metadata_widgets = ["metadata_piece_size", "metadata_timeout", "metadata_synthetic"]
                for widget_name in metadata_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(extensions_enabled and metadata_enabled)

            # Set up PEX synthetic count dependency
            if self._widgets.get("pex_synthetic_peers") and self._widgets.get("pex_synthetic_count"):
                synthetic_enabled = self._widgets["pex_synthetic_peers"].get_active()
                pex_enabled = self._widgets.get("ut_pex") and self._widgets["ut_pex"].get_active()
                extensions_enabled = (
                    self._widgets.get("extensions_enabled") and self._widgets["extensions_enabled"].get_state()
                )
                self._widgets["pex_synthetic_count"].set_sensitive(
                    extensions_enabled and pex_enabled and synthetic_enabled
                )

        except Exception as e:
            self.logger.error(f"Error setting up Protocol Extensions dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Protocol Extensions tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: Dict[str, Any] = {}

        # Collect extension protocol settings
        for widget_name, setting_key in [
            ("ut_metadata", "protocols.extensions.ut_metadata"),
            ("ut_pex", "protocols.extensions.ut_pex"),
            ("lt_donthave", "protocols.extensions.lt_donthave"),
            ("fast_extension", "protocols.extensions.fast_extension"),
            ("ut_holepunch", "protocols.extensions.ut_holepunch"),
        ]:
            widget = self._widgets.get(widget_name)
            if widget:
                settings[setting_key] = widget.get_active()

        # Collect PEX settings
        for widget_name, setting_key, value_type in [
            ("pex_interval", "protocols.pex.interval", int),
            ("pex_max_peers", "protocols.pex.max_peers_per_message", int),
            ("pex_max_dropped", "protocols.pex.max_dropped_peers", int),
            ("pex_synthetic_peers", "protocols.pex.generate_synthetic_peers", bool),
            ("pex_synthetic_count", "protocols.pex.synthetic_peer_count", int),
        ]:
            widget = self._widgets.get(widget_name)
            if widget:
                if value_type == int:
                    settings[setting_key] = int(widget.get_value())
                else:
                    settings[setting_key] = widget.get_active()

        # Collect Transport settings
        for widget_name, setting_key, value_type in [
            ("utp_enabled", "protocols.transport.utp_enabled", bool),
            ("tcp_fallback", "protocols.transport.tcp_fallback", bool),
            ("connection_timeout", "protocols.transport.connection_timeout", int),
            ("keep_alive_interval", "protocols.transport.keep_alive_interval", int),
            ("nagle_algorithm", "protocols.transport.nagle_algorithm", bool),
            ("tcp_keepalive", "protocols.transport.tcp_keepalive", bool),
        ]:
            widget = self._widgets.get(widget_name)
            if widget:
                if value_type == int:
                    settings[setting_key] = int(widget.get_value())
                else:
                    settings[setting_key] = widget.get_active()

        # Collect Extended settings
        for widget_name, setting_key, value_type in [
            ("metadata_enabled", "protocols.extended.metadata_enabled", bool),
            ("metadata_piece_size", "protocols.extended.metadata_piece_size", int),
            ("metadata_timeout", "protocols.extended.metadata_timeout", int),
            ("metadata_synthetic", "protocols.extended.metadata_synthetic", bool),
            ("extension_timeout", "protocols.extended.extension_timeout", int),
            ("max_extension_msg_size", "protocols.extended.max_extension_msg_size", int),
            ("track_extension_stats", "protocols.extended.track_extension_stats", bool),
            ("stats_update_interval", "protocols.extended.stats_update_interval", int),
            ("validate_extensions", "protocols.extended.validate_extensions", bool),
            ("limit_extension_msgs", "protocols.extended.limit_extension_msgs", bool),
            ("max_msgs_per_second", "protocols.extended.max_msgs_per_second", int),
        ]:
            widget = self._widgets.get(widget_name)
            if widget:
                if value_type == int:
                    settings[setting_key] = int(widget.get_value())
                else:
                    settings[setting_key] = widget.get_active()

        self.logger.trace(f"Collected {len(settings)} settings from Protocol Extensions tab")
        return settings

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace(
            "Protocol Extensions tab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting

    def load_settings(self) -> None:
        """Load Protocol Extensions settings from configuration using nested keys."""
        try:
            # Extension Protocol Settings
            ut_metadata = self.app_settings.get("protocols.extensions.ut_metadata", True)
            ut_pex = self.app_settings.get("protocols.extensions.ut_pex", True)
            lt_donthave = self.app_settings.get("protocols.extensions.lt_donthave", True)
            fast_ext = self.app_settings.get("protocols.extensions.fast_extension", True)
            ut_holepunch = self.app_settings.get("protocols.extensions.ut_holepunch", False)

            # Overall extensions enabled (any extension is enabled)
            extensions_enabled = any([ut_metadata, ut_pex, lt_donthave, fast_ext, ut_holepunch])
            if self._widgets["extensions_enabled"]:
                self._widgets["extensions_enabled"].set_state(extensions_enabled)

            # Individual extensions
            if self._widgets["ut_metadata"]:
                self._widgets["ut_metadata"].set_active(ut_metadata)
            if self._widgets["ut_pex"]:
                self._widgets["ut_pex"].set_active(ut_pex)
            if self._widgets["lt_donthave"]:
                self._widgets["lt_donthave"].set_active(lt_donthave)
            if self._widgets["fast_extension"]:
                self._widgets["fast_extension"].set_active(fast_ext)
            if self._widgets["ut_holepunch"]:
                self._widgets["ut_holepunch"].set_active(ut_holepunch)

            # PEX Settings
            if self._widgets["pex_interval"]:
                value = self.app_settings.get("protocols.pex.interval", 60)
                self._widgets["pex_interval"].set_value(value)
            if self._widgets["pex_max_peers"]:
                value = self.app_settings.get("protocols.pex.max_peers_per_message", 50)
                self._widgets["pex_max_peers"].set_value(value)
            if self._widgets["pex_max_dropped"]:
                value = self.app_settings.get("protocols.pex.max_dropped_peers", 20)
                self._widgets["pex_max_dropped"].set_value(value)
            if self._widgets["pex_synthetic_peers"]:
                value = self.app_settings.get("protocols.pex.generate_synthetic_peers", True)
                self._widgets["pex_synthetic_peers"].set_active(value)
            if self._widgets["pex_synthetic_count"]:
                value = self.app_settings.get("protocols.pex.synthetic_peer_count", 20)
                self._widgets["pex_synthetic_count"].set_value(value)

            # Transport Settings
            if self._widgets["utp_enabled"]:
                value = self.app_settings.get("protocols.transport.utp_enabled", False)
                self._widgets["utp_enabled"].set_active(value)
            if self._widgets["tcp_fallback"]:
                value = self.app_settings.get("protocols.transport.tcp_fallback", True)
                self._widgets["tcp_fallback"].set_active(value)
            if self._widgets["connection_timeout"]:
                value = self.app_settings.get("protocols.transport.connection_timeout", 30)
                self._widgets["connection_timeout"].set_value(value)
            if self._widgets["keep_alive_interval"]:
                value = self.app_settings.get("protocols.transport.keep_alive_interval", 120)
                self._widgets["keep_alive_interval"].set_value(value)
            if self._widgets["nagle_algorithm"]:
                value = self.app_settings.get("protocols.transport.nagle_algorithm", False)
                self._widgets["nagle_algorithm"].set_active(value)
            if self._widgets["tcp_keepalive"]:
                value = self.app_settings.get("protocols.transport.tcp_keepalive", True)
                self._widgets["tcp_keepalive"].set_active(value)

            # Extended settings
            if self._widgets["metadata_enabled"]:
                value = self.app_settings.get("protocols.extended.metadata_enabled", True)
                self._widgets["metadata_enabled"].set_active(value)
            if self._widgets["metadata_piece_size"]:
                value = self.app_settings.get("protocols.extended.metadata_piece_size", 16384)
                self._widgets["metadata_piece_size"].set_value(value)
            if self._widgets["metadata_timeout"]:
                value = self.app_settings.get("protocols.extended.metadata_timeout", 60)
                self._widgets["metadata_timeout"].set_value(value)
            if self._widgets["metadata_synthetic"]:
                value = self.app_settings.get("protocols.extended.metadata_synthetic", True)
                self._widgets["metadata_synthetic"].set_active(value)
            if self._widgets["extension_timeout"]:
                value = self.app_settings.get("protocols.extended.extension_timeout", 30)
                self._widgets["extension_timeout"].set_value(value)
            if self._widgets["max_extension_msg_size"]:
                value = self.app_settings.get("protocols.extended.max_extension_msg_size", 1048576)
                self._widgets["max_extension_msg_size"].set_value(value)
            if self._widgets["track_extension_stats"]:
                value = self.app_settings.get("protocols.extended.track_extension_stats", True)
                self._widgets["track_extension_stats"].set_active(value)
            if self._widgets["stats_update_interval"]:
                value = self.app_settings.get("protocols.extended.stats_update_interval", 60)
                self._widgets["stats_update_interval"].set_value(value)
            if self._widgets["validate_extensions"]:
                value = self.app_settings.get("protocols.extended.validate_extensions", True)
                self._widgets["validate_extensions"].set_active(value)
            if self._widgets["limit_extension_msgs"]:
                value = self.app_settings.get("protocols.extended.limit_extension_msgs", True)
                self._widgets["limit_extension_msgs"].set_active(value)
            if self._widgets["max_msgs_per_second"]:
                value = self.app_settings.get("protocols.extended.max_msgs_per_second", 50)
                self._widgets["max_msgs_per_second"].set_value(value)

            self.logger.trace(
                "Protocol Extensions settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load Protocol Extensions settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    # Removed custom save_settings() - now using base class implementation with _collect_settings()

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Protocol Extensions settings. Returns dict of field_name -> error_message."""
        errors: Dict[str, str] = {}

        try:
            # Validate PEX interval
            if self._widgets.get("pex_interval"):
                interval = self._widgets["pex_interval"].get_value()
                if interval < 30:
                    errors["pex_interval"] = "PEX interval below 30 seconds may cause high network load"
                elif interval > 300:
                    errors["pex_interval"] = "PEX interval above 5 minutes may reduce peer discovery effectiveness"

            # Validate metadata piece size
            if self._widgets.get("metadata_piece_size"):
                piece_size = self._widgets["metadata_piece_size"].get_value()
                if piece_size < 1024 or piece_size > 65536:
                    errors["metadata_piece_size"] = "Metadata piece size must be between 1KB and 64KB"

            # Validate connection timeout
            if self._widgets.get("connection_timeout"):
                timeout = self._widgets["connection_timeout"].get_value()
                if timeout < 5:
                    errors["connection_timeout"] = "Connection timeout below 5 seconds may cause frequent timeouts"
                elif timeout > 120:
                    errors["connection_timeout"] = (
                        "Connection timeout above 2 minutes may cause slow connection establishment"
                    )

            # Validate extension message size
            if self._widgets.get("max_extension_msg_size"):
                max_size = self._widgets["max_extension_msg_size"].get_value()
                if max_size < 1024:
                    errors["max_extension_msg_size"] = "Maximum extension message size cannot be less than 1KB"
                elif max_size > 10485760:  # 10MB
                    errors["max_extension_msg_size"] = (
                        "Maximum extension message size above 10MB may cause memory issues"
                    )

            # Check for conflicting settings
            if (
                self._widgets.get("utp_enabled")
                and self._widgets["utp_enabled"].get_active()
                and self._widgets.get("tcp_fallback")
                and not self._widgets["tcp_fallback"].get_active()
            ):
                errors["tcp_fallback"] = "µTP enabled without TCP fallback may cause connection issues"

        except Exception as e:
            errors["general"] = f"Validation error: {str(e)}"
            self.logger.error(
                f"Protocol Extensions settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return errors

    # Signal handlers
    def _on_extensions_enabled_changed(self, switch: Any, state: Any) -> None:
        """Handle overall extensions enable/disable"""
        # NOTE: Setting will be saved in batch via _collect_settings()
        self.logger.trace(
            f"Extensions enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )

        # Enable/disable ALL extension-related widgets
        extension_widgets = [
            # Extension Protocol toggles
            "ut_metadata",
            "ut_pex",
            "lt_donthave",
            "fast_extension",
            "ut_holepunch",
            # PEX settings
            "pex_interval",
            "pex_max_peers",
            "pex_max_dropped",
            "pex_synthetic_peers",
            "pex_synthetic_count",
            # Metadata settings
            "metadata_enabled",
            "metadata_piece_size",
            "metadata_timeout",
            "metadata_synthetic",
            # Transport protocol settings
            "utp_enabled",
            "tcp_fallback",
            "connection_timeout",
            "keep_alive_interval",
            # Advanced extension settings
            "nagle_algorithm",
            "tcp_keepalive",
            "extension_timeout",
            "max_extension_msg_size",
            # Extension statistics
            "track_extension_stats",
            "stats_update_interval",
            # Security settings
            "validate_extensions",
            "limit_extension_msgs",
            "max_msgs_per_second",
        ]

        for widget_name in extension_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(state)

    def _on_ut_metadata_toggled(self, check_button: Any) -> None:
        """Handle ut_metadata toggle"""
        # NOTE: Setting will be saved in batch via _collect_settings()
        enabled = check_button.get_active()
        # Only enable metadata widgets if extensions are globally enabled
        extensions_enabled = self._widgets.get("extensions_enabled") and self._widgets["extensions_enabled"].get_state()
        # Enable/disable metadata-related widgets
        metadata_widgets = [
            "metadata_piece_size",
            "metadata_timeout",
            "metadata_synthetic",
        ]
        for widget_name in metadata_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(extensions_enabled and enabled)
        self.logger.trace(f"ut_metadata: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_ut_pex_toggled(self, check_button: Any) -> None:
        """Handle ut_pex toggle"""
        # NOTE: Setting will be saved in batch via _collect_settings()
        enabled = check_button.get_active()
        # Only enable PEX widgets if extensions are globally enabled
        extensions_enabled = self._widgets.get("extensions_enabled") and self._widgets["extensions_enabled"].get_state()
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
                self._widgets[widget_name].set_sensitive(extensions_enabled and enabled)
        self.logger.trace(f"ut_pex: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_pex_interval_changed(self, spin_button: Any) -> None:
        """Handle PEX interval changes"""
        interval = spin_button.get_value()
        self.logger.trace(f"PEX interval: {interval}", extra={"class_name": self.__class__.__name__})

    def _on_pex_max_peers_changed(self, spin_button: Any) -> None:
        """Handle PEX max peers changes"""
        max_peers = spin_button.get_value()
        self.logger.trace(f"PEX max peers: {max_peers}", extra={"class_name": self.__class__.__name__})

    def _on_pex_max_dropped_changed(self, spin_button: Any) -> None:
        """Handle PEX max dropped changes"""
        max_dropped = spin_button.get_value()
        self.logger.trace(
            f"PEX max dropped: {max_dropped}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_pex_synthetic_peers_toggled(self, check_button: Any) -> None:
        """Handle PEX synthetic peers toggle"""
        enabled = check_button.get_active()
        # Only enable synthetic count if extensions AND ut_pex AND synthetic_peers are all enabled
        extensions_enabled = self._widgets.get("extensions_enabled") and self._widgets["extensions_enabled"].get_state()
        pex_enabled = self._widgets.get("ut_pex") and self._widgets["ut_pex"].get_active()
        if self._widgets["pex_synthetic_count"]:
            self._widgets["pex_synthetic_count"].set_sensitive(extensions_enabled and pex_enabled and enabled)
        self.logger.trace(
            f"PEX synthetic peers: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_pex_synthetic_count_changed(self, spin_button: Any) -> None:
        """Handle PEX synthetic count changes"""
        count = spin_button.get_value()
        self.logger.trace(
            f"PEX synthetic count: {count}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_enabled_toggled(self, check_button: Any) -> None:
        """Handle metadata enabled toggle"""
        enabled = check_button.get_active()
        self.logger.trace(
            f"Metadata enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_piece_size_changed(self, spin_button: Any) -> None:
        """Handle metadata piece size changes"""
        size = spin_button.get_value()
        self.logger.trace(
            f"Metadata piece size: {size}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_timeout_changed(self, spin_button: Any) -> None:
        """Handle metadata timeout changes"""
        timeout = spin_button.get_value()
        self.logger.trace(
            f"Metadata timeout: {timeout}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_metadata_synthetic_toggled(self, check_button: Any) -> None:
        """Handle metadata synthetic toggle"""
        enabled = check_button.get_active()
        self.logger.trace(
            f"Metadata synthetic: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_utp_enabled_toggled(self, check_button: Any) -> None:
        """Handle µTP enabled toggle"""
        enabled = check_button.get_active()
        self.logger.trace(f"µTP enabled: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_tcp_fallback_toggled(self, check_button: Any) -> None:
        """Handle TCP fallback toggle"""
        enabled = check_button.get_active()
        self.logger.trace(f"TCP fallback: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_connection_timeout_changed(self, spin_button: Any) -> None:
        """Handle connection timeout changes"""
        timeout = spin_button.get_value()
        self.logger.trace(
            f"Connection timeout: {timeout}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_keep_alive_interval_changed(self, spin_button: Any) -> None:
        """Handle keep alive interval changes"""
        interval = spin_button.get_value()
        self.logger.trace(
            f"Keep alive interval: {interval}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_nagle_algorithm_toggled(self, check_button: Any) -> None:
        """Handle Nagle algorithm toggle"""
        enabled = check_button.get_active()
        self.logger.trace(f"Nagle algorithm: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_tcp_keepalive_toggled(self, check_button: Any) -> None:
        """Handle TCP keepalive toggle"""
        enabled = check_button.get_active()
        self.logger.trace(f"TCP keepalive: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_extension_timeout_changed(self, spin_button: Any) -> None:
        """Handle extension timeout changes"""
        timeout = spin_button.get_value()
        self.logger.trace(
            f"Extension timeout: {timeout}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_max_extension_msg_size_changed(self, spin_button: Any) -> None:
        """Handle max extension message size changes"""
        size = spin_button.get_value()
        self.logger.trace(
            f"Max extension message size: {size}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_track_extension_stats_toggled(self, check_button: Any) -> None:
        """Handle track extension stats toggle"""
        enabled = check_button.get_active()
        if self._widgets["stats_update_interval"]:
            self._widgets["stats_update_interval"].set_sensitive(enabled)
        self.logger.trace(
            f"Track extension stats: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_stats_update_interval_changed(self, spin_button: Any) -> None:
        """Handle stats update interval changes"""
        interval = spin_button.get_value()
        self.logger.trace(
            f"Stats update interval: {interval}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_validate_extensions_toggled(self, check_button: Any) -> None:
        """Handle validate extensions toggle"""
        enabled = check_button.get_active()
        self.logger.trace(
            f"Validate extensions: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_limit_extension_msgs_toggled(self, check_button: Any) -> None:
        """Handle limit extension messages toggle"""
        enabled = check_button.get_active()
        if self._widgets["max_msgs_per_second"]:
            self._widgets["max_msgs_per_second"].set_sensitive(enabled)
        self.logger.trace(
            f"Limit extension messages: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_max_msgs_per_second_changed(self, spin_button: Any) -> None:
        """Handle max messages per second changes"""
        max_msgs = spin_button.get_value()
        self.logger.trace(
            f"Max messages per second: {max_msgs}",
            extra={"class_name": self.__class__.__name__},
        )
