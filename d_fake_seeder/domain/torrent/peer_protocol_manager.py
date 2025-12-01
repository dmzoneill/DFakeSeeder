"""
BitTorrent Peer Protocol Manager

Manages peer-to-peer connections for a torrent with rate limiting and
connection pooling. Includes protection against excessive peer communication
when users frequently switch between torrents.
"""

# fmt: off
import asyncio
import struct
import threading
import time
from typing import Dict, List, Optional

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.bittorrent_message import BitTorrentMessage
from d_fake_seeder.domain.torrent.peer_connection import PeerConnection
from d_fake_seeder.domain.torrent.peer_info import PeerInfo
from d_fake_seeder.domain.torrent.shared_async_executor import SharedAsyncExecutor
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import (
    AsyncConstants,
    BitTorrentProtocolConstants,
    ConnectionConstants,
    TimeoutConstants,
)

# fmt: on


class PeerProtocolManager:
    """Manages peer-to-peer connections for a torrent"""

    def __init__(
        self,
        info_hash: bytes,
        our_peer_id: bytes,
        max_connections: int = ConnectionConstants.DEFAULT_MAX_PEER_CONNECTIONS,
        connection_callback=None,
    ):
        self.info_hash = info_hash
        self.our_peer_id = our_peer_id
        self.max_connections = max_connections
        self.connection_callback = connection_callback

        # Get settings instance
        self.settings = AppSettings.get_instance()
        peer_protocol = getattr(self.settings, "peer_protocol", {})
        ui_settings = getattr(self.settings, "ui_settings", {})

        # Configurable async sleep intervals
        self.async_sleep_interval = ui_settings.get("async_sleep_interval_seconds", 1.0)
        self.error_sleep_interval = ui_settings.get("error_sleep_interval_seconds", 5.0)
        self.peer_protocol_message_timeout = ui_settings.get("peer_protocol_message_receive_timeout_seconds", 0.1)
        self.manager_thread_join_timeout = ui_settings.get("manager_thread_join_timeout_seconds", 5.0)
        self.metadata_exchange_probability = ui_settings.get("metadata_exchange_probability", 0.3)
        self.fake_piece_count_max = ui_settings.get("fake_piece_count_max", 1000)
        self.connection_cleanup_timeout = ui_settings.get(
            "connection_cleanup_timeout_seconds", 120
        )  # Reduced from 300 to 120 to prevent socket accumulation

        # Connection management
        self.peers: Dict[str, PeerInfo] = {}  # ip:port -> PeerInfo
        self.active_connections: Dict[str, PeerConnection] = {}

        # Use shared async executor instead of per-instance thread pool
        self.executor = SharedAsyncExecutor.get_instance()
        self.manager_id = f"{info_hash.hex()[:16]}"  # Unique ID for task tracking
        self.manager_task: Optional[asyncio.Task] = None

        # Rate limiting - prevent excessive peer communication (use config values)
        self.peer_contact_history: Dict[str, float] = {}  # ip:port -> last_contact_time
        self.min_contact_interval = peer_protocol.get("contact_interval_seconds", 300.0)
        self.startup_grace_period = peer_protocol.get("startup_grace_period_seconds", 60.0)

        # State management (no dedicated thread - using shared executor)
        self.running = False
        self.lock = threading.Lock()
        self.startup_time = time.time()

        # Timing (use config values)
        self.last_peer_scan = 0
        self.keep_alive_interval = peer_protocol.get("keep_alive_interval_seconds", 120.0)
        self.connection_retry_interval = peer_protocol.get("retry_interval_seconds", 30.0)

        # Connection simulation and rotation (use config values)
        self.metadata_exchange_interval = peer_protocol.get("metadata_exchange_interval_seconds", 30.0)
        self.connection_duration = peer_protocol.get("connection_duration_seconds", 300.0)
        self.connection_rotation_percentage = peer_protocol.get("connection_rotation_percentage", 0.25)
        self.last_metadata_exchange = 0.0
        self.last_connection_rotation = 0.0

    def add_peers(self, peer_addresses: List[str]):
        """Add peers from tracker response with rate limiting and max peer limits"""
        with self.lock:
            current_time = time.time()
            added_count = 0
            MAX_PEERS = 1000  # Prevent unbounded growth

            for address in peer_addresses:
                if ":" not in address:
                    continue

                try:
                    ip, port_str = address.rsplit(":", 1)
                    port = int(port_str)

                    # Check rate limiting unless in startup grace period
                    if current_time - self.startup_time > self.startup_grace_period:
                        last_contact = self.peer_contact_history.get(address, 0)
                        if current_time - last_contact < self.min_contact_interval:
                            logger.debug(
                                f"🔒 Rate limited peer {address} "
                                f"(last contact {current_time - last_contact:.1f}s ago)",
                                extra={"class_name": self.__class__.__name__},
                            )
                            continue

                    # Enforce max peer limit - remove oldest peer if at limit
                    if address not in self.peers:
                        if len(self.peers) >= MAX_PEERS:
                            # Remove oldest peer
                            oldest_address = min(self.peers.items(), key=lambda x: x[1].last_seen)[0]
                            del self.peers[oldest_address]
                            if oldest_address in self.peer_contact_history:
                                del self.peer_contact_history[oldest_address]
                            logger.debug(
                                f"🗑️ Removed oldest peer {oldest_address} to make room (max: {MAX_PEERS})",
                                extra={"class_name": self.__class__.__name__},
                            )

                        self.peers[address] = PeerInfo(ip=ip, port=port, last_seen=current_time)
                        added_count += 1
                        logger.debug(
                            f"➕ Added peer {address}",
                            extra={"class_name": self.__class__.__name__},
                        )
                    else:
                        # Update last seen time
                        self.peers[address].last_seen = current_time

                except ValueError:
                    logger.debug(
                        f"❌ Invalid peer address format: {address}",
                        extra={"class_name": self.__class__.__name__},
                    )

            if added_count > 0:
                logger.debug(
                    f"📋 Added {added_count} new peers "
                    f"(total: {len(self.peers)}, active: {len(self.active_connections)})",
                    extra={"class_name": self.__class__.__name__},
                )

    def start(self):
        """Start the peer protocol manager using shared executor"""
        if self.running:
            return

        self.running = True

        # Submit async loop to shared executor
        self.manager_task = self.executor.submit_coroutine(self._async_manager_loop(), manager_id=self.manager_id)

        if self.manager_task is None:
            logger.error(
                f"❌ Failed to submit task to SharedAsyncExecutor for {self.manager_id}",
                extra={"class_name": self.__class__.__name__},
            )
            self.running = False
            return

        logger.debug(
            f"🚀 Started PeerProtocolManager via SharedAsyncExecutor "
            f"(manager_id: {self.manager_id}, max_connections: {self.max_connections})",
            extra={"class_name": self.__class__.__name__},
        )

    def stop(self):
        """Stop the peer protocol manager"""
        if not self.running:
            return

        logger.debug(
            f"🛑 Stopping PeerProtocolManager (manager_id: {self.manager_id})",
            extra={"class_name": self.__class__.__name__},
        )

        self.running = False

        # Cancel all tasks for this manager via shared executor
        self.executor.cancel_manager_tasks(self.manager_id)

        # Close all active connections
        with self.lock:
            for connection in self.active_connections.values():
                connection.close()
            self.active_connections.clear()

        logger.debug(
            f"✅ PeerProtocolManager stopped (manager_id: {self.manager_id})",
            extra={"class_name": self.__class__.__name__},
        )

    async def _async_manager_loop(self):
        """Async manager loop with proper cancellation"""
        logger.debug(
            "🔄 PeerProtocolManager loop started",
            extra={"class_name": self.__class__.__name__},
        )

        try:
            while self.running:
                try:
                    current_time = time.time()

                    # Check for shutdown more frequently
                    if not self.running:
                        break

                    # Manage connections with cancellation checks and timeout
                    await asyncio.wait_for(
                        self._manage_connections(current_time),
                        timeout=AsyncConstants.MANAGE_CONNECTIONS_TIMEOUT,
                    )

                    if not self.running:
                        break

                    # Send keep-alive messages with timeout
                    await asyncio.wait_for(
                        self._send_keep_alives(current_time),
                        timeout=AsyncConstants.SEND_KEEP_ALIVES_TIMEOUT,
                    )

                    if not self.running:
                        break

                    # Poll peer status with timeout
                    await asyncio.wait_for(
                        self._poll_peer_status(),
                        timeout=AsyncConstants.POLL_PEER_STATUS_TIMEOUT,
                    )

                    if not self.running:
                        break

                    # Exchange metadata with timeout
                    await asyncio.wait_for(
                        self._exchange_metadata(current_time),
                        timeout=AsyncConstants.EXCHANGE_METADATA_TIMEOUT,
                    )

                    if not self.running:
                        break

                    # Rotate connections with timeout
                    await asyncio.wait_for(
                        self._rotate_connections(current_time),
                        timeout=AsyncConstants.ROTATE_CONNECTIONS_TIMEOUT,
                    )

                    if not self.running:
                        break

                    # Clean up connections with timeout
                    await asyncio.wait_for(
                        self._cleanup_connections(current_time),
                        timeout=AsyncConstants.CLEANUP_CONNECTIONS_TIMEOUT,
                    )

                    # Use shorter sleep with cancellation checks
                    sleep_duration = self.async_sleep_interval
                    sleep_chunks = max(
                        1,
                        int(sleep_duration / TimeoutConstants.PEER_MANAGER_SLEEP_CHUNK),
                    )
                    for _ in range(sleep_chunks):
                        if not self.running:
                            return
                        await asyncio.sleep(TimeoutConstants.PEER_MANAGER_SLEEP_CHUNK)

                except asyncio.TimeoutError:
                    # Timeout is expected during shutdown
                    if not self.running:
                        break
                    logger.debug(
                        "⏱️ Operation timeout in peer manager loop",
                        extra={"class_name": self.__class__.__name__},
                    )
                except Exception as e:
                    logger.error(
                        f"❌ Error in peer manager loop: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    if not self.running:
                        break
                    # Shorter error sleep with cancellation check
                    error_sleep_chunks = max(
                        1,
                        int(self.error_sleep_interval / TimeoutConstants.PEER_MANAGER_SLEEP_CHUNK),
                    )
                    for _ in range(error_sleep_chunks):
                        if not self.running:
                            return
                        await asyncio.sleep(TimeoutConstants.PEER_MANAGER_SLEEP_CHUNK)

        except asyncio.CancelledError:
            logger.debug(
                "🛑 PeerProtocolManager async loop cancelled",
                extra={"class_name": self.__class__.__name__},
            )
        finally:
            logger.debug(
                "🛑 PeerProtocolManager loop stopped",
                extra={"class_name": self.__class__.__name__},
            )

    async def _manage_connections(self, current_time: float):
        """Manage peer connections with rate limiting"""
        with self.lock:
            peers_list = list(self.peers.items())
            active_count = len(self.active_connections)

        # Don't exceed max connections
        if active_count >= self.max_connections:
            return

        # Try to connect to peers we're not connected to
        for address, peer_info in peers_list:
            if address in self.active_connections:
                continue

            # Check rate limiting
            last_contact = self.peer_contact_history.get(address, 0)
            if (
                current_time - self.startup_time > self.startup_grace_period
                and current_time - last_contact < self.min_contact_interval
            ):
                continue

            # Check if enough time has passed since last connection attempt
            if current_time - peer_info.last_connected < self.connection_retry_interval:
                continue

            # Try to connect with proper cleanup
            connection = PeerConnection(peer_info, self.info_hash, self.our_peer_id, self.connection_callback)
            connection_success = False

            try:
                if await connection.connect():
                    if await connection.perform_handshake():
                        # Successful connection
                        with self.lock:
                            self.active_connections[address] = connection
                            # Update contact history
                            self.peer_contact_history[address] = current_time

                        logger.debug(
                            f"✅ Connected to peer {address}",
                            extra={"class_name": self.__class__.__name__},
                        )

                        # Send interested message
                        await connection.send_message(BitTorrentMessage.INTERESTED)
                        connection_success = True
                    else:
                        # Handshake failed - close connection
                        logger.debug(
                            f"🔒 Handshake failed with {address}",
                            extra={"class_name": self.__class__.__name__},
                        )
                else:
                    # Connection failed - increment attempts
                    peer_info.connection_attempts += 1
                    logger.debug(
                        f"❌ Connection failed to {address} (attempt {peer_info.connection_attempts})",
                        extra={"class_name": self.__class__.__name__},
                    )
            except Exception as e:
                logger.debug(
                    f"❌ Error connecting to {address}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
            finally:
                # CRITICAL FIX: Always close connection if not successfully established
                # This prevents socket leaks when connections fail
                if not connection_success:
                    connection.close()

            # Don't try to connect to too many at once
            with self.lock:
                if len(self.active_connections) >= self.max_connections:
                    break

    async def _send_keep_alives(self, current_time: float):
        """Send keep-alive messages to maintain connections"""
        with self.lock:
            connections_list = list(self.active_connections.items())

        for address, connection in connections_list:
            if current_time - connection.last_message_time > self.keep_alive_interval:
                if not await connection.send_keep_alive():
                    # Connection failed, remove it
                    with self.lock:
                        if address in self.active_connections:
                            del self.active_connections[address]
                    connection.close()

    async def _poll_peer_status(self):
        """Poll peers for their status"""
        with self.lock:
            connections_list = list(self.active_connections.items())

        connections_to_remove = []

        for address, connection in connections_list:
            try:
                # Try to receive any pending messages
                message = await connection.receive_message(timeout=self.peer_protocol_message_timeout)
                if message:
                    message_id, payload = message
                    await self._handle_peer_message(address, connection, message_id, payload)
                elif message is None:
                    # Connection closed by peer - mark for removal
                    logger.debug(
                        f"🔌 Connection closed by peer {address}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    connections_to_remove.append((address, connection))

            except Exception as e:
                logger.debug(
                    f"❌ Error polling peer {address}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                # Connection is broken - mark for removal
                connections_to_remove.append((address, connection))

        # Clean up failed connections
        for address, connection in connections_to_remove:
            with self.lock:
                if address in self.active_connections:
                    del self.active_connections[address]
            connection.close()
            logger.debug(
                f"🗑️ Removed failed connection to {address}",
                extra={"class_name": self.__class__.__name__},
            )

    async def _handle_peer_message(self, address: str, connection: PeerConnection, message_id: int, payload: bytes):
        """Handle incoming peer message"""
        if message_id == -1:  # Keep-alive
            logger.debug(f"💓 Keep-alive from {address}")
            return

        if message_id == BitTorrentMessage.BITFIELD:
            # Peer sent their bitfield (which pieces they have)
            connection.peer_info.has_pieces = payload
            progress = self._calculate_progress_from_bitfield(payload)
            connection.peer_info.progress = progress
            connection.peer_info.is_seed = progress >= 1.0

            logger.debug(
                f"📋 Bitfield from {address}: {progress:.1%} complete",
                extra={"class_name": self.__class__.__name__},
            )

        elif message_id == BitTorrentMessage.HAVE:
            # Peer has a new piece
            if len(payload) >= BitTorrentProtocolConstants.HAVE_PAYLOAD_SIZE:
                piece_index = struct.unpack("!I", payload[: BitTorrentProtocolConstants.HAVE_PAYLOAD_SIZE])[0]
                logger.debug(f"📦 Peer {address} has piece {piece_index}")

        elif message_id == BitTorrentMessage.CHOKE:
            connection.peer_info.choked = True
            logger.debug(f"🚫 Choked by {address}")

        elif message_id == BitTorrentMessage.UNCHOKE:
            connection.peer_info.choked = False
            logger.debug(f"✅ Unchoked by {address}")

    def _calculate_progress_from_bitfield(self, bitfield: bytes) -> float:
        """Calculate download progress from bitfield"""
        if not bitfield:
            return 0.0

        total_bits = len(bitfield) * 8
        set_bits = 0

        for byte in bitfield:
            set_bits += bin(byte).count("1")

        return set_bits / total_bits if total_bits > 0 else 0.0

    async def _cleanup_connections(self, current_time: float):
        """Clean up dead or old connections, peers, and contact history"""
        to_remove_connections = []
        to_remove_peers = []
        to_remove_history = []

        # Clean up stale connections
        with self.lock:
            for address, connection in self.active_connections.items():
                # Remove connections that haven't communicated in a while
                if (
                    current_time - connection.last_message_time > self.connection_cleanup_timeout
                ):  # Configurable timeout
                    to_remove_connections.append(address)
                    connection.close()

            for address in to_remove_connections:
                if address in self.active_connections:
                    del self.active_connections[address]
                    logger.debug(
                        f"🗑️ Cleaned up stale connection to {address}",
                        extra={"class_name": self.__class__.__name__},
                    )

        # Clean up old inactive peers (not seen in 24 hours)
        PEER_EXPIRY_SECONDS = 86400  # 24 hours
        with self.lock:
            for address, peer_info in self.peers.items():
                if current_time - peer_info.last_seen > PEER_EXPIRY_SECONDS:
                    to_remove_peers.append(address)

            for address in to_remove_peers:
                del self.peers[address]
                if address in self.peer_contact_history:
                    del self.peer_contact_history[address]

            if to_remove_peers:
                logger.debug(
                    f"🗑️ Cleaned up {len(to_remove_peers)} old peers (not seen in 24h)",
                    extra={"class_name": self.__class__.__name__},
                )

        # Clean up old contact history entries (keep last 30 days)
        HISTORY_EXPIRY_SECONDS = 2592000  # 30 days
        with self.lock:
            for address, last_contact in self.peer_contact_history.items():
                if current_time - last_contact > HISTORY_EXPIRY_SECONDS:
                    to_remove_history.append(address)

            for address in to_remove_history:
                del self.peer_contact_history[address]

            if to_remove_history:
                logger.debug(
                    f"🗑️ Cleaned up {len(to_remove_history)} old contact history entries",
                    extra={"class_name": self.__class__.__name__},
                )

    def get_peer_stats(self) -> Dict[str, Dict]:
        """Get current peer statistics"""
        stats = {}

        with self.lock:
            for address, peer_info in self.peers.items():
                stats[address] = {
                    "ip": peer_info.ip,
                    "port": peer_info.port,
                    "connected": address in self.active_connections,
                    "client": peer_info.client_name or "Unknown",
                    "progress": peer_info.progress,
                    "is_seed": peer_info.is_seed,
                    "choked": peer_info.choked,
                    "last_seen": peer_info.last_seen,
                    "download_speed": peer_info.download_speed,
                    "upload_speed": peer_info.upload_speed,
                }

        return stats

    async def _exchange_metadata(self, current_time: float):
        """Exchange metadata with connected peers (simulate activity)"""
        if current_time - self.last_metadata_exchange < self.metadata_exchange_interval:
            return

        with self.lock:
            connections_list = list(self.active_connections.items())

        for address, connection in connections_list:
            try:
                # Send harmless metadata messages to simulate activity
                # These are legitimate BitTorrent protocol messages

                # Send bitfield message (what pieces we "have")
                bitfield = (
                    b"\x00" * BitTorrentProtocolConstants.FAKE_BITFIELD_SIZE_BYTES
                )  # Fake bitfield - all zeros (we have no pieces)
                await connection.send_message(BitTorrentMessage.BITFIELD, bitfield)

                # Send have messages occasionally (claiming to have pieces)
                # This simulates progress without transferring data
                import random

                if random.random() < self.metadata_exchange_probability:  # Configurable chance
                    piece_index = random.randint(0, self.fake_piece_count_max)  # Configurable fake piece number
                    piece_data = struct.pack(">I", piece_index)
                    await connection.send_message(BitTorrentMessage.HAVE, piece_data)

                logger.debug(
                    f"📊 Exchanged metadata with {address}",
                    extra={"class_name": self.__class__.__name__},
                )

            except Exception as e:
                logger.debug(
                    f"❌ Error exchanging metadata with {address}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        self.last_metadata_exchange = current_time

    async def _rotate_connections(self, current_time: float):
        """Rotate connections periodically to simulate real peer behavior"""
        if current_time - self.last_connection_rotation < self.connection_duration:
            return

        with self.lock:
            connections_list = list(self.active_connections.items())

        # Disconnect some random connections to make room for new ones
        if len(connections_list) > self.max_connections // 2:
            import random

            disconnect_count = int(len(connections_list) * self.connection_rotation_percentage)
            connections_to_disconnect = random.sample(connections_list, disconnect_count)

            for address, connection in connections_to_disconnect:
                logger.debug(
                    f"🔄 Rotating connection to {address}",
                    extra={"class_name": self.__class__.__name__},
                )
                connection.close()
                with self.lock:
                    if address in self.active_connections:
                        del self.active_connections[address]

        self.last_connection_rotation = current_time
