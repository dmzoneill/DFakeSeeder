"""
DontHave Extension Implementation

Extension for indicating that a peer no longer has a piece.
This is useful for correcting erroneous HAVE messages and maintaining
accurate piece availability information.
"""

# fmt: off
import struct
from typing import Set

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import BitTorrentProtocolConstants

# fmt: on


class DontHaveExtension:
    """DontHave extension implementation"""

    # DontHave message type (using libtorrent's convention)
    DONT_HAVE = 18

    def __init__(self, peer_connection):
        """
        Initialize DontHave Extension

        Args:
            peer_connection: PeerConnection instance
        """
        self.peer_connection = peer_connection
        self.settings = AppSettings.get_instance()

        # Extension configuration
        ext_config = getattr(self.settings, "protocols", {}).get("extensions", {})
        self.donthave_enabled = ext_config.get("lt_donthave", True)

        # DontHave state
        self.peer_supports_donthave = False
        self.sent_donthave_pieces: Set[int] = set()
        self.received_donthave_pieces: Set[int] = set()

        # For fake seeding
        self.simulate_donthave_behavior = True
        self.error_correction_enabled = True

        logger.debug(
            "DontHave Extension initialized",
            extra={
                "class_name": self.__class__.__name__,
                "enabled": self.donthave_enabled,
            },
        )

    def supports_donthave_extension(self) -> bool:
        """Check if DontHave Extension is supported"""
        return self.donthave_enabled

    def enable_peer_donthave_support(self):
        """Enable DontHave extension support for peer"""
        self.peer_supports_donthave = True
        logger.debug(
            "Peer DontHave extension support enabled",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_donthave(self, payload: bytes):
        """
        Handle DONT_HAVE message

        Args:
            payload: Message payload containing piece index
        """
        if len(payload) < BitTorrentProtocolConstants.DONTHAVE_PAYLOAD_SIZE:
            logger.warning(
                "Invalid DONT_HAVE message length",
                extra={"class_name": self.__class__.__name__},
            )
            return

        try:
            piece_index = struct.unpack(">I", payload[:4])[0]
            self.received_donthave_pieces.add(piece_index)

            logger.debug(
                f"Received DONT_HAVE: {piece_index}",
                extra={"class_name": self.__class__.__name__},
            )

            # Update peer's piece availability
            self._update_peer_availability(piece_index, has_piece=False)

            # Handle the correction in our availability tracking
            if self.simulate_donthave_behavior:
                self._handle_piece_unavailable(piece_index)

        except Exception as e:
            logger.error(
                f"Failed to handle DONT_HAVE: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def send_donthave(self, piece_index: int) -> bool:
        """
        Send DONT_HAVE message

        Args:
            piece_index: Index of piece we no longer have

        Returns:
            True if message sent successfully
        """
        if not self.peer_supports_donthave:
            logger.debug(
                "Peer doesn't support DONT_HAVE",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            message = struct.pack(">IBL", 5, self.DONT_HAVE, piece_index)

            if hasattr(self.peer_connection, "send_message"):
                self.peer_connection.send_message(message)
                self.sent_donthave_pieces.add(piece_index)

                logger.debug(
                    f"Sent DONT_HAVE: {piece_index}",
                    extra={"class_name": self.__class__.__name__},
                )
                return True
            else:
                logger.warning(
                    "Peer connection has no send_message method",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to send DONT_HAVE: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return False

    def correct_have_message(self, piece_index: int) -> bool:
        """
        Correct a previously sent HAVE message by sending DONT_HAVE

        Args:
            piece_index: Index of piece to correct

        Returns:
            True if correction sent successfully
        """
        if not self.error_correction_enabled:
            return False

        logger.debug(
            f"Correcting HAVE message for piece {piece_index}",
            extra={"class_name": self.__class__.__name__},
        )

        return self.send_donthave(piece_index)

    def simulate_piece_loss(self, piece_index: int) -> bool:
        """
        Simulate losing a piece (for fake seeding scenarios)

        Args:
            piece_index: Index of piece to simulate losing

        Returns:
            True if simulation successful
        """
        if not self.simulate_donthave_behavior:
            return False

        # Check if we previously claimed to have this piece
        if hasattr(self.peer_connection, "sent_have_pieces"):
            if piece_index in self.peer_connection.sent_have_pieces:
                logger.debug(
                    f"Simulating loss of piece {piece_index}",
                    extra={"class_name": self.__class__.__name__},
                )
                return self.send_donthave(piece_index)

        return False

    def handle_storage_error(self, piece_index: int):
        """
        Handle storage error that makes a piece unavailable

        Args:
            piece_index: Index of piece that became unavailable
        """
        logger.warning(
            f"Storage error for piece {piece_index}, sending DONT_HAVE",
            extra={"class_name": self.__class__.__name__},
        )

        # Send DONT_HAVE to correct any previous HAVE messages
        self.send_donthave(piece_index)

        # Update our internal state
        if hasattr(self.peer_connection, "available_pieces"):
            self.peer_connection.available_pieces.discard(piece_index)

    def verify_piece_availability(self, piece_indices: Set[int]) -> Set[int]:
        """
        Verify piece availability and send corrections if needed

        Args:
            piece_indices: Set of piece indices to verify

        Returns:
            Set of pieces that are actually unavailable
        """
        unavailable_pieces: Set[int] = set()

        if not self.error_correction_enabled:
            return unavailable_pieces

        try:
            for piece_index in piece_indices:
                # In fake seeding, randomly simulate some pieces becoming unavailable
                if self.simulate_donthave_behavior:
                    import random

                    if (
                        random.random() < BitTorrentProtocolConstants.PIECE_UNAVAILABLE_PROBABILITY
                    ):  # 5% chance piece becomes unavailable
                        unavailable_pieces.add(piece_index)
                        self.send_donthave(piece_index)

            if unavailable_pieces:
                logger.debug(
                    f"Sent DONT_HAVE corrections for {len(unavailable_pieces)} pieces",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to verify piece availability: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return unavailable_pieces

    def _update_peer_availability(self, piece_index: int, has_piece: bool):
        """
        Update peer's piece availability

        Args:
            piece_index: Piece index
            has_piece: Whether peer has the piece
        """
        if hasattr(self.peer_connection, "peer_pieces"):
            if not hasattr(self.peer_connection.peer_pieces, "add"):
                self.peer_connection.peer_pieces = set()

            if has_piece:
                self.peer_connection.peer_pieces.add(piece_index)
            else:
                self.peer_connection.peer_pieces.discard(piece_index)

    def _handle_piece_unavailable(self, piece_index: int):
        """
        Handle when a piece becomes unavailable from peer

        Args:
            piece_index: Index of unavailable piece
        """
        # Cancel any pending requests for this piece
        if hasattr(self.peer_connection, "pending_requests"):
            requests_to_cancel = [
                req
                for req in self.peer_connection.pending_requests
                if req[0] == piece_index  # req format: (piece_index, begin, length)
            ]

            for req in requests_to_cancel:
                self.peer_connection.pending_requests.discard(req)
                logger.debug(
                    f"Cancelled request for unavailable piece {piece_index}",
                    extra={"class_name": self.__class__.__name__},
                )

        # Update piece priority/selection logic
        self._update_piece_selection(piece_index)

    def _update_piece_selection(self, unavailable_piece: int):
        """
        Update piece selection strategy based on unavailable piece

        Args:
            unavailable_piece: Index of piece that's no longer available
        """
        # In fake seeding, we can simulate adjusting piece selection
        logger.debug(
            f"Adjusting piece selection due to unavailable piece {unavailable_piece}",
            extra={"class_name": self.__class__.__name__},
        )

    def get_statistics(self) -> dict:
        """
        Get DontHave Extension statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "enabled": self.donthave_enabled,
            "peer_supports_donthave": self.peer_supports_donthave,
            "sent_donthave_count": len(self.sent_donthave_pieces),
            "received_donthave_count": len(self.received_donthave_pieces),
            "error_correction_enabled": self.error_correction_enabled,
            "simulation_enabled": self.simulate_donthave_behavior,
        }

    def get_corrected_pieces(self) -> Set[int]:
        """
        Get set of pieces that have been corrected with DONT_HAVE

        Returns:
            Set of piece indices that were corrected
        """
        return self.sent_donthave_pieces.copy()

    def get_peer_unavailable_pieces(self) -> Set[int]:
        """
        Get set of pieces that peer indicated as unavailable

        Returns:
            Set of piece indices peer doesn't have
        """
        return self.received_donthave_pieces.copy()

    def reset_corrections(self):
        """Reset DONT_HAVE correction tracking"""
        self.sent_donthave_pieces.clear()
        self.received_donthave_pieces.clear()

        logger.debug("Reset DONT_HAVE corrections", extra={"class_name": self.__class__.__name__})

    def cleanup(self):
        """Clean up DontHave Extension state"""
        self.sent_donthave_pieces.clear()
        self.received_donthave_pieces.clear()
        self.peer_supports_donthave = False

        logger.debug(
            "DontHave Extension cleaned up",
            extra={"class_name": self.__class__.__name__},
        )
