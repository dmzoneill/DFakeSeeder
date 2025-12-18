# fmt: off
import random

# import select  # Replaced with socket timeout for PyPy compatibility
import socket
import struct
import time
from typing import Any

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.model.tracker import Tracker
from d_fake_seeder.domain.torrent.seeders.base_seeder import BaseSeeder
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import (
    NetworkConstants,
    TimeoutConstants,
    UDPTrackerConstants,
)

# fmt: on


class UDPSeeder(BaseSeeder):
    def __init__(self, torrent: Any) -> None:
        super().__init__(torrent)

    def build_announce_packet(
        self,
        connection_id: Any,
        transaction_id: Any,
        info_hash: Any,
        peer_id: Any,
        uploaded: Any = 0,
        downloaded: Any = 0,
        left: Any = 0,
    ) -> None:  # noqa: E501
        info_hash = (info_hash + b"\x00" * 20)[:20]
        peer_id = (peer_id + b"\x00" * 20)[:20]

        # Determine event: 0=none, 1=completed, 2=started, 3=stopped
        # Send event=2 (started) on first announce
        if self.first_announce:
            event = 2  # started
            self.first_announce = False
        elif left == 0 and uploaded == 0 and downloaded == 0:
            event = 1  # completed
        else:
            event = 0  # none (regular update)

        packet = struct.pack(
            "!QII20s20sQQQIIIiH",
            connection_id,
            1,  # action: announce
            transaction_id,
            info_hash,
            peer_id,
            downloaded,
            left,
            uploaded,
            event,
            0,  # IP address (0 = default)
            random.getrandbits(32),  # key
            -1,  # num_want (-1 = default)
            NetworkConstants.DEFAULT_PORT,
        )
        return packet  # type: ignore[return-value]

    def process_announce_response(self, response: Any) -> None:
        peers = []
        action, transaction_id, interval, leechers, seeders = struct.unpack_from("!IIIII", response, offset=0)
        offset = 20
        while offset + UDPTrackerConstants.IPV4_WITH_PORT_LENGTH <= len(response):
            ip, port = struct.unpack_from("!IH", response, offset=offset)
            ip = socket.inet_ntoa(struct.pack("!I", ip))
            peers.append((ip, port))
            offset += UDPTrackerConstants.IPV4_WITH_PORT_LENGTH
        return peers, interval, leechers, seeders  # type: ignore[return-value]

    def handle_announce(self, packet_data: Any, timeout: Any, log_msg: Any) -> None:
        logger.trace(log_msg, extra={"class_name": self.__class__.__name__})

        # Mark tracker as announcing
        self._set_tracker_announcing()
        request_start_time = time.time()

        # Log UDP tracker connection details
        logger.trace(
            f"📡 Connecting to UDP tracker: {self.tracker_hostname}:{self.tracker_port}",
            extra={"class_name": self.__class__.__name__},
        )
        logger.trace(
            f"📁 Torrent: {self.torrent.name} " f"(Hash: {self.torrent.file_hash.hex()[:16]}...)",
            extra={"class_name": self.__class__.__name__},
        )
        logger.trace(f"🆔 Peer ID: {self.peer_id}", extra={"class_name": self.__class__.__name__})

        # Log packet data if present (for upload announces)
        if packet_data:
            uploaded, downloaded, left = packet_data
            logger.trace(
                f"📊 Upload announce - Up: {uploaded} bytes, " f"Down: {downloaded} bytes, Left: {left} bytes",
                extra={"class_name": self.__class__.__name__},
            )

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((self.tracker_hostname, self.tracker_port))
                sock.settimeout(timeout)
                logger.trace(
                    f"🔌 UDP socket connected with {timeout}s timeout",
                    extra={"class_name": self.__class__.__name__},
                )

                connection_id = UDPTrackerConstants.MAGIC_CONNECTION_ID
                transaction_id = self.generate_transaction_id()
                logger.trace(
                    f"🔢 Transaction ID: {transaction_id}, " f"Connection ID: {hex(connection_id)}",
                    extra={"class_name": self.__class__.__name__},
                )

                announce_packet = self.build_announce_packet(  # type: ignore[func-returns-value]
                    connection_id,
                    transaction_id,
                    self.torrent.file_hash,
                    self.peer_id.encode("ascii"),
                    *packet_data,  # Unpack additional packet data
                )
                logger.trace(
                    f"📦 Sending UDP packet ({len(announce_packet)} bytes)",
                    extra={"class_name": self.__class__.__name__},
                )
                sock.send(announce_packet)

                # Use socket timeout instead of select for PyPy compatibility
                try:
                    app_settings = AppSettings.get_instance()
                    buffer_size = app_settings.get("seeders", {}).get(
                        "udp_buffer_size_bytes", UDPTrackerConstants.DEFAULT_BUFFER_SIZE
                    )
                    response = sock.recv(buffer_size)
                    logger.trace(
                        f"📨 Received UDP response ({len(response)} bytes)",
                        extra={"class_name": self.__class__.__name__},
                    )

                    peers, interval, leechers, seeders = self.process_announce_response(response)  # type: ignore[func-returns-value]  # noqa: E501

                    # Calculate response time and update tracker model
                    request_end_time = time.time()
                    response_time = request_end_time - request_start_time
                    response_data = {
                        "complete": seeders,
                        "incomplete": leechers,
                        "interval": interval,
                    }
                    self._update_tracker_success(response_data, response_time)

                    # Log tracker response details
                    logger.trace(
                        "✅ UDP tracker response processed successfully",
                        extra={"class_name": self.__class__.__name__},
                    )
                    logger.trace(
                        f"🌱 Seeders: {seeders}, ⬇️ Leechers: {leechers}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    logger.trace(
                        f"⏱️ Update interval: {interval} seconds",
                        extra={"class_name": self.__class__.__name__},
                    )
                    logger.trace(
                        f"👥 Found {len(peers)} peers",
                        extra={"class_name": self.__class__.__name__},
                    )

                    # Log individual peer details
                    for i, (ip, port) in enumerate(peers[: UDPTrackerConstants.PEER_LOG_LIMIT]):
                        logger.trace(
                            f"👥 Peer {i+1}: {ip}:{port}",
                            extra={"class_name": self.__class__.__name__},
                        )
                    if len(peers) > UDPTrackerConstants.PEER_LOG_LIMIT:
                        logger.trace(
                            f"👥 ... and {len(peers)-UDPTrackerConstants.PEER_LOG_LIMIT} more peers",
                            extra={"class_name": self.__class__.__name__},
                        )

                    if peers is not None:
                        self.info = {
                            b"peers": peers,
                            b"interval": interval,
                            b"leechers": leechers,
                            b"seeders": seeders,
                        }
                        self.update_interval = self._apply_announce_jitter(self.info[b"interval"])
                    return True  # type: ignore[return-value]
                except socket.timeout:
                    # Update tracker model with timeout failure
                    request_end_time = time.time()
                    response_time = request_end_time - request_start_time
                    self._update_tracker_failure(f"Socket timeout ({timeout}s)", response_time)

                    # Timeout occurred
                    logger.error(
                        f"⏱️ UDP socket timeout ({timeout}s) - no response from tracker",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.set_random_announce_url()
                    logger.trace(
                        f"🔄 Switched to backup tracker: " f"{self.tracker_hostname}:{self.tracker_port}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return False  # type: ignore[return-value]

        except Exception as e:
            # Update tracker model with failure
            if "request_start_time" in locals():
                request_end_time = time.time()
                response_time = request_end_time - request_start_time
                self._update_tracker_failure(str(e), response_time)
            else:
                self._update_tracker_failure(str(e))

            logger.error(
                f"❌ UDP tracker error: {str(e)}",
                extra={"class_name": self.__class__.__name__},
            )
            self.set_random_announce_url()
            logger.trace(
                f"🔄 Switched to backup tracker: " f"{self.tracker_hostname}:{self.tracker_port}",
                extra={"class_name": self.__class__.__name__},
            )
            self.handle_exception(e, f"Seeder unknown error in {log_msg}")
            return False  # type: ignore[return-value]

    def load_peers(self) -> None:
        logger.trace(
            "🔄 Starting UDP peer discovery",
            extra={"class_name": self.__class__.__name__},
        )

        if self.shutdown_requested:
            logger.trace(
                "🛑 Shutdown requested, aborting UDP load_peers",
                extra={"class_name": self.__class__.__name__},
            )
            return False  # type: ignore[return-value]

        # Use timeout for semaphore acquisition
        if not self.get_tracker_semaphore().acquire(timeout=TimeoutConstants.TRACKER_SEMAPHORE_UDP):
            logger.warning(
                "⏱️ Timeout acquiring tracker semaphore for UDP load_peers",
                extra={"class_name": self.__class__.__name__},
            )
            return False  # type: ignore[return-value]

        try:
            # Send initial announce with download_left = total_size
            result = self.handle_announce(  # type: ignore[func-returns-value]
                packet_data=(
                    0,
                    0,
                    self.torrent.total_size,
                ),  # uploaded=0, downloaded=0, left=total_size
                timeout=getattr(self.settings, "seeders", {}).get("udp_load_timeout_seconds", 5),
                log_msg="Seeder load peers",
            )
        finally:
            self.get_tracker_semaphore().release()

        if result:
            logger.trace(
                "✅ UDP peer discovery completed successfully",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            logger.error(
                "❌ UDP peer discovery failed",
                extra={"class_name": self.__class__.__name__},
            )

        return result  # type: ignore[no-any-return]

    def upload(self, uploaded_bytes: Any, downloaded_bytes: Any, download_left: Any) -> Any:
        logger.trace(
            "📤 Starting UDP announce to tracker",
            extra={"class_name": self.__class__.__name__},
        )

        if self.shutdown_requested:
            logger.trace(
                "🛑 Shutdown requested, aborting UDP upload",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        # Validate uploaded/downloaded bytes to prevent reporting unrealistic values
        # Maximum reasonable value: 1 TB (1,000,000,000,000 bytes)
        MAX_REASONABLE_BYTES = 1_000_000_000_000

        if uploaded_bytes > MAX_REASONABLE_BYTES:
            logger.warning(
                f"⚠️ Unrealistic upload value detected: {uploaded_bytes:,} bytes "
                f"({uploaded_bytes / 1_000_000_000:.2f} GB). Capping at 1 TB.",
                extra={"class_name": self.__class__.__name__},
            )
            uploaded_bytes = MAX_REASONABLE_BYTES

        if downloaded_bytes > MAX_REASONABLE_BYTES:
            logger.warning(
                f"⚠️ Unrealistic download value detected: {downloaded_bytes:,} bytes "
                f"({downloaded_bytes / 1_000_000_000:.2f} GB). Capping at 1 TB.",
                extra={"class_name": self.__class__.__name__},
            )
            downloaded_bytes = MAX_REASONABLE_BYTES

        packet_data = (uploaded_bytes, downloaded_bytes, download_left)
        result = self.handle_announce(  # type: ignore[func-returns-value]
            packet_data=packet_data,
            timeout=getattr(self.settings, "seeders", {}).get("udp_upload_timeout_seconds", 4),
            log_msg="Seeder upload",
        )

        if result:
            logger.trace(
                "✅ UDP announce completed successfully",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            logger.error("❌ UDP announce failed", extra={"class_name": self.__class__.__name__})

        return result

    def _get_tracker_model(self) -> Tracker:
        """Get or create tracker model for current tracker URL"""
        tracker_url = f"udp://{self.tracker_hostname}:{self.tracker_port}"
        if not hasattr(self, "_tracker_model") or self._tracker_model is None:  # type: ignore[has-type]
            # Create tracker model with current URL and tier
            self._tracker_model = Tracker(url=tracker_url, tier=0)
        elif self._tracker_model.get_property("url") != tracker_url:
            # URL changed, create new tracker model
            self._tracker_model = Tracker(url=tracker_url, tier=0)
        return self._tracker_model

    def _set_tracker_announcing(self) -> Any:
        """Mark tracker as currently announcing"""
        try:
            tracker = self._get_tracker_model()
            tracker.set_announcing()
        except Exception as e:
            logger.trace(
                f"Failed to set tracker announcing status: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _update_tracker_success(self, response_data: dict, response_time: float) -> None:
        """Update tracker model with successful response"""
        try:
            tracker = self._get_tracker_model()
            tracker.update_announce_response(response_data, response_time)
        except Exception as e:
            logger.trace(
                f"Failed to update tracker success: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _update_tracker_failure(self, error_message: str, response_time: float = None) -> None:  # type: ignore[assignment]  # noqa: E501
        """Update tracker model with failed response"""
        try:
            tracker = self._get_tracker_model()
            tracker.update_announce_failure(error_message, response_time)
        except Exception as e:
            logger.trace(
                f"Failed to update tracker failure: {e}",
                extra={"class_name": self.__class__.__name__},
            )
