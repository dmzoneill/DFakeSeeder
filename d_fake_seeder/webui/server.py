"""
Web UI Server for DFakeSeeder.

Provides an async HTTP server for web-based remote management.
"""

import asyncio
import ssl
from pathlib import Path
from typing import Any, Optional

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

# Try to import aiohttp - it's an optional dependency
try:
    from aiohttp import web

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None

from .auth import create_auth_middleware, create_security_middleware
from .routes import setup_routes


class WebUIServer:
    """
    Async HTTP server for web-based management.

    Provides a REST API and simple web dashboard for remote
    management of DFakeSeeder.
    """

    def __init__(self, model: Any = None) -> None:
        """
        Initialize the Web UI server.

        Args:
            model: The application model containing torrents.
        """
        self.model = model
        self.settings = AppSettings.get_instance()
        self.app: Optional[Any] = None
        self.runner: Optional[Any] = None
        self.site: Optional[Any] = None
        self._started = False
        self._task: Optional[asyncio.Task] = None

        if not AIOHTTP_AVAILABLE:
            logger.warning(
                "aiohttp not installed - Web UI disabled. " "Install with: pip install aiohttp",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            logger.trace(
                "WebUIServer initialized",
                extra={"class_name": self.__class__.__name__},
            )

    async def start(self) -> bool:
        """
        Start the Web UI server if enabled.

        Returns:
            True if server started successfully, False otherwise.
        """
        if not AIOHTTP_AVAILABLE:
            logger.warning(
                "Cannot start Web UI - aiohttp not installed",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        if not self.settings.get("webui.enabled", False):
            logger.debug(
                "Web UI disabled in settings",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        if self._started:
            return True

        try:
            port = self.settings.get("webui.port", 8080)
            interface = self.settings.get("webui.interface", "127.0.0.1")
            localhost_only = self.settings.get("webui.localhost_only", True)

            # Determine bind address
            bind_addr = "127.0.0.1" if localhost_only else interface

            # Build middleware list
            middlewares = []

            # Add security headers middleware
            if self.settings.get("webui.secure_headers", True):
                middlewares.append(create_security_middleware(self.settings))

            # Add authentication middleware
            if self.settings.get("webui.auth_enabled", True):
                middlewares.append(create_auth_middleware(self.settings))

            # Create the application
            self.app = web.Application(middlewares=middlewares)
            self.app["model"] = self.model
            self.app["settings"] = self.settings

            # Set up routes
            setup_routes(self.app)

            # SSL context if HTTPS enabled
            ssl_ctx = None
            if self.settings.get("webui.https_enabled", False):
                ssl_ctx = self._create_ssl_context()

            # Start the server
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.site = web.TCPSite(self.runner, bind_addr, port, ssl_context=ssl_ctx)
            await self.site.start()

            self._started = True
            protocol = "https" if ssl_ctx else "http"

            logger.info(
                f"Web UI started on {protocol}://{bind_addr}:{port}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to start Web UI: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    async def stop(self) -> None:
        """Stop the Web UI server."""
        if not self._started:
            return

        try:
            if self.runner:
                await self.runner.cleanup()
                self.runner = None
                self.site = None

            self._started = False

            logger.info(
                "Web UI stopped",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Error stopping Web UI: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _create_ssl_context(self) -> Optional[ssl.SSLContext]:
        """
        Create SSL context for HTTPS.

        Returns:
            SSL context or None if certificates not found.
        """
        try:
            # Look for certificates in config directory
            config_dir = Path.home() / ".config" / "dfakeseeder"
            cert_file = config_dir / "cert.pem"
            key_file = config_dir / "key.pem"

            if not cert_file.exists() or not key_file.exists():
                logger.warning(
                    f"SSL certificates not found at {config_dir}. "
                    "Generate with: openssl req -x509 -newkey rsa:4096 "
                    "-keyout key.pem -out cert.pem -days 365 -nodes",
                    extra={"class_name": self.__class__.__name__},
                )
                return None

            ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ssl_ctx.load_cert_chain(str(cert_file), str(key_file))

            logger.debug(
                "SSL context created for HTTPS",
                extra={"class_name": self.__class__.__name__},
            )
            return ssl_ctx

        except Exception as e:
            logger.error(
                f"Failed to create SSL context: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._started

    def is_available(self) -> bool:
        """Check if aiohttp is available."""
        return AIOHTTP_AVAILABLE

    def get_status(self) -> dict:
        """
        Get the current server status.

        Returns:
            Dictionary with server status information.
        """
        return {
            "available": AIOHTTP_AVAILABLE,
            "enabled": self.settings.get("webui.enabled", False),
            "running": self._started,
            "port": self.settings.get("webui.port", 8080),
            "localhost_only": self.settings.get("webui.localhost_only", True),
            "https": self.settings.get("webui.https_enabled", False),
            "auth": self.settings.get("webui.auth_enabled", True),
        }

    def set_model(self, model: Any) -> None:
        """
        Set the application model.

        Args:
            model: The application model containing torrents.
        """
        self.model = model
        if self.app:
            self.app["model"] = model


# Convenience function to get a singleton instance
_instance: Optional[WebUIServer] = None


def get_webui_server(model: Any = None) -> WebUIServer:
    """Get or create the WebUIServer singleton instance."""
    global _instance
    if _instance is None:
        _instance = WebUIServer(model)
    elif model is not None:
        _instance.set_model(model)
    return _instance
