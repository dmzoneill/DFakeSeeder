"""
GTK3 Implementation of Translation Manager

This implementation provides compatibility with GTK3 widgets and applications,
specifically designed for use with system tray applications that require GTK3
due to AppIndicator3 dependencies. Widgets are handled by duck typing, so this
module needs no GTK import of its own (the tray process pins GTK 3 itself).
Shared language/registry logic lives in ``common``.
"""

from collections.abc import Callable
from typing import Any, ClassVar

from d_fake_seeder.lib.logger import logger

from .common import LABEL, PLACEHOLDER, TITLE, TOOLTIP, TranslationManagerCommon, read_text_properties

_GTK_ERRORS: tuple[type[BaseException], ...] = (RuntimeError, AttributeError, TypeError)

# Class-name fragments scanned for translatable text, checked in order (first match wins)
_SCAN_RULES: tuple[tuple[tuple[str, ...], tuple[tuple[str, str], ...]], ...] = (
    (("Label",), (LABEL,)),
    (("Button",), (LABEL, TOOLTIP)),
    (("CheckButton", "ToggleButton"), (LABEL, TOOLTIP)),
    (("Window", "Dialog"), (TITLE,)),
    (("MenuButton",), (LABEL, TOOLTIP)),
    (("Entry",), (PLACEHOLDER, TOOLTIP)),
)

_SETTERS = {
    "label": "set_label",
    "title": "set_title",
    "text": "set_text",
    "tooltip_text": "set_tooltip_text",
}

LANGUAGE_NAMES = {
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


class TranslationManagerGTK3(TranslationManagerCommon):
    """
    GTK3 implementation of the TranslationManager

    This implementation provides translation management for GTK3 applications,
    with a focus on system tray applications and AppIndicator3 compatibility.
    """

    LOG_TAG: ClassVar[str] = "TranslationManagerGTK3"
    GTK_VERSION: ClassVar[str] = "3"
    TARGET_LANGUAGE_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (ImportError, RuntimeError, AttributeError)
    WIDGET_ERRORS: ClassVar[tuple[type[BaseException], ...]] = _GTK_ERRORS

    def register_translation_function(self, widget: Any, get_text_func: Callable[[], str]) -> None:
        """Register a translation function for automatic widget updates"""
        translation_key = get_text_func()
        widget_id = getattr(widget, "get_name", lambda: None)()
        property_name = next(
            (name for name, setter in _SETTERS.items() if name != "tooltip_text" and hasattr(widget, setter)),
            "label",
        )
        self.register_widget(widget, translation_key, property_name, widget_id)

    def _is_widget_alive(self, widget: Any) -> bool:
        try:
            return bool(widget) and not (hasattr(widget, "get_visible") and not widget.get_realized())
        except (RuntimeError, AttributeError):
            return False

    def _set_widget_property(self, widget: Any, property_name: str, value: str) -> None:
        """Set a property on a widget with appropriate method"""
        try:
            setter_name = _SETTERS.get(property_name)
            if setter_name is not None and hasattr(widget, setter_name):
                getattr(widget, setter_name)(value)
            elif hasattr(widget, "set_property"):
                widget.set_property(property_name, value)
        except _GTK_ERRORS as e:
            logger.warning(f"Warning: Could not set property '{property_name}': {e}")

    def get_language_name(self, language_code: str) -> str:
        """Get the display name for a language code"""
        return LANGUAGE_NAMES.get(language_code, language_code.upper())

    def register_simple_text(self, text_key: str) -> str:
        """
        Simple text translation for menu items and labels

        This is a convenience method for tray applications that don't need
        complex widget management but need translation support.
        """
        return self.translate_func(text_key)

    def create_translated_menu_items(self, menu_items: list[dict[str, str]]) -> list[dict[str, str]]:
        """Create translated menu items (dicts with 'key' and 'action') for GTK3 menus"""
        return [{"text": self.translate_func(item["key"]), "action": item.get("action", "")} for item in menu_items]

    def get_language_display_names(self) -> dict[str, str]:
        """Get a mapping of language codes to display names"""
        return {lang: self.get_language_name(lang) for lang in self.supported_languages}

    def _builder_objects(self, builder: Any) -> list[Any] | None:
        try:
            return list(builder.get_objects())
        except (RuntimeError, AttributeError) as e:
            logger.trace(f"Could not get objects from builder: {e}", self.LOG_TAG)
            return None

    def _get_widget_id(self, widget: Any, builder: Any) -> str | None:
        """Try to find the ID of a widget from the builder (GTK3 compatible)"""
        try:
            for getter in ("get_buildable_id", "get_name"):
                if hasattr(widget, getter):
                    found: str | None = getattr(widget, getter)()
                    return found
        except (RuntimeError, AttributeError):
            pass
        try:
            for obj in builder.get_objects():
                if obj is widget and hasattr(obj, "get_name"):
                    name: str | None = obj.get_name()
                    return name
        except (RuntimeError, AttributeError):
            pass
        return None

    def _translatable_properties(self, widget: Any) -> list[tuple[str, str]]:
        """Translatable (property, text) pairs, chosen by class-name matching for GTK3 compatibility."""
        try:
            widget_type = widget.__class__.__name__
            for fragments, properties in _SCAN_RULES:
                if any(fragment in widget_type for fragment in fragments):
                    return read_text_properties(widget, properties)
            return read_text_properties(widget, (TOOLTIP,))
        except _GTK_ERRORS as e:
            logger.error(f"Error checking widget for translation: {e}", self.LOG_TAG)
            return []

    def register_menu(self, menu: Any, menu_items: list[dict[str, str]], popover: Any = None) -> None:
        """Register a menu for translation updates (GTK3 compatible)"""
        if any(existing["menu"] is menu for existing in self.translatable_menus):
            logger.trace("Skipping duplicate menu registration", self.LOG_TAG)
            return
        self.translatable_menus.append({"menu": menu, "items": menu_items, "popover": popover})
        logger.trace(f"Registered menu with {len(menu_items)} items for translation", self.LOG_TAG)

    def refresh_menu_translations(self) -> None:
        """Recreate all registered menus with translated text (GTK3 compatible)"""
        if not self.translatable_menus:
            logger.trace("No menus registered for translation", self.LOG_TAG)
            return
        logger.trace(f"Refreshing translations for {len(self.translatable_menus)} menus", self.LOG_TAG)
        for menu_info in self.translatable_menus:
            try:
                self._recreate_menu(menu_info)
            except _GTK_ERRORS as e:
                logger.trace(f"Warning: Could not refresh menu translations: {e}", self.LOG_TAG)

    def _recreate_menu(self, menu_info: dict[str, Any]) -> None:
        """Recreate a menu with translated text (GTK3 compatible)"""
        menu = menu_info["menu"]
        popover = menu_info.get("popover")
        try:
            if hasattr(menu, "remove_all"):
                menu.remove_all()
            for item in menu_info["items"]:
                translated_text = self.translate_func(item["key"])
                if hasattr(menu, "append"):
                    menu.append(translated_text, item["action"])
                logger.trace(
                    f"Menu item: '{item['key']}' -> '{translated_text}' (action: {item.get('action', 'none')})",
                    self.LOG_TAG,
                )
            if popover and hasattr(popover, "set_menu_model"):
                popover.set_menu_model(menu)
                logger.trace("Updated popover menu model", self.LOG_TAG)
        except _GTK_ERRORS as e:
            logger.trace(f"Could not recreate menu: {e}", self.LOG_TAG)
