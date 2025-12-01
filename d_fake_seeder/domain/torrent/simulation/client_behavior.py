"""
Advanced Client Behavior Simulation Engine

Provides deep emulation of specific BitTorrent client behaviors,
including protocol-level quirks, timing patterns, and behavioral characteristics.
"""

# fmt: off
import random
import time
from typing import Any, Dict, List

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import BitTorrentProtocolConstants

# fmt: on


class ClientBehaviorEngine:
    """Advanced client behavior simulation engine"""

    # Comprehensive client profiles with realistic behavior patterns
    CLIENT_PROFILES = {
        "qBittorrent": {
            "peer_id_prefix": "-qB4420-",
            "user_agent": "qBittorrent/4.4.2",
            "client_version": "4.4.2",
            "extensions": ["ut_metadata", "ut_pex", "lt_donthave", "ut_holepunch"],
            "behavior_patterns": {
                "aggressive_seeding": True,
                "dht_participation": True,
                "pex_enabled": True,
                "pex_frequency": 60,  # seconds
                "keep_alive_interval": 120,
                "connection_timeout": 30,
                "max_connections_per_torrent": 200,
                "upload_slots": 4,
                "request_queue_size": 250,
                "piece_selection_strategy": "rarest_first",
                "endgame_threshold": 0.98,
                "fast_extension": True,
            },
            "timing_patterns": {
                "handshake_delay": (0.1, 0.5),  # min, max seconds
                "announce_variance": 0.1,  # ±10% of announce interval
                "piece_request_delay": (0.01, 0.1),
                "unchoke_interval": 10,
                "optimistic_unchoke_interval": 30,
            },
            "network_behavior": {
                "tcp_keepalive": True,
                "nagle_algorithm": False,
                "send_buffer_size": 1048576,  # 1MB
                "recv_buffer_size": 1048576,
                "connection_backlog": 50,
            },
        },
        "Deluge": {
            "peer_id_prefix": "-DE2030-",
            "user_agent": "Deluge 2.0.3",
            "client_version": "2.0.3",
            "extensions": ["ut_metadata", "ut_pex"],
            "behavior_patterns": {
                "conservative_seeding": True,
                "dht_participation": True,
                "pex_enabled": True,
                "pex_frequency": 120,
                "keep_alive_interval": 150,
                "connection_timeout": 60,
                "max_connections_per_torrent": 300,
                "upload_slots": 7,
                "request_queue_size": 500,
                "piece_selection_strategy": "rarest_first",
                "endgame_threshold": 0.95,
                "fast_extension": False,
            },
            "timing_patterns": {
                "handshake_delay": (0.2, 1.0),
                "announce_variance": 0.15,
                "piece_request_delay": (0.05, 0.2),
                "unchoke_interval": 10,
                "optimistic_unchoke_interval": 30,
            },
            "network_behavior": {
                "tcp_keepalive": True,
                "nagle_algorithm": True,
                "send_buffer_size": 524288,  # 512KB
                "recv_buffer_size": 524288,
                "connection_backlog": 30,
            },
        },
        "Transmission": {
            "peer_id_prefix": "-TR3000-",
            "user_agent": "Transmission/3.00",
            "client_version": "3.00",
            "extensions": ["ut_metadata", "ut_pex", "ut_holepunch"],
            "behavior_patterns": {
                "lightweight_operation": True,
                "dht_participation": True,
                "pex_enabled": True,
                "pex_frequency": 90,
                "keep_alive_interval": 120,
                "connection_timeout": 20,
                "max_connections_per_torrent": 150,
                "upload_slots": 14,
                "request_queue_size": 100,
                "piece_selection_strategy": "rarest_first",
                "endgame_threshold": 0.99,
                "fast_extension": True,
            },
            "timing_patterns": {
                "handshake_delay": (0.05, 0.3),
                "announce_variance": 0.05,
                "piece_request_delay": (0.01, 0.05),
                "unchoke_interval": 10,
                "optimistic_unchoke_interval": 30,
            },
            "network_behavior": {
                "tcp_keepalive": True,
                "nagle_algorithm": False,
                "send_buffer_size": 262144,  # 256KB
                "recv_buffer_size": 262144,
                "connection_backlog": 20,
            },
        },
        "uTorrent": {
            "peer_id_prefix": "-UT3450-",
            "user_agent": "µTorrent/3.4.5",
            "client_version": "3.4.5.45395",
            "extensions": ["ut_metadata", "ut_pex", "ut_holepunch", "ut_comment"],
            "behavior_patterns": {
                "proprietary_optimizations": True,
                "dht_participation": True,
                "pex_enabled": True,
                "pex_frequency": 45,
                "keep_alive_interval": 110,
                "connection_timeout": 25,
                "max_connections_per_torrent": 250,
                "upload_slots": 6,
                "request_queue_size": 300,
                "piece_selection_strategy": "sequential_rarest",
                "endgame_threshold": 0.97,
                "fast_extension": True,
                "utp_support": True,
            },
            "timing_patterns": {
                "handshake_delay": (0.08, 0.4),
                "announce_variance": 0.08,
                "piece_request_delay": (0.02, 0.08),
                "unchoke_interval": 10,
                "optimistic_unchoke_interval": 30,
            },
            "network_behavior": {
                "tcp_keepalive": True,
                "nagle_algorithm": False,
                "send_buffer_size": 2097152,  # 2MB
                "recv_buffer_size": 1048576,  # 1MB
                "connection_backlog": 100,
                "utp_enabled": True,
            },
        },
        "BiglyBT": {
            "peer_id_prefix": "-BiglyBT-",
            "user_agent": "BiglyBT/2.7.0.0",
            "client_version": "2.7.0.0",
            "extensions": ["ut_metadata", "ut_pex", "azureus_messaging"],
            "behavior_patterns": {
                "feature_rich": True,
                "dht_participation": True,
                "pex_enabled": True,
                "pex_frequency": 75,
                "keep_alive_interval": 180,
                "connection_timeout": 45,
                "max_connections_per_torrent": 500,
                "upload_slots": 8,
                "request_queue_size": 1000,
                "piece_selection_strategy": "availability_rarest",
                "endgame_threshold": 0.93,
                "fast_extension": True,
                "super_seeding": True,
            },
            "timing_patterns": {
                "handshake_delay": (0.15, 0.8),
                "announce_variance": 0.12,
                "piece_request_delay": (0.03, 0.15),
                "unchoke_interval": 10,
                "optimistic_unchoke_interval": 30,
            },
            "network_behavior": {
                "tcp_keepalive": True,
                "nagle_algorithm": True,
                "send_buffer_size": 1048576,
                "recv_buffer_size": 2097152,
                "connection_backlog": 200,
            },
        },
    }

    def __init__(self, torrent_manager=None):
        """
        Initialize client behavior engine

        Args:
            torrent_manager: Optional torrent manager for coordination
        """
        self.torrent_manager = torrent_manager
        self.settings = AppSettings.get_instance()

        # Get simulation configuration
        simulation_config = getattr(self.settings, "simulation", {})
        client_config = simulation_config.get("client_behavior_engine", {})

        self.enabled = client_config.get("enabled", True)
        self.primary_client = client_config.get("primary_client", "qBittorrent")
        self.behavior_variation = client_config.get("behavior_variation", 0.3)
        self.switch_client_probability = client_config.get("switch_client_probability", 0.05)

        # Current client state
        self.current_client_profile = self.CLIENT_PROFILES.get(self.primary_client)
        self.session_start_time = time.time()
        self.last_behavior_update = 0
        self.behavior_state = {}

        # Performance tracking
        self.behavior_stats = {
            "client_switches": 0,
            "behavior_adaptations": 0,
            "protocol_violations": 0,
        }

        logger.info(
            "Client behavior engine initialized",
            extra={
                "class_name": self.__class__.__name__,
                "primary_client": self.primary_client,
                "enabled": self.enabled,
            },
        )

    def get_peer_id(self) -> str:
        """
        Generate realistic peer ID for current client

        Returns:
            Peer ID string
        """
        if not self.enabled or not self.current_client_profile:
            return self._generate_generic_peer_id()

        try:
            prefix = self.current_client_profile["peer_id_prefix"]

            # Generate random suffix (usually 12 characters)
            suffix_length = 20 - len(prefix)
            suffix = "".join(
                random.choices(
                    "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
                    k=suffix_length,
                )
            )

            return prefix + suffix

        except Exception as e:
            logger.error(
                f"Failed to generate peer ID: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return self._generate_generic_peer_id()

    def get_user_agent(self) -> str:
        """
        Get user agent string for current client

        Returns:
            User agent string
        """
        if not self.enabled or not self.current_client_profile:
            return "DFakeSeeder/1.0"

        return self.current_client_profile.get("user_agent", "DFakeSeeder/1.0")

    def get_supported_extensions(self) -> List[str]:
        """
        Get list of supported extensions for current client

        Returns:
            List of extension names
        """
        if not self.enabled or not self.current_client_profile:
            return ["ut_metadata", "ut_pex"]

        return self.current_client_profile.get("extensions", [])

    def get_behavior_parameter(self, parameter: str, default=None):
        """
        Get behavior parameter with variation

        Args:
            parameter: Parameter name
            default: Default value if not found

        Returns:
            Parameter value with applied variation
        """
        if not self.enabled or not self.current_client_profile:
            return default

        try:
            patterns = self.current_client_profile.get("behavior_patterns", {})
            base_value = patterns.get(parameter, default)

            if base_value is None:
                return default

            # Apply variation for numeric values (but not booleans)
            if (
                isinstance(base_value, (int, float))
                and not isinstance(base_value, bool)
                and self.behavior_variation > 0
            ):
                variation = base_value * self.behavior_variation * (random.random() - 0.5) * 2
                return max(0, base_value + variation)

            return base_value

        except Exception as e:
            logger.error(
                f"Failed to get behavior parameter {parameter}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return default

    def get_timing_parameter(self, parameter: str, default=None):
        """
        Get timing parameter with realistic delays

        Args:
            parameter: Timing parameter name
            default: Default value if not found

        Returns:
            Timing value
        """
        if not self.enabled or not self.current_client_profile:
            return default

        try:
            timing = self.current_client_profile.get("timing_patterns", {})
            timing_value = timing.get(parameter, default)

            if isinstance(timing_value, tuple) and len(timing_value) == 2:
                # Return random value in range
                min_val, max_val = timing_value
                return random.uniform(min_val, max_val)

            return timing_value

        except Exception as e:
            logger.error(
                f"Failed to get timing parameter {parameter}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return default

    # TODO: UNUSED METHOD - Simulation engine not integrated
    # def simulate_client_behavior(self, action: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    #     """
    #     Simulate client-specific behavior for given action
    #
    #     Args:
    #         action: Action to simulate (e.g., 'handshake', 'announce', 'piece_request')
    #         context: Additional context information
    #
    #     Returns:
    #         Dictionary with behavior simulation results
    #     """
    #     if not self.enabled:
    #         return {"simulated": False}
    #
    #     try:
    #         # Update client behavior if needed
    #         self._maybe_update_behavior()
    #
    #         # Dispatch to specific behavior simulation
    #         if action == "handshake":
    #             return self._simulate_handshake(context or {})
    #         elif action == "announce":
    #             return self._simulate_announce(context or {})
    #         elif action == "piece_request":
    #             return self._simulate_piece_request(context or {})
    #         elif action == "peer_exchange":
    #             return self._simulate_peer_exchange(context or {})
    #         elif action == "keep_alive":
    #             return self._simulate_keep_alive(context or {})
    #         else:
    #             return self._simulate_generic_behavior(action, context or {})
    #
    #     except Exception as e:
    #         logger.error(
    #             f"Failed to simulate client behavior for {action}: {e}", extra={"class_name": self.__class__.__name__}
    #         )
    #         return {"simulated": False, "error": str(e)}

    def _simulate_handshake(self, context: Dict) -> Dict[str, Any]:
        """Simulate client-specific handshake behavior"""
        delay = self.get_timing_parameter("handshake_delay", 0.1)
        extensions = self.get_supported_extensions()

        return {
            "simulated": True,
            "action": "handshake",
            "delay": delay,
            "extensions": extensions,
            "client": self.primary_client,
            "reserved_bytes": self._get_reserved_bytes(),
        }

    def _simulate_announce(self, context: Dict) -> Dict[str, Any]:
        """Simulate client-specific announce behavior"""
        variance = self.get_timing_parameter("announce_variance", 0.1)
        base_interval = context.get("interval", 1800)

        # Apply variance
        actual_interval = base_interval * (1 + variance * (random.random() - 0.5) * 2)

        return {
            "simulated": True,
            "action": "announce",
            "interval": actual_interval,
            "user_agent": self.get_user_agent(),
            "client": self.primary_client,
        }

    def _simulate_piece_request(self, context: Dict) -> Dict[str, Any]:
        """Simulate client-specific piece request behavior"""
        delay = self.get_timing_parameter("piece_request_delay", 0.05)
        strategy = self.get_behavior_parameter("piece_selection_strategy", "rarest_first")
        queue_size = self.get_behavior_parameter("request_queue_size", 250)

        return {
            "simulated": True,
            "action": "piece_request",
            "delay": delay,
            "strategy": strategy,
            "queue_size": queue_size,
            "client": self.primary_client,
        }

    def _simulate_peer_exchange(self, context: Dict) -> Dict[str, Any]:
        """Simulate client-specific PEX behavior"""
        frequency = self.get_behavior_parameter("pex_frequency", 60)
        enabled = self.get_behavior_parameter("pex_enabled", True)

        return {
            "simulated": True,
            "action": "peer_exchange",
            "enabled": enabled,
            "frequency": frequency,
            "client": self.primary_client,
        }

    def _simulate_keep_alive(self, context: Dict) -> Dict[str, Any]:
        """Simulate client-specific keep-alive behavior"""
        interval = self.get_behavior_parameter("keep_alive_interval", 120)

        return {
            "simulated": True,
            "action": "keep_alive",
            "interval": interval,
            "client": self.primary_client,
        }

    def _simulate_generic_behavior(self, action: str, context: Dict) -> Dict[str, Any]:
        """Simulate generic client behavior"""
        return {
            "simulated": True,
            "action": action,
            "client": self.primary_client,
            "context": context,
        }

    def _maybe_update_behavior(self):
        """Possibly update client behavior based on time and probability"""
        current_time = time.time()

        # Check if we should switch client profiles
        if (
            current_time - self.session_start_time > 3600  # After 1 hour
            and random.random() < self.switch_client_probability
        ):
            self._switch_client_profile()

        self.last_behavior_update = current_time

    def _switch_client_profile(self):
        """Switch to a different client profile"""
        try:
            available_clients = list(self.CLIENT_PROFILES.keys())
            available_clients.remove(self.primary_client)

            if available_clients:
                new_client = random.choice(available_clients)
                self.primary_client = new_client
                self.current_client_profile = self.CLIENT_PROFILES[new_client]
                self.behavior_stats["client_switches"] += 1

                logger.info(
                    f"Switched client profile to {new_client}",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Failed to switch client profile: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _get_reserved_bytes(self) -> bytes:
        """Get client-specific reserved bytes for handshake"""
        # Different clients set different reserved bits
        reserved = bytearray(8)

        if self.current_client_profile:
            extensions = self.current_client_profile.get("extensions", [])

            # Set extension protocol bit if supported
            if "ut_metadata" in extensions or "ut_pex" in extensions:
                reserved[5] |= BitTorrentProtocolConstants.EXTENSION_PROTOCOL_BIT  # Extension protocol bit

            # Set DHT bit if supported
            if self.get_behavior_parameter("dht_participation", False):
                reserved[7] |= BitTorrentProtocolConstants.DHT_BIT  # DHT bit

            # Set fast extension bit if supported
            if self.get_behavior_parameter("fast_extension", False):
                reserved[7] |= BitTorrentProtocolConstants.FAST_EXTENSION_BIT  # Fast extension bit

        return bytes(reserved)

    def _generate_generic_peer_id(self) -> str:
        """Generate generic peer ID"""
        try:
            return "-DF1000-" + "".join(random.choices("0123456789ABCDEF", k=12))
        except Exception:
            # Ultimate fallback - use fixed suffix if random fails
            return "-DF1000-000000000000"

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get client behavior engine statistics

        Returns:
            Dictionary with statistics
        """
        return {
            "enabled": self.enabled,
            "current_client": self.primary_client,
            "session_duration": time.time() - self.session_start_time,
            "behavior_variation": self.behavior_variation,
            "stats": self.behavior_stats.copy(),
            "supported_extensions": self.get_supported_extensions(),
        }

    def cleanup(self):
        """Clean up client behavior engine"""
        self.behavior_state.clear()

        logger.debug(
            "Client behavior engine cleaned up",
            extra={"class_name": self.__class__.__name__},
        )
