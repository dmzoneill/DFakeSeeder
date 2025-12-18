"""
Local Peer Discovery (LPD) Module.

Implements BEP-014 for discovering peers on the local network
via multicast announcements.
"""

from .discovery import LocalPeerDiscovery, get_lpd_manager

__all__ = ["LocalPeerDiscovery", "get_lpd_manager"]

