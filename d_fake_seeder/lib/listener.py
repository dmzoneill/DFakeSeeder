import signal
import socket
import struct
import threading

# Importing necessary libraries
from lib.logger import logger


class Listener:
    def __init__(self, model):
        self.model = model
        self.server_socket = None
        self.thread = None
        self.running = False
        logger.info(
            "Listener instantiated",
            extra={"class_name": self.__class__.__name__},
        )
        signal.signal(signal.SIGINT, self.quit)

    def handle_connection(self, client_socket):
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            # Process the received data
            # You can send responses back to the client if needed
            logger.info("Expected input information for BitTorrent client connection")

    def start_listening(self, port):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(("0.0.0.0", port))
        self.server_socket.listen(5)
        self.running = True

        def listening_thread():
            while self.running:
                client_socket, address = self.server_socket.accept()
                self.handle_connection(client_socket)
                client_socket.close()

        self.thread = threading.Thread(target=listening_thread)
        self.thread.start()

    def start(self):
        self.start_listening(34567)

    # Sending a handshake message
    def send_handshake(peer_id, info_hash, peer_ip, peer_port):
        info_hash = (info_hash + b"\x00" * 20)[:20]
        peer_id = (peer_id + b"\x00" * 20)[:20]
        handshake = struct.pack(
            "!B19s8x20s20s", 19, b"BitTorrent protocol", info_hash, peer_id
        )
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((peer_ip, peer_port))
        sock.send(handshake)
        # Close the socket after sending the message
        sock.close()

    # Sending an "interested" message
    def send_interested(peer_ip, peer_port):
        interested = struct.pack(
            "!IB", 1, 2
        )  # Message length (1) and message ID for "interested" (2)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((peer_ip, peer_port))
        sock.send(interested)
        # Close the socket after sending the message
        sock.close()

    def process_scrape_response(self, response):
        files = []
        action, transaction_id = struct.unpack_from("!II", response, offset=0)
        offset = 8
        while offset + 12 <= len(response):
            seeders, completed, leechers = struct.unpack_from(
                "!III", response, offset=offset
            )
            files.append((seeders, completed, leechers))
            offset += 12
        return files

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.thread:
            self.thread.join()

    # Function to quit the application
    def quit(self, widget=None, event=None):
        logger.info("View quit", extra={"class_name": self.__class__.__name__})
        self.stop()
