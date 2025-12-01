#!/usr/bin/env python3
"""
Translation Manager Factory

Provides factory functions to create the appropriate TranslationManager
implementation based on GTK version requirements and auto-detection.
"""

# fmt: off
import sys
from typing import Optional, Set

from d_fake_seeder.lib.logger import logger

from .base import TranslationManagerBase

# fmt: on


def detect_gtk_version() -> str:
    """
    Detect which GTK version is already loaded or should be used

    Returns:
        "3" for GTK3, "4" for GTK4
    """
    try:
        # Check if GTK is already loaded
        if "gi.repository.Gtk" in sys.modules:
            gtk_module = sys.modules["gi.repository.Gtk"]

            # Try to determine version from module attributes
            if hasattr(gtk_module, "_version"):
                version_str = str(gtk_module._version)
                if "3." in version_str:
                    return "3"
                elif "4." in version_str:
                    return "4"

            # Alternative detection method - check for GTK4-specific features
            if hasattr(gtk_module, "Application") and hasattr(gtk_module.Application, "get_default"):
                # GTK4 has different API signatures
                try:
                    # This is a GTK4-specific check
                    if hasattr(gtk_module, "CssProvider") and hasattr(gtk_module.CssProvider, "load_from_data"):
                        return "4"
                except Exception:
                    pass

            # If we can't determine, check for GTK3-specific features
            if hasattr(gtk_module, "main"):
                return "3"
            else:
                return "4"

        # No GTK loaded - default to GTK4 for new applications
        # We avoid trying to load GTK versions here to prevent conflicts
        logger.debug("No GTK version loaded, defaulting to GTK4", "TranslationManagerFactory")
        return "4"

    except Exception as e:
        logger.warning(
            f"Error detecting GTK version: {e}, defaulting to GTK4",
            "TranslationManagerFactory",
        )
        return "4"


def create_translation_manager(
    gtk_version: Optional[str] = None,
    auto_detect: bool = True,
    domain: str = "messages",
    localedir: Optional[str] = None,
    supported_languages: Optional[Set[str]] = None,
    fallback_language: str = "en",
    **kwargs,
) -> TranslationManagerBase:
    """
    Factory function to create the appropriate TranslationManager implementation

    Args:
        gtk_version: Specific GTK version to use ("3" or "4"). If None, auto-detect.
        auto_detect: Whether to auto-detect GTK version (default: True)
        domain: Translation domain name (default: "messages")
        localedir: Directory containing translation files
        supported_languages: Set of supported language codes
        fallback_language: Fallback language when others fail (default: "en")
        **kwargs: Additional arguments passed to the implementation

    Returns:
        TranslationManagerBase: The appropriate implementation instance

    Raises:
        ValueError: If unsupported GTK version is specified
        ImportError: If required GTK version is not available
    """
    # Determine GTK version to use
    if gtk_version is None and auto_detect:
        detected_version = detect_gtk_version()
        logger.debug(
            f"Auto-detected GTK version: {detected_version}",
            "TranslationManagerFactory",
        )
        gtk_version = detected_version
    elif gtk_version is None:
        gtk_version = "4"  # Default to GTK4

    # Validate GTK version
    if gtk_version not in ["3", "4"]:
        raise ValueError(f"Unsupported GTK version: {gtk_version}. Must be '3' or '4'.")

    # Import and create the appropriate implementation
    try:
        if gtk_version == "3":
            from .gtk3_implementation import TranslationManagerGTK3

            logger.debug("Creating GTK3 TranslationManager", "TranslationManagerFactory")
            return TranslationManagerGTK3(
                domain=domain,
                localedir=localedir,
                supported_languages=supported_languages,
                fallback_language=fallback_language,
                **kwargs,
            )
        else:  # GTK4
            from .gtk4_implementation import TranslationManagerGTK4

            logger.debug("Creating GTK4 TranslationManager", "TranslationManagerFactory")
            return TranslationManagerGTK4(
                domain=domain,
                localedir=localedir,
                supported_languages=supported_languages,
                fallback_language=fallback_language,
                **kwargs,
            )

    except ImportError as e:
        logger.error(
            f"Failed to import GTK{gtk_version} implementation: {e}",
            "TranslationManagerFactory",
        )

        # Check if the error is due to GTK version conflict
        error_msg = str(e)
        if "already loaded" in error_msg:
            # Don't try fallback if there's a version conflict - this means GTK is already loaded
            logger.error(
                f"GTK version conflict detected - cannot load GTK{gtk_version} implementation",
                "TranslationManagerFactory",
            )
            raise ImportError(f"GTK{gtk_version} implementation cannot be loaded due to GTK version conflict: {e}")

        # Try fallback to the other version only if no version conflict
        fallback_version = "4" if gtk_version == "3" else "3"
        logger.warning(f"Attempting fallback to GTK{fallback_version}", "TranslationManagerFactory")

        try:
            if fallback_version == "3":
                from .gtk3_implementation import TranslationManagerGTK3

                return TranslationManagerGTK3(
                    domain=domain,
                    localedir=localedir,
                    supported_languages=supported_languages,
                    fallback_language=fallback_language,
                    **kwargs,
                )
            else:
                from .gtk4_implementation import TranslationManagerGTK4

                return TranslationManagerGTK4(
                    domain=domain,
                    localedir=localedir,
                    supported_languages=supported_languages,
                    fallback_language=fallback_language,
                    **kwargs,
                )
        except ImportError as fallback_error:
            logger.error(
                f"Fallback to GTK{fallback_version} also failed: {fallback_error}",
                "TranslationManagerFactory",
            )
            raise ImportError(f"Neither GTK{gtk_version} nor GTK{fallback_version} implementation available")


def create_gtk3_translation_manager(
    domain: str = "messages",
    localedir: Optional[str] = None,
    supported_languages: Optional[Set[str]] = None,
    fallback_language: str = "en",
    **kwargs,
) -> TranslationManagerBase:
    """
    Convenience function to create a GTK3 TranslationManager

    This is useful when you explicitly need GTK3 compatibility,
    such as for tray applications using AppIndicator3.
    """
    try:
        from .gtk3_implementation import TranslationManagerGTK3

        logger.debug("Creating GTK3 TranslationManager directly", "TranslationManagerFactory")
        return TranslationManagerGTK3(
            domain=domain,
            localedir=localedir,
            supported_languages=supported_languages,
            fallback_language=fallback_language,
            **kwargs,
        )
    except ImportError as e:
        logger.error(
            f"Failed to import GTK3 implementation directly: {e}",
            "TranslationManagerFactory",
        )
        raise ImportError(f"GTK3 implementation not available: {e}")


def create_gtk4_translation_manager(
    domain: str = "messages",
    localedir: Optional[str] = None,
    supported_languages: Optional[Set[str]] = None,
    fallback_language: str = "en",
    **kwargs,
) -> TranslationManagerBase:
    """
    Convenience function to create a GTK4 TranslationManager

    This is the preferred choice for modern GTK applications.
    """
    try:
        from .gtk4_implementation import TranslationManagerGTK4

        logger.debug("Creating GTK4 TranslationManager directly", "TranslationManagerFactory")
        return TranslationManagerGTK4(
            domain=domain,
            localedir=localedir,
            supported_languages=supported_languages,
            fallback_language=fallback_language,
            **kwargs,
        )
    except ImportError as e:
        logger.error(
            f"Failed to import GTK4 implementation directly: {e}",
            "TranslationManagerFactory",
        )
        raise ImportError(f"GTK4 implementation not available: {e}")


def get_available_gtk_versions() -> Set[str]:
    """
    Check which GTK versions are available on the system

    This function avoids loading GTK to prevent version conflicts.

    Returns:
        Set of available GTK versions ("3", "4")
    """
    available_versions = set()

    try:
        # Check if GTK is already loaded and detect its version
        if "gi.repository.Gtk" in sys.modules:
            gtk_module = sys.modules["gi.repository.Gtk"]
            if hasattr(gtk_module, "_version"):
                version_str = str(gtk_module._version)
                if "3." in version_str:
                    available_versions.add("3")
                elif "4." in version_str:
                    available_versions.add("4")
            else:
                # Use feature detection for loaded GTK
                if hasattr(gtk_module, "main"):
                    available_versions.add("3")
                else:
                    available_versions.add("4")
        else:
            # If no GTK is loaded, assume both are potentially available
            # In production, this would be determined by the specific environment
            # For safety, we don't try to load GTK versions here
            available_versions.add("3")
            available_versions.add("4")

    except ImportError:
        logger.warning("PyGObject not available", "TranslationManagerFactory")

    return available_versions


def validate_gtk_environment(gtk_version: str) -> bool:
    """
    Validate that the specified GTK version is available and working

    Args:
        gtk_version: GTK version to validate ("3" or "4")

    Returns:
        True if GTK version is available and working
    """
    # Validate version is supported before attempting to load GTK
    if gtk_version not in ["3", "4"]:
        logger.debug(
            f"Invalid GTK version: {gtk_version}. Must be '3' or '4'.",
            "TranslationManagerFactory",
        )
        return False

    try:
        import gi

        gi.require_version("Gtk", f"{gtk_version}.0")
        from gi.repository import Gtk

        # Try to create a simple widget to ensure GTK is working
        if gtk_version == "3":
            widget = Gtk.Label()
        else:  # GTK4
            widget = Gtk.Label()

        return widget is not None

    except Exception as e:
        logger.debug(f"GTK{gtk_version} validation failed: {e}", "TranslationManagerFactory")
        return False
