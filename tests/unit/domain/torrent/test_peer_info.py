"""
Unit tests for d_fake_seeder.domain.torrent.peer_info module.

Tests PeerInfo dataclass representing peer connection information.
"""

import pytest
from d_fake_seeder.domain.torrent.peer_info import PeerInfo


def test_peer_info_creates_with_required_fields():
    """Test that PeerInfo can be created with only required fields"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Assert
    assert peer.ip == "192.168.1.1"
    assert peer.port == 6881


def test_peer_info_has_default_values():
    """Test that PeerInfo has correct default values for optional fields"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Assert
    assert peer.peer_id is None
    assert peer.client_name is None
    assert peer.last_seen == 0
    assert peer.last_connected == 0
    assert peer.connection_attempts == 0
    assert peer.choked is True
    assert peer.interested is False
    assert peer.has_pieces is None
    assert peer.download_speed == 0.0
    assert peer.upload_speed == 0.0
    assert peer.progress == 0.0
    assert peer.is_seed is False


def test_peer_info_creates_with_all_fields():
    """Test that PeerInfo can be created with all fields specified"""
    # Arrange
    peer_id = b"-DE13F0-123456789012"
    bitfield = b"\xff\x00"

    # Act
    peer = PeerInfo(
        ip="10.0.0.5",
        port=51413,
        peer_id=peer_id,
        client_name="Deluge 1.3.15",
        last_seen=1234567890.5,
        last_connected=1234567880.0,
        connection_attempts=3,
        choked=False,
        interested=True,
        has_pieces=bitfield,
        download_speed=125.5,
        upload_speed=50.2,
        progress=0.75,
        is_seed=True,
    )

    # Assert
    assert peer.ip == "10.0.0.5"
    assert peer.port == 51413
    assert peer.peer_id == peer_id
    assert peer.client_name == "Deluge 1.3.15"
    assert peer.last_seen == 1234567890.5
    assert peer.last_connected == 1234567880.0
    assert peer.connection_attempts == 3
    assert peer.choked is False
    assert peer.interested is True
    assert peer.has_pieces == bitfield
    assert peer.download_speed == 125.5
    assert peer.upload_speed == 50.2
    assert peer.progress == 0.75
    assert peer.is_seed is True


def test_peer_info_ip_can_be_ipv4():
    """Test that PeerInfo accepts IPv4 addresses"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Assert
    assert peer.ip == "192.168.1.1"


def test_peer_info_ip_can_be_ipv6():
    """Test that PeerInfo accepts IPv6 addresses"""
    # Arrange & Act
    peer = PeerInfo(ip="2001:db8::1", port=6881)

    # Assert
    assert peer.ip == "2001:db8::1"


def test_peer_info_ip_can_be_hostname():
    """Test that PeerInfo accepts hostnames"""
    # Arrange & Act
    peer = PeerInfo(ip="peer.example.com", port=6881)

    # Assert
    assert peer.ip == "peer.example.com"


def test_peer_info_port_accepts_valid_range():
    """Test that PeerInfo accepts valid port numbers"""
    # Arrange & Act
    peer1 = PeerInfo(ip="192.168.1.1", port=1)
    peer2 = PeerInfo(ip="192.168.1.1", port=6881)
    peer3 = PeerInfo(ip="192.168.1.1", port=65535)

    # Assert
    assert peer1.port == 1
    assert peer2.port == 6881
    assert peer3.port == 65535


def test_peer_info_peer_id_accepts_20_bytes():
    """Test that PeerInfo accepts 20-byte peer IDs"""
    # Arrange
    peer_id = b"-DE13F0-123456789012"

    # Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, peer_id=peer_id)

    # Assert
    assert peer.peer_id == peer_id
    assert len(peer.peer_id) == 20


def test_peer_info_client_name_accepts_string():
    """Test that PeerInfo accepts client name strings"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, client_name="qBittorrent 4.5.0")

    # Assert
    assert peer.client_name == "qBittorrent 4.5.0"


def test_peer_info_last_seen_accepts_timestamp():
    """Test that PeerInfo accepts float timestamp for last_seen"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, last_seen=1234567890.123)

    # Assert
    assert peer.last_seen == 1234567890.123


def test_peer_info_last_connected_accepts_timestamp():
    """Test that PeerInfo accepts float timestamp for last_connected"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, last_connected=1234567890.456)

    # Assert
    assert peer.last_connected == 1234567890.456


def test_peer_info_connection_attempts_increments():
    """Test that PeerInfo connection_attempts can be incremented"""
    # Arrange
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Act
    peer.connection_attempts += 1
    peer.connection_attempts += 1

    # Assert
    assert peer.connection_attempts == 2


def test_peer_info_choked_can_be_toggled():
    """Test that PeerInfo choked state can be toggled"""
    # Arrange
    peer = PeerInfo(ip="192.168.1.1", port=6881, choked=True)

    # Act
    peer.choked = False

    # Assert
    assert peer.choked is False


def test_peer_info_interested_can_be_toggled():
    """Test that PeerInfo interested state can be toggled"""
    # Arrange
    peer = PeerInfo(ip="192.168.1.1", port=6881, interested=False)

    # Act
    peer.interested = True

    # Assert
    assert peer.interested is True


def test_peer_info_has_pieces_accepts_bitfield():
    """Test that PeerInfo accepts bitfield for has_pieces"""
    # Arrange
    bitfield = b"\xff\x80\x00"

    # Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, has_pieces=bitfield)

    # Assert
    assert peer.has_pieces == bitfield


def test_peer_info_download_speed_accepts_float():
    """Test that PeerInfo accepts float for download_speed"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, download_speed=1024.5)

    # Assert
    assert peer.download_speed == 1024.5


def test_peer_info_upload_speed_accepts_float():
    """Test that PeerInfo accepts float for upload_speed"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, upload_speed=512.25)

    # Assert
    assert peer.upload_speed == 512.25


def test_peer_info_progress_accepts_percentage():
    """Test that PeerInfo accepts float percentage for progress"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, progress=0.5)

    # Assert
    assert peer.progress == 0.5


def test_peer_info_progress_can_be_zero():
    """Test that PeerInfo progress can be 0.0 (no pieces)"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, progress=0.0)

    # Assert
    assert peer.progress == 0.0


def test_peer_info_progress_can_be_one():
    """Test that PeerInfo progress can be 1.0 (complete)"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881, progress=1.0)

    # Assert
    assert peer.progress == 1.0


def test_peer_info_is_seed_identifies_seeders():
    """Test that PeerInfo is_seed identifies seeders"""
    # Arrange & Act
    leecher = PeerInfo(ip="192.168.1.1", port=6881, is_seed=False)
    seeder = PeerInfo(ip="192.168.1.2", port=6882, is_seed=True)

    # Assert
    assert leecher.is_seed is False
    assert seeder.is_seed is True


def test_peer_info_is_dataclass():
    """Test that PeerInfo is a dataclass"""
    # Arrange & Act
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Assert
    # Dataclasses have __dataclass_fields__ attribute
    assert hasattr(PeerInfo, "__dataclass_fields__")


def test_peer_info_equality():
    """Test that PeerInfo instances can be compared for equality"""
    # Arrange
    peer1 = PeerInfo(ip="192.168.1.1", port=6881, peer_id=b"12345678901234567890")
    peer2 = PeerInfo(ip="192.168.1.1", port=6881, peer_id=b"12345678901234567890")
    peer3 = PeerInfo(ip="192.168.1.2", port=6881, peer_id=b"12345678901234567890")

    # Act & Assert
    assert peer1 == peer2
    assert peer1 != peer3


def test_peer_info_repr():
    """Test that PeerInfo has readable repr"""
    # Arrange
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Act
    repr_str = repr(peer)

    # Assert
    assert "PeerInfo" in repr_str
    assert "192.168.1.1" in repr_str
    assert "6881" in repr_str


def test_peer_info_can_be_modified():
    """Test that PeerInfo instances are mutable"""
    # Arrange
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Act
    peer.download_speed = 1024.0
    peer.upload_speed = 512.0
    peer.progress = 0.5
    peer.choked = False
    peer.interested = True

    # Assert
    assert peer.download_speed == 1024.0
    assert peer.upload_speed == 512.0
    assert peer.progress == 0.5
    assert peer.choked is False
    assert peer.interested is True


def test_peer_info_speeds_can_be_updated():
    """Test that PeerInfo speeds can be updated over time"""
    # Arrange
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Act - simulate speed measurements
    peer.download_speed = 100.0
    peer.upload_speed = 50.0
    # Later measurement
    peer.download_speed = 150.0
    peer.upload_speed = 75.0

    # Assert
    assert peer.download_speed == 150.0
    assert peer.upload_speed == 75.0


def test_peer_info_connection_tracking():
    """Test that PeerInfo can track connection history"""
    # Arrange
    peer = PeerInfo(ip="192.168.1.1", port=6881)

    # Act - simulate connection attempts
    peer.connection_attempts = 0
    peer.last_connected = 1000.0
    peer.last_seen = 1000.0

    peer.connection_attempts += 1
    peer.last_connected = 2000.0
    peer.last_seen = 2500.0

    # Assert
    assert peer.connection_attempts == 1
    assert peer.last_connected == 2000.0
    assert peer.last_seen == 2500.0
