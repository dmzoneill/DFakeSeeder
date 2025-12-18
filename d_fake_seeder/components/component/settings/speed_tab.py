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

    # Note: Most speed settings use manual loading/saving due to nested structure
    # and scheduler uses individual widgets for hours/minutes/days
    WIDGET_MAPPINGS: list = []

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Speed"

    def _init_widgets(self) -> None:
        """Initialize Speed tab widgets."""
        logger.trace("Starting widget initialization", "SpeedTab")
        # Cache commonly used widgets
        widgets_to_get = [
            # Global speed limits
            ("upload_limit", "settings_upload_limit"),
            ("download_limit", "settings_download_limit"),
            # Alternative speed settings
            ("enable_alt_speeds", "settings_enable_alt_speeds"),
            ("alt_speed_box", "settings_alt_speed_box"),
            ("alt_upload_limit", "settings_alt_upload_limit"),
            ("alt_download_limit", "settings_alt_download_limit"),
            # Scheduler settings
            ("enable_scheduler", "settings_enable_scheduler"),
            ("scheduler_box", "settings_scheduler_box"),
            ("scheduler_start_hour", "settings_scheduler_start_hour"),
            ("scheduler_start_minute", "settings_scheduler_start_minute"),
            ("scheduler_end_hour", "settings_scheduler_end_hour"),
            ("scheduler_end_minute", "settings_scheduler_end_minute"),
            # Scheduler day checkbuttons
            ("scheduler_mon", "settings_scheduler_mon"),
            ("scheduler_tue", "settings_scheduler_tue"),
            ("scheduler_wed", "settings_scheduler_wed"),
            ("scheduler_thu", "settings_scheduler_thu"),
            ("scheduler_fri", "settings_scheduler_fri"),
            ("scheduler_sat", "settings_scheduler_sat"),
            ("scheduler_sun", "settings_scheduler_sun"),
            # Upload speed distribution
            ("upload_dist_algorithm", "settings_upload_dist_algorithm"),
            ("upload_dist_percentage", "settings_upload_dist_percentage"),
            ("upload_dist_mode", "settings_upload_dist_mode"),
            ("upload_dist_interval_box", "settings_upload_dist_interval_box"),
            ("upload_dist_interval", "settings_upload_dist_interval"),
            ("upload_dist_stopped_min", "settings_upload_dist_stopped_min"),
            ("upload_dist_stopped_max", "settings_upload_dist_stopped_max"),
            # Download speed distribution
            ("download_dist_algorithm", "settings_download_dist_algorithm"),
            ("download_dist_percentage", "settings_download_dist_percentage"),
            ("download_dist_mode", "settings_download_dist_mode"),
            ("download_dist_interval_box", "settings_download_dist_interval_box"),
            ("download_dist_interval", "settings_download_dist_interval"),
            ("download_dist_stopped_min", "settings_download_dist_stopped_min"),
            ("download_dist_stopped_max", "settings_download_dist_stopped_max"),
        ]
        for widget_name, object_id in widgets_to_get:
            logger.trace(f"Getting widget: {object_id}", "SpeedTab")
            try:
                widget = self.builder.get_object(object_id)
                self._widgets[widget_name] = widget
                if widget:
                    logger.trace(f"Successfully got widget: {object_id}", "SpeedTab")
                else:
                    logger.warning(f"Widget not found: {object_id}", "SpeedTab")
            except Exception as e:
                logger.error(f"ERROR getting widget {object_id}: {e}", "SpeedTab")
        logger.trace("Completed widget initialization", "SpeedTab")

    def _connect_signals(self) -> None:
        """Connect signal handlers for Speed tab."""
        # Global speed limits
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

        # Scheduler enable
        enable_scheduler = self.get_widget("enable_scheduler")
        if enable_scheduler:
            self.track_signal(
                enable_scheduler,
                enable_scheduler.connect("state-set", self.on_enable_scheduler_changed),
            )

        # Scheduler time widgets (hour/minute spinbuttons)
        scheduler_start_hour = self.get_widget("scheduler_start_hour")
        if scheduler_start_hour:
            self.track_signal(
                scheduler_start_hour,
                scheduler_start_hour.connect("value-changed", self.on_scheduler_time_changed),
            )

        scheduler_start_minute = self.get_widget("scheduler_start_minute")
        if scheduler_start_minute:
            self.track_signal(
                scheduler_start_minute,
                scheduler_start_minute.connect("value-changed", self.on_scheduler_time_changed),
            )

        scheduler_end_hour = self.get_widget("scheduler_end_hour")
        if scheduler_end_hour:
            self.track_signal(
                scheduler_end_hour,
                scheduler_end_hour.connect("value-changed", self.on_scheduler_time_changed),
            )

        scheduler_end_minute = self.get_widget("scheduler_end_minute")
        if scheduler_end_minute:
            self.track_signal(
                scheduler_end_minute,
                scheduler_end_minute.connect("value-changed", self.on_scheduler_time_changed),
            )

        # Scheduler day checkbuttons
        day_widgets = [
            "scheduler_mon",
            "scheduler_tue",
            "scheduler_wed",
            "scheduler_thu",
            "scheduler_fri",
            "scheduler_sat",
            "scheduler_sun",
        ]
        for day_widget_name in day_widgets:
            day_widget = self.get_widget(day_widget_name)
            if day_widget:
                self.track_signal(
                    day_widget,
                    day_widget.connect("toggled", self.on_scheduler_day_changed),
                )

        # Upload speed distribution
        upload_dist_algorithm = self.get_widget("upload_dist_algorithm")
        if upload_dist_algorithm:
            self.track_signal(
                upload_dist_algorithm,
                upload_dist_algorithm.connect("notify::selected", self.on_upload_dist_algorithm_changed),
            )

        upload_dist_percentage = self.get_widget("upload_dist_percentage")
        if upload_dist_percentage:
            self.track_signal(
                upload_dist_percentage,
                upload_dist_percentage.connect("value-changed", self.on_upload_dist_percentage_changed),
            )

        upload_dist_mode = self.get_widget("upload_dist_mode")
        if upload_dist_mode:
            self.track_signal(
                upload_dist_mode,
                upload_dist_mode.connect("notify::selected", self.on_upload_dist_mode_changed),
            )

        upload_dist_interval = self.get_widget("upload_dist_interval")
        if upload_dist_interval:
            self.track_signal(
                upload_dist_interval,
                upload_dist_interval.connect("value-changed", self.on_upload_dist_interval_changed),
            )

        # Download speed distribution
        download_dist_algorithm = self.get_widget("download_dist_algorithm")
        if download_dist_algorithm:
            self.track_signal(
                download_dist_algorithm,
                download_dist_algorithm.connect("notify::selected", self.on_download_dist_algorithm_changed),
            )

        download_dist_percentage = self.get_widget("download_dist_percentage")
        if download_dist_percentage:
            self.track_signal(
                download_dist_percentage,
                download_dist_percentage.connect("value-changed", self.on_download_dist_percentage_changed),
            )

        download_dist_mode = self.get_widget("download_dist_mode")
        if download_dist_mode:
            self.track_signal(
                download_dist_mode,
                download_dist_mode.connect("notify::selected", self.on_download_dist_mode_changed),
            )

        download_dist_interval = self.get_widget("download_dist_interval")
        if download_dist_interval:
            self.track_signal(
                download_dist_interval,
                download_dist_interval.connect("value-changed", self.on_download_dist_interval_changed),
            )

        # Upload stopped torrents percentage range
        upload_dist_stopped_min = self.get_widget("upload_dist_stopped_min")
        if upload_dist_stopped_min:
            self.track_signal(
                upload_dist_stopped_min,
                upload_dist_stopped_min.connect("value-changed", self.on_upload_dist_stopped_min_changed),
            )

        upload_dist_stopped_max = self.get_widget("upload_dist_stopped_max")
        if upload_dist_stopped_max:
            self.track_signal(
                upload_dist_stopped_max,
                upload_dist_stopped_max.connect("value-changed", self.on_upload_dist_stopped_max_changed),
            )

        # Download stopped torrents percentage range
        download_dist_stopped_min = self.get_widget("download_dist_stopped_min")
        if download_dist_stopped_min:
            self.track_signal(
                download_dist_stopped_min,
                download_dist_stopped_min.connect("value-changed", self.on_download_dist_stopped_min_changed),
            )

        download_dist_stopped_max = self.get_widget("download_dist_stopped_max")
        if download_dist_stopped_max:
            self.track_signal(
                download_dist_stopped_max,
                download_dist_stopped_max.connect("value-changed", self.on_download_dist_stopped_max_changed),
            )

    def _load_settings(self) -> None:
        """Load current settings into Speed tab widgets."""
        logger.trace("Starting _load_settings", "SpeedTab")
        try:
            # Load speed settings using nested keys
            logger.trace("Loading speed settings from app_settings", "SpeedTab")
            self._load_speed_settings()
            logger.trace("Completed _load_speed_settings", "SpeedTab")

            # Load scheduler settings using nested keys
            logger.trace("Loading scheduler settings from app_settings", "SpeedTab")
            self._load_scheduler_settings()
            logger.trace("Completed _load_scheduler_settings", "SpeedTab")

            # Load speed distribution settings
            logger.trace("About to call _load_distribution_settings", "SpeedTab")
            self._load_distribution_settings()
            logger.trace("Completed _load_distribution_settings", "SpeedTab")

            # Update widget dependencies after loading (enable/disable based on loaded state)
            logger.trace("Updating dependencies after settings load", "SpeedTab")
            self.update_dependencies()
            logger.trace("Dependencies updated", "SpeedTab")

            self.logger.info("Speed tab settings loaded")
            logger.info("Completed _load_settings successfully", "SpeedTab")
        except Exception as e:
            logger.error(f"ERROR in _load_settings: {e}", "SpeedTab")
            self.logger.error(f"Error loading Speed tab settings: {e}")

    def _load_speed_settings(self) -> None:
        """Load speed-related settings using nested keys."""
        logger.trace("Starting _load_speed_settings", "SpeedTab")
        try:
            # Global limits (0 = unlimited)
            upload_limit = self.get_widget("upload_limit")
            if upload_limit:
                value = self.app_settings.get("speed.upload_limit_kbps", 0)
                upload_limit.set_value(value)
                logger.trace(f"Upload limit set to: {value}", "SpeedTab")

            download_limit = self.get_widget("download_limit")
            if download_limit:
                value = self.app_settings.get("speed.download_limit_kbps", 0)
                download_limit.set_value(value)
                logger.trace(f"Download limit set to: {value}", "SpeedTab")

            # Alternative speeds
            enable_alt = self.get_widget("enable_alt_speeds")
            if enable_alt:
                value = self.app_settings.get("speed.enable_alternative_speeds", False)
                self.set_switch_state(enable_alt, value)
                logger.trace(f"Enable alt speeds set to: {value}", "SpeedTab")

            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                value = self.app_settings.get("speed.alt_upload_limit_kbps", 50)
                alt_upload_limit.set_value(value)
                logger.trace(f"Alt upload limit set to: {value}", "SpeedTab")

            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                value = self.app_settings.get("speed.alt_download_limit_kbps", 100)
                alt_download_limit.set_value(value)
                logger.trace(f"Alt download limit set to: {value}", "SpeedTab")

            logger.info("Completed _load_speed_settings successfully", "SpeedTab")
        except Exception as e:
            logger.error(f"ERROR in _load_speed_settings: {e}", "SpeedTab")
            self.logger.error(f"Error loading speed settings: {e}")

    def _load_scheduler_settings(self) -> None:
        """Load scheduler settings using nested keys."""
        try:
            # Scheduler enabled
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                value = self.app_settings.get("scheduler.enabled", False)
                self.set_switch_state(enable_scheduler, value)
                logger.trace(f"Scheduler enabled set to: {value}", "SpeedTab")

            # Start time (hour and minute)
            scheduler_start_hour = self.get_widget("scheduler_start_hour")
            if scheduler_start_hour:
                value = self.app_settings.get("scheduler.start_hour", 22)
                scheduler_start_hour.set_value(value)
                logger.trace(f"Scheduler start hour set to: {value}", "SpeedTab")

            scheduler_start_minute = self.get_widget("scheduler_start_minute")
            if scheduler_start_minute:
                value = self.app_settings.get("scheduler.start_minute", 0)
                scheduler_start_minute.set_value(value)
                logger.trace(f"Scheduler start minute set to: {value}", "SpeedTab")

            # End time (hour and minute)
            scheduler_end_hour = self.get_widget("scheduler_end_hour")
            if scheduler_end_hour:
                value = self.app_settings.get("scheduler.end_hour", 6)
                scheduler_end_hour.set_value(value)
                logger.trace(f"Scheduler end hour set to: {value}", "SpeedTab")

            scheduler_end_minute = self.get_widget("scheduler_end_minute")
            if scheduler_end_minute:
                value = self.app_settings.get("scheduler.end_minute", 0)
                scheduler_end_minute.set_value(value)
                logger.trace(f"Scheduler end minute set to: {value}", "SpeedTab")

            # Scheduler days (individual checkbuttons)
            days = self.app_settings.get("scheduler.days", {})
            day_mapping = [
                ("scheduler_mon", "monday"),
                ("scheduler_tue", "tuesday"),
                ("scheduler_wed", "wednesday"),
                ("scheduler_thu", "thursday"),
                ("scheduler_fri", "friday"),
                ("scheduler_sat", "saturday"),
                ("scheduler_sun", "sunday"),
            ]
            for widget_name, day_key in day_mapping:
                day_widget = self.get_widget(widget_name)
                if day_widget:
                    value = days.get(day_key, True)
                    day_widget.set_active(value)
                    logger.trace(f"Scheduler {day_key} set to: {value}", "SpeedTab")

        except Exception as e:
            logger.error(f"Error loading scheduler settings: {e}", "SpeedTab")
            self.logger.error(f"Error loading scheduler settings: {e}")

    def _load_distribution_settings(self) -> None:
        """Load speed distribution settings."""
        try:
            # Map algorithm names to dropdown indices
            algorithm_map = {"off": 0, "pareto": 1, "power-law": 2, "log-normal": 3}

            # Upload distribution
            upload_algorithm = self.app_settings.upload_distribution_algorithm.lower()

            upload_dist_algorithm = self.get_widget("upload_dist_algorithm")
            if upload_dist_algorithm:
                # Note: No need to block signals - they haven't been connected yet
                # (_load_settings is called BEFORE _connect_signals in base_tab.py)
                index = algorithm_map.get(upload_algorithm, 0)
                upload_dist_algorithm.set_selected(index)

            upload_dist_percentage = self.get_widget("upload_dist_percentage")
            if upload_dist_percentage:
                upload_dist_percentage.set_value(self.app_settings.upload_distribution_spread_percentage)

            upload_mode = self.app_settings.upload_distribution_redistribution_mode.lower()
            upload_dist_mode = self.get_widget("upload_dist_mode")
            if upload_dist_mode:
                if upload_mode == "tick":
                    upload_dist_mode.set_selected(0)
                elif "minute" in upload_mode or upload_mode == "custom":
                    upload_dist_mode.set_selected(1)
                elif upload_mode == "announce":
                    upload_dist_mode.set_selected(2)

            upload_dist_interval = self.get_widget("upload_dist_interval")
            if upload_dist_interval:
                upload_dist_interval.set_value(self.app_settings.upload_distribution_custom_interval_minutes)

            upload_dist_stopped_min = self.get_widget("upload_dist_stopped_min")
            if upload_dist_stopped_min:
                upload_dist_stopped_min.set_value(self.app_settings.upload_distribution_stopped_min_percentage)

            upload_dist_stopped_max = self.get_widget("upload_dist_stopped_max")
            if upload_dist_stopped_max:
                upload_dist_stopped_max.set_value(self.app_settings.upload_distribution_stopped_max_percentage)

            # Download distribution
            download_algorithm = self.app_settings.download_distribution_algorithm.lower()
            download_dist_algorithm = self.get_widget("download_dist_algorithm")
            if download_dist_algorithm:
                index = algorithm_map.get(download_algorithm, 0)
                download_dist_algorithm.set_selected(index)

            download_dist_percentage = self.get_widget("download_dist_percentage")
            if download_dist_percentage:
                download_dist_percentage.set_value(self.app_settings.download_distribution_spread_percentage)

            download_mode = self.app_settings.download_distribution_redistribution_mode.lower()
            download_dist_mode = self.get_widget("download_dist_mode")
            if download_dist_mode:
                if download_mode == "tick":
                    download_dist_mode.set_selected(0)
                elif "minute" in download_mode or download_mode == "custom":
                    download_dist_mode.set_selected(1)
                elif download_mode == "announce":
                    download_dist_mode.set_selected(2)

            download_dist_interval = self.get_widget("download_dist_interval")
            if download_dist_interval:
                download_dist_interval.set_value(self.app_settings.download_distribution_custom_interval_minutes)

            download_dist_stopped_min = self.get_widget("download_dist_stopped_min")
            if download_dist_stopped_min:
                download_dist_stopped_min.set_value(self.app_settings.download_distribution_stopped_min_percentage)

            download_dist_stopped_max = self.get_widget("download_dist_stopped_max")
            if download_dist_stopped_max:
                download_dist_stopped_max.set_value(self.app_settings.download_distribution_stopped_max_percentage)

        except Exception as e:
            self.logger.error(f"Error loading distribution settings: {e}", exc_info=True)

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Speed tab."""
        self._update_speed_dependencies()
        self._update_distribution_dependencies()

    def _update_tab_dependencies(self) -> None:
        """Update Speed tab dependencies."""
        self._update_speed_dependencies()
        self._update_distribution_dependencies()

    def _update_speed_dependencies(self) -> None:
        """Update speed-related widget dependencies."""
        try:
            # Enable/disable alternative speed controls
            enable_alt = self.get_widget("enable_alt_speeds")
            alt_enabled = enable_alt and enable_alt.get_active()
            # IMPORTANT: Enable the parent box first (hardcoded to sensitive=False in XML)
            self.update_widget_sensitivity("alt_speed_box", alt_enabled)
            self.update_widget_sensitivity("alt_upload_limit", alt_enabled)
            self.update_widget_sensitivity("alt_download_limit", alt_enabled)

            # Enable/disable scheduler controls
            enable_scheduler = self.get_widget("enable_scheduler")
            scheduler_enabled = enable_scheduler and enable_scheduler.get_active()
            # IMPORTANT: Enable the parent box first (hardcoded to sensitive=False in XML)
            self.update_widget_sensitivity("scheduler_box", scheduler_enabled)
            # Individual scheduler widgets
            self.update_widget_sensitivity("scheduler_start_hour", scheduler_enabled)
            self.update_widget_sensitivity("scheduler_start_minute", scheduler_enabled)
            self.update_widget_sensitivity("scheduler_end_hour", scheduler_enabled)
            self.update_widget_sensitivity("scheduler_end_minute", scheduler_enabled)
            # Day checkbuttons
            for day in [
                "scheduler_mon",
                "scheduler_tue",
                "scheduler_wed",
                "scheduler_thu",
                "scheduler_fri",
                "scheduler_sat",
                "scheduler_sun",
            ]:
                self.update_widget_sensitivity(day, scheduler_enabled)
        except Exception as e:
            self.logger.error(f"Error updating speed dependencies: {e}")

    def _update_distribution_dependencies(self) -> None:
        """Update speed distribution widget dependencies."""
        try:
            # Upload distribution - enable widgets only if algorithm is not "off"
            upload_dist_algorithm = self.get_widget("upload_dist_algorithm")
            if upload_dist_algorithm:
                upload_algorithm_enabled = upload_dist_algorithm.get_selected() > 0  # 0 = "off"
                self.update_widget_sensitivity("upload_dist_percentage", upload_algorithm_enabled)
                self.update_widget_sensitivity("upload_dist_mode", upload_algorithm_enabled)
                self.update_widget_sensitivity("upload_dist_stopped_min", upload_algorithm_enabled)
                self.update_widget_sensitivity("upload_dist_stopped_max", upload_algorithm_enabled)

                # Also handle interval box visibility based on mode (only if algorithm is enabled)
                if upload_algorithm_enabled:
                    upload_dist_mode = self.get_widget("upload_dist_mode")
                    if upload_dist_mode:
                        mode_index = upload_dist_mode.get_selected()
                        is_custom = mode_index == 1  # custom mode
                        interval_box = self.get_widget("upload_dist_interval_box")
                        if interval_box:
                            interval_box.set_visible(is_custom)
                else:
                    # Hide interval box when algorithm is off
                    interval_box = self.get_widget("upload_dist_interval_box")
                    if interval_box:
                        interval_box.set_visible(False)

            # Download distribution - enable widgets only if algorithm is not "off"
            download_dist_algorithm = self.get_widget("download_dist_algorithm")
            if download_dist_algorithm:
                download_algorithm_enabled = download_dist_algorithm.get_selected() > 0  # 0 = "off"
                self.update_widget_sensitivity("download_dist_percentage", download_algorithm_enabled)
                self.update_widget_sensitivity("download_dist_mode", download_algorithm_enabled)
                self.update_widget_sensitivity("download_dist_stopped_min", download_algorithm_enabled)
                self.update_widget_sensitivity("download_dist_stopped_max", download_algorithm_enabled)

                # Also handle interval box visibility based on mode (only if algorithm is enabled)
                if download_algorithm_enabled:
                    download_dist_mode = self.get_widget("download_dist_mode")
                    if download_dist_mode:
                        mode_index = download_dist_mode.get_selected()
                        is_custom = mode_index == 1  # custom mode
                        interval_box = self.get_widget("download_dist_interval_box")
                        if interval_box:
                            interval_box.set_visible(is_custom)
                else:
                    # Hide interval box when algorithm is off
                    interval_box = self.get_widget("download_dist_interval_box")
                    if interval_box:
                        interval_box.set_visible(False)

        except Exception as e:
            self.logger.error(f"Error updating distribution dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Speed tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: Dict[str, Any] = {}

        try:
            # Collect speed settings (already uses nested keys like "speed.upload_limit_kbps")
            speed_settings = self._collect_speed_settings()
            settings.update(speed_settings)

            # Collect scheduler settings (already uses nested keys like "scheduler.enabled")
            scheduler_settings = self._collect_scheduler_settings()
            settings.update(scheduler_settings)

            # Collect distribution settings with proper key prefixes
            distribution_settings = self._collect_distribution_settings()
            for direction in ["upload", "download"]:
                if direction in distribution_settings:
                    for key, value in distribution_settings[direction].items():
                        settings[f"speed_distribution.{direction}.{key}"] = value

        except Exception as e:
            self.logger.error(f"Error collecting Speed tab settings: {e}")

        self.logger.trace(f"Collected {len(settings)} settings from Speed tab")
        return settings

    def _collect_speed_settings(self) -> Dict[str, Any]:
        """Collect speed-related settings with nested keys."""
        speed_settings: Dict[str, Any] = {}
        try:
            upload_limit = self.get_widget("upload_limit")
            if upload_limit:
                speed_settings["speed.upload_limit_kbps"] = int(upload_limit.get_value())

            download_limit = self.get_widget("download_limit")
            if download_limit:
                speed_settings["speed.download_limit_kbps"] = int(download_limit.get_value())

            enable_alt = self.get_widget("enable_alt_speeds")
            if enable_alt:
                speed_settings["speed.enable_alternative_speeds"] = enable_alt.get_active()

            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                speed_settings["speed.alt_upload_limit_kbps"] = int(alt_upload_limit.get_value())

            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                speed_settings["speed.alt_download_limit_kbps"] = int(alt_download_limit.get_value())
        except Exception as e:
            self.logger.error(f"Error collecting speed settings: {e}")
        return speed_settings

    def _collect_scheduler_settings(self) -> Dict[str, Any]:
        """Collect scheduler settings with nested keys."""
        scheduler_settings: Dict[str, Any] = {}
        try:
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                scheduler_settings["scheduler.enabled"] = enable_scheduler.get_active()

            # Start time (hour and minute)
            scheduler_start_hour = self.get_widget("scheduler_start_hour")
            if scheduler_start_hour:
                scheduler_settings["scheduler.start_hour"] = int(scheduler_start_hour.get_value())

            scheduler_start_minute = self.get_widget("scheduler_start_minute")
            if scheduler_start_minute:
                scheduler_settings["scheduler.start_minute"] = int(scheduler_start_minute.get_value())

            # End time (hour and minute)
            scheduler_end_hour = self.get_widget("scheduler_end_hour")
            if scheduler_end_hour:
                scheduler_settings["scheduler.end_hour"] = int(scheduler_end_hour.get_value())

            scheduler_end_minute = self.get_widget("scheduler_end_minute")
            if scheduler_end_minute:
                scheduler_settings["scheduler.end_minute"] = int(scheduler_end_minute.get_value())

            # Collect day settings
            days = {}
            day_mapping = [
                ("scheduler_mon", "monday"),
                ("scheduler_tue", "tuesday"),
                ("scheduler_wed", "wednesday"),
                ("scheduler_thu", "thursday"),
                ("scheduler_fri", "friday"),
                ("scheduler_sat", "saturday"),
                ("scheduler_sun", "sunday"),
            ]
            for widget_name, day_key in day_mapping:
                day_widget = self.get_widget(widget_name)
                if day_widget:
                    days[day_key] = day_widget.get_active()
            scheduler_settings["scheduler.days"] = days

        except Exception as e:
            self.logger.error(f"Error collecting scheduler settings: {e}")
        return scheduler_settings

    def _collect_distribution_settings(self) -> Dict[str, Any]:
        """Collect speed distribution settings from widgets."""
        distribution_settings = {"upload": {}, "download": {}}  # type: ignore[var-annotated]

        try:
            # Map dropdown indices to algorithm names
            algorithm_names = ["off", "pareto", "power-law", "log-normal"]
            mode_names = ["tick", "custom", "announce"]

            # Upload distribution
            upload_dist_algorithm = self.get_widget("upload_dist_algorithm")
            if upload_dist_algorithm:
                selected = upload_dist_algorithm.get_selected()
                distribution_settings["upload"]["algorithm"] = algorithm_names[selected]

            upload_dist_percentage = self.get_widget("upload_dist_percentage")
            if upload_dist_percentage:
                distribution_settings["upload"]["spread_percentage"] = int(upload_dist_percentage.get_value())

            upload_dist_mode = self.get_widget("upload_dist_mode")
            if upload_dist_mode:
                selected = upload_dist_mode.get_selected()
                distribution_settings["upload"]["redistribution_mode"] = mode_names[selected]

            upload_dist_interval = self.get_widget("upload_dist_interval")
            if upload_dist_interval:
                distribution_settings["upload"]["custom_interval_minutes"] = int(upload_dist_interval.get_value())

            upload_dist_stopped_min = self.get_widget("upload_dist_stopped_min")
            if upload_dist_stopped_min:
                distribution_settings["upload"]["stopped_min_percentage"] = int(upload_dist_stopped_min.get_value())

            upload_dist_stopped_max = self.get_widget("upload_dist_stopped_max")
            if upload_dist_stopped_max:
                distribution_settings["upload"]["stopped_max_percentage"] = int(upload_dist_stopped_max.get_value())

            # Download distribution
            download_dist_algorithm = self.get_widget("download_dist_algorithm")
            if download_dist_algorithm:
                selected = download_dist_algorithm.get_selected()
                distribution_settings["download"]["algorithm"] = algorithm_names[selected]

            download_dist_percentage = self.get_widget("download_dist_percentage")
            if download_dist_percentage:
                distribution_settings["download"]["spread_percentage"] = int(download_dist_percentage.get_value())

            download_dist_mode = self.get_widget("download_dist_mode")
            if download_dist_mode:
                selected = download_dist_mode.get_selected()
                distribution_settings["download"]["redistribution_mode"] = mode_names[selected]

            download_dist_interval = self.get_widget("download_dist_interval")
            if download_dist_interval:
                distribution_settings["download"]["custom_interval_minutes"] = int(download_dist_interval.get_value())

            download_dist_stopped_min = self.get_widget("download_dist_stopped_min")
            if download_dist_stopped_min:
                distribution_settings["download"]["stopped_min_percentage"] = int(download_dist_stopped_min.get_value())

            download_dist_stopped_max = self.get_widget("download_dist_stopped_max")
            if download_dist_stopped_max:
                distribution_settings["download"]["stopped_max_percentage"] = int(download_dist_stopped_max.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting distribution settings: {e}", exc_info=True)

        return distribution_settings

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

    def on_enable_alt_speeds_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle alternative speeds toggle."""
        if self._loading_settings:
            return
        try:
            self.update_dependencies()
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Alternative speeds will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except Exception as e:
            self.logger.error(f"Error changing alternative speeds setting: {e}")

    def on_enable_scheduler_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle scheduler toggle."""
        if self._loading_settings:
            return
        try:
            self.update_dependencies()
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Speed scheduler will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except Exception as e:
            self.logger.error(f"Error changing scheduler setting: {e}")

    def on_upload_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle upload limit change."""
        if self._loading_settings:
            return
        try:
            value = int(spin_button.get_value())
            self.app_settings.set("speed.upload_limit_kbps", value)
            self.logger.trace(f"Upload limit changed to: {value} KB/s")
        except Exception as e:
            self.logger.error(f"Error changing upload limit: {e}")

    def on_download_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle download limit change."""
        if self._loading_settings:
            return
        try:
            value = int(spin_button.get_value())
            self.app_settings.set("speed.download_limit_kbps", value)
            self.logger.trace(f"Download limit changed to: {value} KB/s")
        except Exception as e:
            self.logger.error(f"Error changing download limit: {e}")

    def on_alt_upload_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle alternative upload limit change."""
        if self._loading_settings:
            return
        try:
            value = int(spin_button.get_value())
            self.app_settings.set("speed.alt_upload_limit_kbps", value)
            self.logger.trace(f"Alt upload limit changed to: {value} KB/s")
        except Exception as e:
            self.logger.error(f"Error changing alt upload limit: {e}")

    def on_alt_download_limit_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle alternative download limit change."""
        if self._loading_settings:
            return
        try:
            value = int(spin_button.get_value())
            self.app_settings.set("speed.alt_download_limit_kbps", value)
            self.logger.trace(f"Alt download limit changed to: {value} KB/s")
        except Exception as e:
            self.logger.error(f"Error changing alt download limit: {e}")

    def on_scheduler_time_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle scheduler time change (hour or minute)."""
        if self._loading_settings:
            return
        try:
            # Collect all time values and save
            start_hour = self.get_widget("scheduler_start_hour")
            start_minute = self.get_widget("scheduler_start_minute")
            end_hour = self.get_widget("scheduler_end_hour")
            end_minute = self.get_widget("scheduler_end_minute")

            if start_hour:
                self.app_settings.set("scheduler.start_hour", int(start_hour.get_value()))
            if start_minute:
                self.app_settings.set("scheduler.start_minute", int(start_minute.get_value()))
            if end_hour:
                self.app_settings.set("scheduler.end_hour", int(end_hour.get_value()))
            if end_minute:
                self.app_settings.set("scheduler.end_minute", int(end_minute.get_value()))

            self.logger.trace("Scheduler time changed")
        except Exception as e:
            self.logger.error(f"Error changing scheduler time: {e}")

    def on_scheduler_day_changed(self, check_button: Gtk.CheckButton) -> None:
        """Handle scheduler day checkbox change."""
        if self._loading_settings:
            return
        try:
            # Collect all day values and save
            days = {}
            day_mapping = [
                ("scheduler_mon", "monday"),
                ("scheduler_tue", "tuesday"),
                ("scheduler_wed", "wednesday"),
                ("scheduler_thu", "thursday"),
                ("scheduler_fri", "friday"),
                ("scheduler_sat", "saturday"),
                ("scheduler_sun", "sunday"),
            ]
            for widget_name, day_key in day_mapping:
                day_widget = self.get_widget(widget_name)
                if day_widget:
                    days[day_key] = day_widget.get_active()

            self.app_settings.set("scheduler.days", days)
            self.logger.trace("Scheduler days changed")
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
                self.set_switch_state(enable_alt, False)
            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                alt_upload_limit.set_value(50)
            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                alt_download_limit.set_value(100)

            # Reset scheduler
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                self.set_switch_state(enable_scheduler, False)

            # Reset scheduler time
            scheduler_start_hour = self.get_widget("scheduler_start_hour")
            if scheduler_start_hour:
                scheduler_start_hour.set_value(22)
            scheduler_start_minute = self.get_widget("scheduler_start_minute")
            if scheduler_start_minute:
                scheduler_start_minute.set_value(0)
            scheduler_end_hour = self.get_widget("scheduler_end_hour")
            if scheduler_end_hour:
                scheduler_end_hour.set_value(6)
            scheduler_end_minute = self.get_widget("scheduler_end_minute")
            if scheduler_end_minute:
                scheduler_end_minute.set_value(0)

            # Reset scheduler days (all enabled by default)
            for day in [
                "scheduler_mon",
                "scheduler_tue",
                "scheduler_wed",
                "scheduler_thu",
                "scheduler_fri",
                "scheduler_sat",
                "scheduler_sun",
            ]:
                day_widget = self.get_widget(day)
                if day_widget:
                    day_widget.set_active(True)

            # Reset speed distribution settings
            upload_dist_algorithm = self.get_widget("upload_dist_algorithm")
            if upload_dist_algorithm:
                upload_dist_algorithm.set_selected(0)  # Off
            upload_dist_percentage = self.get_widget("upload_dist_percentage")
            if upload_dist_percentage:
                upload_dist_percentage.set_value(50)
            upload_dist_mode = self.get_widget("upload_dist_mode")
            if upload_dist_mode:
                upload_dist_mode.set_selected(0)  # Tick
            upload_dist_interval = self.get_widget("upload_dist_interval")
            if upload_dist_interval:
                upload_dist_interval.set_value(5)
            upload_dist_stopped_min = self.get_widget("upload_dist_stopped_min")
            if upload_dist_stopped_min:
                upload_dist_stopped_min.set_value(20)
            upload_dist_stopped_max = self.get_widget("upload_dist_stopped_max")
            if upload_dist_stopped_max:
                upload_dist_stopped_max.set_value(40)

            download_dist_algorithm = self.get_widget("download_dist_algorithm")
            if download_dist_algorithm:
                download_dist_algorithm.set_selected(0)  # Off
            download_dist_percentage = self.get_widget("download_dist_percentage")
            if download_dist_percentage:
                download_dist_percentage.set_value(50)
            download_dist_mode = self.get_widget("download_dist_mode")
            if download_dist_mode:
                download_dist_mode.set_selected(0)  # Tick
            download_dist_interval = self.get_widget("download_dist_interval")
            if download_dist_interval:
                download_dist_interval.set_value(5)
            download_dist_stopped_min = self.get_widget("download_dist_stopped_min")
            if download_dist_stopped_min:
                download_dist_stopped_min.set_value(20)
            download_dist_stopped_max = self.get_widget("download_dist_stopped_max")
            if download_dist_stopped_max:
                download_dist_stopped_max.set_value(40)

            self.update_dependencies()
            self.show_notification("Speed settings reset to defaults", "success")
        except Exception as e:
            self.logger.error(f"Error resetting Speed tab to defaults: {e}")

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace(
            "SpeedTab update view",
            extra={"class_name": self.__class__.__name__},
        )

    # Speed distribution signal handlers
    def on_upload_dist_algorithm_changed(self, dropdown: Any, _param: Any) -> None:
        """Handle upload distribution algorithm change."""
        if self._loading_settings:
            return
        try:
            selected = dropdown.get_selected()
            algorithm_names = ["off", "pareto", "power-law", "log-normal"]
            algorithm = algorithm_names[selected] if selected < len(algorithm_names) else "off"

            self.app_settings.upload_distribution_algorithm = algorithm
            self.logger.trace(f"Upload distribution algorithm changed to: {algorithm}")

            # Update dependencies to enable/disable distribution options
            self.update_dependencies()
        except Exception as e:
            self.logger.error(f"Error changing upload distribution algorithm: {e}", exc_info=True)

    def on_upload_dist_percentage_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle upload distribution percentage change."""
        if self._loading_settings:
            return
        try:
            percentage = int(spin_button.get_value())
            self.app_settings.upload_distribution_spread_percentage = percentage
            self.logger.trace(f"Upload distribution percentage changed to: {percentage}%")
        except Exception as e:
            self.logger.error(f"Error changing upload distribution percentage: {e}")

    def on_upload_dist_mode_changed(self, dropdown: Any, _param: Any) -> None:
        """Handle upload distribution mode change."""
        if self._loading_settings:
            return
        try:
            selected = dropdown.get_selected()
            mode_names = ["tick", "custom", "announce"]
            mode = mode_names[selected] if selected < len(mode_names) else "tick"
            self.app_settings.upload_distribution_redistribution_mode = mode

            # Show/hide interval box based on mode
            interval_box = self.get_widget("upload_dist_interval_box")
            if interval_box:
                interval_box.set_visible(mode == "custom")

            self.logger.trace(f"Upload distribution mode changed to: {mode}")
        except Exception as e:
            self.logger.error(f"Error changing upload distribution mode: {e}")

    def on_upload_dist_interval_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle upload distribution interval change."""
        if self._loading_settings:
            return
        try:
            interval = int(spin_button.get_value())
            self.app_settings.upload_distribution_custom_interval_minutes = interval
            self.logger.trace(f"Upload distribution interval changed to: {interval} minutes")
        except Exception as e:
            self.logger.error(f"Error changing upload distribution interval: {e}")

    def on_download_dist_algorithm_changed(self, dropdown: Any, _param: Any) -> None:
        """Handle download distribution algorithm change."""
        if self._loading_settings:
            return
        try:
            selected = dropdown.get_selected()
            algorithm_names = ["off", "pareto", "power-law", "log-normal"]
            algorithm = algorithm_names[selected] if selected < len(algorithm_names) else "off"
            self.app_settings.download_distribution_algorithm = algorithm
            self.logger.trace(f"Download distribution algorithm changed to: {algorithm}")

            # Update dependencies to enable/disable distribution options
            self.update_dependencies()
        except Exception as e:
            self.logger.error(f"Error changing download distribution algorithm: {e}")

    def on_download_dist_percentage_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle download distribution percentage change."""
        if self._loading_settings:
            return
        try:
            percentage = int(spin_button.get_value())
            self.app_settings.download_distribution_spread_percentage = percentage
            self.logger.trace(f"Download distribution percentage changed to: {percentage}%")
        except Exception as e:
            self.logger.error(f"Error changing download distribution percentage: {e}")

    def on_download_dist_mode_changed(self, dropdown: Any, _param: Any) -> None:
        """Handle download distribution mode change."""
        if self._loading_settings:
            return
        try:
            selected = dropdown.get_selected()
            mode_names = ["tick", "custom", "announce"]
            mode = mode_names[selected] if selected < len(mode_names) else "tick"
            self.app_settings.download_distribution_redistribution_mode = mode

            # Show/hide interval box based on mode
            interval_box = self.get_widget("download_dist_interval_box")
            if interval_box:
                interval_box.set_visible(mode == "custom")

            self.logger.trace(f"Download distribution mode changed to: {mode}")
        except Exception as e:
            self.logger.error(f"Error changing download distribution mode: {e}")

    def on_download_dist_interval_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle download distribution interval change."""
        if self._loading_settings:
            return
        try:
            interval = int(spin_button.get_value())
            self.app_settings.download_distribution_custom_interval_minutes = interval
            self.logger.trace(f"Download distribution interval changed to: {interval} minutes")
        except Exception as e:
            self.logger.error(f"Error changing download distribution interval: {e}")

    def on_upload_dist_stopped_min_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle upload distribution stopped min percentage change."""
        if self._loading_settings:
            return
        try:
            percentage = int(spin_button.get_value())
            self.app_settings.upload_distribution_stopped_min_percentage = percentage
            self.logger.trace(f"Upload distribution stopped min percentage changed to: {percentage}%")
        except Exception as e:
            self.logger.error(f"Error changing upload distribution stopped min percentage: {e}")

    def on_upload_dist_stopped_max_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle upload distribution stopped max percentage change."""
        if self._loading_settings:
            return
        try:
            percentage = int(spin_button.get_value())
            self.app_settings.upload_distribution_stopped_max_percentage = percentage
            self.logger.trace(f"Upload distribution stopped max percentage changed to: {percentage}%")
        except Exception as e:
            self.logger.error(f"Error changing upload distribution stopped max percentage: {e}")

    def on_download_dist_stopped_min_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle download distribution stopped min percentage change."""
        if self._loading_settings:
            return
        try:
            percentage = int(spin_button.get_value())
            self.app_settings.download_distribution_stopped_min_percentage = percentage
            self.logger.trace(f"Download distribution stopped min percentage changed to: {percentage}%")
        except Exception as e:
            self.logger.error(f"Error changing download distribution stopped min percentage: {e}")

    def on_download_dist_stopped_max_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle download distribution stopped max percentage change."""
        if self._loading_settings:
            return
        try:
            percentage = int(spin_button.get_value())
            self.app_settings.download_distribution_stopped_max_percentage = percentage
            self.logger.trace(f"Download distribution stopped max percentage changed to: {percentage}%")
        except Exception as e:
            self.logger.error(f"Error changing download distribution stopped max percentage: {e}")
