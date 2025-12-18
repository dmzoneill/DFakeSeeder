"""
Message Stream Encryption (MSE/PE) Implementation.

Implements the BitTorrent Message Stream Encryption protocol for
secure peer-to-peer communication. This provides:
- Diffie-Hellman key exchange for shared secret generation
- RC4 stream cipher for data encryption
- Protocol obfuscation to avoid traffic analysis

Note: This requires the pycryptodome package for RC4 cipher.
"""

import enum
import hashlib
import os
from typing import Any, Optional, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

# Try to import Crypto (pycryptodome) - it's an optional dependency
try:
    from Crypto.Cipher import ARC4

    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    ARC4 = None  # type: ignore[assignment, misc]


# Diffie-Hellman parameters (standard for BitTorrent MSE)
# This is the 768-bit MODP group
DH_PRIME = int(
    "0xFFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1"
    "29024E088A67CC74020BBEA63B139B22514A08798E3404DD"
    "EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245"
    "E485B576625E7EC6F44C42E9A63A36210000000000090563",
    16,
)
DH_GENERATOR = 2

# Protocol constants
CRYPTO_PLAIN = 0x01  # Plaintext protocol
CRYPTO_RC4 = 0x02  # RC4 encrypted protocol


class MSEState(enum.Enum):
    """MSE handshake state machine states."""

    INITIAL = "initial"
    DH_SENT = "dh_sent"
    DH_RECEIVED = "dh_received"
    SYNC_SENT = "sync_sent"
    SYNC_RECEIVED = "sync_received"
    CRYPTO_SELECT_SENT = "crypto_select_sent"
    ESTABLISHED = "established"
    FAILED = "failed"


class MSEHandler:
    """
    Handles MSE/PE encryption for peer connections.

    This implements the Message Stream Encryption protocol
    for obfuscating BitTorrent traffic.
    """

    def __init__(
        self,
        info_hash: bytes,
        encryption_mode: str = "enabled",
        is_initiator: bool = True,
    ) -> None:
        """
        Initialize MSE handler.

        Args:
            info_hash: 20-byte torrent info hash.
            encryption_mode: "disabled", "enabled", or "forced".
            is_initiator: True if we're initiating the connection.
        """
        self.info_hash = info_hash
        self.encryption_mode = encryption_mode
        self.is_initiator = is_initiator
        self.settings = AppSettings.get_instance()

        # DH key exchange
        self.private_key: Optional[int] = None
        self.public_key: Optional[int] = None
        self.peer_public_key: Optional[int] = None
        self.shared_secret: Optional[bytes] = None

        # RC4 ciphers (initialized after key exchange)
        self.encrypt_cipher: Optional[Any] = None
        self.decrypt_cipher: Optional[Any] = None

        # State machine
        self.state = MSEState.INITIAL
        self.encrypted = False

        # Buffer for handshake data
        self.handshake_buffer = b""

        if not CRYPTO_AVAILABLE:
            logger.warning(
                "pycryptodome not installed - MSE encryption disabled. "
                "Install with: pip install pycryptodome",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            # Generate our DH key pair
            self._generate_dh_keypair()

            logger.trace(
                f"MSEHandler initialized (mode: {encryption_mode}, "
                f"initiator: {is_initiator})",
                extra={"class_name": self.__class__.__name__},
            )

    def _generate_dh_keypair(self) -> None:
        """Generate Diffie-Hellman key pair."""
        # Generate random private key (160 bits for performance)
        self.private_key = int.from_bytes(os.urandom(20), "big")

        # Calculate public key: g^private mod p
        self.public_key = pow(DH_GENERATOR, self.private_key, DH_PRIME)

    def is_available(self) -> bool:
        """Check if encryption is available."""
        return CRYPTO_AVAILABLE

    def is_required(self) -> bool:
        """Check if encryption is required."""
        return self.encryption_mode == "forced"

    def is_enabled(self) -> bool:
        """Check if encryption is enabled."""
        return self.encryption_mode in ("enabled", "forced")

    def is_established(self) -> bool:
        """Check if encrypted connection is established."""
        return self.state == MSEState.ESTABLISHED and self.encrypted

    def generate_dh_public(self) -> bytes:
        """
        Generate our DH public key for the handshake.

        Returns:
            96-byte DH public key.
        """
        if not CRYPTO_AVAILABLE or self.public_key is None:
            return b""

        # Pad to 96 bytes (768 bits)
        return self.public_key.to_bytes(96, "big")

    def process_dh_public(self, peer_public_bytes: bytes) -> bool:
        """
        Process peer's DH public key and derive shared secret.

        Args:
            peer_public_bytes: Peer's 96-byte DH public key.

        Returns:
            True if shared secret was derived successfully.
        """
        if not CRYPTO_AVAILABLE or self.private_key is None:
            return False

        try:
            # Parse peer's public key
            self.peer_public_key = int.from_bytes(peer_public_bytes, "big")

            # Derive shared secret: peer_public^private mod p
            shared_int = pow(self.peer_public_key, self.private_key, DH_PRIME)
            shared_bytes = shared_int.to_bytes(96, "big")

            # Hash the shared secret
            self.shared_secret = hashlib.sha1(shared_bytes).digest()

            self.state = MSEState.DH_RECEIVED

            logger.trace(
                "MSE: Shared secret derived",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"MSE: Failed to derive shared secret: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self.state = MSEState.FAILED
            return False

    def initialize_ciphers(self) -> bool:
        """
        Initialize RC4 ciphers after key exchange.

        Returns:
            True if ciphers were initialized successfully.
        """
        if not CRYPTO_AVAILABLE or not self.shared_secret:
            return False

        try:
            # Derive RC4 keys using HASH(key || S || SKEY)
            # where S = "keyA" or "keyB", SKEY = info_hash

            if self.is_initiator:
                # Initiator uses keyA for encryption, keyB for decryption
                enc_key = hashlib.sha1(
                    b"keyA" + self.shared_secret + self.info_hash
                ).digest()
                dec_key = hashlib.sha1(
                    b"keyB" + self.shared_secret + self.info_hash
                ).digest()
            else:
                # Responder uses keyB for encryption, keyA for decryption
                enc_key = hashlib.sha1(
                    b"keyB" + self.shared_secret + self.info_hash
                ).digest()
                dec_key = hashlib.sha1(
                    b"keyA" + self.shared_secret + self.info_hash
                ).digest()

            # Create RC4 ciphers
            self.encrypt_cipher = ARC4.new(enc_key)
            self.decrypt_cipher = ARC4.new(dec_key)

            # Discard first 1024 bytes of RC4 keystream
            # (mitigation for RC4 initial bias weakness)
            self.encrypt_cipher.encrypt(b"\x00" * 1024)
            self.decrypt_cipher.decrypt(b"\x00" * 1024)

            self.encrypted = True
            self.state = MSEState.ESTABLISHED

            logger.debug(
                "MSE: Ciphers initialized, encryption enabled",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"MSE: Failed to initialize ciphers: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self.state = MSEState.FAILED
            return False

    def encrypt(self, data: bytes) -> bytes:
        """
        Encrypt outgoing data.

        Args:
            data: Plaintext data to encrypt.

        Returns:
            Encrypted data, or original data if encryption not active.
        """
        if self.encrypted and self.encrypt_cipher:
            return self.encrypt_cipher.encrypt(data)
        return data

    def decrypt(self, data: bytes) -> bytes:
        """
        Decrypt incoming data.

        Args:
            data: Encrypted data to decrypt.

        Returns:
            Decrypted data, or original data if encryption not active.
        """
        if self.encrypted and self.decrypt_cipher:
            return self.decrypt_cipher.decrypt(data)
        return data

    def get_sync_hash(self) -> bytes:
        """
        Generate synchronization hash for handshake.

        Returns:
            20-byte sync hash.
        """
        if not self.shared_secret:
            return b""

        # HASH('req1' + S) for initiator
        # HASH('req2' + SKEY) for responder
        if self.is_initiator:
            return hashlib.sha1(b"req1" + self.shared_secret).digest()
        else:
            return hashlib.sha1(b"req2" + self.info_hash).digest()

    def verify_sync_hash(self, received_hash: bytes) -> bool:
        """
        Verify received synchronization hash.

        Args:
            received_hash: 20-byte hash to verify.

        Returns:
            True if hash is valid.
        """
        if not self.shared_secret:
            return False

        # Verify opposite of what we send
        if self.is_initiator:
            expected = hashlib.sha1(b"req2" + self.info_hash).digest()
        else:
            expected = hashlib.sha1(b"req1" + self.shared_secret).digest()

        return received_hash == expected

    def get_crypto_provide(self) -> int:
        """
        Get our supported crypto methods.

        Returns:
            Bitmask of supported crypto methods.
        """
        if self.encryption_mode == "forced":
            return CRYPTO_RC4
        elif self.encryption_mode == "enabled":
            return CRYPTO_PLAIN | CRYPTO_RC4
        else:
            return CRYPTO_PLAIN

    def select_crypto(self, crypto_provide: int) -> int:
        """
        Select crypto method based on peer's offer.

        Args:
            crypto_provide: Peer's supported crypto methods bitmask.

        Returns:
            Selected crypto method, or 0 if no compatible method.
        """
        our_methods = self.get_crypto_provide()
        common = our_methods & crypto_provide

        # Prefer RC4 if available and we want encryption
        if self.encryption_mode != "disabled" and (common & CRYPTO_RC4):
            return CRYPTO_RC4

        # Fall back to plaintext if allowed
        if self.encryption_mode != "forced" and (common & CRYPTO_PLAIN):
            return CRYPTO_PLAIN

        return 0

    def reset(self) -> None:
        """Reset the handler to initial state."""
        self.state = MSEState.INITIAL
        self.peer_public_key = None
        self.shared_secret = None
        self.encrypt_cipher = None
        self.decrypt_cipher = None
        self.encrypted = False
        self.handshake_buffer = b""

        # Generate new DH key pair
        if CRYPTO_AVAILABLE:
            self._generate_dh_keypair()

    def get_status(self) -> dict:
        """
        Get the current encryption status.

        Returns:
            Dictionary with encryption status information.
        """
        return {
            "available": CRYPTO_AVAILABLE,
            "mode": self.encryption_mode,
            "state": self.state.value,
            "encrypted": self.encrypted,
            "is_initiator": self.is_initiator,
        }

