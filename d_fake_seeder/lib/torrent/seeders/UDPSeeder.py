import random
import select
import socket
import struct

from lib.logger import logger
from lib.torrent.seeders.BaseSeeder import BaseSeeder


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
        action, transaction_id, interval, leechers, seeders = struct.unpack_from(
            "!IIIII", response, offset=0
        )
        offset = 20
        while offset + 6 <= len(response):
            ip, port = struct.unpack_from("!IH", response, offset=offset)
            ip = socket.inet_ntoa(struct.pack("!I", ip))
            peers.append((ip, port))
            offset += 6
        return peers, interval, leechers, seeders

    def handle_announce(self, packet_data, timeout, log_msg):
        logger.info(log_msg, extra={"class_name": self.__class__.__name__})

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((self.tracker_hostname, self.tracker_port))
                sock.settimeout(timeout)

                connection_id = 0x41727101980
                transaction_id = self.generate_transaction_id()
                announce_packet = self.build_announce_packet(
                    connection_id,
                    transaction_id,
                    self.torrent.file_hash,
                    self.peer_id.encode("ascii"),
                    *packet_data,  # Unpack additional packet data
                )
                sock.send(announce_packet)

                ready = select.select([sock], [], [], timeout)
                if ready[0]:
                    response = sock.recv(2048)
                    peers, interval, leechers, seeders = self.process_announce_response(
                        response
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
                else:
                    # Timeout occurred
                    self.set_random_announce_url()
                    logger.error("Socket operation timed out")
                    return False

        except Exception as e:
            self.set_random_announce_url()
            self.handle_exception(e, f"Seeder unknown error in {log_msg}")
            return False

    def load_peers(self):
        self.tracker_semaphore.acquire()
        result = self.handle_announce(
            packet_data=(), timeout=5, log_msg="Seeder load peers"
        )
        self.tracker_semaphore.release()
        return result

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        packet_data = (uploaded_bytes, downloaded_bytes, download_left)
        return self.handle_announce(
            packet_data=packet_data, timeout=4, log_msg="Seeder upload"
        )
