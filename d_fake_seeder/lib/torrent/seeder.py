"""
RFC: https://wiki.theory.org/index.php/BitTorrentSpecification
"""

from urllib.parse import urlparse

from gi.repository import GLib
from lib.logger import logger
from lib.torrent.seeders.HTTPSeeder import HTTPSeeder
from lib.torrent.seeders.UDPSeeder import UDPSeeder


class Seeder:
    def __init__(self, torrent):
        logger.info("Seeder Startup", extra={"class_name": self.__class__.__name__})
        self.ready = False
        self.seeder = None
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
                print("Unsupported tracker scheme: " + parsed_url.scheme)
        else:
            if attempts > 0:
                GLib.timeout_add_seconds(
                    1, self.check_announce_attribute, torrent, attempts - 1
                )
            else:
                print("Problem with torrent: " + torrent.filepath)

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

    def ready(self):
        return self.ready and self.seeder is not None

    def handle_settings_changed(self, source, key, value):
        self.seeder.handle_settings_changed(source, key, value)

    def __str__(self):
        return str(self.seeder)
