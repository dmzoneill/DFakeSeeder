# fmt: off
# isort: skip_file
from typing import List,  Any
import random
import threading

import gi

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.file import File
from d_fake_seeder.domain.torrent.model.attributes import Attributes
from d_fake_seeder.domain.torrent.model.tracker import Tracker
from d_fake_seeder.domain.torrent.seeder import Seeder
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import CalculationConstants, TimeoutConstants
from d_fake_seeder.view import View

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import GLib  # noqa: E402
from gi.repository import GObject  # noqa: E402

# fmt: on


# Torrent class definition
class Torrent(GObject.GObject):
    # Define custom signal 'attribute-changed'
    # which is emitted when torrent data is modified
    __gsignals__ = {
        "attribute-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (object, object),
        )
    }

    def __init__(self, filepath: Any) -> None:
        super().__init__()
        logger.trace("instantiate", extra={"class_name": self.__class__.__name__})

        self.torrent_attributes = Attributes()

        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        # Get UI settings for configurable sleep intervals and random factors
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.seeder_retry_interval = ui_settings.get("error_sleep_interval_seconds", 5.0) / ui_settings.get(
            "seeder_retry_interval_divisor", 2
        )
        self.worker_sleep_interval = (
            ui_settings.get("async_sleep_interval_seconds", 1.0) / 2
        )  # Half of the async sleep interval
        self.seeder_retry_count = ui_settings.get("seeder_retry_count", 5)
        self.speed_variation_min = ui_settings.get("speed_variation_min", 0.2)
        self.speed_variation_max = ui_settings.get("speed_variation_max", 0.8)
        self.peer_idle_probability = ui_settings.get("peer_idle_probability", 0.3)
        self.speed_calculation_multiplier = ui_settings.get("speed_calculation_multiplier", 1000)

        self.file_path = filepath

        # Track additional background threads for cleanup
        self.tracker_update_threads: List[Any] = []  # Track force tracker update threads
        self.is_stopping = False  # Flag to prevent new threads during shutdown

        # Coalescing flag to prevent duplicate UI update callbacks
        self._ui_update_pending = False

        # DEBUG: Check if torrent exists in settings
        torrent_exists = self.file_path in self.settings.torrents
        logger.trace(
            f"🔍 TORRENT INIT: file_path='{self.file_path}', exists_in_settings={torrent_exists}",
            extra={"class_name": self.__class__.__name__},
        )
        if not torrent_exists and hasattr(self.settings, "torrents"):
            logger.trace(
                f"🔍 Number of torrents in settings: {len(self.settings.torrents)}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.trace(
                f"🔍 First 3 keys in settings.torrents: {list(self.settings.torrents.keys())[:3]}",
                extra={"class_name": self.__class__.__name__},
            )

        if self.file_path not in self.settings.torrents:
            logger.warning(
                "⚠️  CREATING NEW TORRENT ENTRY (this will reset stats to 0!)",
                extra={"class_name": self.__class__.__name__},
            )

            # Build new torrent data dictionary
            new_torrent_data = {
                "active": True,
                "id": (len(self.settings.torrents) + 1 if len(self.settings.torrents) > 0 else 1),
                "name": "",
                "upload_speed": self.settings.upload_speed,
                "download_speed": self.settings.download_speed,
                "progress": 0.0,
                "announce_interval": self.settings.announce_interval,
                "next_update": self.settings.announce_interval,
                "uploading": False,
                "total_uploaded": 0,
                "total_downloaded": 0,
                "session_uploaded": 0,
                "session_downloaded": 0,
                "seeders": 0,
                "leechers": 0,
                "threshold": self.settings.threshold,
                "filepath": self.file_path,
                "small_torrent_limit": 0,
                "total_size": 0,
                # New attributes for enhanced context menu functionality
                "label": "",
                "priority": "normal",
                "upload_limit": 0,
                "download_limit": 0,
                "super_seeding": False,
                "sequential_download": False,
                "force_start": False,
            }

            # Add to transient storage (will be saved during shutdown via save_quit())
            self.settings.torrents[self.file_path] = new_torrent_data

            logger.info(
                f"New torrent added to transient storage: {self.file_path}",
                extra={"class_name": self.__class__.__name__},
            )

        ATTRIBUTES = Attributes
        attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]

        self.torrent_file = File(self.file_path)
        self.seeder = Seeder(self.torrent_file)

        # Load attributes from settings with fallback to default values
        logger.trace(
            f"📥 LOADING {len(attributes)} attributes from settings for torrent",
            extra={"class_name": self.__class__.__name__},
        )
        for attr in attributes:
            # Use .get() with default values for backward compatibility
            default_value = None
            if attr == "label":
                default_value = ""
            elif attr == "priority":
                default_value = "normal"
            elif attr in ("upload_limit", "download_limit"):
                default_value = 0  # type: ignore[assignment]
            elif attr in ("super_seeding", "sequential_download", "force_start"):
                default_value = False  # type: ignore[assignment]

            # Get value from settings, or use default if key doesn't exist
            value = self.settings.torrents[self.file_path].get(attr, default_value)
            if value is not None:
                setattr(self.torrent_attributes, attr, value)
                # Debug log for critical stats
                if attr in (
                    "progress",
                    "total_uploaded",
                    "total_downloaded",
                    "session_uploaded",
                    "session_downloaded",
                ):
                    logger.trace(
                        f"  ✅ Loaded {attr} = {value}",
                        extra={"class_name": self.__class__.__name__},
                    )

        # Don't reset session stats - they are loaded from settings above
        # Session stats should persist across application restarts to maintain accurate totals

        # Start the thread to update the name
        self.torrent_worker_stop_event = threading.Event()
        self.torrent_worker = threading.Thread(
            target=self.update_torrent_worker,
            name=f"TorrentWorker-{getattr(self, 'name', 'Unknown')}",
            daemon=True,  # PyPy optimization: daemon threads for better cleanup
        )
        self.torrent_worker.start()

        # Start peers worker thread
        self.peers_worker_stop_event = threading.Event()
        self.peers_worker = threading.Thread(
            target=self.peers_worker_update,
            name=f"PeersWorker-{getattr(self, 'name', 'Unknown')}",
            daemon=True,  # PyPy optimization: daemon threads for better cleanup
        )
        self.peers_worker.start()

    def peers_worker_update(self) -> Any:
        logger.trace(
            "Peers worker",
            extra={"class_name": self.__class__.__name__},
        )

        try:
            fetched = False
            count = self.seeder_retry_count

            while fetched is False and count != 0:
                # Check for shutdown request before each iteration
                if self.peers_worker_stop_event.is_set():
                    logger.trace(
                        f"🛑 PEERS WORKER SHUTDOWN: {self.name} - stop event received",  # type: ignore[has-type]
                        extra={"class_name": self.__class__.__name__},
                    )
                    break

                logger.trace(
                    "Requesting seeder information",
                    extra={"class_name": self.__class__.__name__},
                )
                fetched = self.seeder.load_peers()  # type: ignore[func-returns-value]
                if fetched is False:
                    logger.trace(
                        f"Seeder failed to load peers, retrying in {TimeoutConstants.TORRENT_PEER_RETRY} seconds",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Use Event.wait() instead of time.sleep() for instant shutdown response
                    if self.peers_worker_stop_event.wait(timeout=int(self.seeder_retry_interval)):
                        logger.trace(
                            f"🛑 PEERS WORKER SHUTDOWN: {self.name} - stop event received during retry sleep",  # type: ignore[has-type]  # noqa: E501
                            extra={"class_name": self.__class__.__name__},
                        )
                        break
                    count -= 1
                    if count == 0:
                        self.active = False

        except Exception as e:
            logger.error(
                f"Error in seeder_request_worker: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def update_torrent_worker(self) -> None:
        logger.trace(
            f"🔄 TORRENT UPDATE WORKER STARTED for {self.name}",  # type: ignore[has-type]
            extra={"class_name": self.__class__.__name__},
        )

        try:
            ticker = 0.0

            # Use Event.wait() instead of time.sleep() for instant shutdown response
            while not self.torrent_worker_stop_event.wait(timeout=self.worker_sleep_interval):
                logger.trace(
                    f"🔄 WORKER LOOP: {self.name} ticker={ticker:.2f}, tickspeed={self.settings.tickspeed}, "  # type: ignore[has-type]  # noqa: E501
                    f"active={self.active}",
                    extra={"class_name": self.__class__.__name__},
                )
                if ticker >= self.settings.tickspeed and self.active:
                    # Coalesce updates: skip if an update is already pending
                    if not self._ui_update_pending:
                        self._ui_update_pending = True
                        logger.trace(
                            f"🔄 WORKER: Adding update callback to UI thread for {self.name} "  # type: ignore[has-type]
                            f"(ticker={ticker}, tickspeed={self.settings.tickspeed})",
                            extra={"class_name": self.__class__.__name__},
                        )
                        GLib.idle_add(self.update_torrent_callback)
                if ticker >= self.settings.tickspeed:
                    ticker = 0.0
                ticker += self.worker_sleep_interval

        except Exception as e:
            logger.error(
                f"Error in update_torrent_worker: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def update_torrent_callback(self) -> None:
        # Clear pending flag - this callback is now executing
        self._ui_update_pending = False

        logger.trace(
            f"📊 TORRENT UPDATE CALLBACK STARTED for {self.name} - updating values",  # type: ignore[has-type]
            extra={"class_name": self.__class__.__name__},
        )

        update_internal = int(self.settings.tickspeed)

        if self.name != self.torrent_file.name:  # type: ignore[has-type]
            self.name = self.torrent_file.name

        if self.total_size != self.torrent_file.total_size:  # type: ignore[has-type]
            self.total_size = self.torrent_file.total_size

        if self.seeder.ready:  # type: ignore[truthy-function]
            if self.seeders != self.seeder.seeders:  # type: ignore[has-type]
                self.seeders = self.seeder.seeders

            if self.leechers != self.seeder.leechers:  # type: ignore[has-type]
                self.leechers = self.seeder.leechers

        # Get torrent-specific threshold, or fall back to global threshold
        threshold = self.settings.torrents[self.file_path].get("threshold", self.settings.threshold)

        if self.threshold != threshold:  # type: ignore[has-type]
            self.threshold = threshold

        if self.progress >= (threshold / 100) and not self.uploading:  # type: ignore[has-type]
            if self.uploading is False:  # type: ignore[has-type]
                self.uploading = True

        if self.uploading:
            upload_factor = int(
                random.uniform(self.speed_variation_min, self.speed_variation_max)
                * CalculationConstants.SPEED_CALCULATION_DIVISOR
            )
            next_speed = self.upload_speed * CalculationConstants.BYTES_PER_KB * upload_factor
            next_speed *= update_internal
            next_speed /= CalculationConstants.SPEED_CALCULATION_DIVISOR
            next_speed_bytes = int(next_speed)
            old_session = self.session_uploaded
            old_total = self.total_uploaded
            self.session_uploaded += next_speed_bytes
            self.total_uploaded += next_speed_bytes  # Add only incremental amount, not entire session total
            # Debug: Log first update for this torrent
            if old_total == 0 and self.total_uploaded > 0:
                logger.trace(
                    f"📊 FIRST UPLOAD: {self.name[:30]} - session:{old_session}→{self.session_uploaded}, "
                    f"total:{old_total}→{self.total_uploaded}",
                    extra={"class_name": self.__class__.__name__},
                )

        if self.progress < 1.0:  # type: ignore[has-type]
            download_factor = int(
                random.uniform(self.speed_variation_min, self.speed_variation_max)
                * CalculationConstants.SPEED_CALCULATION_DIVISOR
            )
            next_speed = self.download_speed * CalculationConstants.BYTES_PER_KB * download_factor
            next_speed *= update_internal
            next_speed /= CalculationConstants.SPEED_CALCULATION_DIVISOR
            old_downloaded = self.total_downloaded
            self.session_downloaded += int(next_speed)
            self.total_downloaded += int(next_speed)

            if self.total_downloaded >= self.total_size:
                self.progress = 1.0
            else:
                self.progress = self.total_downloaded / self.total_size

            # Debug: Log first download for this torrent
            if old_downloaded == 0 and self.total_downloaded > 0:
                logger.trace(
                    f"📥 FIRST DOWNLOAD: {self.name[:30]} - downloaded:{old_downloaded}→{self.total_downloaded}, "
                    f"size:{self.total_size}, progress:{self.progress:.2%}",
                    extra={"class_name": self.__class__.__name__},
                )

        if self.next_update > 0:  # type: ignore[has-type]
            old_next_update = self.next_update  # type: ignore[has-type]
            update = self.next_update - int(self.settings.tickspeed)  # type: ignore[has-type]
            self.next_update = update if update > 0 else 0
            logger.trace(
                f"📊 COUNTDOWN UPDATE: {self.name} next_update {old_next_update} -> {self.next_update}",
                extra={"class_name": self.__class__.__name__},
            )

        if self.next_update <= 0:
            self.next_update = self.announce_interval
            logger.trace(
                f"📊 ANNOUNCE CYCLE: {self.name} resetting next_update to {self.announce_interval}",
                extra={"class_name": self.__class__.__name__},
            )
            # announce
            download_left = (
                self.total_size - self.total_downloaded if self.total_size - self.total_downloaded > 0 else 0
            )
            self.seeder.upload(
                self.session_uploaded,
                self.session_downloaded,
                download_left,
            )

        logger.trace(
            f"🚀 EMITTING SIGNAL: {self.name} - progress={self.progress:.3f}, "
            f"up_speed={self.session_uploaded}, down_speed={self.session_downloaded}, "
            f"next_update={self.next_update}",
            extra={"class_name": self.__class__.__name__},
        )
        self.emit("attribute-changed", None, None)

    def save_to_transient(self) -> None:
        """
        Save current torrent state to transient storage (in-memory only, no disk write).
        Called periodically during runtime and when stopping.
        """
        ATTRIBUTES = Attributes
        attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]

        # Build torrent data dictionary
        torrent_data = {attr: getattr(self, attr) for attr in attributes}

        # Update transient storage (NO disk write during runtime)
        # Torrents are only persisted to disk during application shutdown via save_quit()
        self.settings.torrents[self.file_path] = torrent_data

        logger.trace(
            f"💾 Torrent data saved to transient: {self.name[:30]} - progress={self.progress:.2%}, "
            f"uploaded={self.total_uploaded:,}, downloaded={self.total_downloaded:,}",
            extra={"class_name": self.__class__.__name__},
        )

    def stop(self) -> Any:
        logger.info("Torrent stop", extra={"class_name": self.__class__.__name__})

        # Set stopping flag to prevent new threads
        self.is_stopping = True

        # Stop the name update thread
        logger.info(
            "Torrent Stopping fake seeder: " + self.name,
            extra={"class_name": self.__class__.__name__},
        )
        # Only notify if view instance still exists (may be None during shutdown)
        if View.instance is not None:
            View.instance.notify("Stopping fake seeder " + self.name)

        # Request graceful shutdown of seeder first
        if hasattr(self, "seeder") and self.seeder:
            self.seeder.request_shutdown()

        # Stop worker threads with aggressive timeout
        self.torrent_worker_stop_event.set()
        self.torrent_worker.join(timeout=TimeoutConstants.WORKER_SHUTDOWN)

        if self.torrent_worker.is_alive():
            logger.warning(f"⚠️ Torrent worker thread for {self.name} still alive after timeout - forcing shutdown")

        self.peers_worker_stop_event.set()
        self.peers_worker.join(timeout=TimeoutConstants.WORKER_SHUTDOWN)

        if self.peers_worker.is_alive():
            logger.warning(f"⚠️ Peers worker thread for {self.name} still alive after timeout - forcing shutdown")

        # Join any outstanding tracker update threads
        if hasattr(self, "tracker_update_threads") and self.tracker_update_threads:
            logger.trace(
                f"🧹 Joining {len(self.tracker_update_threads)} tracker update threads for {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
            for thread in self.tracker_update_threads:
                if thread.is_alive():
                    thread.join(timeout=0.1)  # Very short timeout - these should finish quickly
            # Clear the list
            self.tracker_update_threads.clear()

        # Save final state to transient storage
        self.save_to_transient()

    def get_seeder(self) -> Any:
        # logger.info("Torrent get seeder",
        # extra={"class_name": self.__class__.__name__})
        return self.seeder

    def is_ready(self) -> Any:
        # logger.info("Torrent get seeder",
        # extra={"class_name": self.__class__.__name__})
        return self.seeder.ready

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace(
            "Torrent settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def _perform_tracker_update(self) -> Any:
        """Perform the actual tracker update - called in background thread"""
        try:
            # First, load peers to refresh peer list
            logger.trace(
                f"📥 Loading peers for {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
            peers_loaded = self.seeder.load_peers()  # type: ignore[func-returns-value]

            if peers_loaded:
                logger.trace(
                    f"✅ Peers loaded successfully for {self.name}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    f"⚠️ Failed to load peers for {self.name}",
                    extra={"class_name": self.__class__.__name__},
                )

            # Calculate current stats for announce
            download_left = (
                self.total_size - self.total_downloaded if self.total_size - self.total_downloaded > 0 else 0
            )

            # Announce to tracker with current stats
            logger.trace(
                f"📤 Announcing to tracker for {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
            self.seeder.upload(
                self.session_uploaded,
                self.session_downloaded,
                download_left,
            )

            # Reset the timer to 1800 seconds (using GLib.idle_add for thread safety)
            GLib.idle_add(self._complete_tracker_update)

        except Exception as e:
            logger.error(
                f"❌ Error during force tracker update for {self.name}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            # Update status bar with error message
            if View.instance is not None:
                GLib.idle_add(self._notify_tracker_update_failed)

    def _complete_tracker_update(self) -> Any:
        """Complete tracker update in UI thread - resets timer and updates UI"""
        self.next_update = 1800
        logger.trace(
            f"⏰ Timer reset to 1800 seconds for {self.name}",
            extra={"class_name": self.__class__.__name__},
        )

        # Emit signal to update UI
        self.emit("attribute-changed", None, None)

        # Update status bar with completion message
        if View.instance is not None:
            View.instance.notify(f"Tracker updated for {self.name}")

        return False  # Don't repeat

    def _notify_tracker_update_failed(self) -> Any:
        """Notify user of tracker update failure"""
        if View.instance is not None:
            View.instance.notify(f"Failed to update tracker for {self.name}")
        return False  # Don't repeat

    def force_tracker_update(self) -> Any:
        """Force an immediate tracker update (called from UI context menu)"""
        # Don't create new threads during shutdown
        if self.is_stopping:
            logger.trace(
                f"🚫 FORCE TRACKER UPDATE: Skipping during shutdown for {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
            return

        logger.trace(
            f"🔄 FORCE TRACKER UPDATE: Manually triggered for {self.name}",
            extra={"class_name": self.__class__.__name__},
        )

        # Only notify if view instance still exists
        if View.instance is not None:
            View.instance.notify(f"Updating tracker for {self.name}")

        # Start the update in a background thread and track it
        update_thread = threading.Thread(
            target=self._perform_tracker_update,
            name=f"ForceTrackerUpdate-{self.name}",
            daemon=True,
        )
        update_thread.start()

        # Track thread for cleanup
        self.tracker_update_threads.append(update_thread)

        # Clean up finished threads from the list
        self.tracker_update_threads = [t for t in self.tracker_update_threads if t.is_alive()]

    def restart_worker(self, state: Any) -> Any:
        logger.trace(
            f"⚡ RESTART WORKER: {self.name} state={state} (active={getattr(self, 'active', 'Unknown')})",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            # Only notify if view instance still exists (may be None during shutdown)
            if View.instance is not None:
                View.instance.notify("Stopping fake seeder " + self.name)
            self.torrent_worker_stop_event.set()
            self.torrent_worker.join()

            self.peers_worker_stop_event.set()
            self.peers_worker.join()
            logger.trace(
                f"⚡ STOPPED WORKERS: {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Error stopping peers worker: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        if state:
            try:
                # Only notify if view instance still exists (may be None during shutdown)
                if View.instance is not None:
                    View.instance.notify("Starting fake seeder " + self.name)
                self.torrent_worker_stop_event = threading.Event()
                self.torrent_worker = threading.Thread(
                    target=self.update_torrent_worker,
                    name=f"TorrentWorker-{self.name}",
                    daemon=True,  # PyPy optimization: daemon threads for better cleanup
                )
                self.torrent_worker.start()
                logger.trace(
                    f"⚡ STARTED UPDATE WORKER: {self.name}",
                    extra={"class_name": self.__class__.__name__},
                )

                # Start peers worker thread
                self.peers_worker_stop_event = threading.Event()
                self.peers_worker = threading.Thread(
                    target=self.peers_worker_update,
                    name=f"PeersWorker-{self.name}",
                    daemon=True,  # PyPy optimization: daemon threads for better cleanup
                )
                self.peers_worker.start()
                logger.trace(
                    f"⚡ STARTED PEERS WORKER: {self.name}",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.error(
                    f"Error starting peers worker: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    def get_attributes(self) -> Any:
        return self.torrent_attributes

    def get_torrent_file(self) -> Any:
        return self.torrent_file

    def __getattr__(self, attr: Any) -> Any:
        if attr == "torrent_attributes":
            self.torrent_attributes = Attributes()
            return self.torrent_attributes
        elif hasattr(self.torrent_attributes, attr):
            return getattr(self.torrent_attributes, attr)
        # Note: Removed hasattr(self, attr) check - it creates infinite recursion
        # and is unnecessary since __getattr__ is only called when attr doesn't exist on self
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

    def __setattr__(self, attr: Any, value: Any) -> None:
        if attr == "torrent_attributes":
            self.__dict__["torrent_attributes"] = value
        elif hasattr(self.torrent_attributes, attr):
            if attr == "active":
                logger.trace(
                    f"🔄 ACTIVE CHANGED: {getattr(self, 'name', 'Unknown')} active={value}",
                    extra={"class_name": self.__class__.__name__},
                )
            setattr(self.torrent_attributes, attr, value)
            if attr == "active":
                self.restart_worker(value)
        else:
            super().__setattr__(attr, value)

    def get_active_tracker_model(self) -> Any:
        """Get tracker model from the currently active seeder"""
        try:
            if hasattr(self, "seeder") and self.seeder and hasattr(self.seeder, "seeder"):
                active_seeder = self.seeder.seeder
                if hasattr(active_seeder, "_get_tracker_model"):
                    return active_seeder._get_tracker_model()  # type: ignore[attr-defined]
            return None
        except Exception as e:
            logger.trace(
                f"Failed to get active tracker model: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    def get_all_tracker_models(self) -> Any:
        """Get tracker models for all trackers (primary and backup)"""
        tracker_models = []

        try:
            # Get primary tracker model from active seeder
            active_tracker = self.get_active_tracker_model()
            if active_tracker:
                tracker_models.append(active_tracker)

            # Create models for backup trackers from announce-list
            if hasattr(self, "torrent_file") and hasattr(self.torrent_file, "announce_list"):
                current_url = active_tracker.get_property("url") if active_tracker else None

                for tier, announce_url in enumerate(self.torrent_file.announce_list):
                    # Skip if this is already the active tracker
                    if announce_url != current_url:
                        tracker_model = Tracker(url=announce_url, tier=tier + 1)
                        tracker_models.append(tracker_model)

        except Exception as e:
            logger.trace(
                f"Failed to get all tracker models: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return tracker_models

    def get_tracker_statistics(self) -> Any:
        """Get aggregated statistics from all tracker models"""
        stats = {
            "total_trackers": 0,
            "working_trackers": 0,
            "failed_trackers": 0,
            "total_seeders": 0,
            "total_leechers": 0,
            "average_response_time": 0.0,
            "last_announce": 0.0,
        }

        try:
            tracker_models = self.get_all_tracker_models()
            stats["total_trackers"] = len(tracker_models)

            working_count = 0
            failed_count = 0
            total_seeders = 0
            total_leechers = 0
            response_times = []
            last_announces = []

            for tracker in tracker_models:
                status = tracker.get_property("status")
                if status == "working":
                    working_count += 1
                    total_seeders += tracker.get_property("seeders")
                    total_leechers += tracker.get_property("leechers")

                    response_time = tracker.get_property("average_response_time")
                    if response_time > 0:
                        response_times.append(response_time)

                    last_announce = tracker.get_property("last_announce")
                    if last_announce > 0:
                        last_announces.append(last_announce)

                elif status == "failed":
                    failed_count += 1

            stats["working_trackers"] = working_count
            stats["failed_trackers"] = failed_count
            stats["total_seeders"] = total_seeders
            stats["total_leechers"] = total_leechers

            if response_times:
                stats["average_response_time"] = sum(response_times) / len(response_times)

            if last_announces:
                stats["last_announce"] = max(last_announces)

        except Exception as e:
            logger.trace(
                f"Failed to get tracker statistics: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return stats
