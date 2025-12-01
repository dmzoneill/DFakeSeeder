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

    @property
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        return "DHT"

    def _init_widgets(self):
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

        self.logger.debug("DHT tab widgets initialized", extra={"class_name": self.__class__.__name__})

    def _connect_signals(self):
        """Connect DHT-specific signals"""
        # Enable/Disable DHT
        if self._widgets["dht_enabled"]:
            self._widgets["dht_enabled"].connect("state-set", self._on_dht_enabled_changed)

        # Node ID configuration
        if self._widgets["node_id_auto"]:
            self._widgets["node_id_auto"].connect("toggled", self._on_node_id_auto_toggled)

        if self._widgets["node_id_custom"]:
            self._widgets["node_id_custom"].connect("changed", self._on_node_id_custom_changed)

        # Timing settings
        if self._widgets["announcement_interval"]:
            self._widgets["announcement_interval"].connect("value-changed", self._on_announcement_interval_changed)

        if self._widgets["bootstrap_timeout"]:
            self._widgets["bootstrap_timeout"].connect("value-changed", self._on_bootstrap_timeout_changed)

        if self._widgets["query_timeout"]:
            self._widgets["query_timeout"].connect("value-changed", self._on_query_timeout_changed)

        # Network settings
        if self._widgets["routing_table_size"]:
            self._widgets["routing_table_size"].connect("value-changed", self._on_routing_table_size_changed)

        if self._widgets["max_nodes"]:
            self._widgets["max_nodes"].connect("value-changed", self._on_max_nodes_changed)

        if self._widgets["bucket_size"]:
            self._widgets["bucket_size"].connect("value-changed", self._on_bucket_size_changed)

        if self._widgets["concurrent_queries"]:
            self._widgets["concurrent_queries"].connect("value-changed", self._on_concurrent_queries_changed)

        # Bootstrap settings
        if self._widgets["auto_bootstrap"]:
            self._widgets["auto_bootstrap"].connect("toggled", self._on_auto_bootstrap_toggled)

        # Statistics settings
        if self._widgets["enable_stats"]:
            self._widgets["enable_stats"].connect("toggled", self._on_enable_stats_toggled)

        if self._widgets["stats_interval"]:
            self._widgets["stats_interval"].connect("value-changed", self._on_stats_interval_changed)

        # Security settings
        if self._widgets["validate_tokens"]:
            self._widgets["validate_tokens"].connect("toggled", self._on_validate_tokens_toggled)

        if self._widgets["rate_limit_enabled"]:
            self._widgets["rate_limit_enabled"].connect("toggled", self._on_rate_limit_toggled)

        if self._widgets["max_queries_per_second"]:
            self._widgets["max_queries_per_second"].connect("value-changed", self._on_max_queries_changed)

        self.logger.debug("DHT tab signals connected", extra={"class_name": self.__class__.__name__})

    def _load_settings(self):
        """Load DHT settings from configuration"""
        try:
            dht_config = getattr(self.app_settings, "protocols", {}).get("dht", {})

            # Basic DHT settings
            if self._widgets["dht_enabled"]:
                self._widgets["dht_enabled"].set_state(dht_config.get("enabled", True))

            # Node configuration
            node_id_setting = dht_config.get("node_id", "auto_generate")
            if self._widgets["node_id_auto"]:
                self._widgets["node_id_auto"].set_active(node_id_setting == "auto_generate")

            if self._widgets["node_id_custom"]:
                if node_id_setting != "auto_generate":
                    self._widgets["node_id_custom"].set_text(str(node_id_setting))
                self._widgets["node_id_custom"].set_sensitive(node_id_setting != "auto_generate")

            # Network settings
            if self._widgets["routing_table_size"]:
                self._widgets["routing_table_size"].set_value(dht_config.get("routing_table_size", 160))

            if self._widgets["announcement_interval"]:
                self._widgets["announcement_interval"].set_value(dht_config.get("announcement_interval", 1800))

            # Extended settings from configuration
            extended_config = dht_config.get("extended", {})

            if self._widgets["bootstrap_timeout"]:
                self._widgets["bootstrap_timeout"].set_value(extended_config.get("bootstrap_timeout", 30))

            if self._widgets["query_timeout"]:
                self._widgets["query_timeout"].set_value(extended_config.get("query_timeout", 10))

            if self._widgets["max_nodes"]:
                self._widgets["max_nodes"].set_value(extended_config.get("max_nodes", 1000))

            if self._widgets["bucket_size"]:
                self._widgets["bucket_size"].set_value(extended_config.get("bucket_size", 8))

            if self._widgets["concurrent_queries"]:
                self._widgets["concurrent_queries"].set_value(extended_config.get("concurrent_queries", 3))

            # Bootstrap settings
            if self._widgets["auto_bootstrap"]:
                self._widgets["auto_bootstrap"].set_active(extended_config.get("auto_bootstrap", True))

            # Bootstrap nodes text
            if self._widgets["bootstrap_nodes"]:
                buffer = self._widgets["bootstrap_nodes"].get_buffer()
                bootstrap_list = extended_config.get(
                    "bootstrap_nodes",
                    [
                        "router.bittorrent.com:6881",
                        "dht.transmissionbt.com:6881",
                        "router.utorrent.com:6881",
                    ],
                )
                buffer.set_text("\n".join(bootstrap_list))

            # Statistics settings
            if self._widgets["enable_stats"]:
                self._widgets["enable_stats"].set_active(extended_config.get("enable_stats", True))

            if self._widgets["stats_interval"]:
                self._widgets["stats_interval"].set_value(extended_config.get("stats_interval", 60))

            # Security settings
            if self._widgets["validate_tokens"]:
                self._widgets["validate_tokens"].set_active(extended_config.get("validate_tokens", True))

            if self._widgets["rate_limit_enabled"]:
                self._widgets["rate_limit_enabled"].set_active(extended_config.get("rate_limit_enabled", True))

            if self._widgets["max_queries_per_second"]:
                self._widgets["max_queries_per_second"].set_value(extended_config.get("max_queries_per_second", 10))

            self.logger.debug(
                "DHT settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load DHT settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current DHT settings from UI widgets"""
        try:
            # Get current protocols config
            protocols_config = getattr(self.app_settings, "protocols", {})
            dht_config = protocols_config.get("dht", {})

            # Basic settings
            if self._widgets["dht_enabled"]:
                dht_config["enabled"] = self._widgets["dht_enabled"].get_state()

            # Node configuration
            if self._widgets["node_id_auto"] and self._widgets["node_id_auto"].get_active():
                dht_config["node_id"] = "auto_generate"
            elif self._widgets["node_id_custom"]:
                custom_id = self._widgets["node_id_custom"].get_text().strip()
                if custom_id:
                    dht_config["node_id"] = custom_id

            # Network settings
            if self._widgets["routing_table_size"]:
                dht_config["routing_table_size"] = int(self._widgets["routing_table_size"].get_value())

            if self._widgets["announcement_interval"]:
                dht_config["announcement_interval"] = int(self._widgets["announcement_interval"].get_value())

            # Extended settings
            extended_config = dht_config.setdefault("extended", {})

            if self._widgets["bootstrap_timeout"]:
                extended_config["bootstrap_timeout"] = int(self._widgets["bootstrap_timeout"].get_value())

            if self._widgets["query_timeout"]:
                extended_config["query_timeout"] = int(self._widgets["query_timeout"].get_value())

            if self._widgets["max_nodes"]:
                extended_config["max_nodes"] = int(self._widgets["max_nodes"].get_value())

            if self._widgets["bucket_size"]:
                extended_config["bucket_size"] = int(self._widgets["bucket_size"].get_value())

            if self._widgets["concurrent_queries"]:
                extended_config["concurrent_queries"] = int(self._widgets["concurrent_queries"].get_value())

            # Bootstrap settings
            if self._widgets["auto_bootstrap"]:
                extended_config["auto_bootstrap"] = self._widgets["auto_bootstrap"].get_active()

            # Bootstrap nodes
            if self._widgets["bootstrap_nodes"]:
                buffer = self._widgets["bootstrap_nodes"].get_buffer()
                start, end = buffer.get_bounds()
                text = buffer.get_text(start, end, False)
                nodes = [line.strip() for line in text.split("\n") if line.strip()]
                extended_config["bootstrap_nodes"] = nodes

            # Statistics settings
            if self._widgets["enable_stats"]:
                extended_config["enable_stats"] = self._widgets["enable_stats"].get_active()

            if self._widgets["stats_interval"]:
                extended_config["stats_interval"] = int(self._widgets["stats_interval"].get_value())

            # Security settings
            if self._widgets["validate_tokens"]:
                extended_config["validate_tokens"] = self._widgets["validate_tokens"].get_active()

            if self._widgets["rate_limit_enabled"]:
                extended_config["rate_limit_enabled"] = self._widgets["rate_limit_enabled"].get_active()

            if self._widgets["max_queries_per_second"]:
                extended_config["max_queries_per_second"] = int(self._widgets["max_queries_per_second"].get_value())

            # Save back to settings
            protocols_config["dht"] = dht_config

            self.logger.debug(
                "DHT settings collected successfully",
                extra={"class_name": self.__class__.__name__},
            )

            return {"protocols": protocols_config}

        except Exception as e:
            self.logger.error(
                f"Failed to collect DHT settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {}

    def _setup_dependencies(self):
        """Set up dependencies between UI elements"""
        # Initial dependency state based on current settings
        try:
            if self._widgets.get("dht_enabled"):
                state = self._widgets["dht_enabled"].get_state()
                sensitive_widgets = [
                    "node_id_auto",
                    "node_id_custom",
                    "routing_table_size",
                    "announcement_interval",
                    "bootstrap_nodes",
                    "auto_bootstrap",
                ]
                for widget_name in sensitive_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(state)

            # Node ID custom field sensitivity
            if self._widgets.get("node_id_auto") and self._widgets.get("node_id_custom"):
                auto_enabled = self._widgets["node_id_auto"].get_active()
                self._widgets["node_id_custom"].set_sensitive(not auto_enabled)

            # Stats interval sensitivity
            if self._widgets.get("enable_stats") and self._widgets.get("stats_interval"):
                stats_enabled = self._widgets["enable_stats"].get_active()
                self._widgets["stats_interval"].set_sensitive(stats_enabled)

            # Rate limit max queries sensitivity
            if self._widgets.get("rate_limit_enabled") and self._widgets.get("max_queries_per_second"):
                rate_limit_enabled = self._widgets["rate_limit_enabled"].get_active()
                self._widgets["max_queries_per_second"].set_sensitive(rate_limit_enabled)

            self.logger.debug(
                "DHT tab dependencies set up",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to set up DHT dependencies: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _validate_tab_settings(self) -> Dict[str, Any]:
        """Validate DHT settings"""
        validation_result: Dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        try:
            # Validate custom node ID format
            if (
                self._widgets["node_id_auto"]
                and not self._widgets["node_id_auto"].get_active()
                and self._widgets["node_id_custom"]
            ):
                custom_id = self._widgets["node_id_custom"].get_text().strip()
                if custom_id and len(custom_id) != 40:  # 20 bytes = 40 hex chars
                    validation_result["errors"].append("Node ID must be 40 hexadecimal characters (20 bytes)")
                    validation_result["valid"] = False

            # Validate routing table size
            if self._widgets["routing_table_size"]:
                size = self._widgets["routing_table_size"].get_value()
                if size < 8 or size > 512:
                    validation_result["warnings"].append("Routing table size should be between 8 and 512")

            # Validate announcement interval
            if self._widgets["announcement_interval"]:
                interval = self._widgets["announcement_interval"].get_value()
                if interval < 300:  # 5 minutes
                    validation_result["warnings"].append(
                        "Announcement interval below 5 minutes may cause high network load"
                    )

            # Validate bootstrap nodes format
            if self._widgets["bootstrap_nodes"]:
                buffer = self._widgets["bootstrap_nodes"].get_buffer()
                start, end = buffer.get_bounds()
                text = buffer.get_text(start, end, False)
                nodes = [line.strip() for line in text.split("\n") if line.strip()]

                for node in nodes:
                    if ":" not in node:
                        validation_result["errors"].append(
                            f"Invalid bootstrap node format: {node} (should be host:port)"
                        )
                        validation_result["valid"] = False
                    else:
                        host, port_str = node.rsplit(":", 1)
                        try:
                            port = int(port_str)
                            if port < 1 or port > 65535:
                                validation_result["errors"].append(f"Invalid port in bootstrap node: {node}")
                                validation_result["valid"] = False
                        except ValueError:
                            validation_result["errors"].append(f"Invalid port in bootstrap node: {node}")
                            validation_result["valid"] = False

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
            self.logger.error(
                f"DHT settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return validation_result

    # Signal handlers
    def _on_dht_enabled_changed(self, switch, state):
        """Handle DHT enable/disable toggle"""
        self.logger.debug(
            f"DHT enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        # Enable/disable other DHT widgets based on state
        sensitive_widgets = [
            "node_id_auto",
            "node_id_custom",
            "routing_table_size",
            "announcement_interval",
            "bootstrap_nodes",
            "auto_bootstrap",
        ]

        for widget_name in sensitive_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(state)

    def _on_node_id_auto_toggled(self, check_button):
        """Handle automatic node ID toggle"""
        auto_enabled = check_button.get_active()
        if self._widgets["node_id_custom"]:
            self._widgets["node_id_custom"].set_sensitive(not auto_enabled)
        self.logger.debug(
            f"Node ID auto generation: {auto_enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_node_id_custom_changed(self, entry):
        """Handle custom node ID changes"""
        self.logger.debug("Custom node ID changed", extra={"class_name": self.__class__.__name__})

    def _on_announcement_interval_changed(self, spin_button):
        """Handle announcement interval changes"""
        interval = spin_button.get_value()
        self.logger.debug(
            f"DHT announcement interval: {interval}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_bootstrap_timeout_changed(self, spin_button):
        """Handle bootstrap timeout changes"""
        timeout = spin_button.get_value()
        self.logger.debug(
            f"Bootstrap timeout: {timeout}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_query_timeout_changed(self, spin_button):
        """Handle query timeout changes"""
        timeout = spin_button.get_value()
        self.logger.debug(f"Query timeout: {timeout}", extra={"class_name": self.__class__.__name__})

    def _on_routing_table_size_changed(self, spin_button):
        """Handle routing table size changes"""
        size = spin_button.get_value()
        self.logger.debug(f"Routing table size: {size}", extra={"class_name": self.__class__.__name__})

    def _on_max_nodes_changed(self, spin_button):
        """Handle max nodes changes"""
        max_nodes = spin_button.get_value()
        self.logger.debug(f"Max nodes: {max_nodes}", extra={"class_name": self.__class__.__name__})

    def _on_bucket_size_changed(self, spin_button):
        """Handle bucket size changes"""
        bucket_size = spin_button.get_value()
        self.logger.debug(f"Bucket size: {bucket_size}", extra={"class_name": self.__class__.__name__})

    def _on_concurrent_queries_changed(self, spin_button):
        """Handle concurrent queries changes"""
        queries = spin_button.get_value()
        self.logger.debug(
            f"Concurrent queries: {queries}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_auto_bootstrap_toggled(self, check_button):
        """Handle auto bootstrap toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"Auto bootstrap: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_enable_stats_toggled(self, check_button):
        """Handle enable stats toggle"""
        enabled = check_button.get_active()
        if self._widgets["stats_interval"]:
            self._widgets["stats_interval"].set_sensitive(enabled)
        self.logger.debug(
            f"DHT stats enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_stats_interval_changed(self, spin_button):
        """Handle stats interval changes"""
        interval = spin_button.get_value()
        self.logger.debug(f"Stats interval: {interval}", extra={"class_name": self.__class__.__name__})

    def _on_validate_tokens_toggled(self, check_button):
        """Handle validate tokens toggle"""
        enabled = check_button.get_active()
        self.logger.debug(f"Validate tokens: {enabled}", extra={"class_name": self.__class__.__name__})

    def _on_rate_limit_toggled(self, check_button):
        """Handle rate limit toggle"""
        enabled = check_button.get_active()
        if self._widgets["max_queries_per_second"]:
            self._widgets["max_queries_per_second"].set_sensitive(enabled)
        self.logger.debug(
            f"Rate limit enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_max_queries_changed(self, spin_button):
        """Handle max queries per second changes"""
        max_queries = spin_button.get_value()
        self.logger.debug(
            f"Max queries per second: {max_queries}",
            extra={"class_name": self.__class__.__name__},
        )
