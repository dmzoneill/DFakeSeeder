"""
Advanced Simulation Settings Tab

Provides configuration interface for client behavior simulation engine,
traffic pattern simulation, and swarm intelligence features.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")

from .base_tab import BaseSettingsTab  # noqa: E402
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import (  # noqa: E402
    TranslationMixin,
    UtilityMixin,
    ValidationMixin,
)

# fmt: on


class SimulationTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """Advanced Simulation configuration tab"""

    # Note: Simulation settings use manual loading/saving due to deeply nested structure
    WIDGET_MAPPINGS: list = []

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Simulation"

    def _init_widgets(self) -> None:
        """Initialize Advanced Simulation widgets"""
        # Client Behavior Engine Settings
        self._widgets["client_behavior_enabled"] = self.builder.get_object("client_behavior_enabled_switch")
        self._widgets["primary_client"] = self.builder.get_object("primary_client_combo")
        self._widgets["behavior_variation"] = self.builder.get_object("behavior_variation_spin")
        self._widgets["switch_client_probability"] = self.builder.get_object("switch_client_probability_spin")

        # Traffic Pattern Settings
        self._widgets["traffic_profile"] = self.builder.get_object("traffic_profile_combo")
        self._widgets["realistic_variations"] = self.builder.get_object("realistic_variations_check")
        self._widgets["time_based_patterns"] = self.builder.get_object("time_based_patterns_check")

        # Conservative Profile Settings
        self._widgets["conservative_upload_speed"] = self.builder.get_object("conservative_upload_speed_spin")
        self._widgets["conservative_download_speed"] = self.builder.get_object("conservative_download_speed_spin")
        self._widgets["conservative_upload_variance"] = self.builder.get_object("conservative_upload_variance_spin")
        self._widgets["conservative_download_variance"] = self.builder.get_object("conservative_download_variance_spin")
        self._widgets["conservative_max_connections"] = self.builder.get_object("conservative_max_connections_spin")
        self._widgets["conservative_burst_probability"] = self.builder.get_object("conservative_burst_probability_spin")
        self._widgets["conservative_idle_probability"] = self.builder.get_object("conservative_idle_probability_spin")

        # Balanced Profile Settings
        self._widgets["balanced_upload_speed"] = self.builder.get_object("balanced_upload_speed_spin")
        self._widgets["balanced_download_speed"] = self.builder.get_object("balanced_download_speed_spin")
        self._widgets["balanced_upload_variance"] = self.builder.get_object("balanced_upload_variance_spin")
        self._widgets["balanced_download_variance"] = self.builder.get_object("balanced_download_variance_spin")
        self._widgets["balanced_max_connections"] = self.builder.get_object("balanced_max_connections_spin")
        self._widgets["balanced_burst_probability"] = self.builder.get_object("balanced_burst_probability_spin")
        self._widgets["balanced_idle_probability"] = self.builder.get_object("balanced_idle_probability_spin")

        # Aggressive Profile Settings
        self._widgets["aggressive_upload_speed"] = self.builder.get_object("aggressive_upload_speed_spin")
        self._widgets["aggressive_download_speed"] = self.builder.get_object("aggressive_download_speed_spin")
        self._widgets["aggressive_upload_variance"] = self.builder.get_object("aggressive_upload_variance_spin")
        self._widgets["aggressive_download_variance"] = self.builder.get_object("aggressive_download_variance_spin")
        self._widgets["aggressive_max_connections"] = self.builder.get_object("aggressive_max_connections_spin")
        self._widgets["aggressive_burst_probability"] = self.builder.get_object("aggressive_burst_probability_spin")
        self._widgets["aggressive_idle_probability"] = self.builder.get_object("aggressive_idle_probability_spin")

        # Swarm Intelligence Settings
        self._widgets["swarm_intelligence_enabled"] = self.builder.get_object("swarm_intelligence_enabled_check")
        self._widgets["adaptation_rate"] = self.builder.get_object("adaptation_rate_spin")
        self._widgets["peer_analysis_depth"] = self.builder.get_object("peer_analysis_depth_spin")

        # Advanced Client Behavior Settings
        self._widgets["client_profile_switching"] = self.builder.get_object("client_profile_switching_check")
        self._widgets["protocol_compliance_level"] = self.builder.get_object("protocol_compliance_level_combo")
        self._widgets["behavior_randomization"] = self.builder.get_object("behavior_randomization_check")

        self.logger.trace(
            "Advanced Simulation tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _connect_signals(self) -> None:
        """Connect Advanced Simulation signals"""
        # Simple widgets (behavior_variation, switch_client_probability, realistic_variations,
        # time_based_patterns, all profile settings, adaptation_rate, peer_analysis_depth,
        # client_profile_switching, behavior_randomization) are now auto-connected via WIDGET_MAPPINGS

        # Client Behavior Engine (has dependencies - controls child widget sensitivity)
        if self._widgets["client_behavior_enabled"]:
            self._widgets["client_behavior_enabled"].connect("state-set", self._on_client_behavior_enabled_changed)

        # Dropdown widgets with custom text extraction (uses _get_combo_active_text helper)
        if self._widgets["primary_client"]:
            self._widgets["primary_client"].connect("notify::selected", self._on_primary_client_changed)

        if self._widgets["traffic_profile"]:
            self._widgets["traffic_profile"].connect("notify::selected", self._on_traffic_profile_changed)

        # Swarm Intelligence (has dependencies - controls adaptation_rate/peer_analysis_depth sensitivity)
        if self._widgets["swarm_intelligence_enabled"]:
            self._widgets["swarm_intelligence_enabled"].connect("toggled", self._on_swarm_intelligence_enabled_toggled)

        if self._widgets["protocol_compliance_level"]:
            self._widgets["protocol_compliance_level"].connect(
                "notify::selected", self._on_protocol_compliance_level_changed
            )

        self.logger.trace(
            "Advanced Simulation tab signals connected",
            extra={"class_name": self.__class__.__name__},
        )

    def _load_settings(self) -> None:
        """Load Advanced Simulation settings from configuration using nested keys."""
        try:
            # Client Behavior Engine Settings
            if self._widgets["client_behavior_enabled"]:
                value = self.app_settings.get("simulation.client_behavior_engine.enabled", True)
                self._widgets["client_behavior_enabled"].set_state(value)

            if self._widgets["primary_client"]:
                value = self.app_settings.get("simulation.client_behavior_engine.primary_client", "qBittorrent")
                self._set_combo_active_text(self._widgets["primary_client"], value)

            if self._widgets["behavior_variation"]:
                value = self.app_settings.get("simulation.client_behavior_engine.behavior_variation", 0.3)
                self._widgets["behavior_variation"].set_value(value)

            if self._widgets["switch_client_probability"]:
                value = self.app_settings.get("simulation.client_behavior_engine.switch_client_probability", 0.05)
                self._widgets["switch_client_probability"].set_value(value)

            if self._widgets["client_profile_switching"]:
                value = self.app_settings.get("simulation.client_behavior_engine.client_profile_switching", True)
                self._widgets["client_profile_switching"].set_active(value)

            if self._widgets["protocol_compliance_level"]:
                value = self.app_settings.get("simulation.client_behavior_engine.protocol_compliance_level", "standard")
                self._set_combo_active_text(self._widgets["protocol_compliance_level"], value)

            if self._widgets["behavior_randomization"]:
                value = self.app_settings.get("simulation.client_behavior_engine.behavior_randomization", True)
                self._widgets["behavior_randomization"].set_active(value)

            # Traffic Pattern Settings
            if self._widgets["traffic_profile"]:
                value = self.app_settings.get("simulation.traffic_patterns.profile", "balanced")
                self._set_combo_active_text(self._widgets["traffic_profile"], value)

            if self._widgets["realistic_variations"]:
                value = self.app_settings.get("simulation.traffic_patterns.realistic_variations", True)
                self._widgets["realistic_variations"].set_active(value)

            if self._widgets["time_based_patterns"]:
                value = self.app_settings.get("simulation.traffic_patterns.time_based_patterns", True)
                self._widgets["time_based_patterns"].set_active(value)

            # Conservative Profile
            self._load_profile_settings("conservative")
            # Balanced Profile
            self._load_profile_settings("balanced")
            # Aggressive Profile
            self._load_profile_settings("aggressive")

            # Swarm Intelligence Settings
            if self._widgets["swarm_intelligence_enabled"]:
                value = self.app_settings.get("simulation.swarm_intelligence.enabled", True)
                self._widgets["swarm_intelligence_enabled"].set_active(value)

            if self._widgets["adaptation_rate"]:
                value = self.app_settings.get("simulation.swarm_intelligence.adaptation_rate", 0.5)
                self._widgets["adaptation_rate"].set_value(value)

            if self._widgets["peer_analysis_depth"]:
                value = self.app_settings.get("simulation.swarm_intelligence.peer_analysis_depth", 10)
                self._widgets["peer_analysis_depth"].set_value(value)

            self.logger.trace(
                "Advanced Simulation settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load Advanced Simulation settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _load_profile_settings(self, profile_name: str) -> None:
        """Load settings for a specific profile (conservative, balanced, aggressive)."""
        prefix = f"simulation.profiles.{profile_name}"
        defaults = {
            "conservative": {
                "upload_speed": 50,
                "download_speed": 200,
                "upload_variance": 0.1,
                "download_variance": 0.15,
                "max_connections": 100,
                "burst_probability": 0.05,
                "idle_probability": 0.2,
            },
            "balanced": {
                "upload_speed": 200,
                "download_speed": 800,
                "upload_variance": 0.3,
                "download_variance": 0.25,
                "max_connections": 200,
                "burst_probability": 0.15,
                "idle_probability": 0.1,
            },
            "aggressive": {
                "upload_speed": 500,
                "download_speed": 2048,
                "upload_variance": 0.5,
                "download_variance": 0.4,
                "max_connections": 500,
                "burst_probability": 0.3,
                "idle_probability": 0.05,
            },
        }
        profile_defaults = defaults.get(profile_name, {})

        widget_map = [
            ("upload_speed", "upload_speed"),
            ("download_speed", "download_speed"),
            ("upload_variance", "upload_variance"),
            ("download_variance", "download_variance"),
            ("max_connections", "max_connections"),
            ("burst_probability", "burst_probability"),
            ("idle_probability", "idle_probability"),
        ]

        for widget_suffix, key in widget_map:
            widget_name = f"{profile_name}_{widget_suffix}"
            if self._widgets.get(widget_name):
                value = self.app_settings.get(f"{prefix}.{key}", profile_defaults.get(key, 0))
                self._widgets[widget_name].set_value(value)

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Simulation tab."""
        # Enable/disable ALL simulation widgets based on client behavior enabled
        try:
            if self._widgets.get("client_behavior_enabled"):
                enabled = self._widgets["client_behavior_enabled"].get_state()
                behavior_widgets = [
                    # Client behavior settings
                    "primary_client",
                    "behavior_variation",
                    "switch_client_probability",
                    "client_profile_switching",
                    "protocol_compliance_level",
                    "behavior_randomization",
                    # Traffic pattern settings
                    "traffic_profile",
                    "realistic_variations",
                    "time_based_patterns",
                    # Conservative profile widgets
                    "conservative_upload_speed",
                    "conservative_download_speed",
                    "conservative_upload_variance",
                    "conservative_download_variance",
                    "conservative_max_connections",
                    "conservative_burst_probability",
                    "conservative_idle_probability",
                    # Balanced profile widgets
                    "balanced_upload_speed",
                    "balanced_download_speed",
                    "balanced_upload_variance",
                    "balanced_download_variance",
                    "balanced_max_connections",
                    "balanced_burst_probability",
                    "balanced_idle_probability",
                    # Aggressive profile widgets
                    "aggressive_upload_speed",
                    "aggressive_download_speed",
                    "aggressive_upload_variance",
                    "aggressive_download_variance",
                    "aggressive_max_connections",
                    "aggressive_burst_probability",
                    "aggressive_idle_probability",
                ]
                for widget_name in behavior_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(enabled)

            # Enable/disable swarm intelligence widgets (independent of client_behavior_enabled)
            if self._widgets.get("swarm_intelligence_enabled"):
                enabled = self._widgets["swarm_intelligence_enabled"].get_active()
                swarm_widgets = ["adaptation_rate", "peer_analysis_depth"]
                for widget_name in swarm_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(enabled)
        except Exception as e:
            self.logger.error(f"Error setting up Simulation tab dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Simulation tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: Dict[str, Any] = {}

        try:
            # Client Behavior Engine Settings
            if self._widgets.get("client_behavior_enabled"):
                settings["simulation.client_behavior_engine.enabled"] = self._widgets[
                    "client_behavior_enabled"
                ].get_state()

            if self._widgets.get("primary_client"):
                settings["simulation.client_behavior_engine.primary_client"] = self._get_combo_active_text(
                    self._widgets["primary_client"]
                )

            if self._widgets.get("behavior_variation"):
                settings["simulation.client_behavior_engine.behavior_variation"] = self._widgets[
                    "behavior_variation"
                ].get_value()

            if self._widgets.get("switch_client_probability"):
                settings["simulation.client_behavior_engine.switch_client_probability"] = self._widgets[
                    "switch_client_probability"
                ].get_value()

            if self._widgets.get("client_profile_switching"):
                settings["simulation.client_behavior_engine.client_profile_switching"] = self._widgets[
                    "client_profile_switching"
                ].get_active()

            if self._widgets.get("protocol_compliance_level"):
                settings["simulation.client_behavior_engine.protocol_compliance_level"] = self._get_combo_active_text(
                    self._widgets["protocol_compliance_level"]
                )

            if self._widgets.get("behavior_randomization"):
                settings["simulation.client_behavior_engine.behavior_randomization"] = self._widgets[
                    "behavior_randomization"
                ].get_active()

            # Traffic Pattern Settings
            if self._widgets.get("traffic_profile"):
                settings["simulation.traffic_patterns.profile"] = self._get_combo_active_text(
                    self._widgets["traffic_profile"]
                )

            if self._widgets.get("realistic_variations"):
                settings["simulation.traffic_patterns.realistic_variations"] = self._widgets[
                    "realistic_variations"
                ].get_active()

            if self._widgets.get("time_based_patterns"):
                settings["simulation.traffic_patterns.time_based_patterns"] = self._widgets[
                    "time_based_patterns"
                ].get_active()

            # Swarm Intelligence Settings
            if self._widgets.get("swarm_intelligence_enabled"):
                settings["simulation.swarm_intelligence.enabled"] = self._widgets[
                    "swarm_intelligence_enabled"
                ].get_active()

            if self._widgets.get("adaptation_rate"):
                settings["simulation.swarm_intelligence.adaptation_rate"] = self._widgets["adaptation_rate"].get_value()

            if self._widgets.get("peer_analysis_depth"):
                settings["simulation.swarm_intelligence.peer_analysis_depth"] = int(
                    self._widgets["peer_analysis_depth"].get_value()
                )

            # Profile Settings - Conservative, Balanced, Aggressive
            self._collect_profile_settings(settings, "conservative")
            self._collect_profile_settings(settings, "balanced")
            self._collect_profile_settings(settings, "aggressive")

            self.logger.trace(f"Collected {len(settings)} settings from Simulation tab")

        except Exception as e:
            self.logger.error(f"Error collecting Simulation tab settings: {e}")

        return settings

    def _collect_profile_settings(self, settings: Dict[str, Any], profile_name: str) -> None:
        """Collect settings for a specific profile."""
        prefix = f"simulation.profiles.{profile_name}"
        widget_map = [
            ("upload_speed", "upload_speed", int),
            ("download_speed", "download_speed", int),
            ("upload_variance", "upload_variance", float),
            ("download_variance", "download_variance", float),
            ("max_connections", "max_connections", int),
            ("burst_probability", "burst_probability", float),
            ("idle_probability", "idle_probability", float),
        ]

        for widget_suffix, key, value_type in widget_map:
            widget_name = f"{profile_name}_{widget_suffix}"
            if self._widgets.get(widget_name):
                value = self._widgets[widget_name].get_value()
                settings[f"{prefix}.{key}"] = value_type(value)

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Advanced Simulation settings. Returns dict of field_name -> error_message."""
        errors: Dict[str, str] = {}

        try:
            # Validate behavior variation range
            if self._widgets.get("behavior_variation"):
                variation = self._widgets["behavior_variation"].get_value()
                if variation < 0 or variation > 1:
                    errors["behavior_variation"] = "Behavior variation must be between 0.0 and 1.0"

            # Validate switch client probability
            if self._widgets.get("switch_client_probability"):
                probability = self._widgets["switch_client_probability"].get_value()
                if probability < 0 or probability > 1:
                    errors["switch_client_probability"] = "Switch client probability must be between 0.0 and 1.0"

            # Validate adaptation rate
            if self._widgets.get("adaptation_rate"):
                rate = self._widgets["adaptation_rate"].get_value()
                if rate < 0 or rate > 1:
                    errors["adaptation_rate"] = "Adaptation rate must be between 0.0 and 1.0"

            # Validate variance values for all profiles
            variance_widgets = [
                "conservative_upload_variance",
                "conservative_download_variance",
                "balanced_upload_variance",
                "balanced_download_variance",
                "aggressive_upload_variance",
                "aggressive_download_variance",
            ]

            for widget_name in variance_widgets:
                if self._widgets.get(widget_name):
                    variance = self._widgets[widget_name].get_value()
                    if variance < 0 or variance > 1:
                        errors[widget_name] = f"{widget_name.replace('_', ' ').title()} must be between 0.0 and 1.0"

            # Validate probability values
            probability_widgets = [
                "conservative_burst_probability",
                "conservative_idle_probability",
                "balanced_burst_probability",
                "balanced_idle_probability",
                "aggressive_burst_probability",
                "aggressive_idle_probability",
            ]

            for widget_name in probability_widgets:
                if self._widgets.get(widget_name):
                    probability = self._widgets[widget_name].get_value()
                    if probability < 0 or probability > 1:
                        errors[widget_name] = f"{widget_name.replace('_', ' ').title()} must be between 0.0 and 1.0"

            # Warning for aggressive settings
            if (
                self._widgets.get("aggressive_max_connections")
                and self._widgets["aggressive_max_connections"].get_value() > 1000
            ):
                errors["aggressive_max_connections"] = (
                    "Aggressive profile with >1000 connections may cause high resource usage"
                )

        except Exception as e:
            errors["general"] = f"Validation error: {str(e)}"
            self.logger.error(
                f"Advanced Simulation settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return errors

    # Helper methods
    def _set_combo_active_text(self, dropdown: Any, text: Any) -> Any:
        """Set dropdown active item by text"""
        if not dropdown:
            return

        model = dropdown.get_model()
        if not model:
            return

        # For GTK4 DropDown with StringList
        for i in range(model.get_n_items()):
            item = model.get_string(i)
            if item.lower() == text.lower():
                dropdown.set_selected(i)
                break

    def _get_combo_active_text(self, dropdown: Any) -> Any:
        """Get active dropdown text"""
        if not dropdown:
            return ""

        model = dropdown.get_model()
        if not model:
            return ""

        selected = dropdown.get_selected()
        if selected != 4294967295:  # GTK_INVALID_LIST_POSITION
            return model.get_string(selected)
        return ""

    # Signal handlers
    def _on_client_behavior_enabled_changed(self, switch: Any, state: Any) -> None:
        """Handle client behavior engine enable/disable"""
        self.logger.trace(
            f"Client behavior engine enabled: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        # NOTE: Setting will be saved in batch via _collect_settings()

        # Enable/disable ALL simulation-related widgets
        behavior_widgets = [
            # Client behavior settings
            "primary_client",
            "behavior_variation",
            "switch_client_probability",
            "client_profile_switching",
            "protocol_compliance_level",
            "behavior_randomization",
            # Traffic pattern settings
            "traffic_profile",
            "realistic_variations",
            "time_based_patterns",
            # Conservative profile widgets
            "conservative_upload_speed",
            "conservative_download_speed",
            "conservative_upload_variance",
            "conservative_download_variance",
            "conservative_max_connections",
            "conservative_burst_probability",
            "conservative_idle_probability",
            # Balanced profile widgets
            "balanced_upload_speed",
            "balanced_download_speed",
            "balanced_upload_variance",
            "balanced_download_variance",
            "balanced_max_connections",
            "balanced_burst_probability",
            "balanced_idle_probability",
            # Aggressive profile widgets
            "aggressive_upload_speed",
            "aggressive_download_speed",
            "aggressive_upload_variance",
            "aggressive_download_variance",
            "aggressive_max_connections",
            "aggressive_burst_probability",
            "aggressive_idle_probability",
        ]

        for widget_name in behavior_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(state)

    def _on_primary_client_changed(self, combo_box: Any, _param: Any) -> None:
        """Handle primary client changes"""
        client = self._get_combo_active_text(combo_box)
        # NOTE: Setting will be saved in batch via _collect_settings()
        self.logger.trace(
            f"Primary client will change to: {client}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_traffic_profile_changed(self, combo_box: Any, _param: Any) -> None:
        """Handle traffic profile changes"""
        profile = self._get_combo_active_text(combo_box)
        # NOTE: Setting will be saved in batch via _collect_settings()
        self.logger.trace(
            f"Traffic profile will change to: {profile}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_swarm_intelligence_enabled_toggled(self, check_button: Any) -> None:
        """Handle swarm intelligence enable toggle"""
        enabled = check_button.get_active()
        if self._widgets["adaptation_rate"]:
            self._widgets["adaptation_rate"].set_sensitive(enabled)
        if self._widgets["peer_analysis_depth"]:
            self._widgets["peer_analysis_depth"].set_sensitive(enabled)
        # NOTE: Setting will be saved in batch via _collect_settings()
        self.logger.trace(
            f"Swarm intelligence will be {'enabled' if enabled else 'disabled'}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_protocol_compliance_level_changed(self, combo_box: Any, _param: Any) -> None:
        """Handle protocol compliance level changes"""
        level = self._get_combo_active_text(combo_box)
        # NOTE: Setting will be saved in batch via _collect_settings()
        self.logger.trace(
            f"Protocol compliance level will change to: {level}",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes and enable dropdown translation."""
        self.logger.trace(
            "SimulationTab update_view called",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation functionality
        self.model = model
        self.logger.trace(f"Model stored in SimulationTab: {model is not None}")

        # Automatically translate all dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_all_dropdowns()

    def _create_notification_overlay(self) -> gi.repository.Gtk.Overlay:
        """Create notification overlay for this tab."""
        # Create a minimal overlay for the notification system
        overlay = gi.repository.Gtk.Overlay()
        self._notification_overlay = overlay
        return overlay
