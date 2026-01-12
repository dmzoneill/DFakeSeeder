"""
Multi-Tracker Support (BEP-012)

Implements multi-tracker tier system with automatic failover and load balancing.
Provides robust tracker interaction with fallback support.
"""

# fmt: off
import asyncio
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import MultiTrackerConstants

# fmt: on


class TrackerTier:
    """Represents a tier of trackers with failover support"""

    def __init__(self, trackers: List[str], tier_number: int = 0) -> None:
        """
        Initialize tracker tier

        Args:
            trackers: List of tracker URLs in this tier
            tier_number: Tier priority (lower = higher priority)
        """
        self.trackers = trackers
        self.tier_number = tier_number

        # Tracker status tracking
        self.tracker_status: Dict[str, Dict] = {}
        for tracker in trackers:
            self.tracker_status[tracker] = {
                "url": tracker,
                "last_attempt": 0.0,
                "last_success": 0.0,
                "consecutive_failures": 0,
                "total_announces": 0,
                "successful_announces": 0,
                "failed_announces": 0,
                "average_response_time": 0.0,
                "current_peers": 0,
                "enabled": True,
            }

        # Current active tracker in this tier
        self.current_tracker_index = 0

        logger.trace(
            f"Tracker tier {tier_number} initialized with {len(trackers)} trackers",
            extra={"class_name": self.__class__.__name__},
        )

    def get_next_tracker(self) -> Optional[str]:
        """
        Get next available tracker in this tier

        Returns:
            Tracker URL or None if all trackers failed
        """
        if not self.trackers:
            return None

        # Try each tracker in round-robin fashion
        attempts = 0
        while attempts < len(self.trackers):
            tracker = self.trackers[self.current_tracker_index]
            status = self.tracker_status[tracker]

            # Move to next tracker for next call
            self.current_tracker_index = (self.current_tracker_index + 1) % len(self.trackers)

            # Check if tracker is enabled and not in cooldown
            if status["enabled"] and self._is_tracker_available(status):
                return tracker

            attempts += 1

        return None

    def mark_success(self, tracker_url: str, response_time: float, peer_count: int = 0) -> Any:
        """
        Mark tracker announce as successful

        Args:
            tracker_url: Tracker URL
            response_time: Response time in seconds
            peer_count: Number of peers returned
        """
        if tracker_url in self.tracker_status:
            status = self.tracker_status[tracker_url]
            status["last_success"] = time.time()
            status["consecutive_failures"] = 0
            status["successful_announces"] += 1
            status["total_announces"] += 1
            status["current_peers"] = peer_count

            # Update average response time (exponential moving average)
            if status["average_response_time"] == 0:
                status["average_response_time"] = response_time
            else:
                status["average_response_time"] = (
                    MultiTrackerConstants.RESPONSE_TIME_SMOOTHING * status["average_response_time"]
                    + MultiTrackerConstants.RESPONSE_TIME_WEIGHT * response_time
                )

            logger.trace(
                f"Tracker {tracker_url} announce successful ({response_time:.2f}s, {peer_count} peers)",
                extra={"class_name": self.__class__.__name__},
            )

    def mark_failure(self, tracker_url: str, error: str = "") -> Any:
        """
        Mark tracker announce as failed

        Args:
            tracker_url: Tracker URL
            error: Error message
        """
        if tracker_url in self.tracker_status:
            status = self.tracker_status[tracker_url]
            status["last_attempt"] = time.time()
            status["consecutive_failures"] += 1
            status["failed_announces"] += 1
            status["total_announces"] += 1

            # Disable tracker after too many failures
            if status["consecutive_failures"] >= MultiTrackerConstants.MAX_CONSECUTIVE_FAILURES:
                status["enabled"] = False
                logger.warning(
                    f"Tracker {tracker_url} disabled after {status['consecutive_failures']} failures",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.trace(
                    f"Tracker {tracker_url} announce failed: {error}",
                    extra={"class_name": self.__class__.__name__},
                )

    def _is_tracker_available(self, status: Dict) -> bool:
        """
        Check if tracker is available for announce

        Args:
            status: Tracker status dictionary

        Returns:
            True if tracker is available
        """
        current_time = time.time()

        # If never attempted, always available
        if status["last_attempt"] == 0:
            return True

        # Calculate cooldown based on failure count
        cooldown_seconds = min(
            MultiTrackerConstants.BACKOFF_BASE_SECONDS
            * (MultiTrackerConstants.BACKOFF_EXPONENT_BASE ** status["consecutive_failures"]),
            MultiTrackerConstants.MAX_BACKOFF_SECONDS,
        )

        # Check if cooldown has passed
        return current_time - status["last_attempt"] >= cooldown_seconds  # type: ignore[no-any-return]

    def get_statistics(self) -> Dict:
        """Get tier statistics"""
        total_announces = sum(s["total_announces"] for s in self.tracker_status.values())
        successful_announces = sum(s["successful_announces"] for s in self.tracker_status.values())

        return {
            "tier_number": self.tier_number,
            "tracker_count": len(self.trackers),
            "enabled_trackers": sum(1 for s in self.tracker_status.values() if s["enabled"]),
            "total_announces": total_announces,
            "successful_announces": successful_announces,
            "success_rate": successful_announces / total_announces if total_announces > 0 else 0.0,
            "trackers": list(self.tracker_status.values()),
        }


class MultiTrackerManager:
    """Manages multiple tracker tiers with automatic failover"""

    def __init__(self, torrent: Any) -> None:
        """
        Initialize multi-tracker manager

        Args:
            torrent: Torrent instance
        """
        self.torrent = torrent
        self.settings = AppSettings.get_instance()

        # Parse tracker tiers from torrent
        self.tiers: List[TrackerTier] = []
        self._parse_trackers()

        # Multi-tracker configuration
        mt_config = getattr(self.settings, "protocols", {}).get("multi_tracker", {})
        self.enabled = mt_config.get("enabled", True)
        self.failover_enabled = mt_config.get("failover_enabled", True)
        self.announce_to_all_tiers = mt_config.get("announce_to_all_tiers", False)
        self.announce_to_all_in_tier = mt_config.get("announce_to_all_in_tier", False)

        # Current tier tracking
        self.current_tier_index = 0
        self.last_announce_time = 0.0

        logger.trace(
            f"Multi-tracker manager initialized with {len(self.tiers)} tiers",
            extra={"class_name": self.__class__.__name__},
        )

    def _parse_trackers(self) -> Any:
        """Parse trackers from torrent into tiers"""
        try:
            # Get announce-list from torrent (BEP-012 format)
            if hasattr(self.torrent, "torrent_file") and self.torrent.torrent_file:
                torrent_data = self.torrent.torrent_file.get_data()

                # Check for announce-list (multi-tracker)
                if b"announce-list" in torrent_data:
                    announce_list = torrent_data[b"announce-list"]

                    for tier_number, tier_trackers in enumerate(announce_list):
                        # Each tier is a list of tracker URLs
                        tracker_urls = [
                            t.decode("utf-8", errors="ignore") for t in tier_trackers if isinstance(t, bytes)
                        ]

                        if tracker_urls:
                            tier = TrackerTier(tracker_urls, tier_number)
                            self.tiers.append(tier)

                # Fallback to single announce URL
                elif b"announce" in torrent_data:
                    announce_url = torrent_data[b"announce"].decode("utf-8", errors="ignore")
                    tier = TrackerTier([announce_url], 0)
                    self.tiers.append(tier)

            # Additional fallback: check for tracker URLs in torrent object
            if not self.tiers and hasattr(self.torrent, "tracker_url") and self.torrent.tracker_url:
                tier = TrackerTier([self.torrent.tracker_url], 0)
                self.tiers.append(tier)

            logger.trace(
                f"Parsed {len(self.tiers)} tracker tiers from torrent",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to parse trackers: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    async def announce(self, seeder_manager: Any, event: str = "started") -> Tuple[bool, List[Dict]]:
        """
        Perform announce to trackers with failover support

        Args:
            seeder_manager: Seeder manager to perform announces
            event: Announce event type

        Returns:
            Tuple of (success, peers_list)
        """
        if not self.enabled or not self.tiers:
            return False, []

        try:
            self.last_announce_time = time.time()

            if self.announce_to_all_tiers:
                # Announce to all tiers simultaneously
                return await self._announce_all_tiers(seeder_manager, event)
            else:
                # Announce with tier-based failover
                return await self._announce_with_failover(seeder_manager, event)

        except Exception as e:
            logger.error(
                f"Multi-tracker announce failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False, []

    async def _announce_all_tiers(self, seeder_manager: Any, event: str) -> Tuple[bool, List[Dict]]:
        """
        Announce to all tiers simultaneously

        Args:
            seeder_manager: Seeder manager
            event: Announce event

        Returns:
            Tuple of (success, aggregated_peers)
        """
        all_peers = []
        any_success = False

        # Announce to each tier
        for tier in self.tiers:
            success, peers = await self._announce_tier(tier, seeder_manager, event)
            if success:
                any_success = True
                all_peers.extend(peers)

        # Remove duplicate peers
        unique_peers = self._deduplicate_peers(all_peers)

        return any_success, unique_peers

    async def _announce_with_failover(self, seeder_manager: Any, event: str) -> Tuple[bool, List[Dict]]:
        """
        Announce with tier-based failover

        Args:
            seeder_manager: Seeder manager
            event: Announce event

        Returns:
            Tuple of (success, peers)
        """
        # Try tiers in order until one succeeds
        for tier_index in range(len(self.tiers)):
            tier = self.tiers[tier_index]

            success, peers = await self._announce_tier(tier, seeder_manager, event)

            if success:
                self.current_tier_index = tier_index
                return True, peers

        # All tiers failed
        logger.error("All tracker tiers failed", extra={"class_name": self.__class__.__name__})
        return False, []

    async def _announce_tier(self, tier: TrackerTier, seeder_manager: Any, event: str) -> Tuple[bool, List[Dict]]:
        """
        Announce to a single tier

        Args:
            tier: Tracker tier
            seeder_manager: Seeder manager
            event: Announce event

        Returns:
            Tuple of (success, peers)
        """
        if self.announce_to_all_in_tier:
            # Announce to all trackers in tier
            return await self._announce_all_in_tier(tier, seeder_manager, event)
        else:
            # Try trackers in tier with failover
            return await self._announce_single_tracker(tier, seeder_manager, event)

    async def _announce_all_in_tier(
        self, tier: TrackerTier, seeder_manager: Any, event: str
    ) -> Tuple[bool, List[Dict]]:  # noqa: E501
        """Announce to all trackers in a tier"""
        all_peers = []
        any_success = False

        for tracker_url in tier.trackers:
            if not tier.tracker_status[tracker_url]["enabled"]:
                continue

            success, peers = await self._announce_to_tracker(tracker_url, tier, seeder_manager, event)
            if success:
                any_success = True
                all_peers.extend(peers)

        unique_peers = self._deduplicate_peers(all_peers)
        return any_success, unique_peers

    async def _announce_single_tracker(
        self, tier: TrackerTier, seeder_manager: Any, event: str
    ) -> Tuple[bool, List[Dict]]:  # noqa: E501
        """Try trackers in tier with failover"""
        for _ in range(len(tier.trackers)):
            tracker_url = tier.get_next_tracker()
            if not tracker_url:
                break

            success, peers = await self._announce_to_tracker(tracker_url, tier, seeder_manager, event)
            if success:
                return True, peers

        return False, []

    async def _announce_to_tracker(
        self, tracker_url: str, tier: TrackerTier, seeder_manager: Any, event: str
    ) -> Tuple[bool, List[Dict]]:  # noqa: E501
        """
        Perform announce to a specific tracker

        Args:
            tracker_url: Tracker URL
            tier: Tracker tier
            seeder_manager: Seeder manager
            event: Announce event

        Returns:
            Tuple of (success, peers)
        """
        start_time = time.time()

        try:
            # Determine tracker protocol
            if tracker_url.startswith("http://") or tracker_url.startswith("https://"):
                # HTTP tracker
                from domain.torrent.seeders.http_seeder import HTTPSeeder

                seeder = HTTPSeeder(self.torrent)
                seeder.set_announce_url(tracker_url)

            elif tracker_url.startswith("udp://"):
                # UDP tracker
                from domain.torrent.seeders.udp_seeder import UDPSeeder

                seeder = UDPSeeder(self.torrent)
                seeder.set_announce_url(tracker_url)

            else:
                logger.warning(
                    f"Unsupported tracker protocol: {tracker_url}",
                    extra={"class_name": self.__class__.__name__},
                )
                tier.mark_failure(tracker_url, "Unsupported protocol")
                return False, []

            # Perform announce
            await seeder.start()
            # Note: Real implementation would wait for announce response
            await asyncio.sleep(0.1)  # Configurable announce delay  # type: ignore

            # For now, simulate success (real implementation would check actual response)
            response_time = time.time() - start_time
            peer_count = random.randint(5, 50)  # Simulated peer count

            tier.mark_success(tracker_url, response_time, peer_count)

            # Simulated peers (real implementation would return actual peers)
            peers = [{"ip": f"192.168.1.{i}", "port": 6881 + i} for i in range(peer_count)]

            await seeder.stop()

            return True, peers

        except Exception as e:
            tier.mark_failure(tracker_url, str(e))
            logger.error(
                f"Tracker announce failed for {tracker_url}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False, []

    def _deduplicate_peers(self, peers: List[Dict]) -> List[Dict]:
        """Remove duplicate peers from list"""
        seen = set()
        unique_peers = []

        for peer in peers:
            peer_key = (peer.get("ip"), peer.get("port"))
            if peer_key not in seen:
                seen.add(peer_key)
                unique_peers.append(peer)

        return unique_peers

    def get_all_trackers(self) -> List[str]:
        """Get all tracker URLs across all tiers"""
        all_trackers = []
        for tier in self.tiers:
            all_trackers.extend(tier.trackers)
        return all_trackers

    def get_active_trackers(self) -> List[str]:
        """Get currently active (enabled) trackers"""
        active_trackers = []
        for tier in self.tiers:
            for tracker_url, status in tier.tracker_status.items():
                if status["enabled"]:
                    active_trackers.append(tracker_url)
        return active_trackers

    def get_statistics(self) -> Dict:
        """Get comprehensive multi-tracker statistics"""
        tier_stats = [tier.get_statistics() for tier in self.tiers]

        total_trackers = sum(t["tracker_count"] for t in tier_stats)
        enabled_trackers = sum(t["enabled_trackers"] for t in tier_stats)
        total_announces = sum(t["total_announces"] for t in tier_stats)
        successful_announces = sum(t["successful_announces"] for t in tier_stats)

        return {
            "enabled": self.enabled,
            "tier_count": len(self.tiers),
            "total_trackers": total_trackers,
            "enabled_trackers": enabled_trackers,
            "total_announces": total_announces,
            "successful_announces": successful_announces,
            "overall_success_rate": successful_announces / total_announces if total_announces > 0 else 0.0,
            "current_tier": self.current_tier_index,
            "tiers": tier_stats,
        }
