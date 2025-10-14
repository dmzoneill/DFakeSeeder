"""
Mock data fixtures for DFakeSeeder tests

Provides reusable test data including:
- Sample torrent metadata
- Peer information
- Tracker responses
- Settings configurations
"""

# =============================================================================
# Torrent Test Data
# =============================================================================

SAMPLE_TORRENT_DICT = {
    "announce": "http://tracker.example.com:6969/announce",
    "announce-list": [
        ["http://tracker.example.com:6969/announce"],
        ["http://backup.tracker.com:6969/announce"],
    ],
    "comment": "Test torrent file",
    "created by": "DFakeSeeder Test Suite",
    "creation date": 1609459200,  # 2021-01-01 00:00:00 UTC
    "info": {
        "name": "test_torrent",
        "piece length": 16384,
        "pieces": b"\x00" * 20,  # Single piece hash
        "length": 1024,  # Single file torrent
    },
}

SAMPLE_MULTI_FILE_TORRENT_DICT = {
    "announce": "http://tracker.example.com:6969/announce",
    "info": {
        "name": "multi_file_torrent",
        "piece length": 16384,
        "pieces": b"\x00" * 40,  # Two piece hashes
        "files": [
            {"length": 512, "path": ["file1.txt"]},
            {"length": 1024, "path": ["subdir", "file2.txt"]},
        ],
    },
}


# =============================================================================
# Peer Test Data
# =============================================================================

SAMPLE_PEER_DATA = {
    "address": "192.0.2.1",
    "port": 51413,
    "peer_id": "-UT3410-123456789012",
    "client": "μTorrent 3.4.1.0",
    "progress": 0.75,
    "down_speed": 102400,  # 100 KB/s
    "up_speed": 51200,  # 50 KB/s
    "seed": False,
}

SAMPLE_CONNECTION_PEER_DATA = {
    "address": "192.0.2.2",
    "port": 6881,
    "peer_id": "-DE13D0-987654321098",
    "client": "Deluge 1.3.13",
    "direction": "incoming",
    "torrent_hash": "0123456789abcdef0123456789abcdef01234567",
    "connected": True,
    "handshake_complete": True,
    "status": "connected",
}


# =============================================================================
# Tracker Test Data
# =============================================================================

SAMPLE_TRACKER_RESPONSE = {
    "interval": 1800,
    "min interval": 300,
    "complete": 42,  # seeders
    "incomplete": 15,  # leechers
    "downloaded": 127,  # completed downloads
    "peers": [
        {"peer id": "-UT3410-111111111111", "ip": "192.0.2.10", "port": 51413},
        {"peer id": "-DE13D0-222222222222", "ip": "192.0.2.11", "port": 6881},
        {"peer id": "-TR2940-333333333333", "ip": "192.0.2.12", "port": 51000},
    ],
}

SAMPLE_TRACKER_ERROR_RESPONSE = {"failure reason": "Invalid info_hash"}

SAMPLE_UDP_TRACKER_RESPONSE = {
    "action": 1,  # announce response
    "transaction_id": 12345,
    "interval": 1800,
    "leechers": 15,
    "seeders": 42,
    "peers": [
        (3221225994, 51413),  # IP as int, port
        (3221225995, 6881),
        (3221225996, 51000),
    ],
}


# =============================================================================
# Settings Test Data
# =============================================================================

SAMPLE_SETTINGS = {
    "language": "en",
    "tickspeed": 10,
    "listening_port": 6881,
    "enable_upnp": True,
    "enable_dht": True,
    "enable_pex": True,
    "upload_speed": 50,
    "download_speed": 500,
    "announce_interval": 1800,
    "max_incoming_connections": 100,
    "max_outgoing_connections": 100,
    "peer_protocol": {
        "handshake_timeout_seconds": 30.0,
        "message_read_timeout_seconds": 60.0,
        "keep_alive_interval_seconds": 120.0,
        "contact_interval_seconds": 300.0,
    },
    "seeders": {
        "port_range_min": 1025,
        "port_range_max": 65000,
        "udp_timeout_seconds": 5,
        "http_timeout_seconds": 10,
    },
    "ui_settings": {
        "splash_display_duration_seconds": 2,
        "notification_timeout_min_ms": 2000,
    },
}

MINIMAL_SETTINGS = {
    "language": "en",
    "tickspeed": 10,
    "listening_port": 6881,
}


# =============================================================================
# BitTorrent Protocol Data
# =============================================================================

# BitTorrent handshake components
BITTORRENT_PROTOCOL_NAME = b"BitTorrent protocol"
BITTORRENT_PROTOCOL_LENGTH = len(BITTORRENT_PROTOCOL_NAME)

SAMPLE_INFO_HASH = b"\x01\x23\x45\x67\x89\xab\xcd\xef" * 2 + b"\x01\x23\x45\x67"  # 20 bytes
SAMPLE_PEER_ID = b"-DFS010-123456789012"  # 20 bytes

# BitTorrent message type IDs
MESSAGE_CHOKE = 0
MESSAGE_UNCHOKE = 1
MESSAGE_INTERESTED = 2
MESSAGE_NOT_INTERESTED = 3
MESSAGE_HAVE = 4
MESSAGE_BITFIELD = 5
MESSAGE_REQUEST = 6
MESSAGE_PIECE = 7
MESSAGE_CANCEL = 8

# Extension protocol
MESSAGE_EXTENDED = 20
EXTENSION_HANDSHAKE = 0


# =============================================================================
# Bencode Test Data
# =============================================================================

BENCODE_INTEGER = b"i42e"
BENCODE_INTEGER_EXPECTED = 42

BENCODE_STRING = b"5:hello"
BENCODE_STRING_EXPECTED = b"hello"

BENCODE_LIST = b"li1ei2ei3ee"
BENCODE_LIST_EXPECTED = [1, 2, 3]

BENCODE_DICT = b"d3:foo3:bar3:bazi42ee"
BENCODE_DICT_EXPECTED = {b"foo": b"bar", b"baz": 42}
