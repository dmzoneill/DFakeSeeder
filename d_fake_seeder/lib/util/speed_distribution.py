"""
Speed distribution algorithms for realistic torrent seeding.

Provides multiple distribution algorithms to make torrent upload/download speeds
look more realistic and less uniform across multiple torrents.
"""

import math
import random
from abc import ABC, abstractmethod
from typing import Dict, List

from d_fake_seeder.lib.logger import logger


class SpeedDistributor(ABC):
    """Base class for speed distribution algorithms."""

    def __init__(self, percentage: float = 50.0, stopped_percentage: float = 0.0) -> None:
        """
        Initialize distributor.

        Args:
            percentage: Algorithm-specific parameter (0-100)
            stopped_percentage: Percentage of torrents to stop completely (0-100)
        """
        self.percentage = max(0.0, min(100.0, percentage))
        self.stopped_percentage = max(0.0, min(100.0, stopped_percentage))

    @abstractmethod
    def distribute(self, total_bandwidth: float, torrent_ids: List[str]) -> Dict[str, float]:
        """
        Distribute bandwidth across torrents.

        Args:
            total_bandwidth: Total bandwidth to distribute (KB/s)
            torrent_ids: List of torrent identifiers

        Returns:
            Dictionary mapping torrent_id to speed (KB/s)
        """
        pass

    @abstractmethod
    def get_algorithm_name(self) -> str:
        """Return the name of this algorithm."""
        pass

    def _apply_stopped_torrents(self, torrent_ids: List[str]) -> tuple[List[str], List[str]]:
        """
        Randomly select torrents to stop based on stopped_percentage.

        Args:
            torrent_ids: List of all torrent IDs

        Returns:
            Tuple of (active_torrent_ids, stopped_torrent_ids)
        """
        if self.stopped_percentage <= 0 or not torrent_ids:
            return torrent_ids, []

        n_total = len(torrent_ids)
        n_stopped = max(0, int(math.ceil(n_total * (self.stopped_percentage / 100.0))))

        if n_stopped >= n_total:
            # Stop all torrents
            return [], torrent_ids

        # Randomly select torrents to stop
        shuffled = torrent_ids.copy()
        random.shuffle(shuffled)

        stopped_ids = shuffled[:n_stopped]
        active_ids = shuffled[n_stopped:]

        logger.debug(
            f"Stopped {n_stopped}/{n_total} torrents ({self.stopped_percentage}%)",
            "SpeedDistributor",
        )

        return active_ids, stopped_ids

    def _ensure_unique_speeds(self, speeds: Dict[str, float]) -> Dict[str, float]:
        """
        Ensure no two torrents have exactly the same speed.

        Args:
            speeds: Dictionary of torrent speeds

        Returns:
            Modified dictionary with unique speeds
        """
        # Add tiny random jitter to prevent identical speeds
        result = {}
        for torrent_id, speed in speeds.items():
            # Skip category metadata entries (they're strings, not floats)
            if torrent_id.endswith("_category"):
                result[torrent_id] = speed
                continue

            jitter = random.uniform(0.999, 1.001)
            result[torrent_id] = speed * jitter
        return result


class ParetoDistributor(SpeedDistributor):
    """
    Pareto distribution (80/20 rule).

    The percentage parameter controls the ratio:
    - 80 (default): 80% of torrents get 20% of bandwidth, 20% get 80%
    - 70: 70% of torrents get 30% of bandwidth, 30% get 70%
    - 90: 90% of torrents get 10% of bandwidth, 10% get 90%
    """

    def get_algorithm_name(self) -> str:
        return "Pareto"

    def distribute(self, total_bandwidth: float, torrent_ids: List[str]) -> Dict[str, float]:
        """Distribute using Pareto principle."""
        if not torrent_ids:
            return {}

        # Apply stopped torrents percentage
        active_ids, stopped_ids = self._apply_stopped_torrents(torrent_ids)

        # Initialize speeds dict with stopped torrents at 0
        speeds = {}
        for tid in stopped_ids:
            speeds[tid] = 0.0
            speeds[tid + "_category"] = "Stopped"  # type: ignore[assignment]

        # If all torrents are stopped, return early
        if not active_ids:
            return speeds

        # If only one active torrent, give it all bandwidth
        if len(active_ids) == 1:
            speeds[active_ids[0]] = total_bandwidth
            return speeds

        n = len(active_ids)

        # Calculate tier sizes
        # percentage% of torrents are in "bottom" tier
        n_bottom = max(1, int(math.ceil(n * (self.percentage / 100.0))))
        n_top = n - n_bottom

        # percentage% of bandwidth goes to "top" tier
        b_top = total_bandwidth * ((100.0 - self.percentage) / 100.0)
        b_bottom = total_bandwidth * (self.percentage / 100.0)

        logger.debug(
            f"Pareto distribution: {n} active torrents, {n_top} top ({b_top:.1f} KB/s), "
            f"{n_bottom} bottom ({b_bottom:.1f} KB/s), {len(stopped_ids)} stopped",
            "ParetoDistributor",
        )

        # Shuffle to randomize which torrents are in which tier
        shuffled_ids = active_ids.copy()
        random.shuffle(shuffled_ids)

        # Top tier (few torrents, high speeds)
        if n_top > 0 and b_top > 0:
            top_ids = shuffled_ids[:n_top]
            speeds.update(self._distribute_tier(b_top, top_ids, "Top"))

        # Bottom tier (many torrents, low speeds)
        if n_bottom > 0 and b_bottom > 0:
            bottom_ids = shuffled_ids[n_top:]
            speeds.update(self._distribute_tier(b_bottom, bottom_ids, "Bottom"))

        return self._ensure_unique_speeds(speeds)

    def _distribute_tier(self, bandwidth: float, torrent_ids: List[str], tier: str) -> Dict[str, float]:
        """Distribute bandwidth within a tier using random weights."""
        if not torrent_ids:
            return {}

        # Generate random weights
        weights = [random.uniform(0.5, 1.5) for _ in torrent_ids]
        total_weight = sum(weights)

        # Distribute proportionally
        speeds = {}
        for tid, weight in zip(torrent_ids, weights):
            speeds[tid] = (weight / total_weight) * bandwidth
            speeds[tid + "_category"] = tier  # type: ignore[assignment]

        return speeds


class PowerLawDistributor(SpeedDistributor):
    """
    Power law distribution.

    The percentage parameter controls the steepness:
    - 0: Very shallow curve (α=0.5), speeds are relatively similar
    - 50: Medium curve (α=1.75), moderate variation
    - 100: Very steep curve (α=3.0), extreme variation in speeds
    """

    def get_algorithm_name(self) -> str:
        return "Power-Law"

    def distribute(self, total_bandwidth: float, torrent_ids: List[str]) -> Dict[str, float]:
        """Distribute using power law."""
        if not torrent_ids:
            return {}

        # Apply stopped torrents percentage
        active_ids, stopped_ids = self._apply_stopped_torrents(torrent_ids)

        # Initialize speeds dict with stopped torrents at 0
        speeds = {}
        for tid in stopped_ids:
            speeds[tid] = 0.0

        # If all torrents are stopped, return early
        if not active_ids:
            return speeds

        # If only one active torrent, give it all bandwidth
        if len(active_ids) == 1:
            speeds[active_ids[0]] = total_bandwidth
            return speeds

        n = len(active_ids)

        # Convert percentage to alpha (power law exponent)
        # 0% -> α=0.5 (shallow), 100% -> α=3.0 (steep)
        alpha = 0.5 + (self.percentage / 100.0) * 2.5

        logger.debug(
            f"Power-law distribution: {n} active torrents, α={alpha:.2f}, {len(stopped_ids)} stopped",
            "PowerLawDistributor",
        )

        # Shuffle to randomize assignment
        shuffled_ids = active_ids.copy()
        random.shuffle(shuffled_ids)

        # Generate power law weights
        weights = []
        for rank in range(1, n + 1):
            weight = 1.0 / (rank**alpha)
            weights.append(weight)

        total_weight = sum(weights)

        # Distribute bandwidth
        for tid, weight in zip(shuffled_ids, weights):
            speed = (weight / total_weight) * total_bandwidth
            # Add small jitter for variation
            speed *= random.uniform(0.95, 1.05)
            speeds[tid] = max(0.0, speed)

        return self._ensure_unique_speeds(speeds)


class LogNormalDistributor(SpeedDistributor):
    """
    Log-normal distribution.

    The percentage parameter controls the spread (standard deviation):
    - 0: Very narrow spread (σ=0.1), speeds cluster near mean
    - 50: Medium spread (σ=1.0), moderate variation
    - 100: Very wide spread (σ=2.0), extreme variation with long tail
    """

    def get_algorithm_name(self) -> str:
        return "Log-Normal"

    def distribute(self, total_bandwidth: float, torrent_ids: List[str]) -> Dict[str, float]:
        """Distribute using log-normal distribution."""
        if not torrent_ids:
            return {}

        # Apply stopped torrents percentage
        active_ids, stopped_ids = self._apply_stopped_torrents(torrent_ids)

        # Initialize speeds dict with stopped torrents at 0
        speeds = {}
        for tid in stopped_ids:
            speeds[tid] = 0.0

        # If all torrents are stopped, return early
        if not active_ids:
            return speeds

        # If only one active torrent, give it all bandwidth
        if len(active_ids) == 1:
            speeds[active_ids[0]] = total_bandwidth
            return speeds

        n = len(active_ids)

        # Convert percentage to sigma (standard deviation)
        # 0% -> σ=0.1 (narrow), 100% -> σ=2.0 (wide)
        sigma = 0.1 + (self.percentage / 100.0) * 1.9

        # Calculate mu (mean in log space)
        # We want the mean speed to be roughly total_bandwidth / n
        mu = math.log(total_bandwidth / n)

        logger.debug(
            f"Log-normal distribution: {n} active torrents, σ={sigma:.2f}, μ={mu:.2f}, {len(stopped_ids)} stopped",
            "LogNormalDistributor",
        )

        # Generate log-normal samples
        raw_speeds = []
        for _ in range(n):
            # Generate standard normal random value
            z = random.gauss(0, 1)
            # Convert to log-normal
            raw_speed = math.exp(mu + sigma * z)
            raw_speeds.append(max(0.1, raw_speed))  # Ensure positive

        # Normalize to exactly match total bandwidth
        total_raw = sum(raw_speeds)
        normalized_speeds = [(speed / total_raw) * total_bandwidth for speed in raw_speeds]

        # Shuffle to randomize assignment
        shuffled_ids = active_ids.copy()
        random.shuffle(shuffled_ids)

        # Assign speeds
        for tid, speed in zip(shuffled_ids, normalized_speeds):
            speeds[tid] = speed

        return self._ensure_unique_speeds(speeds)


class OffDistributor(SpeedDistributor):
    """
    No distribution - equal speeds for all torrents.

    Used when speed distribution is disabled.
    """

    def get_algorithm_name(self) -> str:
        return "Off"

    def distribute(self, total_bandwidth: float, torrent_ids: List[str]) -> Dict[str, float]:
        """Distribute equally across all torrents."""
        n = len(torrent_ids)

        if n == 0:
            return {}

        speed_per_torrent = total_bandwidth / n

        return {tid: speed_per_torrent for tid in torrent_ids}


def create_distributor(algorithm: str, percentage: float = 50.0, stopped_percentage: float = 0.0) -> SpeedDistributor:
    """
    Factory function to create a speed distributor.

    Args:
        algorithm: Algorithm name ("off", "pareto", "power-law", "log-normal")
        percentage: Algorithm-specific parameter (0-100)
        stopped_percentage: Percentage of torrents to stop completely (0-100)

    Returns:
        SpeedDistributor instance
    """
    algorithm = algorithm.lower().strip()

    distributors = {
        "off": OffDistributor,
        "pareto": ParetoDistributor,
        "power-law": PowerLawDistributor,
        "power_law": PowerLawDistributor,
        "powerlaw": PowerLawDistributor,
        "log-normal": LogNormalDistributor,
        "log_normal": LogNormalDistributor,
        "lognormal": LogNormalDistributor,
    }

    distributor_class = distributors.get(algorithm, OffDistributor)
    return distributor_class(percentage, stopped_percentage)  # type: ignore[abstract]


def format_debug_output(torrent_name: str, algorithm: str, speed: float, category: str = None) -> str:  # type: ignore[assignment]  # noqa: E501
    """
    Format debug output for a torrent's distributed speed.

    Args:
        torrent_name: Name of the torrent
        algorithm: Algorithm used
        speed: Speed in KB/s
        category: Optional category (e.g., "Top 20%", "Bottom 80%")

    Returns:
        Formatted debug string
    """
    if speed == 0:
        return f"[SpeedDist] {torrent_name} [Algorithm: {algorithm}, Speed: 0 KB/s, Stopped]"

    if category:
        return f"[SpeedDist] {torrent_name} [Algorithm: {algorithm}, Speed: {speed:.2f} KB/s, Category: {category}]"

    return f"[SpeedDist] {torrent_name} [Algorithm: {algorithm}, Speed: {speed:.2f} KB/s]"
