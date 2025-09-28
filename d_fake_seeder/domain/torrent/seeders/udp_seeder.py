import random

# import select  # Replaced with socket timeout for PyPy compatibility
import socket
import struct

from domain.app_settings import AppSettings
from domain.torrent.seeders.base_seeder import BaseSeeder
from lib.logger import logger


class UDPSeeder(BaseSeeder):
    def __init__(self, torrent):
        super().__init__(torrent)

    def build_announce_packet(self, connection_id, transaction_id, info_hash, peer_id):
        info_hash = (info_hash + b"\x00" * 20)[:20]
        peer_id = (peer_id + b"\x00" * 20)[:20]
        packet = struct.pack(
            "!QII20s20sQQQIIIiH",
            connection_id,
            1,
            transaction_id,
            info_hash,
            peer_id,
            0,
            0,
            0,
            0,
            0,
            random.getrandbits(32),
            -1,
            6881,
        )
        return packet

    def process_announce_response(self, response):
        peers = []
        action, transaction_id, interval, leechers, seeders = struct.unpack_from("!IIIII", response, offset=0)
        offset = 20
        while offset + 6 <= len(response):
            ip, port = struct.unpack_from("!IH", response, offset=offset)
            ip = socket.inet_ntoa(struct.pack("!I", ip))
            peers.append((ip, port))
            offset += 6
        return peers, interval, leechers, seeders

    def handle_announce(self, packet_data, timeout, log_msg):
        logger.info(log_msg, extra={"class_name": self.__class__.__name__})

        # Log UDP tracker connection details
        logger.info(
            f"📡 Connecting to UDP tracker: {self.tracker_hostname}:{self.tracker_port}",
            extra={"class_name": self.__class__.__name__},
        )
        logger.info(
            f"📁 Torrent: {self.torrent.name} " f"(Hash: {self.torrent.file_hash.hex()[:16]}...)",
            extra={"class_name": self.__class__.__name__},
        )
        logger.info(f"🆔 Peer ID: {self.peer_id}", extra={"class_name": self.__class__.__name__})

        # Log packet data if present (for upload announces)
        if packet_data:
            uploaded, downloaded, left = packet_data
            logger.info(
                f"📊 Upload announce - Up: {uploaded} bytes, " f"Down: {downloaded} bytes, Left: {left} bytes",
                extra={"class_name": self.__class__.__name__},
            )

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((self.tracker_hostname, self.tracker_port))
                sock.settimeout(timeout)
                logger.info(
                    f"🔌 UDP socket connected with {timeout}s timeout",
                    extra={"class_name": self.__class__.__name__},
                )

                connection_id = 0x41727101980
                transaction_id = self.generate_transaction_id()
                logger.info(
                    f"🔢 Transaction ID: {transaction_id}, " f"Connection ID: {hex(connection_id)}",
                    extra={"class_name": self.__class__.__name__},
                )

                announce_packet = self.build_announce_packet(
                    connection_id,
                    transaction_id,
                    self.torrent.file_hash,
                    self.peer_id.encode("ascii"),
                    *packet_data,  # Unpack additional packet data
                )
                logger.info(
                    f"📦 Sending UDP packet ({len(announce_packet)} bytes)",
                    extra={"class_name": self.__class__.__name__},
                )
                sock.send(announce_packet)

                # Use socket timeout instead of select for PyPy compatibility
                try:
                    app_settings = AppSettings.get_instance()
                    buffer_size = app_settings.get("seeders", {}).get("udp_buffer_size_bytes", 2048)
                    response = sock.recv(buffer_size)
                    logger.info(
                        f"📨 Received UDP response ({len(response)} bytes)",
                        extra={"class_name": self.__class__.__name__},
                    )

                    peers, interval, leechers, seeders = self.process_announce_response(response)

                    # Log tracker response details
                    logger.info(
                        "✅ UDP tracker response processed successfully",
                        extra={"class_name": self.__class__.__name__},
                    )
                    logger.info(
                        f"🌱 Seeders: {seeders}, ⬇️ Leechers: {leechers}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    logger.info(
                        f"⏱️ Update interval: {interval} seconds",
                        extra={"class_name": self.__class__.__name__},
                    )
                    logger.info(
                        f"👥 Found {len(peers)} peers",
                        extra={"class_name": self.__class__.__name__},
                    )

                    # Log individual peer details
                    for i, (ip, port) in enumerate(peers[:5]):  # Log first 5 peers
                        logger.info(
                            f"👥 Peer {i+1}: {ip}:{port}",
                            extra={"class_name": self.__class__.__name__},
                        )
                    if len(peers) > 5:
                        logger.info(
                            f"👥 ... and {len(peers)-5} more peers",
                            extra={"class_name": self.__class__.__name__},
                        )

                    if peers is not None:
                        self.info = {
                            b"peers": peers,
                            b"interval": interval,
                            b"leechers": leechers,
                            b"seeders": seeders,
                        }
                        self.update_interval = self.info[b"interval"]
                    return True
                except socket.timeout:
                    # Timeout occurred
                    logger.error(
                        f"⏱️ UDP socket timeout ({timeout}s) - no response from tracker",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.set_random_announce_url()
                    logger.info(
                        f"🔄 Switched to backup tracker: " f"{self.tracker_hostname}:{self.tracker_port}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return False

        except Exception as e:
            logger.error(
                f"❌ UDP tracker error: {str(e)}",
                extra={"class_name": self.__class__.__name__},
            )
            self.set_random_announce_url()
            logger.info(
                f"🔄 Switched to backup tracker: " f"{self.tracker_hostname}:{self.tracker_port}",
                extra={"class_name": self.__class__.__name__},
            )
            self.handle_exception(e, f"Seeder unknown error in {log_msg}")
            return False

    def load_peers(self):
        logger.info(
            "🔄 Starting UDP peer discovery",
            extra={"class_name": self.__class__.__name__},
        )

        if self.shutdown_requested:
            logger.info("🛑 Shutdown requested, aborting UDP load_peers", extra={"class_name": self.__class__.__name__})
            return False

        # Use timeout for semaphore acquisition
        if not self.get_tracker_semaphore().acquire(timeout=3.0):
            logger.warning(
                "⏱️ Timeout acquiring tracker semaphore for UDP load_peers",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            result = self.handle_announce(
                packet_data=(),
                timeout=getattr(self.settings, "seeders", {}).get("udp_load_timeout_seconds", 5),
                log_msg="Seeder load peers",
            )
        finally:
            self.get_tracker_semaphore().release()

        if result:
            logger.info(
                "✅ UDP peer discovery completed successfully",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            logger.error(
                "❌ UDP peer discovery failed",
                extra={"class_name": self.__class__.__name__},
            )

        return result

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        logger.info(
            "📤 Starting UDP announce to tracker",
            extra={"class_name": self.__class__.__name__},
        )

        if self.shutdown_requested:
            logger.info("🛑 Shutdown requested, aborting UDP upload", extra={"class_name": self.__class__.__name__})
            return False

        packet_data = (uploaded_bytes, downloaded_bytes, download_left)
        result = self.handle_announce(
            packet_data=packet_data,
            timeout=getattr(self.settings, "seeders", {}).get("udp_upload_timeout_seconds", 4),
            log_msg="Seeder upload",
        )

        if result:
            logger.info(
                "✅ UDP announce completed successfully",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            logger.error("❌ UDP announce failed", extra={"class_name": self.__class__.__name__})

        return result
