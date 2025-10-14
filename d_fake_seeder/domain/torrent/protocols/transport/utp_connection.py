"""
µTP (Micro Transport Protocol) Implementation (BEP-029)

Implements the µTorrent Transport Protocol for NAT-friendly peer connections.
Provides congestion control and connection multiplexing over UDP.
"""

import asyncio
import random
import struct
import time
from enum import IntEnum
from typing import Dict, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import UTPConstants


class UTPPacketType(IntEnum):
    """µTP packet types"""

    ST_DATA = 0  # Data packet
    ST_FIN = 1  # Finish connection
    ST_STATE = 2  # State packet (ACK)
    ST_RESET = 3  # Reset connection
    ST_SYN = 4  # Synchronize, initiating connection


class UTPConnection:
    """µTP connection implementation"""

    def __init__(self, connection_id: int, remote_addr: Tuple[str, int], socket):
        """
        Initialize µTP connection

        Args:
            connection_id: Connection identifier
            remote_addr: Remote (IP, port) tuple
            socket: UDP socket for sending/receiving
        """
        self.connection_id = connection_id
        self.remote_addr = remote_addr
        self.socket = socket
        self.settings = AppSettings.get_instance()

        # Connection state
        self.state = "IDLE"  # IDLE, SYN_SENT, CONNECTED, FIN_SENT, CLOSED
        self.seq_nr = random.randint(1, UTPConstants.MAX_RANDOM_SEQUENCE)  # Sequence number
        self.ack_nr = 0  # Acknowledgment number
        self.recv_window = UTPConstants.DEFAULT_WINDOW_SIZE  # Receive window size
        self.send_window = UTPConstants.DEFAULT_WINDOW_SIZE  # Send window size

        # Timing and congestion control
        self.rtt = 0.0  # Round-trip time
        self.rtt_variance = 0.0
        self.timeout = UTPConstants.INITIAL_TIMEOUT_MS / 1000.0
        self.last_packet_time = 0.0
        self.base_delay = 0.0

        # Packet tracking
        self.sent_packets: Dict[int, Dict] = {}  # seq_nr -> packet_info
        self.recv_buffer: Dict[int, bytes] = {}  # seq_nr -> data
        self.out_of_order_packets: Dict[int, bytes] = {}

        # Statistics
        self.bytes_sent = 0
        self.bytes_received = 0
        self.packets_sent = 0
        self.packets_received = 0
        self.retransmits = 0

        # Configuration from settings
        utp_config = getattr(self.settings, "protocols", {}).get("transport", {}).get("utp", {})
        self.max_window_size = utp_config.get("max_window_size", UTPConstants.MAX_WINDOW_SIZE)
        self.min_window_size = utp_config.get("min_window_size", UTPConstants.MIN_WINDOW_SIZE)
        self.target_delay_ms = utp_config.get("target_delay_ms", UTPConstants.TARGET_DELAY_MS)

        logger.debug(
            "µTP connection initialized",
            extra={
                "class_name": self.__class__.__name__,
                "connection_id": connection_id,
                "remote_addr": remote_addr,
            },
        )

    async def connect(self, timeout: float = 30.0) -> bool:
        """
        Initiate µTP connection

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connection established successfully
        """
        try:
            logger.info(
                f"Initiating µTP connection to {self.remote_addr}", extra={"class_name": self.__class__.__name__}
            )

            # Send SYN packet
            self.state = "SYN_SENT"
            await self._send_syn()

            # Wait for STATE packet (ACK of SYN)
            start_time = time.time()
            while self.state != "CONNECTED" and time.time() - start_time < timeout:
                await asyncio.sleep(0.1)

                # Retransmit SYN if needed
                if time.time() - self.last_packet_time > self.timeout:
                    await self._send_syn()

            if self.state == "CONNECTED":
                logger.info("µTP connection established", extra={"class_name": self.__class__.__name__})
                return True
            else:
                logger.warning("µTP connection timeout", extra={"class_name": self.__class__.__name__})
                return False

        except Exception as e:
            logger.error(f"Failed to connect via µTP: {e}", extra={"class_name": self.__class__.__name__})
            return False

    async def send_data(self, data: bytes) -> bool:
        """
        Send data over µTP connection

        Args:
            data: Data to send

        Returns:
            True if data was sent successfully
        """
        if self.state != "CONNECTED":
            logger.warning(
                "Cannot send data, connection not established", extra={"class_name": self.__class__.__name__}
            )
            return False

        try:
            # Fragment data into packets if needed
            max_payload = UTPConstants.MAX_PACKET_SIZE - UTPConstants.HEADER_SIZE
            offset = 0

            while offset < len(data):
                chunk = data[offset : offset + max_payload]
                await self._send_data_packet(chunk)
                offset += max_payload

            return True

        except Exception as e:
            logger.error(f"Failed to send data: {e}", extra={"class_name": self.__class__.__name__})
            return False

    async def close(self):
        """Close µTP connection gracefully"""
        if self.state == "CLOSED":
            return

        try:
            logger.debug("Closing µTP connection", extra={"class_name": self.__class__.__name__})

            # Send FIN packet
            self.state = "FIN_SENT"
            await self._send_fin()

            # Wait briefly for ACK
            await asyncio.sleep(0.5)

            self.state = "CLOSED"

        except Exception as e:
            logger.error(f"Error closing µTP connection: {e}", extra={"class_name": self.__class__.__name__})
            self.state = "CLOSED"

    async def handle_packet(self, packet: bytes, addr: Tuple[str, int]):
        """
        Handle incoming µTP packet

        Args:
            packet: Received packet data
            addr: Source address
        """
        try:
            # Parse packet header
            if len(packet) < UTPConstants.HEADER_SIZE:
                return

            header = self._parse_header(packet)
            packet_type = header["type"]
            payload = packet[UTPConstants.HEADER_SIZE :]

            self.packets_received += 1
            self.last_packet_time = time.time()

            # Handle different packet types
            if packet_type == UTPPacketType.ST_SYN:
                await self._handle_syn(header, addr)
            elif packet_type == UTPPacketType.ST_STATE:
                await self._handle_state(header)
            elif packet_type == UTPPacketType.ST_DATA:
                await self._handle_data(header, payload)
            elif packet_type == UTPPacketType.ST_FIN:
                await self._handle_fin(header)
            elif packet_type == UTPPacketType.ST_RESET:
                await self._handle_reset(header)

            # Update RTT and congestion window
            self._update_rtt(header)
            self._update_congestion_window(header)

        except Exception as e:
            logger.error(f"Error handling µTP packet: {e}", extra={"class_name": self.__class__.__name__})

    async def _send_syn(self):
        """Send SYN packet to initiate connection"""
        packet = self._create_packet(UTPPacketType.ST_SYN, b"")
        await self._send_packet(packet)
        self.last_packet_time = time.time()

    async def _send_data_packet(self, data: bytes):
        """Send DATA packet"""
        self.seq_nr = (self.seq_nr + 1) % UTPConstants.MAX_SEQUENCE_NUMBER
        packet = self._create_packet(UTPPacketType.ST_DATA, data)
        await self._send_packet(packet)

        # Track sent packet for retransmission
        self.sent_packets[self.seq_nr] = {"data": data, "timestamp": time.time(), "retransmits": 0}

    async def _send_fin(self):
        """Send FIN packet to close connection"""
        packet = self._create_packet(UTPPacketType.ST_FIN, b"")
        await self._send_packet(packet)

    async def _send_state(self):
        """Send STATE packet (ACK)"""
        packet = self._create_packet(UTPPacketType.ST_STATE, b"")
        await self._send_packet(packet)

    async def _send_packet(self, packet: bytes):
        """Send packet via UDP socket"""
        try:
            if self.socket:
                await asyncio.get_running_loop().sock_sendto(self.socket, packet, self.remote_addr)
                self.packets_sent += 1
                self.bytes_sent += len(packet)
        except Exception as e:
            logger.error(f"Failed to send µTP packet: {e}", extra={"class_name": self.__class__.__name__})
            raise

    def _create_packet(self, packet_type: UTPPacketType, payload: bytes) -> bytes:
        """
        Create µTP packet

        Args:
            packet_type: Type of packet
            payload: Packet payload

        Returns:
            Complete packet bytes
        """
        # µTP packet header format (20 bytes):
        # - version (4 bits) + type (4 bits)
        # - extension (8 bits)
        # - connection_id (16 bits)
        # - timestamp_microseconds (32 bits)
        # - timestamp_difference_microseconds (32 bits)
        # - wnd_size (32 bits)
        # - seq_nr (16 bits)
        # - ack_nr (16 bits)

        version = 1
        extension = 0
        timestamp_us = int(time.time() * UTPConstants.MICROSECONDS_PER_SECOND) & UTPConstants.VERSION_TYPE_MASK
        timestamp_diff_us = 0

        header = struct.pack(
            ">BBHIIIHH",
            (version << 4) | packet_type,
            extension,
            self.connection_id,
            timestamp_us,
            timestamp_diff_us,
            self.recv_window,
            self.seq_nr,
            self.ack_nr,
        )

        return header + payload

    def _parse_header(self, packet: bytes) -> Dict:
        """Parse µTP packet header"""
        if len(packet) < UTPConstants.HEADER_SIZE:
            return {}

        (
            version_type,
            extension,
            connection_id,
            timestamp_us,
            timestamp_diff_us,
            wnd_size,
            seq_nr,
            ack_nr,
        ) = struct.unpack(">BBHIIIHH", packet[: UTPConstants.HEADER_SIZE])

        version = (version_type >> UTPConstants.VERSION_SHIFT) & UTPConstants.VERSION_MASK
        packet_type = version_type & UTPConstants.PACKET_TYPE_MASK

        return {
            "version": version,
            "type": packet_type,
            "extension": extension,
            "connection_id": connection_id,
            "timestamp_us": timestamp_us,
            "timestamp_diff_us": timestamp_diff_us,
            "wnd_size": wnd_size,
            "seq_nr": seq_nr,
            "ack_nr": ack_nr,
        }

    async def _handle_syn(self, header: Dict, addr: Tuple[str, int]):
        """Handle incoming SYN packet (server side)"""
        # Accept connection
        self.connection_id = header["connection_id"] + 1
        self.ack_nr = header["seq_nr"]
        self.state = "CONNECTED"

        # Send STATE (ACK)
        await self._send_state()

        logger.info("µTP connection accepted", extra={"class_name": self.__class__.__name__})

    async def _handle_state(self, header: Dict):
        """Handle STATE packet (ACK)"""
        if self.state == "SYN_SENT":
            # SYN was acknowledged
            self.ack_nr = header["seq_nr"]
            self.state = "CONNECTED"

        # Update send window
        self.send_window = header["wnd_size"]

        # Remove acknowledged packets from sent buffer
        ack_nr = header["ack_nr"]
        self.sent_packets = {seq: data for seq, data in self.sent_packets.items() if seq > ack_nr}

    async def _handle_data(self, header: Dict, payload: bytes):
        """Handle DATA packet"""
        if self.state != "CONNECTED":
            return

        seq_nr = header["seq_nr"]
        self.bytes_received += len(payload)

        # Store in receive buffer
        self.recv_buffer[seq_nr] = payload

        # Update ack_nr
        self.ack_nr = seq_nr

        # Send STATE (ACK)
        await self._send_state()

    async def _handle_fin(self, header: Dict):
        """Handle FIN packet"""
        # Send final STATE (ACK)
        await self._send_state()
        self.state = "CLOSED"

        logger.debug("µTP connection closed by peer", extra={"class_name": self.__class__.__name__})

    async def _handle_reset(self, header: Dict):
        """Handle RESET packet"""
        self.state = "CLOSED"
        logger.warning("µTP connection reset by peer", extra={"class_name": self.__class__.__name__})

    def _update_rtt(self, header: Dict):
        """Update RTT estimate"""
        if header.get("timestamp_diff_us"):
            rtt_sample = header["timestamp_diff_us"] / UTPConstants.MICROSECONDS_PER_SECOND  # Convert to seconds

            if self.rtt == 0:
                # First sample
                self.rtt = rtt_sample
                self.rtt_variance = rtt_sample / 2
            else:
                # Exponential moving average
                delta = abs(rtt_sample - self.rtt)
                self.rtt_variance = (
                    UTPConstants.RTT_VARIANCE_SMOOTHING * self.rtt_variance + UTPConstants.RTT_VARIANCE_WEIGHT * delta
                )
                self.rtt = UTPConstants.RTT_SMOOTHING_FACTOR * self.rtt + UTPConstants.RTT_SAMPLE_WEIGHT * rtt_sample

            # Update timeout
            self.timeout = max(
                self.rtt + UTPConstants.RTT_TIMEOUT_MULTIPLIER * self.rtt_variance,
                UTPConstants.MIN_TIMEOUT_MS / UTPConstants.MILLISECONDS_PER_SECOND,
            )

    def _update_congestion_window(self, header: Dict):
        """Update congestion window based on delay"""
        try:
            # Calculate current delay
            if header.get("timestamp_diff_us"):
                current_delay_ms = header["timestamp_diff_us"] / UTPConstants.MILLISECONDS_PER_SECOND

                # LEDBAT congestion control
                if self.base_delay == 0:
                    self.base_delay = current_delay_ms
                else:
                    self.base_delay = min(self.base_delay, current_delay_ms)

                queuing_delay = current_delay_ms - self.base_delay
                target_delay = self.target_delay_ms

                # Adjust window based on delay
                if queuing_delay < target_delay:
                    # Increase window (slow start/congestion avoidance)
                    self.send_window = min(self.send_window + UTPConstants.WINDOW_INCREASE_STEP, self.max_window_size)
                else:
                    # Decrease window (congestion detected)
                    self.send_window = max(self.send_window - UTPConstants.WINDOW_DECREASE_STEP, self.min_window_size)

        except Exception as e:
            logger.error(f"Error updating congestion window: {e}", extra={"class_name": self.__class__.__name__})

    def get_statistics(self) -> Dict:
        """Get connection statistics"""
        return {
            "state": self.state,
            "connection_id": self.connection_id,
            "remote_addr": self.remote_addr,
            "bytes_sent": self.bytes_sent,
            "bytes_received": self.bytes_received,
            "packets_sent": self.packets_sent,
            "packets_received": self.packets_received,
            "retransmits": self.retransmits,
            "rtt": self.rtt,
            "send_window": self.send_window,
            "recv_window": self.recv_window,
        }
