# fmt: off
# isort: skip_file
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

    def __init__(self, filepath):
        super().__init__()
        logger.debug("instantiate", extra={"class_name": self.__class__.__name__})

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
        self.tracker_update_threads = []  # Track force tracker update threads
        self.is_stopping = False  # Flag to prevent new threads during shutdown

        if self.file_path not in self.settings.torrents:
            self.settings.torrents[self.file_path] = {
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
            self.settings.save_settings()

        ATTRIBUTES = Attributes
        attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]

        self.torrent_file = File(self.file_path)
        self.seeder = Seeder(self.torrent_file)

        # Load attributes from settings with fallback to default values
        for attr in attributes:
            # Use .get() with default values for backward compatibility
            default_value = None
            if attr == "label":
                default_value = ""
            elif attr == "priority":
                default_value = "normal"
            elif attr in ("upload_limit", "download_limit"):
                default_value = 0
            elif attr in ("super_seeding", "sequential_download", "force_start"):
                default_value = False

            # Get value from settings, or use default if key doesn't exist
            value = self.settings.torrents[self.file_path].get(attr, default_value)
            if value is not None:
                setattr(self.torrent_attributes, attr, value)

        self.session_uploaded = 0
        self.session_downloaded = 0

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

    def peers_worker_update(self):
        logger.debug(
            "Peers worker",
            extra={"class_name": self.__class__.__name__},
        )

        try:
            fetched = False
            count = self.seeder_retry_count

            while fetched is False and count != 0:
                # Check for shutdown request before each iteration
                if self.peers_worker_stop_event.is_set():
                    logger.debug(
                        f"🛑 PEERS WORKER SHUTDOWN: {self.name} - stop event received",
                        extra={"class_name": self.__class__.__name__},
                    )
                    break

                logger.debug(
                    "Requesting seeder information",
                    extra={"class_name": self.__class__.__name__},
                )
                fetched = self.seeder.load_peers()
                if fetched is False:
                    logger.debug(
                        f"Seeder failed to load peers, retrying in {TimeoutConstants.TORRENT_PEER_RETRY} seconds",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Use Event.wait() instead of time.sleep() for instant shutdown response
                    if self.peers_worker_stop_event.wait(timeout=int(self.seeder_retry_interval)):
                        logger.debug(
                            f"🛑 PEERS WORKER SHUTDOWN: {self.name} - stop event received during retry sleep",
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

    def update_torrent_worker(self):
        logger.debug(
            f"🔄 TORRENT UPDATE WORKER STARTED for {self.name}",
            extra={"class_name": self.__class__.__name__},
        )

        try:
            ticker = 0.0

            # Use Event.wait() instead of time.sleep() for instant shutdown response
            while not self.torrent_worker_stop_event.wait(timeout=self.worker_sleep_interval):
                logger.debug(
                    f"🔄 WORKER LOOP: {self.name} ticker={ticker:.2f}, tickspeed={self.settings.tickspeed}, "
                    f"active={self.active}",
                    extra={"class_name": self.__class__.__name__},
                )
                if ticker >= self.settings.tickspeed and self.active:
                    logger.debug(
                        f"🔄 WORKER: Adding update callback to UI thread for {self.name} "
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

    def update_torrent_callback(self):
        logger.debug(
            f"📊 TORRENT UPDATE CALLBACK STARTED for {self.name} - updating values",
            extra={"class_name": self.__class__.__name__},
        )

        update_internal = int(self.settings.tickspeed)

        if self.name != self.torrent_file.name:
            self.name = self.torrent_file.name

        if self.total_size != self.torrent_file.total_size:
            self.total_size = self.torrent_file.total_size

        if self.seeder.ready:
            if self.seeders != self.seeder.seeders:
                self.seeders = self.seeder.seeders

            if self.leechers != self.seeder.leechers:
                self.leechers = self.seeder.leechers

        threshold = (
            self.settings.torrents[self.file_path]["threshold"]
            if "threshold" in self.settings.torrents[self.file_path]
            else self.settings.threshold
        )

        if self.threshold != threshold:
            self.threshold = threshold

        if self.progress >= (threshold / 100) and not self.uploading:
            if self.uploading is False:
                self.uploading = True

        if self.uploading:
            upload_factor = int(
                random.uniform(self.speed_variation_min, self.speed_variation_max)
                * CalculationConstants.SPEED_CALCULATION_DIVISOR
            )
            next_speed = self.upload_speed * CalculationConstants.BYTES_PER_KB * upload_factor
            next_speed *= update_internal
            next_speed /= CalculationConstants.SPEED_CALCULATION_DIVISOR
            self.session_uploaded += int(next_speed)
            self.total_uploaded += self.session_uploaded

        if self.progress < 1.0:
            download_factor = int(
                random.uniform(self.speed_variation_min, self.speed_variation_max)
                * CalculationConstants.SPEED_CALCULATION_DIVISOR
            )
            next_speed = self.download_speed * CalculationConstants.BYTES_PER_KB * download_factor
            next_speed *= update_internal
            next_speed /= CalculationConstants.SPEED_CALCULATION_DIVISOR
            self.session_downloaded += int(next_speed)
            self.total_downloaded += int(next_speed)

            if self.total_downloaded >= self.total_size:
                self.progress = 1.0
            else:
                self.progress = self.total_downloaded / self.total_size

        if self.next_update > 0:
            old_next_update = self.next_update
            update = self.next_update - int(self.settings.tickspeed)
            self.next_update = update if update > 0 else 0
            logger.debug(
                f"📊 COUNTDOWN UPDATE: {self.name} next_update {old_next_update} -> {self.next_update}",
                extra={"class_name": self.__class__.__name__},
            )

        if self.next_update <= 0:
            self.next_update = self.announce_interval
            logger.debug(
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

        logger.debug(
            f"🚀 EMITTING SIGNAL: {self.name} - progress={self.progress:.3f}, "
            f"up_speed={self.session_uploaded}, down_speed={self.session_downloaded}, "
            f"next_update={self.next_update}",
            extra={"class_name": self.__class__.__name__},
        )
        self.emit("attribute-changed", None, None)

    def stop(self):
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
            logger.debug(
                f"🧹 Joining {len(self.tracker_update_threads)} tracker update threads for {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
            for thread in self.tracker_update_threads:
                if thread.is_alive():
                    thread.join(timeout=0.1)  # Very short timeout - these should finish quickly
            # Clear the list
            self.tracker_update_threads.clear()

        ATTRIBUTES = Attributes
        attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
        self.settings.torrents[self.file_path] = {attr: getattr(self, attr) for attr in attributes}

    def get_seeder(self):
        # logger.info("Torrent get seeder",
        # extra={"class_name": self.__class__.__name__})
        return self.seeder

    def is_ready(self):
        # logger.info("Torrent get seeder",
        # extra={"class_name": self.__class__.__name__})
        return self.seeder.ready

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrent settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def _perform_tracker_update(self):
        """Perform the actual tracker update - called in background thread"""
        try:
            # First, load peers to refresh peer list
            logger.debug(
                f"📥 Loading peers for {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
            peers_loaded = self.seeder.load_peers()

            if peers_loaded:
                logger.debug(
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
            logger.debug(
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

    def _complete_tracker_update(self):
        """Complete tracker update in UI thread - resets timer and updates UI"""
        self.next_update = 1800
        logger.debug(
            f"⏰ Timer reset to 1800 seconds for {self.name}",
            extra={"class_name": self.__class__.__name__},
        )

        # Emit signal to update UI
        self.emit("attribute-changed", None, None)

        # Update status bar with completion message
        if View.instance is not None:
            View.instance.notify(f"Tracker updated for {self.name}")

        return False  # Don't repeat

    def _notify_tracker_update_failed(self):
        """Notify user of tracker update failure"""
        if View.instance is not None:
            View.instance.notify(f"Failed to update tracker for {self.name}")
        return False  # Don't repeat

    def force_tracker_update(self):
        """Force an immediate tracker update (called from UI context menu)"""
        # Don't create new threads during shutdown
        if self.is_stopping:
            logger.debug(
                f"🚫 FORCE TRACKER UPDATE: Skipping during shutdown for {self.name}",
                extra={"class_name": self.__class__.__name__},
            )
            return

        logger.debug(
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

    def restart_worker(self, state):
        logger.debug(
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
            logger.debug(
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
                logger.debug(
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
                logger.debug(
                    f"⚡ STARTED PEERS WORKER: {self.name}",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.error(
                    f"Error starting peers worker: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    def get_attributes(self):
        return self.torrent_attributes

    def get_torrent_file(self):
        return self.torrent_file

    def __getattr__(self, attr):
        if attr == "torrent_attributes":
            self.torrent_attributes = Attributes()
            return self.torrent_attributes
        elif hasattr(self.torrent_attributes, attr):
            return getattr(self.torrent_attributes, attr)
        # Note: Removed hasattr(self, attr) check - it creates infinite recursion
        # and is unnecessary since __getattr__ is only called when attr doesn't exist on self
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attr}'")

    def __setattr__(self, attr, value):
        if attr == "torrent_attributes":
            self.__dict__["torrent_attributes"] = value
        elif hasattr(self.torrent_attributes, attr):
            if attr == "active":
                logger.debug(
                    f"🔄 ACTIVE CHANGED: {getattr(self, 'name', 'Unknown')} active={value}",
                    extra={"class_name": self.__class__.__name__},
                )
            setattr(self.torrent_attributes, attr, value)
            if attr == "active":
                self.restart_worker(value)
        else:
            super().__setattr__(attr, value)

    def get_active_tracker_model(self):
        """Get tracker model from the currently active seeder"""
        try:
            if hasattr(self, "seeder") and self.seeder and hasattr(self.seeder, "seeder"):
                active_seeder = self.seeder.seeder
                if hasattr(active_seeder, "_get_tracker_model"):
                    return active_seeder._get_tracker_model()
            return None
        except Exception as e:
            logger.debug(
                f"Failed to get active tracker model: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    def get_all_tracker_models(self):
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
            logger.debug(
                f"Failed to get all tracker models: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return tracker_models

    def get_tracker_statistics(self):
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
            logger.debug(
                f"Failed to get tracker statistics: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return stats
