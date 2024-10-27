import gi
from lib.component.component import Component
from lib.logger import logger
from lib.settings import Settings

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa


class States(Component):
    def __init__(self, builder, model):
        self.builder = builder
        self.model = model

        # Subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.states_columnview = self.builder.get_object("states_columnview")

        # Initialize columns
        self.create_columns()

    def create_columns(self):
        # Create the column for the tracker name
        tracker_col = Gtk.ColumnViewColumn()
        tracker_col.set_title("Tracker")
        tracker_col.set_visible(True)  # Set column visibility
        tracker_col.set_expand(True)

        # Create a custom factory for the tracker column
        tracker_factory = Gtk.SignalListItemFactory()
        tracker_factory.connect("setup", self.setup_tracker_factory)
        tracker_factory.connect("bind", self.bind_tracker_factory)
        tracker_col.set_factory(tracker_factory)

        self.states_columnview.append_column(tracker_col)

        # Create the column for the count
        count_col = Gtk.ColumnViewColumn()
        count_col.set_title("#")
        count_col.set_visible(True)  # Set column visibility

        # Create a custom factory for the count column
        count_factory = Gtk.SignalListItemFactory()
        count_factory.connect("setup", self.setup_count_factory)
        count_factory.connect("bind", self.bind_count_factory)
        count_col.set_factory(count_factory)

        self.states_columnview.append_column(count_col)

    def setup_tracker_factory(self, factory, item):
        item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def bind_tracker_factory(self, factory, item):
        # Get the item from the factory
        torrent_state = item.get_item()

        # Update the label with the tracker data
        value = torrent_state.tracker if torrent_state.tracker is not None else ""
        item.get_child().set_label(value)

    def setup_count_factory(self, factory, item):
        item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def bind_count_factory(self, factory, item):
        # Get the item from the factory
        torrent_state = item.get_item()

        # Update the label with the count data
        item.get_child().set_label(str(torrent_state.count))

    # Method to update the ColumnView with compatible attributes
    def update_view(self, model, torrent, attribute):
        selection_model = Gtk.SingleSelection.new(model.get_trackers_liststore())
        self.states_columnview.set_model(selection_model)

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.debug(
            "States settings update",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

    def handle_attribute_changed(self, source, key, value):
        logger.debug(
            "Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def model_selection_changed(self, source, model, torrent):
        logger.debug(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
