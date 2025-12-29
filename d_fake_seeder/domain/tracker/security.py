# fmt: off
# isort: skip_file
"""
Security features for the inbuilt BitTorrent tracker.

Provides IP filtering and rate limiting.
"""

import threading
import time
from collections import defaultdict
from typing import List, Optional, Set

from d_fake_seeder.lib.logger import logger

# fmt: on


class IPFilter:
    """
    IP address filter for the tracker.

    Supports whitelist and blacklist modes.
    """

    def __init__(
        self,
        whitelist: Optional[List[str]] = None,
        blacklist: Optional[List[str]] = None,
    ) -> None:
        """
        Initialize the IP filter.

        Args:
            whitelist: List of allowed IP addresses/ranges.
                       If provided, only these IPs are allowed.
            blacklist: List of blocked IP addresses/ranges.
        """
        self._whitelist: Set[str] = set(whitelist) if whitelist else set()
        self._blacklist: Set[str] = set(blacklist) if blacklist else set()
        self._lock = threading.RLock()

        logger.debug(
            f"IPFilter initialized: whitelist={len(self._whitelist)}, " f"blacklist={len(self._blacklist)}",
            extra={"class_name": self.__class__.__name__},
        )

    def is_allowed(self, ip: str) -> bool:
        """
        Check if an IP address is allowed.

        Args:
            ip: IP address to check

        Returns:
            True if allowed, False if blocked
        """
        with self._lock:
            # Check blacklist first
            if self._is_in_list(ip, self._blacklist):
                return False

            # If whitelist is defined, IP must be in it
            if self._whitelist:
                return self._is_in_list(ip, self._whitelist)

            return True

    def _is_in_list(self, ip: str, ip_list: Set[str]) -> bool:
        """Check if IP is in a list (supports exact match and prefix match)."""
        if ip in ip_list:
            return True

        # Check for CIDR-style ranges (simple prefix match)
        for pattern in ip_list:
            if pattern.endswith(".*"):
                # Simple wildcard: 192.168.*
                prefix = pattern[:-1]  # Remove *
                if ip.startswith(prefix):
                    return True
            elif "/" in pattern:
                # CIDR notation (simplified - just check prefix)
                network = pattern.split("/")[0]
                if ip.startswith(network.rsplit(".", 1)[0]):
                    return True

        return False

    def add_to_whitelist(self, ip: str) -> None:
        """Add an IP to the whitelist."""
        with self._lock:
            self._whitelist.add(ip)

    def add_to_blacklist(self, ip: str) -> None:
        """Add an IP to the blacklist."""
        with self._lock:
            self._blacklist.add(ip)

    def remove_from_whitelist(self, ip: str) -> None:
        """Remove an IP from the whitelist."""
        with self._lock:
            self._whitelist.discard(ip)

    def remove_from_blacklist(self, ip: str) -> None:
        """Remove an IP from the blacklist."""
        with self._lock:
            self._blacklist.discard(ip)


class RateLimiter:
    """
    Rate limiter for the tracker.

    Limits the number of requests per IP per time window.
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        ban_duration_seconds: int = 300,
    ) -> None:
        """
        Initialize the rate limiter.

        Args:
            requests_per_minute: Maximum requests allowed per minute per IP
            ban_duration_seconds: How long to ban IPs that exceed the limit
        """
        self._limit = requests_per_minute
        self._ban_duration = ban_duration_seconds
        self._requests: defaultdict = defaultdict(list)  # ip -> [timestamps]
        self._banned: dict = {}  # ip -> ban_end_time
        self._lock = threading.RLock()

        logger.debug(
            f"RateLimiter initialized: {requests_per_minute}/min, " f"ban={ban_duration_seconds}s",
            extra={"class_name": self.__class__.__name__},
        )

    def is_allowed(self, ip: str) -> bool:
        """
        Check if an IP is allowed to make a request.

        Also records the request if allowed.

        Args:
            ip: IP address to check

        Returns:
            True if allowed, False if rate limited or banned
        """
        now = time.time()

        with self._lock:
            # Check if IP is banned
            if ip in self._banned:
                if now < self._banned[ip]:
                    return False
                del self._banned[ip]

            # Clean old requests
            cutoff = now - 60  # 1 minute window
            self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]

            # Check rate
            if len(self._requests[ip]) >= self._limit:
                # Ban the IP
                self._banned[ip] = now + self._ban_duration
                logger.warning(
                    f"IP {ip} rate limited and banned for {self._ban_duration}s",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Record request
            self._requests[ip].append(now)
            return True

    def get_remaining(self, ip: str) -> int:
        """Get remaining requests for an IP."""
        with self._lock:
            now = time.time()
            cutoff = now - 60
            requests = [t for t in self._requests.get(ip, []) if t > cutoff]
            return max(0, self._limit - len(requests))

    def is_banned(self, ip: str) -> bool:
        """Check if an IP is currently banned."""
        with self._lock:
            if ip in self._banned:
                if time.time() < self._banned[ip]:
                    return True
                del self._banned[ip]
            return False

    def unban(self, ip: str) -> None:
        """Manually unban an IP."""
        with self._lock:
            self._banned.pop(ip, None)

    def cleanup(self) -> None:
        """Clean up expired entries."""
        now = time.time()
        cutoff = now - 60

        with self._lock:
            # Clean expired requests
            for ip in list(self._requests.keys()):
                self._requests[ip] = [t for t in self._requests[ip] if t > cutoff]
                if not self._requests[ip]:
                    del self._requests[ip]

            # Clean expired bans
            for ip in list(self._banned.keys()):
                if now >= self._banned[ip]:
                    del self._banned[ip]


class TrackerSecurity:  # pylint: disable=too-few-public-methods
    """
    Combined security manager for the tracker.

    Integrates IP filtering and rate limiting.
    """

    def __init__(
        self,
        ip_whitelist: Optional[List[str]] = None,
        ip_blacklist: Optional[List[str]] = None,
        rate_limit_per_minute: int = 60,
        ban_duration_seconds: int = 300,
    ) -> None:
        """
        Initialize the security manager.

        Args:
            ip_whitelist: List of allowed IP addresses
            ip_blacklist: List of blocked IP addresses
            rate_limit_per_minute: Max requests per minute per IP
            ban_duration_seconds: Ban duration when rate limit exceeded
        """
        self.ip_filter = IPFilter(
            whitelist=ip_whitelist,
            blacklist=ip_blacklist,
        )
        self.rate_limiter = RateLimiter(
            requests_per_minute=rate_limit_per_minute,
            ban_duration_seconds=ban_duration_seconds,
        )

        logger.debug(
            "TrackerSecurity initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def check_request(self, ip: str) -> tuple:
        """
        Check if a request from an IP is allowed.

        Args:
            ip: IP address of the requester

        Returns:
            Tuple of (allowed: bool, reason: str or None)
        """
        # Check IP filter first
        if not self.ip_filter.is_allowed(ip):
            return False, "IP blocked"

        # Check rate limit
        if not self.rate_limiter.is_allowed(ip):
            if self.rate_limiter.is_banned(ip):
                return False, "IP temporarily banned"
            return False, "Rate limit exceeded"

        return True, None
