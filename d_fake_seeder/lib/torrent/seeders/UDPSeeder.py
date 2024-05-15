import random
import socket
import struct
from time import sleep

from lib.logger import logger
from lib.torrent.seeders.BaseSeeder import BaseSeeder
from lib.view import View


class UDPSeeder(BaseSeeder):

    def __init__(self, torrent):
        super().__init__(torrent)

    def generate_transaction_id(self):
        return random.randint(0, 255)

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

    def load_peers(self):
        logger.info("Seeder load peers", extra={"class_name": self.__class__.__name__})
        try:
            self.tracker_semaphore.acquire()
            View.instance.notify("load_peers " + self.tracker_url)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.connect((self.tracker_hostname, self.tracker_port))
                connection_id = 0x41727101980
                transaction_id = self.generate_transaction_id()
                announce_packet = self.build_announce_packet(
                    connection_id,
                    transaction_id,
                    self.torrent.file_hash,
                    self.peer_id.encode("ascii"),
                )
                sock.send(announce_packet)
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
                    self.tracker_semaphore.release()
                    return True

            self.tracker_semaphore.release()
            return False
        except Exception as e:
            self.handle_exception(e, "Seeder unknown error in load_peers_udp")
            return False

    def upload(self, uploaded_bytes, downloaded_bytes, download_left):
        logger.info("Seeder upload", extra={"class_name": self.__class__.__name__})
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.connect((self.tracker_hostname, self.tracker_port))
                    connection_id = 0x41727101980
                    transaction_id = self.generate_transaction_id()
                    announce_packet = self.build_announce_packet(
                        connection_id,
                        transaction_id,
                        self.torrent.file_hash,
                        self.peer_id.encode("ascii"),
                        uploaded_bytes,
                        downloaded_bytes,
                        download_left,
                    )
                    sock.send(announce_packet)
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
                        break
            except Exception as e:
                self.handle_exception(e, "Seeder unknown error in upload")
            sleep(0.5)
