"""
Language configuration loader for DFakeSeeder.

Provides functionality to load language configurations from JSON files
instead of hardcoded dictionaries.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


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
        # Fallback to hardcoded minimal set if config loading fails
        print(f"Warning: Could not load languages config ({e}), using fallback")
        return {
            "en": {"name": "English", "plural_forms": "nplurals=2; plural=n != 1;"},
            "es": {"name": "Spanish", "plural_forms": "nplurals=2; plural=n != 1;"},
            "fr": {"name": "French", "plural_forms": "nplurals=2; plural=n > 1;"},
        }


def get_language_display_names() -> Dict[str, str]:
    """
    Get language display names for UI dropdowns.

    Returns:
        Dictionary mapping language codes to display names
        Format: {"en": "English", "es": "Spanish", ...}
    """
    languages = get_supported_languages()
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
