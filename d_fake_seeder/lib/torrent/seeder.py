"""
RFC: https://wiki.theory.org/index.php/BitTorrentSpecification
"""

from urllib.parse import urlparse

from lib.logger import logger
from lib.torrent.seeders.HTTPSeeder import HTTPSeeder
from lib.torrent.seeders.UDPSeeder import UDPSeeder


class Seeder:

    def __init__(self, torrent):
        logger.info("Seeder Startup", extra={"class_name": self.__class__.__name__})
        parsed_url = urlparse(torrent.announce)

        if parsed_url.scheme == "http":
            self.seeder = HTTPSeeder(torrent)
        elif parsed_url.scheme == "udp":
            self.seeder = UDPSeeder(torrent)
        else:
            print("Unsupported tracker scheme: " + parsed_url.scheme)
            self.seeder = None

    def load_peers(self):
        if self.seeder:
            self.seeder.load_peers()

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        if self.seeder:
            self.seeder.upload(uploaded_bytes, downloaded_bytes, download_left)

    @property
    def peers(self):
        return self.seeder.peers

    @property
    def clients(self):
        return self.seeder.clients

    @property
    def seeders(self):
        return self.seeder.seeders

    @property
    def tracker(self):
        return self.seeder.tracker

    @property
    def leechers(self):
        return self.seeder.leechers

    def handle_settings_changed(self, source, key, value):
        self.seeder.handle_settings_changed(source, key, value)

    def __str__(self):
        return str(self.seeder)
