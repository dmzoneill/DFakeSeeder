"""
ut_metadata Extension (BEP 9) - Metadata Exchange

Allows fetching torrent metadata from peers without requiring the .torrent file.
"""

# fmt: off
from typing import Any, Optional

try:
    import bencodepy
except ImportError:
    bencodepy = None

from d_fake_seeder.lib.logger import logger

# fmt: on


class UTMetadataExtension:
    """
    Handles ut_metadata extension protocol (BEP 9).

    Message types:
    - 0: request - Request a metadata piece
    - 1: data - Send a metadata piece
    - 2: reject - Reject a metadata request
    """

    # Message type constants
    REQUEST = 0
    DATA = 1
    REJECT = 2

    # Maximum piece size (16KB as per BEP 9)
    PIECE_SIZE = 16384

    def __init__(self, info_dict: Optional[dict] = None, metadata_size: Optional[int] = None) -> None:
        """
        Initialize ut_metadata extension.

        Args:
            info_dict: The torrent info dictionary (if we have it)
            metadata_size: Size of the metadata in bytes
        """
        self.info_dict = info_dict
        self.metadata_size = metadata_size
        self.metadata_pieces = {}  # type: ignore[var-annotated]

        # If we have the info dict, calculate metadata and split into pieces
        if info_dict and bencodepy:
            try:
                self.metadata = bencodepy.encode(info_dict)
                self.metadata_size = len(self.metadata)
                self._split_metadata_into_pieces()
            except Exception as e:
                logger.error(f"Failed to encode metadata: {e}", "UTMetadataExtension", exc_info=True)
                self.metadata = None

    def _split_metadata_into_pieces(self) -> Any:
        """Split metadata into 16KB pieces"""
        if not hasattr(self, "metadata") or not self.metadata:
            return

        num_pieces = (self.metadata_size + self.PIECE_SIZE - 1) // self.PIECE_SIZE  # type: ignore[operator]

        for i in range(num_pieces):
            start = i * self.PIECE_SIZE
            end = min(start + self.PIECE_SIZE, self.metadata_size)  # type: ignore[type-var]
            self.metadata_pieces[i] = self.metadata[start:end]

        logger.trace(f"Split metadata into {num_pieces} pieces ({self.metadata_size} bytes)", "UTMetadataExtension")

    def handle_request(self, piece_index: int) -> Optional[bytes]:
        """
        Handle a metadata piece request.

        Args:
            piece_index: Index of the requested piece

        Returns:
            Bencoded response message or None if piece not available
        """
        if not bencodepy:
            logger.warning("bencodepy not available, cannot handle metadata requests", "UTMetadataExtension")
            return None

        if piece_index not in self.metadata_pieces:
            # Reject request
            response = {
                b"msg_type": self.REJECT,
                b"piece": piece_index,
            }
            return bencodepy.encode(response)  # type: ignore[no-any-return]

        # Send metadata piece
        response = {
            b"msg_type": self.DATA,
            b"piece": piece_index,
            b"total_size": self.metadata_size,  # type: ignore[dict-item]
        }

        # Bencode the response and append the piece data
        encoded_response = bencodepy.encode(response)
        return encoded_response + self.metadata_pieces[piece_index]  # type: ignore[no-any-return]

    def parse_message(self, payload: bytes) -> Optional[dict]:
        """
        Parse a ut_metadata message.

        Args:
            payload: The message payload (after extended message ID byte)

        Returns:
            Dictionary with message info or None if parse fails
        """
        if not bencodepy:
            return None

        try:
            # Find where the bencoded dictionary ends
            # (metadata piece data comes after it for DATA messages)
            decoded, end_pos = bencodepy.decode_from_file(payload)

            msg_type = decoded.get(b"msg_type", -1)
            piece_index = decoded.get(b"piece", -1)

            result = {
                "msg_type": msg_type,
                "piece": piece_index,
            }

            if msg_type == self.DATA:
                result["total_size"] = decoded.get(b"total_size", 0)
                # Extract piece data (everything after the bencoded dict)
                if end_pos < len(payload):
                    result["data"] = payload[end_pos:]

            return result

        except Exception as e:
            logger.trace(f"Failed to parse ut_metadata message: {e}", "UTMetadataExtension")
            return None

    def create_request(self, piece_index: int) -> Optional[bytes]:
        """
        Create a metadata piece request message.

        Args:
            piece_index: Index of the piece to request

        Returns:
            Bencoded request message or None if bencodepy not available
        """
        if not bencodepy:
            return None

        request = {
            b"msg_type": self.REQUEST,
            b"piece": piece_index,
        }

        return bencodepy.encode(request)  # type: ignore[no-any-return]
