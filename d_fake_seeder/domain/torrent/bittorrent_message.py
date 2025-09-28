"""
BitTorrent Protocol Message Constants

Defines message type constants for the BitTorrent protocol.
"""


class BitTorrentMessage:
    """BitTorrent protocol message types"""

    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7
    CANCEL = 8
    PORT = 9  # DHT extension

    # Extended protocol messages (BEP-010)
    EXTENDED = 20
