"""
Tab configuration loader for DFakeSeeder.
Provides functionality to load tab configurations from JSON files
instead of hardcoded class lists, enabling modular tab management.
"""

# fmt: off
import json
from pathlib import Path
from typing import Any, Dict, List, Type

from d_fake_seeder.lib.logger import logger

# fmt: on


def get_tabs_config_path() -> Path:
    """Get the path to the tabs configuration file."""
    # Get the package directory
    package_dir = Path(__file__).parent.parent.parent
    config_dir = package_dir / "domain" / "config"
    return config_dir / "tabs.json"


def load_tabs_config() -> Dict[str, Any]:
    """
    Load tab configurations from JSON file.
    Returns:
        Dictionary containing tab configurations with metadata
    Raises:
        FileNotFoundError: If tabs config file not found
        json.JSONDecodeError: If config file is invalid JSON
    """
    config_path = get_tabs_config_path()
    if not config_path.exists():
        raise FileNotFoundError(f"Tabs configuration file not found: {config_path}")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in tabs config: {e}", e.doc, e.pos)


def get_settings_tab_config() -> Dict[str, Any]:
    """
    Get settings tab configuration.
    Returns:
        Dictionary with settings tab configuration
    """
    try:
        config = load_tabs_config()
        return config.get("settings_tabs", {})
    except Exception:
        logger.debug("Warning: Could not load tabs config (...), using fallback", "UnknownClass")
        return {
            "enabled": True,
            "order": ["GeneralTab", "ConnectionTab", "AdvancedTab"],
            "optional": [],
            "required": ["GeneralTab", "ConnectionTab", "AdvancedTab"],
        }


def get_torrent_details_tab_config() -> Dict[str, Any]:
    """
    Get torrent details tab configuration.
    Returns:
        Dictionary with torrent details tab configuration
    """
    try:
        config = load_tabs_config()
        return config.get("torrent_details_tabs", {})
    except Exception:
        logger.debug("Warning: Could not load tabs config (...), using fallback", "UnknownClass")
        return {
            "enabled": True,
            "order": ["StatusTab", "FilesTab", "DetailsTab"],
            "essential": ["StatusTab"],
            "lazy_load": ["FilesTab", "DetailsTab"],
        }


def get_tab_features() -> Dict[str, Any]:
    """
    Get tab feature configuration.
    Returns:
        Dictionary with tab feature settings
    """
    try:
        config = load_tabs_config()
        return config.get("tab_features", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "lazy_loading": True,
            "background_initialization": True,
            "dynamic_tab_creation": False,
            "tab_caching": True,
            "essential_only_mode": False,
        }


def resolve_tab_classes(tab_names: List[str], module_mapping: Dict[str, Type]) -> List[Type]:
    """
    Resolve tab class names to actual class objects.
    Args:
        tab_names: List of tab class names from configuration
        module_mapping: Dictionary mapping class names to actual classes
    Returns:
        List of resolved tab classes
    Raises:
        KeyError: If a tab class name cannot be resolved
    """
    resolved_classes = []
    for tab_name in tab_names:
        if tab_name not in module_mapping:
            raise KeyError(f"Tab class '{tab_name}' not found in module mapping")
        resolved_classes.append(module_mapping[tab_name])
    return resolved_classes


def get_settings_tab_classes(module_mapping: Dict[str, Type]) -> List[Type]:
    """
    Get settings tab classes in configured order.
    Args:
        module_mapping: Dictionary mapping class names to actual classes
    Returns:
        List of tab classes in configured order
    """
    config = get_settings_tab_config()
    if not config.get("enabled", True):
        return []
    tab_names = config.get("order", [])
    return resolve_tab_classes(tab_names, module_mapping)


def get_torrent_details_tab_classes(module_mapping: Dict[str, Type]) -> List[Type]:
    """
    Get torrent details tab classes in configured order.
    Args:
        module_mapping: Dictionary mapping class names to actual classes
    Returns:
        List of tab classes in configured order
    """
    config = get_torrent_details_tab_config()
    if not config.get("enabled", True):
        return []
    tab_names = config.get("order", [])
    return resolve_tab_classes(tab_names, module_mapping)


def get_essential_tab_classes(module_mapping: Dict[str, Type]) -> List[Type]:
    """
    Get essential torrent details tab classes only.
    Args:
        module_mapping: Dictionary mapping class names to actual classes
    Returns:
        List of essential tab classes
    """
    config = get_torrent_details_tab_config()
    essential_names = config.get("essential", ["StatusTab"])
    return resolve_tab_classes(essential_names, module_mapping)


def get_lazy_load_tab_classes(module_mapping: Dict[str, Type]) -> List[Type]:
    """
    Get tab classes that should be lazy loaded.
    Args:
        module_mapping: Dictionary mapping class names to actual classes
    Returns:
        List of lazy-loadable tab classes
    """
    config = get_torrent_details_tab_config()
    lazy_names = config.get("lazy_load", [])
    return resolve_tab_classes(lazy_names, module_mapping)


def is_tab_enabled(tab_name: str, context: str = "settings") -> bool:
    """
    Check if a tab is enabled in configuration.
    Args:
        tab_name: Name of the tab class
        context: Context ("settings" or "torrent_details")
    Returns:
        True if tab is enabled, False otherwise
    """
    try:
        if context == "settings":
            config = get_settings_tab_config()
            return tab_name in config.get("order", [])
        elif context == "torrent_details":
            config = get_torrent_details_tab_config()
            return tab_name in config.get("order", [])
        return False
    except Exception:
        return True  # Default to enabled if config fails


def is_feature_enabled(feature_name: str) -> bool:
    """
    Check if a tab feature is enabled.
    Args:
        feature_name: Name of the feature
    Returns:
        True if feature is enabled, False otherwise
    """
    features = get_tab_features()
    return features.get(feature_name, True)


def get_config_metadata() -> Dict[str, Any]:
    """
    Get metadata about the tab configuration.
    Returns:
        Metadata dictionary with version, description, etc.
    """
    try:
        config = load_tabs_config()
        return config.get("metadata", {})
    except (FileNotFoundError, json.JSONDecodeError):
        return {"version": "unknown", "description": "Fallback configuration"}
