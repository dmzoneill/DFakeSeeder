"""
Torrent details components package.

This package contains the refactored torrent details components, broken down
into focused, single-responsibility classes for better maintainability.
"""

# Base classes
# fmt: off
from .base_tab import BaseTorrentTab
from .details_tab import DetailsTab
from .files_tab import FilesTab

# Connection tabs
from .incoming_connections_tab import IncomingConnectionsTab
from .log_tab import LogTab
from .notebook import TorrentDetailsNotebook
from .options_tab import OptionsTab
from .outgoing_connections_tab import OutgoingConnectionsTab
from .peers_tab import PeersTab

# Tab-specific components
from .status_tab import StatusTab
from .tab_mixins import DataUpdateMixin, UIUtilityMixin
from .trackers_tab import TrackersTab

__all__ = [
    "TorrentDetailsNotebook",
    "StatusTab",
    "FilesTab",
    "DetailsTab",
    "OptionsTab",
    "PeersTab",
    "TrackersTab",
    "LogTab",
    "BaseTorrentTab",
    "DataUpdateMixin",
    "UIUtilityMixin",
    "IncomingConnectionsTab",
    "OutgoingConnectionsTab",
]

# fmt: on
