"""
Advanced Simulation Engines

Provides sophisticated simulation capabilities for realistic BitTorrent behavior,
including client behavior emulation, traffic pattern simulation, and swarm intelligence.
"""

# fmt: off
from .client_behavior import ClientBehaviorEngine
from .swarm_intelligence import (
    PieceSelectionStrategy,
    SwarmHealthMetrics,
    SwarmIntelligence,
)
from .traffic_patterns import TrafficPatternSimulator

__all__ = [
    "ClientBehaviorEngine",
    "TrafficPatternSimulator",
    "SwarmIntelligence",
    "SwarmHealthMetrics",
    "PieceSelectionStrategy",
]

# fmt: on
