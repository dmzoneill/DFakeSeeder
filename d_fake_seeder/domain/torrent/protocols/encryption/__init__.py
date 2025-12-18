"""
Protocol Encryption Module.

Implements Message Stream Encryption (MSE/PE) for BitTorrent peer connections.
"""

from .mse import MSEHandler, MSEState

__all__ = ["MSEHandler", "MSEState"]
