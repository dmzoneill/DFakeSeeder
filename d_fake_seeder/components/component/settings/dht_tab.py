"""
DHT Settings Tab

Provides configuration interface for DHT (Distributed Hash Table) settings.
Manages DHT node configuration, bootstrap settings, and trackerless operation parameters.
"""

from typing import Any, ClassVar

from d_fake_seeder.lib.gi_gtk4 import GLib

from .base_tab import BaseSettingsTab


class DHTTab(BaseSettingsTab):
    """DHT configuration tab"""

    # Note: DHT settings use manual loading/saving due to nested structure (protocols.dht.*)
    WIDGET_MAPPINGS: ClassVar[list] = []

    @property
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        return "DHT"

    def _init_widgets(self) -> None:
        """Initialize DHT-specific widgets"""
        # DHT Enable/Disable
        self._widgets["dht_enabled"] = self.builder.get_object("dht_enabled_switch")

        # DHT Node Configuration
        self._widgets["node_id_auto"] = self.builder.get_object("node_id_auto_check")
        self._widgets["node_id_custom"] = self.builder.get_object("node_id_custom_entry")
        self._widgets["routing_table_size"] = self.builder.get_object("routing_table_size_spin")

        # DHT Timing Settings
        self._widgets["announcement_interval"] = self.builder.get_object("dht_announcement_interval_spin")
        self._widgets["bootstrap_timeout"] = self.builder.get_object("bootstrap_timeout_spin")
        self._widgets["query_timeout"] = self.builder.get_object("dht_query_timeout_spin")

        # DHT Network Settings
        self._widgets["max_nodes"] = self.builder.get_object("dht_max_nodes_spin")
        self._widgets["bucket_size"] = self.builder.get_object("dht_bucket_size_spin")
        self._widgets["concurrent_queries"] = self.builder.get_object("dht_concurrent_queries_spin")

        # Bootstrap Nodes
        self._widgets["bootstrap_nodes"] = self.builder.get_object("bootstrap_nodes_textview")
        self._widgets["auto_bootstrap"] = self.builder.get_object("auto_bootstrap_check")

        # DHT Statistics and Monitoring
        self._widgets["enable_stats"] = self.builder.get_object("dht_enable_stats_check")
        self._widgets["stats_interval"] = self.builder.get_object("dht_stats_interval_spin")

        # DHT Security Settings
        self._widgets["validate_tokens"] = self.builder.get_object("dht_validate_tokens_check")
        self._widgets["rate_limit_enabled"] = self.builder.get_object("dht_rate_limit_check")
        self._widgets["max_queries_per_second"] = self.builder.get_object("dht_max_queries_spin")

        self.logger.info("DHT tab widgets initialized", extra={"class_name": self.__class__.__name__})

    def _connect_signals(self) -> None:
        """Connect DHT-specific signals"""
        # Simple widgets (node_id_custom, announcement_interval, bootstrap_timeout, query_timeout,
        # routing_table_size, max_nodes, bucket_size, concurrent_queries, auto_bootstrap,
        # stats_interval, validate_tokens, max_queries_per_second) are now auto-connected via WIDGET_MAPPINGS

        # Enable/Disable DHT (has dependencies - controls sensitivity of child widgets)
        if self._widgets["dht_enabled"]:
            self._widgets["dht_enabled"].connect("state-set", self._on_dht_enabled_changed)

        # Node ID configuration (has dependencies - controls node_id_custom sensitivity)
        if self._widgets["node_id_auto"]:
            self._widgets["node_id_auto"].connect("toggled", self._on_node_id_auto_toggled)

        # Statistics settings (has dependencies - controls stats_interval sensitivity)
        if self._widgets["enable_stats"]:
            self._widgets["enable_stats"].connect("toggled", self._on_enable_stats_toggled)

        # Security settings (has dependencies - controls max_queries_per_second sensitivity)
        if self._widgets["rate_limit_enabled"]:
            self._widgets["rate_limit_enabled"].connect("toggled", self._on_rate_limit_toggled)

        self.logger.trace("DHT tab signals connected", extra={"class_name": self.__class__.__name__})

    def _load_settings(self) -> None:
        """Load DHT settings from configuration using nested keys."""
        try:
            self._load_toggle_settings()
            self._load_numeric_settings()
            self._load_node_and_bootstrap()
            self.logger.trace(
                "DHT settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(
                f"Failed to load DHT settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _load_toggle_settings(self) -> None:
        """Load the on/off switch widgets."""
        toggles = [
            ("dht_enabled", "protocols.dht.enabled", True),
            ("auto_bootstrap", "protocols.dht.auto_bootstrap", True),
            ("enable_stats", "protocols.dht.enable_stats", True),
            ("validate_tokens", "protocols.dht.validate_tokens", True),
            ("rate_limit_enabled", "protocols.dht.rate_limit_enabled", True),
        ]
        self.apply_widget_settings(toggles, "set_active")

    def _load_numeric_settings(self) -> None:
        """Load the spin-button widgets."""
        numerics = [
            ("routing_table_size", "protocols.dht.routing_table_size", 160),
            ("announcement_interval", "protocols.dht.announcement_interval", 1800),
            ("bootstrap_timeout", "protocols.dht.bootstrap_timeout", 30),
            ("query_timeout", "protocols.dht.query_timeout", 10),
            ("max_nodes", "protocols.dht.max_nodes", 1000),
            ("bucket_size", "protocols.dht.bucket_size", 8),
            ("concurrent_queries", "protocols.dht.concurrent_queries", 3),
            ("stats_interval", "protocols.dht.stats_interval", 60),
            ("max_queries_per_second", "protocols.dht.max_queries_per_second", 10),
        ]
        self.apply_widget_settings(numerics, "set_value")

    def _load_node_and_bootstrap(self) -> None:
        """Load the node-id controls and the bootstrap-nodes buffer."""
        node_id_setting = self.app_settings.get("protocols.dht.node_id", "auto_generate")
        is_auto = node_id_setting == "auto_generate"
        if self._widgets["node_id_auto"]:
            self._widgets["node_id_auto"].set_active(is_auto)
        if self._widgets["node_id_custom"]:
            if not is_auto:
                self._widgets["node_id_custom"].set_text(str(node_id_setting))
            self._widgets["node_id_custom"].set_sensitive(not is_auto)

        if self._widgets["bootstrap_nodes"]:
            buffer = self._widgets["bootstrap_nodes"].get_buffer()
            bootstrap_list = self.app_settings.get(
                "protocols.dht.bootstrap_nodes",
                [
                    "router.bittorrent.com:6881",
                    "dht.transmissionbt.com:6881",
                    "router.utorrent.com:6881",
                ],
            )
            buffer.set_text("\n".join(bootstrap_list))

    def _collect_settings(self) -> dict[str, Any]:
        """Collect current DHT settings from UI widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: dict[str, Any] = {}

        try:
            self._collect_toggle_settings(settings)
            self._collect_numeric_settings(settings)
            self._collect_node_and_bootstrap(settings)
            self.logger.trace(f"Collected {len(settings)} settings from DHT tab")
            return settings
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(
                f"Failed to collect DHT settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {}

    def _collect_toggle_settings(self, settings: dict[str, Any]) -> None:
        """Collect the on/off switch values into ``settings``."""
        toggles = [
            ("dht_enabled", "protocols.dht.enabled"),
            ("auto_bootstrap", "protocols.dht.auto_bootstrap"),
            ("enable_stats", "protocols.dht.enable_stats"),
            ("validate_tokens", "protocols.dht.validate_tokens"),
            ("rate_limit_enabled", "protocols.dht.rate_limit_enabled"),
        ]
        for widget_id, key in toggles:
            if self._widgets.get(widget_id):
                settings[key] = self._widgets[widget_id].get_active()

    def _collect_numeric_settings(self, settings: dict[str, Any]) -> None:
        """Collect the integer spin-button values into ``settings``."""
        numerics = [
            ("routing_table_size", "protocols.dht.routing_table_size"),
            ("announcement_interval", "protocols.dht.announcement_interval"),
            ("bootstrap_timeout", "protocols.dht.bootstrap_timeout"),
            ("query_timeout", "protocols.dht.query_timeout"),
            ("max_nodes", "protocols.dht.max_nodes"),
            ("bucket_size", "protocols.dht.bucket_size"),
            ("concurrent_queries", "protocols.dht.concurrent_queries"),
            ("stats_interval", "protocols.dht.stats_interval"),
            ("max_queries_per_second", "protocols.dht.max_queries_per_second"),
        ]
        for widget_id, key in numerics:
            if self._widgets.get(widget_id):
                settings[key] = int(self._widgets[widget_id].get_value())

    def _collect_node_and_bootstrap(self, settings: dict[str, Any]) -> None:
        """Collect the node-id choice and the bootstrap-nodes list into ``settings``."""
        if self._widgets.get("node_id_auto") and self._widgets["node_id_auto"].get_active():
            settings["protocols.dht.node_id"] = "auto_generate"
        elif self._widgets.get("node_id_custom"):
            custom_id = self._widgets["node_id_custom"].get_text().strip()
            if custom_id:
                settings["protocols.dht.node_id"] = custom_id

        if self._widgets.get("bootstrap_nodes"):
            settings["protocols.dht.bootstrap_nodes"] = self._read_text_lines(self._widgets["bootstrap_nodes"])

    @staticmethod
    def _read_text_lines(widget: Any) -> list[str]:
        """Return the non-empty, stripped lines from a text-view widget."""
        buffer = widget.get_buffer()
        start, end = buffer.get_bounds()
        text = buffer.get_text(start, end, False)
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _setup_dependencies(self) -> None:
        """Set up dependencies between UI elements"""
        # Initial dependency state based on current settings
        try:
            if self._widgets.get("dht_enabled"):
                state = self._widgets["dht_enabled"].get_active()
                # Control ALL DHT widgets based on dht_enabled state
                sensitive_widgets = [
                    # Node configuration
                    "node_id_auto",
                    "node_id_custom",
                    "routing_table_size",
                    # Timing settings
                    "announcement_interval",
                    "bootstrap_timeout",
                    "query_timeout",
                    # Network settings
                    "max_nodes",
                    "bucket_size",
                    "concurrent_queries",
                    # Bootstrap settings
                    "bootstrap_nodes",
                    "auto_bootstrap",
                    # Statistics settings
                    "enable_stats",
                    "stats_interval",
                    # Security settings
                    "validate_tokens",
                    "rate_limit_enabled",
                    "max_queries_per_second",
                ]
                for widget_name in sensitive_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(state)

            # Node ID custom field sensitivity (only if DHT is enabled)
            if self._widgets.get("node_id_auto") and self._widgets.get("node_id_custom"):
                auto_enabled = self._widgets["node_id_auto"].get_active()
                dht_enabled = self._widgets.get("dht_enabled") and self._widgets["dht_enabled"].get_active()
                self._widgets["node_id_custom"].set_sensitive(dht_enabled and not auto_enabled)

            # Stats interval sensitivity (only if DHT is enabled)
            if self._widgets.get("enable_stats") and self._widgets.get("stats_interval"):
                stats_enabled = self._widgets["enable_stats"].get_active()
                dht_enabled = self._widgets.get("dht_enabled") and self._widgets["dht_enabled"].get_active()
                self._widgets["stats_interval"].set_sensitive(dht_enabled and stats_enabled)

            # Rate limit max queries sensitivity (only if DHT is enabled)
            if self._widgets.get("rate_limit_enabled") and self._widgets.get("max_queries_per_second"):
                rate_limit_enabled = self._widgets["rate_limit_enabled"].get_active()
                dht_enabled = self._widgets.get("dht_enabled") and self._widgets["dht_enabled"].get_active()
                self._widgets["max_queries_per_second"].set_sensitive(dht_enabled and rate_limit_enabled)

            self.logger.trace(
                "DHT tab dependencies set up",
                extra={"class_name": self.__class__.__name__},
            )

        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.error(
                f"Failed to set up DHT dependencies: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _validate_tab_settings(self) -> dict[str, str]:
        """Validate DHT settings. Returns dict of field_name -> error_message."""
        errors: dict[str, str] = {}

        try:
            self._validate_node_id(errors)
            self._validate_ranges(errors)
            self._validate_bootstrap_nodes(errors)
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            errors["general"] = f"Validation error: {e}"
            self.logger.error(
                f"DHT settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return errors

    def _validate_node_id(self, errors: dict[str, str]) -> None:
        """Validate the custom node-id length when auto-generation is off."""
        if (
            self._widgets.get("node_id_auto")
            and not self._widgets["node_id_auto"].get_active()
            and self._widgets.get("node_id_custom")
        ):
            custom_id = self._widgets["node_id_custom"].get_text().strip()
            if custom_id and len(custom_id) != 40:  # 20 bytes = 40 hex chars
                errors["node_id_custom"] = "Node ID must be 40 hexadecimal characters (20 bytes)"

    def _validate_ranges(self, errors: dict[str, str]) -> None:
        """Validate the routing-table size and announcement interval."""
        if self._widgets.get("routing_table_size"):
            size = self._widgets["routing_table_size"].get_value()
            if size < 8 or size > 512:
                errors["routing_table_size"] = "Routing table size should be between 8 and 512"

        if self._widgets.get("announcement_interval"):
            interval = self._widgets["announcement_interval"].get_value()
            if interval < 300:  # 5 minutes
                errors["announcement_interval"] = "Announcement interval below 5 minutes may cause high network load"

    def _validate_bootstrap_nodes(self, errors: dict[str, str]) -> None:
        """Validate that each bootstrap node is a well-formed host:port entry."""
        if not self._widgets.get("bootstrap_nodes"):
            return
        for node in self._read_text_lines(self._widgets["bootstrap_nodes"]):
            message = self._bootstrap_node_error(node)
            if message:
                errors["bootstrap_nodes"] = message
                break

    @staticmethod
    def _bootstrap_node_error(node: str) -> str | None:
        """Return an error message for a malformed host:port node, else ``None``."""
        if ":" not in node:
            return f"Invalid bootstrap node format: {node} (should be host:port)"
        _host, port_str = node.rsplit(":", 1)
        try:
            port = int(port_str)
        except ValueError:
            return f"Invalid port in bootstrap node: {node}"
        if port < 1 or port > 65535:
            return f"Invalid port in bootstrap node: {node}"
        return None

    # Signal handlers
    def _on_dht_enabled_changed(self, switch: Any, state: Any) -> None:
        """Handle DHT enable/disable toggle"""
        self.logger.trace(
            f"DHT enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        # NOTE: Setting will be saved in batch via _collect_settings()

        # Enable/disable ALL DHT widgets based on state
        sensitive_widgets = [
            # Node configuration
            "node_id_auto",
            "node_id_custom",
            "routing_table_size",
            # Timing settings
            "announcement_interval",
            "bootstrap_timeout",
            "query_timeout",
            # Network settings
            "max_nodes",
            "bucket_size",
            "concurrent_queries",
            # Bootstrap settings
            "bootstrap_nodes",
            "auto_bootstrap",
            # Statistics settings
            "enable_stats",
            "stats_interval",
            # Security settings
            "validate_tokens",
            "rate_limit_enabled",
            "max_queries_per_second",
        ]

        for widget_name in sensitive_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(state)

    def _on_node_id_auto_toggled(self, check_button: Any) -> None:
        """Handle automatic node ID toggle"""
        auto_enabled = check_button.get_active()
        # NOTE: Setting will be saved in batch via _collect_settings()
        if self._widgets["node_id_custom"]:
            self._widgets["node_id_custom"].set_sensitive(not auto_enabled)
        self.logger.trace(
            f"Node ID auto generation: {auto_enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_enable_stats_toggled(self, check_button: Any) -> None:
        """Handle enable stats toggle"""
        enabled = check_button.get_active()
        # NOTE: Setting will be saved in batch via _collect_settings()
        if self._widgets["stats_interval"]:
            self._widgets["stats_interval"].set_sensitive(enabled)
        self.logger.trace(
            f"DHT stats enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_rate_limit_toggled(self, check_button: Any) -> None:
        """Handle rate limit toggle"""
        enabled = check_button.get_active()
        # NOTE: Setting will be saved in batch via _collect_settings()
        if self._widgets["max_queries_per_second"]:
            self._widgets["max_queries_per_second"].set_sensitive(enabled)
        self.logger.trace(
            f"Rate limit enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )
