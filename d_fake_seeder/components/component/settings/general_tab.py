"""
General settings tab for the settings dialog.
Handles general application settings like auto-start, minimized start,
language selection, and other basic preferences.
"""

# isort: skip_file

# fmt: off
from typing import Any, Dict

import gi

from d_fake_seeder.lib.logger import logger

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from d_fake_seeder.lib.seeding_profile_manager import (  # noqa: E402
    SeedingProfileManager,
)
from d_fake_seeder.lib.util.language_config import (  # noqa: E402
    get_language_display_names,
    get_supported_language_codes,
)

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import TranslationMixin  # noqa: E402
from .settings_mixins import UtilityMixin  # noqa: E402
from .settings_mixins import ValidationMixin  # noqa: E402

# fmt: on


class GeneralTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """
    General settings tab component.
    Manages:
    - Application startup behavior (auto-start, start minimized)
    - Theme preferences
    - Basic UI preferences
    """

    # Original English dropdown items (used as translation keys)
    THEME_STYLE_ITEMS = ["System Theme", "Deluge Theme", "Modern Chunky"]
    COLOR_SCHEME_ITEMS = ["Auto (Follow System)", "Light", "Dark"]
    PROFILE_ITEMS = ["Conservative", "Balanced", "Aggressive", "Custom"]

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS = [
        # Application startup behavior
        {
            "id": "settings_auto_start",
            "name": "auto_start",
            "setting_key": "auto_start",
            "type": bool,
        },
        {
            "id": "settings_start_minimized",
            "name": "start_minimized",
            "setting_key": "start_minimized",
            "type": bool,
        },
        {
            "id": "settings_minimize_to_tray",
            "name": "minimize_to_tray",
            "setting_key": "minimize_to_tray",
            "type": bool,
        },
        {
            "id": "settings_remember_window_size",
            "name": "remember_window_size",
            "setting_key": "remember_window_size",
            "type": bool,
        },
        # Watch folder settings
        {
            "id": "settings_watch_folder_enabled",
            "name": "watch_folder_enabled",
            "setting_key": "watch_folder.enabled",
            "type": bool,
            "enables": [
                "watch_folder_path",
                "watch_folder_browse",
                "watch_folder_scan_interval",
                "watch_folder_auto_start",
                "watch_folder_delete_added",
            ],
            "on_change": lambda self, value: self.show_notification(
                f"Watch folder {'enabled' if value else 'disabled'}", "success"
            ),
        },
        {
            "id": "settings_watch_folder_path",
            "name": "watch_folder_path",
            "setting_key": "watch_folder.path",
            "type": str,
        },
        {
            "id": "settings_watch_folder_scan_interval",
            "name": "watch_folder_scan_interval",
            "setting_key": "watch_folder.scan_interval_seconds",
            "type": int,
        },
        {
            "id": "settings_watch_folder_auto_start",
            "name": "watch_folder_auto_start",
            "setting_key": "watch_folder.auto_start_torrents",
            "type": bool,
        },
        {
            "id": "settings_watch_folder_delete_added",
            "name": "watch_folder_delete_added",
            "setting_key": "watch_folder.delete_added_torrents",
            "type": bool,
        },
    ]

    def __init__(self, builder: Gtk.Builder, app_settings: Any, app: Any = None) -> None:
        """Initialize the General tab."""
        self.app = app
        # Initialize seeding profile manager BEFORE super().__init__
        # because _update_ui_from_settings (called during super().__init__) needs it
        self.profile_manager = SeedingProfileManager(app_settings)
        super().__init__(builder, app_settings)

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "General"

    def _init_widgets(self) -> None:
        """Initialize General tab widgets."""
        logger.trace("===== _init_widgets() CALLED =====", "GeneralTab")
        logger.trace(f"Builder: {self.builder}", "GeneralTab")
        # Let's try to debug what objects are available in the builder
        if self.builder:
            logger.trace("Checking for language-related objects in builder...", "GeneralTab")
            # Try various possible names for the language dropdown
            possible_names = [
                "settings_language",
                "language_dropdown",
                "language_combo",
                "language_combobox",
                "language_selection",
                "combo_language",
                "general_language",
                "preferences_language",
            ]
            for name in possible_names:
                obj = self.builder.get_object(name)
                logger.trace(
                    f"- {name}: {obj} (type: {type(obj).__name__ if obj else 'None'})",
                    "GeneralTab",
                )
        # Cache commonly used widgets
        widget_objects = {
            "auto_start": self.builder.get_object("settings_auto_start"),
            "start_minimized": self.builder.get_object("settings_start_minimized"),
            "minimize_to_tray": self.builder.get_object("settings_minimize_to_tray"),
            "remember_window_size": self.builder.get_object("settings_remember_window_size"),
            "language_dropdown": self.builder.get_object("settings_language"),
            # Configuration management buttons
            "export_button": self.builder.get_object("settings_export_button"),
            "import_button": self.builder.get_object("settings_import_button"),
            "reset_button": self.builder.get_object("general_reset_button"),
            # Watch folder widgets
            "watch_folder_enabled": self.builder.get_object("settings_watch_folder_enabled"),
            "watch_folder_path": self.builder.get_object("settings_watch_folder_path"),
            "watch_folder_browse": self.builder.get_object("settings_watch_folder_browse"),
            "watch_folder_scan_interval": self.builder.get_object("settings_watch_folder_scan_interval"),
            "watch_folder_auto_start": self.builder.get_object("settings_watch_folder_auto_start"),
            "watch_folder_delete_added": self.builder.get_object("settings_watch_folder_delete_added"),
        }
        logger.trace("Widget lookup completed", "GeneralTab")
        self._widgets.update(widget_objects)
        # Initialize language dropdown if available
        logger.trace("About to call _setup_language_dropdown()...", "GeneralTab")
        self._setup_language_dropdown()
        logger.trace("_init_widgets() completed", "GeneralTab")

    def _connect_signals(self) -> None:
        """Connect signal handlers for General tab."""
        # Simple widgets (auto_start, start_minimized, minimize_to_tray, remember_window_size,
        # watch_folder_enabled, watch_folder_path, watch_folder_scan_interval,
        # watch_folder_auto_start, watch_folder_delete_added) are now auto-connected via WIDGET_MAPPINGS

        # Configuration management buttons
        export_button = self.get_widget("export_button")
        if export_button:
            self.track_signal(
                export_button,
                export_button.connect("clicked", self.on_export_clicked),
            )

        import_button = self.get_widget("import_button")
        if import_button:
            self.track_signal(
                import_button,
                import_button.connect("clicked", self.on_import_clicked),
            )

        reset_button = self.get_widget("reset_button")
        if reset_button:
            self.track_signal(
                reset_button,
                reset_button.connect("clicked", self.on_reset_clicked),
            )

        # Theme style dropdown
        theme_style_dropdown = self.get_widget("settings_theme")
        if theme_style_dropdown:
            self.track_signal(
                theme_style_dropdown,
                theme_style_dropdown.connect("notify::selected", self.on_theme_style_changed),
            )
        # Color scheme dropdown
        color_scheme_dropdown = self.get_widget("settings_color_scheme")
        if color_scheme_dropdown:
            self.track_signal(
                color_scheme_dropdown,
                color_scheme_dropdown.connect("notify::selected", self.on_color_scheme_changed),
            )
        # Seeding profile dropdown
        profile_dropdown = self.get_widget("settings_seeding_profile")
        if profile_dropdown:
            self.track_signal(
                profile_dropdown,
                profile_dropdown.connect("notify::selected", self.on_seeding_profile_changed),
            )

        # Watch folder browse button (complex logic, keep manual)
        watch_folder_browse = self.get_widget("watch_folder_browse")
        if watch_folder_browse:
            self.track_signal(
                watch_folder_browse,
                watch_folder_browse.connect("clicked", self.on_watch_folder_browse_clicked),
            )

        # Language dropdown - signal connection handled in _setup_language_dropdown()
        # to avoid dual connections and ensure proper disconnect/reconnect during population

    def _load_settings(self) -> None:
        """Load current settings into General tab widgets."""
        try:
            self.logger.trace("Loading General tab settings", "GeneralTab")

            # Auto-start setting
            auto_start = self.get_widget("auto_start")
            if auto_start:
                self.set_switch_state(auto_start, getattr(self.app_settings, "auto_start", False))
            # Start minimized setting
            start_minimized = self.get_widget("start_minimized")
            if start_minimized:
                self.set_switch_state(start_minimized, getattr(self.app_settings, "start_minimized", False))

            # Minimize to tray setting
            minimize_to_tray = self.get_widget("minimize_to_tray")
            if minimize_to_tray:
                self.set_switch_state(minimize_to_tray, getattr(self.app_settings, "minimize_to_tray", False))

            # Remember window size setting
            remember_window_size = self.get_widget("remember_window_size")
            if remember_window_size:
                self.set_switch_state(remember_window_size, getattr(self.app_settings, "remember_window_size", True))

            # Theme style setting - load from ui_settings.theme_style
            theme_style_dropdown = self.get_widget("settings_theme")
            if theme_style_dropdown:
                ui_settings = getattr(self.app_settings, "ui_settings", {})
                current_theme_style = ui_settings.get("theme_style", "classic")
                theme_style_mapping = {"system": 0, "classic": 1, "modern": 2}
                theme_style_dropdown.set_selected(theme_style_mapping.get(current_theme_style, 1))
            # Color scheme setting - load from ui_settings.color_scheme
            color_scheme_dropdown = self.get_widget("settings_color_scheme")
            if color_scheme_dropdown:
                ui_settings = getattr(self.app_settings, "ui_settings", {})
                current_color_scheme = ui_settings.get("color_scheme", "auto")
                color_scheme_mapping = {"auto": 0, "light": 1, "dark": 2}
                color_scheme_dropdown.set_selected(color_scheme_mapping.get(current_color_scheme, 0))
            # Seeding profile setting
            profile_dropdown = self.get_widget("settings_seeding_profile")
            if profile_dropdown:
                current_profile = self.profile_manager.get_current_profile()
                profile_index = self.profile_manager.get_profile_dropdown_index(current_profile)
                profile_dropdown.set_selected(profile_index)

            # Watch folder settings
            watch_folder_config = getattr(self.app_settings, "watch_folder", {})

            watch_folder_enabled = self.get_widget("watch_folder_enabled")
            if watch_folder_enabled:
                self.set_switch_state(watch_folder_enabled, watch_folder_config.get("enabled", False))

            watch_folder_path = self.get_widget("watch_folder_path")
            if watch_folder_path:
                watch_folder_path.set_text(watch_folder_config.get("path", ""))

            watch_folder_scan_interval = self.get_widget("watch_folder_scan_interval")
            if watch_folder_scan_interval:
                watch_folder_scan_interval.set_value(watch_folder_config.get("scan_interval_seconds", 10))

            watch_folder_auto_start = self.get_widget("watch_folder_auto_start")
            if watch_folder_auto_start:
                self.set_switch_state(watch_folder_auto_start, watch_folder_config.get("auto_start_torrents", True))

            watch_folder_delete_added = self.get_widget("watch_folder_delete_added")
            if watch_folder_delete_added:
                self.set_switch_state(
                    watch_folder_delete_added, watch_folder_config.get("delete_added_torrents", False)
                )

            self.logger.info("General tab settings loaded successfully", "GeneralTab")
        except Exception as e:
            self.logger.error(f"Error loading General tab settings: {e}", exc_info=True)

    def _setup_dependencies(self) -> None:
        """Set up dependencies for General tab."""
        # General tab typically doesn't have complex dependencies
        pass

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from General tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        # Collect from WIDGET_MAPPINGS (auto_start, start_minimized, minimize_to_tray,
        # remember_window_size, watch_folder settings)
        settings = self._collect_mapped_settings()

        # Collect manual widgets not in WIDGET_MAPPINGS

        # Theme style dropdown
        theme_dropdown = self.get_widget("settings_theme")
        if theme_dropdown:
            theme_style_values = ["system", "classic", "modern"]
            selected_index = theme_dropdown.get_selected()
            if 0 <= selected_index < len(theme_style_values):
                settings["ui_settings.theme_style"] = theme_style_values[selected_index]

        # Color scheme dropdown
        color_scheme_dropdown = self.get_widget("settings_color_scheme")
        if color_scheme_dropdown:
            color_scheme_values = ["auto", "light", "dark"]
            selected_index = color_scheme_dropdown.get_selected()
            if 0 <= selected_index < len(color_scheme_values):
                settings["ui_settings.color_scheme"] = color_scheme_values[selected_index]

        # Seeding profile - collect the selected profile name (don't apply it)
        # NOTE: Profile is applied immediately when user changes dropdown via on_seeding_profile_changed()
        # We only collect the setting value here for persistence
        profile_dropdown = self.get_widget("settings_seeding_profile")
        if profile_dropdown:
            selected_index = profile_dropdown.get_selected()
            profile_name = self.profile_manager.get_profile_from_dropdown_index(selected_index)
            settings["seeding_profile"] = profile_name
            logger.trace(f"Collected seeding profile: {profile_name}", "GeneralTab")

        # Language dropdown
        language_dropdown = self.get_widget("language_dropdown")
        if language_dropdown and hasattr(self, "language_codes"):
            selected_index = language_dropdown.get_selected()
            if 0 <= selected_index < len(self.language_codes):
                settings["language"] = self.language_codes[selected_index]

        logger.trace(f"Collected {len(settings)} settings from General tab", "GeneralTab")
        return settings

    def on_export_clicked(self, button: Gtk.Button) -> None:
        """Handle export settings button click."""
        try:
            from gi.repository import Gio

            # Create file chooser dialog
            dialog = Gtk.FileDialog()
            dialog.set_title("Export Settings")

            # Set initial name
            dialog.set_initial_name("dfakeseeder-settings.json")

            # Create file filter for JSON files
            json_filter = Gtk.FileFilter()
            json_filter.set_name("JSON files")
            json_filter.add_pattern("*.json")

            all_filter = Gtk.FileFilter()
            all_filter.set_name("All files")
            all_filter.add_pattern("*")

            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(json_filter)
            filters.append(all_filter)
            dialog.set_filters(filters)

            # Get parent window
            parent = button.get_root()

            # Show save dialog
            dialog.save(parent, None, self._on_export_file_selected)

        except Exception as e:
            self.logger.error(f"Error showing export dialog: {e}", exc_info=True)
            self.show_notification(f"Error exporting settings: {e}", "error")

    def _on_export_file_selected(self, dialog: Any, result: Any) -> None:
        """Handle file selection for export."""
        try:
            file = dialog.save_finish(result)
            if file:
                file_path = file.get_path()
                # Export settings
                self.app_settings.export_settings(file_path)
                self.show_notification(f"Settings exported to {file_path}", "success")
                self.logger.info(f"Settings exported to: {file_path}")
        except Exception as e:
            if "dismissed" not in str(e).lower():  # Don't show error if user cancelled
                self.logger.error(f"Error exporting settings: {e}", exc_info=True)
                self.show_notification(f"Error exporting settings: {e}", "error")

    def on_import_clicked(self, button: Gtk.Button) -> None:
        """Handle import settings button click."""
        try:
            from gi.repository import Gio

            # Create file chooser dialog
            dialog = Gtk.FileDialog()
            dialog.set_title("Import Settings")

            # Create file filter for JSON files
            json_filter = Gtk.FileFilter()
            json_filter.set_name("JSON files")
            json_filter.add_pattern("*.json")

            all_filter = Gtk.FileFilter()
            all_filter.set_name("All files")
            all_filter.add_pattern("*")

            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(json_filter)
            filters.append(all_filter)
            dialog.set_filters(filters)

            # Get parent window
            parent = button.get_root()

            # Show open dialog
            dialog.open(parent, None, self._on_import_file_selected)

        except Exception as e:
            self.logger.error(f"Error showing import dialog: {e}", exc_info=True)
            self.show_notification(f"Error importing settings: {e}", "error")

    def _on_import_file_selected(self, dialog: Any, result: Any) -> None:
        """Handle file selection for import."""
        try:
            file = dialog.open_finish(result)
            if file:
                file_path = file.get_path()
                # Import settings
                self.app_settings.import_settings(file_path)
                # Reload all settings in UI
                self._load_settings()
                self.show_notification(f"Settings imported from {file_path}", "success")
                self.logger.info(f"Settings imported from: {file_path}")
        except Exception as e:
            if "dismissed" not in str(e).lower():  # Don't show error if user cancelled
                self.logger.error(f"Error importing settings: {e}", exc_info=True)
                self.show_notification(f"Error importing settings: {e}", "error")

    def on_reset_clicked(self, button: Gtk.Button) -> None:
        """Handle reset to defaults button click."""
        try:
            # Show confirmation dialog
            dialog = Gtk.AlertDialog()
            dialog.set_message("Reset to Defaults?")
            dialog.set_detail("This will reset ALL settings to their default values. This action cannot be undone.")
            dialog.set_buttons(["Cancel", "Reset to Defaults"])
            dialog.set_cancel_button(0)
            dialog.set_default_button(0)

            # Get parent window
            parent = button.get_root()

            # Show dialog
            dialog.choose(parent, None, self._on_reset_confirmed)

        except Exception as e:
            self.logger.error(f"Error showing reset dialog: {e}", exc_info=True)
            self.show_notification(f"Error resetting settings: {e}", "error")

    def _on_reset_confirmed(self, dialog: Any, result: Any) -> None:
        """Handle reset confirmation."""
        try:
            button_index = dialog.choose_finish(result)
            if button_index == 1:  # "Reset to Defaults" button
                # Reset all settings to defaults
                self.app_settings.reset_to_defaults()
                # Reload all settings in UI
                self._load_settings()
                self.show_notification("All settings reset to defaults", "success")
                self.logger.info("Settings reset to defaults")
        except Exception as e:
            if "dismissed" not in str(e).lower():  # Don't show error if user cancelled
                self.logger.error(f"Error resetting settings: {e}", exc_info=True)
                self.show_notification(f"Error resetting settings: {e}", "error")

    def on_theme_style_changed(self, dropdown: Gtk.DropDown, param: Any) -> None:
        """Handle theme style setting change."""
        if self._loading_settings:
            return
        try:
            theme_style_values = ["system", "classic", "modern"]
            selected_index = dropdown.get_selected()

            if 0 <= selected_index < len(theme_style_values):
                new_theme_style = theme_style_values[selected_index]
                # NOTE: Setting will be saved in batch via _collect_settings()
                # when dialog closes or Apply is clicked
                self.logger.trace(f"Theme style changed to: {new_theme_style}")

                # Show notification
                theme_style_names = {
                    "system": "System Theme",
                    "classic": "Deluge Theme",
                    "modern": "Modern Chunky",
                }
                message = f"Theme style will change to: {theme_style_names.get(new_theme_style, new_theme_style)}"
                self.show_notification(message, "info")
        except Exception as e:
            self.logger.error(f"Error changing theme style setting: {e}")

    def on_color_scheme_changed(self, dropdown: Gtk.DropDown, param: Any) -> None:
        """Handle color scheme setting change."""
        if self._loading_settings:
            return
        try:
            color_scheme_values = ["auto", "light", "dark"]
            selected_index = dropdown.get_selected()

            if 0 <= selected_index < len(color_scheme_values):
                new_color_scheme = color_scheme_values[selected_index]
                # NOTE: Setting will be saved in batch via _collect_settings()
                # when dialog closes or Apply is clicked
                self.logger.trace(f"Color scheme changed to: {new_color_scheme}")

                # Show notification
                color_scheme_names = {
                    "auto": "Auto (Follow System)",
                    "light": "Light",
                    "dark": "Dark",
                }
                message = f"Color scheme will change to: {color_scheme_names.get(new_color_scheme, new_color_scheme)}"
                self.show_notification(message, "info")
        except Exception as e:
            self.logger.error(f"Error changing color scheme setting: {e}")

    def on_seeding_profile_changed(self, dropdown: Gtk.DropDown, param: Any) -> None:
        """Handle seeding profile setting change."""
        if self._loading_settings:
            return
        try:
            selected_index = dropdown.get_selected()
            profile_name = self.profile_manager.get_profile_from_dropdown_index(selected_index)

            self.logger.trace(f"Seeding profile changed to: {profile_name}")

            # Apply profile immediately
            if self.profile_manager.apply_profile(profile_name):
                # Show notification with profile summary
                profile_summary = self.profile_manager.get_profile_summary(profile_name)
                profile_names = {
                    "conservative": "Conservative",
                    "balanced": "Balanced",
                    "aggressive": "Aggressive",
                    "custom": "Custom",
                }
                display_name = profile_names.get(profile_name, profile_name.title())
                message = f"Applied {display_name} profile: {profile_summary}"
                self.show_notification(message, "success")
            else:
                self.show_notification("Failed to apply seeding profile", "error")

        except Exception as e:
            self.logger.error(f"Error changing seeding profile setting: {e}")
            self.show_notification("Error applying seeding profile", "error")

    def _reset_tab_defaults(self) -> None:
        """Reset General tab to default values."""
        try:
            # Reset to default values
            auto_start = self.get_widget("auto_start")
            if auto_start:
                self.set_switch_state(auto_start, False)
            start_minimized = self.get_widget("start_minimized")
            if start_minimized:
                self.set_switch_state(start_minimized, False)
            # Reset theme to system default
            theme_dropdown = self.get_widget("settings_theme")
            if theme_dropdown:
                theme_dropdown.set_selected(0)  # "system" is index 0
            # Reset seeding profile to balanced default
            profile_dropdown = self.get_widget("settings_seeding_profile")
            if profile_dropdown:
                profile_dropdown.set_selected(1)  # "balanced" is index 1
            self.show_notification("General settings reset to defaults", "success")
        except Exception as e:
            self.logger.error(f"Error resetting General tab to defaults: {e}")

    def _create_notification_overlay(self) -> Gtk.Overlay:
        """Create notification overlay for this tab."""
        # Create a minimal overlay for the notification system
        overlay = Gtk.Overlay()
        self._notification_overlay = overlay
        return overlay

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace(
            "GeneralTab update_view called",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for language functionality
        self.model = model
        self.logger.trace(f"Model stored in GeneralTab: {model is not None}")
        # Set initialization flag to prevent triggering language changes during setup
        self._initializing = True
        # DO NOT connect to language-changed signal - this would create a loop!
        # The settings dialog handles its own translation when the user changes language
        logger.trace(
            "NOT connecting to model language-changed signal to avoid loops",
            "GeneralTab",
        )
        logger.trace("Settings dialog will handle its own translation directly", "GeneralTab")
        # Note: Language dropdown population postponed to avoid initialization loops
        # self._populate_language_dropdown() will be called when needed
        # Translate dropdown items now that we have the model using original English items
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_dropdown_items("settings_theme", self.THEME_ITEMS)  # type: ignore[attr-defined]
        self.translate_dropdown_items("settings_seeding_profile", self.PROFILE_ITEMS)

    def _setup_language_dropdown(self) -> None:
        """Setup the language dropdown with supported languages."""
        logger.trace("===== _setup_language_dropdown() CALLED =====", "GeneralTab")
        language_dropdown = self.get_widget("language_dropdown")
        logger.trace("Language dropdown widget:", "GeneralTab")
        logger.trace("Language dropdown type:", "GeneralTab")
        self.logger.trace(f"Language dropdown widget found: {language_dropdown is not None}")
        if not language_dropdown:
            logger.error("ERROR: Language dropdown widget not found!", "GeneralTab")
            return
        # Create string list for dropdown
        logger.trace("Creating Gtk.StringList for language dropdown...", "GeneralTab")
        self.language_list = Gtk.StringList()
        self.language_codes = []  # type: ignore[var-annotated]
        # We'll populate this when we have access to the model
        # For now, just set up the basic structure
        logger.trace("Setting model on language dropdown...", "GeneralTab")
        language_dropdown.set_model(self.language_list)
        # Connect the language change signal
        logger.trace("About to connect language change signal...", "GeneralTab")
        try:
            self.track_signal(
                language_dropdown,
                language_dropdown.connect("notify::selected", self.on_language_changed),
            )
            logger.info("Language signal connected successfully with ID:", "GeneralTab")
        except Exception as e:
            logger.error(f"FAILED to connect language signal: {e}", "GeneralTab", exc_info=True)
        logger.trace("Language dropdown setup completed", "GeneralTab")
        self.logger.trace("Language dropdown setup completed with empty StringList")

    def _populate_language_dropdown(self) -> Any:
        """Populate language dropdown with supported languages when model is available."""
        logger.trace("===== _populate_language_dropdown() CALLED =====", "GeneralTab")
        self.logger.trace("_populate_language_dropdown called")

        if not hasattr(self, "model") or not self.model:
            self.logger.trace("Model not available, skipping language dropdown population")
            return

        language_dropdown = self.get_widget("language_dropdown")
        if not language_dropdown:
            self.logger.error("Language dropdown widget not found")
            return

        try:
            # Get supported languages from centralized config
            supported_languages = get_supported_language_codes()

            if not supported_languages:
                self.logger.error("No supported languages found in configuration")
                self.logger.warning("Language dropdown will be disabled")
                language_dropdown.set_sensitive(False)
                return

            # Get current language from settings
            current_language = self.app_settings.get_language()
            self.logger.trace(f"Found {len(supported_languages)} languages: {supported_languages}")
            self.logger.trace(f"Current language: {current_language}")

            # Clear existing items
            self.language_list.splice(0, self.language_list.get_n_items(), [])
            self.language_codes.clear()

            # Get language display names (native names for better UX)
            # This ensures users can always identify their own language regardless of current UI language
            try:
                language_names = get_language_display_names(use_native_names=True)
                self.logger.trace(f"Loaded {len(language_names)} language names from config")
            except Exception as e:
                self.logger.error(f"Failed to load language display names: {e}", exc_info=True)
                # Fallback: use uppercase language codes
                language_names = {code: code.upper() for code in supported_languages}

            # Add supported languages to dropdown
            selected_index = 0
            for i, lang_code in enumerate(supported_languages):
                display_name = language_names.get(lang_code, lang_code.upper())
                self.language_list.append(display_name)
                self.language_codes.append(lang_code)
                self.logger.trace(f"Added language {i}: {lang_code} -> {display_name}")
                if lang_code == current_language:
                    selected_index = i
            # Temporarily disconnect the signal to avoid triggering the callback
            # when setting the selection programmatically
            signal_was_connected = False
            try:
                if hasattr(self, "_language_signal_id") and self._language_signal_id:
                    logger.trace("Disconnecting language signal ID:", "GeneralTab")
                    language_dropdown.handler_block(self._language_signal_id)
                    signal_was_connected = True
                    logger.info("Language signal blocked successfully", "GeneralTab")
            except Exception:
                logger.error("Failed to block language signal:", "GeneralTab")
            # Set current selection
            logger.debug("Setting dropdown selection to index:", "GeneralTab")
            language_dropdown.set_selected(selected_index)
            # Reconnect the signal handler
            try:
                if signal_was_connected:
                    logger.trace("Unblocking language signal ID:", "GeneralTab")
                    language_dropdown.handler_unblock(self._language_signal_id)
                    logger.info("Language signal unblocked successfully", "GeneralTab")
            except Exception:
                logger.error("Failed to unblock language signal:", "GeneralTab")
                # If unblocking fails, try to reconnect
                try:
                    self.track_signal(
                        language_dropdown,
                        language_dropdown.connect("notify::selected", self.on_language_changed),
                    )
                    logger.trace("Reconnected language signal with new ID:", "GeneralTab")
                except Exception:
                    logger.error("Failed to reconnect language signal:", "GeneralTab")
            # Clear initialization flag here after setting up the dropdown
            # This ensures the signal handler can work for user interactions
            logger.trace("About to clear _initializing flag...", "GeneralTab")
            logger.trace("_initializing before:", "GeneralTab")
            if hasattr(self, "_initializing"):
                self._initializing = False
                logger.trace("_initializing after:", "GeneralTab")
                logger.trace(
                    "Language dropdown initialization completed - enabling user interactions",
                    "GeneralTab",
                )
                self.logger.info("Language dropdown initialization completed - enabling user interactions")
            else:
                logger.error("Warning: _initializing attribute not found", "GeneralTab")
            lang_count = len(self.language_codes)
            self.logger.trace(
                f"Language dropdown populated with {lang_count} languages, selected index: {selected_index}"
            )
        except Exception as e:
            self.logger.error(f"Error populating language dropdown: {e}")

    def on_language_changed(self, dropdown: Any, _param: Any) -> None:
        """Handle language dropdown selection change."""
        # Skip language changes during settings load
        if self._loading_settings:
            return
        logger.trace("===== on_language_changed() CALLED =====", "GeneralTab")
        logger.trace("Dropdown:", "GeneralTab")
        logger.trace("Param:", "GeneralTab")
        logger.trace("Selected index:", "GeneralTab")
        # Note: No need for recursive call prevention since we removed the problematic signal connection
        if not hasattr(self, "model") or not self.model:
            logger.trace("No model available, returning early", "GeneralTab")
            logger.trace("hasattr(self, 'model'):", "GeneralTab")
            logger.trace("self.model:", "GeneralTab")
            return
        # Skip language changes during initialization to prevent loops
        if hasattr(self, "_initializing") and self._initializing:
            logger.trace("Skipping language change during initialization", "GeneralTab")
            logger.trace("_initializing flag:", "GeneralTab")
            logger.trace(
                "Need to clear _initializing flag for user interactions to work",
                "GeneralTab",
            )
            # EMERGENCY FIX: If the language dropdown has content, we can clear the initialization flag
            # This handles cases where _populate_language_dropdown() didn't complete properly
            if hasattr(self, "language_codes") and len(self.language_codes) > 0:
                logger.trace(
                    "EMERGENCY FIX: Language codes available (), clearing _initializing flag",
                    "GeneralTab",
                )
                self._initializing = False
                logger.trace(
                    "_initializing flag cleared, continuing with language change...",
                    "GeneralTab",
                )
                # Don't return - continue with the language change
            else:
                logger.trace(
                    "Language codes not available, keeping initialization flag",
                    "GeneralTab",
                )
                self.logger.trace("Skipping language change during initialization")
                return
        # Prevent concurrent language changes - use class-level lock
        if hasattr(self.__class__, "_changing_language") and self.__class__._changing_language:
            self.logger.trace("Skipping language change - already in progress globally")
            return
        # Check if the selected language is already the current language
        selected_index = dropdown.get_selected()
        current_lang = getattr(self.app_settings, "language", "en")
        if 0 <= selected_index < len(self.language_codes):
            selected_lang = self.language_codes[selected_index]
            # If we're trying to switch to the same language, skip
            if selected_lang == current_lang:
                self.logger.trace(f"Skipping language change - already using {selected_lang}")
                return
        logger.trace(
            f"Language change initiated: {current_lang} -> "
            f"{self.language_codes[selected_index] if 0 <= selected_index < len(self.language_codes) else 'unknown'}",
            "UnknownClass",
        )
        # Set class-level guard to prevent concurrent changes
        self.__class__._changing_language = True
        try:
            if 0 <= selected_index < len(self.language_codes):
                selected_lang = self.language_codes[selected_index]
                logger.trace(
                    "User language change request: {current_lang} -> {selected_lang}",
                    "UnknownClass",
                )
                self.logger.trace(f"User language change request: {current_lang} -> {selected_lang}")
                # Temporarily disconnect the signal to prevent feedback loops
                signal_was_blocked = False
                if hasattr(self, "_language_signal_id") and self._language_signal_id:
                    dropdown.handler_block(self._language_signal_id)
                    signal_was_blocked = True
                logger.trace(
                    "Signal block took {(disconnect_end - disconnect_start)*1000:.1f}ms",
                    "UnknownClass",
                )
                # Update AppSettings which will trigger Model to handle the rest of the app
                logger.trace("Saving language to AppSettings:", "GeneralTab")
                logger.trace(
                    "DEBUG: About to call app_settings.set('language', '')",
                    "GeneralTab",
                )
                logger.debug("DEBUG: AppSettings instance:", "GeneralTab")
                logger.debug("DEBUG: Current language before set:", "GeneralTab")
                self.app_settings.set("language", selected_lang)
                logger.trace("DEBUG: app_settings.set() completed", "GeneralTab")
                logger.debug("DEBUG: Current language after set:", "GeneralTab")
                logger.trace(
                    "AppSettings.set() took {(settings_end - settings_start)*1000:.1f}ms",
                    "UnknownClass",
                )
                # Handle settings dialog translation directly (not via model signal to avoid loops)
                logger.trace("Handling settings dialog translation directly...", "GeneralTab")
                self._handle_settings_translation(selected_lang)
                logger.trace("Settings dialog translation completed", "GeneralTab")
                # Unblock the signal
                if signal_was_blocked and hasattr(self, "_language_signal_id") and self._language_signal_id:
                    dropdown.handler_unblock(self._language_signal_id)
                    logger.info("Signal unblocked successfully", "GeneralTab")
                logger.trace(
                    "Signal unblock took {(reconnect_end - reconnect_start)*1000:.1f}ms",
                    "UnknownClass",
                )
                # Show success notification
                self.show_notification(f"Language switched to {selected_lang}", "success")
                logger.trace(
                    "Notification took {(notification_end - notification_start)*1000:.1f}ms",
                    "UnknownClass",
                )
                logger.trace("Language change completed - TOTAL UI TIME: ms", "GeneralTab")
        except Exception as e:
            self.logger.error(f"Error changing language: {e}")
            self.show_notification("Error changing language", "error")
            # Make sure to reconnect signal even on error
            if hasattr(self, "_language_signal_id"):
                try:
                    self.track_signal(
                        dropdown,
                        dropdown.connect("notify::selected", self.on_language_changed),
                    )
                except Exception:
                    pass
        finally:
            # Reset the guard flag
            self.__class__._changing_language = False

    def _handle_settings_translation(self, new_language: Any) -> None:
        """Handle translation for the settings dialog directly (not via model signal)."""
        try:
            self.logger.trace(f"_handle_settings_translation() called with language: {new_language}")

            # First, handle GeneralTab's own dropdowns using original English items
            self.translate_dropdown_items("settings_theme", self.THEME_ITEMS)  # type: ignore[attr-defined]
            self.translate_dropdown_items("settings_seeding_profile", self.PROFILE_ITEMS)

            # Then handle other tabs
            if hasattr(self, "settings_dialog") and hasattr(self.settings_dialog, "tabs"):
                # Use a direct approach: call translate_all_dropdowns() on each tab that has it
                for i, tab in enumerate(self.settings_dialog.tabs):
                    if hasattr(tab, "tab_name") and tab.tab_name != "General":
                        # Try direct dropdown translation instead of update_view
                        if hasattr(tab, "translate_all_dropdowns"):
                            try:
                                tab.translate_all_dropdowns()
                                self.logger.trace(f"Updated {tab.tab_name} dropdowns via translate_all_dropdowns()")
                            except Exception as e:
                                self.logger.error(f"Error updating {tab.tab_name} via translate_all_dropdowns: {e}")
                        elif hasattr(tab, "update_view"):
                            try:
                                # Use the same call pattern as SettingsDialog.__init__
                                tab.update_view(self.model, None, None)
                                self.logger.trace(f"Updated {tab.tab_name} dropdowns via update_view()")
                            except Exception as e:
                                self.logger.error(f"Error updating {tab.tab_name} via update_view: {e}")

        except Exception as e:
            self.logger.error(f"Error handling settings dialog translation: {e}", exc_info=True)

    # This was causing infinite loops. Settings dialog handles its own translation directly.

    def on_watch_folder_browse_clicked(self, button: Gtk.Button) -> None:
        """Handle browse button click to select watch folder."""
        try:
            # Create file chooser dialog for folder selection
            dialog = Gtk.FileDialog()
            dialog.set_title("Select Watch Folder")

            # Set initial folder if path exists
            path_entry = self.get_widget("watch_folder_path")
            if path_entry and path_entry.get_text():
                import os

                from gi.repository import Gio  # noqa: E402

                initial_path = path_entry.get_text()
                if os.path.exists(initial_path):
                    initial_file = Gio.File.new_for_path(initial_path)
                    dialog.set_initial_folder(initial_file)

            # Show dialog and handle response
            def on_folder_selected(dialog: Any, result: Any) -> None:
                try:
                    folder = dialog.select_folder_finish(result)
                    if folder:
                        folder_path = folder.get_path()
                        if path_entry:
                            path_entry.set_text(folder_path)
                            # NOTE: Setting will be saved in batch via _collect_settings()
                            self.logger.trace(f"Watch folder path selected: {folder_path}")
                            self.show_notification(f"Watch folder set to: {folder_path}", "success")
                except Exception as e:
                    self.logger.error(f"Error selecting folder: {e}")

            # Get parent window for dialog
            parent_window = self.get_widget("settings_theme")  # Get any widget
            if parent_window:
                parent_window = parent_window.get_root()  # Get window from widget

            dialog.select_folder(parent_window, None, on_folder_selected)

        except Exception as e:
            self.logger.error(f"Error showing folder chooser dialog: {e}")
            self.show_notification("Error opening folder browser", "error")
