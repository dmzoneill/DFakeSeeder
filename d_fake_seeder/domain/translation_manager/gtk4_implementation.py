#!/usr/bin/env python3
"""
GTK4 Implementation of Translation Manager

This implementation provides full compatibility with GTK4 widgets and applications.
It includes all the advanced features like widget discovery, menu translation,
and automatic UI updates.
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
    gi.require_version("Gtk", "4.0")  # noqa: E402

from gi.repository import Gio, Gtk  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402

from .base import TranslationManagerBase  # noqa: E402

# fmt: on


class TranslationManagerGTK4(TranslationManagerBase):
    """
    GTK4 implementation of the TranslationManager

    This implementation provides complete translation management for GTK4 applications,
    including automatic widget discovery, menu translation, and runtime language switching.
    """

    def __init__(
        self,
        domain: str = "messages",
        localedir: Optional[str] = None,
        supported_languages: Optional[Set[str]] = None,
        config_file: Optional[str] = None,
        fallback_language: str = "en",
    ):
        """Initialize the GTK4 translation manager"""
        self._domain = domain
        self._localedir = localedir or os.path.join(os.getcwd(), "locale")
        self.config_file = config_file or os.path.join(os.getcwd(), "config.json")
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
        self._scanned_builders: Set[Any] = set()

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
        return "4"

    def _discover_supported_languages(self) -> Set[str]:
        """Dynamically discover supported languages from the locale directory"""
        logger.debug(
            f"Starting language discovery in {self._localedir}",
            "TranslationManagerGTK4",
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
                "TranslationManagerGTK4",
            )
        except Exception:
            logger.debug("Warning: Could not discover languages", "TranslationManagerGTK4")

        return discovered_languages

    def _is_valid_language_code(self, code: str) -> bool:
        """Check if a string looks like a valid language code"""
        import re

        pattern = r"^[a-z]{2,3}(_[A-Z]{2})?$"
        return bool(re.match(pattern, code))

    def switch_language(self, language_code: str) -> str:
        """Switch to a specific language"""
        with logger.performance.operation_context("switch_language", "TranslationManagerGTK4"):
            logger.debug(
                f"switch_language() called with: {language_code}",
                "TranslationManagerGTK4",
            )

            if self._current_language == language_code:
                logger.debug(
                    f"Already using language '{language_code}' - skipping switch",
                    "TranslationManagerGTK4",
                )
                return language_code

            # Validate language is supported
            if language_code not in self.supported_languages:
                logger.debug(
                    f"Warning: Unsupported language '{language_code}', falling back to system locale",
                    "TranslationManagerGTK4",
                )
                language_code = self._get_system_language()

            # Create translation object
            try:
                if language_code == self.fallback_language:
                    trans = gettext.NullTranslations()
                    logger.debug(
                        "Using NullTranslations for fallback language",
                        "TranslationManagerGTK4",
                    )
                else:
                    trans = gettext.translation(self._domain, self._localedir, languages=[language_code])
                    logger.debug(
                        f"Loaded translation for '{language_code}'",
                        "TranslationManagerGTK4",
                    )
            except FileNotFoundError:
                logger.debug(
                    f"Warning: Translation file for '{language_code}' not found",
                    "TranslationManagerGTK4",
                )
                trans = gettext.NullTranslations()
                language_code = self.fallback_language

            # Install translation
            trans.install()
            self.translate_func = trans.gettext
            self._current_language = language_code

            # Update all registered widgets and menus
            if self.translatable_widgets:
                self._refresh_translations_immediate()
            if self.translatable_menus:
                self.refresh_menu_translations()

            logger.debug(f"Language switched to '{language_code}'", "TranslationManagerGTK4")
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
            logger.debug("Warning: Could not detect system locale", "TranslationManagerGTK4")

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
        # Extract widget type and property for registration
        if isinstance(widget, Gtk.Label):
            property_name = "label"
        elif isinstance(widget, Gtk.Button):
            property_name = "label"
        elif isinstance(widget, (Gtk.Window, Gtk.Dialog)):
            property_name = "title"
        else:
            property_name = "label"  # Default

        # Get the text to use as translation key
        translation_key = get_text_func()

        # Register the widget
        widget_id = getattr(widget, "get_buildable_id", lambda: None)()
        self.register_widget(widget, translation_key, property_name, widget_id)

    def register_widget(
        self,
        widget: Gtk.Widget,
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
                if not widget or not hasattr(widget, "get_visible"):
                    continue

                try:
                    translated_text = self.translate_func(translation_key)
                    self._set_widget_property(widget, property_name, translated_text)
                except Exception as e:
                    logger.debug(f"Warning: Could not translate widget property {property_name}: {e}")
        finally:
            self._updating = False

    def _set_widget_property(self, widget: Gtk.Widget, property_name: str, value: str):
        """Set a property on a widget with appropriate method"""
        if property_name == "label":
            if hasattr(widget, "set_label"):
                widget.set_label(value)
        elif property_name == "title":
            if hasattr(widget, "set_title"):
                widget.set_title(value)
        elif property_name == "text":
            if hasattr(widget, "set_text"):
                widget.set_text(value)
        elif property_name == "tooltip_text":
            if hasattr(widget, "set_tooltip_text"):
                widget.set_tooltip_text(value)
        elif property_name == "placeholder_text":
            if hasattr(widget, "set_placeholder_text"):
                widget.set_placeholder_text(value)
        else:
            try:
                widget.set_property(property_name, value)
            except Exception as e:
                logger.debug(f"Warning: Could not set property '{property_name}': {e}")

    def get_language_name(self, language_code: str) -> str:
        """Get the display name for a language code"""
        # Load language names dynamically from configuration
        try:
            from lib.util.language_config import get_language_display_names

            language_names = get_language_display_names()
            return language_names.get(language_code, language_code.upper())
        except Exception as e:
            logger.debug(
                f"Could not load language names from config: {e}",
                "TranslationManagerGTK4",
            )
            # Ultimate fallback: uppercase language code
            return language_code.upper()

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
            # This is a simplified implementation - actual coverage would require parsing MO files
            return {"translated_count": 1, "total_count": 1, "coverage_percent": 100}
        except FileNotFoundError:
            return {"translated_count": 0, "total_count": 1, "coverage_percent": 0}

    # GTK4-specific methods for advanced functionality
    def scan_builder_widgets(self, builder: Gtk.Builder):
        """
        Scan all widgets from a Gtk.Builder and register those marked as translatable.
        This method finds widgets that were marked with translatable="yes" in the UI file
        by capturing their current text values as translation keys.
        """
        # Create a unique identifier for this builder based on its objects
        builder_id = id(builder)
        if builder_id in self._scanned_builders:
            logger.debug(
                f"Skipping scan_builder_widgets - builder {builder_id} already scanned",
                "TranslationManagerGTK4",
            )
            return

        # Get all objects from the builder
        objects = builder.get_objects()
        logger.debug(
            f"Getting {len(objects)} objects from builder {builder_id}",
            "TranslationManagerGTK4",
        )

        # Mark this builder as scanned
        self._scanned_builders.add(builder_id)
        widgets_before = len(self.translatable_widgets)

        for obj in objects:
            if isinstance(obj, Gtk.Widget):
                widget_id = self._get_widget_id(obj, builder)
                self._check_and_register_widget(obj, widget_id)

        widgets_after = len(self.translatable_widgets)
        newly_registered = widgets_after - widgets_before
        logger.debug(
            f"Registered {newly_registered} new widgets (total: {widgets_after})",
            "TranslationManagerGTK4",
        )

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
        # List to store multiple translatable properties for this widget
        translatable_properties = []

        # Check for different translatable properties based on widget type
        if isinstance(widget, Gtk.Label):
            text = widget.get_label()
            if text and text.strip():
                translatable_properties.append(("label", text))
        elif isinstance(widget, Gtk.Button):
            # Check for button label
            text = widget.get_label()
            if text and text.strip():
                translatable_properties.append(("label", text))
            # Check for tooltip text on buttons
            tooltip_text = widget.get_tooltip_text()
            if tooltip_text and tooltip_text.strip():
                translatable_properties.append(("tooltip_text", tooltip_text))
        elif isinstance(widget, Gtk.CheckButton):
            # Check for checkbox label
            text = widget.get_label()
            if text and text.strip():
                translatable_properties.append(("label", text))
            # Check for tooltip text on checkboxes
            tooltip_text = widget.get_tooltip_text()
            if tooltip_text and tooltip_text.strip():
                translatable_properties.append(("tooltip_text", tooltip_text))
        elif isinstance(widget, (Gtk.Window, Gtk.Dialog)):
            text = widget.get_title()
            if text and text.strip():
                translatable_properties.append(("title", text))
        elif isinstance(widget, Gtk.MenuButton):
            text = widget.get_label()
            if text and text.strip():
                translatable_properties.append(("label", text))
            # Check for tooltip text on menu buttons
            tooltip_text = widget.get_tooltip_text()
            if tooltip_text and tooltip_text.strip():
                translatable_properties.append(("tooltip_text", tooltip_text))
        elif isinstance(widget, Gtk.Entry):
            # Check for placeholder text in entries
            placeholder_text = widget.get_placeholder_text()
            if placeholder_text and placeholder_text.strip():
                translatable_properties.append(("placeholder_text", placeholder_text))
            # Check for tooltip text on entries
            tooltip_text = widget.get_tooltip_text()
            if tooltip_text and tooltip_text.strip():
                translatable_properties.append(("tooltip_text", tooltip_text))
        elif isinstance(widget, Gtk.Scale):
            # Check for tooltip text on scales
            tooltip_text = widget.get_tooltip_text()
            if tooltip_text and tooltip_text.strip():
                translatable_properties.append(("tooltip_text", tooltip_text))
        else:
            # For any other widget, check for tooltip text
            try:
                tooltip_text = widget.get_tooltip_text()
                if tooltip_text and tooltip_text.strip():
                    translatable_properties.append(("tooltip_text", tooltip_text))
            except AttributeError:
                # Some widgets might not support tooltips
                pass

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
                    "TranslationManagerGTK4",
                )
            else:
                logger.debug(
                    f"Skipped duplicate {widget.__class__.__name__} '{widget_id or '(no id)'}' "
                    f"property '{property_name}' with text: '{translation_key}'",
                    "TranslationManagerGTK4",
                )

    def register_menu(
        self,
        menu: Gio.Menu,
        menu_items: List[Dict[str, str]],
        popover: Optional[Gtk.PopoverMenu] = None,
    ):
        """Register a menu for translation updates"""
        for existing_menu in self.translatable_menus:
            if existing_menu["menu"] is menu:
                return

        menu_info = {"menu": menu, "items": menu_items, "popover": popover}
        self.translatable_menus.append(menu_info)

    def refresh_menu_translations(self):
        """Recreate all registered menus with translated text"""
        for menu_info in self.translatable_menus:
            try:
                self._recreate_menu(menu_info)
            except Exception as e:
                logger.debug(f"Warning: Could not refresh menu translations: {e}")

    def _recreate_menu(self, menu_info: Dict[str, Any]):
        """Recreate a menu with translated text"""
        menu = menu_info["menu"]
        items = menu_info["items"]
        popover = menu_info.get("popover")

        menu.remove_all()

        for item in items:
            translated_text = self.translate_func(item["key"])
            menu.append(translated_text, item["action"])

        if popover:
            popover.set_menu_model(menu)

    # Additional methods from original TranslationManager for full compatibility

    def refresh_supported_languages(self) -> Set[str]:
        """Re-scan the locale directory and update supported languages"""
        self.supported_languages = self._discover_supported_languages()
        return self.supported_languages.copy()

    def setup_translations(self, auto_detect: bool = True) -> str:
        """Set up translations with automatic language detection"""
        with logger.performance.operation_context("setup_translations", "TranslationManagerGTK4"):
            logger.debug(
                f"setup_translations called with auto_detect={auto_detect}",
                "TranslationManagerGTK4",
            )

            if auto_detect:
                target_language = self._get_target_language()
                logger.debug(
                    f"_get_target_language() returned: {target_language}",
                    "TranslationManagerGTK4",
                )
            else:
                target_language = self.fallback_language
                logger.debug(
                    f"Using fallback language: {target_language}",
                    "TranslationManagerGTK4",
                )

            result = self.switch_language(target_language)
            logger.debug("setup_translations completed", "TranslationManagerGTK4")
            return result

    def _get_target_language(self) -> str:
        """Determine target language from config and system locale"""
        with logger.performance.operation_context("get_target_language", "TranslationManagerGTK4"):
            # Get system locale as fallback
            system_language = self._get_system_language()
            logger.debug(f"System language detected: {system_language}", "TranslationManagerGTK4")

            # Try to get language from AppSettings first
            try:
                from domain.app_settings import AppSettings

                with logger.performance.operation_context("app_settings_instance", "TranslationManagerGTK4"):
                    app_settings = AppSettings.get_instance()
                    logger.debug("AppSettings.get_instance() completed", "TranslationManagerGTK4")

                with logger.performance.operation_context("get_language", "TranslationManagerGTK4"):
                    language = app_settings.get_language()
                    logger.debug(
                        f"AppSettings.get_language() returned: {language}",
                        "TranslationManagerGTK4",
                    )

                logger.debug(
                    f"_get_target_language() final target: {language}",
                    "TranslationManagerGTK4",
                )
                return language
            except Exception as e:
                logger.debug(
                    f"Could not get language from AppSettings: {e}",
                    "TranslationManagerGTK4",
                )

            # Fallback to system language
            logger.debug(
                f"AppSettings failed, falling back to system language: {system_language}",
                "TranslationManagerGTK4",
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
        self.translatable_menus.clear()
        if hasattr(self, "state_storage"):
            self.state_storage.clear()
        if hasattr(self, "_scanned_builders"):
            self._scanned_builders.clear()

    def print_discovered_widgets(self):
        """Debug method to print all discovered translatable widgets"""
        logger.debug("Discovered translatable widgets:", "TranslationManagerGTK4")
        for widget_info in self.translatable_widgets:
            widget_id = widget_info.get("widget_id", "Unknown")
            widget_type = type(widget_info["widget"]).__name__
            translation_key = widget_info["translation_key"]
            property_name = widget_info["property_name"]
            logger.debug(
                f"  - {widget_id} ({widget_type}): '{translation_key}' -> {property_name}",
                "TranslationManagerGTK4",
            )
