"""
Advanced Simulation Engines

Provides sophisticated simulation capabilities for realistic BitTorrent behavior,
including client behavior emulation, traffic pattern simulation, and swarm intelligence.
"""

from .client_behavior import ClientBehaviorEngine
from .traffic_patterns import TrafficPatternSimulator

__all__ = ["ClientBehaviorEngine", "TrafficPatternSimulator"]
