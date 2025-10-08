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
