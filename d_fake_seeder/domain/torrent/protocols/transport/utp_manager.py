"""
µTP Connection Manager

Manages multiple µTP connections and provides connection pooling.
"""

# fmt: off
import asyncio
import socket
from typing import Dict, Optional, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import UTPConstants

from .utp_connection import UTPConnection

# fmt: on


class UTPManager:
    """Manages µTP connections"""

    def __init__(self, port: int = 0):
        """
        Initialize µTP manager

        Args:
            port: UDP port to listen on (0 for random port)
        """
        self.port = port
        self.settings = AppSettings.get_instance()

        # Socket and connections
        self.socket = None
        self.running = False
        self.connections: Dict[int, UTPConnection] = {}  # connection_id -> UTPConnection
        self.next_connection_id = 1

        # Configuration
        utp_config = getattr(self.settings, "protocols", {}).get("transport", {}).get("utp", {})
        self.enabled = utp_config.get("enabled", True)
        self.max_connections = utp_config.get("max_connections", 100)

        logger.debug(
            "µTP Manager initialized",
            extra={"class_name": self.__class__.__name__, "port": port},
        )

    async def start(self) -> bool:
        """
        Start µTP manager

        Returns:
            True if started successfully
        """
        if not self.enabled:
            logger.info(
                "µTP disabled in settings",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            logger.debug("Starting µTP manager", extra={"class_name": self.__class__.__name__})

            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind(("0.0.0.0", self.port))
            self.socket.setblocking(False)

            # Get actual port if random was chosen
            if self.port == 0:
                self.port = self.socket.getsockname()[1]

            self.running = True

            # Start listening loop
            asyncio.create_task(self._listen_loop())

            logger.debug(
                f"µTP manager started on port {self.port}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to start µTP manager: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def stop(self):
        """Stop µTP manager"""
        logger.debug("Stopping µTP manager", extra={"class_name": self.__class__.__name__})

        self.running = False

        # Close all connections
        for conn in list(self.connections.values()):
            await conn.close()

        self.connections.clear()

        # Close socket
        if self.socket:
            self.socket.close()
            self.socket = None

    async def connect(self, host: str, port: int, timeout: float = 30.0) -> Optional[UTPConnection]:
        """
        Create outgoing µTP connection

        Args:
            host: Remote host
            port: Remote port
            timeout: Connection timeout

        Returns:
            UTPConnection instance if successful, None otherwise
        """
        if not self.running:
            logger.warning(
                "Cannot connect, µTP manager not running",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        if len(self.connections) >= self.max_connections:
            logger.warning(
                "Maximum µTP connections reached",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        try:
            # Create connection
            connection_id = self._get_next_connection_id()
            remote_addr = (host, port)

            connection = UTPConnection(connection_id, remote_addr, self.socket)
            self.connections[connection_id] = connection

            # Initiate connection
            success = await connection.connect(timeout)

            if success:
                logger.debug(
                    f"µTP connection established to {host}:{port}",
                    extra={"class_name": self.__class__.__name__},
                )
                return connection
            else:
                # Connection failed, remove it
                del self.connections[connection_id]
                return None

        except Exception as e:
            logger.error(
                f"Failed to create µTP connection: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    async def _listen_loop(self):
        """Main listening loop for incoming packets"""
        while self.running:
            try:
                # Receive packet
                data, addr = await asyncio.get_running_loop().sock_recvfrom(self.socket, UTPConstants.MAX_PACKET_SIZE)

                # Route to appropriate connection
                asyncio.create_task(self._route_packet(data, addr))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"µTP listen error: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                await asyncio.sleep(0.1)

    async def _route_packet(self, data: bytes, addr: Tuple[str, int]):
        """
        Route incoming packet to appropriate connection

        Args:
            data: Packet data
            addr: Source address
        """
        try:
            # Parse connection ID from packet header (bytes 2-3)
            if len(data) < 4:
                return

            connection_id = int.from_bytes(data[2:4], byteorder="big")

            # Find connection
            if connection_id in self.connections:
                connection = self.connections[connection_id]
                await connection.handle_packet(data, addr)
            else:
                # New incoming connection (SYN packet)
                # Check packet type (bits 0-3 of first byte)
                packet_type = data[0] & UTPConstants.PACKET_TYPE_MASK
                if packet_type == 4:  # ST_SYN
                    await self._accept_connection(data, addr, connection_id)

        except Exception as e:
            logger.error(
                f"Error routing µTP packet: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    async def _accept_connection(self, data: bytes, addr: Tuple[str, int], connection_id: int):
        """
        Accept incoming µTP connection

        Args:
            data: SYN packet data
            addr: Remote address
            connection_id: Connection identifier
        """
        if len(self.connections) >= self.max_connections:
            logger.warning(
                "Cannot accept µTP connection, max connections reached",
                extra={"class_name": self.__class__.__name__},
            )
            return

        try:
            # Create connection
            connection = UTPConnection(connection_id, addr, self.socket)
            self.connections[connection_id] = connection

            # Handle SYN packet
            await connection.handle_packet(data, addr)

            logger.debug(
                f"Accepted µTP connection from {addr}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to accept µTP connection: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _get_next_connection_id(self) -> int:
        """Get next available connection ID"""
        connection_id = self.next_connection_id
        self.next_connection_id = (self.next_connection_id + 1) % UTPConstants.MAX_SEQUENCE_NUMBER
        return connection_id

    def remove_connection(self, connection_id: int):
        """
        Remove connection from manager

        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.connections:
            del self.connections[connection_id]

    def get_statistics(self) -> Dict:
        """Get µTP manager statistics"""
        connection_stats = [conn.get_statistics() for conn in self.connections.values()]

        total_bytes_sent = sum(s["bytes_sent"] for s in connection_stats)
        total_bytes_received = sum(s["bytes_received"] for s in connection_stats)

        return {
            "enabled": self.enabled,
            "running": self.running,
            "port": self.port,
            "active_connections": len(self.connections),
            "max_connections": self.max_connections,
            "total_bytes_sent": total_bytes_sent,
            "total_bytes_received": total_bytes_received,
            "connections": connection_stats,
        }

    def is_enabled(self) -> bool:
        """Check if µTP is enabled"""
        return self.enabled

    def is_running(self) -> bool:
        """Check if µTP manager is running"""
        return self.running
