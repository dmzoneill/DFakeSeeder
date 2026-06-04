"""
File Modified Event Handler.

This module provides a watchdog-based file system event handler that monitors
settings file changes and triggers reload operations when modifications are detected.
"""

from typing import Any

try:
    # fmt: off
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    # fmt: on
    # Fallback if watchdog is not available
    class FileSystemEventHandler:  # type: ignore[no-redef]  # pylint: disable=too-few-public-methods
        """Stub fallback when watchdog is not available."""

    WATCHDOG_AVAILABLE = False


class FileModifiedEventHandler(FileSystemEventHandler):  # pylint: disable=too-few-public-methods
    """Handler that triggers settings reload when config file is modified."""

    def __init__(self, settings_instance: Any) -> None:
        self.settings = settings_instance

    def on_modified(self, event: Any) -> None:
        """Reload settings when config file is modified."""
        if event.src_path == self.settings._file_path:  # pylint: disable=protected-access
            self.settings.load_settings()
