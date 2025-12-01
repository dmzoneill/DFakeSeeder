"""
BitTorrent Extension Protocol Implementation (BEP-010)

Implements the Extension Protocol that allows BitTorrent clients to send
extension messages and exchange metadata about supported extensions.
"""

# fmt: off
from .donthave import DontHaveExtension
from .fast_extension import FastExtension
from .manager import ExtensionManager
from .metadata import MetadataExtension
from .pex import PeerExchangeExtension

__all__ = [
    "ExtensionManager",
    "MetadataExtension",
    "PeerExchangeExtension",
    "DontHaveExtension",
    "FastExtension",
]

# fmt: on
