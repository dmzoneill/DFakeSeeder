"""
Metadata Extension (BEP-009)

Extension for Peers to Send Metadata Files.
Allows peers to exchange torrent metadata for magnet links.
"""

# fmt: off
import math
import struct
from typing import Dict, Optional

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import (
    BitTorrentProtocolConstants,
    ProtocolConstants,
)

try:
    import bencodepy as bencode
except ImportError:
    from d_fake_seeder.domain.torrent.bencoding import bencode

# fmt: on


class MetadataExtension:
    """Metadata extension implementation (BEP-009)"""

    # Message types
    REQUEST = 0
    DATA = 1
    REJECT = 2

    def __init__(self, extension_manager, peer_connection):
        """
        Initialize metadata extension

        Args:
            extension_manager: ExtensionManager instance
            peer_connection: PeerConnection instance
        """
        self.extension_manager = extension_manager
        self.peer_connection = peer_connection
        self.settings = AppSettings.get_instance()

        # Metadata state
        self.metadata: Optional[bytes] = None
        self.metadata_size = 0
        self.piece_size = ProtocolConstants.PIECE_SIZE_DEFAULT
        self.pieces_count = 0
        self.received_pieces: Dict[int, bytes] = {}
        self.requested_pieces: set = set()

        # For fake seeding - generate synthetic metadata if needed
        self.generate_synthetic_metadata = True

        logger.debug(
            "Metadata extension initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def initialize(self):
        """Initialize metadata extension after handshake"""
        # Get metadata from peer handshake if available
        peer_info = self.extension_manager.get_peer_info()
        if "metadata_size" in peer_info and peer_info["metadata_size"] > 0:
            self.metadata_size = peer_info["metadata_size"]
            self.pieces_count = math.ceil(self.metadata_size / self.piece_size)

        # For fake seeding, generate synthetic metadata
        if self.generate_synthetic_metadata and not self.metadata:
            self._generate_synthetic_metadata()

        logger.debug(
            f"Metadata extension ready - size: {self.metadata_size}, " f"pieces: {self.pieces_count}",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_message(self, payload: bytes):
        """
        Handle incoming metadata message

        Args:
            payload: Metadata message payload
        """
        try:
            if len(payload) < 1:
                return

            # Extract message type
            msg_type = payload[0]

            if msg_type == self.REQUEST:
                self._handle_request(payload[1:])
            elif msg_type == self.DATA:
                self._handle_data(payload[1:])
            elif msg_type == self.REJECT:
                self._handle_reject(payload[1:])
            else:
                logger.debug(
                    f"Unknown metadata message type: {msg_type}",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to handle metadata message: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _handle_request(self, payload: bytes):
        """
        Handle metadata request message

        Args:
            payload: Request payload containing piece index
        """
        try:
            # Decode request
            request_data = bencode.bdecode(payload)
            piece_index = request_data.get(b"piece", 0)

            logger.debug(
                f"Received metadata request for piece {piece_index}",
                extra={"class_name": self.__class__.__name__},
            )

            # Check if we have the metadata
            if not self.metadata:
                self._send_reject(piece_index)
                return

            # Check piece index validity
            if piece_index >= self.pieces_count:
                self._send_reject(piece_index)
                return

            # Send the requested piece
            self._send_metadata_piece(piece_index)

        except Exception as e:
            logger.error(
                f"Failed to handle metadata request: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _handle_data(self, payload: bytes):
        """
        Handle metadata data message

        Args:
            payload: Data payload containing piece data
        """
        try:
            # Find the dictionary end to separate metadata from piece data
            dict_end = payload.find(b"ee") + 2
            if dict_end < 2:
                return

            # Decode metadata
            metadata_dict = bencode.bdecode(payload[:dict_end])
            piece_index = metadata_dict.get(b"piece", 0)
            total_size = metadata_dict.get(b"total_size", 0)

            # Extract piece data
            piece_data = payload[dict_end:]

            logger.debug(
                f"Received metadata piece {piece_index}, size: {len(piece_data)}",
                extra={"class_name": self.__class__.__name__},
            )

            # Store piece
            self.received_pieces[piece_index] = piece_data
            self.requested_pieces.discard(piece_index)

            # Update metadata size
            if total_size > 0:
                self.metadata_size = total_size
                self.pieces_count = math.ceil(self.metadata_size / self.piece_size)

            # Check if we have all pieces
            if len(self.received_pieces) == self.pieces_count:
                self._assemble_metadata()

        except Exception as e:
            logger.error(
                f"Failed to handle metadata data: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _handle_reject(self, payload: bytes):
        """
        Handle metadata reject message

        Args:
            payload: Reject payload containing piece index
        """
        try:
            reject_data = bencode.bdecode(payload)
            piece_index = reject_data.get(b"piece", 0)

            logger.debug(
                f"Metadata request rejected for piece {piece_index}",
                extra={"class_name": self.__class__.__name__},
            )

            # Remove from requested pieces
            self.requested_pieces.discard(piece_index)

        except Exception as e:
            logger.error(
                f"Failed to handle metadata reject: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _send_metadata_piece(self, piece_index: int):
        """
        Send metadata piece to peer

        Args:
            piece_index: Index of piece to send
        """
        try:
            if not self.metadata:
                self._send_reject(piece_index)
                return

            # Calculate piece bounds
            start_offset = piece_index * self.piece_size
            end_offset = min(start_offset + self.piece_size, len(self.metadata))
            piece_data = self.metadata[start_offset:end_offset]

            # Build message
            metadata_dict = {
                b"msg_type": self.DATA,
                b"piece": piece_index,
                b"total_size": len(self.metadata),
            }

            # Encode message
            payload = struct.pack("B", self.DATA)
            payload += bencode.bencode(metadata_dict)
            payload += piece_data

            # Send message
            success = self.extension_manager.send_extended_message("ut_metadata", payload)

            if success:
                logger.debug(
                    f"Sent metadata piece {piece_index}, size: {len(piece_data)}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.debug(
                    f"Failed to send metadata piece {piece_index}",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to send metadata piece: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _send_reject(self, piece_index: int):
        """
        Send metadata reject message

        Args:
            piece_index: Index of rejected piece
        """
        try:
            reject_dict = {b"msg_type": self.REJECT, b"piece": piece_index}

            payload = struct.pack("B", self.REJECT)
            payload += bencode.bencode(reject_dict)

            self.extension_manager.send_extended_message("ut_metadata", payload)

            logger.debug(
                f"Sent metadata reject for piece {piece_index}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to send metadata reject: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def request_metadata(self):
        """Request metadata from peer"""
        if not self.metadata_size or self.pieces_count == 0:
            logger.debug(
                "No metadata size information available",
                extra={"class_name": self.__class__.__name__},
            )
            return

        # Request all pieces we don't have
        for piece_index in range(self.pieces_count):
            if piece_index not in self.received_pieces and piece_index not in self.requested_pieces:
                self._request_piece(piece_index)

    def _request_piece(self, piece_index: int):
        """
        Request specific metadata piece

        Args:
            piece_index: Index of piece to request
        """
        try:
            request_dict = {b"msg_type": self.REQUEST, b"piece": piece_index}

            payload = struct.pack("B", self.REQUEST)
            payload += bencode.bencode(request_dict)

            success = self.extension_manager.send_extended_message("ut_metadata", payload)

            if success:
                self.requested_pieces.add(piece_index)
                logger.debug(
                    f"Requested metadata piece {piece_index}",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to request metadata piece: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _assemble_metadata(self):
        """Assemble complete metadata from received pieces"""
        try:
            # Sort pieces by index and concatenate
            sorted_pieces = sorted(self.received_pieces.items())
            self.metadata = b"".join(piece_data for _, piece_data in sorted_pieces)

            # Verify metadata integrity
            if len(self.metadata) != self.metadata_size:
                logger.warning(
                    "Assembled metadata size mismatch",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            # Parse metadata to verify it's valid
            try:
                metadata_dict = bencode.bdecode(self.metadata)
                if b"announce" in metadata_dict and b"info" in metadata_dict:
                    logger.debug(
                        "Successfully assembled complete metadata",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    logger.warning(
                        "Assembled metadata appears invalid",
                        extra={"class_name": self.__class__.__name__},
                    )
            except Exception:
                logger.warning(
                    "Failed to parse assembled metadata",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to assemble metadata: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _generate_synthetic_metadata(self):
        """Generate synthetic metadata for fake seeding"""
        try:
            # Create minimal but valid torrent metadata
            info_dict = {
                b"name": b"fake_file.txt",
                b"length": 1024 * 1024,  # 1MB file
                b"piece length": 32768,  # 32KB pieces
                b"pieces": b"\x00" * 20 * BitTorrentProtocolConstants.FAKE_METADATA_PIECE_COUNT,  # 32 fake piece hashes
            }

            metadata_dict = {
                b"announce": b"http://tracker.example.com:8080/announce",
                b"info": info_dict,
                b"creation date": 1234567890,
                b"created by": b"DFakeSeeder 1.0",
            }

            self.metadata = bencode.bencode(metadata_dict)
            self.metadata_size = len(self.metadata)
            self.pieces_count = math.ceil(self.metadata_size / self.piece_size)

            logger.debug(
                f"Generated synthetic metadata - size: {self.metadata_size}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to generate synthetic metadata: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def get_metadata(self) -> Optional[bytes]:
        """
        Get complete metadata

        Returns:
            Complete metadata bytes or None
        """
        return self.metadata

    def has_complete_metadata(self) -> bool:
        """
        Check if we have complete metadata

        Returns:
            True if metadata is complete
        """
        return self.metadata is not None and len(self.metadata) == self.metadata_size

    def get_statistics(self) -> dict:
        """
        Get metadata extension statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "metadata_size": self.metadata_size,
            "pieces_count": self.pieces_count,
            "received_pieces": len(self.received_pieces),
            "requested_pieces": len(self.requested_pieces),
            "complete": self.has_complete_metadata(),
            "piece_size": self.piece_size,
        }

    def cleanup(self):
        """Clean up metadata extension"""
        self.received_pieces.clear()
        self.requested_pieces.clear()
        self.metadata = None

        logger.debug(
            "Metadata extension cleaned up",
            extra={"class_name": self.__class__.__name__},
        )
