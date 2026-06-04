"""
Advanced Client Behavior Simulation

Simulates realistic BitTorrent client behavior patterns including:
- Choke/unchoke algorithms
- Interest state changes
- Piece selection strategies
- Connection management patterns
"""

# fmt: off
import random
import time
from typing import List, Optional

from d_fake_seeder.lib.logger import logger

# fmt: on


class ClientBehaviorSimulator:
    """Simulates realistic torrent client behavior"""

    def __init__(self, behavior_profile: Optional[str] = "balanced") -> None:
        """
        Initialize behavior simulator.

        Args:
            behavior_profile: Behavior profile name (conservative, balanced, aggressive)
        """
        self.behavior_profile = behavior_profile
        self.last_choke_round = 0.0
        self.choke_round_interval = 10.0  # Run choke algorithm every 10 seconds

        # Behavior profiles
        self.profiles = {
            "conservative": {
                "max_unchoked_peers": 4,
                "optimistic_unchoke_probability": 0.3,
                "interest_change_probability": 0.1,
                "choke_round_interval": 15.0,
            },
            "balanced": {
                "max_unchoked_peers": 8,
                "optimistic_unchoke_probability": 0.5,
                "interest_change_probability": 0.3,
                "choke_round_interval": 10.0,
            },
            "aggressive": {
                "max_unchoked_peers": 16,
                "optimistic_unchoke_probability": 0.7,
                "interest_change_probability": 0.5,
                "choke_round_interval": 5.0,
            },
        }

        # Load profile settings
        profile_settings = self.profiles.get(behavior_profile, self.profiles["balanced"])  # type: ignore[arg-type]
        self.max_unchoked_peers = profile_settings["max_unchoked_peers"]
        self.optimistic_unchoke_probability = profile_settings["optimistic_unchoke_probability"]
        self.interest_change_probability = profile_settings["interest_change_probability"]
        self.choke_round_interval = profile_settings["choke_round_interval"]

        logger.trace(
            f"Client behavior simulator initialized with profile: {behavior_profile}",
            "ClientBehaviorSimulator",
        )

    def simulate_tick(self, torrents: List) -> None:
        """
        Simulate client behavior for all torrents.

        Args:
            torrents: List of torrent objects to simulate behavior for
        """
        current_time = time.time()

        # Run choke algorithm periodically
        if current_time - self.last_choke_round >= self.choke_round_interval:
            self._run_choke_algorithm(torrents)
            self.last_choke_round = current_time

        # Simulate interest state changes
        self._simulate_interest_changes(torrents)

    def _run_choke_algorithm(self, torrents: List) -> None:
        """
        Simulate BitTorrent choke algorithm.

        The choke algorithm determines which peers to unchoke based on:
        - Upload rate (prefer faster uploaders)
        - Optimistic unchoke (give new peers a chance)
        - Download interest
        """
        for torrent in torrents:
            if not hasattr(torrent, "peer_protocol_manager") or not torrent.peer_protocol_manager:
                continue

            manager = torrent.peer_protocol_manager
            connections = list(manager.active_connections.values())

            if not connections:
                continue

            # Sort peers by upload rate (simulate preferring fast uploaders)
            sorted_peers = sorted(
                connections,
                key=lambda c: getattr(c.peer_info, "upload_speed", 0.0),
                reverse=True,
            )

            # Unchoke top N peers
            for i, connection in enumerate(sorted_peers):
                if i < self.max_unchoked_peers:
                    # Unchoke
                    if hasattr(connection.peer_info, "choked"):
                        connection.peer_info.choked = False
                else:
                    # Choke
                    if hasattr(connection.peer_info, "choked"):
                        connection.peer_info.choked = True

            # Optimistic unchoke - randomly unchoke one choked peer
            if random.random() < self.optimistic_unchoke_probability:
                choked_peers = [c for c in connections if getattr(c.peer_info, "choked", True)]
                if choked_peers:
                    lucky_peer = random.choice(choked_peers)
                    lucky_peer.peer_info.choked = False
                    logger.trace(
                        f"🎲 Optimistic unchoke for peer {lucky_peer.peer_info.ip}",
                        "ClientBehaviorSimulator",
                    )

    def _simulate_interest_changes(self, torrents: List) -> None:
        """
        Simulate interest state changes.

        Peers become interested/not interested based on piece availability.
        """
        for torrent in torrents:
            if not hasattr(torrent, "peer_protocol_manager") or not torrent.peer_protocol_manager:
                continue

            manager = torrent.peer_protocol_manager
            connections = list(manager.active_connections.values())

            for connection in connections:
                if random.random() < self.interest_change_probability:
                    # Toggle interest state
                    if hasattr(connection.peer_info, "interested"):
                        connection.peer_info.interested = not connection.peer_info.interested

    def change_profile(self, new_profile: str) -> None:
        """
        Change the behavior profile at runtime.

        Args:
            new_profile: New profile name (conservative, balanced, aggressive)
        """
        if new_profile not in self.profiles:
            logger.warning(
                f"Unknown behavior profile: {new_profile}, keeping current profile",
                "ClientBehaviorSimulator",
            )
            return

        self.behavior_profile = new_profile
        profile_settings = self.profiles[new_profile]
        self.max_unchoked_peers = profile_settings["max_unchoked_peers"]
        self.optimistic_unchoke_probability = profile_settings["optimistic_unchoke_probability"]
        self.interest_change_probability = profile_settings["interest_change_probability"]
        self.choke_round_interval = profile_settings["choke_round_interval"]

        logger.trace(
            f"Behavior profile changed to: {new_profile}",
            "ClientBehaviorSimulator",
        )

    def get_stats(self) -> dict:
        """Get current simulator statistics"""
        return {
            "profile": self.behavior_profile,
            "max_unchoked_peers": self.max_unchoked_peers,
            "choke_round_interval": self.choke_round_interval,
            "last_choke_round": self.last_choke_round,
        }
