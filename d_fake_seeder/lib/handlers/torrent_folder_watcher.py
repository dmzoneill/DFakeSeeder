"""
Torrent Watch Folder Handler

Monitors a specified folder for new torrent files and automatically adds them to DFakeSeeder.
"""

# fmt: off
import os
import shutil
import time

from d_fake_seeder.lib.logger import logger

try:
    from watchdog.events import FileSystemEventHandler
    from watchdog.observers import Observer

    WATCHDOG_AVAILABLE = True
except ImportError:
    # Fallback if watchdog is not available
    class FileSystemEventHandler:
        pass

    class Observer:
        pass

    WATCHDOG_AVAILABLE = False

# fmt: on


class TorrentFolderWatcher:
    """Watches a folder for new torrent files and triggers callbacks when found"""

    def __init__(self, model, settings, global_peer_manager=None):
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
        self.observer = None
        self.event_handler = None
        self.watch_path = None
        self.is_running = False

        logger.debug(
            "TorrentFolderWatcher initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def start(self):
        """Start watching the configured folder"""
        if not WATCHDOG_AVAILABLE:
            logger.warning(
                "Watchdog library not available - watch folder feature disabled",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        # Get watch folder configuration
        watch_config = getattr(self.settings, "watch_folder", {})
        enabled = watch_config.get("enabled", False)
        watch_path = watch_config.get("path", "")

        if not enabled:
            logger.debug(
                "Watch folder is disabled in settings",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        if not watch_path:
            logger.warning(
                "Watch folder enabled but no path configured",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        # Expand path and validate
        self.watch_path = os.path.expanduser(watch_path)

        if not os.path.exists(self.watch_path):
            logger.warning(
                f"Watch folder path does not exist: {self.watch_path}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        if not os.path.isdir(self.watch_path):
            logger.warning(
                f"Watch folder path is not a directory: {self.watch_path}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            # Create event handler
            self.event_handler = TorrentFileEventHandler(self.model, watch_config, self.global_peer_manager)

            # Create and start observer
            self.observer = Observer()
            self.observer.schedule(self.event_handler, self.watch_path, recursive=False)
            self.observer.start()
            self.is_running = True

            logger.debug(
                f"Started watching folder for torrents: {self.watch_path}",
                extra={"class_name": self.__class__.__name__},
            )

            # Scan existing files in folder
            self._scan_existing_files()

            return True

        except Exception as e:
            logger.error(
                f"Failed to start watch folder: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def stop(self):
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
            except Exception as e:
                logger.error(
                    f"Error stopping watch folder: {e}",
                    extra={"class_name": self.__class__.__name__},
                    exc_info=True,
                )

    def _scan_existing_files(self):
        """Scan for existing torrent files in the watch folder"""
        if not self.watch_path or not os.path.exists(self.watch_path):
            return

        try:
            logger.debug(
                f"Scanning watch folder for existing torrents: {self.watch_path}",
                extra={"class_name": self.__class__.__name__},
            )

            for filename in os.listdir(self.watch_path):
                if filename.lower().endswith(".torrent"):
                    torrent_path = os.path.join(self.watch_path, filename)
                    if os.path.isfile(torrent_path):
                        self.event_handler.process_torrent_file(torrent_path)

        except Exception as e:
            logger.error(
                f"Error scanning existing files: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )


class TorrentFileEventHandler(FileSystemEventHandler):
    """Handles file system events for torrent files"""

    def __init__(self, model, watch_config, global_peer_manager=None):
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
        self.processed_files = set()  # Track processed files to avoid duplicates
        self.last_process_time = {}  # Track when files were last processed

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        if event.src_path.lower().endswith(".torrent"):
            # Small delay to ensure file is fully written
            time.sleep(0.5)
            self.process_torrent_file(event.src_path)

    def on_moved(self, event):
        """Handle file move events (e.g., file moved into watch folder)"""
        if event.is_directory:
            return

        if event.dest_path.lower().endswith(".torrent"):
            # Small delay to ensure file is fully written
            time.sleep(0.5)
            self.process_torrent_file(event.dest_path)

    def process_torrent_file(self, file_path):
        """
        Process a torrent file by copying it to the config directory

        Args:
            file_path: Path to the torrent file in the watch folder
        """
        try:
            # Avoid processing the same file multiple times in quick succession
            current_time = time.time()
            if file_path in self.last_process_time:
                if current_time - self.last_process_time[file_path] < 2.0:
                    logger.debug(
                        f"Skipping recently processed file: {file_path}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return

            self.last_process_time[file_path] = current_time

            # Verify file still exists and is readable
            if not os.path.exists(file_path):
                logger.debug(
                    f"Torrent file no longer exists: {file_path}",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            if not os.access(file_path, os.R_OK):
                logger.warning(
                    f"Cannot read torrent file: {file_path}",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            # Get filename and check if already exists in config directory
            filename = os.path.basename(file_path)
            torrents_path = os.path.expanduser("~/.config/dfakeseeder/torrents")
            destination_path = os.path.join(torrents_path, filename)

            # Check if torrent already exists in config directory
            if os.path.exists(destination_path):
                logger.debug(
                    f"Torrent already exists in config directory: {filename}",
                    extra={"class_name": self.__class__.__name__},
                )
                # Still delete from watch folder if configured
                if self.watch_config.get("delete_added_torrents", False):
                    try:
                        os.remove(file_path)
                        logger.info(
                            f"Deleted duplicate torrent from watch folder: {filename}",
                            extra={"class_name": self.__class__.__name__},
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to delete torrent file {filename}: {e}",
                            extra={"class_name": self.__class__.__name__},
                        )
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
            if self.global_peer_manager:
                # Get the newly added torrent from the model
                torrents = self.model.get_torrents()
                if torrents:
                    new_torrent = torrents[-1]  # Last added torrent
                    self.global_peer_manager.add_torrent(new_torrent)
                    logger.debug(
                        f"Added torrent to global peer manager: {filename}",
                        extra={"class_name": self.__class__.__name__},
                    )

            logger.info(
                f"Successfully added torrent from watch folder: {filename}",
                extra={"class_name": self.__class__.__name__},
            )

            # Handle source file deletion if configured
            if self.watch_config.get("delete_added_torrents", False):
                try:
                    os.remove(file_path)
                    logger.info(
                        f"Deleted source torrent file from watch folder: {filename}",
                        extra={"class_name": self.__class__.__name__},
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to delete source torrent file {filename}: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

        except Exception as e:
            logger.error(
                f"Error processing torrent file {file_path}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
