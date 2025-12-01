#!/usr/bin/env python3
"""
Translation Manager Package

Provides unified translation management for both GTK3 and GTK4 applications.
The factory automatically detects the appropriate GTK version and creates
the compatible TranslationManager implementation.

Usage Examples:

    # Auto-detect GTK version and create appropriate manager
# fmt: off
    from domain.translation_manager import create_translation_manager
    tm = create_translation_manager(domain="dfakeseeder", localedir="d_fake_seeder/locale")

    # Explicitly create GTK4 manager (for main application)
    from domain.translation_manager import create_gtk4_translation_manager
    tm = create_gtk4_translation_manager(domain="dfakeseeder", localedir="d_fake_seeder/locale")

    # Explicitly create GTK3 manager (for tray application)
    from domain.translation_manager import create_gtk3_translation_manager
    tm = create_gtk3_translation_manager(domain="dfakeseeder", localedir="d_fake_seeder/locale")

    # Check available GTK versions
    from domain.translation_manager import get_available_gtk_versions
    from lib.logger import logger
    versions = get_available_gtk_versions()
    logger.debug(f"Available GTK versions: {versions}", extra={"class_name": "TranslationManager"})

    # Use the manager
    tm.switch_language("es")
    translate_func = tm.get_translate_func()
    translated_text = translate_func("Hello World")
"""

from .base import TranslationManagerBase
from .factory import (
    create_gtk3_translation_manager,
    create_gtk4_translation_manager,
    create_translation_manager,
    detect_gtk_version,
    get_available_gtk_versions,
    validate_gtk_environment,
)

# Export the main factory function and utilities
__all__ = [
    # Main factory function
    "create_translation_manager",
    # Convenience functions
    "create_gtk3_translation_manager",
    "create_gtk4_translation_manager",
    # Utility functions
    "detect_gtk_version",
    "get_available_gtk_versions",
    "validate_gtk_environment",
    # Base class (for type hints)
    "TranslationManagerBase",
]

# Backwards compatibility aliases
TranslationManager = create_translation_manager
GTK3TranslationManager = create_gtk3_translation_manager
GTK4TranslationManager = create_gtk4_translation_manager

# Version information
__version__ = "1.0.0"
__author__ = "DFakeSeeder Development Team"
__description__ = "Unified translation management for GTK3 and GTK4 applications"

# fmt: on
