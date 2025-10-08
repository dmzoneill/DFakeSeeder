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
    ICON_SIZES = ["16x16", "32x32", "48x48", "64x64", "96x96", "128x128", "192x192", "256x256"]


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

    # Thread shutdown timeouts
    WORKER_SHUTDOWN = 0.5
    SERVER_THREAD_SHUTDOWN = 1.0
    MANAGER_THREAD_JOIN = 5.0

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
