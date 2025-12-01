"""
Swarm Intelligence System

Analyzes torrent swarms and adapts seeding behavior based on swarm health,
peer distribution, and network conditions for optimal fake seeding performance.
"""

# fmt: off
import random
import time
from typing import Dict, List, Optional

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import SwarmIntelligenceConstants

# fmt: on


class SwarmHealthMetrics:
    """Tracks and analyzes swarm health metrics"""

    def __init__(self, info_hash: bytes):
        """
        Initialize swarm health metrics

        Args:
            info_hash: Torrent info hash
        """
        self.info_hash = info_hash

        # Swarm composition
        self.total_seeders = 0
        self.total_leechers = 0
        self.total_peers = 0

        # Distribution metrics
        self.peer_countries: Dict[str, int] = {}
        self.peer_clients: Dict[str, int] = {}
        self.upload_speeds: List[float] = []
        self.download_speeds: List[float] = []

        # Health indicators
        self.seed_to_peer_ratio = 0.0
        self.average_upload_speed = 0.0
        self.average_download_speed = 0.0
        self.swarm_age_hours = 0.0
        self.last_update_time = time.time()

        # Swarm state
        self.is_healthy = True
        self.health_score = 1.0  # 0.0 to 1.0
        self.recommendation = "normal"  # normal, boost, reduce, pause

    def update_metrics(self, peers_data: List[Dict]):
        """
        Update metrics from peer data

        Args:
            peers_data: List of peer information dictionaries
        """
        self.total_peers = len(peers_data)
        self.total_seeders = sum(1 for p in peers_data if p.get("complete", False))
        self.total_leechers = self.total_peers - self.total_seeders

        # Calculate seed-to-peer ratio
        if self.total_peers > 0:
            self.seed_to_peer_ratio = self.total_seeders / self.total_peers
        else:
            self.seed_to_peer_ratio = 0.0

        # Update geographic distribution
        self.peer_countries.clear()
        for peer in peers_data:
            country = peer.get("country", "Unknown")
            self.peer_countries[country] = self.peer_countries.get(country, 0) + 1

        # Update client distribution
        self.peer_clients.clear()
        for peer in peers_data:
            client = peer.get("client", "Unknown")
            self.peer_clients[client] = self.peer_clients.get(client, 0) + 1

        # Update speed metrics
        self.upload_speeds = [p.get("upload_speed", 0.0) for p in peers_data if p.get("upload_speed", 0) > 0]
        self.download_speeds = [p.get("download_speed", 0.0) for p in peers_data if p.get("download_speed", 0) > 0]

        if self.upload_speeds:
            self.average_upload_speed = sum(self.upload_speeds) / len(self.upload_speeds)

        if self.download_speeds:
            self.average_download_speed = sum(self.download_speeds) / len(self.download_speeds)

        # Calculate health score
        self._calculate_health_score()

        self.last_update_time = time.time()

    def _calculate_health_score(self):
        """Calculate overall swarm health score"""
        score = 1.0

        # Factor 1: Seed-to-peer ratio (optimal: 0.1-0.3)
        if self.seed_to_peer_ratio < SwarmIntelligenceConstants.SEED_RATIO_LOW_THRESHOLD:
            # Too few seeds
            score *= SwarmIntelligenceConstants.SCORE_VERY_LOW_SEEDS
            self.recommendation = "boost"
        elif self.seed_to_peer_ratio > SwarmIntelligenceConstants.SEED_RATIO_HIGH_THRESHOLD:
            # Too many seeds (oversaturated)
            score *= SwarmIntelligenceConstants.SCORE_HIGH_SEEDS
            self.recommendation = "reduce"
        else:
            # Healthy ratio
            score *= 1.0
            self.recommendation = "normal"

        # Factor 2: Total peer count (optimal: 20-200)
        if self.total_peers < SwarmIntelligenceConstants.PEER_COUNT_VERY_LOW:
            # Very few peers (unhealthy swarm)
            score *= SwarmIntelligenceConstants.SCORE_VERY_FEW_PEERS
        elif self.total_peers > SwarmIntelligenceConstants.PEER_COUNT_VERY_HIGH:
            # Very large swarm (may not need our help)
            score *= SwarmIntelligenceConstants.SCORE_MANY_PEERS

        # Factor 3: Upload speed distribution (check for stalled peers)
        if self.upload_speeds:
            stalled_ratio = sum(
                1 for s in self.upload_speeds if s < SwarmIntelligenceConstants.STALLED_SPEED_THRESHOLD
            ) / len(self.upload_speeds)
            if stalled_ratio > SwarmIntelligenceConstants.STALLED_RATIO_THRESHOLD:
                # Many stalled peers
                score *= SwarmIntelligenceConstants.SCORE_STALLED_PEERS

        self.health_score = max(
            SwarmIntelligenceConstants.HEALTH_SCORE_MIN,
            min(SwarmIntelligenceConstants.HEALTH_SCORE_MAX, score),
        )
        self.is_healthy = self.health_score > SwarmIntelligenceConstants.HEALTH_SCORE_THRESHOLD

    def get_summary(self) -> Dict:
        """Get health metrics summary"""
        return {
            "total_peers": self.total_peers,
            "total_seeders": self.total_seeders,
            "total_leechers": self.total_leechers,
            "seed_to_peer_ratio": self.seed_to_peer_ratio,
            "health_score": self.health_score,
            "is_healthy": self.is_healthy,
            "recommendation": self.recommendation,
            "average_upload_speed": self.average_upload_speed,
            "average_download_speed": self.average_download_speed,
            "peer_countries": self.peer_countries,
            "peer_clients": self.peer_clients,
        }


class PieceSelectionStrategy:
    """Implements realistic piece selection algorithms"""

    def __init__(self, total_pieces: int):
        """
        Initialize piece selection strategy

        Args:
            total_pieces: Total number of pieces in torrent
        """
        self.total_pieces = total_pieces
        self.piece_availability: Dict[int, int] = {i: 0 for i in range(total_pieces)}
        self.completed_pieces: List[int] = []
        self.strategy = "rarest_first"  # rarest_first, sequential, random

        logger.debug(
            f"Piece selection strategy initialized with {total_pieces} pieces",
            extra={"class_name": self.__class__.__name__},
        )

    def update_availability(self, peer_bitfields: List[bytes]):
        """
        Update piece availability from peer bitfields

        Args:
            peer_bitfields: List of peer bitfield data
        """
        # Reset availability
        self.piece_availability = {i: 0 for i in range(self.total_pieces)}

        # Count availability for each piece
        for bitfield in peer_bitfields:
            for piece_index in range(min(self.total_pieces, len(bitfield) * 8)):
                byte_index = piece_index // 8
                bit_index = 7 - (piece_index % 8)

                if byte_index < len(bitfield) and (bitfield[byte_index] & (1 << bit_index)):
                    self.piece_availability[piece_index] += 1

    def select_piece(self) -> Optional[int]:
        """
        Select next piece to request based on strategy

        Returns:
            Piece index or None if no pieces available
        """
        # Filter out completed pieces
        available_pieces = [p for p in self.piece_availability.keys() if p not in self.completed_pieces]

        if not available_pieces:
            return None

        if self.strategy == "rarest_first":
            return self._select_rarest(available_pieces)
        elif self.strategy == "sequential":
            return self._select_sequential(available_pieces)
        else:
            return random.choice(available_pieces)

    def _select_rarest(self, available_pieces: List[int]) -> int:
        """Select rarest piece"""
        # Find pieces with minimum availability
        min_availability = min(self.piece_availability[p] for p in available_pieces)
        rarest_pieces = [p for p in available_pieces if self.piece_availability[p] == min_availability]

        # Random selection among rarest
        return random.choice(rarest_pieces)

    def _select_sequential(self, available_pieces: List[int]) -> int:
        """Select next sequential piece"""
        return min(available_pieces)

    def mark_completed(self, piece_index: int):
        """Mark piece as completed"""
        if piece_index not in self.completed_pieces:
            self.completed_pieces.append(piece_index)

    def is_endgame(self) -> bool:
        """Check if we're in endgame mode (>95% complete)"""
        completion = len(self.completed_pieces) / self.total_pieces if self.total_pieces > 0 else 0
        return completion > SwarmIntelligenceConstants.ENDGAME_COMPLETION_THRESHOLD


class SwarmIntelligence:
    """Main swarm intelligence system"""

    def __init__(self, torrent_manager=None):
        """
        Initialize swarm intelligence system

        Args:
            torrent_manager: Optional torrent manager for coordination
        """
        self.torrent_manager = torrent_manager
        self.settings = AppSettings.get_instance()

        # Swarm tracking
        self.swarm_metrics: Dict[bytes, SwarmHealthMetrics] = {}
        self.piece_strategies: Dict[bytes, PieceSelectionStrategy] = {}

        # Configuration
        si_config = getattr(self.settings, "simulation", {}).get("swarm_intelligence", {})
        self.enabled = si_config.get("enabled", True)
        self.adaptation_rate = si_config.get("adaptation_rate", 0.5)
        self.peer_analysis_depth = si_config.get("peer_analysis_depth", 10)

        # Behavior state
        self.current_behaviors: Dict[bytes, str] = {}  # info_hash -> behavior_mode

        logger.info(
            "Swarm Intelligence system initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def register_torrent(self, info_hash: bytes, total_pieces: int):
        """
        Register torrent for swarm intelligence

        Args:
            info_hash: Torrent info hash
            total_pieces: Total number of pieces
        """
        if info_hash not in self.swarm_metrics:
            self.swarm_metrics[info_hash] = SwarmHealthMetrics(info_hash)
            self.piece_strategies[info_hash] = PieceSelectionStrategy(total_pieces)
            self.current_behaviors[info_hash] = "normal"

            logger.info(
                f"Registered torrent {info_hash.hex()[:16]} for swarm intelligence",
                extra={"class_name": self.__class__.__name__},
            )

    def analyze_swarm(self, info_hash: bytes, peers_data: List[Dict]) -> Dict:
        """
        Analyze swarm health and provide recommendations

        Args:
            info_hash: Torrent info hash
            peers_data: List of peer information

        Returns:
            Analysis results with recommendations
        """
        if info_hash not in self.swarm_metrics:
            return {"error": "Torrent not registered"}

        try:
            # Update metrics
            metrics = self.swarm_metrics[info_hash]
            metrics.update_metrics(peers_data)

            # Get current behavior recommendation
            summary = metrics.get_summary()

            logger.debug(
                f"Swarm analysis for {info_hash.hex()[:16]}: "
                f"{summary['total_peers']} peers, health={summary['health_score']:.2f}",
                extra={"class_name": self.__class__.__name__},
            )

            return summary

        except Exception as e:
            logger.error(
                f"Failed to analyze swarm: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {"error": str(e)}

    def adapt_seeding_behavior(self, info_hash: bytes) -> Dict[str, any]:
        """
        Adapt seeding behavior based on swarm analysis

        Args:
            info_hash: Torrent info hash

        Returns:
            Recommended behavior adjustments
        """
        if info_hash not in self.swarm_metrics:
            return {"behavior": "normal"}

        try:
            metrics = self.swarm_metrics[info_hash]
            recommendation = metrics.recommendation

            # Calculate behavior adjustments
            adjustments = self._calculate_adjustments(metrics)

            # Update current behavior
            self.current_behaviors[info_hash] = recommendation

            logger.debug(
                f"Adapted behavior for {info_hash.hex()[:16]}: {recommendation}",
                extra={"class_name": self.__class__.__name__},
            )

            return {
                "behavior": recommendation,
                "upload_speed_multiplier": adjustments["upload_multiplier"],
                "connection_limit_multiplier": adjustments["connection_multiplier"],
                "announce_frequency_multiplier": adjustments["announce_multiplier"],
                "peer_exchange_enabled": adjustments["pex_enabled"],
            }

        except Exception as e:
            logger.error(
                f"Failed to adapt behavior: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {"behavior": "normal"}

    def _calculate_adjustments(self, metrics: SwarmHealthMetrics) -> Dict:
        """Calculate behavior adjustment multipliers"""
        adjustments = {
            "upload_multiplier": 1.0,
            "connection_multiplier": 1.0,
            "announce_multiplier": 1.0,
            "pex_enabled": True,
        }

        if metrics.recommendation == "boost":
            # Unhealthy swarm - be more active
            adjustments["upload_multiplier"] = SwarmIntelligenceConstants.BOOST_UPLOAD_MULTIPLIER
            adjustments["connection_multiplier"] = SwarmIntelligenceConstants.BOOST_CONNECTION_MULTIPLIER
            adjustments["announce_multiplier"] = SwarmIntelligenceConstants.BOOST_ANNOUNCE_MULTIPLIER
            adjustments["pex_enabled"] = True

        elif metrics.recommendation == "reduce":
            # Oversaturated swarm - be less active
            adjustments["upload_multiplier"] = SwarmIntelligenceConstants.REDUCE_UPLOAD_MULTIPLIER
            adjustments["connection_multiplier"] = SwarmIntelligenceConstants.REDUCE_CONNECTION_MULTIPLIER
            adjustments["announce_multiplier"] = SwarmIntelligenceConstants.REDUCE_ANNOUNCE_MULTIPLIER
            adjustments["pex_enabled"] = True

        elif metrics.recommendation == "pause":
            # Swarm doesn't need us
            adjustments["upload_multiplier"] = SwarmIntelligenceConstants.PAUSE_UPLOAD_MULTIPLIER
            adjustments["connection_multiplier"] = SwarmIntelligenceConstants.PAUSE_CONNECTION_MULTIPLIER
            adjustments["announce_multiplier"] = SwarmIntelligenceConstants.PAUSE_ANNOUNCE_MULTIPLIER
            adjustments["pex_enabled"] = False

        # Apply adaptation rate
        for key in [
            "upload_multiplier",
            "connection_multiplier",
            "announce_multiplier",
        ]:
            # Smooth transitions using adaptation rate
            adjustments[key] = 1.0 + (adjustments[key] - 1.0) * self.adaptation_rate

        return adjustments

    def select_piece(self, info_hash: bytes) -> Optional[int]:
        """
        Select optimal piece using intelligent strategy

        Args:
            info_hash: Torrent info hash

        Returns:
            Piece index or None
        """
        if info_hash not in self.piece_strategies:
            return None

        strategy = self.piece_strategies[info_hash]
        return strategy.select_piece()

    def update_piece_availability(self, info_hash: bytes, peer_bitfields: List[bytes]):
        """
        Update piece availability information

        Args:
            info_hash: Torrent info hash
            peer_bitfields: List of peer bitfields
        """
        if info_hash in self.piece_strategies:
            self.piece_strategies[info_hash].update_availability(peer_bitfields)

    def get_statistics(self) -> Dict:
        """Get swarm intelligence statistics"""
        return {
            "enabled": self.enabled,
            "tracked_torrents": len(self.swarm_metrics),
            "swarms": {
                info_hash.hex()[:16]: {
                    "metrics": metrics.get_summary(),
                    "behavior": self.current_behaviors.get(info_hash, "normal"),
                }
                for info_hash, metrics in self.swarm_metrics.items()
            },
        }

    def cleanup(self):
        """Clean up swarm intelligence data"""
        self.swarm_metrics.clear()
        self.piece_strategies.clear()
        self.current_behaviors.clear()

        logger.debug(
            "Swarm intelligence cleaned up",
            extra={"class_name": self.__class__.__name__},
        )
