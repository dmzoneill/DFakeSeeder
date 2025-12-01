"""
BitTorrent Peer Server

Accepts incoming peer connections and handles the BitTorrent peer protocol.
Responds with fake data that will be discarded by real clients due to hash verification.
"""

# fmt: off
import asyncio
import struct
import threading
from typing import Dict, Optional, Set

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.bittorrent_message import BitTorrentMessage
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import (
    BitTorrentProtocolConstants,
    ConnectionConstants,
    NetworkConstants,
    TimeoutConstants,
)

# fmt: on


class PeerServer:
    """Server to accept incoming BitTorrent peer connections"""

    def __init__(
        self,
        port: int = NetworkConstants.DEFAULT_PORT,
        max_connections: int = ConnectionConstants.DEFAULT_MAX_INCOMING_CONNECTIONS,
    ):
        self.port = port
        self.max_connections = max_connections
        self.running = False
        self.server: Optional[asyncio.Server] = None
        self.server_thread: Optional[threading.Thread] = None

        # Get settings instance
        self.settings = AppSettings.get_instance()

        # Connection tracking
        self.active_connections: Dict[str, asyncio.StreamWriter] = {}
        self.connection_count = 0

        # Known info hashes from torrents we're seeding
        self.known_info_hashes: Set[bytes] = set()

        # Fake data responses - get size from config
        peer_protocol = getattr(self.settings, "peer_protocol", {})
        fake_piece_size_kb = peer_protocol.get("fake_piece_data_size_kb", 16)
        self.fake_piece_data = b"X" * (fake_piece_size_kb * 1024)

        # Timeout settings from config
        self.handshake_timeout = peer_protocol.get("handshake_timeout_seconds", 30.0)
        self.message_read_timeout = peer_protocol.get("message_read_timeout_seconds", 60.0)
        self.data_read_timeout = peer_protocol.get("data_read_timeout_seconds", 30.0)

        # Thread management timeout
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.server_thread_join_timeout = ui_settings.get("manager_thread_join_timeout_seconds", 5.0)

        # Configurable bitfield probability
        self.bitfield_piece_probability = ui_settings.get("bitfield_piece_probability", 0.3)
        self.max_piece_request_size = ui_settings.get("max_piece_request_size_bytes", 32768)
        self.bitfield_size = ui_settings.get("bitfield_size_bytes", 32)

        # UI callback for connection updates
        self.connection_callback = None

    def add_info_hash(self, info_hash: bytes):
        """Add an info hash that we should respond to"""
        self.known_info_hashes.add(info_hash)
        logger.debug(
            f"📝 Added info hash {info_hash.hex()[:12]}... to peer server",
            extra={"class_name": self.__class__.__name__},
        )

    def set_connection_callback(self, callback):
        """Set callback for connection updates"""
        self.connection_callback = callback

    def start(self):
        """Start the peer server"""
        if self.running:
            return

        self.running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

        logger.info(
            f"🌐 Started BitTorrent peer server on port {self.port}",
            extra={"class_name": self.__class__.__name__},
        )

    def stop(self):
        """Stop the peer server"""
        if not self.running:
            return

        logger.info(
            "🛑 Stopping BitTorrent peer server",
            extra={"class_name": self.__class__.__name__},
        )

        self.running = False

        # Close the asyncio server to stop accepting new connections
        if self.server:
            try:
                self.server.close()
                logger.debug(
                    "🚪 Peer server closed (no longer accepting connections)",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.warning(
                    f"⚠️ Error closing peer server: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        # Close all active connections
        for writer in self.active_connections.values():
            try:
                writer.close()
            except Exception:
                pass
        self.active_connections.clear()

        # Wait for server thread with aggressive timeout
        if self.server_thread and self.server_thread.is_alive():
            join_timeout = TimeoutConstants.SERVER_THREAD_SHUTDOWN
            logger.debug(
                f"⏱️ Waiting for server thread to finish (timeout: {join_timeout}s)",
                extra={"class_name": self.__class__.__name__},
            )
            self.server_thread.join(timeout=join_timeout)

            if self.server_thread.is_alive():
                logger.warning(
                    "⚠️ Peer server thread still alive after timeout - forcing shutdown",
                    extra={"class_name": self.__class__.__name__},
                )

    def _run_server(self):
        """Run the async server in a thread"""
        asyncio.new_event_loop().run_until_complete(self._async_server())

    async def _async_server(self):
        """Main async server loop"""
        try:
            app_settings = AppSettings.get_instance()
            bind_address = app_settings.get("peer_server_bind_address", "0.0.0.0")

            self.server = await asyncio.start_server(self._handle_client, bind_address, self.port)

            logger.debug(
                f"🎧 Peer server listening on {bind_address}:{self.port}",
                extra={"class_name": self.__class__.__name__},
            )

            async with self.server:
                await self.server.serve_forever()

        except Exception as e:
            logger.error(
                f"❌ Error in peer server: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming peer connection"""
        client_addr = writer.get_extra_info("peername")
        client_key = f"{client_addr[0]}:{client_addr[1]}"
        client_ip, client_port = client_addr[0], client_addr[1]

        # Check connection limit
        if len(self.active_connections) >= self.max_connections:
            logger.debug(
                f"🚫 Rejected connection from {client_key} (max connections reached)",
                extra={"class_name": self.__class__.__name__},
            )
            writer.close()
            return

        self.active_connections[client_key] = writer
        self.connection_count += 1

        logger.debug(
            f"🤝 Accepted peer connection from {client_key} " f"(total: {len(self.active_connections)})",
            extra={"class_name": self.__class__.__name__},
        )

        # Notify UI of new connection
        if self.connection_callback:
            self.connection_callback(
                "incoming",
                "add",
                client_ip,
                client_port,
                {"connected": True, "handshake_complete": False},
            )

        try:
            # Handle the peer protocol
            await self._handle_peer_protocol(reader, writer, client_key)

        except Exception as e:
            logger.debug(
                f"❌ Error handling peer {client_key}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        finally:
            # Cleanup
            if client_key in self.active_connections:
                del self.active_connections[client_key]
            try:
                writer.close()
            except Exception:
                pass

            logger.debug(
                f"👋 Disconnected peer {client_key}",
                extra={"class_name": self.__class__.__name__},
            )

            # Notify UI of disconnection
            if self.connection_callback:
                self.connection_callback("incoming", "remove", client_ip, client_port)

    async def _handle_peer_protocol(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        client_key: str,
    ):
        """Handle BitTorrent peer protocol messages"""

        # Wait for handshake
        try:
            handshake_data = await asyncio.wait_for(
                reader.read(BitTorrentProtocolConstants.HANDSHAKE_LENGTH),
                timeout=self.handshake_timeout,
            )
            if len(handshake_data) < BitTorrentProtocolConstants.HANDSHAKE_LENGTH:
                return

            # Parse handshake
            if (
                handshake_data[0] != BitTorrentProtocolConstants.PROTOCOL_NAME_LENGTH
                or handshake_data[1:20] != BitTorrentProtocolConstants.PROTOCOL_NAME
            ):
                logger.debug(f"❌ Invalid handshake from {client_key}")
                return

            info_hash_start = (
                1 + BitTorrentProtocolConstants.PROTOCOL_NAME_LENGTH + BitTorrentProtocolConstants.RESERVED_BYTES_LENGTH
            )
            info_hash_end = info_hash_start + BitTorrentProtocolConstants.INFOHASH_LENGTH
            info_hash = handshake_data[info_hash_start:info_hash_end]

            # Check if we know this torrent
            if info_hash not in self.known_info_hashes:
                logger.debug(
                    f"❌ Unknown info hash from {client_key}: {info_hash.hex()[:12]}...",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            logger.debug(
                f"✅ Valid handshake from {client_key} for {info_hash.hex()[:12]}...",
                extra={"class_name": self.__class__.__name__},
            )

            # Update UI with handshake completion
            if hasattr(self, "connection_callback") and self.connection_callback:
                client_ip, client_port = client_key.split(":")
                self.connection_callback(
                    "incoming",
                    "update",
                    client_ip,
                    int(client_port),
                    {"handshake_complete": True},
                )

            # Send handshake response
            our_peer_id = (
                BitTorrentProtocolConstants.FAKE_SEEDER_PEER_ID_PREFIX + b"1234567890ab"
            )  # Fake Seeder v0.0.01
            handshake_response = (
                struct.pack("!B", BitTorrentProtocolConstants.PROTOCOL_NAME_LENGTH)  # Protocol name length
                + BitTorrentProtocolConstants.PROTOCOL_NAME  # Protocol string
                + BitTorrentProtocolConstants.RESERVED_BYTES  # Reserved bytes
                + info_hash  # Info hash
                + our_peer_id  # Our peer ID
            )
            writer.write(handshake_response)
            await writer.drain()

            # Send bitfield (claim we have some pieces)
            await self._send_fake_bitfield(writer)

            # Handle ongoing messages
            await self._handle_peer_messages(reader, writer, client_key, info_hash)

        except asyncio.TimeoutError:
            logger.debug(f"⏰ Handshake timeout from {client_key}")

    async def _send_fake_bitfield(self, writer: asyncio.StreamWriter):
        """Send a fake bitfield claiming we have some pieces"""
        # Create a fake bitfield with configurable size
        bitfield = bytearray(self.bitfield_size)

        # Set some random bits to indicate we have those pieces
        import random

        for i in range(0, self.bitfield_size * 8, 8):  # Set every 8th piece
            byte_index = i // 8
            bit_index = i % 8
            if random.random() < self.bitfield_piece_probability:  # Configurable chance to have piece
                bitfield[byte_index] |= 1 << (7 - bit_index)

        # Send bitfield message
        message = struct.pack(">I", len(bitfield) + 1) + bytes([BitTorrentMessage.BITFIELD]) + bytes(bitfield)
        writer.write(message)
        await writer.drain()

    async def _handle_peer_messages(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        client_key: str,
        info_hash: bytes,
    ):
        """Handle ongoing peer protocol messages"""

        while self.running:
            try:
                # Read message length
                length_data = await asyncio.wait_for(reader.read(4), timeout=self.message_read_timeout)
                if len(length_data) != 4:
                    break

                message_length = struct.unpack(">I", length_data)[0]

                # Keep-alive message
                if message_length == BitTorrentProtocolConstants.KEEPALIVE_MESSAGE_LENGTH:
                    logger.debug(f"💓 Keep-alive from {client_key}")
                    continue

                # Read message type and payload
                message_data = await asyncio.wait_for(reader.read(message_length), timeout=self.data_read_timeout)
                if len(message_data) != message_length:
                    break

                message_type = message_data[0]
                payload = (
                    message_data[BitTorrentProtocolConstants.MESSAGE_PAYLOAD_START_OFFSET :]
                    if len(message_data) > BitTorrentProtocolConstants.MESSAGE_ID_LENGTH_BYTES
                    else b""
                )

                await self._handle_message(writer, client_key, message_type, payload)

            except asyncio.TimeoutError:
                # Send keep-alive
                writer.write(struct.pack(">I", 0))
                await writer.drain()

            except Exception as e:
                logger.debug(f"❌ Message handling error for {client_key}: {e}")
                break

    async def _handle_message(
        self,
        writer: asyncio.StreamWriter,
        client_key: str,
        message_type: int,
        payload: bytes,
    ):
        """Handle specific peer protocol messages"""

        if message_type == BitTorrentMessage.INTERESTED:
            logger.debug(f"🤔 Peer {client_key} is interested")
            # Send unchoke
            unchoke_msg = struct.pack(">I", 1) + bytes([BitTorrentMessage.UNCHOKE])
            writer.write(unchoke_msg)
            await writer.drain()

        elif message_type == BitTorrentMessage.REQUEST:
            if len(payload) >= BitTorrentProtocolConstants.REQUEST_PAYLOAD_SIZE:
                piece_index = struct.unpack(">I", payload[0:4])[0]
                offset = struct.unpack(">I", payload[4:8])[0]
                length = struct.unpack(">I", payload[8:12])[0]

                logger.debug(
                    f"📥 Piece request from {client_key}: " f"piece={piece_index}, offset={offset}, length={length}"
                )

                # Send fake piece data (will be rejected due to hash mismatch)
                await self._send_fake_piece(writer, piece_index, offset, length)

        elif message_type == BitTorrentMessage.HAVE:
            if len(payload) >= BitTorrentProtocolConstants.HAVE_PAYLOAD_SIZE:
                piece_index = struct.unpack(">I", payload[0:4])[0]
                logger.debug(f"📦 Peer {client_key} has piece {piece_index}")

        elif message_type == BitTorrentMessage.CHOKE:
            logger.debug(f"🚫 Peer {client_key} choked us")

        elif message_type == BitTorrentMessage.UNCHOKE:
            logger.debug(f"✅ Peer {client_key} unchoked us")

    async def _send_fake_piece(self, writer: asyncio.StreamWriter, piece_index: int, offset: int, length: int):
        """Send fake piece data that will be rejected by hash verification"""

        # Limit length to prevent abuse
        length = min(length, self.max_piece_request_size)  # Configurable max size

        # Create fake data
        fake_data = self.fake_piece_data[:length]

        # Send piece message
        message_header = struct.pack(">I", BitTorrentProtocolConstants.PIECE_MESSAGE_HEADER_SIZE + length)  # Length
        message_type = bytes([BitTorrentMessage.PIECE])  # Type
        piece_header = struct.pack(">II", piece_index, offset)  # Piece index + offset

        full_message = message_header + message_type + piece_header + fake_data

        writer.write(full_message)
        await writer.drain()

        logger.debug(
            f"📤 Sent fake piece to peer: piece={piece_index}, " f"offset={offset}, length={length}",
            extra={"class_name": self.__class__.__name__},
        )

    def get_stats(self) -> Dict:
        """Get server statistics"""
        return {
            "running": self.running,
            "port": self.port,
            "active_connections": len(self.active_connections),
            "total_connections": self.connection_count,
            "known_torrents": len(self.known_info_hashes),
        }
