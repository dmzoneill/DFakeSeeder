"""
UPnP Port Forwarding Manager.

Manages automatic port forwarding using UPnP/NAT-PMP protocols
for better peer connectivity through NAT routers.
"""

import threading
from typing import Any, Optional

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

# Try to import miniupnpc - it's an optional dependency
try:
    import miniupnpc

    UPNP_AVAILABLE = True
except ImportError:
    UPNP_AVAILABLE = False
    miniupnpc = None


class UPnPManager:
    """
    Manages UPnP/NAT-PMP port forwarding.

    Automatically configures port forwarding on NAT routers when enabled,
    allowing incoming peer connections for better torrent performance.
    """

    def __init__(self) -> None:
        """Initialize the UPnP manager."""
        self.settings = AppSettings.get_instance()
        self.upnp: Optional[Any] = None
        self.mapped_port: Optional[int] = None
        self.external_ip: Optional[str] = None
        self._lock = threading.Lock()
        self._started = False

        if not UPNP_AVAILABLE:
            logger.warning(
                "miniupnpc not installed - UPnP port forwarding disabled. " "Install with: pip install miniupnpc",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            logger.trace(
                "UPnPManager initialized",
                extra={"class_name": self.__class__.__name__},
            )

    def start(self) -> bool:
        """
        Initialize UPnP and add port mapping.

        Returns:
            True if port mapping was successful, False otherwise.
        """
        if not UPNP_AVAILABLE:
            return False

        if not self.settings.get("connection.upnp_enabled", True):
            logger.debug(
                "UPnP disabled in settings",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        if self._started:
            return True

        port = self.settings.get("connection.listening_port", 6881)

        try:
            with self._lock:
                self.upnp = miniupnpc.UPnP()
                self.upnp.discoverdelay = 200  # milliseconds

                # Discover UPnP devices
                devices = self.upnp.discover()

                if devices == 0:
                    logger.warning(
                        "No UPnP devices found on the network",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return False

                # Select the Internet Gateway Device
                self.upnp.selectigd()

                # Get external IP address
                self.external_ip = self.upnp.externalipaddress()
                local_ip = self.upnp.lanaddr

                logger.debug(
                    f"UPnP: Found IGD, external IP: {self.external_ip}, " f"local IP: {local_ip}",
                    extra={"class_name": self.__class__.__name__},
                )

                # Add port mapping for TCP
                try:
                    self.upnp.addportmapping(
                        port,  # External port
                        "TCP",  # Protocol
                        local_ip,  # Internal IP
                        port,  # Internal port
                        "DFakeSeeder TCP",  # Description
                        "",  # Remote host (empty = any)
                    )
                    logger.debug(
                        f"UPnP: Added TCP port mapping for port {port}",
                        extra={"class_name": self.__class__.__name__},
                    )
                except Exception as e:
                    logger.warning(
                        f"UPnP: Failed to add TCP port mapping: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

                # Add port mapping for UDP (for DHT)
                try:
                    self.upnp.addportmapping(
                        port,  # External port
                        "UDP",  # Protocol
                        local_ip,  # Internal IP
                        port,  # Internal port
                        "DFakeSeeder UDP",  # Description
                        "",  # Remote host (empty = any)
                    )
                    logger.debug(
                        f"UPnP: Added UDP port mapping for port {port}",
                        extra={"class_name": self.__class__.__name__},
                    )
                except Exception as e:
                    logger.warning(
                        f"UPnP: Failed to add UDP port mapping: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

                self.mapped_port = port
                self._started = True

                logger.info(
                    f"UPnP: Successfully mapped port {port} " f"(external IP: {self.external_ip})",
                    extra={"class_name": self.__class__.__name__},
                )
                return True

        except Exception as e:
            logger.error(
                f"UPnP setup failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def stop(self) -> None:
        """Remove port mapping and cleanup."""
        if not self._started or not self.upnp or not self.mapped_port:
            return

        with self._lock:
            try:
                # Remove TCP port mapping
                self.upnp.deleteportmapping(self.mapped_port, "TCP")
                logger.debug(
                    f"UPnP: Removed TCP port mapping for {self.mapped_port}",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.warning(
                    f"Failed to remove TCP UPnP mapping: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

            try:
                # Remove UDP port mapping
                self.upnp.deleteportmapping(self.mapped_port, "UDP")
                logger.debug(
                    f"UPnP: Removed UDP port mapping for {self.mapped_port}",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.warning(
                    f"Failed to remove UDP UPnP mapping: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

            self.mapped_port = None
            self.external_ip = None
            self._started = False

            logger.info(
                "UPnP: Port mappings removed",
                extra={"class_name": self.__class__.__name__},
            )

    def refresh_mapping(self) -> bool:
        """
        Refresh the port mapping (useful if external IP changed).

        Returns:
            True if refresh was successful.
        """
        self.stop()
        return self.start()

    def get_external_ip(self) -> Optional[str]:
        """
        Get the external IP address from UPnP.

        Returns:
            External IP address string, or None if not available.
        """
        return self.external_ip

    def get_status(self) -> dict:
        """
        Get the current UPnP status.

        Returns:
            Dictionary with UPnP status information.
        """
        return {
            "available": UPNP_AVAILABLE,
            "enabled": self.settings.get("connection.upnp_enabled", True),
            "started": self._started,
            "mapped_port": self.mapped_port,
            "external_ip": self.external_ip,
        }

    def is_available(self) -> bool:
        """Check if UPnP library is available."""
        return UPNP_AVAILABLE

    def is_active(self) -> bool:
        """Check if port mapping is currently active."""
        return self._started and self.mapped_port is not None


# Convenience function to get a singleton instance
_instance: Optional[UPnPManager] = None


def get_upnp_manager() -> UPnPManager:
    """Get or create the UPnPManager singleton instance."""
    global _instance
    if _instance is None:
        _instance = UPnPManager()
    return _instance
