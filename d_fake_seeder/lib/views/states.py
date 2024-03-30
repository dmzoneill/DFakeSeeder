import gi
from lib.logger import logger
from lib.settings import Settings

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa


class States:
    def __init__(self, builder, model):
        logger.info("States startup", extra={"class_name": self.__class__.__name__})
        self.builder = builder
        self.model = model

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.states_treeview = self.builder.get_object("states_treeview")

    def set_model(self, model):
        self.model = model

    # Method to update the TreeView with compatible attributes
    def update_view(self, model, _, torrent, attribute):
        logger.debug("States update view", extra={"class_name": self.__class__.__name__})
        if len(self.states_treeview.get_columns()) != 2:
            # Create the column for the tracker name
            tracker_col = Gtk.TreeViewColumn("Tracker", Gtk.CellRendererText(), text=0)
            self.states_treeview.append_column(tracker_col)
            # Create the column for the count
            count_col = Gtk.TreeViewColumn("#", Gtk.CellRendererText(), text=1)
            self.states_treeview.append_column(count_col)

        self.states_treeview.set_model(self.model.get_trackers_liststore())

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "States settings update",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)
