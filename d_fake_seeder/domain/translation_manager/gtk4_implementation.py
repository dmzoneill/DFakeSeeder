"""
GTK4 Implementation of Translation Manager

This implementation provides full compatibility with GTK4 widgets and applications.
It includes all the advanced features like widget discovery, menu translation,
and automatic UI updates. Shared language/registry logic lives in ``common``.
"""

import os
from collections.abc import Callable
from typing import Any, ClassVar

from d_fake_seeder.lib.gi_gtk4 import Gtk
from d_fake_seeder.lib.logger import logger

from .common import LABEL, PLACEHOLDER, TITLE, TOOLTIP, TranslationManagerCommon, read_text_properties

# Widget types scanned for translatable text, checked in order (first match wins)
_SCAN_RULES: tuple[tuple[str, tuple[tuple[str, str], ...]], ...] = (
    ("Label", (LABEL,)),
    ("Button", (LABEL, TOOLTIP)),
    ("CheckButton", (LABEL, TOOLTIP)),
    ("Window", (TITLE,)),
    ("Dialog", (TITLE,)),
    ("MenuButton", (LABEL, TOOLTIP)),
    ("Entry", (PLACEHOLDER, TOOLTIP)),
    ("Scale", (TOOLTIP,)),
)

# Properties set through a dedicated setter; anything else goes through set_property()
_SETTERS = {
    "label": "set_label",
    "title": "set_title",
    "text": "set_text",
    "tooltip_text": "set_tooltip_text",
    "placeholder_text": "set_placeholder_text",
}


_INIT_OPTIONS = frozenset({"supported_languages", "config_file", "fallback_language"})


class TranslationManagerGTK4(TranslationManagerCommon):
    """
    GTK4 implementation of the TranslationManager

    This implementation provides complete translation management for GTK4 applications,
    including automatic widget discovery, menu translation, and runtime language switching.
    """

    LOG_TAG: ClassVar[str] = "TranslationManagerGTK4"
    GTK_VERSION: ClassVar[str] = "4"
    PERF_CONTEXTS: ClassVar[bool] = True
    REFRESH_MENUS_ON_SWITCH: ClassVar[bool] = True
    LOG_DUPLICATE_SKIPS: ClassVar[bool] = True
    TARGET_LANGUAGE_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (
        ImportError,
        AttributeError,
        TypeError,
        KeyError,
    )
    WIDGET_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (AttributeError, TypeError, ValueError)

    def __init__(self, domain: str = "messages", localedir: str | None = None, **options: Any) -> None:
        """Initialize the GTK4 translation manager

        Options: ``supported_languages`` (set of codes, auto-discovered if omitted),
        ``config_file`` (defaults to ./config.json) and ``fallback_language`` (default "en").
        """
        unknown = set(options) - _INIT_OPTIONS
        if unknown:
            raise TypeError(f"Unexpected TranslationManagerGTK4 option(s): {', '.join(sorted(unknown))}")
        super().__init__(
            domain,
            localedir,
            supported_languages=options.get("supported_languages"),
            fallback_language=options.get("fallback_language", "en"),
        )
        self.config_file: str = options.get("config_file") or os.path.join(os.getcwd(), "config.json")

    def register_translation_function(self, widget: Any, get_text_func: Callable[[], str]) -> None:
        """Register a translation function for automatic widget updates"""
        property_name = "title" if isinstance(widget, (Gtk.Window, Gtk.Dialog)) else "label"
        translation_key = get_text_func()
        widget_id = getattr(widget, "get_buildable_id", lambda: None)()
        self.register_widget(widget, translation_key, property_name, widget_id)

    def _is_widget_alive(self, widget: Any) -> bool:
        return bool(widget) and hasattr(widget, "get_visible")

    def _set_widget_property(self, widget: Any, property_name: str, value: str) -> None:
        """Set a property on a widget with appropriate method"""
        setter_name = _SETTERS.get(property_name)
        if setter_name is not None:
            if hasattr(widget, setter_name):
                getattr(widget, setter_name)(value)
            return
        try:
            widget.set_property(property_name, value)
        except (AttributeError, TypeError, ValueError) as e:
            logger.warning(f"Warning: Could not set property '{property_name}': {e}")

    def get_language_name(self, language_code: str) -> str:
        """Get the display name for a language code"""
        try:
            from lib.util.language_config import get_language_display_names

            language_names: dict[str, str] = get_language_display_names()
            return language_names.get(language_code, language_code.upper())
        except (ImportError, KeyError, AttributeError, TypeError) as e:
            logger.trace(f"Could not load language names from config: {e}", self.LOG_TAG)
            return language_code.upper()

    def _is_scannable(self, obj: Any) -> bool:
        return isinstance(obj, Gtk.Widget)

    def _get_widget_id(self, widget: Any, builder: Any) -> str | None:
        """Try to find the ID of a widget from the builder."""
        if hasattr(widget, "get_buildable_id"):
            buildable_id: str | None = widget.get_buildable_id()
            return buildable_id
        for obj in builder.get_objects():
            if obj is widget and hasattr(obj, "get_name"):
                name: str | None = obj.get_name()
                return name
        return None

    def _translatable_properties(self, widget: Any) -> list[tuple[str, str]]:
        """Translatable (property, text) pairs, chosen by the widget's GTK type."""
        for type_name, properties in _SCAN_RULES:
            if isinstance(widget, getattr(Gtk, type_name)):
                return read_text_properties(widget, properties)
        # Any other widget: only its tooltip
        return read_text_properties(widget, (TOOLTIP,))

    def register_menu(self, menu: Any, menu_items: list[dict[str, str]], popover: Any = None) -> None:
        """Register a Gio.Menu (optionally shown by a Gtk.PopoverMenu) for translation updates"""
        if any(existing["menu"] is menu for existing in self.translatable_menus):
            return
        self.translatable_menus.append({"menu": menu, "items": menu_items, "popover": popover})

    def refresh_menu_translations(self) -> None:
        """Recreate all registered menus with translated text"""
        for menu_info in self.translatable_menus:
            try:
                self._recreate_menu(menu_info)
            except (AttributeError, TypeError, KeyError) as e:
                logger.warning(f"Warning: Could not refresh menu translations: {e}")

    def _recreate_menu(self, menu_info: dict[str, Any]) -> None:
        """Recreate a menu with translated text"""
        menu = menu_info["menu"]
        menu.remove_all()
        for item in menu_info["items"]:
            menu.append(self.translate_func(item["key"]), item["action"])
        popover = menu_info.get("popover")
        if popover:
            popover.set_menu_model(menu)
