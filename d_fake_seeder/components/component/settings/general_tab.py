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
from .settings_mixins import ValidationMixin  # noqa: E402

# fmt: on


class GeneralTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin):
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

    def __init__(self, builder: Gtk.Builder, app_settings, app=None):
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
            "language_dropdown": self.builder.get_object("settings_language"),
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
        # Auto-start toggle
        auto_start = self.get_widget("auto_start")
        if auto_start:
            self.track_signal(auto_start, auto_start.connect("state-set", self.on_auto_start_changed))
        # Start minimized toggle
        start_minimized = self.get_widget("start_minimized")
        if start_minimized:
            self.track_signal(
                start_minimized,
                start_minimized.connect("state-set", self.on_start_minimized_changed),
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
        # Watch folder widgets
        watch_folder_enabled = self.get_widget("watch_folder_enabled")
        if watch_folder_enabled:
            self.track_signal(
                watch_folder_enabled,
                watch_folder_enabled.connect("state-set", self.on_watch_folder_enabled_changed),
            )
        watch_folder_path = self.get_widget("watch_folder_path")
        if watch_folder_path:
            self.track_signal(
                watch_folder_path,
                watch_folder_path.connect("changed", self.on_watch_folder_path_changed),
            )
        watch_folder_browse = self.get_widget("watch_folder_browse")
        if watch_folder_browse:
            self.track_signal(
                watch_folder_browse,
                watch_folder_browse.connect("clicked", self.on_watch_folder_browse_clicked),
            )
        watch_folder_scan_interval = self.get_widget("watch_folder_scan_interval")
        if watch_folder_scan_interval:
            self.track_signal(
                watch_folder_scan_interval,
                watch_folder_scan_interval.connect("value-changed", self.on_watch_folder_scan_interval_changed),
            )
        watch_folder_auto_start = self.get_widget("watch_folder_auto_start")
        if watch_folder_auto_start:
            self.track_signal(
                watch_folder_auto_start,
                watch_folder_auto_start.connect("state-set", self.on_watch_folder_auto_start_changed),
            )
        watch_folder_delete_added = self.get_widget("watch_folder_delete_added")
        if watch_folder_delete_added:
            self.track_signal(
                watch_folder_delete_added,
                watch_folder_delete_added.connect("state-set", self.on_watch_folder_delete_added_changed),
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
                self.set_switch_state(watch_folder_delete_added, watch_folder_config.get("delete_added_torrents", False))

            self.logger.info("General tab settings loaded successfully", "GeneralTab")
        except Exception as e:
            self.logger.error(f"Error loading General tab settings: {e}", exc_info=True)

    def _setup_dependencies(self) -> None:
        """Set up dependencies for General tab."""
        # General tab typically doesn't have complex dependencies
        pass

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from General tab widgets."""
        settings = {}
        try:
            # Auto-start setting
            auto_start = self.get_widget("auto_start")
            if auto_start:
                settings["auto_start"] = auto_start.get_active()
            # Start minimized setting
            start_minimized = self.get_widget("start_minimized")
            if start_minimized:
                settings["start_minimized"] = start_minimized.get_active()
            # Theme style setting (system/classic/modern)
            theme_style_dropdown = self.get_widget("settings_theme")
            if theme_style_dropdown:
                theme_style_values = ["system", "classic", "modern"]
                selected_index = theme_style_dropdown.get_selected()
                if 0 <= selected_index < len(theme_style_values):
                    settings["theme_style"] = theme_style_values[selected_index]

            # Color scheme setting (auto/light/dark)
            color_scheme_dropdown = self.get_widget("settings_color_scheme")
            if color_scheme_dropdown:
                color_scheme_values = ["auto", "light", "dark"]
                selected_index = color_scheme_dropdown.get_selected()
                if 0 <= selected_index < len(color_scheme_values):
                    settings["color_scheme"] = color_scheme_values[selected_index]
            # Seeding profile setting
            profile_dropdown = self.get_widget("settings_seeding_profile")
            if profile_dropdown:
                selected_index = profile_dropdown.get_selected()
                profile_name = self.profile_manager.get_profile_from_dropdown_index(selected_index)
                settings["seeding_profile"] = profile_name

            # Watch folder settings
            watch_folder_settings = {}
            watch_folder_enabled = self.get_widget("watch_folder_enabled")
            if watch_folder_enabled:
                watch_folder_settings["enabled"] = watch_folder_enabled.get_active()
            watch_folder_path = self.get_widget("watch_folder_path")
            if watch_folder_path:
                watch_folder_settings["path"] = watch_folder_path.get_text()
            watch_folder_scan_interval = self.get_widget("watch_folder_scan_interval")
            if watch_folder_scan_interval:
                watch_folder_settings["scan_interval_seconds"] = int(watch_folder_scan_interval.get_value())
            watch_folder_auto_start = self.get_widget("watch_folder_auto_start")
            if watch_folder_auto_start:
                watch_folder_settings["auto_start_torrents"] = watch_folder_auto_start.get_active()
            watch_folder_delete_added = self.get_widget("watch_folder_delete_added")
            if watch_folder_delete_added:
                watch_folder_settings["delete_added_torrents"] = watch_folder_delete_added.get_active()
            if watch_folder_settings:
                settings["watch_folder"] = watch_folder_settings
        except Exception as e:
            self.logger.error(f"Error collecting General tab settings: {e}")
        return settings

    def on_auto_start_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle auto-start setting change."""
        try:
            self.app_settings.set("auto_start", state)
            self.logger.trace(f"Auto-start changed to: {state}")
            # Show notification
            message = "Auto-start enabled" if state else "Auto-start disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing auto-start setting: {e}")

    def on_start_minimized_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle start minimized setting change."""
        try:
            self.app_settings.set("start_minimized", state)
            self.logger.trace(f"Start minimized changed to: {state}")
            # Show notification
            message = "Start minimized enabled" if state else "Start minimized disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing start minimized setting: {e}")

    def on_theme_style_changed(self, dropdown: Gtk.DropDown, param) -> None:
        """Handle theme style setting change."""
        try:
            theme_style_values = ["system", "classic", "modern"]
            selected_index = dropdown.get_selected()

            if 0 <= selected_index < len(theme_style_values):
                new_theme_style = theme_style_values[selected_index]
                # Save to ui_settings.theme_style
                self.app_settings.set("ui_settings.theme_style", new_theme_style)
                self.logger.trace(f"Theme style changed to: {new_theme_style}")

                # Apply theme immediately by emitting a signal
                # The view should listen to app_settings changes and apply themes accordingly

                # Show notification
                theme_style_names = {
                    "system": "System Theme",
                    "classic": "Deluge Theme",
                    "modern": "Modern Chunky",
                }
                message = f"Theme style changed to: {theme_style_names.get(new_theme_style, new_theme_style)}"
                self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing theme style setting: {e}")

    def on_color_scheme_changed(self, dropdown: Gtk.DropDown, param) -> None:
        """Handle color scheme setting change."""
        try:
            color_scheme_values = ["auto", "light", "dark"]
            selected_index = dropdown.get_selected()

            if 0 <= selected_index < len(color_scheme_values):
                new_color_scheme = color_scheme_values[selected_index]
                # Save to ui_settings.color_scheme
                self.app_settings.set("ui_settings.color_scheme", new_color_scheme)
                self.logger.trace(f"Color scheme changed to: {new_color_scheme}")

                # Apply color scheme immediately by emitting a signal
                # The view should listen to app_settings changes and apply themes accordingly

                # Show notification
                color_scheme_names = {
                    "auto": "Auto (Follow System)",
                    "light": "Light",
                    "dark": "Dark",
                }
                message = f"Color scheme changed to: {color_scheme_names.get(new_color_scheme, new_color_scheme)}"
                self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing color scheme setting: {e}")

    def on_seeding_profile_changed(self, dropdown: Gtk.DropDown, param) -> None:
        """Handle seeding profile setting change."""
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

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.trace(
            "GeneralTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.trace(
            "GeneralTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.trace(
            "GeneralTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
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
        self.translate_dropdown_items("settings_theme", self.THEME_ITEMS)
        self.translate_dropdown_items("settings_seeding_profile", self.PROFILE_ITEMS)

    def _setup_language_dropdown(self):
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
        self.language_codes = []
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

    def _populate_language_dropdown(self):
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

    def on_language_changed(self, dropdown, _param):
        """Handle language dropdown selection change."""
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
        if 0 <= selected_index < len(self.language_codes):
            selected_lang = self.language_codes[selected_index]
            current_lang = getattr(self.app_settings, "language", "en")
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

    def _handle_settings_translation(self, new_language):
        """Handle translation for the settings dialog directly (not via model signal)."""
        try:
            self.logger.trace(f"_handle_settings_translation() called with language: {new_language}")

            # First, handle GeneralTab's own dropdowns using original English items
            self.translate_dropdown_items("settings_theme", self.THEME_ITEMS)
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

    # REMOVED: on_model_language_changed() - settings dialog should not listen to model language changes
    # This was causing infinite loops. Settings dialog handles its own translation directly.

    # Watch folder signal handlers
    def on_watch_folder_enabled_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle watch folder enabled setting change."""
        try:
            self.app_settings.set("watch_folder.enabled", state)
            self.logger.trace(f"Watch folder enabled changed to: {state}")

            # Get current path to provide helpful feedback
            watch_folder_config = getattr(self.app_settings, "watch_folder", {})
            watch_path = watch_folder_config.get("path", "")

            if state:
                if watch_path:
                    message = f"Watch folder enabled: monitoring {watch_path}"
                else:
                    message = "Watch folder enabled (set a path to start monitoring)"
                    self.show_notification(message, "warning")
                    return
            else:
                message = "Watch folder disabled"

            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing watch folder enabled setting: {e}")
            self.show_notification("Error enabling watch folder", "error")

    def on_watch_folder_path_changed(self, entry: Gtk.Entry) -> None:
        """Handle watch folder path setting change."""
        try:
            path = entry.get_text()
            self.app_settings.set("watch_folder.path", path)
            self.logger.trace(f"Watch folder path changed to: {path}")
        except Exception as e:
            self.logger.error(f"Error changing watch folder path setting: {e}")

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
            def on_folder_selected(dialog, result):
                try:
                    folder = dialog.select_folder_finish(result)
                    if folder:
                        folder_path = folder.get_path()
                        if path_entry:
                            path_entry.set_text(folder_path)
                            self.app_settings.set("watch_folder.path", folder_path)
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

    def on_watch_folder_scan_interval_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle watch folder scan interval setting change."""
        try:
            interval = int(spin_button.get_value())
            self.app_settings.set("watch_folder.scan_interval_seconds", interval)
            self.logger.trace(f"Watch folder scan interval changed to: {interval}")
        except Exception as e:
            self.logger.error(f"Error changing watch folder scan interval setting: {e}")

    def on_watch_folder_auto_start_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle watch folder auto-start setting change."""
        try:
            self.app_settings.set("watch_folder.auto_start_torrents", state)
            self.logger.trace(f"Watch folder auto-start changed to: {state}")
            message = "Auto-start torrents enabled" if state else "Auto-start torrents disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing watch folder auto-start setting: {e}")

    def on_watch_folder_delete_added_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle watch folder delete added torrents setting change."""
        try:
            self.app_settings.set("watch_folder.delete_added_torrents", state)
            self.logger.trace(f"Watch folder delete added changed to: {state}")
            message = "Delete added torrents enabled" if state else "Delete added torrents disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing watch folder delete added setting: {e}")
