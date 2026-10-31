"""
Torrent Watch Folder Handler

Monitors a specified folder for new torrent files and automatically adds them to DFakeSeeder.
"""

import os
import shutil
import time
from typing import Any

from d_fake_seeder.lib.gi_base import GLib
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.xdg_paths import get_config_dir
from d_fake_seeder.view import View

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    # Fallback no-op implementations when watchdog is not installed. They mirror
    # the subset of the watchdog interface this module touches so nothing breaks
    # if they are ever reached (the watch-folder feature stays disabled).
    class FileSystemEventHandler:  # type: ignore[no-redef]
        """Stub fallback for watchdog's FileSystemEventHandler."""

        def dispatch(self, _event: Any) -> None:
            """No-op event dispatch used when watchdog is unavailable."""

        def on_any_event(self, _event: Any) -> None:
            """No-op catch-all event hook used when watchdog is unavailable."""

    class Observer:  # type: ignore[no-redef]
        """Stub fallback for watchdog's Observer."""

        def schedule(self, *args: Any, **kwargs: Any) -> None:
            """No-op schedule used when watchdog is unavailable."""

        def start(self) -> None:
            """No-op start used when watchdog is unavailable."""

        def stop(self) -> None:
            """No-op stop used when watchdog is unavailable."""

        def join(self, *args: Any, **kwargs: Any) -> None:
            """No-op join used when watchdog is unavailable."""

    WATCHDOG_AVAILABLE = False


class TorrentFolderWatcher:
    """Watches a folder for new torrent files and triggers callbacks when found"""

    def __init__(self, model: Any, settings: Any, global_peer_manager: Any = None) -> None:
        """
        Initialize torrent folder watcher

        Args:
            model: The application model instance for adding torrents
            settings: AppSettings instance for configuration
            global_peer_manager: Optional GlobalPeerManager for adding torrents to P2P network
        """
        self.model = model
        self.settings = settings
        self.global_peer_manager = global_peer_manager
        self.observer: Any = None
        self.event_handler: Any = None
        self.watch_path: str | None = None
        self.is_running = False

        logger.trace(
            "TorrentFolderWatcher initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _resolve_watch_path(self, watch_config: Any) -> str | None:
        """
        Validate the configured watch folder and return its expanded path.

        Args:
            watch_config: The ``watch_folder`` settings dict.

        Returns:
            The validated, expanded folder path, or ``None`` when the feature is
            disabled or misconfigured (reason is logged).
        """
        if not watch_config.get("enabled", False):
            logger.trace(
                "Watch folder is disabled in settings",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        watch_path = watch_config.get("path", "")
        if not watch_path:
            logger.warning(
                "Watch folder enabled but no path configured",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        expanded: str = os.path.expanduser(watch_path)
        if not os.path.exists(expanded):
            logger.warning(
                f"Watch folder path does not exist: {expanded}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        if not os.path.isdir(expanded):
            logger.warning(
                f"Watch folder path is not a directory: {expanded}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        return expanded

    def start(self) -> Any:
        """Start watching the configured folder"""
        if not WATCHDOG_AVAILABLE:
            logger.warning(
                "Watchdog library not available - watch folder feature disabled",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        watch_config = getattr(self.settings, "watch_folder", {})
        watch_path = self._resolve_watch_path(watch_config)
        if watch_path is None:
            return False
        self.watch_path = watch_path

        try:
            self.event_handler = TorrentFileEventHandler(self.model, watch_config, self.global_peer_manager)

            self.observer = Observer()
            self.observer.schedule(self.event_handler, self.watch_path, recursive=False)
            self.observer.start()
            self.is_running = True

            logger.trace(
                f"Started watching folder for torrents: {self.watch_path}",
                extra={"class_name": self.__class__.__name__},
            )

            self._scan_existing_files()

            return True

        except (OSError, RuntimeError, AttributeError, TypeError, ValueError) as e:
            logger.error(
                f"Failed to start watch folder: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def stop(self) -> Any:
        """Stop watching the folder"""
        if self.observer and self.is_running:
            try:
                self.observer.stop()
                self.observer.join(timeout=5.0)
                self.is_running = False
                logger.info(
                    "Stopped watching torrent folder",
                    extra={"class_name": self.__class__.__name__},
                )
            except (OSError, RuntimeError, AttributeError) as e:
                logger.error(
                    f"Error stopping watch folder: {e}",
                    extra={"class_name": self.__class__.__name__},
                    exc_info=True,
                )

    def _scan_existing_files(self) -> Any:
        """Scan for existing torrent files in the watch folder"""
        if not self.watch_path or not os.path.exists(self.watch_path):
            return

        try:
            logger.trace(
                f"Scanning watch folder for existing torrents: {self.watch_path}",
                extra={"class_name": self.__class__.__name__},
            )

            for filename in os.listdir(self.watch_path):
                if filename.lower().endswith(".torrent"):
                    torrent_path = os.path.join(self.watch_path, filename)
                    if os.path.isfile(torrent_path):
                        self.event_handler.process_torrent_file(torrent_path)

        except (OSError, AttributeError, TypeError) as e:
            logger.error(
                f"Error scanning existing files: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )


class TorrentFileEventHandler(FileSystemEventHandler):
    """Handles file system events for torrent files"""

    def __init__(self, model: Any, watch_config: Any, global_peer_manager: Any = None) -> None:
        """
        Initialize event handler

        Args:
            model: The application model instance
            watch_config: Watch folder configuration dict
            global_peer_manager: Optional GlobalPeerManager for P2P network integration
        """
        super().__init__()
        self.model = model
        self.watch_config = watch_config
        self.global_peer_manager = global_peer_manager
        self.processed_files: set[Any] = set()  # Track processed files to avoid duplicates
        self.last_process_time: dict[str, Any] = {}  # Track when files were last processed

    def on_created(self, event: Any) -> None:
        """Handle file creation events"""
        if event.is_directory:
            return

        if event.src_path.lower().endswith(".torrent"):
            # Small delay to ensure file is fully written
            time.sleep(0.5)
            # Marshal to GTK main thread for safe model access
            GLib.idle_add(self._deferred_process, event.src_path)

    def on_moved(self, event: Any) -> None:
        """Handle file move events (e.g., file moved into watch folder)"""
        if event.is_directory:
            return

        if event.dest_path.lower().endswith(".torrent"):
            # Small delay to ensure file is fully written
            time.sleep(0.5)
            # Marshal to GTK main thread for safe model access
            GLib.idle_add(self._deferred_process, event.dest_path)

    def _deferred_process(self, file_path: Any) -> bool:
        """GLib callback to process torrent file on main thread"""
        self.process_torrent_file(file_path)
        return False  # Don't repeat

    def _is_recently_processed(self, file_path: Any) -> bool:
        """Return True when the file was processed within the last 2 seconds."""
        last = self.last_process_time.get(file_path)
        if last is not None and time.time() - last < 2.0:
            logger.trace(
                f"Skipping recently processed file: {file_path}",
                extra={"class_name": self.__class__.__name__},
            )
            return True
        return False

    def _is_readable_torrent(self, file_path: Any) -> bool:
        """Return True when the torrent file still exists and is readable."""
        if not os.path.exists(file_path):
            logger.trace(
                f"Torrent file no longer exists: {file_path}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        if not os.access(file_path, os.R_OK):
            logger.warning(
                f"Cannot read torrent file: {file_path}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        return True

    def _maybe_delete_watch_file(self, file_path: Any, filename: str, duplicate: bool) -> None:
        """Delete the source file from the watch folder when configured to do so."""
        if not self.watch_config.get("delete_added_torrents", False):
            return

        deleted_msg = (
            f"Deleted duplicate torrent from watch folder: {filename}"
            if duplicate
            else f"Deleted source torrent file from watch folder: {filename}"
        )
        failed_msg = (
            f"Failed to delete torrent file {filename}"
            if duplicate
            else f"Failed to delete source torrent file {filename}"
        )
        try:
            os.remove(file_path)
            logger.info(deleted_msg, extra={"class_name": self.__class__.__name__})
        except OSError as e:
            logger.warning(f"{failed_msg}: {e}", extra={"class_name": self.__class__.__name__})

    def _register_with_peer_manager(self, filename: str) -> None:
        """Add the most recently added torrent to the global peer manager, if present."""
        if not self.global_peer_manager:
            return

        torrents = self.model.get_torrents()
        if not torrents:
            return

        new_torrent = torrents[-1]  # Last added torrent
        self.global_peer_manager.add_torrent(new_torrent)
        logger.trace(
            f"Added torrent to global peer manager: {filename}",
            extra={"class_name": self.__class__.__name__},
        )

    def _notify_added(self, filename: str) -> None:
        """Show a transient notification that a torrent was auto-added."""
        if not View.instance:
            return

        # Truncate long filenames for display
        display_name = filename.removesuffix(".torrent")
        if len(display_name) > 40:
            display_name = display_name[:37] + "..."
        View.instance.notify(
            f"Auto-added: {display_name}",
            notification_type="success",
            timeout_ms=2500,
            translate=False,  # Contains dynamic filename
        )

    def process_torrent_file(self, file_path: Any) -> None:
        """
        Process a torrent file by copying it to the config directory

        Args:
            file_path: Path to the torrent file in the watch folder
        """
        try:
            # Avoid processing the same file multiple times in quick succession
            if self._is_recently_processed(file_path):
                return
            self.last_process_time[file_path] = time.time()

            if not self._is_readable_torrent(file_path):
                return

            # Get filename and check if already exists in config directory
            filename = os.path.basename(file_path)
            torrents_path = os.path.join(get_config_dir(), "torrents")
            destination_path = os.path.join(torrents_path, filename)

            # Check if torrent already exists in config directory
            if os.path.exists(destination_path):
                logger.trace(
                    f"Torrent already exists in config directory: {filename}",
                    extra={"class_name": self.__class__.__name__},
                )
                # Still delete from watch folder if configured
                self._maybe_delete_watch_file(file_path, filename, duplicate=True)
                return

            # Ensure torrents directory exists
            os.makedirs(torrents_path, exist_ok=True)

            # Copy torrent to config directory (same as toolbar.py does)
            logger.info(
                f"Copying torrent from watch folder to config directory: {filename}",
                extra={"class_name": self.__class__.__name__},
            )

            shutil.copy(file_path, torrents_path)

            # Add torrent to model using the copied file path
            self.model.add_torrent(destination_path)

            # Add to global peer manager if available (same as controller.run() does)
            self._register_with_peer_manager(filename)

            logger.info(
                f"Successfully added torrent from watch folder: {filename}",
                extra={"class_name": self.__class__.__name__},
            )

            # Notify user of auto-added torrent
            self._notify_added(filename)

            # Handle source file deletion if configured
            self._maybe_delete_watch_file(file_path, filename, duplicate=False)

        except (OSError, shutil.Error, AttributeError, TypeError, ValueError, KeyError, RuntimeError) as e:
            logger.error(
                f"Error processing torrent file {file_path}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
