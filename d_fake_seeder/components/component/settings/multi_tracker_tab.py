"""
Multi-Tracker Settings Tab

Provides configuration interface for Multi-Tracker Support (BEP-012).
Manages tracker tier configuration, failover settings, and announce strategies.
"""

from typing import Any, ClassVar

from d_fake_seeder.lib.gi_gtk4 import GLib

from .base_tab import BaseSettingsTab
from .settings_mixins import (
    NotificationMixin,
    TranslationMixin,
    UtilityMixin,
    ValidationMixin,
)


class MultiTrackerTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """Multi-Tracker (BEP-012) configuration tab"""

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS: ClassVar[list] = [
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
            self._load_basic_and_failover(mt_config)
            self._load_strategy_and_health(mt_config)
            self._load_advanced_and_stats(mt_config)
            self.logger.trace(
                "Multi-Tracker settings loaded successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error):
            self.logger.exception(
                "Failed to load Multi-Tracker settings",
                extra={"class_name": self.__class__.__name__},
            )

    def _load_basic_and_failover(self, mt_config: dict[str, Any]) -> None:
        """Load the basic enable switch and the failover configuration."""
        if self._widgets["multi_tracker_enabled"]:
            self._widgets["multi_tracker_enabled"].set_active(mt_config.get("enabled", True))

        if self._widgets["failover_enabled"]:
            self.set_switch_state(
                self._widgets["failover_enabled"],
                mt_config.get("failover_enabled", True),
            )

        failover_config = mt_config.get("failover", {})
        if self._widgets["max_consecutive_failures"]:
            self._widgets["max_consecutive_failures"].set_value(failover_config.get("max_consecutive_failures", 5))
        if self._widgets["backoff_base_seconds"]:
            self._widgets["backoff_base_seconds"].set_value(failover_config.get("backoff_base_seconds", 60))
        if self._widgets["max_backoff_seconds"]:
            self._widgets["max_backoff_seconds"].set_value(failover_config.get("max_backoff_seconds", 3600))

    def _load_strategy_and_health(self, mt_config: dict[str, Any]) -> None:
        """Load the announce-strategy switches and health-monitoring settings."""
        if self._widgets["announce_to_all_tiers"]:
            self.set_switch_state(
                self._widgets["announce_to_all_tiers"],
                mt_config.get("announce_to_all_tiers", False),
            )
        if self._widgets["announce_to_all_in_tier"]:
            self.set_switch_state(
                self._widgets["announce_to_all_in_tier"],
                mt_config.get("announce_to_all_in_tier", False),
            )

        health_config = mt_config.get("health_monitoring", {})
        if self._widgets["health_monitoring_enabled"]:
            self.set_switch_state(
                self._widgets["health_monitoring_enabled"],
                health_config.get("enabled", True),
            )
        if self._widgets["response_time_tracking"]:
            self.set_switch_state(
                self._widgets["response_time_tracking"],
                health_config.get("track_response_time", True),
            )
        if self._widgets["response_time_smoothing"]:
            self._widgets["response_time_smoothing"].set_value(health_config.get("response_time_smoothing", 0.8))

    def _load_advanced_and_stats(self, mt_config: dict[str, Any]) -> None:
        """Load the advanced switches and statistics settings."""
        advanced_config = mt_config.get("advanced", {})
        if self._widgets["auto_disable_failed_trackers"]:
            self.set_switch_state(
                self._widgets["auto_disable_failed_trackers"],
                advanced_config.get("auto_disable_failed", True),
            )
        if self._widgets["tracker_rotation_enabled"]:
            self.set_switch_state(
                self._widgets["tracker_rotation_enabled"],
                advanced_config.get("rotation_enabled", False),
            )
        if self._widgets["rotation_interval_seconds"]:
            self._widgets["rotation_interval_seconds"].set_value(advanced_config.get("rotation_interval_seconds", 300))

        stats_config = mt_config.get("statistics", {})
        if self._widgets["track_tier_statistics"]:
            self.set_switch_state(
                self._widgets["track_tier_statistics"],
                stats_config.get("track_tier_stats", True),
            )
        if self._widgets["log_tracker_failures"]:
            self.set_switch_state(
                self._widgets["log_tracker_failures"],
                stats_config.get("log_failures", True),
            )
        if self._widgets["log_tier_changes"]:
            self.set_switch_state(
                self._widgets["log_tier_changes"],
                stats_config.get("log_tier_changes", False),
            )

    def _setup_dependencies(self) -> None:
        """Set up dependencies between UI elements"""
        try:
            # Update widget sensitivity based on current state
            self._update_tab_dependencies()
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error):
            self.logger.exception(
                "Failed to setup Multi-Tracker dependencies",
                extra={"class_name": self.__class__.__name__},
            )

    def _collect_settings(self) -> dict[str, Any]:
        """Collect current settings from UI widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        # Collect from WIDGET_MAPPINGS
        settings = self._collect_mapped_settings()

        try:
            self._collect_toggle_settings(settings)
            self._collect_numeric_settings(settings)
            self.logger.trace(f"Collected {len(settings)} settings from Multi-Tracker tab")
        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error):
            self.logger.exception(
                "Failed to collect Multi-Tracker settings",
                extra={"class_name": self.__class__.__name__},
            )

        return settings

    def _collect_toggle_settings(self, settings: dict[str, Any]) -> None:
        """Collect the on/off switch values into ``settings``."""
        toggles = [
            ("multi_tracker_enabled", "protocols.multi_tracker.enabled"),
            ("failover_enabled", "protocols.multi_tracker.failover_enabled"),
            ("announce_to_all_tiers", "protocols.multi_tracker.announce_to_all_tiers"),
            ("announce_to_all_in_tier", "protocols.multi_tracker.announce_to_all_in_tier"),
            ("health_monitoring_enabled", "protocols.multi_tracker.health_monitoring.enabled"),
            ("response_time_tracking", "protocols.multi_tracker.health_monitoring.track_response_time"),
            ("auto_disable_failed_trackers", "protocols.multi_tracker.advanced.auto_disable_failed"),
            ("tracker_rotation_enabled", "protocols.multi_tracker.advanced.rotation_enabled"),
            ("track_tier_statistics", "protocols.multi_tracker.statistics.track_tier_stats"),
            ("log_tracker_failures", "protocols.multi_tracker.statistics.log_failures"),
            ("log_tier_changes", "protocols.multi_tracker.statistics.log_tier_changes"),
        ]
        for widget_id, key in toggles:
            if self._widgets.get(widget_id):
                settings[key] = self._widgets[widget_id].get_active()

    def _collect_numeric_settings(self, settings: dict[str, Any]) -> None:
        """Collect the integer spin values and the response-time smoothing float."""
        integers = [
            ("max_consecutive_failures", "protocols.multi_tracker.failover.max_consecutive_failures"),
            ("backoff_base_seconds", "protocols.multi_tracker.failover.backoff_base_seconds"),
            ("max_backoff_seconds", "protocols.multi_tracker.failover.max_backoff_seconds"),
            ("rotation_interval_seconds", "protocols.multi_tracker.advanced.rotation_interval_seconds"),
        ]
        for widget_id, key in integers:
            if self._widgets.get(widget_id):
                settings[key] = int(self._widgets[widget_id].get_value())

        if self._widgets.get("response_time_smoothing"):
            settings["protocols.multi_tracker.health_monitoring.response_time_smoothing"] = self._widgets[
                "response_time_smoothing"
            ].get_value()

    def _validate_tab_settings(self) -> dict[str, str]:
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

        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error) as e:
            self.logger.exception(
                "Multi-Tracker settings validation failed",
                extra={"class_name": self.__class__.__name__},
            )
            errors["general"] = f"Validation error: {e!s}"

        return errors

    def _update_tab_dependencies(self) -> None:
        """Update UI element dependencies"""
        try:
            # Multi-tracker enabled state
            if self._widgets["multi_tracker_enabled"]:
                enabled = self._widgets["multi_tracker_enabled"].get_active()

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

        except (AttributeError, TypeError, ValueError, KeyError, IndexError, GLib.Error):
            self.logger.exception(
                "Failed to update Multi-Tracker dependencies",
                extra={"class_name": self.__class__.__name__},
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
