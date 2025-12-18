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
from .settings_mixins import UtilityMixin  # noqa: E402
from .settings_mixins import ValidationMixin  # noqa: E402

# fmt: on


class MultiTrackerTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """Multi-Tracker (BEP-012) configuration tab"""

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS = [
        # Failover settings
        {
            "id": "max_consecutive_failures_spin",
            "name": "max_consecutive_failures",
            "setting_key": "protocols.multi_tracker.failover.max_consecutive_failures",
            "type": int,
        },
        {
            "id": "backoff_base_seconds_spin",
            "name": "backoff_base_seconds",
            "setting_key": "protocols.multi_tracker.failover.backoff_base_seconds",
            "type": int,
        },
        {
            "id": "max_backoff_seconds_spin",
            "name": "max_backoff_seconds",
            "setting_key": "protocols.multi_tracker.failover.max_backoff_seconds",
            "type": int,
        },
        # Announce strategy
        {
            "id": "announce_to_all_tiers_check",
            "name": "announce_to_all_tiers",
            "setting_key": "protocols.multi_tracker.announce_to_all_tiers",
            "type": bool,
        },
        {
            "id": "announce_to_all_in_tier_check",
            "name": "announce_to_all_in_tier",
            "setting_key": "protocols.multi_tracker.announce_to_all_in_tier",
            "type": bool,
        },
        # Health monitoring
        {
            "id": "response_time_tracking_check",
            "name": "response_time_tracking",
            "setting_key": "protocols.multi_tracker.health_monitoring.track_response_time",
            "type": bool,
        },
        {
            "id": "response_time_smoothing_spin",
            "name": "response_time_smoothing",
            "setting_key": "protocols.multi_tracker.health_monitoring.response_time_smoothing",
            "type": float,
        },
        # Advanced settings
        {
            "id": "auto_disable_failed_trackers_check",
            "name": "auto_disable_failed_trackers",
            "setting_key": "protocols.multi_tracker.advanced.auto_disable_failed",
            "type": bool,
        },
        {
            "id": "rotation_interval_seconds_spin",
            "name": "rotation_interval_seconds",
            "setting_key": "protocols.multi_tracker.advanced.rotation_interval_seconds",
            "type": int,
        },
        # Statistics settings
        {
            "id": "track_tier_statistics_check",
            "name": "track_tier_statistics",
            "setting_key": "protocols.multi_tracker.statistics.track_tier_stats",
            "type": bool,
        },
        {
            "id": "log_tracker_failures_check",
            "name": "log_tracker_failures",
            "setting_key": "protocols.multi_tracker.statistics.log_failures",
            "type": bool,
        },
        {
            "id": "log_tier_changes_check",
            "name": "log_tier_changes",
            "setting_key": "protocols.multi_tracker.statistics.log_tier_changes",
            "type": bool,
        },
    ]

    @property
    def tab_name(self) -> str:
        """Return the name of this tab"""
        return "Multi-Tracker"

    def _init_widgets(self) -> None:
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

        self.logger.trace(
            "Multi-Tracker tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _connect_signals(self) -> None:
        """Connect Multi-Tracker specific signals"""
        # Simple widgets (max_consecutive_failures, backoff_base_seconds, max_backoff_seconds,
        # announce_to_all_tiers, announce_to_all_in_tier, response_time_tracking,
        # response_time_smoothing, auto_disable_failed_trackers, rotation_interval_seconds,
        # track_tier_statistics, log_tracker_failures, log_tier_changes) are now auto-connected via WIDGET_MAPPINGS

        # Enable/Disable Multi-Tracker (has dependencies - controls child widget sensitivity)
        if self._widgets["multi_tracker_enabled"]:
            self._widgets["multi_tracker_enabled"].connect("state-set", self._on_multi_tracker_enabled_changed)

        # Failover enabled (has dependencies - controls failover-related widgets)
        if self._widgets["failover_enabled"]:
            self._widgets["failover_enabled"].connect("toggled", self._on_failover_enabled_toggled)

        # Health monitoring enabled (has dependencies - controls health monitoring widgets)
        if self._widgets["health_monitoring_enabled"]:
            self._widgets["health_monitoring_enabled"].connect("toggled", self._on_health_monitoring_enabled_toggled)

        # Tracker rotation enabled (has dependencies - controls rotation interval widget)
        if self._widgets["tracker_rotation_enabled"]:
            self._widgets["tracker_rotation_enabled"].connect("toggled", self._on_tracker_rotation_enabled_toggled)

        self.logger.trace(
            "Multi-Tracker tab signals connected",
            extra={"class_name": self.__class__.__name__},
        )

    def _load_settings(self) -> None:
        """Load Multi-Tracker settings from configuration"""
        try:
            protocols_config = getattr(self.app_settings, "protocols", {})
            mt_config = protocols_config.get("multi_tracker", {})

            # Basic Multi-Tracker settings
            if self._widgets["multi_tracker_enabled"]:
                self._widgets["multi_tracker_enabled"].set_state(mt_config.get("enabled", True))

            # Failover configuration
            if self._widgets["failover_enabled"]:
                self.set_switch_state(self._widgets["failover_enabled"], mt_config.get("failover_enabled", True))

            failover_config = mt_config.get("failover", {})

            if self._widgets["max_consecutive_failures"]:
                self._widgets["max_consecutive_failures"].set_value(failover_config.get("max_consecutive_failures", 5))

            if self._widgets["backoff_base_seconds"]:
                self._widgets["backoff_base_seconds"].set_value(failover_config.get("backoff_base_seconds", 60))

            if self._widgets["max_backoff_seconds"]:
                self._widgets["max_backoff_seconds"].set_value(failover_config.get("max_backoff_seconds", 3600))

            # Announce strategy
            if self._widgets["announce_to_all_tiers"]:
                self.set_switch_state(
                    self._widgets["announce_to_all_tiers"], mt_config.get("announce_to_all_tiers", False)
                )

            if self._widgets["announce_to_all_in_tier"]:
                self.set_switch_state(
                    self._widgets["announce_to_all_in_tier"], mt_config.get("announce_to_all_in_tier", False)
                )

            # Health monitoring
            health_config = mt_config.get("health_monitoring", {})

            if self._widgets["health_monitoring_enabled"]:
                self.set_switch_state(self._widgets["health_monitoring_enabled"], health_config.get("enabled", True))

            if self._widgets["response_time_tracking"]:
                self.set_switch_state(
                    self._widgets["response_time_tracking"], health_config.get("track_response_time", True)
                )

            if self._widgets["response_time_smoothing"]:
                self._widgets["response_time_smoothing"].set_value(health_config.get("response_time_smoothing", 0.8))

            # Advanced settings
            advanced_config = mt_config.get("advanced", {})

            if self._widgets["auto_disable_failed_trackers"]:
                self.set_switch_state(
                    self._widgets["auto_disable_failed_trackers"], advanced_config.get("auto_disable_failed", True)
                )

            if self._widgets["tracker_rotation_enabled"]:
                self.set_switch_state(
                    self._widgets["tracker_rotation_enabled"], advanced_config.get("rotation_enabled", False)
                )

            if self._widgets["rotation_interval_seconds"]:
                self._widgets["rotation_interval_seconds"].set_value(
                    advanced_config.get("rotation_interval_seconds", 300)
                )

            # Statistics settings
            stats_config = mt_config.get("statistics", {})

            if self._widgets["track_tier_statistics"]:
                self.set_switch_state(
                    self._widgets["track_tier_statistics"], stats_config.get("track_tier_stats", True)
                )

            if self._widgets["log_tracker_failures"]:
                self.set_switch_state(self._widgets["log_tracker_failures"], stats_config.get("log_failures", True))

            if self._widgets["log_tier_changes"]:
                self.set_switch_state(self._widgets["log_tier_changes"], stats_config.get("log_tier_changes", False))

            self.logger.trace(
                "Multi-Tracker settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            self.logger.error(
                f"Failed to load Multi-Tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def _setup_dependencies(self) -> None:
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
        """Collect current settings from UI widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        # Collect from WIDGET_MAPPINGS
        settings = self._collect_mapped_settings()

        try:
            # Basic settings
            if self._widgets.get("multi_tracker_enabled"):
                settings["protocols.multi_tracker.enabled"] = self._widgets["multi_tracker_enabled"].get_state()

            # Failover settings
            if self._widgets.get("failover_enabled"):
                settings["protocols.multi_tracker.failover_enabled"] = self._widgets["failover_enabled"].get_active()

            if self._widgets.get("max_consecutive_failures"):
                settings["protocols.multi_tracker.failover.max_consecutive_failures"] = int(
                    self._widgets["max_consecutive_failures"].get_value()
                )

            if self._widgets.get("backoff_base_seconds"):
                settings["protocols.multi_tracker.failover.backoff_base_seconds"] = int(
                    self._widgets["backoff_base_seconds"].get_value()
                )

            if self._widgets.get("max_backoff_seconds"):
                settings["protocols.multi_tracker.failover.max_backoff_seconds"] = int(
                    self._widgets["max_backoff_seconds"].get_value()
                )

            # Announce strategy
            if self._widgets.get("announce_to_all_tiers"):
                settings["protocols.multi_tracker.announce_to_all_tiers"] = self._widgets[
                    "announce_to_all_tiers"
                ].get_active()

            if self._widgets.get("announce_to_all_in_tier"):
                settings["protocols.multi_tracker.announce_to_all_in_tier"] = self._widgets[
                    "announce_to_all_in_tier"
                ].get_active()

            # Health monitoring
            if self._widgets.get("health_monitoring_enabled"):
                settings["protocols.multi_tracker.health_monitoring.enabled"] = self._widgets[
                    "health_monitoring_enabled"
                ].get_active()

            if self._widgets.get("response_time_tracking"):
                settings["protocols.multi_tracker.health_monitoring.track_response_time"] = self._widgets[
                    "response_time_tracking"
                ].get_active()

            if self._widgets.get("response_time_smoothing"):
                settings["protocols.multi_tracker.health_monitoring.response_time_smoothing"] = self._widgets[
                    "response_time_smoothing"
                ].get_value()

            # Advanced settings
            if self._widgets.get("auto_disable_failed_trackers"):
                settings["protocols.multi_tracker.advanced.auto_disable_failed"] = self._widgets[
                    "auto_disable_failed_trackers"
                ].get_active()

            if self._widgets.get("tracker_rotation_enabled"):
                settings["protocols.multi_tracker.advanced.rotation_enabled"] = self._widgets[
                    "tracker_rotation_enabled"
                ].get_active()

            if self._widgets.get("rotation_interval_seconds"):
                settings["protocols.multi_tracker.advanced.rotation_interval_seconds"] = int(
                    self._widgets["rotation_interval_seconds"].get_value()
                )

            # Statistics settings
            if self._widgets.get("track_tier_statistics"):
                settings["protocols.multi_tracker.statistics.track_tier_stats"] = self._widgets[
                    "track_tier_statistics"
                ].get_active()

            if self._widgets.get("log_tracker_failures"):
                settings["protocols.multi_tracker.statistics.log_failures"] = self._widgets[
                    "log_tracker_failures"
                ].get_active()

            if self._widgets.get("log_tier_changes"):
                settings["protocols.multi_tracker.statistics.log_tier_changes"] = self._widgets[
                    "log_tier_changes"
                ].get_active()

            self.logger.trace(f"Collected {len(settings)} settings from Multi-Tracker tab")

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

    def _update_tab_dependencies(self) -> None:
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
    def _on_multi_tracker_enabled_changed(self, switch: Any, state: Any) -> None:
        """Handle Multi-Tracker enable/disable toggle"""
        self.logger.trace(
            f"Multi-Tracker enabled changed: {state}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def _on_failover_enabled_toggled(self, check_button: Any) -> None:
        """Handle failover enable toggle"""
        enabled = check_button.get_active()
        self.logger.trace(
            f"Failover enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def _on_health_monitoring_enabled_toggled(self, check_button: Any) -> None:
        """Handle health monitoring enable toggle"""
        enabled = check_button.get_active()
        self.logger.trace(
            f"Health monitoring enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def _on_tracker_rotation_enabled_toggled(self, check_button: Any) -> None:
        """Handle tracker rotation enable toggle"""
        enabled = check_button.get_active()
        self.logger.trace(
            f"Tracker rotation enabled: {enabled}",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_dependencies()

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace(
            "MultiTrackerTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()
