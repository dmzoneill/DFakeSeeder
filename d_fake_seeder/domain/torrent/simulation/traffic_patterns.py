"""
Traffic Pattern Simulation

Generates realistic BitTorrent traffic patterns including upload/download variations,
connection patterns, and time-based behavior simulation.
"""

# fmt: off
import math
import random
import time
from typing import Any, Dict, Generator, List, Optional, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

# fmt: on


class TrafficPatternSimulator:
    """Generate realistic BitTorrent traffic patterns"""

    def __init__(self, seeding_profile: str = "balanced"):
        """
        Initialize traffic pattern simulator

        Args:
            seeding_profile: Profile name ('conservative', 'balanced', 'aggressive')
        """
        self.settings = AppSettings.get_instance()

        # Get simulation configuration
        simulation_config = getattr(self.settings, "simulation", {})
        self.traffic_config = simulation_config.get("traffic_patterns", {})

        # Use the provided seeding_profile parameter directly
        self.profile_name = seeding_profile
        self.realistic_variations = self.traffic_config.get("realistic_variations", True)
        self.time_based_patterns = self.traffic_config.get("time_based_patterns", True)

        # Load traffic profiles from configuration
        traffic_profiles_config = self.traffic_config.get("profiles", {})

        # Traffic profiles with realistic characteristics (loaded from config)
        self.profiles = {}
        for profile_name in ["conservative", "balanced", "aggressive"]:
            profile_config = traffic_profiles_config.get(profile_name, {})
            self.profiles[profile_name] = {
                "base_upload_speed": profile_config.get("base_upload_speed_kb", 200) * 1024,
                "base_download_speed": profile_config.get("base_download_speed_kb", 800) * 1024,
                "upload_variance": profile_config.get("upload_variance", 0.3),
                "download_variance": profile_config.get("download_variance", 0.25),
                "connection_frequency": profile_config.get("connection_frequency", "medium"),
                "peer_exchange_rate": profile_config.get("peer_exchange_rate", 0.6),
                "burst_probability": profile_config.get("burst_probability", 0.15),
                "idle_probability": profile_config.get("idle_probability", 0.1),
                "max_connections": profile_config.get("max_connections", 100),
                "connection_timeout": profile_config.get("connection_timeout", 45),
                "announce_frequency_multiplier": profile_config.get("announce_frequency_multiplier", 1.0),
            }

        self.current_profile = self.profiles.get(self.profile_name, self.profiles["balanced"])

        # State tracking
        self.session_start_time = time.time()
        self.last_pattern_update = 0.0
        self.current_burst_state = False
        self.burst_start_time = 0.0
        self.burst_duration = 0.0
        self.idle_state = False
        self.idle_start_time = 0.0
        self.idle_duration = 0.0

        # Traffic history for pattern analysis
        self.traffic_history: List[Dict[str, Any]] = []
        self.connection_history: List[Dict[str, Any]] = []

        logger.info(
            "Traffic pattern simulator initialized",
            extra={"class_name": self.__class__.__name__, "profile": self.profile_name},
        )

    def generate_upload_pattern(
        self, base_speed: Optional[int] = None, duration: int = 60
    ) -> Generator[Tuple[float, int], None, None]:
        """
        Generate realistic upload speed variations over time

        Args:
            base_speed: Base upload speed in bytes/s (uses profile default if None)
            duration: Duration in seconds

        Yields:
            Tuples of (timestamp, speed_bytes_per_second)
        """
        if base_speed is None:
            base_speed = self.current_profile["base_upload_speed"]

        start_time = time.time()

        try:
            for second in range(duration):
                current_time = start_time + second

                # Calculate speed with various factors
                speed = self._calculate_realistic_speed(base_speed, "upload", current_time)

                # Store in history
                self.traffic_history.append({"timestamp": current_time, "type": "upload", "speed": speed})

                # Keep history size manageable
                if len(self.traffic_history) > 3600:  # 1 hour
                    self.traffic_history.pop(0)

                yield (current_time, speed)

        except Exception as e:
            logger.error(
                f"Failed to generate upload pattern: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def generate_download_pattern(
        self, base_speed: Optional[int] = None, duration: int = 60
    ) -> Generator[Tuple[float, int], None, None]:
        """
        Generate realistic download speed variations over time

        Args:
            base_speed: Base download speed in bytes/s (uses profile default if None)
            duration: Duration in seconds

        Yields:
            Tuples of (timestamp, speed_bytes_per_second)
        """
        if base_speed is None:
            base_speed = self.current_profile["base_download_speed"]

        start_time = time.time()

        try:
            for second in range(duration):
                current_time = start_time + second

                speed = self._calculate_realistic_speed(base_speed, "download", current_time)

                self.traffic_history.append({"timestamp": current_time, "type": "download", "speed": speed})

                if len(self.traffic_history) > 3600:
                    self.traffic_history.pop(0)

                yield (current_time, speed)

        except Exception as e:
            logger.error(
                f"Failed to generate download pattern: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def simulate_peer_interactions(self, peer_count: int) -> List[Dict]:
        """
        Generate realistic peer connection patterns

        Args:
            peer_count: Number of peers to simulate

        Returns:
            List of peer interaction events
        """
        try:
            interactions = []
            current_time = time.time()

            # Calculate connection frequency based on profile and configuration
            frequency_settings = self.traffic_config.get("frequency_settings", {"low": 0.5, "medium": 2.0, "high": 5.0})

            frequency = frequency_settings.get(self.current_profile["connection_frequency"], 2.0)

            # Generate connection events
            for i in range(peer_count):
                # Random connection time within the next hour
                connection_delay = random.expovariate(frequency / 60.0)
                connection_time = current_time + connection_delay

                # Generate peer interaction
                interaction = self._generate_peer_interaction(connection_time, i)
                interactions.append(interaction)

            # Sort by time
            interactions.sort(key=lambda x: x["timestamp"])

            # Store in history
            self.connection_history.extend(interactions)
            if len(self.connection_history) > 1000:
                self.connection_history = self.connection_history[-1000:]

            return interactions

        except Exception as e:
            logger.error(
                f"Failed to simulate peer interactions: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return []

    def _calculate_realistic_speed(self, base_speed: int, traffic_type: str, current_time: float) -> int:
        """
        Calculate realistic speed with various factors

        Args:
            base_speed: Base speed in bytes/s
            traffic_type: 'upload' or 'download'
            current_time: Current timestamp

        Returns:
            Calculated speed in bytes/s
        """
        try:
            speed: float = float(base_speed)

            # Apply base variance
            variance_key = f"{traffic_type}_variance"
            variance = self.current_profile.get(variance_key, 0.2)
            variance_factor = 1 + variance * (random.random() - 0.5) * 2
            speed *= variance_factor

            # Apply time-based patterns if enabled
            if self.time_based_patterns:
                time_factor = self._get_time_based_factor(current_time)
                speed *= time_factor

            # Apply burst/idle states
            speed = self._apply_burst_idle_states(speed, current_time)

            # Apply network congestion simulation
            congestion_factor = self._simulate_network_congestion(current_time)
            speed *= congestion_factor

            # Apply peer count influence
            peer_influence = self._calculate_peer_influence()
            speed *= peer_influence

            # Ensure minimum speed and reasonable maximums
            min_speed = max(1024, base_speed * 0.01)  # At least 1KB/s or 1% of base
            max_speed = base_speed * 3  # Maximum 3x base speed

            speed = max(min_speed, min(speed, max_speed))

            return int(speed)

        except Exception as e:
            logger.error(
                f"Failed to calculate realistic speed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return base_speed

    def _get_time_based_factor(self, current_time: float) -> float:
        """
        Calculate time-based speed factor (day/night patterns, weekday/weekend)

        Args:
            current_time: Current timestamp

        Returns:
            Speed multiplier factor
        """
        try:
            # Get local time
            local_time = time.localtime(current_time)
            hour = local_time.tm_hour
            day_of_week = local_time.tm_wday  # 0 = Monday, 6 = Sunday

            # Get time pattern settings from configuration
            time_patterns = self.traffic_config.get("time_patterns", {})
            peak_start = time_patterns.get("peak_hours_start", 8)
            peak_end_morning = time_patterns.get("peak_hours_end_morning", 12)
            peak_start_evening = time_patterns.get("peak_hours_start_evening", 18)
            peak_end_evening = time_patterns.get("peak_hours_end_evening", 23)
            night_start = time_patterns.get("night_hours_start", 0)
            night_end = time_patterns.get("night_hours_end", 6)
            peak_multiplier = time_patterns.get("peak_multiplier", 1.2)
            night_multiplier = time_patterns.get("night_multiplier", 0.7)
            weekend_multiplier = time_patterns.get("weekend_multiplier", 1.1)

            # Time of day factor (peak hours have higher speeds)
            if (peak_start <= hour <= peak_end_morning) or (peak_start_evening <= hour <= peak_end_evening):
                time_factor = peak_multiplier
            elif night_start <= hour <= night_end:  # Night hours
                time_factor = night_multiplier
            else:  # Off-peak hours
                time_factor = 1.0

            # Day of week factor (weekends slightly different)
            if day_of_week >= 5:  # Weekend
                time_factor *= weekend_multiplier

            return time_factor

        except Exception:
            return 1.0

    def _apply_burst_idle_states(self, speed: float, current_time: float) -> float:
        """
        Apply burst and idle state modifications

        Args:
            speed: Current speed
            current_time: Current timestamp

        Returns:
            Modified speed
        """
        try:
            # Check for burst state transitions
            if not self.current_burst_state:
                if random.random() < self.current_profile["burst_probability"] / 60:  # Per second
                    self.current_burst_state = True
                    self.burst_start_time = current_time
                    burst_settings = self.traffic_config.get("burst_settings", {})
                    min_duration = burst_settings.get("min_duration", 5)
                    max_duration = burst_settings.get("max_duration", 30)
                    self.burst_duration = random.uniform(min_duration, max_duration)
            else:
                if current_time - self.burst_start_time > self.burst_duration:
                    self.current_burst_state = False

            # Check for idle state transitions
            if not self.idle_state:
                if random.random() < self.current_profile["idle_probability"] / 300:  # Per 5 minutes
                    self.idle_state = True
                    self.idle_start_time = current_time
                    idle_settings = self.traffic_config.get("idle_settings", {})
                    min_duration = idle_settings.get("min_duration", 10)
                    max_duration = idle_settings.get("max_duration", 120)
                    self.idle_duration = random.uniform(min_duration, max_duration)
            else:
                if current_time - self.idle_start_time > self.idle_duration:
                    self.idle_state = False

            # Apply state modifications
            if self.current_burst_state:
                burst_settings = self.traffic_config.get("burst_settings", {})
                min_mult = burst_settings.get("min_multiplier", 2.0)
                max_mult = burst_settings.get("max_multiplier", 5.0)
                speed *= random.uniform(min_mult, max_mult)
            elif self.idle_state:
                idle_settings = self.traffic_config.get("idle_settings", {})
                min_mult = idle_settings.get("min_multiplier", 0.1)
                max_mult = idle_settings.get("max_multiplier", 0.3)
                speed *= random.uniform(min_mult, max_mult)

            return speed

        except Exception:
            return speed

    def _simulate_network_congestion(self, current_time: float) -> float:
        """
        Simulate network congestion effects

        Args:
            current_time: Current timestamp

        Returns:
            Congestion factor (0.5 to 1.0)
        """
        try:
            # Use sine wave for gradual congestion changes
            congestion_settings = self.traffic_config.get("congestion_simulation", {})
            cycle_duration = congestion_settings.get("cycle_duration", 300)
            base_factor = congestion_settings.get("base_factor", 0.75)
            variance_factor = congestion_settings.get("variance_factor", 0.25)
            random_variance = congestion_settings.get("random_variance", 0.1)

            congestion_cycle = math.sin(current_time / cycle_duration) * variance_factor + base_factor

            # Add random fluctuations
            random_min = 1.0 - random_variance
            random_max = 1.0 + random_variance
            random_factor = random.uniform(random_min, random_max)

            return congestion_cycle * random_factor

        except Exception:
            return 1.0

    def _calculate_peer_influence(self) -> float:
        """
        Calculate influence of peer count on speeds

        Returns:
            Peer influence factor
        """
        try:
            # More peers generally mean better speeds (up to a point)
            recent_connections = [
                conn for conn in self.connection_history if time.time() - conn["timestamp"] < 300  # Last 5 minutes
            ]

            peer_count = len(recent_connections)

            peer_influence_settings = self.traffic_config.get("peer_influence", {})
            few_peers_threshold = peer_influence_settings.get("few_peers_threshold", 5)
            optimal_peers_threshold = peer_influence_settings.get("optimal_peers_threshold", 20)
            few_peers_factor = peer_influence_settings.get("few_peers_factor", 0.8)
            improvement_per_peer = peer_influence_settings.get("improvement_per_peer", 0.02)
            max_improvement_factor = peer_influence_settings.get("max_improvement_factor", 1.3)

            if peer_count < few_peers_threshold:
                return few_peers_factor  # Reduced speed with few peers
            elif peer_count < optimal_peers_threshold:
                return 1.0 + (peer_count - few_peers_threshold) * improvement_per_peer  # Gradual improvement
            else:
                return max_improvement_factor  # Cap at maximum improvement

        except Exception:
            return 1.0

    def _generate_peer_interaction(self, timestamp: float, peer_index: int) -> Dict:
        """
        Generate realistic peer interaction event

        Args:
            timestamp: Event timestamp
            peer_index: Peer index

        Returns:
            Peer interaction event dictionary
        """
        try:
            # Generate realistic peer address
            ip_parts = [
                random.randint(1, 223),
                random.randint(1, 254),
                random.randint(1, 254),
                random.randint(1, 254),
            ]
            ip_address = ".".join(map(str, ip_parts))

            # Generate realistic port
            port = random.choice(
                [
                    random.randint(6881, 6889),
                    random.randint(49152, 65535),
                ]  # Traditional BT ports  # Dynamic ports
            )

            # Generate interaction type
            interaction_types = [
                "connect",
                "disconnect",
                "piece_exchange",
                "keep_alive",
            ]
            weights = [0.3, 0.2, 0.4, 0.1]
            interaction_type = random.choices(interaction_types, weights=weights)[0]

            # Calculate connection duration
            if interaction_type == "connect":
                duration = random.expovariate(1.0 / self.current_profile["connection_timeout"])
            else:
                duration = 0

            return {
                "timestamp": timestamp,
                "peer_index": peer_index,
                "ip_address": ip_address,
                "port": port,
                "interaction_type": interaction_type,
                "duration": duration,
                "bytes_exchanged": random.randint(1024, 1024 * 1024),  # 1KB to 1MB
            }

        except Exception as e:
            logger.error(
                f"Failed to generate peer interaction: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {
                "timestamp": timestamp,
                "peer_index": peer_index,
                "interaction_type": "error",
            }

    def get_current_speeds(self) -> Dict[str, Any]:
        """
        Get current simulated speeds

        Returns:
            Dictionary with current upload/download speeds
        """
        current_time = time.time()

        upload_speed = self._calculate_realistic_speed(
            self.current_profile["base_upload_speed"], "upload", current_time
        )

        download_speed = self._calculate_realistic_speed(
            self.current_profile["base_download_speed"], "download", current_time
        )

        return {
            "upload_speed": upload_speed,
            "download_speed": download_speed,
            "timestamp": current_time,
        }

    def get_statistics(self) -> Dict:
        """
        Get traffic pattern statistics

        Returns:
            Statistics dictionary
        """
        current_time = time.time()
        session_duration = current_time - self.session_start_time

        # Calculate average speeds from history
        recent_traffic = [t for t in self.traffic_history if current_time - t["timestamp"] < 3600]  # Last hour

        upload_speeds = [t["speed"] for t in recent_traffic if t["type"] == "upload"]
        download_speeds = [t["speed"] for t in recent_traffic if t["type"] == "download"]

        return {
            "profile": self.profile_name,
            "session_duration": session_duration,
            "current_burst_state": self.current_burst_state,
            "current_idle_state": self.idle_state,
            "traffic_history_size": len(self.traffic_history),
            "connection_history_size": len(self.connection_history),
            "average_upload_speed": (sum(upload_speeds) / len(upload_speeds) if upload_speeds else 0),
            "average_download_speed": (sum(download_speeds) / len(download_speeds) if download_speeds else 0),
            "realistic_variations_enabled": self.realistic_variations,
            "time_based_patterns_enabled": self.time_based_patterns,
        }

    def cleanup(self):
        """Clean up traffic pattern simulator"""
        self.traffic_history.clear()
        self.connection_history.clear()

        logger.debug(
            "Traffic pattern simulator cleaned up",
            extra={"class_name": self.__class__.__name__},
        )
