import random
import threading
import time

import gi
from lib.logger import logger
from lib.settings import Settings
from lib.torrent.file import File
from lib.torrent.model.attributes import Attributes
from lib.torrent.seeder import Seeder
from lib.view import View

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import GLib, GObject  # noqa


# Torrent class definition
class Torrent(GObject.GObject):
    # Define custom signal 'attribute-changed' which is emitted when torrent data
    # is modified
    __gsignals__ = {
        "attribute-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (object, object),
        )
    }

    def __init__(self, filepath):
        super().__init__()
        logger.info("Torrent instantiate", extra={"class_name": self.__class__.__name__})

        self.torrent_attributes = Attributes()

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.file_path = filepath

        if self.file_path not in self.settings.torrents:
            self.settings.torrents[self.file_path] = {
                "active": True,
                "id": (
                    len(self.settings.torrents) + 1
                    if len(self.settings.torrents) > 0
                    else 1
                ),
                "name": "",
                "upload_speed": self.settings.upload_speed,
                "download_speed": self.settings.download_speed,
                "progress": 0,
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
            }
            self.settings.save_settings()

        ATTRIBUTES = Attributes
        attributes = [
            prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)
        ]

        self.torrent_file = File(self.file_path)
        self.seeder = Seeder(self.torrent_file)

        for attr in attributes:
            setattr(
                self.torrent_attributes,
                attr,
                self.settings.torrents[self.file_path][attr],
            )

        self.session_uploaded = 0
        self.session_downloaded = 0

        # Start the thread to update the name
        self.torrent_worker_stop_event = threading.Event()
        self.torrent_worker = threading.Thread(target=self.update_torrent_worker)
        self.torrent_worker.start()

    def update_torrent_worker(self):
        logger.info(
            "Torrent update worker",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            fetched = False
            count = 3
            while fetched is False and count != 0:
                logger.debug(
                    "Requesting seeder information",
                    extra={"class_name": self.__class__.__name__},
                )
                fetched = self.seeder.load_peers()
                if fetched is False:
                    print("sleeping 30")
                    time.sleep(30)
                    count -= 1
                    if count == 0:
                        print("Paused")
                        self.active = False

            ticker = 0.0
            GLib.idle_add(self.update_torrent_callback)
            time.sleep(random.uniform(1.0, self.settings.tickspeed))

            while not self.torrent_worker_stop_event.is_set():
                if ticker == self.settings.tickspeed and self.active:
                    GLib.idle_add(self.update_torrent_callback)
                if ticker == self.settings.tickspeed:
                    ticker = 0.0
                ticker += 0.5
                time.sleep(0.5)

        except KeyboardInterrupt:
            pass

    def update_torrent_callback(self):
        logger.debug(
            "Torrent torrent update callback",
            extra={"class_name": self.__class__.__name__},
        )

        update_internal = int(self.settings.tickspeed)

        if self.name != self.torrent_file.name:
            self.name = self.torrent_file.name

        if self.total_size != self.torrent_file.total_size:
            self.total_size = self.torrent_file.total_size

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

        if self.progress >= threshold and not self.uploading:
            if self.uploading is False:
                self.uploading = True

        if self.uploading:
            upload_factor = int(random.uniform(0.200, 0.800) * 1000)
            next_speed = self.upload_speed * 1024 * upload_factor
            next_speed *= update_internal
            next_speed /= 1000
            self.session_uploaded += int(next_speed)
            self.total_uploaded += self.session_uploaded

        if self.progress < 100:
            download_factor = int(random.uniform(0.200, 0.800) * 1000)
            next_speed = self.download_speed * 1024 * download_factor
            next_speed *= update_internal
            next_speed /= 1000
            self.session_downloaded += int(next_speed)
            self.total_downloaded += int(next_speed)

            if self.total_downloaded >= self.total_size:
                self.progress = 100
            else:
                self.progress = round((self.total_downloaded / self.total_size) * 100)

        if self.next_update > 0:
            update = self.next_update - int(self.settings.tickspeed)
            self.next_update = update if update > 0 else 0

        if self.next_update <= 0:
            self.next_update = self.announce_interval
            # announce
            download_left = (
                self.total_size - self.total_downloaded
                if self.total_size - self.total_downloaded > 0
                else 0
            )
            self.seeder.upload(
                self.session_uploaded,
                self.session_downloaded,
                download_left,
            )

        self.emit("attribute-changed", None, None)

    def stop(self):
        logger.info("Torrent stop", extra={"class_name": self.__class__.__name__})
        # Stop the name update thread
        logger.info(
            "Torrent Stopping fake seeder: " + self.name,
            extra={"class_name": self.__class__.__name__},
        )
        View.instance.notify("Stopping fake seeder " + self.name)
        self.torrent_worker_stop_event.set()
        self.torrent_worker.join()
        ATTRIBUTES = Attributes
        attributes = [
            prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)
        ]
        self.settings.torrents[self.file_path] = {
            attr: getattr(self, attr) for attr in attributes
        }

    def get_seeder(self):
        logger.info("Torrent get seeder", extra={"class_name": self.__class__.__name__})
        return self.seeder

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Torrent settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

    def restart_worker(self, state):
        logger.info(
            "Torrent restart worker",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            View.instance.notify("Stopping fake seeder " + self.name)
            self.torrent_worker_stop_event.set()
            self.torrent_worker.join()
        except Exception as e:
            print(e)

        if state:
            try:
                View.instance.notify("Starting fake seeder " + self.name)
                self.torrent_worker_stop_event = threading.Event()
                self.torrent_worker = threading.Thread(target=self.update_torrent_worker)
                self.torrent_worker.start()
            except Exception as e:
                print(e)

    def get_attributes(self):
        return self.torrent_attributes

    def __getattr__(self, attr):
        if attr == "torrent_attributes":
            self.torrent_attributes = Attributes()
            return self.torrent_attributes
        elif hasattr(self.torrent_attributes, attr):
            return getattr(self.torrent_attributes, attr)
        elif hasattr(self, attr):
            return getattr(self, attr)
        raise AttributeError(
            f"'{self.__class__.__name__}' object has no attribute '{attr}'"
        )

    def __setattr__(self, attr, value):
        if attr == "torrent_attributes":
            self.__dict__["torrent_attributes"] = value
        elif hasattr(self.torrent_attributes, attr):
            setattr(self.torrent_attributes, attr, value)
            if attr == "active":
                self.restart_worker(value)
        else:
            super().__setattr__(attr, value)
