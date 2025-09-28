"""
Shared constants for the DFakeSeeder application.

This module centralizes commonly used constants to avoid duplication
across the codebase and provide a single source of truth for shared values.
"""

# File size unit constants
SIZE_UNITS_BASIC = ["B", "KB", "MB", "GB", "TB"]
SIZE_UNITS_EXTENDED = ["B", "KB", "MB", "GB", "TB", "PB"]

# BitTorrent protocol constants
DEFAULT_PIECE_SIZE = 16384  # 16KB pieces
MAX_PIECE_SIZE = 32768  # 32KB max piece size
BITFIELD_BYTE_SIZE = 32  # Default bitfield size in bytes

# Network timeouts (seconds)
DEFAULT_SOCKET_TIMEOUT = 30.0
DEFAULT_CONNECT_TIMEOUT = 10.0
DEFAULT_READ_TIMEOUT = 60.0

# UI constants
DEFAULT_ICON_SIZES = ["16x16", "32x32", "48x48", "64x64", "96x96", "128x128", "192x192", "256x256"]
