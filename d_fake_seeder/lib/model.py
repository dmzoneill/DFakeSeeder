from urllib.parse import urlparse

import gi  # noqa
from lib.logger import logger
from lib.settings import Settings
from lib.torrent.model.attributes import Attributes
from lib.torrent.model.torrentstate import TorrentState
from lib.torrent.torrent import Torrent

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GObject, Gtk  # noqa


# Class for handling Torrent data
class Model(GObject.GObject):
    # Define custom signal 'data-changed' which is emitted when torrent data
    # is modified
    __gsignals__ = {
        "data-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (object, object),
        ),
        "selection-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (object, object),
        ),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        logger.info("Model instantiate", extra={"class_name": self.__class__.__name__})

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.torrent_list = []  # List to hold all torrent instances
        self.torrent_list_attributes = Gio.ListStore.new(
            Attributes
        )  # List to hold all Attributes instances

    # Method to add a new torrent
    def add_torrent(self, filepath):
        logger.info("Model add torrent", extra={"class_name": self.__class__.__name__})

        # Create new Torrent instance
        torrent = Torrent(filepath)
        torrent.connect("attribute-changed", self.handle_model_changed)
        self.torrent_list.append(torrent)
        self.torrent_list_attributes.append(torrent.get_attributes())

        current_id = 1
        for torrent in self.torrent_list:
            if torrent.id != current_id:
                torrent.id = current_id
            current_id += 1

        # Emit 'data-changed' signal with torrent instance and message
        self.emit("data-changed", torrent, "add")

    # Method to add a new torrent
    def remove_torrent(self, filepath):
        logger.info("Model add torrent", extra={"class_name": self.__class__.__name__})

        # Find the Torrent instance
        torrent = next((t for t in self.torrent_list if t.filepath == filepath), None)
        if torrent is not None:
            self.torrent_list.remove(torrent)
            self.torrent_list_attributes.remove(torrent.torrent_attributes)

        # Emit 'data-changed' signal with torrent instance and message
        self.emit("data-changed", torrent, "remove")

    # Method to get ListStore of torrents for Gtk.TreeView
    def get_liststore(self):
        logger.debug(
            "Model get_liststore", extra={"class_name": self.__class__.__name__}
        )
        return self.torrent_list_attributes

    def get_torrents(self):
        logger.debug(
            "Model get_torrents", extra={"class_name": self.__class__.__name__}
        )
        return self.torrent_list

    def get_trackers_liststore(self):
        logger.debug(
            "Model get trackers liststore",
            extra={"class_name": self.__class__.__name__},
        )
        tracker_count = {}
        for torrent in self.torrent_list:
            tracker_url = torrent.seeder.tracker
            parsed_url = urlparse(tracker_url)
            fqdn = parsed_url.hostname
            if fqdn in tracker_count:
                tracker_count[fqdn] += 1
            else:
                tracker_count[fqdn] = 1

        # Create a list store with the custom GObject type TorrentState
        list_store = Gio.ListStore.new(TorrentState)

        for fqdn, count in tracker_count.items():
            # Create a new instance of TorrentState and append it to the list store
            list_store.append(TorrentState(fqdn, count))

        return list_store

    # Method to get ListStore of torrents for Gtk.TreeView
    def get_liststore_item(self, index):
        logger.info(
            "Model get list store item",
            extra={"class_name": self.__class__.__name__},
        )
        return self.torrent_list[index]

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Model settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.info(
            "Notebook settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        self.emit("data-changed", data_obj, "attribute")
