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

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS = [
        # Global speed limits
        {
            "id": "settings_upload_limit",
            "name": "upload_limit",
            "setting_key": "speed.upload_limit_kbps",
            "type": int,
        },
        {
            "id": "settings_download_limit",
            "name": "download_limit",
            "setting_key": "speed.download_limit_kbps",
            "type": int,
        },
        # Alternative speed limits
        {
            "id": "settings_alt_upload_limit",
            "name": "alt_upload_limit",
            "setting_key": "speed.alt_upload_limit_kbps",
            "type": int,
        },
        {
            "id": "settings_alt_download_limit",
            "name": "alt_download_limit",
            "setting_key": "speed.alt_download_limit_kbps",
            "type": int,
        },
    ]

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Speed"

    def _init_widgets(self) -> None:
        """Initialize Speed tab widgets."""
        logger.trace("Starting widget initialization", "SpeedTab")
        # Cache commonly used widgets
        widgets_to_get = [
            ("upload_limit", "settings_upload_limit"),
            ("download_limit", "settings_download_limit"),
            ("enable_alt_speeds", "settings_enable_alt_speeds"),
            # Section containers (hardcoded to sensitive=False in XML)
            ("alt_speed_box", "settings_alt_speed_box"),
            ("scheduler_box", "settings_scheduler_box"),
            ("alt_upload_limit", "settings_alt_upload_limit"),
            ("alt_download_limit", "settings_alt_download_limit"),
            ("enable_scheduler", "settings_enable_scheduler"),
            ("scheduler_start_time", "settings_scheduler_start_time"),
            ("scheduler_end_time", "settings_scheduler_end_time"),
            ("scheduler_days", "settings_scheduler_days"),
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
            logger.trace("Getting widget:", "SpeedTab")
            try:
                widget = self.builder.get_object(object_id)
                self._widgets[widget_name] = widget
                logger.info("Successfully got widget:", "SpeedTab")
            except Exception:
                logger.error("ERROR getting widget :", "SpeedTab")
        logger.trace("Completed widget initialization", "SpeedTab")

    def _connect_signals(self) -> None:
        """Connect signal handlers for Speed tab."""
        # Simple widgets (upload_limit, download_limit, alt_upload_limit, alt_download_limit)
        # are now auto-connected via WIDGET_MAPPINGS

        # Alternative speeds enable (has dependencies)
        enable_alt = self.get_widget("enable_alt_speeds")
        if enable_alt:
            self.track_signal(
                enable_alt,
                enable_alt.connect("state-set", self.on_enable_alt_speeds_changed),
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
            # Load speed settings
            logger.trace("Getting speed settings from app_settings", "SpeedTab")
            speed_settings = getattr(self.app_settings, "speed", {})
            logger.trace("Got speed settings:", "SpeedTab")
            logger.trace("About to call _load_speed_settings", "SpeedTab")
            self._load_speed_settings(speed_settings)
            logger.trace("Completed _load_speed_settings", "SpeedTab")
            # Load scheduler settings
            logger.trace("Getting scheduler settings from app_settings", "SpeedTab")
            scheduler_settings = getattr(self.app_settings, "scheduler", {})
            logger.trace("Got scheduler settings:", "SpeedTab")
            logger.trace("About to call _load_scheduler_settings", "SpeedTab")
            self._load_scheduler_settings(scheduler_settings)
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
            logger.error("ERROR in _load_settings:", "SpeedTab")
            self.logger.error(f"Error loading Speed tab settings: {e}")

    def _load_speed_settings(self, speed_settings: Dict[str, Any]) -> None:
        """Load speed-related settings."""
        logger.trace("Starting _load_speed_settings", "SpeedTab")
        try:
            # Global limits (0 = unlimited)
            logger.trace("Getting upload_limit widget", "SpeedTab")
            upload_limit = self.get_widget("upload_limit")
            if upload_limit:
                logger.debug("Setting upload_limit value to", "SpeedTab")
                upload_limit.set_value(speed_settings.get("upload_limit_kbps", 0))
                logger.info("Upload limit value set successfully", "SpeedTab")
            logger.trace("Getting download_limit widget", "SpeedTab")
            download_limit = self.get_widget("download_limit")
            if download_limit:
                logger.debug("Setting download_limit value to", "SpeedTab")
                download_limit.set_value(speed_settings.get("download_limit_kbps", 0))
                logger.info("Download limit value set successfully", "SpeedTab")
            # Alternative speeds
            logger.trace("Getting enable_alt_speeds widget", "SpeedTab")
            enable_alt = self.get_widget("enable_alt_speeds")
            if enable_alt:
                logger.debug("Setting enable_alt_speeds active to", "SpeedTab")
                self.set_switch_state(enable_alt, speed_settings.get("enable_alternative_speeds", False))
                logger.info("Enable alt speeds set successfully", "SpeedTab")
            logger.trace("Getting alt_upload_limit widget", "SpeedTab")
            alt_upload_limit = self.get_widget("alt_upload_limit")
            if alt_upload_limit:
                logger.debug("Setting alt_upload_limit value to", "SpeedTab")
                alt_upload_limit.set_value(speed_settings.get("alt_upload_limit_kbps", 0))
                logger.info("Alt upload limit value set successfully", "SpeedTab")
            logger.trace("Getting alt_download_limit widget", "SpeedTab")
            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                logger.trace(
                    "Setting alt_download_limit value to {speed_settings.get('alt_download_limit_kbps', 0)}",
                    "UnknownClass",
                )
                alt_download_limit.set_value(speed_settings.get("alt_download_limit_kbps", 0))
                logger.info("Alt download limit value set successfully", "SpeedTab")
            logger.info("Completed _load_speed_settings successfully", "SpeedTab")
        except Exception as e:
            logger.error("ERROR in _load_speed_settings:", "SpeedTab")
            self.logger.error(f"Error loading speed settings: {e}")

    def _load_scheduler_settings(self, scheduler_settings: Dict[str, Any]) -> None:
        """Load scheduler settings."""
        try:
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                self.set_switch_state(enable_scheduler, scheduler_settings.get("enabled", False))
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
            self.update_widget_sensitivity("scheduler_start_time", scheduler_enabled)
            self.update_widget_sensitivity("scheduler_end_time", scheduler_enabled)
            self.update_widget_sensitivity("scheduler_days", scheduler_enabled)
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
        # Collect from WIDGET_MAPPINGS
        settings = self._collect_mapped_settings()

        try:
            # Collect speed settings with proper key prefixes
            speed_settings = self._collect_speed_settings()
            for key, value in speed_settings.items():
                settings[f"speed.{key}"] = value

            # Collect scheduler settings with proper key prefixes
            scheduler_settings = self._collect_scheduler_settings()
            for key, value in scheduler_settings.items():
                settings[f"scheduler.{key}"] = value

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

    def _collect_distribution_settings(self) -> Dict[str, Any]:
        """Collect speed distribution settings from widgets."""
        distribution_settings = {"upload": {}, "download": {}}

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

    def on_scheduler_start_time_changed(self, widget, param) -> None:
        """Handle scheduler start time change."""
        if self._loading_settings:
            return
        try:
            # NOTE: Setting will be saved in batch via _collect_settings()
            # Implementation depends on the specific time widget used
            self.logger.trace("Scheduler start time changed")
        except Exception as e:
            self.logger.error(f"Error changing scheduler start time: {e}")

    def on_scheduler_end_time_changed(self, widget, param) -> None:
        """Handle scheduler end time change."""
        if self._loading_settings:
            return
        try:
            # NOTE: Setting will be saved in batch via _collect_settings()
            # Implementation depends on the specific time widget used
            self.logger.trace("Scheduler end time changed")
        except Exception as e:
            self.logger.error(f"Error changing scheduler end time: {e}")

    def on_scheduler_days_changed(self, widget) -> None:
        """Handle scheduler days change."""
        if self._loading_settings:
            return
        try:
            # NOTE: Setting will be saved in batch via _collect_settings()
            # Implementation depends on the specific days selection widget used
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
                alt_upload_limit.set_value(0)
            alt_download_limit = self.get_widget("alt_download_limit")
            if alt_download_limit:
                alt_download_limit.set_value(0)
            # Reset scheduler
            enable_scheduler = self.get_widget("enable_scheduler")
            if enable_scheduler:
                self.set_switch_state(enable_scheduler, False)
            self.update_dependencies()
            self.show_notification("Speed settings reset to defaults", "success")
        except Exception as e:
            self.logger.error(f"Error resetting Speed tab to defaults: {e}")

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.trace(
            "SpeedTab update view",
            extra={"class_name": self.__class__.__name__},
        )

    # Speed distribution signal handlers
    def on_upload_dist_algorithm_changed(self, dropdown, _param) -> None:
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

    def on_upload_dist_mode_changed(self, dropdown, _param) -> None:
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

    def on_download_dist_algorithm_changed(self, dropdown, _param) -> None:
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

    def on_download_dist_mode_changed(self, dropdown, _param) -> None:
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
