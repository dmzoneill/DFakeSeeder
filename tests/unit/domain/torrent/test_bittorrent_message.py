"""
Unit tests for d_fake_seeder.domain.torrent.bittorrent_message module.

Tests BitTorrent protocol message type constants.
"""

from d_fake_seeder.domain.torrent.bittorrent_message import BitTorrentMessage


def test_choke_message_constant():
    """Test that CHOKE message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.CHOKE == 0


def test_unchoke_message_constant():
    """Test that UNCHOKE message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.UNCHOKE == 1


def test_interested_message_constant():
    """Test that INTERESTED message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.INTERESTED == 2


def test_not_interested_message_constant():
    """Test that NOT_INTERESTED message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.NOT_INTERESTED == 3


def test_have_message_constant():
    """Test that HAVE message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.HAVE == 4


def test_bitfield_message_constant():
    """Test that BITFIELD message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.BITFIELD == 5


def test_request_message_constant():
    """Test that REQUEST message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.REQUEST == 6


def test_piece_message_constant():
    """Test that PIECE message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.PIECE == 7


def test_cancel_message_constant():
    """Test that CANCEL message constant has correct value"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.CANCEL == 8


def test_port_message_constant():
    """Test that PORT message constant has correct value for DHT extension"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.PORT == 9


def test_extended_message_constant():
    """Test that EXTENDED message constant has correct value for BEP-010"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.EXTENDED == 20


def test_all_message_types_are_integers():
    """Test that all message type constants are integers"""
    # Arrange & Act & Assert
    assert isinstance(BitTorrentMessage.CHOKE, int)
    assert isinstance(BitTorrentMessage.UNCHOKE, int)
    assert isinstance(BitTorrentMessage.INTERESTED, int)
    assert isinstance(BitTorrentMessage.NOT_INTERESTED, int)
    assert isinstance(BitTorrentMessage.HAVE, int)
    assert isinstance(BitTorrentMessage.BITFIELD, int)
    assert isinstance(BitTorrentMessage.REQUEST, int)
    assert isinstance(BitTorrentMessage.PIECE, int)
    assert isinstance(BitTorrentMessage.CANCEL, int)
    assert isinstance(BitTorrentMessage.PORT, int)
    assert isinstance(BitTorrentMessage.EXTENDED, int)


def test_message_types_are_unique():
    """Test that all message type constants have unique values"""
    # Arrange
    message_types = [
        BitTorrentMessage.CHOKE,
        BitTorrentMessage.UNCHOKE,
        BitTorrentMessage.INTERESTED,
        BitTorrentMessage.NOT_INTERESTED,
        BitTorrentMessage.HAVE,
        BitTorrentMessage.BITFIELD,
        BitTorrentMessage.REQUEST,
        BitTorrentMessage.PIECE,
        BitTorrentMessage.CANCEL,
        BitTorrentMessage.PORT,
        BitTorrentMessage.EXTENDED,
    ]

    # Act & Assert
    assert len(message_types) == len(set(message_types))


def test_message_types_are_non_negative():
    """Test that all message type constants are non-negative"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.CHOKE >= 0
    assert BitTorrentMessage.UNCHOKE >= 0
    assert BitTorrentMessage.INTERESTED >= 0
    assert BitTorrentMessage.NOT_INTERESTED >= 0
    assert BitTorrentMessage.HAVE >= 0
    assert BitTorrentMessage.BITFIELD >= 0
    assert BitTorrentMessage.REQUEST >= 0
    assert BitTorrentMessage.PIECE >= 0
    assert BitTorrentMessage.CANCEL >= 0
    assert BitTorrentMessage.PORT >= 0
    assert BitTorrentMessage.EXTENDED >= 0


def test_basic_messages_sequential():
    """Test that basic messages (0-9) are sequential"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.CHOKE == 0
    assert BitTorrentMessage.UNCHOKE == 1
    assert BitTorrentMessage.INTERESTED == 2
    assert BitTorrentMessage.NOT_INTERESTED == 3
    assert BitTorrentMessage.HAVE == 4
    assert BitTorrentMessage.BITFIELD == 5
    assert BitTorrentMessage.REQUEST == 6
    assert BitTorrentMessage.PIECE == 7
    assert BitTorrentMessage.CANCEL == 8
    assert BitTorrentMessage.PORT == 9


def test_extended_message_separate_from_basic():
    """Test that EXTENDED message ID is separate from basic messages"""
    # Arrange & Act & Assert
    assert BitTorrentMessage.EXTENDED > BitTorrentMessage.PORT
    assert BitTorrentMessage.EXTENDED == 20


def test_message_type_fits_in_single_byte():
    """Test that all message types fit in a single byte (0-255)"""
    # Arrange
    message_types = [
        BitTorrentMessage.CHOKE,
        BitTorrentMessage.UNCHOKE,
        BitTorrentMessage.INTERESTED,
        BitTorrentMessage.NOT_INTERESTED,
        BitTorrentMessage.HAVE,
        BitTorrentMessage.BITFIELD,
        BitTorrentMessage.REQUEST,
        BitTorrentMessage.PIECE,
        BitTorrentMessage.CANCEL,
        BitTorrentMessage.PORT,
        BitTorrentMessage.EXTENDED,
    ]

    # Act & Assert
    for msg_type in message_types:
        assert 0 <= msg_type <= 255
