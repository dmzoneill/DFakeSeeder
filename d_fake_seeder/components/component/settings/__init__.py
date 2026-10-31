"""
Settings dialog components package.

This package contains the refactored settings dialog components, broken down
into focused, single-responsibility classes for better maintainability.
"""

# fmt: off
from .advanced_tab import AdvancedTab

# Base classes
from .base_tab import BaseSettingsTab
from .bittorrent_tab import BitTorrentTab
from .connection_tab import ConnectionTab
from .dht_tab import DHTTab

# Tab-specific components
from .general_tab import GeneralTab
from .multi_tracker_tab import MultiTrackerTab
from .peer_protocol_tab import PeerProtocolTab
from .protocol_extensions_tab import ProtocolExtensionsTab
from .settings_dialog import SettingsDialog
from .settings_mixins import (
    KeyboardShortcutMixin,
    NotificationMixin,
    ValidationMixin,
)
from .simulation_tab import SimulationTab
from .speed_tab import SpeedTab
from .webui_tab import WebUITab

__all__ = [
    "AdvancedTab",
    "BaseSettingsTab",
    "BitTorrentTab",
    "ConnectionTab",
    "DHTTab",
    "GeneralTab",
    "KeyboardShortcutMixin",
    "MultiTrackerTab",
    "NotificationMixin",
    "PeerProtocolTab",
    "ProtocolExtensionsTab",
    "SettingsDialog",
    "SimulationTab",
    "SpeedTab",
    "ValidationMixin",
    "WebUITab",
]

# fmt: on
