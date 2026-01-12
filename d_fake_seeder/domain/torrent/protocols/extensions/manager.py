"""
Extension Protocol Manager (BEP-010)

Manages BitTorrent protocol extensions and handles extension handshakes.
Coordinates between different extension implementations.
"""

# fmt: off
import struct
from typing import Any, Dict

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.bittorrent_message import BitTorrentMessage
from d_fake_seeder.lib.logger import logger

try:
    import bencodepy as bencode
except ImportError:
    from d_fake_seeder.domain.torrent.bencoding import bencode

# fmt: on


class ExtensionManager:
    """Manages BitTorrent protocol extensions"""

    def __init__(self, peer_connection: Any) -> None:
        """
        Initialize extension manager

        Args:
            peer_connection: PeerConnection instance
        """
        self.peer_connection = peer_connection
        self.settings = AppSettings.get_instance()

        # Extension configuration
        extensions_config = getattr(self.settings, "protocols", {}).get("extensions", {})
        self.ut_metadata_enabled = extensions_config.get("ut_metadata", True)
        self.ut_pex_enabled = extensions_config.get("ut_pex", True)
        self.lt_donthave_enabled = extensions_config.get("lt_donthave", True)

        # Extension registry
        self.supported_extensions = {}  # type: ignore[var-annotated]
        self.peer_extensions: Dict[str, Any] = {}  # Extensions supported by peer
        self.extension_instances: Dict[str, Any] = {}  # Active extension instances

        # Extension message IDs (negotiated during handshake)
        self.local_extension_ids: Dict[str, Any] = {}  # Our extension name -> message ID
        self.remote_extension_ids: Dict[str, Any] = {}  # Peer's extension name -> message ID

        self._register_extensions()

        logger.trace(
            "Extension manager initialized",
            extra={
                "class_name": self.__class__.__name__,
                "supported_extensions": list(self.supported_extensions.keys()),
            },
        )

    def _register_extensions(self) -> Any:
        """Register supported extensions"""
        if self.ut_metadata_enabled:
            from .metadata import MetadataExtension

            self.supported_extensions["ut_metadata"] = MetadataExtension

        if self.ut_pex_enabled:
            from .pex import PeerExchangeExtension

            self.supported_extensions["ut_pex"] = PeerExchangeExtension

        if self.lt_donthave_enabled:
            from .donthave import DontHaveExtension

            self.supported_extensions["lt_donthave"] = DontHaveExtension

        # Register Fast Extension
        from .fast_extension import FastExtension

        self.supported_extensions["fast_extension"] = FastExtension

        logger.trace(
            f"Registered {len(self.supported_extensions)} extensions",
            extra={"class_name": self.__class__.__name__},
        )

    def create_extended_handshake(self) -> bytes:
        """
        Create extended handshake message

        Returns:
            Encoded extended handshake message
        """
        try:
            # Build extension dictionary with message IDs
            extension_dict = {}
            message_id = 1  # Start from 1 (0 is reserved for handshake)

            for ext_name in self.supported_extensions:
                extension_dict[ext_name] = message_id
                self.local_extension_ids[ext_name] = message_id
                message_id += 1

            # Build handshake message
            handshake_data = {
                b"m": extension_dict,  # Extension mapping
                b"v": b"DFakeSeeder 1.0",  # Client version
                b"p": self.peer_connection.port if hasattr(self.peer_connection, "port") else 6881,
            }

            # Add metadata size if available
            if hasattr(self.peer_connection, "torrent") and self.peer_connection.torrent:
                try:
                    metadata_size = len(bencode.bencode(self.peer_connection.torrent.info))
                    handshake_data[b"metadata_size"] = metadata_size
                except Exception:
                    pass

            # Encode handshake
            handshake_payload = bencode.bencode(handshake_data)

            # Create extended message (ID 0 = handshake)
            message_length = 2 + len(handshake_payload)  # message_id + ext_id + payload
            message = struct.pack(">IB", message_length, BitTorrentMessage.EXTENDED)
            message += struct.pack(">B", 0)  # Extended handshake ID
            message += handshake_payload

            logger.trace(
                "Created extended handshake",
                extra={
                    "class_name": self.__class__.__name__,
                    "extensions": list(extension_dict.keys()),
                    "payload_size": len(handshake_payload),
                },
            )

            return message  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(
                f"Failed to create extended handshake: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return b""

    def handle_extended_handshake(self, payload: bytes) -> None:
        """
        Handle extended handshake from peer

        Args:
            payload: Handshake payload data
        """
        try:
            handshake_data = bencode.bdecode(payload)

            # Extract peer's extensions
            peer_extensions = handshake_data.get(b"m", {})
            self.peer_extensions = {
                ext_name.decode("utf-8"): ext_id
                for ext_name, ext_id in peer_extensions.items()
                if isinstance(ext_name, bytes)
            }

            # Build reverse mapping
            self.remote_extension_ids = {ext_name: ext_id for ext_name, ext_id in self.peer_extensions.items()}

            # Initialize extension instances for common extensions
            for ext_name in self.supported_extensions:
                if ext_name in self.peer_extensions:
                    self._initialize_extension(ext_name)

            logger.trace(
                "Processed extended handshake",
                extra={
                    "class_name": self.__class__.__name__,
                    "peer_extensions": list(self.peer_extensions.keys()),
                    "common_extensions": [ext for ext in self.supported_extensions if ext in self.peer_extensions],
                },
            )

            # Store peer metadata
            self.peer_version = handshake_data.get(b"v", b"Unknown").decode("utf-8", errors="ignore")
            self.peer_port = handshake_data.get(b"p", 0)
            self.peer_metadata_size = handshake_data.get(b"metadata_size", 0)

        except Exception as e:
            logger.error(
                f"Failed to handle extended handshake: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def handle_extended_message(self, extension_id: int, payload: bytes) -> None:
        """
        Handle extended message from peer

        Args:
            extension_id: Extension message ID
            payload: Message payload
        """
        try:
            if extension_id == 0:
                # Extended handshake
                self.handle_extended_handshake(payload)
                return

            # Find extension by ID
            extension_name = None
            for ext_name, ext_id in self.remote_extension_ids.items():
                if ext_id == extension_id:
                    extension_name = ext_name
                    break

            if not extension_name:
                logger.trace(
                    f"Unknown extension ID: {extension_id}",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            # Handle extension message
            if extension_name in self.extension_instances:
                extension = self.extension_instances[extension_name]
                extension.handle_message(payload)
            else:
                logger.trace(
                    f"No handler for extension: {extension_name}",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to handle extended message: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def send_extended_message(self, extension_name: str, payload: bytes) -> Any:
        """
        Send extended message to peer

        Args:
            extension_name: Name of extension
            payload: Message payload
        """
        try:
            # Check if peer supports this extension
            if extension_name not in self.peer_extensions:
                logger.trace(
                    f"Peer doesn't support extension: {extension_name}",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            extension_id = self.peer_extensions[extension_name]

            # Create extended message
            message_length = 2 + len(payload)  # message_id + ext_id + payload
            message = struct.pack(">IB", message_length, BitTorrentMessage.EXTENDED)
            message += struct.pack(">B", extension_id)
            message += payload

            # Send via peer connection
            if hasattr(self.peer_connection, "send_message"):
                self.peer_connection.send_message(message)
                return True
            else:
                logger.warning(
                    "Peer connection has no send_message method",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

        except Exception as e:
            logger.error(
                f"Failed to send extended message: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _initialize_extension(self, extension_name: str) -> Any:
        """
        Initialize extension instance

        Args:
            extension_name: Name of extension to initialize
        """
        try:
            if extension_name in self.extension_instances:
                return  # Already initialized

            extension_class = self.supported_extensions.get(extension_name)
            if not extension_class:
                return

            # Create extension instance
            extension = extension_class(self, self.peer_connection)
            self.extension_instances[extension_name] = extension

            # Initialize extension
            if hasattr(extension, "initialize"):
                extension.initialize()

            logger.trace(
                f"Initialized extension: {extension_name}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize extension {extension_name}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def get_extension(self, extension_name: str) -> Any:
        """
        Get extension instance

        Args:
            extension_name: Name of extension

        Returns:
            Extension instance or None
        """
        return self.extension_instances.get(extension_name)

    def is_extension_supported(self, extension_name: str) -> bool:
        """
        Check if extension is supported by peer

        Args:
            extension_name: Name of extension

        Returns:
            True if supported by peer
        """
        return extension_name in self.peer_extensions

    def get_peer_info(self) -> Dict[str, Any]:
        """
        Get peer information from extended handshake

        Returns:
            Dictionary with peer information
        """
        return {
            "version": getattr(self, "peer_version", "Unknown"),
            "port": getattr(self, "peer_port", 0),
            "metadata_size": getattr(self, "peer_metadata_size", 0),
            "extensions": list(self.peer_extensions.keys()),
        }

    def cleanup(self) -> Any:
        """Clean up extension instances"""
        for extension_name, extension in self.extension_instances.items():
            try:
                if hasattr(extension, "cleanup"):
                    extension.cleanup()
            except Exception as e:
                logger.error(
                    f"Error cleaning up extension {extension_name}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        self.extension_instances.clear()
        self.peer_extensions.clear()
        self.remote_extension_ids.clear()
