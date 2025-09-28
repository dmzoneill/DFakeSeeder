from time import sleep

import domain.torrent.bencoding as bencoding
import requests
from domain.app_settings import AppSettings
from domain.torrent.seeders.base_seeder import BaseSeeder
from lib.logger import logger
from view import View


class HTTPSeeder(BaseSeeder):
    def __init__(self, torrent):
        super().__init__(torrent)

        # Get configurable sleep interval
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.retry_sleep_interval = (
            ui_settings.get("error_sleep_interval_seconds", 5.0)
            / ui_settings.get("seeder_retry_interval_divisor", 2)
            / 10
        )  # Much smaller for HTTP retries

    def load_peers(self):
        logger.info("Seeder load peers", extra={"class_name": self.__class__.__name__})

        if self.shutdown_requested:
            logger.info("🛑 Shutdown requested, aborting load_peers", extra={"class_name": self.__class__.__name__})
            return False

        try:
            # Use timeout for semaphore acquisition
            if not self.get_tracker_semaphore().acquire(timeout=5.0):
                logger.warning(
                    "⏱️ Timeout acquiring tracker semaphore for load_peers",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            View.instance.notify("load_peers " + self.tracker_url)

            # Log torrent information
            logger.info(
                f"🔗 Connecting to HTTP tracker: {self.tracker_url}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.info(
                f"📁 Torrent: {self.torrent.name} " f"(Hash: {self.torrent.file_hash.hex()[:16]}...)",
                extra={"class_name": self.__class__.__name__},
            )
            logger.info(
                f"🆔 Peer ID: {self.peer_id}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.info(f"🔌 Port: {self.port}", extra={"class_name": self.__class__.__name__})

            req = self.make_http_request(download_left=self.torrent.total_size)

            # Log HTTP response details
            logger.info(
                f"📡 HTTP Response: {req.status_code} ({req.reason})",
                extra={"class_name": self.__class__.__name__},
            )
            logger.info(
                f"📊 Response size: {len(req.content)} bytes",
                extra={"class_name": self.__class__.__name__},
            )

            data = bencoding.decode(req.content)
            if data is not None:
                self.info = data

                # Log tracker response details
                logger.info(
                    "✅ Tracker response decoded successfully",
                    extra={"class_name": self.__class__.__name__},
                )
                response_keys = [k.decode() if isinstance(k, bytes) else k for k in data.keys()]
                logger.info(
                    f"🔑 Response keys: {response_keys}",
                    extra={"class_name": self.__class__.__name__},
                )

                # Log seeders/leechers info
                if b"complete" in data:
                    logger.info(
                        f"🌱 Seeders: {data[b'complete']}",
                        extra={"class_name": self.__class__.__name__},
                    )
                if b"incomplete" in data:
                    logger.info(
                        f"⬇️ Leechers: {data[b'incomplete']}",
                        extra={"class_name": self.__class__.__name__},
                    )
                if b"interval" in data:
                    logger.info(
                        f"⏱️ Update interval: {data[b'interval']} seconds",
                        extra={"class_name": self.__class__.__name__},
                    )

                # Log peer information
                if b"peers" in data:
                    peers_data = data[b"peers"]
                    if isinstance(peers_data, bytes):
                        peer_count = len(peers_data) // 6
                        logger.info(
                            f"👥 Found {peer_count} peers " f"(compact format, {len(peers_data)} bytes)",
                            extra={"class_name": self.__class__.__name__},
                        )
                    elif isinstance(peers_data, list):
                        logger.info(
                            f"👥 Found {len(peers_data)} peers (dictionary format)",
                            extra={"class_name": self.__class__.__name__},
                        )
                    else:
                        logger.warning(
                            f"❓ Unknown peers format: {type(peers_data)}",
                            extra={"class_name": self.__class__.__name__},
                        )
                else:
                    logger.warning(
                        "❌ No 'peers' key in tracker response",
                        extra={"class_name": self.__class__.__name__},
                    )

                # Log any failure reason
                if b"failure reason" in data:
                    logger.error(
                        f"💥 Tracker failure: {data[b'failure reason'].decode()}",
                        extra={"class_name": self.__class__.__name__},
                    )

                # Log warning message if present
                if b"warning message" in data:
                    logger.warning(
                        f"⚠️ Tracker warning: {data[b'warning message'].decode()}",
                        extra={"class_name": self.__class__.__name__},
                    )

                self.update_interval = self.info[b"interval"]
                self.get_tracker_semaphore().release()
                return True

            logger.error(
                "❌ Failed to decode tracker response",
                extra={"class_name": self.__class__.__name__},
            )
            self.get_tracker_semaphore().release()
            return False
        except Exception as e:
            self.set_random_announce_url()
            self.handle_exception(e, "Seeder unknown error in load_peers_http")
            return False

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        logger.info("Seeder upload", extra={"class_name": self.__class__.__name__})

        # Log upload attempt
        logger.info(
            f"📤 Announcing to tracker: {self.tracker_url}",
            extra={"class_name": self.__class__.__name__},
        )
        logger.info(
            f"📊 Upload stats - Up: {uploaded_bytes} bytes, "
            f"Down: {downloaded_bytes} bytes, Left: {download_left} bytes",
            extra={"class_name": self.__class__.__name__},
        )

        max_retries = 3  # Limit retries to prevent infinite loops
        retry_count = 0

        while retry_count < max_retries and not self.shutdown_requested:
            try:
                # Use timeout for semaphore acquisition
                if not self.get_tracker_semaphore().acquire(timeout=2.0):
                    logger.warning(
                        "⏱️ Timeout acquiring tracker semaphore",
                        extra={"class_name": self.__class__.__name__},
                    )
                    retry_count += 1
                    continue

                req = self.make_http_request(uploaded_bytes, downloaded_bytes, download_left, num_want=0)

                # Log successful announce
                logger.info(
                    f"✅ Announce successful: HTTP {req.status_code}",
                    extra={"class_name": self.__class__.__name__},
                )

                # Try to decode response for any additional info
                try:
                    data = bencoding.decode(req.content)
                    if data and b"interval" in data:
                        logger.info(
                            f"⏱️ Next announce in: {data[b'interval']} seconds",
                            extra={"class_name": self.__class__.__name__},
                        )
                except Exception:
                    pass  # Not all announce responses contain decodable data

                self.get_tracker_semaphore().release()
                return  # Success, exit the loop

            except BaseException as e:
                retry_count += 1
                if self.shutdown_requested:
                    logger.info(
                        "🛑 Shutdown requested, aborting HTTP announce",
                        extra={"class_name": self.__class__.__name__},
                    )
                    break

                logger.warning(
                    f"⚠️ Announce failed (attempt {retry_count}/{max_retries}): {str(e)}",
                    extra={"class_name": self.__class__.__name__},
                )

                if retry_count < max_retries:
                    self.set_random_announce_url()
                    logger.info(
                        f"🔄 Switched to tracker: {self.tracker_url}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Limit sleep time and check for shutdown
                    sleep_time = min(self.retry_sleep_interval, 1.0)
                    sleep(sleep_time)
            finally:
                try:
                    self.get_tracker_semaphore().release()
                except Exception:
                    pass  # Ignore if already released or error occurred

        if retry_count >= max_retries:
            logger.error(
                f"❌ HTTP announce failed after {max_retries} attempts",
                extra={"class_name": self.__class__.__name__},
            )

    def make_http_request(
        self,
        uploaded_bytes=0,
        downloaded_bytes=0,
        download_left=0,
        num_want=None,
    ):
        if num_want is None:
            app_settings = AppSettings.get_instance()
            num_want = app_settings.get("seeders", {}).get("peer_request_count", 200)
        http_params = {
            "info_hash": self.torrent.file_hash,
            "peer_id": self.peer_id.encode("ascii"),
            "port": self.port,
            "uploaded": uploaded_bytes,
            "downloaded": downloaded_bytes,
            "left": download_left,
            "key": self.download_key,
            "compact": 0,  # Request non-compact format to get peer IDs
            "numwant": num_want,
            "supportcrypto": 1,
            "no_peer_id": 0,  # Request peer IDs for client identification
        }

        if download_left == 0:
            http_params["event"] = "started"

        http_agent_headers = self.settings.http_headers
        http_agent_headers["User-Agent"] = self.settings.agents[self.settings.agent].split(",")[0]

        # Log request details
        logger.info(
            f"🌐 Making HTTP request to: {self.tracker_url}",
            extra={"class_name": self.__class__.__name__},
        )
        logger.info(
            f"🔧 User-Agent: {http_agent_headers['User-Agent']}",
            extra={"class_name": self.__class__.__name__},
        )
        event = http_params.get("event", "none")
        logger.info(
            f"📋 Request params: numwant={num_want}, event={event}",
            extra={"class_name": self.__class__.__name__},
        )

        req = requests.get(
            self.tracker_url,
            params=http_params,
            proxies=self.settings.proxies,
            headers=http_agent_headers,
            timeout=getattr(self.settings, "seeders", {}).get("http_timeout_seconds", 10),
        )

        return req
