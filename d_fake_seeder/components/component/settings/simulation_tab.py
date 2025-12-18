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

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS = [
        # Behavior settings (no dependencies)
        {
            "id": "behavior_variation_spin",
            "name": "behavior_variation",
            "setting_key": "simulation.behavior_variation",
            "type": float,
        },
        {
            "id": "switch_client_probability_spin",
            "name": "switch_client_probability",
            "setting_key": "simulation.switch_client_probability",
            "type": float,
        },
        # Traffic pattern settings
        {
            "id": "realistic_variations_check",
            "name": "realistic_variations",
            "setting_key": "simulation.realistic_variations",
            "type": bool,
        },
        {
            "id": "time_based_patterns_check",
            "name": "time_based_patterns",
            "setting_key": "simulation.time_based_patterns",
            "type": bool,
        },
        # Conservative profile settings (7 widgets)
        {
            "id": "conservative_upload_speed_spin",
            "name": "conservative_upload_speed",
            "setting_key": "simulation.profiles.conservative.upload_speed",
            "type": int,
        },
        {
            "id": "conservative_download_speed_spin",
            "name": "conservative_download_speed",
            "setting_key": "simulation.profiles.conservative.download_speed",
            "type": int,
        },
        {
            "id": "conservative_upload_variance_spin",
            "name": "conservative_upload_variance",
            "setting_key": "simulation.profiles.conservative.upload_variance",
            "type": float,
        },
        {
            "id": "conservative_download_variance_spin",
            "name": "conservative_download_variance",
            "setting_key": "simulation.profiles.conservative.download_variance",
            "type": float,
        },
        {
            "id": "conservative_max_connections_spin",
            "name": "conservative_max_connections",
            "setting_key": "simulation.profiles.conservative.max_connections",
            "type": int,
        },
        {
            "id": "conservative_burst_probability_spin",
            "name": "conservative_burst_probability",
            "setting_key": "simulation.profiles.conservative.burst_probability",
            "type": float,
        },
        {
            "id": "conservative_idle_probability_spin",
            "name": "conservative_idle_probability",
            "setting_key": "simulation.profiles.conservative.idle_probability",
            "type": float,
        },
        # Balanced profile settings (7 widgets)
        {
            "id": "balanced_upload_speed_spin",
            "name": "balanced_upload_speed",
            "setting_key": "simulation.profiles.balanced.upload_speed",
            "type": int,
        },
        {
            "id": "balanced_download_speed_spin",
            "name": "balanced_download_speed",
            "setting_key": "simulation.profiles.balanced.download_speed",
            "type": int,
        },
        {
            "id": "balanced_upload_variance_spin",
            "name": "balanced_upload_variance",
            "setting_key": "simulation.profiles.balanced.upload_variance",
            "type": float,
        },
        {
            "id": "balanced_download_variance_spin",
            "name": "balanced_download_variance",
            "setting_key": "simulation.profiles.balanced.download_variance",
            "type": float,
        },
        {
            "id": "balanced_max_connections_spin",
            "name": "balanced_max_connections",
            "setting_key": "simulation.profiles.balanced.max_connections",
            "type": int,
        },
        {
            "id": "balanced_burst_probability_spin",
            "name": "balanced_burst_probability",
            "setting_key": "simulation.profiles.balanced.burst_probability",
            "type": float,
        },
        {
            "id": "balanced_idle_probability_spin",
            "name": "balanced_idle_probability",
            "setting_key": "simulation.profiles.balanced.idle_probability",
            "type": float,
        },
        # Aggressive profile settings (7 widgets)
        {
            "id": "aggressive_upload_speed_spin",
            "name": "aggressive_upload_speed",
            "setting_key": "simulation.profiles.aggressive.upload_speed",
            "type": int,
        },
        {
            "id": "aggressive_download_speed_spin",
            "name": "aggressive_download_speed",
            "setting_key": "simulation.profiles.aggressive.download_speed",
            "type": int,
        },
        {
            "id": "aggressive_upload_variance_spin",
            "name": "aggressive_upload_variance",
            "setting_key": "simulation.profiles.aggressive.upload_variance",
            "type": float,
        },
        {
            "id": "aggressive_download_variance_spin",
            "name": "aggressive_download_variance",
            "setting_key": "simulation.profiles.aggressive.download_variance",
            "type": float,
        },
        {
            "id": "aggressive_max_connections_spin",
            "name": "aggressive_max_connections",
            "setting_key": "simulation.profiles.aggressive.max_connections",
            "type": int,
        },
        {
            "id": "aggressive_burst_probability_spin",
            "name": "aggressive_burst_probability",
            "setting_key": "simulation.profiles.aggressive.burst_probability",
            "type": float,
        },
        {
            "id": "aggressive_idle_probability_spin",
            "name": "aggressive_idle_probability",
            "setting_key": "simulation.profiles.aggressive.idle_probability",
            "type": float,
        },
        # Swarm intelligence settings
        {
            "id": "adaptation_rate_spin",
            "name": "adaptation_rate",
            "setting_key": "simulation.adaptation_rate",
            "type": float,
        },
        {
            "id": "peer_analysis_depth_spin",
            "name": "peer_analysis_depth",
            "setting_key": "simulation.peer_analysis_depth",
            "type": int,
        },
        # Advanced settings
        {
            "id": "client_profile_switching_check",
            "name": "client_profile_switching",
            "setting_key": "simulation.client_profile_switching",
            "type": bool,
        },
        {
            "id": "behavior_randomization_check",
            "name": "behavior_randomization",
            "setting_key": "simulation.behavior_randomization",
            "type": bool,
        },
    ]

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
        """Load Advanced Simulation settings from configuration"""
        try:
            simulation_config = getattr(self.app_settings, "simulation", {})

            # Client Behavior Engine Settings
            client_config = simulation_config.get("client_behavior_engine", {})

            if self._widgets["client_behavior_enabled"]:
                self._widgets["client_behavior_enabled"].set_state(client_config.get("enabled", True))

            if self._widgets["primary_client"]:
                primary_client = client_config.get("primary_client", "qBittorrent")
                self._set_combo_active_text(self._widgets["primary_client"], primary_client)

            if self._widgets["behavior_variation"]:
                self._widgets["behavior_variation"].set_value(client_config.get("behavior_variation", 0.3))

            if self._widgets["switch_client_probability"]:
                self._widgets["switch_client_probability"].set_value(
                    client_config.get("switch_client_probability", 0.05)
                )

            # Traffic Pattern Settings
            traffic_config = simulation_config.get("traffic_patterns", {})

            if self._widgets["traffic_profile"]:
                profile = traffic_config.get("profile", "balanced")
                self._set_combo_active_text(self._widgets["traffic_profile"], profile)

            if self._widgets["realistic_variations"]:
                self.set_switch_state(
                    self._widgets["realistic_variations"], traffic_config.get("realistic_variations", True)
                )

            if self._widgets["time_based_patterns"]:
                self.set_switch_state(
                    self._widgets["time_based_patterns"], traffic_config.get("time_based_patterns", True)
                )

            # Load traffic profiles from seeding_profiles config
            seeding_profiles = getattr(self.app_settings, "seeding_profiles", {})

            # Conservative Profile
            conservative = seeding_profiles.get("conservative", {})
            if self._widgets["conservative_upload_speed"]:
                self._widgets["conservative_upload_speed"].set_value(conservative.get("upload_limit", 50))
            if self._widgets["conservative_download_speed"]:
                self._widgets["conservative_download_speed"].set_value(conservative.get("download_limit", 200))
            if self._widgets["conservative_max_connections"]:
                self._widgets["conservative_max_connections"].set_value(conservative.get("max_connections", 100))

            # Set default variance and probability values for conservative
            if self._widgets["conservative_upload_variance"]:
                self._widgets["conservative_upload_variance"].set_value(0.1)
            if self._widgets["conservative_download_variance"]:
                self._widgets["conservative_download_variance"].set_value(0.15)
            if self._widgets["conservative_burst_probability"]:
                self._widgets["conservative_burst_probability"].set_value(0.05)
            if self._widgets["conservative_idle_probability"]:
                self._widgets["conservative_idle_probability"].set_value(0.2)

            # Balanced Profile
            balanced = seeding_profiles.get("balanced", {})
            if self._widgets["balanced_upload_speed"]:
                self._widgets["balanced_upload_speed"].set_value(balanced.get("upload_limit", 200))
            if self._widgets["balanced_download_speed"]:
                self._widgets["balanced_download_speed"].set_value(balanced.get("download_limit", 800))
            if self._widgets["balanced_max_connections"]:
                self._widgets["balanced_max_connections"].set_value(balanced.get("max_connections", 200))

            # Set default variance and probability values for balanced
            if self._widgets["balanced_upload_variance"]:
                self._widgets["balanced_upload_variance"].set_value(0.3)
            if self._widgets["balanced_download_variance"]:
                self._widgets["balanced_download_variance"].set_value(0.25)
            if self._widgets["balanced_burst_probability"]:
                self._widgets["balanced_burst_probability"].set_value(0.15)
            if self._widgets["balanced_idle_probability"]:
                self._widgets["balanced_idle_probability"].set_value(0.1)

            # Aggressive Profile
            aggressive = seeding_profiles.get("aggressive", {})
            if self._widgets["aggressive_upload_speed"]:
                self._widgets["aggressive_upload_speed"].set_value(aggressive.get("upload_limit", 0))
            if self._widgets["aggressive_download_speed"]:
                self._widgets["aggressive_download_speed"].set_value(aggressive.get("download_limit", 2048))
            if self._widgets["aggressive_max_connections"]:
                self._widgets["aggressive_max_connections"].set_value(aggressive.get("max_connections", 500))

            # Set default variance and probability values for aggressive
            if self._widgets["aggressive_upload_variance"]:
                self._widgets["aggressive_upload_variance"].set_value(0.5)
            if self._widgets["aggressive_download_variance"]:
                self._widgets["aggressive_download_variance"].set_value(0.4)
            if self._widgets["aggressive_burst_probability"]:
                self._widgets["aggressive_burst_probability"].set_value(0.3)
            if self._widgets["aggressive_idle_probability"]:
                self._widgets["aggressive_idle_probability"].set_value(0.05)

            # Swarm Intelligence Settings
            swarm_config = simulation_config.get("swarm_intelligence", {})

            if self._widgets["swarm_intelligence_enabled"]:
                self.set_switch_state(self._widgets["swarm_intelligence_enabled"], swarm_config.get("enabled", True))

            if self._widgets["adaptation_rate"]:
                self._widgets["adaptation_rate"].set_value(swarm_config.get("adaptation_rate", 0.5))

            if self._widgets["peer_analysis_depth"]:
                self._widgets["peer_analysis_depth"].set_value(swarm_config.get("peer_analysis_depth", 10))

            # Advanced Settings (set defaults)
            if self._widgets["client_profile_switching"]:
                self.set_switch_state(self._widgets["client_profile_switching"], True)

            if self._widgets["protocol_compliance_level"]:
                self._set_combo_active_text(self._widgets["protocol_compliance_level"], "strict")

            if self._widgets["behavior_randomization"]:
                self.set_switch_state(self._widgets["behavior_randomization"], True)

            self.logger.trace(
                "Advanced Simulation settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load Advanced Simulation settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

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
        # Collect from WIDGET_MAPPINGS
        settings = self._collect_mapped_settings()

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

            # Seeding Profiles - Conservative
            if self._widgets.get("conservative_upload_speed"):
                settings["seeding_profiles.conservative.upload_limit"] = int(
                    self._widgets["conservative_upload_speed"].get_value()
                )
            if self._widgets.get("conservative_download_speed"):
                settings["seeding_profiles.conservative.download_limit"] = int(
                    self._widgets["conservative_download_speed"].get_value()
                )
            if self._widgets.get("conservative_max_connections"):
                settings["seeding_profiles.conservative.max_connections"] = int(
                    self._widgets["conservative_max_connections"].get_value()
                )

            # Seeding Profiles - Balanced
            if self._widgets.get("balanced_upload_speed"):
                settings["seeding_profiles.balanced.upload_limit"] = int(
                    self._widgets["balanced_upload_speed"].get_value()
                )
            if self._widgets.get("balanced_download_speed"):
                settings["seeding_profiles.balanced.download_limit"] = int(
                    self._widgets["balanced_download_speed"].get_value()
                )
            if self._widgets.get("balanced_max_connections"):
                settings["seeding_profiles.balanced.max_connections"] = int(
                    self._widgets["balanced_max_connections"].get_value()
                )

            # Seeding Profiles - Aggressive
            if self._widgets.get("aggressive_upload_speed"):
                settings["seeding_profiles.aggressive.upload_limit"] = int(
                    self._widgets["aggressive_upload_speed"].get_value()
                )
            if self._widgets.get("aggressive_download_speed"):
                settings["seeding_profiles.aggressive.download_limit"] = int(
                    self._widgets["aggressive_download_speed"].get_value()
                )
            if self._widgets.get("aggressive_max_connections"):
                settings["seeding_profiles.aggressive.max_connections"] = int(
                    self._widgets["aggressive_max_connections"].get_value()
                )

            self.logger.trace(f"Collected {len(settings)} settings from Simulation tab")

        except Exception as e:
            self.logger.error(f"Error collecting Simulation tab settings: {e}")

        return settings

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
