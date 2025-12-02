#!/usr/bin/env python3
"""
GTK3 Implementation of Translation Manager

This implementation provides compatibility with GTK3 widgets and applications,
specifically designed for use with system tray applications that require GTK3
due to AppIndicator3 dependencies.
"""
# isort: skip_file

# fmt: off
import gettext
import locale
import os
import sys
import time
from typing import Any, Callable, Dict, List, Optional, Set

import gi

if "gi.repository.Gtk" not in sys.modules:
    gi.require_version("Gdk", "3.0")  # noqa: E402
    gi.require_version("Gtk", "3.0")  # noqa: E402

# GTK3 imports - Gio imported for interface compatibility with GTK4 version
from gi.repository import Gtk  # noqa: E402,F401

# Import logger first
from d_fake_seeder.lib.logger import logger  # noqa: E402

try:
    from gi.repository import Gio  # noqa: E402
except ImportError as e:
    # Fallback if Gio has version conflicts
    logger.warning(f"Could not import Gio in GTK3 mode: {e}", "TranslationManagerGTK3")
    Gio = None

from .base import TranslationManagerBase  # noqa: E402

# fmt: on


class TranslationManagerGTK3(TranslationManagerBase):
    """
    GTK3 implementation of the TranslationManager

    This implementation provides translation management for GTK3 applications,
    with a focus on system tray applications and AppIndicator3 compatibility.
    """

    def __init__(
        self,
        domain: str = "messages",
        localedir: Optional[str] = None,
        supported_languages: Optional[Set[str]] = None,
        fallback_language: str = "en",
    ):
        """Initialize the GTK3 translation manager"""
        self._domain = domain
        self._localedir = localedir or os.path.join(os.getcwd(), "locale")
        self.fallback_language = fallback_language

        # Auto-discover supported languages if not provided
        if supported_languages is None:
            self.supported_languages = self._discover_supported_languages()
        else:
            self.supported_languages = supported_languages

        self._current_language: Optional[str] = None
        self.translate_func = lambda x: x  # Default passthrough
        self.translatable_widgets: List[Dict[str, Any]] = []
        self.translatable_menus: List[Dict[str, Any]] = []
        self.state_storage: Dict[str, Any] = {}
        self._updating = False

        # Set up gettext domain
        gettext.bindtextdomain(self._domain, self._localedir)
        gettext.textdomain(self._domain)

    @property
    def domain(self) -> str:
        """Translation domain name"""
        return self._domain

    @property
    def localedir(self) -> str:
        """Locale directory path"""
        return self._localedir

    @property
    def current_language(self) -> str:
        """Currently active language code"""
        return self._current_language or self.fallback_language

    @property
    def gtk_version(self) -> str:
        """GTK version this implementation supports"""
        return "3"

    def _discover_supported_languages(self) -> Set[str]:
        """Dynamically discover supported languages from the locale directory"""
        logger.debug(
            f"Starting language discovery in {self._localedir}",
            "TranslationManagerGTK3",
        )
        start_time = time.time()
        discovered_languages = {self.fallback_language}

        try:
            if os.path.exists(self._localedir):
                for item in os.listdir(self._localedir):
                    lang_dir = os.path.join(self._localedir, item)
                    if os.path.isdir(lang_dir) and self._is_valid_language_code(item):
                        lc_messages_dir = os.path.join(lang_dir, "LC_MESSAGES")
                        if os.path.exists(lc_messages_dir):
                            mo_files = [f for f in os.listdir(lc_messages_dir) if f.endswith(".mo")]
                            if mo_files:
                                discovered_languages.add(item)

            end_time = time.time()
            discovery_time = (end_time - start_time) * 1000
            logger.debug(
                f"Discovered languages: {sorted(discovered_languages)} (took {discovery_time:.1f}ms)",
                "TranslationManagerGTK3",
            )
        except Exception:
            logger.debug("Warning: Could not discover languages", "TranslationManagerGTK3")

        return discovered_languages

    def _is_valid_language_code(self, code: str) -> bool:
        """Check if a string looks like a valid language code"""
        import re

        pattern = r"^[a-z]{2,3}(_[A-Z]{2})?$"
        return bool(re.match(pattern, code))

    def switch_language(self, language_code: str) -> str:
        """Switch to a specific language"""
        logger.debug(f"switch_language() called with: {language_code}", "TranslationManagerGTK3")

        if self._current_language == language_code:
            logger.debug(
                f"Already using language '{language_code}' - skipping switch",
                "TranslationManagerGTK3",
            )
            return language_code

        # Validate language is supported
        if language_code not in self.supported_languages:
            logger.debug(
                f"Warning: Unsupported language '{language_code}', falling back to system locale",
                "TranslationManagerGTK3",
            )
            language_code = self._get_system_language()

        # Create translation object
        try:
            if language_code == self.fallback_language:
                trans = gettext.NullTranslations()
                logger.debug(
                    "Using NullTranslations for fallback language",
                    "TranslationManagerGTK3",
                )
            else:
                trans = gettext.translation(self._domain, self._localedir, languages=[language_code])
                logger.debug(
                    f"Loaded translation for '{language_code}'",
                    "TranslationManagerGTK3",
                )
        except FileNotFoundError:
            logger.debug(
                f"Warning: Translation file for '{language_code}' not found",
                "TranslationManagerGTK3",
            )
            trans = gettext.NullTranslations()
            language_code = self.fallback_language

        # Install translation
        trans.install()
        self.translate_func = trans.gettext
        self._current_language = language_code

        # Update all registered widgets
        if self.translatable_widgets:
            self._refresh_translations_immediate()

        logger.debug(f"Language switched to '{language_code}'", "TranslationManagerGTK3")
        return language_code

    def _get_system_language(self) -> str:
        """Detect system language and map to supported languages"""
        try:
            try:
                current_locale = locale.getlocale()[0]
                system_locale = current_locale if current_locale else locale.getdefaultlocale()[0]
            except Exception:
                system_locale = locale.getdefaultlocale()[0]

            if system_locale:
                lang_code = system_locale.split("_")[0].lower()
                if lang_code in self.supported_languages:
                    return lang_code
        except Exception:
            logger.debug("Warning: Could not detect system locale", "TranslationManagerGTK3")

        return self.fallback_language

    def get_translate_func(self) -> Callable[[str], str]:
        """Get the translation function for the current language"""
        return self.translate_func

    def get_current_language(self) -> str:
        """Get the currently active language code"""
        return self._current_language or self.fallback_language

    def get_available_languages(self) -> List[str]:
        """Get list of available languages"""
        return sorted(list(self.supported_languages))

    def register_translation_function(self, widget: Any, get_text_func: Callable[[], str]) -> None:
        """Register a translation function for automatic widget updates"""
        # For GTK3, we'll use a simplified approach since this is mainly for tray applications
        translation_key = get_text_func()
        widget_id = getattr(widget, "get_name", lambda: None)()

        # Simple property detection for GTK3 widgets
        if hasattr(widget, "set_label"):
            property_name = "label"
        elif hasattr(widget, "set_title"):
            property_name = "title"
        elif hasattr(widget, "set_text"):
            property_name = "text"
        else:
            property_name = "label"  # Default

        self.register_widget(widget, translation_key, property_name, widget_id)

    def register_widget(
        self,
        widget: Any,  # More flexible for GTK3 compatibility
        translation_key: str,
        property_name: str = "label",
        widget_id: Optional[str] = None,
    ):
        """Manually register a widget for translation"""
        # Check if already registered
        for existing_widget in self.translatable_widgets:
            if existing_widget["widget"] is widget and existing_widget["property_name"] == property_name:
                return

        self.translatable_widgets.append(
            {
                "widget": widget,
                "translation_key": translation_key,
                "property_name": property_name,
                "widget_id": widget_id,
                "original_text": translation_key,
            }
        )

    def update_translations(self) -> None:
        """Update all registered translation functions"""
        self._refresh_translations_immediate()

    def _refresh_translations_immediate(self):
        """Update all widget translations immediately"""
        if self._updating:
            return

        self._updating = True
        try:
            for widget_info in self.translatable_widgets:
                widget = widget_info["widget"]
                translation_key = widget_info["translation_key"]
                property_name = widget_info["property_name"]

                # Skip destroyed widgets
                try:
                    if not widget:
                        continue
                    # GTK3 compatibility check
                    if hasattr(widget, "get_visible") and not widget.get_realized():
                        continue
                except Exception:
                    continue

                try:
                    translated_text = self.translate_func(translation_key)
                    self._set_widget_property(widget, property_name, translated_text)
                except Exception as e:
                    logger.debug(f"Warning: Could not translate widget property {property_name}: {e}")
        finally:
            self._updating = False

    def _set_widget_property(self, widget: Any, property_name: str, value: str):
        """Set a property on a widget with appropriate method"""
        try:
            if property_name == "label" and hasattr(widget, "set_label"):
                widget.set_label(value)
            elif property_name == "title" and hasattr(widget, "set_title"):
                widget.set_title(value)
            elif property_name == "text" and hasattr(widget, "set_text"):
                widget.set_text(value)
            elif property_name == "tooltip_text" and hasattr(widget, "set_tooltip_text"):
                widget.set_tooltip_text(value)
            elif hasattr(widget, "set_property"):
                widget.set_property(property_name, value)
        except Exception as e:
            logger.debug(f"Warning: Could not set property '{property_name}': {e}")

    def get_language_name(self, language_code: str) -> str:
        """Get the display name for a language code"""
        language_names = {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "ru": "Русский",
            "zh": "中文",
            "ja": "日本語",
            "ko": "한국어",
            "ar": "العربية",
            "hi": "हिन्दी",
            "nl": "Nederlands",
            "sv": "Svenska",
            "pl": "Polski",
        }
        return language_names.get(language_code, language_code.upper())

    def set_default_language(self, language_code: str) -> None:
        """Set the default fallback language"""
        self.fallback_language = language_code

    def get_translation_coverage(self, language_code: str) -> Dict[str, Any]:
        """Get translation coverage information for a language"""
        try:
            if language_code == self.fallback_language:
                return {
                    "translated_count": 100,
                    "total_count": 100,
                    "coverage_percent": 100,
                }

            gettext.translation(self._domain, self._localedir, languages=[language_code])
            return {"translated_count": 1, "total_count": 1, "coverage_percent": 100}
        except FileNotFoundError:
            return {"translated_count": 0, "total_count": 1, "coverage_percent": 0}

    # GTK3-specific simplified methods for tray applications
    def register_simple_text(self, text_key: str) -> str:
        """
        Simple text translation for menu items and labels

        This is a convenience method for tray applications that don't need
        complex widget management but need translation support.
        """
        return self.translate_func(text_key)

    def create_translated_menu_items(self, menu_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Create translated menu items for GTK3 menus

        Args:
            menu_items: List of dicts with 'key' and 'action' fields

        Returns:
            List of dicts with translated text and actions
        """
        translated_items = []
        for item in menu_items:
            translated_text = self.translate_func(item["key"])
            translated_items.append({"text": translated_text, "action": item.get("action", "")})
        return translated_items

    def get_language_display_names(self) -> Dict[str, str]:
        """Get a mapping of language codes to display names"""
        return {lang: self.get_language_name(lang) for lang in self.supported_languages}

    # Additional methods for full feature parity with GTK4 implementation

    def refresh_supported_languages(self) -> Set[str]:
        """Re-scan the locale directory and update supported languages"""
        self.supported_languages = self._discover_supported_languages()
        return self.supported_languages.copy()

    def setup_translations(self, auto_detect: bool = True) -> str:
        """Set up translations with automatic language detection"""
        logger.debug(
            f"setup_translations called with auto_detect={auto_detect}",
            "TranslationManagerGTK3",
        )

        if auto_detect:
            target_language = self._get_target_language()
            logger.debug(
                f"_get_target_language() returned: {target_language}",
                "TranslationManagerGTK3",
            )
        else:
            target_language = self.fallback_language
            logger.debug(f"Using fallback language: {target_language}", "TranslationManagerGTK3")

        result = self.switch_language(target_language)
        logger.debug("setup_translations completed", "TranslationManagerGTK3")
        return result

    def _get_target_language(self) -> str:
        """Determine target language from config and system locale"""
        # Get system locale as fallback
        system_language = self._get_system_language()
        logger.debug(f"System language detected: {system_language}", "TranslationManagerGTK3")

        # Try to get language from AppSettings first (if available)
        try:
            from domain.app_settings import AppSettings

            app_settings = AppSettings.get_instance()
            logger.debug("AppSettings.get_instance() completed", "TranslationManagerGTK3")

            language = app_settings.get_language()
            logger.debug(
                f"AppSettings.get_language() returned: {language}",
                "TranslationManagerGTK3",
            )

            logger.debug(
                f"_get_target_language() final target: {language}",
                "TranslationManagerGTK3",
            )
            return language
        except Exception as e:
            logger.debug(
                f"Could not get language from AppSettings: {e}",
                "TranslationManagerGTK3",
            )

        # Fallback to system language
        logger.debug(
            f"AppSettings failed, falling back to system language: {system_language}",
            "TranslationManagerGTK3",
        )
        return system_language

    def get_supported_languages(self) -> Set[str]:
        """Get the set of supported language codes"""
        return self.supported_languages.copy()

    def set_widget_state(self, widget_id: str, key: str, value: Any):
        """Store state for a widget (e.g., whether button was clicked)"""
        if not hasattr(self, "state_storage"):
            self.state_storage = {}
        if widget_id not in self.state_storage:
            self.state_storage[widget_id] = {}
        self.state_storage[widget_id][key] = value

    def get_widget_state(self, widget_id: str, key: str, default: Any = None) -> Any:
        """Retrieve stored state for a widget"""
        if not hasattr(self, "state_storage"):
            self.state_storage = {}
        return self.state_storage.get(widget_id, {}).get(key, default)

    def update_translation_key(self, widget_id: str, new_key: str):
        """Update the translation key for a specific widget"""
        for widget_info in self.translatable_widgets:
            if widget_info.get("widget_id") == widget_id:
                widget_info["translation_key"] = new_key
                break

    def refresh_all_translations(self):
        """Refresh translations for all registered widgets immediately"""
        self._refresh_translations_immediate()

    def get_translatable_widgets(self) -> List[Dict[str, Any]]:
        """Get list of all registered translatable widgets"""
        return self.translatable_widgets.copy()

    def clear_registrations(self):
        """Clear all registered widgets and menus"""
        self.translatable_widgets.clear()
        if hasattr(self, "translatable_menus"):
            self.translatable_menus.clear()
        if hasattr(self, "state_storage"):
            self.state_storage.clear()
        if hasattr(self, "_scanned_builders"):
            self._scanned_builders.clear()

    def print_discovered_widgets(self):
        """Debug method to print all discovered translatable widgets"""
        logger.debug("Discovered translatable widgets:", "TranslationManagerGTK3")
        for widget_info in self.translatable_widgets:
            widget_id = widget_info.get("widget_id", "Unknown")
            widget_type = type(widget_info["widget"]).__name__
            translation_key = widget_info["translation_key"]
            property_name = widget_info["property_name"]
            logger.debug(
                f"  - {widget_id} ({widget_type}): '{translation_key}' -> {property_name}",
                "TranslationManagerGTK3",
            )

    # GTK3 Builder scanning functionality (simplified for GTK3)
    def scan_builder_widgets(self, builder):
        """
        Scan all widgets from a builder and register translatable ones.
        Simplified for GTK3 compatibility but maintains same interface.
        """
        # Create a unique identifier for this builder
        builder_id = id(builder)
        if not hasattr(self, "_scanned_builders"):
            self._scanned_builders = set()

        if builder_id in self._scanned_builders:
            logger.debug(
                f"Skipping scan_builder_widgets - builder {builder_id} already scanned",
                "TranslationManagerGTK3",
            )
            return

        # Get all objects from the builder
        try:
            objects = builder.get_objects()
            logger.debug(
                f"Getting {len(objects)} objects from builder {builder_id}",
                "TranslationManagerGTK3",
            )
        except Exception as e:
            logger.debug(f"Could not get objects from builder: {e}", "TranslationManagerGTK3")
            return

        # Mark this builder as scanned
        self._scanned_builders.add(builder_id)
        widgets_before = len(self.translatable_widgets)

        for obj in objects:
            # GTK3 compatible widget checking
            if hasattr(obj, "get_visible"):  # Basic widget check for GTK3
                widget_id = self._get_widget_id(obj, builder)
                self._check_and_register_widget(obj, widget_id)

        widgets_after = len(self.translatable_widgets)
        newly_registered = widgets_after - widgets_before
        logger.debug(
            f"Registered {newly_registered} new widgets (total: {widgets_after})",
            "TranslationManagerGTK3",
        )

    def _get_widget_id(self, widget, builder) -> Optional[str]:
        """Try to find the ID of a widget from the builder (GTK3 compatible)"""
        try:
            # Try to get the buildable name (the ID from the UI file)
            if hasattr(widget, "get_buildable_id"):
                return widget.get_buildable_id()
            elif hasattr(widget, "get_name"):
                return widget.get_name()
        except Exception:
            pass

        # Fallback: check all objects to find matching widget
        try:
            objects = builder.get_objects()
            for obj in objects:
                if obj is widget and hasattr(obj, "get_name"):
                    return obj.get_name()
        except Exception:
            pass

        return None

    def _check_and_register_widget(self, widget, widget_id: Optional[str]):
        """Check if a widget should be registered for translation (GTK3 compatible)"""
        translatable_properties = []

        try:
            # Check for different translatable properties based on widget type
            # Use string-based type checking for better GTK3 compatibility
            widget_type = widget.__class__.__name__

            if "Label" in widget_type:
                if hasattr(widget, "get_label"):
                    text = widget.get_label()
                    if text and text.strip():
                        translatable_properties.append(("label", text))

            elif "Button" in widget_type:
                # Check for button label
                if hasattr(widget, "get_label"):
                    text = widget.get_label()
                    if text and text.strip():
                        translatable_properties.append(("label", text))
                # Check for tooltip text on buttons
                if hasattr(widget, "get_tooltip_text"):
                    tooltip_text = widget.get_tooltip_text()
                    if tooltip_text and tooltip_text.strip():
                        translatable_properties.append(("tooltip_text", tooltip_text))

            elif "CheckButton" in widget_type or "ToggleButton" in widget_type:
                # Check for checkbox/toggle label
                if hasattr(widget, "get_label"):
                    text = widget.get_label()
                    if text and text.strip():
                        translatable_properties.append(("label", text))
                # Check for tooltip text
                if hasattr(widget, "get_tooltip_text"):
                    tooltip_text = widget.get_tooltip_text()
                    if tooltip_text and tooltip_text.strip():
                        translatable_properties.append(("tooltip_text", tooltip_text))

            elif "Window" in widget_type or "Dialog" in widget_type:
                if hasattr(widget, "get_title"):
                    text = widget.get_title()
                    if text and text.strip():
                        translatable_properties.append(("title", text))

            elif "MenuButton" in widget_type:
                if hasattr(widget, "get_label"):
                    text = widget.get_label()
                    if text and text.strip():
                        translatable_properties.append(("label", text))
                # Check for tooltip text
                if hasattr(widget, "get_tooltip_text"):
                    tooltip_text = widget.get_tooltip_text()
                    if tooltip_text and tooltip_text.strip():
                        translatable_properties.append(("tooltip_text", tooltip_text))

            elif "Entry" in widget_type:
                # Check for placeholder text in entries
                if hasattr(widget, "get_placeholder_text"):
                    placeholder_text = widget.get_placeholder_text()
                    if placeholder_text and placeholder_text.strip():
                        translatable_properties.append(("placeholder_text", placeholder_text))
                # Check for tooltip text
                if hasattr(widget, "get_tooltip_text"):
                    tooltip_text = widget.get_tooltip_text()
                    if tooltip_text and tooltip_text.strip():
                        translatable_properties.append(("tooltip_text", tooltip_text))

            else:
                # For any other widget, check for tooltip text
                if hasattr(widget, "get_tooltip_text"):
                    tooltip_text = widget.get_tooltip_text()
                    if tooltip_text and tooltip_text.strip():
                        translatable_properties.append(("tooltip_text", tooltip_text))

        except Exception as e:
            logger.debug(f"Error checking widget for translation: {e}", "TranslationManagerGTK3")

        # Register each translatable property separately
        for property_name, translation_key in translatable_properties:
            # Check if this specific widget+property combination is already registered
            already_registered = False
            for existing_widget in self.translatable_widgets:
                if existing_widget["widget"] is widget and existing_widget["property_name"] == property_name:
                    already_registered = True
                    break

            if not already_registered:
                self.translatable_widgets.append(
                    {
                        "widget": widget,
                        "translation_key": translation_key,
                        "property_name": property_name,
                        "widget_id": widget_id,
                        "original_text": translation_key,
                    }
                )
                logger.debug(
                    f"Registered {widget.__class__.__name__} '{widget_id or '(no id)'}' "
                    f"property '{property_name}' with text: '{translation_key}'",
                    "TranslationManagerGTK3",
                )

    # Menu functionality for GTK3 (using Gio.Menu if available)
    def register_menu(self, menu, menu_items: List[Dict[str, str]], popover=None):
        """Register a menu for translation updates (GTK3 compatible)"""
        if not hasattr(self, "translatable_menus"):
            self.translatable_menus = []

        # Check if this menu is already registered
        for existing_menu in self.translatable_menus:
            if existing_menu["menu"] is menu:
                logger.debug("Skipping duplicate menu registration", "TranslationManagerGTK3")
                return

        menu_info = {"menu": menu, "items": menu_items, "popover": popover}
        self.translatable_menus.append(menu_info)
        logger.debug(
            f"Registered menu with {len(menu_items)} items for translation",
            "TranslationManagerGTK3",
        )

    def refresh_menu_translations(self):
        """Recreate all registered menus with translated text (GTK3 compatible)"""
        if not hasattr(self, "translatable_menus"):
            self.translatable_menus = []

        if not self.translatable_menus:
            logger.debug("No menus registered for translation", "TranslationManagerGTK3")
            return

        logger.debug(
            f"Refreshing translations for {len(self.translatable_menus)} menus",
            "TranslationManagerGTK3",
        )

        for menu_info in self.translatable_menus:
            try:
                self._recreate_menu(menu_info)
            except Exception as e:
                logger.debug(
                    f"Warning: Could not refresh menu translations: {e}",
                    "TranslationManagerGTK3",
                )

    def _recreate_menu(self, menu_info: Dict[str, Any]):
        """Recreate a menu with translated text (GTK3 compatible)"""
        menu = menu_info["menu"]
        items = menu_info["items"]
        popover = menu_info.get("popover")

        try:
            # Clear existing menu items if possible
            if hasattr(menu, "remove_all"):
                menu.remove_all()

            # Recreate menu with translated text
            for item in items:
                translated_text = self.translate_func(item["key"])
                if hasattr(menu, "append"):
                    menu.append(translated_text, item["action"])
                logger.debug(
                    f"Menu item: '{item['key']}' -> '{translated_text}' (action: {item.get('action', 'none')})",
                    "TranslationManagerGTK3",
                )

            # If menu is attached to a popover, trigger UI update
            if popover and hasattr(popover, "set_menu_model"):
                popover.set_menu_model(menu)
                logger.debug("Updated popover menu model", "TranslationManagerGTK3")

        except Exception as e:
            logger.debug(f"Could not recreate menu: {e}", "TranslationManagerGTK3")
