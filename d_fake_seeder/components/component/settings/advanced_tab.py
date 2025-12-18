"""
Advanced settings tab for the settings dialog.

Handles advanced configuration, logging, search functionality, and expert settings.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import KeyboardShortcutMixin  # noqa: E402
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import (  # noqa: E402
    TranslationMixin,
    UtilityMixin,
    ValidationMixin,
)

# fmt: on


class AdvancedTab(
    BaseSettingsTab,
    NotificationMixin,
    TranslationMixin,
    ValidationMixin,
    UtilityMixin,
    KeyboardShortcutMixin,
):
    """
    Advanced settings tab component.

    Manages:
    - Settings search functionality
    - Logging configuration
    - Performance settings
    - Expert/debug options
    - Keyboard shortcuts
    """

    # Note: Advanced settings use manual loading/saving with nested keys
    WIDGET_MAPPINGS: list = []

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Advanced"

    def _init_widgets(self) -> None:
        """Initialize Advanced tab widgets using correct XML IDs."""
        # Cache commonly used widgets
        self._widgets.update(
            {
                # Search functionality
                "search_entry": self.builder.get_object("settings_search_entry"),
                "search_clear": self.builder.get_object("settings_search_clear"),
                # Logging (use correct XML IDs)
                "log_level": self.builder.get_object("settings_log_level"),
                "log_to_file": self.builder.get_object("settings_log_to_file"),
                "log_file_box": self.builder.get_object("settings_log_file_box"),
                "log_max_size": self.builder.get_object("settings_max_log_size"),
                # Performance (use correct XML IDs)
                "disk_cache_size": self.builder.get_object("settings_disk_cache_size"),
                "ui_refresh_rate": self.builder.get_object("settings_ui_refresh_rate"),
                "network_interface": self.builder.get_object("settings_network_interface"),
                # Expert settings (use correct XML IDs)
                "debug_mode": self.builder.get_object("settings_debug_mode"),
                "validate_settings": self.builder.get_object("settings_validate_settings"),
                "auto_save": self.builder.get_object("settings_auto_save"),
                # Keyboard shortcuts list (display only)
                "shortcuts_list": self.builder.get_object("settings_shortcuts_list"),
            }
        )

        self.logger.trace(
            "Advanced tab widgets initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _connect_signals(self) -> None:
        """Connect signal handlers for Advanced tab."""
        # Simple widgets (search_threshold, log_file_path, log_max_size, log_backup_count,
        # disk_cache_size, memory_limit, worker_threads, enable_debug_mode, enable_experimental)
        # are now auto-connected via WIDGET_MAPPINGS

        # Search functionality (complex logic)
        search_entry = self.get_widget("search_entry")
        if search_entry:
            self.track_signal(
                search_entry,
                search_entry.connect("search-changed", self.on_search_changed),
            )

        search_clear = self.get_widget("search_clear")
        if search_clear:
            self.track_signal(
                search_clear,
                search_clear.connect("clicked", self.on_search_clear_clicked),
            )

        # Logging (custom dropdown + reconfigure_logger calls)
        log_level = self.get_widget("log_level")
        if log_level:
            self.track_signal(
                log_level,
                log_level.connect("notify::selected", self.on_log_level_changed),
            )

        log_to_file = self.get_widget("log_to_file")
        if log_to_file:
            self.track_signal(
                log_to_file,
                log_to_file.connect("state-set", self.on_log_to_file_changed),
            )

        log_to_console = self.get_widget("log_to_console")
        if log_to_console:
            self.track_signal(
                log_to_console,
                log_to_console.connect("state-set", self.on_log_to_console_changed),
            )

        log_to_systemd = self.get_widget("log_to_systemd")
        if log_to_systemd:
            self.track_signal(
                log_to_systemd,
                log_to_systemd.connect("state-set", self.on_log_to_systemd_changed),
            )

        log_file_browse = self.get_widget("log_file_browse")
        if log_file_browse:
            self.track_signal(
                log_file_browse,
                log_file_browse.connect("clicked", self.on_log_file_browse_clicked),
            )

        # Expert settings (complex button handlers + shortcuts with dependencies)
        config_export = self.get_widget("config_export")
        if config_export:
            self.track_signal(
                config_export,
                config_export.connect("clicked", self.on_config_export_clicked),
            )

        config_import = self.get_widget("config_import")
        if config_import:
            self.track_signal(
                config_import,
                config_import.connect("clicked", self.on_config_import_clicked),
            )

        reset_all = self.get_widget("reset_all_settings")
        if reset_all:
            self.track_signal(reset_all, reset_all.connect("clicked", self.on_reset_all_clicked))

        # Keyboard shortcuts (has dependencies - controls shortcuts_config widget)
        enable_shortcuts = self.get_widget("enable_shortcuts")
        if enable_shortcuts:
            self.track_signal(
                enable_shortcuts,
                enable_shortcuts.connect("state-set", self.on_enable_shortcuts_changed),
            )

        shortcuts_config = self.get_widget("shortcuts_config")
        if shortcuts_config:
            self.track_signal(
                shortcuts_config,
                shortcuts_config.connect("clicked", self.on_shortcuts_config_clicked),
            )

    def _load_settings(self) -> None:
        """Load current settings into Advanced tab widgets using nested keys."""
        try:
            # Load logging settings
            if self._widgets.get("log_level"):
                level = self.app_settings.get("logging.level", "INFO")
                level_mapping = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3, "CRITICAL": 4}
                self._widgets["log_level"].set_selected(level_mapping.get(level, 1))

            if self._widgets.get("log_to_file"):
                value = self.app_settings.get("logging.log_to_file", False)
                self._widgets["log_to_file"].set_state(value)

            if self._widgets.get("log_max_size"):
                value = self.app_settings.get("logging.max_size_mb", 10)
                self._widgets["log_max_size"].set_value(value)

            # Load performance settings
            if self._widgets.get("disk_cache_size"):
                value = self.app_settings.get("performance.disk_cache_size_mb", 64)
                self._widgets["disk_cache_size"].set_value(value)

            if self._widgets.get("ui_refresh_rate"):
                value = self.app_settings.get("performance.ui_refresh_rate_sec", 9)
                self._widgets["ui_refresh_rate"].set_value(value)

            if self._widgets.get("network_interface"):
                value = self.app_settings.get("performance.network_interface", "")
                self._widgets["network_interface"].set_text(value)

            # Load expert settings
            if self._widgets.get("debug_mode"):
                value = self.app_settings.get("expert.debug_mode", False)
                self._widgets["debug_mode"].set_state(value)

            if self._widgets.get("validate_settings"):
                value = self.app_settings.get("expert.validate_settings", True)
                self._widgets["validate_settings"].set_state(value)

            if self._widgets.get("auto_save"):
                value = self.app_settings.get("expert.auto_save", True)
                self._widgets["auto_save"].set_state(value)

            self.logger.trace("Advanced tab settings loaded")

        except Exception as e:
            self.logger.error(f"Error loading Advanced tab settings: {e}")

    def _load_search_settings(self, search_settings: Dict[str, Any]) -> None:
        """Load search-related settings."""
        try:
            search_threshold = self.get_widget("search_threshold")
            if search_threshold:
                search_threshold.set_value(search_settings.get("threshold", 0.6))

        except Exception as e:
            self.logger.error(f"Error loading search settings: {e}")

    def _load_logging_settings(self, logging_settings: Dict[str, Any]) -> None:
        """Load logging configuration."""
        try:
            # Log level
            log_level = self.get_widget("log_level")
            if log_level:
                level = logging_settings.get("level", "INFO")
                level_mapping = {
                    "TRACE": 0,
                    "DEBUG": 1,
                    "INFO": 2,
                    "WARNING": 3,
                    "ERROR": 4,
                    "CRITICAL": 5,
                }
                log_level.set_selected(level_mapping.get(level, 2))

            # Log to file
            log_to_file = self.get_widget("log_to_file")
            if log_to_file:
                self.set_switch_state(log_to_file, logging_settings.get("log_to_file", False))

            # Log to console
            log_to_console = self.get_widget("log_to_console")
            if log_to_console:
                self.set_switch_state(log_to_console, logging_settings.get("log_to_console", False))

            # Log to systemd
            log_to_systemd = self.get_widget("log_to_systemd")
            if log_to_systemd:
                self.set_switch_state(log_to_systemd, logging_settings.get("log_to_systemd", True))

            # Log file path
            log_file_path = self.get_widget("log_file_path")
            if log_file_path:
                log_file_path.set_text(logging_settings.get("log_file_path", ""))

            # Log file settings
            log_max_size = self.get_widget("log_max_size")
            if log_max_size:
                log_max_size.set_value(logging_settings.get("max_size_mb", 10))

            log_backup_count = self.get_widget("log_backup_count")
            if log_backup_count:
                log_backup_count.set_value(logging_settings.get("backup_count", 5))

        except Exception as e:
            self.logger.error(f"Error loading logging settings: {e}")

    def _load_performance_settings(self, performance_settings: Dict[str, Any]) -> None:
        """Load performance configuration."""
        try:
            disk_cache_size = self.get_widget("disk_cache_size")
            if disk_cache_size:
                disk_cache_size.set_value(performance_settings.get("disk_cache_size_mb", 256))

            memory_limit = self.get_widget("memory_limit")
            if memory_limit:
                memory_limit.set_value(performance_settings.get("memory_limit_mb", 512))

            worker_threads = self.get_widget("worker_threads")
            if worker_threads:
                worker_threads.set_value(performance_settings.get("worker_threads", 4))

        except Exception as e:
            self.logger.error(f"Error loading performance settings: {e}")

    def _load_expert_settings(self, expert_settings: Dict[str, Any]) -> None:
        """Load expert/debug settings."""
        try:
            enable_debug = self.get_widget("enable_debug_mode")
            if enable_debug:
                self.set_switch_state(enable_debug, expert_settings.get("debug_mode", False))

            enable_experimental = self.get_widget("enable_experimental")
            if enable_experimental:
                self.set_switch_state(enable_experimental, expert_settings.get("experimental_features", False))

            enable_shortcuts = self.get_widget("enable_shortcuts")
            if enable_shortcuts:
                self.set_switch_state(enable_shortcuts, expert_settings.get("keyboard_shortcuts", True))

        except Exception as e:
            self.logger.error(f"Error loading expert settings: {e}")

    def _setup_log_level_dropdown(self) -> None:
        """Set up the log level dropdown."""
        try:
            log_level_dropdown = self.get_widget("log_level")
            if not log_level_dropdown:
                return

            # Log levels
            levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

            # Create string list model
            string_list = Gtk.StringList()
            for level in levels:
                string_list.append(level)

            # Set model
            log_level_dropdown.set_model(string_list)

            self.logger.trace(f"Log level dropdown set up with {len(levels)} levels")

        except Exception as e:
            self.logger.error(f"Error setting up log level dropdown: {e}")

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Advanced tab."""
        self._update_logging_dependencies()
        self._update_expert_dependencies()

    def _update_tab_dependencies(self) -> None:
        """Update Advanced tab dependencies."""
        self._update_logging_dependencies()
        self._update_expert_dependencies()

    def _update_logging_dependencies(self) -> None:
        """Update logging-related widget dependencies."""
        try:
            log_to_file = self.get_widget("log_to_file")
            file_logging_enabled = log_to_file and log_to_file.get_active()

            # IMPORTANT: Enable the parent box first (hardcoded to sensitive=False in XML)
            self.update_widget_sensitivity("log_file_box", file_logging_enabled)
            self.update_widget_sensitivity("log_file_path", file_logging_enabled)
            self.update_widget_sensitivity("log_file_browse", file_logging_enabled)
            self.update_widget_sensitivity("log_max_size", file_logging_enabled)
            self.update_widget_sensitivity("log_backup_count", file_logging_enabled)

        except Exception as e:
            self.logger.error(f"Error updating logging dependencies: {e}")

    def _update_expert_dependencies(self) -> None:
        """Update expert settings dependencies."""
        try:
            enable_shortcuts = self.get_widget("enable_shortcuts")
            shortcuts_enabled = enable_shortcuts and enable_shortcuts.get_active()

            self.update_widget_sensitivity("shortcuts_config", shortcuts_enabled)

        except Exception as e:
            self.logger.error(f"Error updating expert dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Advanced tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        settings: Dict[str, Any] = {}

        try:
            # Collect logging settings
            if self._widgets.get("log_level"):
                level_mapping = {0: "DEBUG", 1: "INFO", 2: "WARNING", 3: "ERROR", 4: "CRITICAL"}
                settings["logging.level"] = level_mapping.get(self._widgets["log_level"].get_selected(), "INFO")

            if self._widgets.get("log_to_file"):
                settings["logging.log_to_file"] = self._widgets["log_to_file"].get_state()

            if self._widgets.get("log_max_size"):
                settings["logging.max_size_mb"] = int(self._widgets["log_max_size"].get_value())

            # Collect performance settings
            if self._widgets.get("disk_cache_size"):
                settings["performance.disk_cache_size_mb"] = int(self._widgets["disk_cache_size"].get_value())

            if self._widgets.get("ui_refresh_rate"):
                settings["performance.ui_refresh_rate_sec"] = int(self._widgets["ui_refresh_rate"].get_value())

            if self._widgets.get("network_interface"):
                settings["performance.network_interface"] = self._widgets["network_interface"].get_text()

            # Collect expert settings
            if self._widgets.get("debug_mode"):
                settings["expert.debug_mode"] = self._widgets["debug_mode"].get_state()

            if self._widgets.get("validate_settings"):
                settings["expert.validate_settings"] = self._widgets["validate_settings"].get_state()

            if self._widgets.get("auto_save"):
                settings["expert.auto_save"] = self._widgets["auto_save"].get_state()

            self.logger.trace(f"Collected {len(settings)} settings from Advanced tab")

        except Exception as e:
            self.logger.error(f"Error collecting Advanced tab settings: {e}")

        return settings

    def _collect_search_settings(self) -> Dict[str, Any]:
        """Collect search settings."""
        search_settings = {}

        try:
            search_threshold = self.get_widget("search_threshold")
            if search_threshold:
                search_settings["threshold"] = search_threshold.get_value()

        except Exception as e:
            self.logger.error(f"Error collecting search settings: {e}")

        return search_settings

    def _collect_logging_settings(self) -> Dict[str, Any]:
        """Collect logging settings."""
        logging_settings: Dict[str, Any] = {}

        try:
            log_level = self.get_widget("log_level")
            if log_level:
                level_mapping = {
                    0: "TRACE",
                    1: "DEBUG",
                    2: "INFO",
                    3: "WARNING",
                    4: "ERROR",
                    5: "CRITICAL",
                }
                logging_settings["level"] = level_mapping.get(log_level.get_selected(), "INFO")

            log_to_file = self.get_widget("log_to_file")
            if log_to_file:
                logging_settings["log_to_file"] = log_to_file.get_active()

            log_to_console = self.get_widget("log_to_console")
            if log_to_console:
                logging_settings["log_to_console"] = log_to_console.get_active()

            log_to_systemd = self.get_widget("log_to_systemd")
            if log_to_systemd:
                logging_settings["log_to_systemd"] = log_to_systemd.get_active()

            log_file_path = self.get_widget("log_file_path")
            if log_file_path:
                logging_settings["log_file_path"] = log_file_path.get_text()

            log_max_size = self.get_widget("log_max_size")
            if log_max_size:
                logging_settings["max_size_mb"] = int(log_max_size.get_value())

            log_backup_count = self.get_widget("log_backup_count")
            if log_backup_count:
                logging_settings["backup_count"] = int(log_backup_count.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting logging settings: {e}")

        return logging_settings

    def _collect_performance_settings(self) -> Dict[str, Any]:
        """Collect performance settings."""
        performance_settings = {}

        try:
            disk_cache_size = self.get_widget("disk_cache_size")
            if disk_cache_size:
                performance_settings["disk_cache_size_mb"] = int(disk_cache_size.get_value())

            memory_limit = self.get_widget("memory_limit")
            if memory_limit:
                performance_settings["memory_limit_mb"] = int(memory_limit.get_value())

            worker_threads = self.get_widget("worker_threads")
            if worker_threads:
                performance_settings["worker_threads"] = int(worker_threads.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting performance settings: {e}")

        return performance_settings

    def _collect_expert_settings(self) -> Dict[str, Any]:
        """Collect expert settings."""
        expert_settings = {}

        try:
            enable_debug = self.get_widget("enable_debug_mode")
            if enable_debug:
                expert_settings["debug_mode"] = enable_debug.get_active()

            enable_experimental = self.get_widget("enable_experimental")
            if enable_experimental:
                expert_settings["experimental_features"] = enable_experimental.get_active()

            enable_shortcuts = self.get_widget("enable_shortcuts")
            if enable_shortcuts:
                expert_settings["keyboard_shortcuts"] = enable_shortcuts.get_active()

        except Exception as e:
            self.logger.error(f"Error collecting expert settings: {e}")

        return expert_settings

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Advanced tab settings."""
        errors = {}

        try:
            # Validate performance settings
            worker_threads = self.get_widget("worker_threads")
            if worker_threads:
                threads = int(worker_threads.get_value())
                if threads < 1 or threads > 32:
                    errors["worker_threads"] = "Worker threads must be between 1 and 32"

            # Validate log file path if logging to file is enabled
            log_to_file = self.get_widget("log_to_file")
            if log_to_file and log_to_file.get_active():
                log_file_path = self.get_widget("log_file_path")
                if log_file_path:
                    path = log_file_path.get_text().strip()
                    if not path:
                        errors["log_file_path"] = "Log file path cannot be empty when file logging is enabled"

        except Exception as e:
            self.logger.error(f"Error validating Advanced tab settings: {e}")
            errors["general"] = str(e)

        return errors

    # Signal handlers
    def on_search_changed(self, search_entry: Gtk.SearchEntry) -> None:
        """Handle settings search."""
        try:
            search_text = search_entry.get_text()
            self.logger.trace(f"Settings search: {search_text}")
            # TODO: Implement actual search filtering
        except Exception as e:
            self.logger.error(f"Error handling search: {e}")

    def on_search_clear_clicked(self, button: Gtk.Button) -> None:
        """Clear search."""
        try:
            search_entry = self.get_widget("search_entry")
            if search_entry:
                search_entry.set_text("")
        except Exception as e:
            self.logger.error(f"Error clearing search: {e}")

    def on_log_level_changed(self, dropdown: Gtk.DropDown, _param: Any) -> None:
        """Handle log level change."""
        try:
            level_mapping = {
                0: "TRACE",
                1: "DEBUG",
                2: "INFO",
                3: "WARNING",
                4: "ERROR",
                5: "CRITICAL",
            }
            level = level_mapping.get(dropdown.get_selected(), "INFO")
            # NOTE: Setting will be saved in batch via _collect_settings()
            self.logger.trace(f"Log level will change to: {level}")
            # Trigger logger reconfiguration will happen after save
        except Exception as e:
            self.logger.error(f"Error changing log level: {e}")

    def on_log_to_file_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle log to file toggle."""
        try:
            self.update_dependencies()
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "File logging will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
            # Trigger logger reconfiguration will happen after save
        except Exception as e:
            self.logger.error(f"Error changing log to file setting: {e}")

    def on_log_to_console_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle log to console toggle."""
        try:
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Console logging will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
            # Trigger logger reconfiguration will happen after save
        except Exception as e:
            self.logger.error(f"Error changing log to console setting: {e}")

    def on_log_to_systemd_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle log to systemd toggle."""
        try:
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Systemd journal logging will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
            # Trigger logger reconfiguration will happen after save
        except Exception as e:
            self.logger.error(f"Error changing log to systemd setting: {e}")

    def on_log_file_browse_clicked(self, button: Gtk.Button) -> None:
        """Open file chooser for log file."""
        try:
            # TODO: Implement file chooser dialog
            self.show_notification("File chooser not yet implemented", "info")
        except Exception as e:
            self.logger.error(f"Error opening file chooser: {e}")

    def on_config_export_clicked(self, button: Gtk.Button) -> None:
        """Export configuration."""
        try:
            # TODO: Implement config export
            self.show_notification("Config export not yet implemented", "info")
        except Exception as e:
            self.logger.error(f"Error exporting config: {e}")

    def on_config_import_clicked(self, button: Gtk.Button) -> None:
        """Import configuration."""
        try:
            # TODO: Implement config import
            self.show_notification("Config import not yet implemented", "info")
        except Exception as e:
            self.logger.error(f"Error importing config: {e}")

    def on_reset_all_clicked(self, button: Gtk.Button) -> None:
        """Reset all settings to defaults."""
        try:
            # TODO: Implement confirmation dialog and reset all settings
            self.show_notification("Reset all settings not yet implemented", "warning")
        except Exception as e:
            self.logger.error(f"Error resetting all settings: {e}")

    def on_enable_shortcuts_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle keyboard shortcuts toggle."""
        try:
            self.update_dependencies()
            # NOTE: Setting will be saved in batch via _collect_settings()
            message = "Keyboard shortcuts will be " + ("enabled" if state else "disabled")
            self.show_notification(message, "info")
        except Exception as e:
            self.logger.error(f"Error changing keyboard shortcuts: {e}")

    def on_shortcuts_config_clicked(self, button: Gtk.Button) -> None:
        """Open shortcuts configuration."""
        try:
            # TODO: Implement shortcuts configuration dialog
            self.show_notification("Shortcuts configuration not yet implemented", "info")
        except Exception as e:
            self.logger.error(f"Error opening shortcuts config: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset Advanced tab to default values."""
        try:
            # Reset search settings
            search_threshold = self.get_widget("search_threshold")
            if search_threshold:
                search_threshold.set_value(0.6)

            # Reset logging
            log_level = self.get_widget("log_level")
            if log_level:
                log_level.set_selected(1)  # INFO

            log_to_file = self.get_widget("log_to_file")
            if log_to_file:
                self.set_switch_state(log_to_file, False)

            # Reset performance
            disk_cache_size = self.get_widget("disk_cache_size")
            if disk_cache_size:
                disk_cache_size.set_value(256)

            memory_limit = self.get_widget("memory_limit")
            if memory_limit:
                memory_limit.set_value(512)

            worker_threads = self.get_widget("worker_threads")
            if worker_threads:
                worker_threads.set_value(4)

            # Reset expert settings
            enable_debug = self.get_widget("enable_debug_mode")
            if enable_debug:
                self.set_switch_state(enable_debug, False)

            enable_experimental = self.get_widget("enable_experimental")
            if enable_experimental:
                self.set_switch_state(enable_experimental, False)

            enable_shortcuts = self.get_widget("enable_shortcuts")
            if enable_shortcuts:
                self.set_switch_state(enable_shortcuts, True)

            self.update_dependencies()
            self.show_notification("Advanced settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting Advanced tab to defaults: {e}")

    def _reconfigure_logger(self) -> None:
        """Reconfigure logger with current settings - applies changes immediately."""
        try:
            # Import reconfigure_logger from logger module
            from d_fake_seeder.lib.logger import reconfigure_logger

            # Reconfigure the logger with new settings
            reconfigure_logger()
            self.logger.trace(
                "Logger reconfigured with new settings",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            self.logger.error(f"Error reconfiguring logger: {e}", exc_info=True)

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace(
            "AdvancedTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()
