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

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Simulation"

    def _init_widgets(self):
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

        self.logger.debug(
            "Advanced Simulation tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _connect_signals(self):
        """Connect Advanced Simulation signals"""
        # Client Behavior Engine
        if self._widgets["client_behavior_enabled"]:
            self._widgets["client_behavior_enabled"].connect("state-set", self._on_client_behavior_enabled_changed)

        if self._widgets["primary_client"]:
            self._widgets["primary_client"].connect("notify::selected", self._on_primary_client_changed)

        if self._widgets["behavior_variation"]:
            self._widgets["behavior_variation"].connect("value-changed", self._on_behavior_variation_changed)

        if self._widgets["switch_client_probability"]:
            self._widgets["switch_client_probability"].connect(
                "value-changed", self._on_switch_client_probability_changed
            )

        # Traffic Pattern Settings
        if self._widgets["traffic_profile"]:
            self._widgets["traffic_profile"].connect("notify::selected", self._on_traffic_profile_changed)

        if self._widgets["realistic_variations"]:
            self._widgets["realistic_variations"].connect("toggled", self._on_realistic_variations_toggled)

        if self._widgets["time_based_patterns"]:
            self._widgets["time_based_patterns"].connect("toggled", self._on_time_based_patterns_toggled)

        # Conservative Profile
        conservative_widgets = [
            "conservative_upload_speed",
            "conservative_download_speed",
            "conservative_upload_variance",
            "conservative_download_variance",
            "conservative_max_connections",
            "conservative_burst_probability",
            "conservative_idle_probability",
        ]
        for widget_name in conservative_widgets:
            if self._widgets[widget_name]:
                self._widgets[widget_name].connect("value-changed", getattr(self, f"_on_{widget_name}_changed"))

        # Balanced Profile
        balanced_widgets = [
            "balanced_upload_speed",
            "balanced_download_speed",
            "balanced_upload_variance",
            "balanced_download_variance",
            "balanced_max_connections",
            "balanced_burst_probability",
            "balanced_idle_probability",
        ]
        for widget_name in balanced_widgets:
            if self._widgets[widget_name]:
                self._widgets[widget_name].connect("value-changed", getattr(self, f"_on_{widget_name}_changed"))

        # Aggressive Profile
        aggressive_widgets = [
            "aggressive_upload_speed",
            "aggressive_download_speed",
            "aggressive_upload_variance",
            "aggressive_download_variance",
            "aggressive_max_connections",
            "aggressive_burst_probability",
            "aggressive_idle_probability",
        ]
        for widget_name in aggressive_widgets:
            if self._widgets[widget_name]:
                self._widgets[widget_name].connect("value-changed", getattr(self, f"_on_{widget_name}_changed"))

        # Swarm Intelligence
        if self._widgets["swarm_intelligence_enabled"]:
            self._widgets["swarm_intelligence_enabled"].connect("toggled", self._on_swarm_intelligence_enabled_toggled)

        if self._widgets["adaptation_rate"]:
            self._widgets["adaptation_rate"].connect("value-changed", self._on_adaptation_rate_changed)

        if self._widgets["peer_analysis_depth"]:
            self._widgets["peer_analysis_depth"].connect("value-changed", self._on_peer_analysis_depth_changed)

        # Advanced Settings
        if self._widgets["client_profile_switching"]:
            self._widgets["client_profile_switching"].connect("toggled", self._on_client_profile_switching_toggled)

        if self._widgets["protocol_compliance_level"]:
            self._widgets["protocol_compliance_level"].connect(
                "notify::selected", self._on_protocol_compliance_level_changed
            )

        if self._widgets["behavior_randomization"]:
            self._widgets["behavior_randomization"].connect("toggled", self._on_behavior_randomization_toggled)

        self.logger.debug(
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
                self._widgets["realistic_variations"].set_active(traffic_config.get("realistic_variations", True))

            if self._widgets["time_based_patterns"]:
                self._widgets["time_based_patterns"].set_active(traffic_config.get("time_based_patterns", True))

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
                self._widgets["swarm_intelligence_enabled"].set_active(swarm_config.get("enabled", True))

            if self._widgets["adaptation_rate"]:
                self._widgets["adaptation_rate"].set_value(swarm_config.get("adaptation_rate", 0.5))

            if self._widgets["peer_analysis_depth"]:
                self._widgets["peer_analysis_depth"].set_value(swarm_config.get("peer_analysis_depth", 10))

            # Advanced Settings (set defaults)
            if self._widgets["client_profile_switching"]:
                self._widgets["client_profile_switching"].set_active(True)

            if self._widgets["protocol_compliance_level"]:
                self._set_combo_active_text(self._widgets["protocol_compliance_level"], "strict")

            if self._widgets["behavior_randomization"]:
                self._widgets["behavior_randomization"].set_active(True)

            self.logger.debug(
                "Advanced Simulation settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load Advanced Simulation settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def save_settings(self):
        """Save Advanced Simulation settings to configuration"""
        try:
            # Get current simulation config
            simulation_config = getattr(self.app_settings, "simulation", {})

            # Client Behavior Engine Settings
            client_config = simulation_config.setdefault("client_behavior_engine", {})

            if self._widgets["client_behavior_enabled"]:
                client_config["enabled"] = self._widgets["client_behavior_enabled"].get_state()

            if self._widgets["primary_client"]:
                client_config["primary_client"] = self._get_combo_active_text(self._widgets["primary_client"])

            if self._widgets["behavior_variation"]:
                client_config["behavior_variation"] = self._widgets["behavior_variation"].get_value()

            if self._widgets["switch_client_probability"]:
                client_config["switch_client_probability"] = self._widgets["switch_client_probability"].get_value()

            # Traffic Pattern Settings
            traffic_config = simulation_config.setdefault("traffic_patterns", {})

            if self._widgets["traffic_profile"]:
                traffic_config["profile"] = self._get_combo_active_text(self._widgets["traffic_profile"])

            if self._widgets["realistic_variations"]:
                traffic_config["realistic_variations"] = self._widgets["realistic_variations"].get_active()

            if self._widgets["time_based_patterns"]:
                traffic_config["time_based_patterns"] = self._widgets["time_based_patterns"].get_active()

            # Swarm Intelligence Settings
            swarm_config = simulation_config.setdefault("swarm_intelligence", {})

            if self._widgets["swarm_intelligence_enabled"]:
                swarm_config["enabled"] = self._widgets["swarm_intelligence_enabled"].get_active()

            if self._widgets["adaptation_rate"]:
                swarm_config["adaptation_rate"] = self._widgets["adaptation_rate"].get_value()

            if self._widgets["peer_analysis_depth"]:
                swarm_config["peer_analysis_depth"] = int(self._widgets["peer_analysis_depth"].get_value())

            # Save simulation config back
            self.app_settings.set("simulation", simulation_config)

            # Update seeding profiles
            seeding_profiles = getattr(self.app_settings, "seeding_profiles", {})

            # Conservative Profile
            conservative = seeding_profiles.setdefault("conservative", {})
            if self._widgets["conservative_upload_speed"]:
                conservative["upload_limit"] = int(self._widgets["conservative_upload_speed"].get_value())
            if self._widgets["conservative_download_speed"]:
                conservative["download_limit"] = int(self._widgets["conservative_download_speed"].get_value())
            if self._widgets["conservative_max_connections"]:
                conservative["max_connections"] = int(self._widgets["conservative_max_connections"].get_value())

            # Balanced Profile
            balanced = seeding_profiles.setdefault("balanced", {})
            if self._widgets["balanced_upload_speed"]:
                balanced["upload_limit"] = int(self._widgets["balanced_upload_speed"].get_value())
            if self._widgets["balanced_download_speed"]:
                balanced["download_limit"] = int(self._widgets["balanced_download_speed"].get_value())
            if self._widgets["balanced_max_connections"]:
                balanced["max_connections"] = int(self._widgets["balanced_max_connections"].get_value())

            # Aggressive Profile
            aggressive = seeding_profiles.setdefault("aggressive", {})
            if self._widgets["aggressive_upload_speed"]:
                aggressive["upload_limit"] = int(self._widgets["aggressive_upload_speed"].get_value())
            if self._widgets["aggressive_download_speed"]:
                aggressive["download_limit"] = int(self._widgets["aggressive_download_speed"].get_value())
            if self._widgets["aggressive_max_connections"]:
                aggressive["max_connections"] = int(self._widgets["aggressive_max_connections"].get_value())

            # Save seeding profiles back
            self.app_settings.set("seeding_profiles", seeding_profiles)

            self.logger.debug(
                "Advanced Simulation settings saved successfully",
                extra={"class_name": self.__class__.__name__},
            )

            # Return the settings dict (required by base class)
            return {"simulation": simulation_config, "seeding_profiles": seeding_profiles}

        except Exception as e:
            self.logger.error(
                f"Failed to save Advanced Simulation settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {}

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Simulation tab."""
        # Enable/disable behavior widgets based on client behavior enabled
        try:
            if self._widgets.get("client_behavior_enabled"):
                enabled = self._widgets["client_behavior_enabled"].get_state()
                behavior_widgets = [
                    "primary_client",
                    "behavior_variation",
                    "switch_client_probability",
                    "client_profile_switching",
                    "protocol_compliance_level",
                    "behavior_randomization",
                ]
                for widget_name in behavior_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(enabled)

            # Enable/disable swarm intelligence widgets
            if self._widgets.get("swarm_intelligence_enabled"):
                enabled = self._widgets["swarm_intelligence_enabled"].get_active()
                swarm_widgets = ["adaptation_rate", "peer_analysis_depth"]
                for widget_name in swarm_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(enabled)
        except Exception as e:
            self.logger.error(f"Error setting up Simulation tab dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Simulation tab widgets."""
        # Simulation tab has its own save_settings() override that handles saving directly
        # Return empty dict here to avoid circular call, since save_settings() doesn't use _collect_settings()
        return {}

    def validate_settings(self) -> Dict[str, Any]:
        """Validate Advanced Simulation settings"""
        validation_result: Dict[str, Any] = {
            "valid": True,
            "errors": [],
            "warnings": [],
        }

        try:
            # Validate behavior variation range
            if self._widgets["behavior_variation"]:
                variation = self._widgets["behavior_variation"].get_value()
                if variation < 0 or variation > 1:
                    validation_result["errors"].append("Behavior variation must be between 0.0 and 1.0")
                    validation_result["valid"] = False

            # Validate switch client probability
            if self._widgets["switch_client_probability"]:
                probability = self._widgets["switch_client_probability"].get_value()
                if probability < 0 or probability > 1:
                    validation_result["errors"].append("Switch client probability must be between 0.0 and 1.0")
                    validation_result["valid"] = False

            # Validate adaptation rate
            if self._widgets["adaptation_rate"]:
                rate = self._widgets["adaptation_rate"].get_value()
                if rate < 0 or rate > 1:
                    validation_result["errors"].append("Adaptation rate must be between 0.0 and 1.0")
                    validation_result["valid"] = False

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
                if self._widgets[widget_name]:
                    variance = self._widgets[widget_name].get_value()
                    if variance < 0 or variance > 1:
                        validation_result["errors"].append(
                            f"{widget_name.replace('_', ' ').title()} must be between 0.0 and 1.0"
                        )
                        validation_result["valid"] = False

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
                if self._widgets[widget_name]:
                    probability = self._widgets[widget_name].get_value()
                    if probability < 0 or probability > 1:
                        validation_result["errors"].append(
                            f"{widget_name.replace('_', ' ').title()} must be between 0.0 and 1.0"
                        )
                        validation_result["valid"] = False

            # Warning for aggressive settings
            if (
                self._widgets["aggressive_max_connections"]
                and self._widgets["aggressive_max_connections"].get_value() > 1000
            ):
                validation_result["warnings"].append(
                    "Aggressive profile with >1000 connections may cause high resource usage"
                )

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {str(e)}")
            validation_result["valid"] = False
            self.logger.error(
                f"Advanced Simulation settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return validation_result

    # Helper methods
    def _set_combo_active_text(self, dropdown, text):
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

    def _get_combo_active_text(self, dropdown):
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
    def _on_client_behavior_enabled_changed(self, switch, state):
        """Handle client behavior engine enable/disable"""
        self.logger.debug(
            f"Client behavior engine enabled: {state}",
            extra={"class_name": self.__class__.__name__},
        )

        # Enable/disable related widgets
        behavior_widgets = [
            "primary_client",
            "behavior_variation",
            "switch_client_probability",
            "client_profile_switching",
            "protocol_compliance_level",
            "behavior_randomization",
        ]

        for widget_name in behavior_widgets:
            if self._widgets.get(widget_name):
                self._widgets[widget_name].set_sensitive(state)

    def _on_primary_client_changed(self, combo_box, _param):
        """Handle primary client changes"""
        client = self._get_combo_active_text(combo_box)
        self.logger.debug(
            f"Primary client changed to: {client}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_behavior_variation_changed(self, spin_button):
        """Handle behavior variation changes"""
        variation = spin_button.get_value()
        self.logger.debug(
            f"Behavior variation: {variation}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_switch_client_probability_changed(self, spin_button):
        """Handle switch client probability changes"""
        probability = spin_button.get_value()
        self.logger.debug(
            f"Switch client probability: {probability}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_traffic_profile_changed(self, combo_box, _param):
        """Handle traffic profile changes"""
        profile = self._get_combo_active_text(combo_box)
        self.logger.debug(
            f"Traffic profile changed to: {profile}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_realistic_variations_toggled(self, check_button):
        """Handle realistic variations toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Realistic variations: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_time_based_patterns_toggled(self, check_button):
        """Handle time-based patterns toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Time-based patterns: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_swarm_intelligence_enabled_toggled(self, check_button):
        """Handle swarm intelligence enable toggle"""
        enabled = check_button.get_active()
        if self._widgets["adaptation_rate"]:
            self._widgets["adaptation_rate"].set_sensitive(enabled)
        if self._widgets["peer_analysis_depth"]:
            self._widgets["peer_analysis_depth"].set_sensitive(enabled)
        self.logger.debug(
            f"Swarm intelligence enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_adaptation_rate_changed(self, spin_button):
        """Handle adaptation rate changes"""
        rate = spin_button.get_value()
        self.logger.debug(f"Adaptation rate: {rate}", extra={"class_name": self.__class__.__name__})

    def _on_peer_analysis_depth_changed(self, spin_button):
        """Handle peer analysis depth changes"""
        depth = spin_button.get_value()
        self.logger.debug(
            f"Peer analysis depth: {depth}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_client_profile_switching_toggled(self, check_button):
        """Handle client profile switching toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Client profile switching: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_protocol_compliance_level_changed(self, combo_box, _param):
        """Handle protocol compliance level changes"""
        level = self._get_combo_active_text(combo_box)
        self.logger.debug(
            f"Protocol compliance level: {level}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_behavior_randomization_toggled(self, check_button):
        """Handle behavior randomization toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Behavior randomization: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    # Dynamic signal handlers for profile settings
    def _on_conservative_upload_speed_changed(self, spin_button):
        self.logger.debug(
            f"Conservative upload speed: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_conservative_download_speed_changed(self, spin_button):
        self.logger.debug(
            f"Conservative download speed: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_conservative_upload_variance_changed(self, spin_button):
        self.logger.debug(
            f"Conservative upload variance: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_conservative_download_variance_changed(self, spin_button):
        self.logger.debug(
            f"Conservative download variance: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_conservative_max_connections_changed(self, spin_button):
        self.logger.debug(
            f"Conservative max connections: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_conservative_burst_probability_changed(self, spin_button):
        self.logger.debug(
            f"Conservative burst probability: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_conservative_idle_probability_changed(self, spin_button):
        self.logger.debug(
            f"Conservative idle probability: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_balanced_upload_speed_changed(self, spin_button):
        self.logger.debug(
            f"Balanced upload speed: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_balanced_download_speed_changed(self, spin_button):
        self.logger.debug(
            f"Balanced download speed: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_balanced_upload_variance_changed(self, spin_button):
        self.logger.debug(
            f"Balanced upload variance: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_balanced_download_variance_changed(self, spin_button):
        self.logger.debug(
            f"Balanced download variance: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_balanced_max_connections_changed(self, spin_button):
        self.logger.debug(
            f"Balanced max connections: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_balanced_burst_probability_changed(self, spin_button):
        self.logger.debug(
            f"Balanced burst probability: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_balanced_idle_probability_changed(self, spin_button):
        self.logger.debug(
            f"Balanced idle probability: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_aggressive_upload_speed_changed(self, spin_button):
        self.logger.debug(
            f"Aggressive upload speed: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_aggressive_download_speed_changed(self, spin_button):
        self.logger.debug(
            f"Aggressive download speed: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_aggressive_upload_variance_changed(self, spin_button):
        self.logger.debug(
            f"Aggressive upload variance: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_aggressive_download_variance_changed(self, spin_button):
        self.logger.debug(
            f"Aggressive download variance: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_aggressive_max_connections_changed(self, spin_button):
        self.logger.debug(
            f"Aggressive max connections: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_aggressive_burst_probability_changed(self, spin_button):
        self.logger.debug(
            f"Aggressive burst probability: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_aggressive_idle_probability_changed(self, spin_button):
        self.logger.debug(
            f"Aggressive idle probability: {spin_button.get_value()}",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes and enable dropdown translation."""
        self.logger.debug(
            "SimulationTab update_view called",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation functionality
        self.model = model
        self.logger.debug(f"Model stored in SimulationTab: {model is not None}")

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

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.debug(
            "SimulationTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "SimulationTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "SimulationTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )
