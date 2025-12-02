"""
RFC: https://wiki.theory.org/index.php/BitTorrentSpecification
"""

# isort: skip_file

# fmt: off
from urllib.parse import urlparse

import gi

gi.require_version("GLib", "2.0")

from gi.repository import GLib  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.domain.torrent.seeders.http_seeder import HTTPSeeder  # noqa: E402
from d_fake_seeder.domain.torrent.seeders.udp_seeder import UDPSeeder  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class Seeder:
    def __init__(self, torrent):
        logger.debug("Startup", extra={"class_name": self.__class__.__name__})
        self.ready = False
        self.seeder = None
        self.settings = AppSettings.get_instance()
        self.check_announce_attribute(torrent)

    def check_announce_attribute(self, torrent, attempts=3):
        if hasattr(torrent, "announce"):
            self.ready = True
            parsed_url = urlparse(torrent.announce)
            if parsed_url.scheme == "http" or parsed_url.scheme == "https":
                self.seeder = HTTPSeeder(torrent)
            elif parsed_url.scheme == "udp":
                self.seeder = UDPSeeder(torrent)
            else:
                logger.error(
                    f"Unsupported tracker scheme: {parsed_url.scheme}",
                    extra={"class_name": self.__class__.__name__},
                )
        else:
            if attempts > 0:
                # Use tickspeed-based retry interval (minimum 1 second)
                retry_interval = max(1, int(self.settings.tickspeed / 2))
                GLib.timeout_add_seconds(retry_interval, self.check_announce_attribute, torrent, attempts - 1)
            else:
                logger.error(
                    f"Problem with torrent after retries: {torrent.filepath}",
                    extra={"class_name": self.__class__.__name__},
                )

    def load_peers(self):
        if self.seeder:
            return self.seeder.load_peers()
        else:
            return False

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        if self.seeder:
            self.seeder.upload(uploaded_bytes, downloaded_bytes, download_left)
        else:
            return False

    @property
    def peers(self):
        return self.seeder.peers if self.seeder is not None else 0

    @property
    def clients(self):
        return self.seeder.clients if self.seeder is not None else 0

    @property
    def seeders(self):
        return self.seeder.seeders if self.seeder is not None else 0

    @property
    def tracker(self):
        return self.seeder.tracker if self.seeder is not None else ""

    @property
    def leechers(self):
        return self.seeder.leechers if self.seeder is not None else 0

    def get_peer_data(self, peer_address):
        """Get comprehensive peer data for a specific peer"""
        return self.seeder.get_peer_data(peer_address) if self.seeder is not None else {}

    def ready(self):
        return self.ready and self.seeder is not None

    def request_shutdown(self):
        """Request graceful shutdown of the seeder"""
        if self.seeder:
            self.seeder.request_shutdown()

    def handle_settings_changed(self, source, key, value):
        self.seeder.handle_settings_changed(source, key, value)

    def __str__(self):
        return str(self.seeder)
