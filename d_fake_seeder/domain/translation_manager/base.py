#!/usr/bin/env python3
"""
Abstract Base Class for Translation Manager

Defines the interface that all TranslationManager implementations must follow,
allowing for GTK3 and GTK4 compatible versions while maintaining a consistent API.
"""

# fmt: off
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List

# fmt: on


class TranslationManagerBase(ABC):
    """
    Abstract base class for translation management systems

    This class defines the interface that all TranslationManager implementations
    must follow, ensuring compatibility across different GTK versions while
    maintaining a consistent API.
    """

    @abstractmethod
    def __init__(self, domain: str, localedir: str = "locale", **kwargs):
        """
        Initialize the translation manager

        Args:
            domain: Translation domain name (e.g., "dfakeseeder")
            localedir: Directory containing translation files
            **kwargs: Additional implementation-specific arguments
        """
        pass

    @abstractmethod
    def switch_language(self, language_code: str) -> str:
        """
        Switch to a different language

        Args:
            language_code: Language code (e.g., "en", "es", "fr")

        Returns:
            The actual language code that was set (may differ from requested)
        """
        pass

    @abstractmethod
    def get_translate_func(self) -> Callable[[str], str]:
        """
        Get the translation function for the current language

        Returns:
            Translation function that takes a string and returns translated version
        """
        pass

    @abstractmethod
    def get_current_language(self) -> str:
        """
        Get the currently active language code

        Returns:
            Current language code (e.g., "en", "es", "fr")
        """
        pass

    @abstractmethod
    def get_available_languages(self) -> List[str]:
        """
        Get list of available languages

        Returns:
            List of available language codes
        """
        pass

    @abstractmethod
    def register_translation_function(self, widget: Any, get_text_func: Callable[[], str]) -> None:
        """
        Register a translation function for automatic widget updates

        Args:
            widget: Widget object to be translated
            get_text_func: Function that returns the text to be translated
        """
        pass

    @abstractmethod
    def update_translations(self) -> None:
        """
        Update all registered translation functions

        This method should be called after language changes to update
        all widgets that have registered translation functions.
        """
        pass

    @abstractmethod
    def get_language_name(self, language_code: str) -> str:
        """
        Get the display name for a language code

        Args:
            language_code: Language code (e.g., "en")

        Returns:
            Human-readable language name (e.g., "English")
        """
        pass

    @abstractmethod
    def set_default_language(self, language_code: str) -> None:
        """
        Set the default fallback language

        Args:
            language_code: Language code to use as default
        """
        pass

    @abstractmethod
    def get_translation_coverage(self, language_code: str) -> Dict[str, Any]:
        """
        Get translation coverage information for a language

        Args:
            language_code: Language code to check

        Returns:
            Dictionary with coverage information (translated_count, total_count, etc.)
        """
        pass

    # Properties that implementations should provide
    @property
    @abstractmethod
    def domain(self) -> str:
        """Translation domain name"""
        pass

    @property
    @abstractmethod
    def localedir(self) -> str:
        """Locale directory path"""
        pass

    @property
    @abstractmethod
    def current_language(self) -> str:
        """Currently active language code"""
        pass

    @property
    @abstractmethod
    def gtk_version(self) -> str:
        """GTK version this implementation supports"""
        pass
