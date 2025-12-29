# fmt: off
# isort: skip_file
"""
Inbuilt BitTorrent Tracker Module

This module provides a complete BitTorrent tracker implementation that can:
- Accept HTTP/UDP announce/scrape requests from external clients
- Track peers for torrents
- Integrate with DFakeSeeder's own seeders via LocalAnnouncer
"""

from d_fake_seeder.domain.tracker.peer_database import PeerDatabase
from d_fake_seeder.domain.tracker.torrent_registry import TorrentRegistry
from d_fake_seeder.domain.tracker.local_announcer import LocalAnnouncer
from d_fake_seeder.domain.tracker.tracker_server import TrackerServer
from d_fake_seeder.domain.tracker.udp_handler import UDPTrackerHandler

# fmt: on

__all__ = [
    "PeerDatabase",
    "TorrentRegistry",
    "LocalAnnouncer",
    "TrackerServer",
    "UDPTrackerHandler",
]
