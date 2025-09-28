#!/usr/bin/env python3

import gettext
import locale
import os
import time
from typing import Any, Dict, List, Optional, Set

import gi

gi.require_version("Gtk", "4.0")  # noqa: E402
from gi.repository import Gtk  # noqa: E402

# Import logger for structured logging
from lib.logger import logger  # noqa: E402


class TranslationManager:
    """
    A reusable class for managing automatic translation and localization of GTK widgets.

    This class provides complete internationalization support including:
    - Automatic widget discovery and translation
    - Locale detection and switching
    - Configuration management
    - Runtime language changes
    """

    def __init__(
        self,
        domain: str = "messages",
        localedir: Optional[str] = None,
        supported_languages: Optional[Set[str]] = None,
        config_file: Optional[str] = None,
        fallback_language: str = "en",
    ):
        """
        Initialize the translation manager.

        Args:
            domain: Gettext domain name (default: "messages")
            localedir: Directory containing translation files (default: "./locale")
            supported_languages: Set of supported language codes (default: auto-discovered from localedir)
            config_file: Path to JSON config file (default: "./config.json")
            fallback_language: Fallback language when others fail (default: "en")
        """
        self.domain = domain
        self.localedir = localedir or os.path.join(os.getcwd(), "locale")
        self.config_file = config_file or os.path.join(os.getcwd(), "config.json")
        self.fallback_language = fallback_language

        # Auto-discover supported languages if not provided
        if supported_languages is None:
            self.supported_languages = self._discover_supported_languages()
        else:
            self.supported_languages = supported_languages

        self.current_language: Optional[str] = None
        self.translate_func = lambda x: x  # Default passthrough
        self.translatable_widgets: List[Dict[str, Any]] = []
        self.state_storage: Dict[str, Any] = {}

        # Simple recursion guard
        self._updating = False
        self._scanned_builders: Set[Any] = set()  # Track builders that have been scanned

        # Set up gettext domain
        gettext.bindtextdomain(self.domain, self.localedir)
        gettext.textdomain(self.domain)

    def _discover_supported_languages(self) -> Set[str]:
        """
        Dynamically discover supported languages from the locale directory.

        Looks for:
        1. Subdirectories in localedir that contain LC_MESSAGES with .mo files
        2. Always includes the fallback language

        Returns:
            Set of discovered language codes
        """
        logger.debug(f"Starting language discovery in {self.localedir}", "TranslationManager")
        start_time = time.time()
        discovered_languages = {self.fallback_language}  # Always include fallback

        try:
            if os.path.exists(self.localedir):
                # Look for language directories
                for item in os.listdir(self.localedir):
                    lang_dir = os.path.join(self.localedir, item)

                    # Check if it's a directory and looks like a language code
                    if os.path.isdir(lang_dir) and self._is_valid_language_code(item):
                        lc_messages_dir = os.path.join(lang_dir, "LC_MESSAGES")

                        # Check if LC_MESSAGES exists and contains .mo files
                        if os.path.exists(lc_messages_dir):
                            mo_files = [f for f in os.listdir(lc_messages_dir) if f.endswith(".mo")]

                            # If we find .mo files, this is a supported language
                            if mo_files:
                                discovered_languages.add(item)

            end_time = time.time()
            discovery_time = (end_time - start_time) * 1000
            logger.debug(f"Discovered languages: {sorted(discovered_languages)} (took {discovery_time:.1f}ms)", "TranslationManager")

        except Exception as e:
            logger.debug("Warning: Could not discover languages from ...: ...", "TranslationManager")

        return discovered_languages

    def _is_valid_language_code(self, code: str) -> bool:
        """
        Check if a string looks like a valid language code.

        Args:
            code: String to check

        Returns:
            True if it looks like a language code (2-3 lowercase letters, optionally with region)
        """
        import re

        # Match patterns like: en, fr, de, pt_BR, zh_CN, etc.
        pattern = r"^[a-z]{2,3}(_[A-Z]{2})?$"
        return bool(re.match(pattern, code))

    def refresh_supported_languages(self) -> Set[str]:
        """
        Re-scan the locale directory and update supported languages.

        Returns:
            Updated set of supported language codes
        """
        self.supported_languages = self._discover_supported_languages()
        return self.supported_languages.copy()

    def setup_translations(self, auto_detect: bool = True) -> str:
        """
        Set up translations with automatic language detection.

        Args:
            auto_detect: Whether to auto-detect system locale (default: True)

        Returns:
            The language code that was actually set up
        """
        with logger.performance.operation_context("setup_translations", "TranslationManager"):
            logger.debug(f"setup_translations called with auto_detect={auto_detect}", "TranslationManager")

            if auto_detect:
                logger.debug("Calling _get_target_language()", "TranslationManager")
                target_language = self._get_target_language()
                logger.debug(f"_get_target_language() returned: {target_language}", "TranslationManager")
            else:
                target_language = self.fallback_language
                logger.debug(f"Using fallback language: {target_language}", "TranslationManager")

            logger.debug(f"About to switch to language: {target_language}", "TranslationManager")
            result = self.switch_language(target_language)
            logger.debug("setup_translations completed", "TranslationManager")

        return result

    def _get_target_language(self) -> str:
        """Determine target language from config and system locale."""
        with logger.performance.operation_context("get_target_language", "TranslationManager"):
            # Get system locale as fallback
            system_language = self._get_system_language()
            logger.debug(f"System language detected: {system_language}", "TranslationManager")

            # Try to get language from AppSettings first to avoid file conflicts
            try:
                from domain.app_settings import AppSettings

                with logger.performance.operation_context("app_settings_instance", "TranslationManager"):
                    app_settings = AppSettings.get_instance()
                    logger.debug("AppSettings.get_instance() completed", "TranslationManager")

                # Use the centralized get_language() method which handles all fallback logic
                with logger.performance.operation_context("get_language", "TranslationManager"):
                    language = app_settings.get_language()
                    logger.debug(f"AppSettings.get_language() returned: {language}", "TranslationManager")

                logger.debug(f"_get_target_language() final target: {language}", "TranslationManager")
                return language
            except Exception as e:
                logger.debug(f"Could not get language from AppSettings: {e}", "TranslationManager")

            # Fallback: if AppSettings completely fails, use system language detection
            logger.debug(f"AppSettings failed, falling back to system language: {system_language}", "TranslationManager")
            return system_language

    def _get_system_language(self) -> str:
        """Detect system language and map to supported languages."""
        try:
            # Get system locale using newer method
            try:
                current_locale = locale.getlocale()[0]
                if current_locale:
                    system_locale = current_locale
                else:
                    # Fallback to deprecated method if getlocale returns None
                    default_locale = locale.getdefaultlocale()[0]
                    system_locale = default_locale if default_locale else "en_US"
            except Exception:
                default_locale = locale.getdefaultlocale()[0]
                system_locale = default_locale if default_locale else "en_US"

            if system_locale:
                # Extract language code (e.g., 'en_US' -> 'en')
                lang_code = system_locale.split("_")[0].lower()

                # Map to supported languages
                if lang_code in self.supported_languages:
                    return lang_code
        except Exception as e:
            logger.debug("Warning: Could not detect system locale: ...", "TranslationManager")

        # Default fallback
        return self.fallback_language

    def switch_language(self, lang_code: str) -> str:
        """
        Switch to a specific language.

        Args:
            lang_code: Language code to switch to

        Returns:
            The language code that was actually set (may differ due to fallbacks)
        """
        with logger.performance.operation_context("switch_language", "TranslationManager"):
            logger.debug(f"switch_language() called with: {lang_code}", "TranslationManager")

            # Check if we're already at this language
            if self.current_language == lang_code:
                logger.debug(f"Already using language '{lang_code}' - skipping switch", "TranslationManager")
                return lang_code

            logger.debug(
                f"Processing language switch: {self.current_language or 'none'} -> {lang_code}",
                "TranslationManager"
            )

            # Validate language is supported
            if lang_code not in self.supported_languages:
                logger.debug(f"Warning: Unsupported language '{lang_code}', falling back to system locale", "TranslationManager")
                lang_code = self._get_system_language()

            # Skip complex locale management - gettext handles this internally

            # Create new translation object for the language
            with logger.performance.operation_context("gettext_translation", "TranslationManager"):
                try:
                    if lang_code == self.fallback_language:
                        # For fallback language, use default messages (no translation needed)
                        trans = gettext.NullTranslations()
                        logger.debug("Using NullTranslations for fallback language", "TranslationManager")
                    else:
                        trans = gettext.translation(self.domain, self.localedir, languages=[lang_code])
                        logger.debug(f"Loaded translation for '{lang_code}'", "TranslationManager")
                except FileNotFoundError:
                    logger.debug(f"Warning: Translation file for '{lang_code}' not found, falling back to system language", "TranslationManager")
                    # Try system language translation
                    system_lang = self._get_system_language()
                    try:
                        if system_lang == self.fallback_language:
                            trans = gettext.NullTranslations()
                        else:
                            trans = gettext.translation(self.domain, self.localedir, languages=[system_lang])
                        lang_code = system_lang
                    except FileNotFoundError:
                        # Final fallback to default language
                        trans = gettext.NullTranslations()
                        lang_code = self.fallback_language

                logger.debug("Gettext translation loading completed", "TranslationManager")

        # Install the translation
        with logger.performance.operation_context("trans_install", "TranslationManager"):
            trans.install()

        # Update translation function
        self.translate_func = trans.gettext
        self.current_language = lang_code
        logger.debug("Updated translation function and current language", "TranslationManager")

        # Note: Language is saved by AppSettings, not TranslationManager
        # This avoids race conditions between the two settings systems

        # Refresh translations for all registered widgets immediately
        if self.translatable_widgets:
            with logger.performance.operation_context("widget_refresh", "TranslationManager"):
                logger.debug(f"Starting widget refresh for {len(self.translatable_widgets)} widgets", "TranslationManager")
                self._refresh_translations_immediate()

        logger.debug(f"Language switched to '{lang_code}'", "TranslationManager")

        return lang_code

    def get_current_language(self) -> Optional[str]:
        """Get the currently active language code."""
        return self.current_language

    def get_supported_languages(self) -> Set[str]:
        """Get the set of supported language codes."""
        return self.supported_languages.copy()

    def register_widget(
        self, widget: Gtk.Widget, translation_key: str, property_name: str = "label", widget_id: Optional[str] = None
    ):
        """
        Manually register a widget for translation.

        Args:
            widget: The GTK widget to translate
            translation_key: The key for translation lookup
            property_name: The property to update (e.g., "label", "title")
            widget_id: Optional ID for state management
        """
        # Check if this widget is already registered to prevent duplicates
        widget_already_registered = False
        for existing_widget in self.translatable_widgets:
            if existing_widget["widget"] is widget:
                widget_already_registered = True
                break

        if not widget_already_registered:
            self.translatable_widgets.append(
                {
                    "widget": widget,
                    "translation_key": translation_key,
                    "property_name": property_name,
                    "widget_id": widget_id,
                    "original_text": translation_key,
                }
            )

    def scan_builder_widgets(self, builder: Gtk.Builder):
        """
        Scan all widgets from a Gtk.Builder and register those marked as translatable.

        This method finds widgets that were marked with translatable="yes" in the UI file
        by capturing their current text values as translation keys.
        """
        start_time = time.time()
        # Create a unique identifier for this builder based on its objects
        builder_id = id(builder)
        if builder_id in self._scanned_builders:
            logger.debug("Skipping scan_builder_widgets - builder {builder_id} already scanned", "TranslationManager")
            return

        # Get all objects from the builder
        get_objects_start = time.time()
        objects = builder.get_objects()
        get_objects_end = time.time()
        logger.debug("Getting {len(objects)} objects took {(get_objects_end - get_objects_start)*1000:.1f}ms from builder {builder_id}", "TranslationManager")

        # Mark this builder as scanned
        self._scanned_builders.add(builder_id)
        widgets_before = len(self.translatable_widgets)

        scan_start = time.time()
        for obj in objects:
            if isinstance(obj, Gtk.Widget):
                widget_id = self._get_widget_id(obj, builder)
                self._check_and_register_widget(obj, widget_id)
        scan_end = time.time()

        widgets_after = len(self.translatable_widgets)
        newly_registered = widgets_after - widgets_before
        end_time = time.time()
        total_time = (end_time - start_time) * 1000
        scan_time = (scan_end - scan_start) * 1000
        logger.debug("Registered {newly_registered} new widgets (total: {widgets_after}) - SCAN TIME: {total_time:.1f}ms (widget processing: {scan_time:.1f}ms)", "TranslationManager")

    def _get_widget_id(self, widget: Gtk.Widget, builder: Gtk.Builder) -> Optional[str]:
        """Try to find the ID of a widget from the builder."""
        # Try to get the buildable name (the ID from the UI file)
        if hasattr(widget, "get_buildable_id"):
            return widget.get_buildable_id()

        # Fallback: check all objects to find matching widget
        objects = builder.get_objects()
        for obj in objects:
            if obj is widget and hasattr(obj, "get_name"):
                return obj.get_name()

        return None

    def _check_and_register_widget(self, widget: Gtk.Widget, widget_id: Optional[str]):
        """Check if a widget should be registered for translation and register it."""
        translation_key = None
        property_name = None

        # Determine if this widget type can be translated and get its current text
        if isinstance(widget, Gtk.Label):
            text = widget.get_label()
            if text:
                translation_key = text
                property_name = "label"

        elif isinstance(widget, Gtk.Button):
            text = widget.get_label()
            if text:
                translation_key = text
                property_name = "label"

        elif isinstance(widget, (Gtk.Window, Gtk.Dialog)):
            text = widget.get_title()
            if text:
                translation_key = text
                property_name = "title"

        elif isinstance(widget, Gtk.MenuButton):
            text = widget.get_label()
            if text:
                translation_key = text
                property_name = "label"

        # Only register if we found translatable text
        if translation_key and translation_key.strip():
            # Check if this widget is already registered to prevent duplicates
            widget_already_registered = False
            for existing_widget in self.translatable_widgets:
                if existing_widget["widget"] is widget:
                    widget_already_registered = True
                    break

            if not widget_already_registered:
                self.translatable_widgets.append(
                    {
                        "widget": widget,
                        "translation_key": translation_key,
                        "property_name": property_name,
                        "widget_id": widget_id,
                        "original_text": translation_key,
                    }
                )
                widget_name = widget.__class__.__name__
                widget_display = widget_id or "(no id)"
                logger.debug("Registered {widget_name} '{widget_display}' with text: '{translation_key}'", "TranslationManager")
            else:
                widget_name = widget.__class__.__name__
                widget_display = widget_id or "(no id)"
                logger.debug("Skipped duplicate {widget_name} '{widget_display}' with text: '{translation_key}'", "TranslationManager")

    def set_widget_state(self, widget_id: str, key: str, value: Any):
        """Store state for a widget (e.g., whether button was clicked)."""
        if widget_id not in self.state_storage:
            self.state_storage[widget_id] = {}
        self.state_storage[widget_id][key] = value

    def get_widget_state(self, widget_id: str, key: str, default: Any = None) -> Any:
        """Retrieve stored state for a widget."""
        return self.state_storage.get(widget_id, {}).get(key, default)

    def update_translation_key(self, widget_id: str, new_key: str):
        """Update the translation key for a specific widget."""
        for widget_info in self.translatable_widgets:
            if widget_info.get("widget_id") == widget_id:
                widget_info["translation_key"] = new_key
                break

    def refresh_all_translations(self):
        """Refresh translations for all registered widgets immediately."""
        self._refresh_translations_immediate()

    def _refresh_translations_immediate(self):
        """Update all widget translations immediately."""
        start_time = time.time()
        if self._updating:
            logger.debug("Skipping refresh - already updating", "TranslationManager")
            return

        self._updating = True
        try:
            logger.debug("Starting immediate refresh for {len(self.translatable_widgets)} widgets", "TranslationManager")

            translate_time = 0
            set_property_time = 0

            for i, widget_info in enumerate(self.translatable_widgets):
                widget = widget_info["widget"]
                translation_key = widget_info["translation_key"]
                property_name = widget_info["property_name"]
                widget_id = widget_info.get("widget_id")

                # Skip if widget has been destroyed
                if not widget or not hasattr(widget, "get_visible"):
                    logger.debug("Skipping destroyed widget :", "TranslationManager")
                    continue

                try:
                    # Time the translation lookup
                    trans_start = time.time()
                    translated_text = self.translate_func(translation_key)
                    trans_end = time.time()
                    translate_time += trans_end - trans_start

                    # Time the property setting
                    prop_start = time.time()
                    self._set_widget_property(widget, property_name, translated_text)
                    prop_end = time.time()
                    set_property_time += prop_end - prop_start

                    # Log every 50th widget to track progress without spam
                    if i % 50 == 0 or i < 10:
                        logger.debug("Widget {i}/{len(self.translatable_widgets)}: '{translation_key}' -> '{translated_text}' ({widget_id})", "TranslationManager")
                except Exception as e:
                    logger.debug("Warning: Could not translate widget {widget_id} property {property_name}: {e}", "TranslationManager")

            end_time = time.time()
            total_time = (end_time - start_time) * 1000
            logger.debug("Translation refresh completed - TOTAL: {total_time:.1f}ms (translate: {translate_time*1000:.1f}ms, set_property: {set_property_time*1000:.1f}ms)", "TranslationManager")
        finally:
            self._updating = False

    def _set_widget_property(self, widget: Gtk.Widget, property_name: str, value: str):
        """Set a property on a widget with appropriate method."""
        if property_name == "label":
            if hasattr(widget, "set_label"):
                widget.set_label(value)
        elif property_name == "title":
            if hasattr(widget, "set_title"):
                widget.set_title(value)
        elif property_name == "text":
            if hasattr(widget, "set_text"):
                widget.set_text(value)
        else:
            # Try generic property setting
            try:
                widget.set_property(property_name, value)
            except Exception as e:
                logger.debug("Warning: Could not set property ...: ...", "TranslationManager")

    def get_translatable_widgets(self) -> List[Dict[str, Any]]:
        """Get list of all registered translatable widgets."""
        return self.translatable_widgets.copy()

    def clear_registrations(self):
        """Clear all registered widgets."""
        self.translatable_widgets.clear()
        self.state_storage.clear()

    def print_discovered_widgets(self):
        """Debug method to print all discovered translatable widgets."""
        logger.debug("Discovered translatable widgets:", "TranslationManager")
        for widget_info in self.translatable_widgets:
            widget_id = widget_info.get("widget_id", "Unknown")
            widget_type = type(widget_info["widget"]).__name__
            translation_key = widget_info["translation_key"]
            property_name = widget_info["property_name"]
            logger.debug(f"  - {widget_id} ({widget_type}): '{translation_key}' -> {property_name}", "TranslationManager")
