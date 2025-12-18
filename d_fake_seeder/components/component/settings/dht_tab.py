"""
DHT Settings Tab

Provides configuration interface for DHT (Distributed Hash Table) settings.
Manages DHT node configuration, bootstrap settings, and trackerless operation parameters.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")

from .base_tab import BaseSettingsTab  # noqa: E402

# fmt: on


class DHTTab(BaseSettingsTab):
    """DHT configuration tab"""

    # Note: DHT settings use manual loading/saving due to nested structure (protocols.dht.*)
    WIDGET_MAPPINGS: list = []

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
            # Basic DHT settings
            if self._widgets["dht_enabled"]:
                value = self.app_settings.get("protocols.dht.enabled", True)
                self._widgets["dht_enabled"].set_state(value)

            # Node configuration
            node_id_setting = self.app_settings.get("protocols.dht.node_id", "auto_generate")
            if self._widgets["node_id_auto"]:
                self._widgets["node_id_auto"].set_active(node_id_setting == "auto_generate")

            if self._widgets["node_id_custom"]:
                if node_id_setting != "auto_generate":
                    self._widgets["node_id_custom"].set_text(str(node_id_setting))
                self._widgets["node_id_custom"].set_sensitive(node_id_setting != "auto_generate")

            # Network settings
            if self._widgets["routing_table_size"]:
                value = self.app_settings.get("protocols.dht.routing_table_size", 160)
                self._widgets["routing_table_size"].set_value(value)

            if self._widgets["announcement_interval"]:
                value = self.app_settings.get("protocols.dht.announcement_interval", 1800)
                self._widgets["announcement_interval"].set_value(value)

            # Extended settings (now directly in protocols.dht.*)
            if self._widgets["bootstrap_timeout"]:
                value = self.app_settings.get("protocols.dht.bootstrap_timeout", 30)
                self._widgets["bootstrap_timeout"].set_value(value)

            if self._widgets["query_timeout"]:
                value = self.app_settings.get("protocols.dht.query_timeout", 10)
                self._widgets["query_timeout"].set_value(value)

            if self._widgets["max_nodes"]:
                value = self.app_settings.get("protocols.dht.max_nodes", 1000)
                self._widgets["max_nodes"].set_value(value)

            if self._widgets["bucket_size"]:
                value = self.app_settings.get("protocols.dht.bucket_size", 8)
                self._widgets["bucket_size"].set_value(value)

            if self._widgets["concurrent_queries"]:
                value = self.app_settings.get("protocols.dht.concurrent_queries", 3)
                self._widgets["concurrent_queries"].set_value(value)

            # Bootstrap settings
            if self._widgets["auto_bootstrap"]:
                value = self.app_settings.get("protocols.dht.auto_bootstrap", True)
                self._widgets["auto_bootstrap"].set_active(value)

            # Bootstrap nodes text
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

            # Statistics settings
            if self._widgets["enable_stats"]:
                value = self.app_settings.get("protocols.dht.enable_stats", True)
                self._widgets["enable_stats"].set_active(value)

            if self._widgets["stats_interval"]:
                value = self.app_settings.get("protocols.dht.stats_interval", 60)
                self._widgets["stats_interval"].set_value(value)

            # Security settings
            if self._widgets["validate_tokens"]:
                value = self.app_settings.get("protocols.dht.validate_tokens", True)
                self._widgets["validate_tokens"].set_active(value)

            if self._widgets["rate_limit_enabled"]:
                value = self.app_settings.get("protocols.dht.rate_limit_enabled", True)
                self._widgets["rate_limit_enabled"].set_active(value)

            if self._widgets["max_queries_per_second"]:
                value = self.app_settings.get("protocols.dht.max_queries_per_second", 10)
                self._widgets["max_queries_per_second"].set_value(value)

            self.logger.trace(
                "DHT settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load DHT settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current DHT settings from UI widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: Dict[str, Any] = {}

        try:
            # Basic settings
            if self._widgets.get("dht_enabled"):
                settings["protocols.dht.enabled"] = self._widgets["dht_enabled"].get_state()

            # Node configuration
            if self._widgets.get("node_id_auto") and self._widgets["node_id_auto"].get_active():
                settings["protocols.dht.node_id"] = "auto_generate"
            elif self._widgets.get("node_id_custom"):
                custom_id = self._widgets["node_id_custom"].get_text().strip()
                if custom_id:
                    settings["protocols.dht.node_id"] = custom_id

            # Network settings
            if self._widgets.get("routing_table_size"):
                settings["protocols.dht.routing_table_size"] = int(self._widgets["routing_table_size"].get_value())

            if self._widgets.get("announcement_interval"):
                settings["protocols.dht.announcement_interval"] = int(
                    self._widgets["announcement_interval"].get_value()
                )

            # Extended settings (now directly in protocols.dht.*)
            if self._widgets.get("bootstrap_timeout"):
                settings["protocols.dht.bootstrap_timeout"] = int(self._widgets["bootstrap_timeout"].get_value())

            if self._widgets.get("query_timeout"):
                settings["protocols.dht.query_timeout"] = int(self._widgets["query_timeout"].get_value())

            if self._widgets.get("max_nodes"):
                settings["protocols.dht.max_nodes"] = int(self._widgets["max_nodes"].get_value())

            if self._widgets.get("bucket_size"):
                settings["protocols.dht.bucket_size"] = int(self._widgets["bucket_size"].get_value())

            if self._widgets.get("concurrent_queries"):
                settings["protocols.dht.concurrent_queries"] = int(self._widgets["concurrent_queries"].get_value())

            # Bootstrap settings
            if self._widgets.get("auto_bootstrap"):
                settings["protocols.dht.auto_bootstrap"] = self._widgets["auto_bootstrap"].get_active()

            # Bootstrap nodes
            if self._widgets.get("bootstrap_nodes"):
                buffer = self._widgets["bootstrap_nodes"].get_buffer()
                start, end = buffer.get_bounds()
                text = buffer.get_text(start, end, False)
                nodes = [line.strip() for line in text.split("\n") if line.strip()]
                settings["protocols.dht.bootstrap_nodes"] = nodes

            # Statistics settings
            if self._widgets.get("enable_stats"):
                settings["protocols.dht.enable_stats"] = self._widgets["enable_stats"].get_active()

            if self._widgets.get("stats_interval"):
                settings["protocols.dht.stats_interval"] = int(self._widgets["stats_interval"].get_value())

            # Security settings
            if self._widgets.get("validate_tokens"):
                settings["protocols.dht.validate_tokens"] = self._widgets["validate_tokens"].get_active()

            if self._widgets.get("rate_limit_enabled"):
                settings["protocols.dht.rate_limit_enabled"] = self._widgets["rate_limit_enabled"].get_active()

            if self._widgets.get("max_queries_per_second"):
                settings["protocols.dht.max_queries_per_second"] = int(
                    self._widgets["max_queries_per_second"].get_value()
                )

            self.logger.trace(f"Collected {len(settings)} settings from DHT tab")

            return settings

        except Exception as e:
            self.logger.error(
                f"Failed to collect DHT settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {}

    def _setup_dependencies(self) -> None:
        """Set up dependencies between UI elements"""
        # Initial dependency state based on current settings
        try:
            if self._widgets.get("dht_enabled"):
                state = self._widgets["dht_enabled"].get_state()
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
                dht_enabled = self._widgets.get("dht_enabled") and self._widgets["dht_enabled"].get_state()
                self._widgets["node_id_custom"].set_sensitive(dht_enabled and not auto_enabled)

            # Stats interval sensitivity (only if DHT is enabled)
            if self._widgets.get("enable_stats") and self._widgets.get("stats_interval"):
                stats_enabled = self._widgets["enable_stats"].get_active()
                dht_enabled = self._widgets.get("dht_enabled") and self._widgets["dht_enabled"].get_state()
                self._widgets["stats_interval"].set_sensitive(dht_enabled and stats_enabled)

            # Rate limit max queries sensitivity (only if DHT is enabled)
            if self._widgets.get("rate_limit_enabled") and self._widgets.get("max_queries_per_second"):
                rate_limit_enabled = self._widgets["rate_limit_enabled"].get_active()
                dht_enabled = self._widgets.get("dht_enabled") and self._widgets["dht_enabled"].get_state()
                self._widgets["max_queries_per_second"].set_sensitive(dht_enabled and rate_limit_enabled)

            self.logger.trace(
                "DHT tab dependencies set up",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to set up DHT dependencies: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate DHT settings. Returns dict of field_name -> error_message."""
        errors: Dict[str, str] = {}

        try:
            # Validate custom node ID format
            if (
                self._widgets.get("node_id_auto")
                and not self._widgets["node_id_auto"].get_active()
                and self._widgets.get("node_id_custom")
            ):
                custom_id = self._widgets["node_id_custom"].get_text().strip()
                if custom_id and len(custom_id) != 40:  # 20 bytes = 40 hex chars
                    errors["node_id_custom"] = "Node ID must be 40 hexadecimal characters (20 bytes)"

            # Validate routing table size
            if self._widgets.get("routing_table_size"):
                size = self._widgets["routing_table_size"].get_value()
                if size < 8 or size > 512:
                    errors["routing_table_size"] = "Routing table size should be between 8 and 512"

            # Validate announcement interval
            if self._widgets.get("announcement_interval"):
                interval = self._widgets["announcement_interval"].get_value()
                if interval < 300:  # 5 minutes
                    errors["announcement_interval"] = (
                        "Announcement interval below 5 minutes may cause high network load"
                    )

            # Validate bootstrap nodes format
            if self._widgets.get("bootstrap_nodes"):
                buffer = self._widgets["bootstrap_nodes"].get_buffer()
                start, end = buffer.get_bounds()
                text = buffer.get_text(start, end, False)
                nodes = [line.strip() for line in text.split("\n") if line.strip()]

                for node in nodes:
                    if ":" not in node:
                        errors["bootstrap_nodes"] = f"Invalid bootstrap node format: {node} (should be host:port)"
                        break
                    else:
                        host, port_str = node.rsplit(":", 1)
                        try:
                            port = int(port_str)
                            if port < 1 or port > 65535:
                                errors["bootstrap_nodes"] = f"Invalid port in bootstrap node: {node}"
                                break
                        except ValueError:
                            errors["bootstrap_nodes"] = f"Invalid port in bootstrap node: {node}"
                            break

        except Exception as e:
            errors["general"] = f"Validation error: {str(e)}"
            self.logger.error(
                f"DHT settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return errors

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
