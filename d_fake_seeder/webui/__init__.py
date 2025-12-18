"""
Web UI Module for DFakeSeeder.

Provides a web-based interface for remote management of the application.
"""

from .server import WebUIServer, get_webui_server

__all__ = ["WebUIServer", "get_webui_server"]
