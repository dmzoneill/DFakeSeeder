import traceback
from time import sleep

import lib.torrent.bencoding as bencoding
import requests
from lib.logger import logger
from lib.torrent.seeders.BaseSeeder import BaseSeeder
from lib.view import View


class HTTPSeeder(BaseSeeder):
    def __init__(self, torrent):
        super().__init__(torrent)

    def load_peers(self):
        logger.info("Seeder load peers", extra={"class_name": self.__class__.__name__})
        try:
            self.tracker_semaphore.acquire()
            View.instance.notify("load_peers " + self.tracker_url)
            req = self.make_http_request(download_left=self.torrent.total_size)

            data = bencoding.decode(req.content)
            if data is not None:
                self.info = data
                self.update_interval = self.info[b"interval"]
                self.tracker_semaphore.release()
                return True

            self.tracker_semaphore.release()
            return False
        except Exception as e:
            self.set_random_announce_url()
            self.handle_exception(e, "Seeder unknown error in load_peers_http")
            return False

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        logger.info("Seeder upload", extra={"class_name": self.__class__.__name__})
        while True:
            try:
                self.tracker_semaphore.acquire()
                self.make_http_request(
                    uploaded_bytes, downloaded_bytes, download_left, num_want=0
                )
                break
            except BaseException:
                self.set_random_announce_url()
                traceback.print_exc()
            finally:
                self.tracker_semaphore.release()
            sleep(0.5)

    def make_http_request(
        self,
        uploaded_bytes=0,
        downloaded_bytes=0,
        download_left=0,
        num_want=200,
    ):
        http_params = {
            "info_hash": self.torrent.file_hash,
            "peer_id": self.peer_id.encode("ascii"),
            "port": self.port,
            "uploaded": uploaded_bytes,
            "downloaded": downloaded_bytes,
            "left": download_left,
            "key": self.download_key,
            "compact": 1,
            "numwant": num_want,
            "supportcrypto": 1,
            "no_peer_id": 1,
        }

        if download_left == 0:
            http_params["event"] = "started"

        http_agent_headers = self.settings.http_headers
        http_agent_headers["User-Agent"] = self.settings.agents[
            self.settings.agent
        ].split(",")[0]

        req = requests.get(
            self.tracker_url,
            params=http_params,
            proxies=self.settings.proxies,
            headers=http_agent_headers,
            timeout=10,
        )

        return req
