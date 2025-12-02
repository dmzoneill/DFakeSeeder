"""
Speed settings tab for the settings dialog.
Handles upload/download limits, alternative speeds, and scheduler configuration.
"""

# isort: skip_file

# fmt: off
from typing import Any, Dict

import gi

from d_fake_seeder.lib.logger import logger

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import UtilityMixin, ValidationMixin  # noqa: E402

# fmt: on


class SpeedTab(BaseSettingsTab, NotificationMixin, ValidationMixin, UtilityMixin):
    """
    Speed settings tab component.
    Manages:
    - Global upload and download limits
    - Alternative speed settings
    - Speed scheduler configuration
    """

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Speed"

    def _init_widgets(self) -> None:
        """Initialize Speed tab widgets."""
        logger.debug("Starting widget initialization", "SpeedTab")
        # Cache commonly used widgets
        widgets_to_get = [
            ("upload_limit", "settings_upload_limit"),
            ("download_limit", "settings_download_limit"),
            ("enable_alt_speeds", "settings_enable_alt_speeds"),
            ("alt_upload_limit", "settings_alt_upload_limit"),
            ("alt_download_limit", "settings_alt_download_limit"),
            ("enable_scheduler", "settings_enable_scheduler"),
            ("scheduler_start_time", "settings_scheduler_start_time"),
            ("scheduler_end_time", "settings_scheduler_end_time"),
            ("scheduler_days", "settings_scheduler_days"),
        ]
        for widget_name, object_id in widgets_to_get:
            logger.debug("Getting widget:", "SpeedTab")
            try:
                widget = self.builder.get_object(object_id)
                self._widgets[widget_name] = widget
                logger.debug("Successfully got widget:", "SpeedTab")
            except Exception:
                logger.debug("ERROR getting widget :", "SpeedTab")
        logger.debug("Completed widget initialization", "SpeedTab")

    def _connect_signals(self) -> None:
        """Connect signal handlers for Speed tab."""
        # Global limits
        upload_limit = self.get_widget("upload_limit")
        if upload_limit:
            self.track_signal(
                upload_limit,
                upload_limit.connect("value-changed", self.on_upload_limit_changed),
            )

        download_limit = self.get_widget("download_limit")
        if download_limit:
            self.track_signal(
                download_limit,
                download_limit.connect("value-changed", self.on_download_limit_changed),
            )

        # Alternative speeds
        enable_alt = self.get_widget("enable_alt_speeds")
        if enable_alt:
            self.track_signal(
                enable_alt,
                enable_alt.connect("state-set", self.on_enable_alt_speeds_changed),
            )

        alt_upload_limit = self.get_widget("alt_upload_limit")
        if alt_upload_limit:
            self.track_signal(
                alt_upload_limit,
                alt_upload_limit.connect("value-changed", self.on_alt_upload_limit_changed),
            )

        alt_download_limit = self.get_widget("alt_download_limit")
        if alt_download_limit:
            self.track_signal(
                alt_download_limit,
                alt_download_limit.connect("value-changed", self.on_alt_download_limit_changed),
            )

        # Scheduler
        enable_scheduler = self.get_widget("enable_scheduler")
        if enable_scheduler:
            self.track_signal(
                enable_scheduler,
                enable_scheduler.connect("state-set", self.on_enable_scheduler_changed),
            )

        scheduler_start_time = self.get_widget("scheduler_start_time")
        if scheduler_start_time:
            self.track_signal(
                scheduler_start_time,
                scheduler_start_time.connect("notify::time", self.on_scheduler_start_time_changed),
            )

        scheduler_end_time = self.get_widget("scheduler_end_time")
        if scheduler_end_time:
            self.track_signal(
                scheduler_end_time,
                scheduler_end_time.connect("notify::time", self.on_scheduler_end_time_changed),
            )

        scheduler_days = self.get_widget("scheduler_days")
        if scheduler_days:
            self.track_signal(
                scheduler_days,
                scheduler_days.connect("changed", self.on_scheduler_days_changed),
            )

    # Note: _disconnect_signals() is no longer needed - CleanupMixin handles it automatically

    def _load_settings(self) -> None:
        """Load current settings into Speed tab widgets."""
        logger.debug("Starting _load_settings", "SpeedTab")
        try:
            # Load speed settings
            logger.debug("Getting speed settings from app_settings", "SpeedTab")
            speed_settings = getattr(self.app_settings, "speed", {})
            logger.debug("Got speed settings:", "SpeedTab")
            logger.debug("About to call _load_speed_settings", "SpeedTab")
            self._load_speed_settings(speed_settings)
            logger.debug("Completed _load_speed_settings", "SpeedTab")
            # Load scheduler settings
            logger.debug("Getting scheduler settings from app_settings", "SpeedTab")
            scheduler_settings = getattr(self.app_settings, "scheduler", {})
            logger.debug("Got scheduler settings:", "SpeedTab")
            logger.debug("About to call _load_scheduler_settings", "SpeedTab")
            self._load_scheduler_settings(scheduler_settings)
            logger.debug("Completed _load_scheduler_settings", "SpeedTab")
            self.logger.debug("Speed tab settings loaded")
            logger.debug("Completed _load_settings successfully", "SpeedTab")
        except Exception as e:
            logger.debug("ERROR in _load_settings:", "SpeedTab")
            self.logger.error(f"Error loading Speed tab settings: {e}")

    def _load_speed_settings(self, speed_settings: Dict[str, Any]) -> None:
        """Load speed-related settings."""
        logger.debug("Starting _load_speed_settings", "SpeedTab")
        try:
            # Global limits (0 = unlimited)
            logger.debug("Getting upload_limit widget", "SpeedTab")
            upload_limit = self.get_widget("upload_limit")
            if upload_limit:
                logger.debug("Setting upload_limit value to", "SpeedTab")
                upload_limit.set_value(speed_settings.get("upload_limit_kbps", 0))
                logger.debug("Upload limit value set successfully", "SpeedTab")
            logger.debug("Getting download_limit widget", "SpeedTab")
            download_limit = self.get_widget("download_limit")
            if download_limit:
                logger.debug("Setting download_limit value to", "SpeedTab")
                download_limit.set_value(speed_settings.get("download_limit_kbps", 0))
                logger.debug("Download limit value set successfully", "SpeedTab")
            # Alternative speeds
            logger.debug("Getting enable_alt_speeds widget", "SpeedTab")
            enable_alt = self.get_widget("enable_alt_speeds")
            if enable_alt:
                logger.debug("Setting enable_alt_speeds active to", "SpeedTab")
                enable_alt.set_active(speed_settings.get("enable_alternative_speeds", False))
                logger.debug("Enable alt speeds set successfully", "SpeedTab")
            logger.debug("Getting alt_upload_limit widget", "SpeedTab")
            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                logger.debug("Setting alt_upload_limit value to", "SpeedTab")
                alt_upload_limit.set_value(speed_settings.get("alt_upload_limit_kbps", 0))
                logger.debug("Alt upload limit value set successfully", "SpeedTab")
            logger.debug("Getting alt_download_limit widget", "SpeedTab")
            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                logger.debug(
                    "Setting alt_download_limit value to {speed_settings.get('alt_download_limit_kbps', 0)}",
                    "UnknownClass",
                )
                alt_download_limit.set_value(speed_settings.get("alt_download_limit_kbps", 0))
                logger.debug("Alt download limit value set successfully", "SpeedTab")
            logger.debug("Completed _load_speed_settings successfully", "SpeedTab")
        except Exception as e:
            logger.debug("ERROR in _load_speed_settings:", "SpeedTab")
            self.logger.error(f"Error loading speed settings: {e}")

    def _load_scheduler_settings(self, scheduler_settings: Dict[str, Any]) -> None:
        """Load scheduler settings."""
        try:
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                enable_scheduler.set_active(scheduler_settings.get("enabled", False))
            # Time settings (these would need specific widget implementations)
            scheduler_start_time = self.get_widget("scheduler_start_time")
            if scheduler_start_time:
                # Set time on widget (implementation depends on widget type)
                # start_time = scheduler_settings.get("start_time", "22:00")
                pass
            scheduler_end_time = self.get_widget("scheduler_end_time")
            if scheduler_end_time:
                # Set time on widget (implementation depends on widget type)
                # end_time = scheduler_settings.get("end_time", "06:00")
                pass
            scheduler_days = self.get_widget("scheduler_days")
            if scheduler_days:
                # Set selected days (implementation depends on widget type)
                # days = scheduler_settings.get("days", [])
                pass
        except Exception as e:
            self.logger.error(f"Error loading scheduler settings: {e}")

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Speed tab."""
        self._update_speed_dependencies()

    def _update_tab_dependencies(self) -> None:
        """Update Speed tab dependencies."""
        self._update_speed_dependencies()

    def _update_speed_dependencies(self) -> None:
        """Update speed-related widget dependencies."""
        try:
            # Enable/disable alternative speed controls
            enable_alt = self.get_widget("enable_alt_speeds")
            alt_enabled = enable_alt and enable_alt.get_active()
            self.update_widget_sensitivity("alt_upload_limit", alt_enabled)
            self.update_widget_sensitivity("alt_download_limit", alt_enabled)
            # Enable/disable scheduler controls
            enable_scheduler = self.get_widget("enable_scheduler")
            scheduler_enabled = enable_scheduler and enable_scheduler.get_active()
            self.update_widget_sensitivity("scheduler_start_time", scheduler_enabled)
            self.update_widget_sensitivity("scheduler_end_time", scheduler_enabled)
            self.update_widget_sensitivity("scheduler_days", scheduler_enabled)
        except Exception as e:
            self.logger.error(f"Error updating speed dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Speed tab widgets."""
        settings = {}
        try:
            # Collect speed settings
            settings["speed"] = self._collect_speed_settings()
            settings["scheduler"] = self._collect_scheduler_settings()
        except Exception as e:
            self.logger.error(f"Error collecting Speed tab settings: {e}")
        return settings

    def _collect_speed_settings(self) -> Dict[str, Any]:
        """Collect speed-related settings."""
        speed_settings = {}
        try:
            upload_limit = self.get_widget("upload_limit")
            if upload_limit:
                speed_settings["upload_limit_kbps"] = int(upload_limit.get_value())
            download_limit = self.get_widget("download_limit")
            if download_limit:
                speed_settings["download_limit_kbps"] = int(download_limit.get_value())
            enable_alt = self.get_widget("enable_alt_speeds")
            if enable_alt:
                speed_settings["enable_alternative_speeds"] = enable_alt.get_active()
            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                speed_settings["alt_upload_limit_kbps"] = int(alt_upload_limit.get_value())
            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                speed_settings["alt_download_limit_kbps"] = int(alt_download_limit.get_value())
        except Exception as e:
            self.logger.error(f"Error collecting speed settings: {e}")
        return speed_settings

    def _collect_scheduler_settings(self) -> Dict[str, Any]:
        """Collect scheduler settings."""
        scheduler_settings = {}
        try:
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                scheduler_settings["enabled"] = enable_scheduler.get_active()
            # Time and day settings would need specific widget implementations
            scheduler_start_time = self.get_widget("scheduler_start_time")
            if scheduler_start_time:
                # Get time from widget (implementation depends on widget type)
                scheduler_settings["start_time"] = "22:00"  # Default/placeholder
            scheduler_end_time = self.get_widget("scheduler_end_time")
            if scheduler_end_time:
                # Get time from widget (implementation depends on widget type)
                scheduler_settings["end_time"] = "06:00"  # Default/placeholder
            scheduler_days = self.get_widget("scheduler_days")
            if scheduler_days:
                # Get selected days (implementation depends on widget type)
                scheduler_settings["days"] = []  # Default/placeholder
        except Exception as e:
            self.logger.error(f"Error collecting scheduler settings: {e}")
        return scheduler_settings

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Speed tab settings."""
        errors = {}
        try:
            # Validate that limits are non-negative
            upload_limit = self.get_widget("upload_limit")
            if upload_limit:
                limit_errors = self.validate_positive_number(upload_limit.get_value(), "upload_limit")
                errors.update(limit_errors)
            download_limit = self.get_widget("download_limit")
            if download_limit:
                limit_errors = self.validate_positive_number(download_limit.get_value(), "download_limit")
                errors.update(limit_errors)
            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                limit_errors = self.validate_positive_number(alt_upload_limit.get_value(), "alt_upload_limit")
                errors.update(limit_errors)
            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                limit_errors = self.validate_positive_number(alt_download_limit.get_value(), "alt_download_limit")
                errors.update(limit_errors)
        except Exception as e:
            self.logger.error(f"Error validating Speed tab settings: {e}")
            errors["general"] = str(e)
        return errors

    # Signal handlers
    def on_upload_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle upload limit change."""
        try:
            limit = int(spin_button.get_value())
            self.app_settings.set("speed.upload_limit_kbps", limit)
            self.logger.debug(f"Upload limit changed to: {limit} kbps")
        except Exception as e:
            self.logger.error(f"Error changing upload limit: {e}")

    def on_download_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle download limit change."""
        try:
            limit = int(spin_button.get_value())
            self.app_settings.set("speed.download_limit_kbps", limit)
            self.logger.debug(f"Download limit changed to: {limit} kbps")
        except Exception as e:
            self.logger.error(f"Error changing download limit: {e}")

    def on_enable_alt_speeds_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle alternative speeds toggle."""
        try:
            self.update_dependencies()
            self.app_settings.set("speed.enable_alternative_speeds", state)
            message = "Alternative speeds enabled" if state else "Alternative speeds disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing alternative speeds setting: {e}")

    def on_alt_upload_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle alternative upload limit change."""
        try:
            limit = int(spin_button.get_value())
            self.app_settings.set("speed.alt_upload_limit_kbps", limit)
            self.logger.debug(f"Alternative upload limit changed to: {limit} kbps")
        except Exception as e:
            self.logger.error(f"Error changing alternative upload limit: {e}")

    def on_alt_download_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle alternative download limit change."""
        try:
            limit = int(spin_button.get_value())
            self.app_settings.set("speed.alt_download_limit_kbps", limit)
            self.logger.debug(f"Alternative download limit changed to: {limit} kbps")
        except Exception as e:
            self.logger.error(f"Error changing alternative download limit: {e}")

    def on_enable_scheduler_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle scheduler toggle."""
        try:
            self.update_dependencies()
            self.app_settings.set("scheduler.enabled", state)
            message = "Speed scheduler enabled" if state else "Speed scheduler disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing scheduler setting: {e}")

    def on_scheduler_start_time_changed(self, widget, param) -> None:
        """Handle scheduler start time change."""
        try:
            # Implementation depends on the specific time widget used
            # This is a placeholder for the actual time handling
            self.app_settings.set("scheduler.start_time", "22:00")
            self.logger.debug("Scheduler start time changed")
        except Exception as e:
            self.logger.error(f"Error changing scheduler start time: {e}")

    def on_scheduler_end_time_changed(self, widget, param) -> None:
        """Handle scheduler end time change."""
        try:
            # Implementation depends on the specific time widget used
            # This is a placeholder for the actual time handling
            self.app_settings.set("scheduler.end_time", "06:00")
            self.logger.debug("Scheduler end time changed")
        except Exception as e:
            self.logger.error(f"Error changing scheduler end time: {e}")

    def on_scheduler_days_changed(self, widget) -> None:
        """Handle scheduler days change."""
        try:
            # Implementation depends on the specific days selection widget used
            # This is a placeholder for the actual days handling
            self.app_settings.set("scheduler.days", [])
            self.logger.debug("Scheduler days changed")
        except Exception as e:
            self.logger.error(f"Error changing scheduler days: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset Speed tab to default values."""
        try:
            # Reset global limits to unlimited (0)
            upload_limit = self.get_widget("upload_limit")
            if upload_limit:
                upload_limit.set_value(0)
            download_limit = self.get_widget("download_limit")
            if download_limit:
                download_limit.set_value(0)
            # Reset alternative speeds
            enable_alt = self.get_widget("enable_alt_speeds")
            if enable_alt:
                enable_alt.set_active(False)
            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                alt_upload_limit.set_value(0)
            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                alt_download_limit.set_value(0)
            # Reset scheduler
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                enable_scheduler.set_active(False)
            self.update_dependencies()
            self.show_notification("Speed settings reset to defaults", "success")
        except Exception as e:
            self.logger.error(f"Error resetting Speed tab to defaults: {e}")

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.debug(
            "SpeedTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "SpeedTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "SpeedTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.debug(
            "SpeedTab update view",
            extra={"class_name": self.__class__.__name__},
        )
