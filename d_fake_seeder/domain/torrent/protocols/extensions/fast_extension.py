"""
Fast Extension Implementation (BEP-006)

Implements the Fast Extension which adds four new message types:
- HAVE_ALL, HAVE_NONE, SUGGEST_PIECE, REJECT_REQUEST
- Allows fast startup by eliminating certain delay-causing messages
"""

import random
import struct
from typing import Set

from domain.app_settings import AppSettings
from lib.logger import logger


class FastExtension:
    """Fast Extension implementation (BEP-006)"""

    # Fast Extension message types
    SUGGEST_PIECE = 13
    HAVE_ALL = 14
    HAVE_NONE = 15
    REJECT_REQUEST = 16
    ALLOWED_FAST = 17

    def __init__(self, peer_connection):
        """
        Initialize Fast Extension

        Args:
            peer_connection: PeerConnection instance
        """
        self.peer_connection = peer_connection
        self.settings = AppSettings.get_instance()

        # Fast extension configuration
        fast_config = getattr(self.settings, "protocols", {}).get("extensions", {})
        self.fast_extension_enabled = fast_config.get("fast_extension", True)

        # Fast extension state
        self.peer_supports_fast = False
        self.allowed_fast_pieces: Set[int] = set()
        self.suggested_pieces: Set[int] = set()
        self.have_all = False
        self.have_none = False

        # For fake seeding
        self.simulate_fast_behavior = True
        self.max_allowed_fast = 10  # Maximum allowed fast pieces
        self.max_suggest_pieces = 5  # Maximum pieces to suggest

        logger.debug(
            "Fast Extension initialized",
            extra={"class_name": self.__class__.__name__, "enabled": self.fast_extension_enabled},
        )

    def supports_fast_extension(self) -> bool:
        """Check if Fast Extension is supported"""
        return self.fast_extension_enabled

    def enable_peer_fast_support(self):
        """Enable fast extension support for peer"""
        self.peer_supports_fast = True
        logger.debug("Peer fast extension support enabled", extra={"class_name": self.__class__.__name__})

    def handle_suggest_piece(self, payload: bytes):
        """
        Handle SUGGEST_PIECE message

        Args:
            payload: Message payload containing piece index
        """
        if len(payload) < 4:
            return

        try:
            piece_index = struct.unpack(">I", payload[:4])[0]
            self.suggested_pieces.add(piece_index)

            logger.debug(f"Received SUGGEST_PIECE: {piece_index}", extra={"class_name": self.__class__.__name__})

            # In fake seeding, we can immediately "consider" this suggestion
            if self.simulate_fast_behavior:
                self._handle_suggested_piece(piece_index)

        except Exception as e:
            logger.error(f"Failed to handle SUGGEST_PIECE: {e}", extra={"class_name": self.__class__.__name__})

    def handle_have_all(self, payload: bytes):
        """
        Handle HAVE_ALL message

        Args:
            payload: Message payload (should be empty)
        """
        self.have_all = True
        self.have_none = False

        logger.debug("Received HAVE_ALL", extra={"class_name": self.__class__.__name__})

        # Update peer's availability to all pieces
        if hasattr(self.peer_connection, "torrent") and self.peer_connection.torrent:
            piece_count = getattr(self.peer_connection.torrent, "piece_count", 0)
            if piece_count > 0:
                # Mark all pieces as available
                for piece_index in range(piece_count):
                    self._mark_peer_has_piece(piece_index)

    def handle_have_none(self, payload: bytes):
        """
        Handle HAVE_NONE message

        Args:
            payload: Message payload (should be empty)
        """
        self.have_none = True
        self.have_all = False

        logger.debug("Received HAVE_NONE", extra={"class_name": self.__class__.__name__})

        # Clear all peer availability
        if hasattr(self.peer_connection, "peer_pieces"):
            self.peer_connection.peer_pieces.clear()

    def handle_reject_request(self, payload: bytes):
        """
        Handle REJECT_REQUEST message

        Args:
            payload: Message payload containing request details
        """
        if len(payload) < 12:
            return

        try:
            piece_index, begin, length = struct.unpack(">III", payload[:12])

            logger.debug(
                f"Received REJECT_REQUEST: piece={piece_index}, begin={begin}, length={length}",
                extra={"class_name": self.__class__.__name__},
            )

            # Handle the rejection - remove from pending requests
            if hasattr(self.peer_connection, "pending_requests"):
                request_key = (piece_index, begin, length)
                self.peer_connection.pending_requests.discard(request_key)

        except Exception as e:
            logger.error(f"Failed to handle REJECT_REQUEST: {e}", extra={"class_name": self.__class__.__name__})

    def handle_allowed_fast(self, payload: bytes):
        """
        Handle ALLOWED_FAST message

        Args:
            payload: Message payload containing piece index
        """
        if len(payload) < 4:
            return

        try:
            piece_index = struct.unpack(">I", payload[:4])[0]
            self.allowed_fast_pieces.add(piece_index)

            logger.debug(f"Received ALLOWED_FAST: {piece_index}", extra={"class_name": self.__class__.__name__})

            # In fake seeding, we can use this for immediate requests
            if self.simulate_fast_behavior:
                self._handle_allowed_fast_piece(piece_index)

        except Exception as e:
            logger.error(f"Failed to handle ALLOWED_FAST: {e}", extra={"class_name": self.__class__.__name__})

    def send_suggest_piece(self, piece_index: int) -> bool:
        """
        Send SUGGEST_PIECE message

        Args:
            piece_index: Index of piece to suggest

        Returns:
            True if message sent successfully
        """
        if not self.peer_supports_fast:
            return False

        try:
            message = struct.pack(">IBL", 5, self.SUGGEST_PIECE, piece_index)

            if hasattr(self.peer_connection, "send_message"):
                self.peer_connection.send_message(message)
                logger.debug(f"Sent SUGGEST_PIECE: {piece_index}", extra={"class_name": self.__class__.__name__})
                return True

        except Exception as e:
            logger.error(f"Failed to send SUGGEST_PIECE: {e}", extra={"class_name": self.__class__.__name__})

        return False

    def send_have_all(self) -> bool:
        """
        Send HAVE_ALL message

        Returns:
            True if message sent successfully
        """
        if not self.peer_supports_fast:
            return False

        try:
            message = struct.pack(">IB", 1, self.HAVE_ALL)

            if hasattr(self.peer_connection, "send_message"):
                self.peer_connection.send_message(message)
                logger.debug("Sent HAVE_ALL", extra={"class_name": self.__class__.__name__})
                return True

        except Exception as e:
            logger.error(f"Failed to send HAVE_ALL: {e}", extra={"class_name": self.__class__.__name__})

        return False

    def send_have_none(self) -> bool:
        """
        Send HAVE_NONE message

        Returns:
            True if message sent successfully
        """
        if not self.peer_supports_fast:
            return False

        try:
            message = struct.pack(">IB", 1, self.HAVE_NONE)

            if hasattr(self.peer_connection, "send_message"):
                self.peer_connection.send_message(message)
                logger.debug("Sent HAVE_NONE", extra={"class_name": self.__class__.__name__})
                return True

        except Exception as e:
            logger.error(f"Failed to send HAVE_NONE: {e}", extra={"class_name": self.__class__.__name__})

        return False

    def send_reject_request(self, piece_index: int, begin: int, length: int) -> bool:
        """
        Send REJECT_REQUEST message

        Args:
            piece_index: Piece index
            begin: Byte offset within piece
            length: Length of data

        Returns:
            True if message sent successfully
        """
        if not self.peer_supports_fast:
            return False

        try:
            message = struct.pack(">IBIII", 13, self.REJECT_REQUEST, piece_index, begin, length)

            if hasattr(self.peer_connection, "send_message"):
                self.peer_connection.send_message(message)
                logger.debug(
                    f"Sent REJECT_REQUEST: piece={piece_index}, begin={begin}, length={length}",
                    extra={"class_name": self.__class__.__name__},
                )
                return True

        except Exception as e:
            logger.error(f"Failed to send REJECT_REQUEST: {e}", extra={"class_name": self.__class__.__name__})

        return False

    def send_allowed_fast(self, piece_index: int) -> bool:
        """
        Send ALLOWED_FAST message

        Args:
            piece_index: Index of piece allowed for fast download

        Returns:
            True if message sent successfully
        """
        if not self.peer_supports_fast:
            return False

        try:
            message = struct.pack(">IBL", 5, self.ALLOWED_FAST, piece_index)

            if hasattr(self.peer_connection, "send_message"):
                self.peer_connection.send_message(message)
                logger.debug(f"Sent ALLOWED_FAST: {piece_index}", extra={"class_name": self.__class__.__name__})
                return True

        except Exception as e:
            logger.error(f"Failed to send ALLOWED_FAST: {e}", extra={"class_name": self.__class__.__name__})

        return False

    def generate_allowed_fast_set(self, info_hash: bytes, peer_ip: str, num_pieces: int):
        """
        Generate allowed fast set based on peer IP and info hash

        Args:
            info_hash: Torrent info hash
            peer_ip: Peer IP address
            num_pieces: Total number of pieces in torrent
        """
        if not self.peer_supports_fast or num_pieces == 0:
            return

        try:
            # Simple implementation - in production would use BEP-006 algorithm
            # For fake seeding, generate a reasonable set
            fast_pieces = set()
            max_fast = min(self.max_allowed_fast, num_pieces)

            # Use info_hash and peer_ip for deterministic selection
            import hashlib

            seed_data = info_hash + peer_ip.encode()
            hash_value = hashlib.sha1(seed_data).digest()

            # Use hash to select pieces
            for i in range(max_fast):
                piece_index = int.from_bytes(hash_value[i * 2 : (i + 1) * 2], "big") % num_pieces
                fast_pieces.add(piece_index)

            # Send allowed fast messages
            for piece_index in fast_pieces:
                self.send_allowed_fast(piece_index)

            logger.debug(
                f"Generated {len(fast_pieces)} allowed fast pieces", extra={"class_name": self.__class__.__name__}
            )

        except Exception as e:
            logger.error(f"Failed to generate allowed fast set: {e}", extra={"class_name": self.__class__.__name__})

    def suggest_pieces_to_peer(self, available_pieces: Set[int]):
        """
        Suggest pieces to peer for download

        Args:
            available_pieces: Set of pieces we have available
        """
        if not self.peer_supports_fast or not available_pieces:
            return

        try:
            # Select random pieces to suggest
            pieces_to_suggest = random.sample(
                list(available_pieces), min(self.max_suggest_pieces, len(available_pieces))
            )

            for piece_index in pieces_to_suggest:
                self.send_suggest_piece(piece_index)

            logger.debug(
                f"Suggested {len(pieces_to_suggest)} pieces to peer", extra={"class_name": self.__class__.__name__}
            )

        except Exception as e:
            logger.error(f"Failed to suggest pieces: {e}", extra={"class_name": self.__class__.__name__})

    def _handle_suggested_piece(self, piece_index: int):
        """Handle a piece suggestion from peer"""
        # In fake seeding, we simulate considering the suggestion
        logger.debug(f"Considering suggested piece: {piece_index}", extra={"class_name": self.__class__.__name__})

    def _handle_allowed_fast_piece(self, piece_index: int):
        """Handle an allowed fast piece from peer"""
        # In fake seeding, we could immediately "request" this piece
        logger.debug(f"Piece {piece_index} available for fast download", extra={"class_name": self.__class__.__name__})

    def _mark_peer_has_piece(self, piece_index: int):
        """Mark that peer has a specific piece"""
        if hasattr(self.peer_connection, "peer_pieces"):
            if not hasattr(self.peer_connection.peer_pieces, "add"):
                self.peer_connection.peer_pieces = set()
            self.peer_connection.peer_pieces.add(piece_index)

    def get_statistics(self) -> dict:
        """
        Get Fast Extension statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "enabled": self.fast_extension_enabled,
            "peer_supports_fast": self.peer_supports_fast,
            "allowed_fast_pieces": len(self.allowed_fast_pieces),
            "suggested_pieces": len(self.suggested_pieces),
            "have_all": self.have_all,
            "have_none": self.have_none,
        }

    def cleanup(self):
        """Clean up Fast Extension state"""
        self.allowed_fast_pieces.clear()
        self.suggested_pieces.clear()
        self.have_all = False
        self.have_none = False
        self.peer_supports_fast = False

        logger.debug("Fast Extension cleaned up", extra={"class_name": self.__class__.__name__})
