import os
import random
import socket
import struct

from lib.torrent.file import File as Torrent


def generate_transaction_id():
    return random.randint(0, 255)


def build_announce_packet(connection_id, transaction_id, info_hash, peer_id):
    info_hash = (info_hash + b"\x00" * 20)[:20]
    peer_id = (peer_id + b"\x00" * 20)[:20]
    packet = struct.pack(
        "!QII20s20sQQQIIIiH",
        connection_id,
        0,
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


def process_announce_response(response):
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


def udp_tracker_announce(tracker_url, info_hash, peer_id):
    try:
        _, tracker_address = tracker_url.split("://")
        host, port_path = tracker_address.split(":")
        port = int(port_path.split("/")[0])
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(30)
        tracker_ip = socket.gethostbyname(host)
        sock.connect((tracker_ip, port))
        connection_id = 0x41727101980
        transaction_id = generate_transaction_id()
        announce_packet = build_announce_packet(
            connection_id, transaction_id, info_hash, peer_id
        )
        sock.send(announce_packet)
        response = sock.recv(2048)
        peers, interval, leechers, seeders = process_announce_response(response)
    except Exception as e:
        print(f"An error occurred while connecting to the tracker. {e}")
    finally:
        sock.close()


if __name__ == "__main__":
    t = Torrent("/home/daoneill/.config/dfakeseeder/torrents/udp.torrent")
    client = "-DE2003-" + os.urandom(9).hex()
    udp_tracker_announce(t.announce, t.file_hash, bytes(client, "utf-8"))
