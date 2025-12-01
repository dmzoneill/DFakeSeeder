"""
Language configuration loader for DFakeSeeder.

Provides functionality to load language configurations from JSON files
instead of hardcoded dictionaries.
"""

# fmt: off
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from lib.logger import logger
except ImportError:
    # Fallback for when imported from tools/ directory
    import logging

    logger = logging.getLogger(__name__)

# fmt: on


def get_languages_config_path() -> Path:
    """Get the path to the languages configuration file."""
    # Get the package directory
    package_dir = Path(__file__).parent.parent.parent
    config_dir = package_dir / "domain" / "config"
    return config_dir / "languages.json"


def load_languages_config() -> Dict[str, Any]:
    """
    Load language configurations from JSON file.

    Returns:
        Dictionary containing language configurations with metadata

    Raises:
        FileNotFoundError: If languages config file not found
        json.JSONDecodeError: If config file is invalid JSON
    """
    config_path = get_languages_config_path()

    if not config_path.exists():
        raise FileNotFoundError(f"Languages configuration file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in languages config: {e}", e.doc, e.pos)


def _discover_languages_from_locale() -> Dict[str, Dict[str, str]]:
    """
    Dynamically discover languages from the locale directory.

    Returns:
        Dictionary mapping language codes to language info with fallback names
    """
    languages = {}

    # Get locale directory
    package_dir = Path(__file__).parent.parent.parent
    locale_dir = package_dir / "components" / "locale"

    # Check if DFS_PATH environment variable is set (runtime)
    if "DFS_PATH" in os.environ:
        locale_dir = Path(os.environ["DFS_PATH"]) / "components" / "locale"

    logger.debug(f"Scanning locale directory: {locale_dir}")

    if locale_dir.exists() and locale_dir.is_dir():
        for item in os.listdir(locale_dir):
            lang_dir = locale_dir / item
            mo_file = lang_dir / "LC_MESSAGES" / "dfakeseeder.mo"

            if lang_dir.is_dir() and mo_file.exists():
                # Standard plural forms for most languages
                plural_forms = "nplurals=2; plural=n != 1;"

                # Language name fallback - uppercase language code
                lang_name = item.upper()

                languages[item] = {"name": lang_name, "plural_forms": plural_forms}
                logger.debug(f"Discovered language: {item} ({lang_name})")

    # Always ensure English is present as ultimate fallback
    if "en" not in languages:
        languages["en"] = {
            "name": "English",
            "plural_forms": "nplurals=2; plural=n != 1;",
        }
        logger.debug("Added English as fallback language")

    logger.info(f"Discovered {len(languages)} languages from locale directory")
    return languages


def get_supported_languages() -> Dict[str, Dict[str, str]]:
    """
    Get the languages dictionary in the format expected by translation tools.

    Returns:
        Dictionary mapping language codes to language info
        Format: {"en": {"name": "English", "plural_forms": "..."}, ...}
    """
    try:
        config = load_languages_config()
        return config.get("languages", {})
    except (FileNotFoundError, json.JSONDecodeError) as e:
        # Fallback to dynamic discovery from locale directory if config loading fails
        logger.warning(f"Could not load languages config ({e}), falling back to locale directory scan")
        return _discover_languages_from_locale()


def get_language_display_names(use_native_names: bool = True) -> Dict[str, str]:
    """
    Get language display names for UI dropdowns.

    Args:
        use_native_names: If True, use native language names (e.g., "Español"),
                         otherwise use English names (e.g., "Spanish")

    Returns:
        Dictionary mapping language codes to display names
        Format: {"en": "English", "es": "Español", ...}
    """
    languages = get_supported_languages()
    if use_native_names:
        return {code: info.get("native_name", info["name"]) for code, info in languages.items()}
    else:
        return {code: info["name"] for code, info in languages.items()}


def get_language_plural_forms(language_code: str) -> Optional[str]:
    """
    Get plural forms string for a specific language.

    Args:
        language_code: Language code (e.g., "en", "es")

    Returns:
        Plural forms string or None if language not found
    """
    languages = get_supported_languages()
    if language_code in languages:
        return languages[language_code].get("plural_forms")
    return None


def get_supported_language_codes() -> list:
    """
    Get list of supported language codes.

    Returns:
        Sorted list of language codes (e.g., ["ar", "de", "en", ...])
    """
    return sorted(get_supported_languages().keys())


def is_language_supported(language_code: str) -> bool:
    """
    Check if a language is supported.

    Args:
        language_code: Language code to check

    Returns:
        True if language is supported, False otherwise
    """
    return language_code in get_supported_languages()


def get_config_metadata() -> Dict[str, Any]:
    """
    Get metadata about the language configuration.

    Returns:
        Metadata dictionary with version, description, etc.
    """
    try:
        config = load_languages_config()
        return config.get("metadata", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {"version": "unknown", "description": "Fallback configuration"}
