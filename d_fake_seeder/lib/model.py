from urllib.parse import urlparse

import gi  # noqa
from lib.logger import logger
from lib.settings import Settings
from lib.torrent.attributes import Attributes
from lib.torrent.torrent import Torrent

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import GObject, Gtk  # noqa


# Class for handling Torrent data
class Model(GObject.GObject):
    # Define custom signal 'data-changed' which is emitted when torrent data
    # is modified
    __gsignals__ = {
        "data-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (object, object, object),
        )
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        logger.info("Model instantiate", extra={"class_name": self.__class__.__name__})

        # prevent too many view changes
        # self.last_data_changed_time = 0

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.torrent_list = []  # List to hold all torrent instances

    # Method to add a new torrent
    def add_torrent(self, filepath):
        logger.info("Model add torrent", extra={"class_name": self.__class__.__name__})

        # Create new Torrent instance
        torrent = Torrent(filepath)

        # Connect 'attribute-changed' signal of torrent to on_attribute_changed
        # method
        torrent.connect("attribute-changed", self.on_attribute_changed)
        self.torrent_list.append(torrent)

        self.torrent_list.sort(key=lambda x: x.id)  # Sort the list by id

        current_id = 1
        for torrent in self.torrent_list:
            if torrent.id != current_id:
                torrent.id = current_id
            current_id += 1

        # Emit 'data-changed' signal with torrent instance and message
        self.emit("data-changed", self, torrent, "add")

    # Method to add a new torrent
    def remove_torrent(self, filepath):
        logger.info("Model add torrent", extra={"class_name": self.__class__.__name__})

        # Create new Torrent instance
        torrent = Torrent(filepath)

        # Connect 'attribute-changed' signal of torrent to on_attribute_changed
        # method
        torrent.connect("attribute-changed", self.on_attribute_changed)
        self.torrent_list.append(torrent)

        # Emit 'data-changed' signal with torrent instance and message
        self.emit("data-changed", self, torrent, "remove")

    # Method to handle 'attribute-changed' signal of Torrent instance
    def on_attribute_changed(self, model, torrent, attributes):
        logger.debug(
            "Model on attribute changed",
            extra={"class_name": self.__class__.__name__},
        )
        # current_time = time.time()
        # if current_time - self.last_data_changed_time >= 1:
        #     self.last_data_changed_time = current_time
        # Emit 'data-changed' signal with torrent instance and modified
        # attribute

        self.emit("data-changed", model, torrent, attributes)

    # Method to get ListStore of torrents for Gtk.TreeView
    def get_liststore(self, filter_torrent=None):
        logger.debug("Model get_liststore", extra={"class_name": self.__class__.__name__})
        ATTRIBUTES = Attributes
        attributes = list(vars(ATTRIBUTES)["__annotations__"].keys())
        cols = self.settings.columns if hasattr(self.settings, "columns") else None

        if cols is not None and cols != "":
            if "," in cols:
                cols = cols.split(",")
                attributes = [attr for attr in cols if attr in attributes]
            else:
                attributes = cols if cols in attributes else attributes

        compatible_attributes = []
        column_types = []

        instance = Attributes()
        # Determine compatible attributes and column types
        for attr in attributes:
            attr_type = type(getattr(instance, attr))
            if attr_type in (int, float, bool, str):
                if attr_type == int:
                    column_types.append(GObject.TYPE_LONG)
                else:
                    column_types.append(attr_type)
                compatible_attributes.append(attr)

        liststore = Gtk.ListStore(*column_types)

        # sort the list
        self.torrent_list.sort(key=lambda x: x.id)

        if filter_torrent is None:
            # Append data of each torrent to ListStore
            for torrent in self.torrent_list:
                row_values = [getattr(torrent, attr) for attr in compatible_attributes]
                liststore.append(row_values)
        else:
            # Append data of each torrent to ListStore
            for torrent in self.torrent_list:
                if torrent.filepath == filter_torrent.filepath:
                    row_values = [
                        getattr(torrent, attr) for attr in compatible_attributes
                    ]
                    liststore.append(row_values)
                    break

        return [compatible_attributes, liststore]

    # Method to get ListStore of torrents for Gtk.TreeView
    def get_liststore_model(self):
        logger.debug("Model get_liststore", extra={"class_name": self.__class__.__name__})
        ATTRIBUTES = Attributes
        attributes = list(vars(ATTRIBUTES)["__annotations__"].keys())
        cols = self.settings.columns if hasattr(self.settings, "columns") else None

        if cols is not None and cols != "":
            if "," in cols:
                cols = cols.split(",")
                attributes = [attr for attr in cols if attr in attributes]
            else:
                attributes = cols if cols in attributes else attributes

        compatible_attributes = []
        column_types = []

        instance = Attributes()
        # Determine compatible attributes and column types
        for attr in attributes:
            attr_type = type(getattr(instance, attr))
            if attr_type in (int, float, bool, str):
                if attr_type == int:
                    column_types.append(GObject.TYPE_LONG)
                else:
                    column_types.append(attr_type)
                compatible_attributes.append(attr)

        liststore = Gtk.ListStore(*column_types)

        return liststore

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

        list_store = Gtk.ListStore(str, int)
        for fqdn, count in tracker_count.items():
            list_store.append([fqdn, count])

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
