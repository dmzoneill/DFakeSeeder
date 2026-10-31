"""
Shared implementation for the GTK 3 and GTK 4 translation managers.

Both managers keep identical language discovery/switching logic and the same widget
registry; only widget introspection, property setting and menu rebuilding differ per
GTK version. Those parts stay in ``gtk3_implementation`` / ``gtk4_implementation``,
which configure the shared behaviour here through class variables and small hooks.
"""

import gettext
import locale
import os
import re
import time
from collections.abc import Callable
from contextlib import AbstractContextManager, nullcontext
from dataclasses import dataclass, field
from typing import Any, ClassVar

from d_fake_seeder.lib.logger import logger

from .base import TranslationManagerBase

LANGUAGE_CODE_PATTERN = re.compile(r"^[a-z]{2,3}(_[A-Z]{2})?$")

# (property_name, getter_name) pairs read from a widget when scanning a builder
LABEL = ("label", "get_label")
TITLE = ("title", "get_title")
TOOLTIP = ("tooltip_text", "get_tooltip_text")
PLACEHOLDER = ("placeholder_text", "get_placeholder_text")


@dataclass
class LanguageConfig:
    """Language/locale configuration of a translation manager."""

    domain: str
    localedir: str
    fallback_language: str
    supported_languages: set[str] = field(default_factory=set)
    current_language: str | None = None


@dataclass
class WidgetRegistry:
    """Widgets, menus and per-widget state registered for translation."""

    widgets: list[dict[str, Any]] = field(default_factory=list)
    menus: list[dict[str, Any]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=dict)
    scanned_builders: set[int] = field(default_factory=set)
    updating: bool = False


def read_text_properties(widget: Any, properties: tuple[tuple[str, str], ...]) -> list[tuple[str, str]]:
    """Return ``(property_name, text)`` for each non-blank text property the widget exposes."""
    found = []
    for property_name, getter_name in properties:
        getter = getattr(widget, getter_name, None)
        if getter is None:
            continue
        text = getter()
        if text and text.strip():
            found.append((property_name, text))
    return found


class WidgetRegistrySupport:
    """Registration, refresh and bookkeeping of translatable widgets."""

    LOG_TAG: ClassVar[str] = "TranslationManager"
    LOG_DUPLICATE_SKIPS: ClassVar[bool] = False
    WIDGET_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (AttributeError, TypeError)

    _registry: WidgetRegistry
    translate_func: Callable[[str], str]

    def _is_widget_alive(self, widget: Any) -> bool:
        """Whether a registered widget can still be updated (per GTK version)."""
        return bool(widget)

    def _set_widget_property(self, widget: Any, property_name: str, value: str) -> None:
        """Set a property on a widget (GTK versions override with setter dispatch)."""
        widget.set_property(property_name, value)

    def _is_registered(self, widget: Any, property_name: str) -> bool:
        return any(
            entry["widget"] is widget and entry["property_name"] == property_name for entry in self._registry.widgets
        )

    def _append_widget(self, widget: Any, translation_key: str, property_name: str, widget_id: str | None) -> None:
        self._registry.widgets.append(
            {
                "widget": widget,
                "translation_key": translation_key,
                "property_name": property_name,
                "widget_id": widget_id,
                "original_text": translation_key,
            }
        )

    def register_widget(
        self, widget: Any, translation_key: str, property_name: str = "label", widget_id: str | None = None
    ) -> None:
        """Manually register a widget for translation"""
        if not self._is_registered(widget, property_name):
            self._append_widget(widget, translation_key, property_name, widget_id)

    def _register_properties(self, widget: Any, widget_id: str | None, properties: list[tuple[str, str]]) -> None:
        """Register each translatable ``(property_name, text)`` of a scanned widget."""
        for property_name, translation_key in properties:
            description = (
                f"{widget.__class__.__name__} '{widget_id or '(no id)'}' "
                f"property '{property_name}' with text: '{translation_key}'"
            )
            if not self._is_registered(widget, property_name):
                self._append_widget(widget, translation_key, property_name, widget_id)
                logger.trace(f"Registered {description}", self.LOG_TAG)
            elif self.LOG_DUPLICATE_SKIPS:
                logger.trace(f"Skipped duplicate {description}", self.LOG_TAG)

    def _builder_objects(self, builder: Any) -> list[Any] | None:
        """All objects of a builder, or None if they cannot be read."""
        return list(builder.get_objects())

    def _is_scannable(self, obj: Any) -> bool:
        """Whether a builder object is a widget worth scanning (per GTK version)."""
        return hasattr(obj, "get_visible")

    def _get_widget_id(self, widget: Any, builder: Any) -> str | None:
        """ID of a widget from the builder (GTK versions override with fallbacks)."""
        buildable_id: str | None = getattr(widget, "get_buildable_id", lambda: None)()
        return buildable_id

    def _translatable_properties(self, widget: Any) -> list[tuple[str, str]]:
        """Translatable ``(property_name, text)`` pairs of a widget (GTK versions override by type)."""
        return read_text_properties(widget, (TOOLTIP,))

    def refresh_menu_translations(self) -> None:
        """Recreate registered menus with translated text (GTK versions override)."""

    def _check_and_register_widget(self, widget: Any, widget_id: str | None) -> None:
        """Check if a widget should be registered for translation and register it."""
        self._register_properties(widget, widget_id, self._translatable_properties(widget))

    def scan_builder_widgets(self, builder: Any) -> None:
        """Scan all widgets of a builder and register those carrying translatable text."""
        builder_id = id(builder)
        if builder_id in self._registry.scanned_builders:
            logger.trace(f"Skipping scan_builder_widgets - builder {builder_id} already scanned", self.LOG_TAG)
            return

        objects = self._builder_objects(builder)
        if objects is None:
            return
        logger.trace(f"Getting {len(objects)} objects from builder {builder_id}", self.LOG_TAG)

        self._registry.scanned_builders.add(builder_id)
        widgets_before = len(self._registry.widgets)
        for obj in objects:
            if self._is_scannable(obj):
                self._check_and_register_widget(obj, self._get_widget_id(obj, builder))

        widgets_after = len(self._registry.widgets)
        logger.trace(
            f"Registered {widgets_after - widgets_before} new widgets (total: {widgets_after})",
            self.LOG_TAG,
        )

    def update_translations(self) -> None:
        """Update all registered translation functions"""
        self._refresh_translations_immediate()

    def refresh_all_translations(self) -> None:
        """Refresh translations for all registered widgets immediately"""
        self._refresh_translations_immediate()

    def _refresh_translations_immediate(self) -> None:
        """Update all widget translations immediately"""
        if self._registry.updating:
            return
        self._registry.updating = True
        try:
            for widget_info in self._registry.widgets:
                widget = widget_info["widget"]
                property_name = widget_info["property_name"]
                if not self._is_widget_alive(widget):
                    continue
                try:
                    translated_text = self.translate_func(widget_info["translation_key"])
                    self._set_widget_property(widget, property_name, translated_text)
                except self.WIDGET_ERRORS as e:
                    logger.warning(f"Warning: Could not translate widget property {property_name}: {e}")
        finally:
            self._registry.updating = False

    def set_widget_state(self, widget_id: str, key: str, value: Any) -> None:
        """Store state for a widget (e.g., whether button was clicked)"""
        self._registry.state.setdefault(widget_id, {})[key] = value

    def get_widget_state(self, widget_id: str, key: str, default: Any = None) -> Any:
        """Retrieve stored state for a widget"""
        return self._registry.state.get(widget_id, {}).get(key, default)

    def update_translation_key(self, widget_id: str, new_key: str) -> None:
        """Update the translation key for a specific widget"""
        for widget_info in self._registry.widgets:
            if widget_info.get("widget_id") == widget_id:
                widget_info["translation_key"] = new_key
                break

    def get_translatable_widgets(self) -> list[dict[str, Any]]:
        """Get list of all registered translatable widgets"""
        return self._registry.widgets.copy()

    def clear_registrations(self) -> None:
        """Clear all registered widgets and menus"""
        self._registry.widgets.clear()
        self._registry.menus.clear()
        self._registry.state.clear()
        self._registry.scanned_builders.clear()

    def print_discovered_widgets(self) -> None:
        """Debug method to print all discovered translatable widgets"""
        logger.trace("Discovered translatable widgets:", self.LOG_TAG)
        for widget_info in self._registry.widgets:
            widget_id = widget_info.get("widget_id", "Unknown")
            widget_type = type(widget_info["widget"]).__name__
            key, property_name = widget_info["translation_key"], widget_info["property_name"]
            logger.trace(f"  - {widget_id} ({widget_type}): '{key}' -> {property_name}", self.LOG_TAG)


class LanguageSupport(WidgetRegistrySupport):
    """Locale discovery, language switching and target-language resolution."""

    LOG_TAG: ClassVar[str] = "TranslationManager"
    PERF_CONTEXTS: ClassVar[bool] = False
    REFRESH_MENUS_ON_SWITCH: ClassVar[bool] = False
    TARGET_LANGUAGE_ERRORS: ClassVar[tuple[type[BaseException], ...]] = (ImportError, AttributeError)

    _config: LanguageConfig
    _registry: WidgetRegistry
    translate_func: Callable[[str], str]

    def _perf(self, name: str) -> AbstractContextManager[Any]:
        """Performance context (GTK 4) or a no-op context (GTK 3)."""
        if self.PERF_CONTEXTS:
            context: AbstractContextManager[Any] = logger.performance.operation_context(name, self.LOG_TAG)
            return context
        return nullcontext()

    def _discover_supported_languages(self) -> set[str]:
        """Dynamically discover supported languages from the locale directory"""
        localedir = self._config.localedir
        logger.trace(f"Starting language discovery in {localedir}", self.LOG_TAG)
        start_time = time.time()
        discovered_languages = {self._config.fallback_language}
        try:
            if os.path.exists(localedir):
                discovered_languages.update(
                    item for item in os.listdir(localedir) if self._has_translations(os.path.join(localedir, item))
                )
            discovery_time = (time.time() - start_time) * 1000
            logger.trace(
                f"Discovered languages: {sorted(discovered_languages)} (took {discovery_time:.1f}ms)",
                self.LOG_TAG,
            )
        except (OSError, ValueError, AttributeError):
            logger.warning("Warning: Could not discover languages", self.LOG_TAG)
        return discovered_languages

    def _has_translations(self, lang_dir: str) -> bool:
        """True if ``lang_dir`` is named like a language code and holds at least one .mo file."""
        if not (os.path.isdir(lang_dir) and self._is_valid_language_code(os.path.basename(lang_dir))):
            return False
        lc_messages_dir = os.path.join(lang_dir, "LC_MESSAGES")
        return os.path.exists(lc_messages_dir) and any(f.endswith(".mo") for f in os.listdir(lc_messages_dir))

    def _is_valid_language_code(self, code: str) -> bool:
        """Check if a string looks like a valid language code"""
        return bool(LANGUAGE_CODE_PATTERN.match(code))

    def _load_translation(self, language_code: str) -> tuple[gettext.NullTranslations, str]:
        """Translation object for ``language_code``; falls back to the fallback language if missing."""
        try:
            if language_code == self._config.fallback_language:
                logger.trace("Using NullTranslations for fallback language", self.LOG_TAG)
                return gettext.NullTranslations(), language_code
            trans = gettext.translation(self._config.domain, self._config.localedir, languages=[language_code])
            logger.trace(f"Loaded translation for '{language_code}'", self.LOG_TAG)
            return trans, language_code
        except FileNotFoundError:
            logger.trace(f"Warning: Translation file for '{language_code}' not found", self.LOG_TAG)
            return gettext.NullTranslations(), self._config.fallback_language

    def switch_language(self, language_code: str) -> str:
        """Switch to a specific language"""
        with self._perf("switch_language"):
            logger.trace(f"switch_language() called with: {language_code}", self.LOG_TAG)
            if self._config.current_language == language_code:
                logger.trace(f"Already using language '{language_code}' - skipping switch", self.LOG_TAG)
                return language_code

            if language_code not in self._config.supported_languages:
                logger.trace(
                    f"Warning: Unsupported language '{language_code}', falling back to system locale",
                    self.LOG_TAG,
                )
                language_code = self._get_system_language()

            trans, language_code = self._load_translation(language_code)
            trans.install()
            self.translate_func = trans.gettext
            self._config.current_language = language_code

            if self._registry.widgets:
                self._refresh_translations_immediate()
            if self.REFRESH_MENUS_ON_SWITCH and self._registry.menus:
                self.refresh_menu_translations()

            logger.info(f"Language switched to '{language_code}'", self.LOG_TAG)
            return language_code

    def _get_system_language(self) -> str:
        """Detect system language and map to supported languages"""
        try:
            try:
                system_locale = locale.getlocale()[0] or os.environ.get("LANG") or os.environ.get("LC_ALL") or ""
            except (ValueError, TypeError, AttributeError):
                system_locale = os.environ.get("LANG") or os.environ.get("LC_ALL") or ""

            if system_locale:
                lang_code = system_locale.split("_")[0].lower()
                if lang_code in self._config.supported_languages:
                    return lang_code
        except (ValueError, TypeError, AttributeError):
            logger.warning("Warning: Could not detect system locale", self.LOG_TAG)
        return self._config.fallback_language

    def get_translate_func(self) -> Callable[[str], str]:
        """Get the translation function for the current language"""
        return self.translate_func

    def get_current_language(self) -> str:
        """Get the currently active language code"""
        return self._config.current_language or self._config.fallback_language

    def get_available_languages(self) -> list[str]:
        """Get list of available languages"""
        return sorted(self._config.supported_languages)

    def get_supported_languages(self) -> set[str]:
        """Get the set of supported language codes"""
        return self._config.supported_languages.copy()

    def refresh_supported_languages(self) -> set[str]:
        """Re-scan the locale directory and update supported languages"""
        self._config.supported_languages = self._discover_supported_languages()
        return self._config.supported_languages.copy()

    def set_default_language(self, language_code: str) -> None:
        """Set the default fallback language"""
        self._config.fallback_language = language_code

    def get_translation_coverage(self, language_code: str) -> dict[str, Any]:
        """Get translation coverage information for a language"""
        try:
            if language_code == self._config.fallback_language:
                return {"translated_count": 100, "total_count": 100, "coverage_percent": 100}
            gettext.translation(self._config.domain, self._config.localedir, languages=[language_code])
            # Simplified: actual coverage would require parsing MO files
            return {"translated_count": 1, "total_count": 1, "coverage_percent": 100}
        except FileNotFoundError:
            return {"translated_count": 0, "total_count": 1, "coverage_percent": 0}

    def setup_translations(self, auto_detect: bool = True) -> str:
        """Set up translations with automatic language detection"""
        with self._perf("setup_translations"):
            logger.trace(f"setup_translations called with auto_detect={auto_detect}", self.LOG_TAG)
            if auto_detect:
                target_language = self._get_target_language()
                logger.trace(f"_get_target_language() returned: {target_language}", self.LOG_TAG)
            else:
                target_language = self._config.fallback_language
                logger.trace(f"Using fallback language: {target_language}", self.LOG_TAG)

            result = self.switch_language(target_language)
            logger.trace("setup_translations completed", self.LOG_TAG)
            return result

    def _get_target_language(self) -> str:
        """Determine target language from config and system locale"""
        with self._perf("get_target_language"):
            system_language = self._get_system_language()
            logger.trace(f"System language detected: {system_language}", self.LOG_TAG)
            try:
                from domain.app_settings import AppSettings

                with self._perf("app_settings_instance"):
                    app_settings = AppSettings.get_instance()
                    logger.trace("AppSettings.get_instance() completed", self.LOG_TAG)
                with self._perf("get_language"):
                    language: str = app_settings.get_language()
                    logger.trace(f"AppSettings.get_language() returned: {language}", self.LOG_TAG)
                logger.trace(f"_get_target_language() final target: {language}", self.LOG_TAG)
                return language
            except self.TARGET_LANGUAGE_ERRORS as e:
                logger.trace(f"Could not get language from AppSettings: {e}", self.LOG_TAG)

            logger.trace(f"AppSettings failed, falling back to system language: {system_language}", self.LOG_TAG)
            return system_language


class TranslationManagerCommon(LanguageSupport, TranslationManagerBase):
    """State shared by the GTK 3 and GTK 4 translation managers."""

    LOG_TAG: ClassVar[str] = "TranslationManager"
    GTK_VERSION: ClassVar[str] = ""

    def __init__(
        self,
        domain: str = "messages",
        localedir: str | None = None,
        supported_languages: set[str] | None = None,
        fallback_language: str = "en",
    ) -> None:
        self._config = LanguageConfig(
            domain=domain,
            localedir=localedir or os.path.join(os.getcwd(), "locale"),
            fallback_language=fallback_language,
        )
        self._registry = WidgetRegistry()
        self.translate_func = lambda text: text  # Default passthrough
        # Auto-discover supported languages if not provided
        self._config.supported_languages = (
            self._discover_supported_languages() if supported_languages is None else supported_languages
        )
        gettext.bindtextdomain(self._config.domain, self._config.localedir)
        gettext.textdomain(self._config.domain)

    def register_translation_function(self, widget: Any, get_text_func: Callable[[], str]) -> None:
        """Register a widget's label for translation (GTK versions override the property detection)."""
        widget_id = getattr(widget, "get_buildable_id", lambda: None)()
        self.register_widget(widget, get_text_func(), "label", widget_id)

    def get_language_name(self, language_code: str) -> str:
        """Display name for a language code (GTK versions override with real names)."""
        return language_code.upper()

    @property
    def domain(self) -> str:
        """Translation domain name"""
        return self._config.domain

    @property
    def localedir(self) -> str:
        """Locale directory path"""
        return self._config.localedir

    @property
    def current_language(self) -> str:
        """Currently active language code"""
        return self._config.current_language or self._config.fallback_language

    @property
    def gtk_version(self) -> str:
        """GTK version this implementation supports"""
        return self.GTK_VERSION

    @property
    def fallback_language(self) -> str:
        """Language used when no translation is available"""
        return self._config.fallback_language

    @fallback_language.setter
    def fallback_language(self, value: str) -> None:
        self._config.fallback_language = value

    @property
    def supported_languages(self) -> set[str]:
        """Language codes with translations available"""
        return self._config.supported_languages

    @supported_languages.setter
    def supported_languages(self, value: set[str]) -> None:
        self._config.supported_languages = value

    @property
    def translatable_widgets(self) -> list[dict[str, Any]]:
        """Registered widget entries (live list)"""
        return self._registry.widgets

    @property
    def translatable_menus(self) -> list[dict[str, Any]]:
        """Registered menu entries (live list)"""
        return self._registry.menus

    @property
    def state_storage(self) -> dict[str, Any]:
        """Per-widget stored state (live dict)"""
        return self._registry.state
