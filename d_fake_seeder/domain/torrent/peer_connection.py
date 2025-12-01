"""
BitTorrent Peer Connection

Handles individual TCP connections to BitTorrent peers including handshakes
and message exchange following BEP-003 specification.
"""

# fmt: off
import asyncio
import socket
import struct
import time
from typing import Optional, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.peer_info import PeerInfo
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import BitTorrentProtocolConstants

# fmt: on


class PeerConnection:
    """Represents a single peer connection"""

    def __init__(
        self,
        peer_info: PeerInfo,
        info_hash: bytes,
        our_peer_id: bytes,
        connection_callback=None,
    ):
        self.peer_info = peer_info
        self.info_hash = info_hash
        self.our_peer_id = our_peer_id
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.handshake_complete = False
        self.last_message_time = 0.0
        self.bytes_downloaded = 0
        self.bytes_uploaded = 0
        self.connection_callback = connection_callback

        # Get settings instance for configurable timeouts
        self.settings = AppSettings.get_instance()
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.connection_timeout = ui_settings.get("connection_timeout_seconds", 10.0)
        self.message_receive_timeout = ui_settings.get("message_receive_timeout_seconds", 5.0)

    async def connect(self, timeout: Optional[float] = None) -> bool:
        """Establish TCP connection to peer"""
        if timeout is None:
            timeout = self.connection_timeout

        try:
            logger.debug(
                f"🔌 Connecting to peer {self.peer_info.ip}:{self.peer_info.port}",
                extra={"class_name": self.__class__.__name__},
            )

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)

            await asyncio.get_running_loop().run_in_executor(
                None, self.socket.connect, (self.peer_info.ip, self.peer_info.port)
            )

            self.connected = True
            self.peer_info.last_connected = time.time()

            # Notify UI of new outgoing connection
            logger.debug(
                f"✅ Successfully connected to peer " f"{self.peer_info.ip}:{self.peer_info.port}",
                extra={"class_name": self.__class__.__name__},
            )
            if self.connection_callback:
                self.connection_callback(
                    "outgoing",
                    "add",
                    self.peer_info.ip,
                    self.peer_info.port,
                    {
                        "connected": True,
                        "handshake_complete": False,
                        "status": "connected",
                    },
                )

            return True

        except (socket.timeout, socket.error, OSError) as e:
            logger.debug(
                f"❌ Failed to connect to " f"{self.peer_info.ip}:{self.peer_info.port}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

            # Notify UI of failed connection attempt
            if self.connection_callback:
                self.connection_callback(
                    "outgoing",
                    "add",
                    self.peer_info.ip,
                    self.peer_info.port,
                    {
                        "connected": False,
                        "status": "failed",
                        "failure_reason": str(e),
                    },
                )

            self.close()
            return False

    async def perform_handshake(self) -> bool:
        """Perform BitTorrent handshake"""
        if not self.connected or self.socket is None:
            return False

        try:
            # BitTorrent handshake format:
            # <pstrlen><pstr><reserved><info_hash><peer_id>
            pstr = BitTorrentProtocolConstants.PROTOCOL_NAME
            pstrlen = BitTorrentProtocolConstants.PROTOCOL_NAME_LENGTH
            reserved = BitTorrentProtocolConstants.RESERVED_BYTES

            handshake = struct.pack("!B", pstrlen) + pstr + reserved + self.info_hash + self.our_peer_id

            # Send handshake
            await asyncio.get_running_loop().run_in_executor(None, self.socket.send, handshake)

            # Receive handshake response
            response = await asyncio.get_running_loop().run_in_executor(
                None, self.socket.recv, BitTorrentProtocolConstants.HANDSHAKE_LENGTH
            )

            if len(response) != BitTorrentProtocolConstants.HANDSHAKE_LENGTH:
                logger.debug(
                    f"❌ Invalid handshake response length from {self.peer_info.ip}",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Parse handshake response
            response_pstrlen = response[0]
            if response_pstrlen != pstrlen:
                return False

            # Extract protocol string
            pstr_start = 1
            pstr_end = 1 + response_pstrlen
            response_pstr = response[pstr_start:pstr_end]
            if response_pstr != pstr:
                return False

            # Extract info hash
            info_hash_start = 1 + response_pstrlen + BitTorrentProtocolConstants.RESERVED_BYTES_LENGTH
            info_hash_end = info_hash_start + BitTorrentProtocolConstants.INFOHASH_LENGTH
            response_info_hash = response[info_hash_start:info_hash_end]
            if response_info_hash != self.info_hash:
                return False

            # Extract peer ID
            peer_id_start = (
                1
                + response_pstrlen
                + BitTorrentProtocolConstants.RESERVED_BYTES_LENGTH
                + BitTorrentProtocolConstants.INFOHASH_LENGTH
            )
            peer_id_end = peer_id_start + BitTorrentProtocolConstants.PEER_ID_LENGTH
            peer_id = response[peer_id_start:peer_id_end]
            self.peer_info.peer_id = peer_id

            logger.debug(
                f"✅ Handshake successful with " f"{self.peer_info.ip}:{self.peer_info.port}",
                extra={"class_name": self.__class__.__name__},
            )

            self.handshake_complete = True
            self.last_message_time = time.time()

            # Notify UI of handshake completion
            if self.connection_callback:
                self.connection_callback(
                    "outgoing",
                    "update",
                    self.peer_info.ip,
                    self.peer_info.port,
                    {"handshake_complete": True, "status": "connected"},
                )

            return True

        except Exception as e:
            logger.debug(
                f"❌ Handshake failed with {self.peer_info.ip}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def send_message(self, message_id: int, payload: bytes = b"") -> bool:
        """Send a BitTorrent message"""
        if not self.handshake_complete or self.socket is None:
            return False

        try:
            # Message format: <length><id><payload>
            length = 1 + len(payload)  # 1 byte for message ID + payload
            message = struct.pack("!I", length) + struct.pack("!B", message_id) + payload

            await asyncio.get_running_loop().run_in_executor(None, self.socket.send, message)

            self.last_message_time = time.time()
            return True

        except Exception as e:
            logger.debug(
                f"❌ Failed to send message to {self.peer_info.ip}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Tuple[int, bytes]]:
        """Receive a BitTorrent message"""
        if timeout is None:
            timeout = self.message_receive_timeout

        if not self.handshake_complete or self.socket is None:
            return None

        try:
            self.socket.settimeout(timeout)

            # Read message length (4 bytes)
            length_data = await asyncio.get_running_loop().run_in_executor(
                None,
                self.socket.recv,
                BitTorrentProtocolConstants.MESSAGE_LENGTH_HEADER_BYTES,
            )

            if len(length_data) != BitTorrentProtocolConstants.MESSAGE_LENGTH_HEADER_BYTES:
                return None

            length = struct.unpack("!I", length_data)[0]

            # Handle keep-alive message (length = 0)
            if length == BitTorrentProtocolConstants.KEEPALIVE_MESSAGE_LENGTH:
                self.last_message_time = time.time()
                return (-1, b"")  # Special case for keep-alive

            # Read message ID and payload
            message_data = await asyncio.get_running_loop().run_in_executor(None, self.socket.recv, length)

            if len(message_data) != length:
                return None

            message_id = message_data[0]
            payload = (
                message_data[BitTorrentProtocolConstants.MESSAGE_PAYLOAD_START_OFFSET :]
                if length > BitTorrentProtocolConstants.MESSAGE_ID_LENGTH_BYTES
                else b""
            )

            self.last_message_time = time.time()
            return (message_id, payload)

        except Exception as e:
            logger.debug(
                f"❌ Failed to receive message from {self.peer_info.ip}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    async def send_keep_alive(self) -> bool:
        """Send keep-alive message"""
        if self.socket is None:
            return False

        try:
            # Keep-alive is just a length of 0
            keep_alive = struct.pack("!I", BitTorrentProtocolConstants.KEEPALIVE_MESSAGE_LENGTH)
            await asyncio.get_running_loop().run_in_executor(None, self.socket.send, keep_alive)
            return True
        except Exception:
            return False

    def close(self):
        """Close the connection"""
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
            self.socket = None

        # Notify UI of disconnection
        if self.connection_callback and self.connected:
            self.connection_callback("outgoing", "remove", self.peer_info.ip, self.peer_info.port)

        self.connected = False
        self.handshake_complete = False
