"""Network utilities for socket binding and interface handling."""

from typing import Optional, Tuple

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger


def get_bind_address() -> str:
    """Get the bind address based on network_interface setting.

    Returns:
        The IP address to bind sockets to. Returns "0.0.0.0" if no specific
        interface is configured (binds to all interfaces).
    """
    settings = AppSettings.get_instance()
    interface = settings.get("performance.network_interface", "")

    if interface and interface != "0.0.0.0" and interface != "any":
        logger.debug(f"Using network interface: {interface}", "Network")
        return str(interface)

    return "0.0.0.0"


def get_bind_tuple(port: int) -> Tuple[str, int]:
    """Get the (address, port) tuple for socket binding.

    Args:
        port: The port number to bind to.

    Returns:
        Tuple of (bind_address, port) for socket.bind()
    """
    return (get_bind_address(), port)


def get_local_ip() -> Optional[str]:
    """Get the local IP address for the configured network interface.

    Returns:
        The local IP address, or None if it cannot be determined.
    """
    import socket

    bind_addr = get_bind_address()

    if bind_addr != "0.0.0.0":
        # Specific interface configured
        return bind_addr

    # Try to get the default outgoing IP
    try:
        # Create a UDP socket and connect to an external address
        # This doesn't actually send data, but gives us the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            s.connect(("8.8.8.8", 80))
            ip: str = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip
    except Exception:
        return None
