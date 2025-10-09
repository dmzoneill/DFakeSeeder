"""
Unit tests for d_fake_seeder.lib.util.constants module.

Tests constant definitions, types, and value ranges.
"""

import pytest
from d_fake_seeder.lib.util.constants import (
    NetworkConstants,
    UIConstants,
    ProtocolConstants,
    AsyncConstants,
    BitTorrentProtocolConstants,
    DHTConstants,
    UDPTrackerConstants,
    TimeoutConstants,
    ConnectionConstants,
    RetryConstants,
    PeerExchangeConstants,
    UTPConstants,
    MultiTrackerConstants,
    SwarmIntelligenceConstants,
    CalculationConstants,
    SizeConstants,
)


# NetworkConstants tests
def test_network_constants_socket_timeouts_are_positive():
    """Test that socket timeout values are positive numbers"""
    # Arrange & Act & Assert
    assert NetworkConstants.DEFAULT_SOCKET_TIMEOUT > 0
    assert NetworkConstants.DEFAULT_CONNECT_TIMEOUT > 0
    assert NetworkConstants.DEFAULT_READ_TIMEOUT > 0


def test_network_constants_protocol_timeouts_are_positive():
    """Test that protocol timeout values are positive numbers"""
    # Arrange & Act & Assert
    assert NetworkConstants.HTTP_TIMEOUT > 0
    assert NetworkConstants.UDP_TIMEOUT > 0
    assert NetworkConstants.HANDSHAKE_TIMEOUT > 0


def test_network_constants_port_ranges_are_valid():
    """Test that port range constants are within valid TCP/UDP port range"""
    # Arrange & Act & Assert
    assert 1 <= NetworkConstants.PORT_RANGE_MIN <= 65535
    assert 1 <= NetworkConstants.PORT_RANGE_MAX <= 65535
    assert NetworkConstants.PORT_RANGE_MIN < NetworkConstants.PORT_RANGE_MAX
    assert 1 <= NetworkConstants.DEFAULT_PORT <= 65535


def test_network_constants_ephemeral_ports_are_valid():
    """Test that ephemeral port range is valid"""
    # Arrange & Act & Assert
    assert NetworkConstants.EPHEMERAL_PORT_MIN < NetworkConstants.EPHEMERAL_PORT_MAX
    assert NetworkConstants.EPHEMERAL_PORT_MIN >= 49152  # Standard ephemeral start
    assert NetworkConstants.EPHEMERAL_PORT_MAX == 65535


def test_network_constants_thread_timeouts_are_positive():
    """Test that thread timeout values are positive"""
    # Arrange & Act & Assert
    assert NetworkConstants.THREAD_JOIN_TIMEOUT > 0
    assert NetworkConstants.WORKER_SHUTDOWN_TIMEOUT > 0


# UIConstants tests
def test_ui_constants_margins_are_positive():
    """Test that UI margin values are positive integers"""
    # Arrange & Act & Assert
    assert UIConstants.MARGIN_LARGE > 0
    assert UIConstants.MARGIN_SMALL > 0
    assert UIConstants.MARGIN_MEDIUM > 0
    assert UIConstants.PADDING_DEFAULT > 0


def test_ui_constants_margin_sizes_are_ordered():
    """Test that margin sizes follow small < medium < large"""
    # Arrange & Act & Assert
    assert UIConstants.MARGIN_SMALL < UIConstants.MARGIN_MEDIUM
    assert UIConstants.MARGIN_MEDIUM < UIConstants.MARGIN_LARGE


def test_ui_constants_timings_are_positive():
    """Test that UI timing values are positive"""
    # Arrange & Act & Assert
    assert UIConstants.SPLASH_DURATION > 0
    assert UIConstants.NOTIFICATION_TIMEOUT > 0
    assert UIConstants.NOTIFICATION_DEFAULT > 0


def test_ui_constants_icon_sizes_are_valid():
    """Test that icon sizes list is properly formatted"""
    # Arrange & Act & Assert
    assert isinstance(UIConstants.ICON_SIZES, list)
    assert len(UIConstants.ICON_SIZES) > 0
    assert "256x256" in UIConstants.ICON_SIZES
    assert "16x16" in UIConstants.ICON_SIZES


# ProtocolConstants tests
def test_protocol_constants_intervals_are_positive():
    """Test that protocol interval values are positive"""
    # Arrange & Act & Assert
    assert ProtocolConstants.KEEP_ALIVE_INTERVAL > 0
    assert ProtocolConstants.CONTACT_INTERVAL > 0


def test_protocol_constants_piece_sizes_are_valid():
    """Test that piece size constants are valid"""
    # Arrange & Act & Assert
    assert ProtocolConstants.PIECE_SIZE_DEFAULT > 0
    assert ProtocolConstants.PIECE_SIZE_MAX > 0
    assert ProtocolConstants.PIECE_SIZE_DEFAULT <= ProtocolConstants.PIECE_SIZE_MAX


def test_protocol_constants_announce_intervals_are_ordered():
    """Test that announce interval constraints are properly ordered"""
    # Arrange & Act & Assert
    assert ProtocolConstants.ANNOUNCE_INTERVAL_MIN < ProtocolConstants.ANNOUNCE_INTERVAL_MIN_ALLOWED
    assert ProtocolConstants.ANNOUNCE_INTERVAL_MIN_ALLOWED < ProtocolConstants.ANNOUNCE_INTERVAL_MAX_ALLOWED


def test_protocol_constants_max_connections_is_positive():
    """Test that max connections default is positive"""
    # Arrange & Act & Assert
    assert ProtocolConstants.MAX_CONNECTIONS_DEFAULT > 0


# BitTorrentProtocolConstants tests
def test_bittorrent_protocol_handshake_structure():
    """Test BitTorrent protocol handshake structure constants"""
    # Arrange & Act & Assert
    assert BitTorrentProtocolConstants.HANDSHAKE_LENGTH == 68
    assert BitTorrentProtocolConstants.PROTOCOL_NAME_LENGTH == 19
    assert BitTorrentProtocolConstants.PROTOCOL_NAME == b"BitTorrent protocol"
    assert len(BitTorrentProtocolConstants.PROTOCOL_NAME) == BitTorrentProtocolConstants.PROTOCOL_NAME_LENGTH


def test_bittorrent_protocol_reserved_bytes():
    """Test BitTorrent reserved bytes constants"""
    # Arrange & Act & Assert
    assert BitTorrentProtocolConstants.RESERVED_BYTES_LENGTH == 8
    assert len(BitTorrentProtocolConstants.RESERVED_BYTES) == 8
    assert BitTorrentProtocolConstants.RESERVED_BYTES == b"\x00" * 8


def test_bittorrent_protocol_hash_lengths():
    """Test BitTorrent hash and ID length constants"""
    # Arrange & Act & Assert
    assert BitTorrentProtocolConstants.INFOHASH_LENGTH == 20  # SHA1 hash
    assert BitTorrentProtocolConstants.PEER_ID_LENGTH == 20


def test_bittorrent_protocol_peer_id_structure():
    """Test BitTorrent peer ID constants"""
    # Arrange & Act & Assert
    assert len(BitTorrentProtocolConstants.FAKE_SEEDER_PEER_ID_PREFIX) == 8
    assert BitTorrentProtocolConstants.FAKE_SEEDER_PEER_ID_SUFFIX_LENGTH == 12
    # Total should equal PEER_ID_LENGTH
    prefix_len = len(BitTorrentProtocolConstants.FAKE_SEEDER_PEER_ID_PREFIX)
    suffix_len = BitTorrentProtocolConstants.FAKE_SEEDER_PEER_ID_SUFFIX_LENGTH
    assert prefix_len + suffix_len == BitTorrentProtocolConstants.PEER_ID_LENGTH


def test_bittorrent_protocol_message_structure():
    """Test BitTorrent message structure constants"""
    # Arrange & Act & Assert
    assert BitTorrentProtocolConstants.MESSAGE_LENGTH_HEADER_BYTES == 4
    assert BitTorrentProtocolConstants.MESSAGE_ID_LENGTH_BYTES == 1
    assert BitTorrentProtocolConstants.KEEPALIVE_MESSAGE_LENGTH == 0


def test_bittorrent_protocol_bitfield_constants():
    """Test BitTorrent bitfield constants"""
    # Arrange & Act & Assert
    assert BitTorrentProtocolConstants.BITFIELD_BITS_PER_BYTE == 8
    assert BitTorrentProtocolConstants.FAKE_BITFIELD_SIZE_BYTES > 0
    assert BitTorrentProtocolConstants.DEFAULT_BITFIELD_SIZE_BYTES > 0


# DHTConstants tests
def test_dht_constants_node_id_is_sha1_size():
    """Test DHT node ID is 160 bits (SHA1)"""
    # Arrange & Act & Assert
    assert DHTConstants.NODE_ID_BITS == 160


def test_dht_constants_limits_are_positive():
    """Test DHT limit constants are positive"""
    # Arrange & Act & Assert
    assert DHTConstants.ROUTING_TABLE_SIZE_LIMIT > 0
    assert DHTConstants.MAX_PEERS_PER_INFOHASH > 0
    assert DHTConstants.MAX_FAIL_COUNT > 0


def test_dht_constants_timeouts_are_positive():
    """Test DHT timeout constants are positive"""
    # Arrange & Act & Assert
    assert DHTConstants.TOKEN_EXPIRY_SECONDS > 0
    assert DHTConstants.CHECK_INTERVAL_SECONDS > 0
    assert DHTConstants.RESPONSE_TIMEOUT_SECONDS > 0


# UDPTrackerConstants tests
def test_udp_tracker_magic_connection_id():
    """Test UDP tracker magic connection ID is defined"""
    # Arrange & Act & Assert
    assert UDPTrackerConstants.MAGIC_CONNECTION_ID == 0x41727101980


def test_udp_tracker_buffer_size_is_reasonable():
    """Test UDP tracker buffer size is reasonable"""
    # Arrange & Act & Assert
    assert UDPTrackerConstants.DEFAULT_BUFFER_SIZE >= 512
    assert UDPTrackerConstants.DEFAULT_BUFFER_SIZE <= 65536


def test_udp_tracker_data_structure_sizes():
    """Test UDP tracker data structure size constants"""
    # Arrange & Act & Assert
    assert UDPTrackerConstants.IPV4_WITH_PORT_LENGTH == 6  # 4 + 2 bytes
    assert UDPTrackerConstants.INFOHASH_LENGTH_BYTES == 20
    assert UDPTrackerConstants.PEER_ID_LENGTH_BYTES == 20


# ConnectionConstants tests
def test_connection_constants_limits_are_positive():
    """Test connection limit constants are positive"""
    # Arrange & Act & Assert
    assert ConnectionConstants.DEFAULT_MAX_INCOMING_CONNECTIONS > 0
    assert ConnectionConstants.DEFAULT_MAX_OUTGOING_CONNECTIONS > 0
    assert ConnectionConstants.DEFAULT_MAX_PEER_CONNECTIONS > 0
    assert ConnectionConstants.MAX_INCOMING_CONNECTIONS > 0
    assert ConnectionConstants.MAX_OUTGOING_CONNECTIONS > 0


def test_connection_constants_max_exceeds_default():
    """Test maximum connection limits exceed defaults"""
    # Arrange & Act & Assert
    assert ConnectionConstants.MAX_INCOMING_CONNECTIONS >= ConnectionConstants.DEFAULT_MAX_INCOMING_CONNECTIONS


def test_connection_constants_lifecycle_values():
    """Test connection lifecycle constants are valid"""
    # Arrange & Act & Assert
    assert ConnectionConstants.FAILED_CONNECTION_DISPLAY_CYCLES >= 0
    assert ConnectionConstants.MIN_DISPLAY_CYCLES > 0
    assert ConnectionConstants.TIMEOUT_CYCLES > 0
    assert ConnectionConstants.CLEANUP_INTERVAL_SECONDS > 0


# UTPConstants tests
def test_utp_constants_header_and_packet_sizes():
    """Test µTP packet size constants"""
    # Arrange & Act & Assert
    assert UTPConstants.HEADER_SIZE == 20
    assert UTPConstants.MAX_PACKET_SIZE == 1500  # Standard MTU
    assert UTPConstants.MAX_PAYLOAD_SIZE == UTPConstants.MAX_PACKET_SIZE - UTPConstants.HEADER_SIZE


def test_utp_constants_window_sizes_are_ordered():
    """Test µTP window size constraints"""
    # Arrange & Act & Assert
    assert UTPConstants.MIN_WINDOW_SIZE < UTPConstants.DEFAULT_WINDOW_SIZE
    assert UTPConstants.DEFAULT_WINDOW_SIZE < UTPConstants.MAX_WINDOW_SIZE


def test_utp_constants_timeouts_are_ordered():
    """Test µTP timeout constraints"""
    # Arrange & Act & Assert
    assert UTPConstants.MIN_TIMEOUT_MS < UTPConstants.INITIAL_TIMEOUT_MS
    assert UTPConstants.INITIAL_TIMEOUT_MS < UTPConstants.MAX_TIMEOUT_MS


def test_utp_constants_rtt_factors_sum_to_one():
    """Test µTP RTT smoothing factors sum to 1.0"""
    # Arrange & Act & Assert
    assert abs((UTPConstants.RTT_SMOOTHING_FACTOR + UTPConstants.RTT_SAMPLE_WEIGHT) - 1.0) < 0.001
    assert abs((UTPConstants.RTT_VARIANCE_SMOOTHING + UTPConstants.RTT_VARIANCE_WEIGHT) - 1.0) < 0.001


# SwarmIntelligenceConstants tests
def test_swarm_intelligence_seed_ratio_thresholds():
    """Test swarm intelligence seed ratio thresholds are properly ordered"""
    # Arrange & Act & Assert
    assert SwarmIntelligenceConstants.SEED_RATIO_LOW_THRESHOLD < SwarmIntelligenceConstants.SEED_RATIO_OPTIMAL_MIN
    assert SwarmIntelligenceConstants.SEED_RATIO_OPTIMAL_MIN < SwarmIntelligenceConstants.SEED_RATIO_OPTIMAL_MAX
    assert SwarmIntelligenceConstants.SEED_RATIO_OPTIMAL_MAX < SwarmIntelligenceConstants.SEED_RATIO_HIGH_THRESHOLD


def test_swarm_intelligence_peer_count_thresholds():
    """Test swarm intelligence peer count thresholds are properly ordered"""
    # Arrange & Act & Assert
    assert SwarmIntelligenceConstants.PEER_COUNT_VERY_LOW < SwarmIntelligenceConstants.PEER_COUNT_OPTIMAL_MIN
    assert SwarmIntelligenceConstants.PEER_COUNT_OPTIMAL_MIN < SwarmIntelligenceConstants.PEER_COUNT_OPTIMAL_MAX
    assert SwarmIntelligenceConstants.PEER_COUNT_OPTIMAL_MAX < SwarmIntelligenceConstants.PEER_COUNT_VERY_HIGH


def test_swarm_intelligence_health_scores_are_valid():
    """Test swarm intelligence health score constants are in [0, 1]"""
    # Arrange & Act & Assert
    assert SwarmIntelligenceConstants.HEALTH_SCORE_MIN == 0.0
    assert SwarmIntelligenceConstants.HEALTH_SCORE_MAX == 1.0
    assert 0.0 <= SwarmIntelligenceConstants.HEALTH_SCORE_THRESHOLD <= 1.0


def test_swarm_intelligence_score_multipliers_are_valid():
    """Test swarm intelligence score multipliers are in valid range"""
    # Arrange & Act & Assert
    assert 0.0 < SwarmIntelligenceConstants.SCORE_VERY_LOW_SEEDS < 1.0
    assert 0.0 < SwarmIntelligenceConstants.SCORE_HIGH_SEEDS < 1.0
    assert 0.0 < SwarmIntelligenceConstants.SCORE_VERY_FEW_PEERS < 1.0
    assert 0.0 < SwarmIntelligenceConstants.SCORE_MANY_PEERS < 1.0
    assert 0.0 < SwarmIntelligenceConstants.SCORE_STALLED_PEERS < 1.0


def test_swarm_intelligence_behavior_multipliers_are_positive():
    """Test swarm intelligence behavior multipliers are positive"""
    # Arrange & Act & Assert
    assert SwarmIntelligenceConstants.BOOST_UPLOAD_MULTIPLIER > 1.0
    assert SwarmIntelligenceConstants.BOOST_CONNECTION_MULTIPLIER > 1.0
    assert SwarmIntelligenceConstants.BOOST_ANNOUNCE_MULTIPLIER < 1.0  # Lower interval = more frequent
    assert SwarmIntelligenceConstants.REDUCE_UPLOAD_MULTIPLIER < 1.0
    assert SwarmIntelligenceConstants.REDUCE_CONNECTION_MULTIPLIER < 1.0


# CalculationConstants tests
def test_calculation_constants_byte_conversions():
    """Test calculation byte conversion constants"""
    # Arrange & Act & Assert
    assert CalculationConstants.BYTES_PER_KB == 1024
    assert CalculationConstants.KB_TO_BYTES_MULTIPLIER == 1024


def test_calculation_constants_jitter_percent_is_valid():
    """Test jitter percentage is reasonable"""
    # Arrange & Act & Assert
    assert 0.0 < CalculationConstants.ANNOUNCE_JITTER_PERCENT < 1.0


# SizeConstants tests
def test_size_constants_basic_units_list():
    """Test size units basic list contains expected values"""
    # Arrange & Act & Assert
    assert isinstance(SizeConstants.SIZE_UNITS_BASIC, list)
    assert "B" in SizeConstants.SIZE_UNITS_BASIC
    assert "KB" in SizeConstants.SIZE_UNITS_BASIC
    assert "MB" in SizeConstants.SIZE_UNITS_BASIC
    assert "GB" in SizeConstants.SIZE_UNITS_BASIC
    assert "TB" in SizeConstants.SIZE_UNITS_BASIC


def test_size_constants_extended_units_include_basic():
    """Test extended size units include all basic units"""
    # Arrange & Act & Assert
    assert isinstance(SizeConstants.SIZE_UNITS_EXTENDED, list)
    for unit in SizeConstants.SIZE_UNITS_BASIC:
        assert unit in SizeConstants.SIZE_UNITS_EXTENDED
    assert "PB" in SizeConstants.SIZE_UNITS_EXTENDED


# Backward compatibility tests
def test_backward_compatibility_constants_exist():
    """Test backward compatibility module-level constants exist"""
    # Arrange & Act & Assert
    from d_fake_seeder.lib.util.constants import (
        SIZE_UNITS_BASIC,
        SIZE_UNITS_EXTENDED,
        DEFAULT_PIECE_SIZE,
        MAX_PIECE_SIZE,
        DEFAULT_SOCKET_TIMEOUT,
        DEFAULT_ICON_SIZES,
        HANDSHAKE_LENGTH,
        PROTOCOL_NAME,
    )

    assert SIZE_UNITS_BASIC is not None
    assert SIZE_UNITS_EXTENDED is not None
    assert DEFAULT_PIECE_SIZE > 0
    assert MAX_PIECE_SIZE > 0
    assert DEFAULT_SOCKET_TIMEOUT > 0
    assert len(DEFAULT_ICON_SIZES) > 0
    assert HANDSHAKE_LENGTH == 68
    assert PROTOCOL_NAME == b"BitTorrent protocol"


def test_backward_compatibility_matches_class_constants():
    """Test backward compatibility constants match class constants"""
    # Arrange & Act & Assert
    from d_fake_seeder.lib.util.constants import (
        SIZE_UNITS_BASIC,
        DEFAULT_PIECE_SIZE,
        MAX_PIECE_SIZE,
        DEFAULT_SOCKET_TIMEOUT,
    )

    assert SIZE_UNITS_BASIC == SizeConstants.SIZE_UNITS_BASIC
    assert DEFAULT_PIECE_SIZE == ProtocolConstants.PIECE_SIZE_DEFAULT
    assert MAX_PIECE_SIZE == ProtocolConstants.PIECE_SIZE_MAX
    assert DEFAULT_SOCKET_TIMEOUT == NetworkConstants.DEFAULT_SOCKET_TIMEOUT
