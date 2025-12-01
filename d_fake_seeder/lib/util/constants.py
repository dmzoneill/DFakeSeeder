"""
Shared constants for the DFakeSeeder application.

This module centralizes commonly used constants to avoid duplication
across the codebase and provide a single source of truth for shared values.

Constants are organized into logical classes for better organization and
to make it clear which category each constant belongs to.
"""


class NetworkConstants:
    """Network-related timeout and connection constants."""

    # Socket timeouts (seconds)
    DEFAULT_SOCKET_TIMEOUT = 30.0
    DEFAULT_CONNECT_TIMEOUT = 10.0
    DEFAULT_READ_TIMEOUT = 60.0

    # HTTP/UDP timeouts (seconds)
    HTTP_TIMEOUT = 10.0
    UDP_TIMEOUT = 5.0
    HANDSHAKE_TIMEOUT = 30.0

    # Port ranges
    PORT_RANGE_MIN = 1025
    PORT_RANGE_MAX = 65535
    DEFAULT_PORT = 6881
    EPHEMERAL_PORT_MIN = 49152
    EPHEMERAL_PORT_MAX = 65535

    # Thread join timeouts (seconds)
    THREAD_JOIN_TIMEOUT = 1.0
    WORKER_SHUTDOWN_TIMEOUT = 0.5

    # Tracker semaphore timeouts (seconds)
    TRACKER_SEMAPHORE_TIMEOUT = 5.0
    TRACKER_SEMAPHORE_QUICK_TIMEOUT = 2.0
    TRACKER_SEMAPHORE_SHORT_TIMEOUT = 3.0


class UIConstants:
    """UI-related margins, padding, and timing constants."""

    # Margins and spacing (pixels)
    MARGIN_LARGE = 10
    MARGIN_SMALL = 5
    MARGIN_MEDIUM = 8
    PADDING_DEFAULT = 6

    # Timing (milliseconds)
    SPLASH_DURATION = 2000
    NOTIFICATION_TIMEOUT = 5000
    NOTIFICATION_DEFAULT = 3000

    # Icon sizes
    ICON_SIZES = [
        "16x16",
        "32x32",
        "48x48",
        "64x64",
        "96x96",
        "128x128",
        "192x192",
        "256x256",
    ]


class ProtocolConstants:
    """BitTorrent protocol constants."""

    # Message intervals (seconds)
    KEEP_ALIVE_INTERVAL = 120
    CONTACT_INTERVAL = 300

    # Piece sizes (bytes)
    PIECE_SIZE_DEFAULT = 16384  # 16KB
    PIECE_SIZE_MAX = 32768  # 32KB
    BITFIELD_BYTE_SIZE = 32

    # Announce intervals (seconds)
    ANNOUNCE_INTERVAL_DEFAULT = 1800  # 30 minutes
    ANNOUNCE_INTERVAL_MIN = 60
    ANNOUNCE_INTERVAL_MIN_ALLOWED = 300
    ANNOUNCE_INTERVAL_MAX_ALLOWED = 7200

    # Connection limits
    MAX_CONNECTIONS_DEFAULT = 50
    FAILED_CONNECTION_TIMEOUT_CYCLES = 3


class AsyncConstants:
    """Async operation timeouts (seconds)."""

    # Peer protocol manager timeouts
    MANAGE_CONNECTIONS_TIMEOUT = 1.0
    SEND_KEEP_ALIVES_TIMEOUT = 1.0
    POLL_PEER_STATUS_TIMEOUT = 0.5
    EXCHANGE_METADATA_TIMEOUT = 1.0
    ROTATE_CONNECTIONS_TIMEOUT = 1.0
    CLEANUP_CONNECTIONS_TIMEOUT = 1.0

    # DHT operation timeouts
    DHT_RESPONSE_TIMEOUT = 10.0
    DHT_RESPONSE_SHORT_TIMEOUT = 5.0

    # Async executor timeouts
    EXECUTOR_SHUTDOWN_TIMEOUT = 2.0


class BitTorrentProtocolConstants:
    """BitTorrent protocol-specific constants."""

    # Handshake structure
    HANDSHAKE_LENGTH = 68
    PROTOCOL_NAME = b"BitTorrent protocol"
    PROTOCOL_NAME_LENGTH = 19
    RESERVED_BYTES_LENGTH = 8
    RESERVED_BYTES = b"\x00" * 8
    INFOHASH_LENGTH = 20
    PEER_ID_LENGTH = 20

    # Message structure
    MESSAGE_LENGTH_HEADER_BYTES = 4
    MESSAGE_ID_LENGTH_BYTES = 1
    MESSAGE_PAYLOAD_START_OFFSET = 1
    KEEPALIVE_MESSAGE_LENGTH = 0

    # Fake Seeder identifiers
    FAKE_SEEDER_PEER_ID_PREFIX = b"-FS0001-"
    FAKE_SEEDER_PEER_ID_SUFFIX_LENGTH = 12

    # Message payload sizes
    REQUEST_PAYLOAD_SIZE = 12
    HAVE_PAYLOAD_SIZE = 4
    DONTHAVE_PAYLOAD_SIZE = 4
    PIECE_MESSAGE_HEADER_SIZE = 9

    # Bitfield
    BITFIELD_BITS_PER_BYTE = 8
    FAKE_BITFIELD_SIZE_BYTES = 32
    DEFAULT_BITFIELD_SIZE_BYTES = 32

    # Piece data
    DEFAULT_FAKE_PIECE_SIZE_KB = 16
    MAX_PIECE_REQUEST_SIZE_BYTES = 32768

    # Reserved bits for protocol extensions
    EXTENSION_PROTOCOL_BIT = 0x10
    DHT_BIT = 0x01
    FAST_EXTENSION_BIT = 0x04

    # Protocol extension limits
    MAX_ALLOWED_FAST_PIECES = 10
    MAX_SUGGEST_PIECES = 5

    # Metadata extension
    FAKE_METADATA_PIECE_COUNT = 32

    # Probabilities for simulation
    PIECE_UNAVAILABLE_PROBABILITY = 0.05

    # ASCII ranges for peer ID generation
    PRINTABLE_ASCII_MIN = 32
    PRINTABLE_ASCII_MAX = 126


class DHTConstants:
    """DHT (Distributed Hash Table) protocol constants."""

    # Node identification
    NODE_ID_BITS = 160  # SHA1-based 160-bit node IDs
    ROUTING_TABLE_SIZE_LIMIT = 100

    # Peer storage
    MAX_PEERS_PER_INFOHASH = 200

    # Node health tracking
    MAX_FAIL_COUNT = 5

    # Token management
    TOKEN_EXPIRY_SECONDS = 600  # 10 minutes

    # Timing intervals
    CHECK_INTERVAL_SECONDS = 60
    RATE_LIMIT_DELAY_SECONDS = 1

    # Timeouts
    RESPONSE_TIMEOUT_SECONDS = 10
    RESPONSE_SHORT_TIMEOUT = 5


class UDPTrackerConstants:
    """UDP tracker protocol constants."""

    # Magic protocol identifier
    MAGIC_CONNECTION_ID = 0x41727101980

    # Network settings
    DEFAULT_BUFFER_SIZE = 2048
    DEFAULT_PORT = 6881

    # Data structure sizes
    IPV4_WITH_PORT_LENGTH = 6  # 4 bytes IP + 2 bytes port
    INFOHASH_LENGTH_BYTES = 20
    PEER_ID_LENGTH_BYTES = 20

    # Logging limits
    PEER_LOG_LIMIT = 5  # Log first N peers


class TimeoutConstants:
    """Centralized timeout values for various operations (seconds)."""

    # Thread shutdown timeouts - OPTIMIZED FOR FAST SHUTDOWN
    WORKER_SHUTDOWN = 0.2  # Reduced from 0.5 for faster per-thread response
    SERVER_THREAD_SHUTDOWN = 0.5  # Reduced from 1.0 for faster server shutdown
    MANAGER_THREAD_JOIN = 1.0  # Reduced from 5.0 for faster manager shutdown
    AGGREGATE_SHUTDOWN_BUDGET = 2.0  # Total time budget for parallel shutdown

    # Tracker operation timeouts
    TRACKER_SEMAPHORE_LOAD = 5.0
    TRACKER_SEMAPHORE_ANNOUNCE = 2.0
    TRACKER_SEMAPHORE_UDP = 3.0

    # Peer protocol operation timeouts
    PEER_PROTOCOL_OPERATION = 1.0
    PEER_STATUS_POLL = 0.5
    PEER_MANAGER_SLEEP_CHUNK = 0.1

    # Retry delays
    TORRENT_PEER_RETRY = 3
    HTTP_RETRY_MAX_SLEEP = 1.0
    TRAY_RETRY_DELAY = 1
    TRAY_STARTUP_DELAY = 2


class ConnectionConstants:
    """Connection management constants."""

    # Connection limits
    DEFAULT_MAX_INCOMING_CONNECTIONS = 50
    DEFAULT_MAX_OUTGOING_CONNECTIONS = 50
    DEFAULT_MAX_PEER_CONNECTIONS = 50
    MAX_INCOMING_CONNECTIONS = 200
    MAX_OUTGOING_CONNECTIONS = 50

    # Connection lifecycle
    FAILED_CONNECTION_DISPLAY_CYCLES = 1
    MIN_DISPLAY_CYCLES = 1
    TIMEOUT_CYCLES = 3
    CLEANUP_INTERVAL_SECONDS = 2

    # Fake piece configuration
    FAKE_PIECE_COUNT_MAX = 1000


class RetryConstants:
    """Retry limits and delays."""

    # HTTP announce retries
    HTTP_ANNOUNCE_MAX_RETRIES = 3

    # Tray application retries
    TRAY_DBUS_MAX_RETRIES = 5


class PeerExchangeConstants:
    """Peer Exchange (PEX) protocol constants."""

    # IP address class ranges (for private IP detection)
    CLASS_A_FIRST_OCTET_MIN = 1
    CLASS_A_FIRST_OCTET_MAX = 126
    CLASS_B_FIRST_OCTET_MIN = 128
    CLASS_B_FIRST_OCTET_MAX = 191
    CLASS_C_FIRST_OCTET_MIN = 192
    CLASS_C_FIRST_OCTET_MAX = 223

    # Port ranges
    WELL_KNOWN_PORT_MIN = 6881
    WELL_KNOWN_PORT_MAX = 6889
    EPHEMERAL_PORT_MIN = 49152
    EPHEMERAL_PORT_MAX = 65535

    # PEX flags
    FLAGS_MIN = 0
    FLAGS_MAX = 3


class UTPConstants:
    """µTP (Micro Transport Protocol) constants (BEP-029)."""

    # Packet structure
    HEADER_SIZE = 20  # µTP header is 20 bytes
    MAX_PACKET_SIZE = 1500  # Standard MTU size
    MAX_PAYLOAD_SIZE = MAX_PACKET_SIZE - HEADER_SIZE

    # Window sizes (bytes)
    DEFAULT_WINDOW_SIZE = 1048576  # 1MB
    MIN_WINDOW_SIZE = 65536  # 64KB
    MAX_WINDOW_SIZE = 4194304  # 4MB
    WINDOW_INCREASE_STEP = 3000  # Bytes to increase window per RTT
    WINDOW_DECREASE_STEP = 1500  # Bytes to decrease window on congestion

    # Timeouts and delays (milliseconds)
    INITIAL_TIMEOUT_MS = 1000  # 1 second initial timeout
    MIN_TIMEOUT_MS = 500  # 500ms minimum timeout
    MAX_TIMEOUT_MS = 60000  # 60 seconds maximum timeout
    TARGET_DELAY_MS = 100  # Target queuing delay for LEDBAT

    # Connection limits
    DEFAULT_MAX_CONNECTIONS = 100
    MAX_SEQUENCE_NUMBER = 65536  # 16-bit sequence number wraps at this value
    MAX_RANDOM_SEQUENCE = 65535  # Maximum value for random sequence number

    # RTT calculation
    RTT_SMOOTHING_FACTOR = 0.875  # Exponential moving average for RTT (7/8)
    RTT_SAMPLE_WEIGHT = 0.125  # Weight for new RTT sample (1/8)
    RTT_VARIANCE_SMOOTHING = 0.75  # Smoothing factor for variance (3/4)
    RTT_VARIANCE_WEIGHT = 0.25  # Weight for new variance sample (1/4)
    RTT_TIMEOUT_MULTIPLIER = 4  # Multiply variance by this for timeout calculation

    # Timestamp conversion
    MICROSECONDS_PER_SECOND = 1000000
    MILLISECONDS_PER_SECOND = 1000

    # Packet type masks
    PACKET_TYPE_MASK = 0x0F  # Lower 4 bits for packet type
    VERSION_MASK = 0x0F  # Lower 4 bits for version
    VERSION_SHIFT = 4  # Shift for version in first byte
    VERSION_TYPE_MASK = 0xFFFFFFFF  # Mask for 32-bit timestamp

    # Packet types (defined in UTPPacketType enum)
    # ST_DATA = 0, ST_FIN = 1, ST_STATE = 2, ST_RESET = 3, ST_SYN = 4


class MultiTrackerConstants:
    """Multi-Tracker protocol constants (BEP-012)."""

    # Tracker health and failover
    MAX_CONSECUTIVE_FAILURES = 5  # Disable tracker after this many failures
    BACKOFF_BASE_SECONDS = 60  # Base seconds for exponential backoff
    BACKOFF_EXPONENT_BASE = 2  # Exponential base for backoff calculation
    MAX_BACKOFF_SECONDS = 3600  # Maximum backoff time (1 hour)

    # Tracker statistics
    RESPONSE_TIME_SMOOTHING = 0.8  # Smoothing factor for average response time
    RESPONSE_TIME_WEIGHT = 0.2  # Weight for new response time sample


class SwarmIntelligenceConstants:
    """Swarm Intelligence system constants."""

    # Swarm health thresholds
    SEED_RATIO_LOW_THRESHOLD = 0.05  # Too few seeds
    SEED_RATIO_HIGH_THRESHOLD = 0.5  # Too many seeds (oversaturated)
    SEED_RATIO_OPTIMAL_MIN = 0.1  # Optimal minimum seed ratio
    SEED_RATIO_OPTIMAL_MAX = 0.3  # Optimal maximum seed ratio

    # Peer count thresholds
    PEER_COUNT_VERY_LOW = 5  # Very unhealthy swarm
    PEER_COUNT_OPTIMAL_MIN = 20  # Minimum optimal peer count
    PEER_COUNT_OPTIMAL_MAX = 200  # Maximum optimal peer count
    PEER_COUNT_VERY_HIGH = 500  # Very large swarm

    # Health scoring
    HEALTH_SCORE_MIN = 0.0  # Minimum health score
    HEALTH_SCORE_MAX = 1.0  # Maximum health score
    HEALTH_SCORE_THRESHOLD = 0.5  # Threshold for "healthy" swarm

    # Health score multipliers
    SCORE_VERY_LOW_SEEDS = 0.3  # Score multiplier for very low seed ratio
    SCORE_HIGH_SEEDS = 0.7  # Score multiplier for oversaturated seeds
    SCORE_VERY_FEW_PEERS = 0.4  # Score multiplier for very few peers
    SCORE_MANY_PEERS = 0.8  # Score multiplier for very large swarm
    SCORE_STALLED_PEERS = 0.6  # Score multiplier for many stalled peers

    # Upload speed thresholds
    STALLED_SPEED_THRESHOLD = 1024  # Below this is considered stalled (1 KB/s)
    STALLED_RATIO_THRESHOLD = 0.5  # Ratio of stalled peers that affects score

    # Behavior adjustment multipliers
    BOOST_UPLOAD_MULTIPLIER = 1.5  # Increase upload for unhealthy swarms
    BOOST_CONNECTION_MULTIPLIER = 1.3  # Increase connections for unhealthy swarms
    BOOST_ANNOUNCE_MULTIPLIER = 0.8  # Announce more frequently (lower interval)

    REDUCE_UPLOAD_MULTIPLIER = 0.7  # Reduce upload for oversaturated swarms
    REDUCE_CONNECTION_MULTIPLIER = 0.8  # Reduce connections for oversaturated swarms
    REDUCE_ANNOUNCE_MULTIPLIER = 1.2  # Announce less frequently (higher interval)

    PAUSE_UPLOAD_MULTIPLIER = 0.3  # Minimal upload when paused
    PAUSE_CONNECTION_MULTIPLIER = 0.5  # Minimal connections when paused
    PAUSE_ANNOUNCE_MULTIPLIER = 2.0  # Much less frequent announces when paused

    # Piece selection
    ENDGAME_COMPLETION_THRESHOLD = 0.95  # Enter endgame mode at 95% complete


class CalculationConstants:
    """Constants used in calculations and conversions."""

    # Byte conversions
    BYTES_PER_KB = 1024
    KB_TO_BYTES_MULTIPLIER = 1024
    SPEED_CALCULATION_DIVISOR = 1000  # For download speed calculations

    # Jitter calculations
    ANNOUNCE_JITTER_PERCENT = 0.1  # ±10% jitter
    JITTER_RANGE_MULTIPLIER = 2  # For random.uniform(-1, 1) * jitter
    JITTER_OFFSET_ADJUSTMENT = -1  # For centering jitter range


class SizeConstants:
    """File size units and conversions."""

    # Size unit arrays
    SIZE_UNITS_BASIC = ["B", "KB", "MB", "GB", "TB"]
    SIZE_UNITS_EXTENDED = ["B", "KB", "MB", "GB", "TB", "PB"]


# Backward compatibility: Keep module-level constants for existing code
# These will be deprecated in favor of class-based constants

# Size units
SIZE_UNITS_BASIC = SizeConstants.SIZE_UNITS_BASIC
SIZE_UNITS_EXTENDED = SizeConstants.SIZE_UNITS_EXTENDED

# BitTorrent protocol
DEFAULT_PIECE_SIZE = ProtocolConstants.PIECE_SIZE_DEFAULT
MAX_PIECE_SIZE = ProtocolConstants.PIECE_SIZE_MAX
BITFIELD_BYTE_SIZE = ProtocolConstants.BITFIELD_BYTE_SIZE

# Network timeouts
DEFAULT_SOCKET_TIMEOUT = NetworkConstants.DEFAULT_SOCKET_TIMEOUT
DEFAULT_CONNECT_TIMEOUT = NetworkConstants.DEFAULT_CONNECT_TIMEOUT
DEFAULT_READ_TIMEOUT = NetworkConstants.DEFAULT_READ_TIMEOUT

# UI
DEFAULT_ICON_SIZES = UIConstants.ICON_SIZES

# Additional backward compatibility for commonly used constants
HANDSHAKE_LENGTH = BitTorrentProtocolConstants.HANDSHAKE_LENGTH
PROTOCOL_NAME = BitTorrentProtocolConstants.PROTOCOL_NAME
INFOHASH_LENGTH = BitTorrentProtocolConstants.INFOHASH_LENGTH
PEER_ID_LENGTH = BitTorrentProtocolConstants.PEER_ID_LENGTH
