import random
import socket
import struct
import traceback

from lib.torrent.file import TorrentFile


def generate_transaction_id():
    return random.randint(0, 255)


def build_announce_packet(connection_id, transaction_id, info_hash, peer_id):
    packet = struct.pack(
        "!QII20s20sQQQ",
        connection_id,
        1,
        transaction_id,
        info_hash,
        peer_id,
        0,
        0,
        0,
    )
    return packet


def process_announce_response(response):
    peers = []
    action, transaction_id, interval, leechers, seeders = struct.unpack_from(
        "!IIIII", response, offset=0
    )
    offset = 20

    print("Raw response:", response.decode("latin-1"))

    print("Action:", action)
    print("Transaction ID:", transaction_id)
    print("Interval:", interval)
    print("Leechers:", leechers)
    print("Seeders:", seeders)

    while offset + 6 <= len(response):
        ip, port = struct.unpack_from("!IH", response, offset=offset)
        ip = socket.inet_ntoa(struct.pack("!I", ip))
        peers.append((ip, port))
        offset += 6

    return peers, interval, leechers, seeders


def udp_tracker_announce(tracker_url, info_hash, peer_id):
    try:
        # Parse the tracker URL
        _, tracker_address = tracker_url.split("://")
        host, port_path = tracker_address.split(":")
        port = int(port_path.split("/")[0])

        # Create a UDP socket and set the timeout
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10)

        # Connect to the tracker
        tracker_ip = socket.gethostbyname(host)
        sock.connect((tracker_ip, port))

        # Generate a connection ID
        connection_id = 0x41727101980

        # Generate a transaction ID
        transaction_id = generate_transaction_id()

        # Construct the announce request packet
        announce_packet = build_announce_packet(
            connection_id, transaction_id, info_hash, peer_id
        )

        # Send the announce request
        sock.send(announce_packet)

        # Receive and process the announce response
        response = sock.recv(2048)
        peers, interval, leechers, seeders = process_announce_response(response)

        print("Peers:")
        for peer in peers:
            print(peer)

        print(f"Interval: {interval}")
        print(f"Leechers: {leechers}")
        print(f"Seeders: {seeders}")

    except Exception as e:
        print(e)
        print(traceback.format_exc())
        print("An error occurred while connecting to the tracker.")

    finally:
        sock.close()


if __name__ == "__main__":
    t = TorrentFile("torrents/d5d24ec621f1f6f77c094aea6bac7c5b9d80b024.torrent")
    print(t.announce)
    print(t.file_hash)
    udp_tracker_announce(t.announce, t.file_hash, b"-MY-PEER-ID-")
