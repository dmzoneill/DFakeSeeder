"""
Multi-Tracker Settings Tab

Provides configuration interface for Multi-Tracker Support (BEP-012).
Manages tracker tier configuration, failover settings, and announce strategies.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")

from .base_tab import BaseSettingsTab  # noqa: E402
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import TranslationMixin  # noqa: E402
from .settings_mixins import ValidationMixin  # noqa: E402

# fmt: on


class MultiTrackerTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin):
    """Multi-Tracker (BEP-012) configuration tab"""

    @property
    def tab_name(self) -> str:
        """Return the name of this tab"""
        return "Multi-Tracker"

    def _init_widgets(self):
        """Initialize Multi-Tracker specific widgets"""
        # Multi-Tracker Enable/Disable
        self._widgets["multi_tracker_enabled"] = self.builder.get_object("multi_tracker_enabled_switch")

        # Failover Configuration
        self._widgets["failover_enabled"] = self.builder.get_object("failover_enabled_check")
        self._widgets["max_consecutive_failures"] = self.builder.get_object("max_consecutive_failures_spin")
        self._widgets["backoff_base_seconds"] = self.builder.get_object("backoff_base_seconds_spin")
        self._widgets["max_backoff_seconds"] = self.builder.get_object("max_backoff_seconds_spin")

        # Announce Strategy Settings
        self._widgets["announce_to_all_tiers"] = self.builder.get_object("announce_to_all_tiers_check")
        self._widgets["announce_to_all_in_tier"] = self.builder.get_object("announce_to_all_in_tier_check")

        # Tracker Health Monitoring
        self._widgets["health_monitoring_enabled"] = self.builder.get_object("health_monitoring_enabled_check")
        self._widgets["response_time_tracking"] = self.builder.get_object("response_time_tracking_check")
        self._widgets["response_time_smoothing"] = self.builder.get_object("response_time_smoothing_spin")

        # Advanced Settings
        self._widgets["auto_disable_failed_trackers"] = self.builder.get_object("auto_disable_failed_trackers_check")
        self._widgets["tracker_rotation_enabled"] = self.builder.get_object("tracker_rotation_enabled_check")
        self._widgets["rotation_interval_seconds"] = self.builder.get_object("rotation_interval_seconds_spin")

        # Statistics and Monitoring
        self._widgets["track_tier_statistics"] = self.builder.get_object("track_tier_statistics_check")
        self._widgets["log_tracker_failures"] = self.builder.get_object("log_tracker_failures_check")
        self._widgets["log_tier_changes"] = self.builder.get_object("log_tier_changes_check")

        self.logger.debug(
            "Multi-Tracker tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _connect_signals(self):
        """Connect Multi-Tracker specific signals"""
        # Enable/Disable Multi-Tracker
        if self._widgets["multi_tracker_enabled"]:
            self._widgets["multi_tracker_enabled"].connect("state-set", self._on_multi_tracker_enabled_changed)

        # Failover settings
        if self._widgets["failover_enabled"]:
            self._widgets["failover_enabled"].connect("toggled", self._on_failover_enabled_toggled)

        if self._widgets["max_consecutive_failures"]:
            self._widgets["max_consecutive_failures"].connect(
                "value-changed", self._on_max_consecutive_failures_changed
            )

        if self._widgets["backoff_base_seconds"]:
            self._widgets["backoff_base_seconds"].connect("value-changed", self._on_backoff_base_seconds_changed)

        if self._widgets["max_backoff_seconds"]:
            self._widgets["max_backoff_seconds"].connect("value-changed", self._on_max_backoff_seconds_changed)

        # Announce strategy
        if self._widgets["announce_to_all_tiers"]:
            self._widgets["announce_to_all_tiers"].connect("toggled", self._on_announce_to_all_tiers_toggled)

        if self._widgets["announce_to_all_in_tier"]:
            self._widgets["announce_to_all_in_tier"].connect("toggled", self._on_announce_to_all_in_tier_toggled)

        # Health monitoring
        if self._widgets["health_monitoring_enabled"]:
            self._widgets["health_monitoring_enabled"].connect("toggled", self._on_health_monitoring_enabled_toggled)

        if self._widgets["response_time_tracking"]:
            self._widgets["response_time_tracking"].connect("toggled", self._on_response_time_tracking_toggled)

        if self._widgets["response_time_smoothing"]:
            self._widgets["response_time_smoothing"].connect("value-changed", self._on_response_time_smoothing_changed)

        # Advanced settings
        if self._widgets["auto_disable_failed_trackers"]:
            self._widgets["auto_disable_failed_trackers"].connect(
                "toggled", self._on_auto_disable_failed_trackers_toggled
            )

        if self._widgets["tracker_rotation_enabled"]:
            self._widgets["tracker_rotation_enabled"].connect("toggled", self._on_tracker_rotation_enabled_toggled)

        if self._widgets["rotation_interval_seconds"]:
            self._widgets["rotation_interval_seconds"].connect(
                "value-changed", self._on_rotation_interval_seconds_changed
            )

        # Statistics settings
        if self._widgets["track_tier_statistics"]:
            self._widgets["track_tier_statistics"].connect("toggled", self._on_track_tier_statistics_toggled)

        if self._widgets["log_tracker_failures"]:
            self._widgets["log_tracker_failures"].connect("toggled", self._on_log_tracker_failures_toggled)

        if self._widgets["log_tier_changes"]:
            self._widgets["log_tier_changes"].connect("toggled", self._on_log_tier_changes_toggled)

        self.logger.debug(
            "Multi-Tracker tab signals connected",
            extra={"class_name": self.__class__.__name__},
        )

    def _load_settings(self):
        """Load Multi-Tracker settings from configuration"""
        try:
            protocols_config = getattr(self.app_settings, "protocols", {})
            mt_config = protocols_config.get("multi_tracker", {})

            # Basic Multi-Tracker settings
            if self._widgets["multi_tracker_enabled"]:
                self._widgets["multi_tracker_enabled"].set_state(mt_config.get("enabled", True))

            # Failover configuration
            if self._widgets["failover_enabled"]:
                self._widgets["failover_enabled"].set_active(mt_config.get("failover_enabled", True))

            failover_config = mt_config.get("failover", {})

            if self._widgets["max_consecutive_failures"]:
                self._widgets["max_consecutive_failures"].set_value(failover_config.get("max_consecutive_failures", 5))

            if self._widgets["backoff_base_seconds"]:
                self._widgets["backoff_base_seconds"].set_value(failover_config.get("backoff_base_seconds", 60))

            if self._widgets["max_backoff_seconds"]:
                self._widgets["max_backoff_seconds"].set_value(failover_config.get("max_backoff_seconds", 3600))

            # Announce strategy
            if self._widgets["announce_to_all_tiers"]:
                self._widgets["announce_to_all_tiers"].set_active(mt_config.get("announce_to_all_tiers", False))

            if self._widgets["announce_to_all_in_tier"]:
                self._widgets["announce_to_all_in_tier"].set_active(mt_config.get("announce_to_all_in_tier", False))

            # Health monitoring
            health_config = mt_config.get("health_monitoring", {})

            if self._widgets["health_monitoring_enabled"]:
                self._widgets["health_monitoring_enabled"].set_active(health_config.get("enabled", True))

            if self._widgets["response_time_tracking"]:
                self._widgets["response_time_tracking"].set_active(health_config.get("track_response_time", True))

            if self._widgets["response_time_smoothing"]:
                self._widgets["response_time_smoothing"].set_value(health_config.get("response_time_smoothing", 0.8))

            # Advanced settings
            advanced_config = mt_config.get("advanced", {})

            if self._widgets["auto_disable_failed_trackers"]:
                self._widgets["auto_disable_failed_trackers"].set_active(
                    advanced_config.get("auto_disable_failed", True)
                )

            if self._widgets["tracker_rotation_enabled"]:
                self._widgets["tracker_rotation_enabled"].set_active(advanced_config.get("rotation_enabled", False))

            if self._widgets["rotation_interval_seconds"]:
                self._widgets["rotation_interval_seconds"].set_value(
                    advanced_config.get("rotation_interval_seconds", 300)
                )

            # Statistics settings
            stats_config = mt_config.get("statistics", {})

            if self._widgets["track_tier_statistics"]:
                self._widgets["track_tier_statistics"].set_active(stats_config.get("track_tier_stats", True))

            if self._widgets["log_tracker_failures"]:
                self._widgets["log_tracker_failures"].set_active(stats_config.get("log_failures", True))

            if self._widgets["log_tier_changes"]:
                self._widgets["log_tier_changes"].set_active(stats_config.get("log_tier_changes", False))

            self.logger.debug(
                "Multi-Tracker settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load Multi-Tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def _setup_dependencies(self):
        """Set up dependencies between UI elements"""
        try:
            # Update widget sensitivity based on current state
            self._update_tab_dependencies()
        except Exception as e:
            self.logger.error(
                f"Failed to setup Multi-Tracker dependencies: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from UI widgets"""
        settings = {}

        try:
            # Get current protocols config
            protocols_config = getattr(self.app_settings, "protocols", {})
            mt_config = protocols_config.get("multi_tracker", {})

            # Basic settings
            if self._widgets["multi_tracker_enabled"]:
                mt_config["enabled"] = self._widgets["multi_tracker_enabled"].get_state()

            # Failover settings
            if self._widgets["failover_enabled"]:
                mt_config["failover_enabled"] = self._widgets["failover_enabled"].get_active()

            failover_config = mt_config.setdefault("failover", {})

            if self._widgets["max_consecutive_failures"]:
                failover_config["max_consecutive_failures"] = int(self._widgets["max_consecutive_failures"].get_value())

            if self._widgets["backoff_base_seconds"]:
                failover_config["backoff_base_seconds"] = int(self._widgets["backoff_base_seconds"].get_value())

            if self._widgets["max_backoff_seconds"]:
                failover_config["max_backoff_seconds"] = int(self._widgets["max_backoff_seconds"].get_value())

            # Announce strategy
            if self._widgets["announce_to_all_tiers"]:
                mt_config["announce_to_all_tiers"] = self._widgets["announce_to_all_tiers"].get_active()

            if self._widgets["announce_to_all_in_tier"]:
                mt_config["announce_to_all_in_tier"] = self._widgets["announce_to_all_in_tier"].get_active()

            # Health monitoring
            health_config = mt_config.setdefault("health_monitoring", {})

            if self._widgets["health_monitoring_enabled"]:
                health_config["enabled"] = self._widgets["health_monitoring_enabled"].get_active()

            if self._widgets["response_time_tracking"]:
                health_config["track_response_time"] = self._widgets["response_time_tracking"].get_active()

            if self._widgets["response_time_smoothing"]:
                health_config["response_time_smoothing"] = self._widgets["response_time_smoothing"].get_value()

            # Advanced settings
            advanced_config = mt_config.setdefault("advanced", {})

            if self._widgets["auto_disable_failed_trackers"]:
                advanced_config["auto_disable_failed"] = self._widgets["auto_disable_failed_trackers"].get_active()

            if self._widgets["tracker_rotation_enabled"]:
                advanced_config["rotation_enabled"] = self._widgets["tracker_rotation_enabled"].get_active()

            if self._widgets["rotation_interval_seconds"]:
                advanced_config["rotation_interval_seconds"] = int(
                    self._widgets["rotation_interval_seconds"].get_value()
                )

            # Statistics settings
            stats_config = mt_config.setdefault("statistics", {})

            if self._widgets["track_tier_statistics"]:
                stats_config["track_tier_stats"] = self._widgets["track_tier_statistics"].get_active()

            if self._widgets["log_tracker_failures"]:
                stats_config["log_failures"] = self._widgets["log_tracker_failures"].get_active()

            if self._widgets["log_tier_changes"]:
                stats_config["log_tier_changes"] = self._widgets["log_tier_changes"].get_active()

            # Update the protocols config
            protocols_config["multi_tracker"] = mt_config
            settings["protocols"] = protocols_config

        except Exception as e:
            self.logger.error(
                f"Failed to collect Multi-Tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

        return settings

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Multi-Tracker settings"""
        errors = {}

        try:
            # Validate max consecutive failures
            max_failures_widget = self._widgets.get("max_consecutive_failures")
            if max_failures_widget:
                failures = max_failures_widget.get_value()
                if failures < 1:
                    errors["max_consecutive_failures"] = "Must allow at least 1 failure before disabling tracker"
                elif failures > 20:
                    errors["max_consecutive_failures"] = "Warning: Very high failure threshold may delay failover"

            # Validate backoff settings
            backoff_base_widget = self._widgets.get("backoff_base_seconds")
            max_backoff_widget = self._widgets.get("max_backoff_seconds")
            if backoff_base_widget and max_backoff_widget:
                base = backoff_base_widget.get_value()
                max_backoff = max_backoff_widget.get_value()

                if base >= max_backoff:
                    errors["backoff_base_seconds"] = "Base backoff must be less than maximum backoff"

                if base < 10:
                    errors["backoff_base_seconds"] = "Warning: Very low backoff may cause excessive retry attempts"

            # Validate response time smoothing
            smoothing_widget = self._widgets.get("response_time_smoothing")
            if smoothing_widget:
                smoothing = smoothing_widget.get_value()
                if smoothing < 0.0 or smoothing > 1.0:
                    errors["response_time_smoothing"] = "Smoothing factor must be between 0.0 and 1.0"

            # Validate rotation interval
            rotation_widget = self._widgets.get("rotation_interval_seconds")
            if rotation_widget:
                interval = rotation_widget.get_value()
                if interval < 60:
                    errors["rotation_interval_seconds"] = "Warning: Very short rotation interval may cause instability"

            # Check for conflicting settings
            announce_all_tiers_widget = self._widgets.get("announce_to_all_tiers")
            failover_widget = self._widgets.get("failover_enabled")
            if (
                announce_all_tiers_widget
                and announce_all_tiers_widget.get_active()
                and failover_widget
                and failover_widget.get_active()
            ):
                errors["announce_to_all_tiers"] = "Info: Announcing to all tiers makes failover less relevant"

        except Exception as e:
            self.logger.error(
                f"Multi-Tracker settings validation failed: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            errors["general"] = f"Validation error: {str(e)}"

        return errors

    def _update_tab_dependencies(self):
        """Update UI element dependencies"""
        try:
            # Multi-tracker enabled state
            if self._widgets["multi_tracker_enabled"]:
                enabled = self._widgets["multi_tracker_enabled"].get_state()

                # Enable/disable all multi-tracker widgets based on main switch
                dependent_widgets = [
                    "failover_enabled",
                    "announce_to_all_tiers",
                    "announce_to_all_in_tier",
                    "health_monitoring_enabled",
                    "track_tier_statistics",
                ]

                for widget_name in dependent_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(enabled)

            # Failover enabled state
            if self._widgets["failover_enabled"]:
                failover_enabled = self._widgets["failover_enabled"].get_active()

                failover_widgets = [
                    "max_consecutive_failures",
                    "backoff_base_seconds",
                    "max_backoff_seconds",
                    "auto_disable_failed_trackers",
                ]

                for widget_name in failover_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(failover_enabled)

            # Health monitoring enabled state
            if self._widgets["health_monitoring_enabled"]:
                health_enabled = self._widgets["health_monitoring_enabled"].get_active()

                health_widgets = ["response_time_tracking", "response_time_smoothing"]

                for widget_name in health_widgets:
                    if self._widgets.get(widget_name):
                        self._widgets[widget_name].set_sensitive(health_enabled)

            # Tracker rotation enabled state
            if self._widgets["tracker_rotation_enabled"]:
                rotation_enabled = self._widgets["tracker_rotation_enabled"].get_active()

                if self._widgets.get("rotation_interval_seconds"):
                    self._widgets["rotation_interval_seconds"].set_sensitive(rotation_enabled)

        except Exception as e:
            self.logger.error(
                f"Failed to update Multi-Tracker dependencies: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    # Signal handlers
    def _on_multi_tracker_enabled_changed(self, switch, state):
        """Handle Multi-Tracker enable/disable toggle"""
        self.logger.debug(
            f"Multi-Tracker enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def _on_failover_enabled_toggled(self, check_button):
        """Handle failover enable toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Failover enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def _on_max_consecutive_failures_changed(self, spin_button):
        """Handle max consecutive failures changes"""
        failures = spin_button.get_value()
        self.logger.debug(
            f"Max consecutive failures: {failures}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_backoff_base_seconds_changed(self, spin_button):
        """Handle backoff base seconds changes"""
        seconds = spin_button.get_value()
        self.logger.debug(
            f"Backoff base seconds: {seconds}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_max_backoff_seconds_changed(self, spin_button):
        """Handle max backoff seconds changes"""
        seconds = spin_button.get_value()
        self.logger.debug(
            f"Max backoff seconds: {seconds}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_announce_to_all_tiers_toggled(self, check_button):
        """Handle announce to all tiers toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Announce to all tiers: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_announce_to_all_in_tier_toggled(self, check_button):
        """Handle announce to all in tier toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Announce to all in tier: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_health_monitoring_enabled_toggled(self, check_button):
        """Handle health monitoring enable toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Health monitoring enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def _on_response_time_tracking_toggled(self, check_button):
        """Handle response time tracking toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Response time tracking: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_response_time_smoothing_changed(self, spin_button):
        """Handle response time smoothing changes"""
        smoothing = spin_button.get_value()
        self.logger.debug(
            f"Response time smoothing: {smoothing}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_auto_disable_failed_trackers_toggled(self, check_button):
        """Handle auto disable failed trackers toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Auto disable failed trackers: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_tracker_rotation_enabled_toggled(self, check_button):
        """Handle tracker rotation enable toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Tracker rotation enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def _on_rotation_interval_seconds_changed(self, spin_button):
        """Handle rotation interval seconds changes"""
        seconds = spin_button.get_value()
        self.logger.debug(
            f"Rotation interval seconds: {seconds}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_track_tier_statistics_toggled(self, check_button):
        """Handle track tier statistics toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Track tier statistics: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_log_tracker_failures_toggled(self, check_button):
        """Handle log tracker failures toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Log tracker failures: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_log_tier_changes_toggled(self, check_button):
        """Handle log tier changes toggle"""
        enabled = check_button.get_active()
        self.logger.debug(
            f"Log tier changes: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.debug(
            "MultiTrackerTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "MultiTrackerTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "MultiTrackerTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.debug(
            "MultiTrackerTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()
