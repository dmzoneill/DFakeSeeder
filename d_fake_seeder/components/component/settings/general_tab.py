"""
General settings tab for the settings dialog.

Handles general application settings like auto-start, minimized start,
language selection, and other basic preferences.
"""

import os
from typing import Any, Dict

import time

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402
from view import View  # noqa

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import TranslationMixin  # noqa: E402
from .settings_mixins import ValidationMixin  # noqa: E402


class GeneralTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin):
    """
    General settings tab component.

    Manages:
    - Application startup behavior (auto-start, start minimized)
    - Theme preferences
    - Basic UI preferences
    """

    def __init__(self, builder: Gtk.Builder, app_settings, app=None):
        """Initialize the General tab."""
        self.app = app

        super().__init__(builder, app_settings)

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "General"

    def _init_widgets(self) -> None:
        """Initialize General tab widgets."""
        print(f"[GeneralTab] ===== _init_widgets() CALLED =====")
        print(f"[GeneralTab] Builder: {self.builder}")

        # Let's try to debug what objects are available in the builder
        if self.builder:
            print(f"[GeneralTab] Checking for language-related objects in builder...")
            # Try various possible names for the language dropdown
            possible_names = [
                "settings_language",
                "language_dropdown",
                "language_combo",
                "language_combobox",
                "language_selection",
                "combo_language",
                "general_language",
                "preferences_language"
            ]

            for name in possible_names:
                obj = self.builder.get_object(name)
                print(f"[GeneralTab] - {name}: {obj} (type: {type(obj) if obj else 'None'})")

        # Cache commonly used widgets
        widget_objects = {
            "auto_start": self.builder.get_object("settings_auto_start"),
            "start_minimized": self.builder.get_object("settings_start_minimized"),
            "language_dropdown": self.builder.get_object("settings_language"),
        }

        print(f"[GeneralTab] Widget lookup results:")
        for name, widget in widget_objects.items():
            print(f"[GeneralTab] - {name}: {widget} (type: {type(widget) if widget else 'None'})")

        self._widgets.update(widget_objects)

        # Initialize language dropdown if available
        print(f"[GeneralTab] About to call _setup_language_dropdown()...")
        self._setup_language_dropdown()
        print(f"[GeneralTab] _init_widgets() completed")

    def _connect_signals(self) -> None:
        """Connect signal handlers for General tab."""
        # Auto-start toggle
        auto_start = self.get_widget("auto_start")
        if auto_start:
            auto_start.connect("state-set", self.on_auto_start_changed)

        # Start minimized toggle
        start_minimized = self.get_widget("start_minimized")
        if start_minimized:
            start_minimized.connect("state-set", self.on_start_minimized_changed)

        # Language dropdown - signal connection handled in _setup_language_dropdown()
        # to avoid dual connections and ensure proper disconnect/reconnect during population

    def _load_settings(self) -> None:
        """Load current settings into General tab widgets."""
        try:
            # Auto-start setting
            auto_start = self.get_widget("auto_start")
            if auto_start:
                auto_start.set_active(getattr(self.app_settings, "auto_start", False))

            # Start minimized setting
            start_minimized = self.get_widget("start_minimized")
            if start_minimized:
                start_minimized.set_active(getattr(self.app_settings, "start_minimized", False))

            self.logger.debug("General tab settings loaded")

        except Exception as e:
            self.logger.error(f"Error loading General tab settings: {e}")

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

        except Exception as e:
            self.logger.error(f"Error collecting General tab settings: {e}")

        return settings

    def on_auto_start_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle auto-start setting change."""
        try:
            self.app_settings.set("auto_start", state)
            self.logger.debug(f"Auto-start changed to: {state}")

            # Show notification
            message = "Auto-start enabled" if state else "Auto-start disabled"
            self.show_notification(message, "success")

        except Exception as e:
            self.logger.error(f"Error changing auto-start setting: {e}")

    def on_start_minimized_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle start minimized setting change."""
        try:
            self.app_settings.set("start_minimized", state)
            self.logger.debug(f"Start minimized changed to: {state}")

            # Show notification
            message = "Start minimized enabled" if state else "Start minimized disabled"
            self.show_notification(message, "success")

        except Exception as e:
            self.logger.error(f"Error changing start minimized setting: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset General tab to default values."""
        try:
            # Reset to default values
            auto_start = self.get_widget("auto_start")
            if auto_start:
                auto_start.set_active(False)

            start_minimized = self.get_widget("start_minimized")
            if start_minimized:
                start_minimized.set_active(False)

            self.show_notification("General settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting General tab to defaults: {e}")

    def _create_notification_overlay(self) -> Gtk.Overlay:
        """Create notification overlay for this tab."""
        # Create a minimal overlay for the notification system
        overlay = Gtk.Overlay()
        self._notification_overlay = overlay
        return overlay

    def handle_model_changed(self, source, data_obj, data_changed):
        """Handle model change events."""
        self.logger.debug(
            "GeneralTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "GeneralTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "GeneralTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.debug(
            "GeneralTab update_view called",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for language functionality
        self.model = model
        self.logger.debug(f"Model stored in GeneralTab: {model is not None}")

        # Set initialization flag to prevent triggering language changes during setup
        self._initializing = True

        # DO NOT connect to language-changed signal - this would create a loop!
        # The settings dialog handles its own translation when the user changes language
        print(f"[GeneralTab] NOT connecting to model language-changed signal to avoid loops")
        print(f"[GeneralTab] Settings dialog will handle its own translation directly")

        # Note: Language dropdown population postponed to avoid initialization loops
        # self._populate_language_dropdown() will be called when needed

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()

    def _setup_language_dropdown(self):
        """Setup the language dropdown with supported languages."""
        print(f"[GeneralTab] ===== _setup_language_dropdown() CALLED =====")
        language_dropdown = self.get_widget("language_dropdown")
        print(f"[GeneralTab] Language dropdown widget: {language_dropdown}")
        print(f"[GeneralTab] Language dropdown type: {type(language_dropdown) if language_dropdown else 'None'}")
        self.logger.debug(f"Language dropdown widget found: {language_dropdown is not None}")
        if not language_dropdown:
            print(f"[GeneralTab] ERROR: Language dropdown widget not found!")
            return

        # Create string list for dropdown
        print(f"[GeneralTab] Creating Gtk.StringList for language dropdown...")
        self.language_list = Gtk.StringList()
        self.language_codes = []

        # We'll populate this when we have access to the model
        # For now, just set up the basic structure
        print(f"[GeneralTab] Setting model on language dropdown...")
        language_dropdown.set_model(self.language_list)

        # Connect the language change signal
        print(f"[GeneralTab] About to connect language change signal...")
        try:
            self._language_signal_id = language_dropdown.connect("notify::selected", self.on_language_changed)
            print(f"[GeneralTab] Language signal connected successfully with ID: {self._language_signal_id}")
        except Exception as e:
            print(f"[GeneralTab] FAILED to connect language signal: {e}")
            import traceback
            traceback.print_exc()

        print(f"[GeneralTab] Language dropdown setup completed")
        self.logger.debug("Language dropdown setup completed with empty StringList")

    def _populate_language_dropdown(self):
        """Populate language dropdown with supported languages when model is available."""
        print(f"[GeneralTab] ===== _populate_language_dropdown() CALLED =====")
        print(f"[GeneralTab] _initializing flag at start: {getattr(self, '_initializing', 'not set')}")
        self.logger.debug("_populate_language_dropdown called")

        if not hasattr(self, "model") or not self.model:
            self.logger.debug("Model not available, skipping language dropdown population")
            return

        language_dropdown = self.get_widget("language_dropdown")
        if not language_dropdown:
            self.logger.debug("Language dropdown widget not found")
            return

        try:
            # Get supported languages from locale directory
            locale_dir = os.path.join(os.environ.get("DFS_PATH", "."), "components", "locale")

            if not os.path.exists(locale_dir):
                self.logger.error(f"Locale directory not found: {locale_dir}")
                self.logger.warning("Language dropdown will be disabled")
                language_dropdown.set_sensitive(False)
                return

            # Scan locale directory for available languages
            supported_languages = []
            for item in os.listdir(locale_dir):
                lang_dir = os.path.join(locale_dir, item)
                mo_file = os.path.join(lang_dir, "LC_MESSAGES", "dfakeseeder.mo")
                if os.path.isdir(lang_dir) and os.path.exists(mo_file):
                    supported_languages.append(item)

            if not supported_languages:
                self.logger.error(f"No translation files found in locale directory: {locale_dir}")
                self.logger.warning("Language dropdown will show default language only")
                # Fall back to English as default
                supported_languages = ["en"]

            # Sort languages for consistent display
            supported_languages.sort()

            # Get current language from settings
            current_language = self.app_settings.get_language()

            self.logger.debug(f"Found {len(supported_languages)} languages in locale directory: {supported_languages}")
            self.logger.debug(f"Current language: {current_language}")

            # Clear existing items
            self.language_list.splice(0, self.language_list.get_n_items(), [])
            self.language_codes.clear()

            # Get translation function
            translate_func = (
                self.model.get_translate_func()
                if hasattr(self, "model") and hasattr(self.model, "get_translate_func")
                else lambda x: x
            )

            # Language display names - get from settings configuration
            # This ensures users can always identify their own language regardless of current UI language
            language_names = getattr(self.app_settings, "language_display_names", {})

            # Fallback to basic names if config doesn't have them
            if not language_names:
                self.logger.warning("language_display_names not found in settings, using fallback")
                language_names = {
                    "en": "English",
                    "fr": "Français",
                    "de": "Deutsch",
                    "es": "Español",
                    "it": "Italiano",
                    "pl": "Polski",
                    "pt": "Português",
                    "ru": "Русский",
                    "zh": "中文",
                    "ja": "日本語",
                    "ko": "한국어",
                    "ar": "العربية",
                    "hi": "हिन्दी",
                    "nl": "Nederlands",
                    "sv": "Svenska",
                }

            # Add supported languages to dropdown
            selected_index = 0
            for i, lang_code in enumerate(sorted(supported_languages)):
                display_name = language_names.get(lang_code, lang_code.upper())
                self.language_list.append(display_name)
                self.language_codes.append(lang_code)
                self.logger.debug(f"Added language {i}: {lang_code} -> {display_name}")

                if lang_code == current_language:
                    selected_index = i

            # Temporarily disconnect the signal to avoid triggering the callback
            # when setting the selection programmatically
            signal_was_connected = False
            try:
                if hasattr(self, "_language_signal_id") and self._language_signal_id:
                    print(f"[GeneralTab] Disconnecting language signal ID: {self._language_signal_id}")
                    language_dropdown.handler_block(self._language_signal_id)
                    signal_was_connected = True
                    print(f"[GeneralTab] Language signal blocked successfully")
            except Exception as e:
                print(f"[GeneralTab] Failed to block language signal: {e}")

            # Set current selection
            print(f"[GeneralTab] Setting dropdown selection to index: {selected_index}")
            language_dropdown.set_selected(selected_index)

            # Reconnect the signal handler
            try:
                if signal_was_connected:
                    print(f"[GeneralTab] Unblocking language signal ID: {self._language_signal_id}")
                    language_dropdown.handler_unblock(self._language_signal_id)
                    print(f"[GeneralTab] Language signal unblocked successfully")
            except Exception as e:
                print(f"[GeneralTab] Failed to unblock language signal: {e}")
                # If unblocking fails, try to reconnect
                try:
                    self._language_signal_id = language_dropdown.connect("notify::selected", self.on_language_changed)
                    print(f"[GeneralTab] Reconnected language signal with new ID: {self._language_signal_id}")
                except Exception as e2:
                    print(f"[GeneralTab] Failed to reconnect language signal: {e2}")

            # Clear initialization flag here after setting up the dropdown
            # This ensures the signal handler can work for user interactions
            print(f"[GeneralTab] About to clear _initializing flag...")
            print(f"[GeneralTab] _initializing before: {getattr(self, '_initializing', 'not set')}")
            if hasattr(self, "_initializing"):
                self._initializing = False
                print(f"[GeneralTab] _initializing after: {self._initializing}")
                print(f"[GeneralTab] Language dropdown initialization completed - enabling user interactions")
                self.logger.debug("Language dropdown initialization completed - enabling user interactions")
            else:
                print(f"[GeneralTab] Warning: _initializing attribute not found")

            lang_count = len(self.language_codes)
            self.logger.debug(
                f"Language dropdown populated with {lang_count} languages, selected index: {selected_index}"
            )

        except Exception as e:
            self.logger.error(f"Error populating language dropdown: {e}")

    def on_language_changed(self, dropdown, param):
        """Handle language dropdown selection change."""
        print(f"[GeneralTab] ===== on_language_changed() CALLED =====")
        print(f"[GeneralTab] Dropdown: {dropdown}")
        print(f"[GeneralTab] Param: {param}")
        print(f"[GeneralTab] Selected index: {dropdown.get_selected() if dropdown else 'N/A'}")

        # Note: No need for recursive call prevention since we removed the problematic signal connection

        if not hasattr(self, "model") or not self.model:
            print(f"[GeneralTab] No model available, returning early")
            print(f"[GeneralTab] hasattr(self, 'model'): {hasattr(self, 'model')}")
            print(f"[GeneralTab] self.model: {getattr(self, 'model', 'N/A')}")
            return

        # Skip language changes during initialization to prevent loops
        if hasattr(self, "_initializing") and self._initializing:
            print(f"[GeneralTab] Skipping language change during initialization")
            print(f"[GeneralTab] _initializing flag: {self._initializing}")
            print(f"[GeneralTab] Need to clear _initializing flag for user interactions to work")

            # EMERGENCY FIX: If the language dropdown has content, we can clear the initialization flag
            # This handles cases where _populate_language_dropdown() didn't complete properly
            if hasattr(self, 'language_codes') and len(self.language_codes) > 0:
                print(f"[GeneralTab] EMERGENCY FIX: Language codes available ({len(self.language_codes)}), clearing _initializing flag")
                self._initializing = False
                print(f"[GeneralTab] _initializing flag cleared, continuing with language change...")
                # Don't return - continue with the language change
            else:
                print(f"[GeneralTab] Language codes not available, keeping initialization flag")
                self.logger.debug("Skipping language change during initialization")
                return

        # Prevent concurrent language changes - use class-level lock
        if hasattr(self.__class__, "_changing_language") and self.__class__._changing_language:
            self.logger.debug("Skipping language change - already in progress globally")
            return

        # Check if the selected language is already the current language
        selected_index = dropdown.get_selected()
        if 0 <= selected_index < len(self.language_codes):
            selected_lang = self.language_codes[selected_index]
            current_lang = getattr(self.app_settings, "language", "en")

            # If we're trying to switch to the same language, skip
            if selected_lang == current_lang:
                self.logger.debug(f"Skipping language change - already using {selected_lang}")
                return

        start_time = time.time()
        print(
            f"[GeneralTab] [{start_time:.3f}] Language change initiated: {current_lang} -> "
            f"{self.language_codes[selected_index] if 0 <= selected_index < len(self.language_codes) else 'unknown'}"
        )

        # Set class-level guard to prevent concurrent changes
        self.__class__._changing_language = True
        try:
            if 0 <= selected_index < len(self.language_codes):
                selected_lang = self.language_codes[selected_index]

                print(
                    f"[GeneralTab] [{time.time():.3f}] User language change request: {current_lang} -> {selected_lang}"
                )
                self.logger.info(f"User language change request: {current_lang} -> {selected_lang}")

                # Temporarily disconnect the signal to prevent feedback loops
                disconnect_start = time.time()
                signal_was_blocked = False
                if hasattr(self, "_language_signal_id") and self._language_signal_id:
                    dropdown.handler_block(self._language_signal_id)
                    signal_was_blocked = True
                disconnect_end = time.time()
                print(
                    f"[GeneralTab] [{disconnect_end:.3f}] Signal block took "
                    f"{(disconnect_end - disconnect_start)*1000:.1f}ms"
                )

                # Update AppSettings which will trigger Model to handle the rest of the app
                settings_start = time.time()
                print(f"[GeneralTab] [{settings_start:.3f}] Saving language to AppSettings: {selected_lang}")
                print(f"[GeneralTab] DEBUG: About to call app_settings.set('language', '{selected_lang}')")
                print(f"[GeneralTab] DEBUG: AppSettings instance: {self.app_settings}")
                print(f"[GeneralTab] DEBUG: Current language before set: {self.app_settings.get('language', 'unknown')}")
                self.app_settings.set("language", selected_lang)
                print(f"[GeneralTab] DEBUG: app_settings.set() completed")
                print(f"[GeneralTab] DEBUG: Current language after set: {self.app_settings.get('language', 'unknown')}")
                settings_end = time.time()
                print(
                    f"[GeneralTab] [{settings_end:.3f}] AppSettings.set() took "
                    f"{(settings_end - settings_start)*1000:.1f}ms"
                )

                # Handle settings dialog translation directly (not via model signal to avoid loops)
                print(f"[GeneralTab] [{time.time():.3f}] Handling settings dialog translation directly...")
                self._handle_settings_translation(selected_lang)
                print(f"[GeneralTab] [{time.time():.3f}] Settings dialog translation completed")

                # Unblock the signal
                reconnect_start = time.time()
                if signal_was_blocked and hasattr(self, "_language_signal_id") and self._language_signal_id:
                    dropdown.handler_unblock(self._language_signal_id)
                    print(f"[GeneralTab] Signal unblocked successfully")
                reconnect_end = time.time()
                print(
                    f"[GeneralTab] [{reconnect_end:.3f}] Signal unblock took "
                    f"{(reconnect_end - reconnect_start)*1000:.1f}ms"
                )

                # Show success notification
                notification_start = time.time()
                self.show_notification(f"Language switched to {selected_lang}", "success")
                notification_end = time.time()
                print(
                    f"[GeneralTab] [{notification_end:.3f}] Notification took "
                    f"{(notification_end - notification_start)*1000:.1f}ms"
                )

                total_time = (time.time() - start_time) * 1000
                print(f"[GeneralTab] [{time.time():.3f}] Language change completed - TOTAL UI TIME: {total_time:.1f}ms")

        except Exception as e:
            self.logger.error(f"Error changing language: {e}")
            self.show_notification("Error changing language", "error")
            # Make sure to reconnect signal even on error
            if hasattr(self, "_language_signal_id"):
                try:
                    self._language_signal_id = dropdown.connect("notify::selected", self.on_language_changed)
                except Exception:
                    pass
        finally:
            # Reset the guard flag
            self.__class__._changing_language = False

    def _handle_settings_translation(self, new_language):
        """Handle translation for the settings dialog directly (not via model signal)."""
        print(f"[GeneralTab] ===== _handle_settings_translation() CALLED =====")
        print(f"[GeneralTab] New language: {new_language}")

        try:
            # DON'T repopulate the language dropdown - it doesn't need translation and
            # manipulating the signal could break subsequent language changes
            print(f"[GeneralTab] Skipping language dropdown repopulation to preserve signal")

            # Refresh all other dropdowns with new translations
            print(f"[GeneralTab] About to translate common dropdowns...")
            self.translate_common_dropdowns()
            print(f"[GeneralTab] Common dropdowns translated")

            print(f"[GeneralTab] Settings dialog translation completed successfully")
        except Exception as e:
            print(f"[GeneralTab] EXCEPTION in _handle_settings_translation: {e}")
            import traceback
            traceback.print_exc()
            self.logger.error(f"Error handling settings dialog translation: {e}")

    # REMOVED: on_model_language_changed() - settings dialog should not listen to model language changes
    # This was causing infinite loops. Settings dialog handles its own translation directly.
