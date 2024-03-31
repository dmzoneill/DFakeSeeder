"""
RFC: https://wiki.theory.org/index.php/BitTorrentSpecification
"""

import random
import struct
import threading
import traceback
from time import sleep
from urllib.parse import urlparse

import lib.torrent.bencoding as bencoding
import lib.util.helpers as helpers
import requests
from lib.logger import logger
from lib.settings import Settings
from lib.view import View
from requests.exceptions import ProxyError
from urllib3.exceptions import MaxRetryError, ReadTimeoutError


class Seeder:
    tracker_semaphore = threading.Semaphore(
        Settings.get_instance().concurrent_http_connections
    )
    peer_clients = {}

    def __init__(self, torrent):
        logger.info("Seeder Startup", extra={"class_name": self.__class__.__name__})

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.torrent = torrent
        self.tracker_url = ""
        self.peer_id = "-DE13F0-" + helpers.random_id(12)
        self.download_key = helpers.random_id(12)
        self.port = random.randint(1025, 65535)
        self.info = {}
        self.active = False

    @staticmethod
    def recreate_semaphore(self):
        logger.info(
            "Seeder recreate_semaphore",
            extra={"class_name": self.__class__.__name__},
        )
        current_count = Seeder.tracker_semaphore._value

        if self.settings.concurrent_http_connections == current_count:
            return

        # Acquire all available permits from the current semaphore
        Seeder.tracker_semaphore.acquire(current_count)

        # Create a new semaphore with the desired count
        new_semaphore = threading.Semaphore(self.settings.concurrent_http_connections)

        # Release the acquired permits on the new semaphore
        new_semaphore.release(current_count)

        # Update the class variable with the new semaphore
        Seeder.tracker_semaphore = new_semaphore

    def load_peers(self):
        logger.info("Seeder load peers", extra={"class_name": self.__class__.__name__})
        try:
            self.tracker_semaphore.acquire()
            if hasattr(self.torrent, "announce") is False:
                self.tracker_semaphore.release()
                return

            self.tracker_url = self.torrent.announce
            parsed_url = urlparse(self.tracker_url)

            if parsed_url.scheme == "http" or parsed_url.scheme == "https":
                View.instance.notify("load_peers " + self.tracker_url)

                http_params = {
                    "info_hash": self.torrent.file_hash,
                    "peer_id": self.peer_id.encode("ascii"),
                    "port": self.port,
                    "uploaded": 0,
                    "downloaded": 0,
                    "left": self.torrent.total_size,
                    "event": "started",
                    "key": self.download_key,
                    "compact": 1,
                    "numwant": 200,
                    "supportcrypto": 1,
                    "no_peer_id": 1,
                }

                req = requests.get(
                    self.tracker_url,
                    params=http_params,
                    proxies=self.settings.proxies,
                    headers=self.settings.http_headers,
                    timeout=10,
                )

                data = bencoding.decode(req.content)
                if data is not None:
                    self.info = data
                    self.update_interval = self.info[b"interval"]
                    self.tracker_semaphore.release()
                    return True

                self.tracker_semaphore.release()
                return False
            else:
                View.instance.notify("Unsupported tracker scheme: " + parsed_url.scheme)
                print("Unsupported tracker scheme: " + parsed_url.scheme)
                self.tracker_semaphore.release()
                return True
        except ProxyError as perror:
            logger.info(
                "Proxy error: " + str(perror),
                extra={"class_name": self.__class__.__name__},
            )
            self.tracker_semaphore.release()
            return False
        except ReadTimeoutError as rerror:
            logger.info(
                "Read timeout error: " + str(rerror),
                extra={"class_name": self.__class__.__name__},
            )
            self.tracker_semaphore.release()
            return False
        except MaxRetryError as merror:
            logger.info(
                "Max retry error: " + str(merror),
                extra={"class_name": self.__class__.__name__},
            )
            self.tracker_semaphore.release()
            return False
        except OSError as oerror:
            logger.info(
                "Os error: " + str(oerror),
                extra={"class_name": self.__class__.__name__},
            )
            self.tracker_semaphore.release()
            return False
        except Exception as e:
            logger.info(
                "Seeder unknown error: " + str(e),
                extra={"class_name": self.__class__.__name__},
            )
            self.tracker_semaphore.release()
            return False

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        logger.info("Seeder upload", extra={"class_name": self.__class__.__name__})
        while True:
            try:
                if hasattr(self.torrent, "announce"):
                    if "udp://" in self.torrent.announce:
                        break
                    self.tracker_semaphore.acquire()
                    self.tracker_url = self.torrent.announce
                    http_params = {
                        "info_hash": self.torrent.file_hash,
                        "peer_id": self.peer_id.encode("ascii"),
                        "port": self.port,
                        "uploaded": uploaded_bytes,
                        "downloaded": downloaded_bytes,
                        "left": download_left,
                        "key": self.download_key,
                        "compact": 1,
                        "numwant": 0,
                        "supportcrypto": 1,
                        "no_peer_id": 1,
                    }
                    requests.get(
                        self.tracker_url,
                        params=http_params,
                        proxies=self.settings.proxies,
                        headers=self.settings.http_headers,
                        timeout=10,
                    )
                    break
                else:
                    break
            except BaseException:
                traceback.print_exc()
            finally:
                self.tracker_semaphore.release()
            sleep(0.5)

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
        logger.debug("Seeder get clients", extra={"class_name": self.__class__.__name__})
        return Seeder.peer_clients

    @property
    def seeders(self):
        # logger.debug(
        #     "Seeder get seeders",
        #     extra={"class_name": self.__class__.__name__}
        # )
        return self.info[b"complete"] if b"complete" in self.info else 0

    @property
    def tracker(self):
        # logger.debug(
        #     "Seeder get tracker",
        #     extra={"class_name": self.__class__.__name__}
        # )
        return self.tracker_url

    @property
    def leechers(self):
        logger.debug("Seeder get leechers", extra={"class_name": self.__class__.__name__})
        return self.info[b"incomplete"] if b"incomplete" in self.info else 0

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Seeder settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        if key == "concurrent_http_connections":
            Seeder.recreate_semaphore(self)

    def __str__(self):
        logger.info("Seeder __get__", extra={"class_name": self.__class__.__name__})
        result = "Peer ID: %s\n" % self.peer_id
        result += "Key: %s\n" % self.download_key
        result += "Port: %d\n" % self.port
        result += "Update tracker interval: %ds" % self.update_interval
        return result
