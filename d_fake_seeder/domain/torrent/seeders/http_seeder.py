# fmt: off
# isort: skip_file
import time
from time import sleep

import requests

import d_fake_seeder.domain.torrent.bencoding as bencoding
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.model.tracker import Tracker
from d_fake_seeder.domain.torrent.seeders.base_seeder import BaseSeeder
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import RetryConstants, TimeoutConstants
from d_fake_seeder.view import View

# fmt: on


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
        logger.debug("Seeder load peers", extra={"class_name": self.__class__.__name__})

        if self.shutdown_requested:
            logger.debug(
                "🛑 Shutdown requested, aborting load_peers",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            # Use timeout for semaphore acquisition
            if not self.get_tracker_semaphore().acquire(timeout=5.0):
                logger.debug(
                    "⏱️ Timeout acquiring tracker semaphore for load_peers",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Only notify if view instance still exists (may be None during shutdown)
            if View.instance is not None:
                View.instance.notify("load_peers " + self.tracker_url)

            # Mark tracker as announcing
            self._set_tracker_announcing()

            # Log torrent information
            logger.debug(
                f"🔗 Connecting to HTTP tracker: {self.tracker_url}",
                extra={"class_name": self.__class__.__name__},
            )

            request_start_time = time.time()
            logger.debug(
                f"📁 Torrent: {self.torrent.name} " f"(Hash: {self.torrent.file_hash.hex()[:16]}...)",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug(
                f"🆔 Peer ID: {self.peer_id}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug(f"🔌 Port: {self.port}", extra={"class_name": self.__class__.__name__})

            req = self.make_http_request(download_left=self.torrent.total_size)

            # Log the actual HTTP request URL
            logger.debug(
                f"🌐 FULL REQUEST URL: {req.url}",
                extra={"class_name": self.__class__.__name__},
            )

            # Log equivalent curl command for manual testing
            logger.debug(
                f"🔧 CURL COMMAND: curl -v '{req.url}'",
                extra={"class_name": self.__class__.__name__},
            )

            # Log HTTP response details
            logger.debug(
                f"📡 HTTP Response: {req.status_code} ({req.reason})",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug(
                f"📊 Response size: {len(req.content)} bytes",
                extra={"class_name": self.__class__.__name__},
            )

            # Log raw response content for debugging
            logger.debug(
                f"📄 Raw response (first 500 bytes): {req.content[:500]}",
                extra={"class_name": self.__class__.__name__},
            )

            # Calculate response time
            request_end_time = time.time()
            response_time = request_end_time - request_start_time

            data = bencoding.decode(req.content)
            if data is not None:
                self.info = data

                # Log tracker response details
                logger.debug(
                    "✅ Tracker response decoded successfully",
                    extra={"class_name": self.__class__.__name__},
                )
                response_keys = [k.decode() if isinstance(k, bytes) else k for k in data.keys()]
                logger.debug(
                    f"🔑 Response keys: {response_keys}",
                    extra={"class_name": self.__class__.__name__},
                )

                # Log complete decoded response for debugging
                logger.debug(
                    f"📦 FULL TRACKER RESPONSE DATA: {data}",
                    extra={"class_name": self.__class__.__name__},
                )

                # Update tracker model with successful response
                self._update_tracker_success(data, response_time)

                # Log seeders/leechers info
                if b"complete" in data:
                    logger.debug(
                        f"🌱 Seeders: {data[b'complete']}",
                        extra={"class_name": self.__class__.__name__},
                    )
                if b"incomplete" in data:
                    logger.debug(
                        f"⬇️ Leechers: {data[b'incomplete']}",
                        extra={"class_name": self.__class__.__name__},
                    )
                if b"interval" in data:
                    logger.debug(
                        f"⏱️ Update interval: {data[b'interval']} seconds",
                        extra={"class_name": self.__class__.__name__},
                    )

                # Log peer information
                if b"peers" in data:
                    peers_data = data[b"peers"]
                    if isinstance(peers_data, bytes):
                        peer_count = len(peers_data) // 6
                        logger.debug(
                            f"👥 Found {peer_count} peers " f"(compact format, {len(peers_data)} bytes)",
                            extra={"class_name": self.__class__.__name__},
                        )
                    elif isinstance(peers_data, list):
                        logger.debug(
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

                # Apply jitter to announce interval to prevent request storms
                base_interval = self.info[b"interval"]
                self.update_interval = self._apply_announce_jitter(base_interval)
                self.get_tracker_semaphore().release()
                return True

            logger.error(
                "❌ Failed to decode tracker response",
                extra={"class_name": self.__class__.__name__},
            )
            self.get_tracker_semaphore().release()
            return False
        except Exception as e:
            # Update tracker model with failure
            if "request_start_time" in locals():
                request_end_time = time.time()
                response_time = request_end_time - request_start_time
                self._update_tracker_failure(str(e), response_time)
            else:
                self._update_tracker_failure(str(e))

            self.set_random_announce_url()
            self.handle_exception(e, "Seeder unknown error in load_peers_http")
            return False

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        logger.debug("Seeder upload", extra={"class_name": self.__class__.__name__})

        # Log upload attempt
        logger.debug(
            f"📤 Announcing to tracker: {self.tracker_url}",
            extra={"class_name": self.__class__.__name__},
        )
        logger.debug(
            f"📊 Upload stats - Up: {uploaded_bytes} bytes, "
            f"Down: {downloaded_bytes} bytes, Left: {download_left} bytes",
            extra={"class_name": self.__class__.__name__},
        )

        max_retries = RetryConstants.HTTP_ANNOUNCE_MAX_RETRIES
        retry_count = 0

        while retry_count < max_retries and not self.shutdown_requested:
            try:
                # Use timeout for semaphore acquisition
                if not self.get_tracker_semaphore().acquire(timeout=TimeoutConstants.TRACKER_SEMAPHORE_ANNOUNCE):
                    logger.debug(
                        "⏱️ Timeout acquiring tracker semaphore",
                        extra={"class_name": self.__class__.__name__},
                    )
                    retry_count += 1
                    continue

                req = self.make_http_request(uploaded_bytes, downloaded_bytes, download_left, num_want=0)

                # Log successful announce
                logger.debug(
                    f"✅ Announce successful: HTTP {req.status_code}",
                    extra={"class_name": self.__class__.__name__},
                )

                # Try to decode response for any additional info
                try:
                    data = bencoding.decode(req.content)
                    if data and b"interval" in data:
                        logger.debug(
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
                    logger.debug(
                        "🛑 Shutdown requested, aborting HTTP announce",
                        extra={"class_name": self.__class__.__name__},
                    )
                    break

                # Update tracker model with failure
                self._update_tracker_failure(str(e))

                logger.warning(
                    f"⚠️ Announce failed (attempt {retry_count}/{max_retries}): {str(e)}",
                    extra={"class_name": self.__class__.__name__},
                )

                if retry_count < max_retries:
                    self.set_random_announce_url()
                    logger.debug(
                        f"🔄 Switched to tracker: {self.tracker_url}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Limit sleep time and check for shutdown
                    sleep_time = min(self.retry_sleep_interval, TimeoutConstants.HTTP_RETRY_MAX_SLEEP)
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

        # Send event=started on first announce, event=completed when download finishes
        if self.first_announce:
            http_params["event"] = "started"
            self.first_announce = False
        elif download_left == 0 and uploaded_bytes == 0 and downloaded_bytes == 0:
            # This is the completion event (first time we have 0 left)
            http_params["event"] = "completed"

        http_agent_headers = self.settings.http_headers
        http_agent_headers["User-Agent"] = self.settings.agents[self.settings.agent].split(",")[0]

        # Log request details
        logger.debug(
            f"🌐 Making HTTP request to: {self.tracker_url}",
            extra={"class_name": self.__class__.__name__},
        )
        logger.debug(
            f"🔧 User-Agent: {http_agent_headers['User-Agent']}",
            extra={"class_name": self.__class__.__name__},
        )
        event = http_params.get("event", "none")
        logger.debug(
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

    def _get_tracker_model(self) -> Tracker:
        """Get or create tracker model for current tracker URL"""
        if not hasattr(self, "_tracker_model") or self._tracker_model is None:
            # Create tracker model with current URL and tier
            self._tracker_model = Tracker(url=self.tracker_url, tier=0)
        elif self._tracker_model.get_property("url") != self.tracker_url:
            # URL changed, create new tracker model
            self._tracker_model = Tracker(url=self.tracker_url, tier=0)
        return self._tracker_model

    def _set_tracker_announcing(self):
        """Mark tracker as currently announcing"""
        try:
            tracker = self._get_tracker_model()
            tracker.set_announcing()
        except Exception as e:
            logger.debug(
                f"Failed to set tracker announcing status: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _update_tracker_success(self, response_data: dict, response_time: float):
        """Update tracker model with successful response"""
        try:
            tracker = self._get_tracker_model()

            # Convert byte keys to string keys for tracker model
            converted_data = {}
            for key, value in response_data.items():
                if isinstance(key, bytes):
                    str_key = key.decode("utf-8")
                else:
                    str_key = key
                converted_data[str_key] = value

            tracker.update_announce_response(converted_data, response_time)
        except Exception as e:
            logger.debug(
                f"Failed to update tracker success: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _update_tracker_failure(self, error_message: str, response_time: float = None):
        """Update tracker model with failed response"""
        try:
            tracker = self._get_tracker_model()
            tracker.update_announce_failure(error_message, response_time)
        except Exception as e:
            logger.debug(
                f"Failed to update tracker failure: {e}",
                extra={"class_name": self.__class__.__name__},
            )
