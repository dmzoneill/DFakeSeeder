import random
import struct
import threading
from urllib.parse import urlparse

import lib.util.helpers as helpers
from lib.logger import logger
from lib.settings import Settings


class BaseSeeder:
    tracker_semaphore = threading.Semaphore(
        Settings.get_instance().concurrent_http_connections
    )
    peer_clients = {}

    # Common functionality goes here
    def __init__(self, torrent):
        logger.info("Seeder Startup", extra={"class_name": self.__class__.__name__})

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.torrent = torrent
        self.tracker_url = ""
        self.peer_id = self.settings.agents[self.settings.agent].split(",")[
            1
        ] + helpers.random_id(12)
        self.download_key = helpers.random_id(12)
        self.port = random.randint(1025, 65000)
        self.info = {}
        self.active = False

        self.tracker_url = self.torrent.announce
        self.parsed_url = urlparse(self.tracker_url)
        self.tracker_scheme = self.parsed_url.scheme
        if hasattr(self.torrent, "announce_list"):
            self.tracker_urls = [
                url
                for url in self.torrent.announce_list
                if urlparse(url).scheme == self.tracker_scheme
            ]
        self.tracker_hostname = self.parsed_url.hostname
        self.tracker_port = self.parsed_url.port

    def set_random_announce_url(self):
        if hasattr(self.torrent, "announce_list") and self.torrent.announce_list:
            same_schema_urls = [
                url
                for url in self.torrent.announce_list
                if urlparse(url).scheme == self.tracker_scheme
            ]
            if same_schema_urls:
                random_url = random.choice(same_schema_urls)
                self.tracker_url = random_url
                self.parsed_url = urlparse(self.tracker_url)
                self.tracker_scheme = self.parsed_url.scheme
                self.tracker_hostname = self.parsed_url.hostname
                self.tracker_port = self.parsed_url.port
        else:
            self.tracker_url = self.torrent.announce
            self.parsed_url = urlparse(self.tracker_url)
            self.tracker_scheme = self.parsed_url.scheme
            self.tracker_hostname = self.parsed_url.hostname
            self.tracker_port = self.parsed_url.port

    @staticmethod
    def recreate_semaphore(obj):
        logger.info(
            "Seeder recreate_semaphore",
            extra={"class_name": obj.__class__.__name__},
        )
        current_count = BaseSeeder.tracker_semaphore._value

        if obj.settings.concurrent_http_connections == current_count:
            return

        # Acquire all available permits from the current semaphore
        BaseSeeder.tracker_semaphore.acquire(current_count)

        # Create a new semaphore with the desired count
        new_semaphore = threading.Semaphore(obj.settings.concurrent_http_connections)

        # Release the acquired permits on the new semaphore
        new_semaphore.release(current_count)

        # Update the class variable with the new semaphore
        BaseSeeder.tracker_semaphore = new_semaphore

    def handle_exception(self, e, message):
        logger.info(
            f"{message}: {str(e)}",
            extra={"class_name": self.__class__.__name__},
        )
        self.tracker_semaphore.release()

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Seeder settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        if key == "concurrent_http_connections":
            BaseSeeder.recreate_semaphore(self)

    def generate_transaction_id(self):
        return random.randint(0, 255)

    def __str__(self):
        logger.info("Seeder __get__", extra={"class_name": self.__class__.__name__})
        result = "Peer ID: %s\n" % self.peer_id
        result += "Key: %s\n" % self.download_key
        result += "Port: %d\n" % self.port
        result += "Update tracker interval: %ds" % self.update_interval
        return result

    @property
    def peers(self):
        logger.info("Seeder get peers", extra={"class_name": self.__class__.__name__})
        result = []
        if b"peers" not in self.info:
            return result
        peers = self.info[b"peers"]
        for i in range(len(peers) // 6):
            ip = peers[i : i + 4]  # noqa: E203
            ip = ".".join("%d" % x for x in ip)
            port = peers[i + 4 : i + 6]  # noqa: E203
            port = struct.unpack(">H", port)[0]
            result.append("%s:%d" % (ip, port))

        return result

    @property
    def clients(self):
        logger.debug(
            "Seeder get clients", extra={"class_name": self.__class__.__name__}
        )
        return BaseSeeder.peer_clients

    @property
    def seeders(self):
        logger.debug(
            "Seeder get seeders", extra={"class_name": self.__class__.__name__}
        )
        return self.info[b"complete"] if b"complete" in self.info else 0

    @property
    def tracker(self):
        logger.debug(
            "Seeder get tracker", extra={"class_name": self.__class__.__name__}
        )
        return self.tracker_url

    @property
    def leechers(self):
        logger.debug(
            "Seeder get leechers", extra={"class_name": self.__class__.__name__}
        )
        return self.info[b"incomplete"] if b"incomplete" in self.info else 0
