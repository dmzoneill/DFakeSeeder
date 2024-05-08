import logging

import gi
from lib.component.component import Component
from lib.logger import logger
from lib.settings import Settings
from lib.torrent.model.attributes import Attributes
from lib.torrent.model.torrent_peer import TorrentPeer

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GLib, GObject, Gtk  # noqa


class Notebook(Component):
    def __init__(self, builder, model):
        logger.info(
            "Notebook view startup",
            extra={"class_name": self.__class__.__name__},
        )
        self.builder = builder
        self.model = model

        self.notebook = self.builder.get_object("notebook1")
        self.peers_columnview = self.builder.get_object("peers_columnview")
        self.log_scroll = self.builder.get_object("log_scroll")
        self.log_viewer = self.builder.get_object("log_viewer")

        self.setup_log_viewer_handler()
        self.init_peers_column_view()

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        # tab children
        self.status_grid_child = None
        self.options_grid_children = []

        tab_names = [
            "status_tab",
            "details_tab",
            "options_tab",
            "peers_tab",
            "trackers_tab",
            "log_tab",
        ]

        for tab_name in tab_names:
            tab = self.builder.get_object(tab_name)
            tab.set_visible(True)
            tab.set_margin_top(10)
            tab.set_margin_bottom(10)
            tab.set_margin_start(10)
            tab.set_margin_end(10)

    def setup_log_viewer_handler(self):
        def update_textview(record):
            msg = f"{record.levelname}: {record.getMessage()}\n"
            GLib.idle_add(lambda: self.update_text_buffer(self.log_viewer, msg))

        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        handler.setLevel(logging.DEBUG)
        handler.emit = update_textview

        logger = logging.getLogger()
        logger.addHandler(handler)

    def update_text_buffer(self, text_view, msg):
        buffer = text_view.get_buffer()
        buffer.insert_at_cursor(msg)

        _, end_iter = buffer.get_bounds()
        end_line = end_iter.get_line()
        if end_line > 1000:
            start_iter, _ = buffer.get_iter_at_line(end_line - 1000)
            buffer.delete(start_iter, buffer.get_start_iter())

    def init_peers_column_view(self):
        logger.info(
            "Notebook init peers columnview",
            extra={"class_name": self.__class__.__name__},
        )

        self.peers_store = Gio.ListStore.new(TorrentPeer)

        properties = [prop.name for prop in TorrentPeer.list_properties()]

        for i, property_name in enumerate(properties):
            factory = Gtk.SignalListItemFactory()
            factory.connect("setup", self.setup, property_name)
            factory.connect("bind", self.bind, property_name)
            column = Gtk.ColumnViewColumn.new(property_name, factory)

            # Create a Gtk.Expression for the property
            property_expression = Gtk.PropertyExpression.new(
                TorrentPeer, None, property_name
            )

            # Create a Gtk.Sorter based on the property type
            property_type = TorrentPeer.find_property(
                property_name
            ).value_type.fundamental
            if property_type == GObject.TYPE_STRING:
                sorter = Gtk.StringSorter.new(property_expression)
            elif property_type == GObject.TYPE_FLOAT:
                sorter = Gtk.NumericSorter.new(property_expression)
            elif property_type == GObject.TYPE_BOOLEAN:
                sorter = Gtk.NumericSorter.new(property_expression)

            # Set the sorter on the column
            column.set_sorter(sorter)

            self.peers_columnview.append_column(column)

        sorter = Gtk.ColumnView.get_sorter(self.peers_columnview)
        self.sort_model = Gtk.SortListModel.new(self.peers_store, sorter)
        self.selection = Gtk.SingleSelection.new(self.sort_model)
        self.peers_columnview.set_model(self.selection)

    def update_notebook_peers(self, torrent):
        logger.info(
            "Notebook update peers",
            extra={"class_name": self.__class__.__name__},
        )

        torrent = next(
            (item for item in self.model.get_torrents() if item.id == torrent.id), None
        )

        num_rows = len(self.peers_columnview.get_model())
        num_peers = len(torrent.get_seeder().peers)

        if num_rows != num_peers:
            self.peers_store.remove_all()

            for peer in torrent.get_seeder().peers:
                client = (
                    torrent.get_seeder().clients[peer]
                    if peer in torrent.get_seeder().clients
                    else ""
                )
                row = TorrentPeer(str(peer), client, 0.0, 0.0, 0.0)
                self.peers_store.append(row)

            self.peers_columnview.set_model(self.peers_store)

    def setup(self, widget, item, property_name):
        def setup_when_idle():
            obj = item.get_item()
            property_type = obj.find_property(property_name).value_type
            if property_type == GObject.TYPE_BOOLEAN:
                widget_type = Gtk.CheckButton
            else:
                widget_type = Gtk.Label
            widget = widget_type()
            item.set_child(widget)

        GLib.idle_add(setup_when_idle)

    def bind(self, widget, item, property_name):
        def bind_when_idle():
            child = item.get_child()
            obj = item.get_item()
            if obj is not None:
                property_type = obj.find_property(property_name).value_type
                if property_type == GObject.TYPE_BOOLEAN:
                    widget_property = "active"
                    obj.bind_property(
                        property_name,
                        child,
                        widget_property,
                        GObject.BindingFlags.SYNC_CREATE,
                    )
                else:
                    widget_property = "label"
                    obj.bind_property(
                        property_name,
                        child,
                        widget_property,
                        GObject.BindingFlags.SYNC_CREATE,
                        self.to_str,
                    )

        GLib.idle_add(bind_when_idle)

    def update_notebook_options(self, torrent):
        grid = self.builder.get_object("options_grid")

        for child in self.options_grid_children:
            grid.remove(child)
            child.unparent()
        self.options_grid_children = []

        def on_value_changed(widget, *args):
            attribute = args[-1]
            if isinstance(widget, Gtk.Switch):
                value = widget.get_active()
            else:
                adjustment = widget.get_adjustment()
                value = adjustment.get_value()
            setattr(torrent, attribute, value)

        row = 0
        for index, attribute in enumerate(self.settings.editwidgets):
            col = 0 if index % 2 == 0 else 2

            widget_type = self.settings.editwidgets[attribute]
            widget_class = eval(widget_type)
            dynamic_widget = widget_class()
            dynamic_widget.set_visible(True)
            dynamic_widget.set_hexpand(True)
            if isinstance(dynamic_widget, Gtk.Switch):
                dynamic_widget.set_active(getattr(torrent, attribute))
                # Connect "state-set" signal for Gtk.Switch
                dynamic_widget.connect("state-set", on_value_changed, attribute)
            else:
                adjustment = Gtk.Adjustment(
                    value=getattr(torrent, attribute),
                    upper=getattr(torrent, attribute) * 10,
                    lower=0,
                    step_increment=1,
                    page_increment=10,
                )
                dynamic_widget.set_adjustment(adjustment)
                dynamic_widget.set_wrap(True)
                # Connect "value-changed" signal for other widgets
                dynamic_widget.connect(
                    "value-changed", on_value_changed, adjustment, attribute
                )

            label = Gtk.Label()
            label.set_text(attribute)
            label.set_name(f"label_{attribute}")
            label.set_visible(True)
            label.set_hexpand(True)

            grid.attach(label, col, row, 1, 1)
            grid.attach(dynamic_widget, col + 1, row, 1, 1)
            self.options_grid_children.append(label)
            self.options_grid_children.append(dynamic_widget)

            if col == 2:
                row += 1

    def update_notebook_status(self, torrent):
        logger.info(
            "Notebook update status",
            extra={"class_name": self.__class__.__name__},
        )

        if self.status_grid_child is not None:
            self.status_tab.remove(self.status_grid_child)
            self.status_grid_child.unparent()

        self.status_grid_child = Gtk.Grid()
        self.status_grid_child.set_column_spacing(10)
        self.status_grid_child.set_hexpand(True)
        self.status_grid_child.set_vexpand(True)
        self.status_grid_child.set_visible(True)

        ATTRIBUTES = Attributes
        compatible_attributes = [
            prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)
        ]

        # Create columns and add them to the TreeView
        for attribute_index, attribute in enumerate(compatible_attributes):
            row = attribute_index

            labeln = Gtk.Label(label=attribute, xalign=0)
            labeln.set_visible(True)
            # labeln.set_margin_left(10)
            labeln.set_halign(Gtk.Align.START)
            labeln.set_size_request(80, -1)
            self.status_grid_child.attach(labeln, 0, row, 1, 1)

            val = torrent.get_property(attribute)
            labelv = Gtk.Label(label=val, xalign=0)
            labelv.set_visible(True)
            # labelv.set_margin_left(10)
            labelv.set_halign(Gtk.Align.START)
            labeln.set_size_request(280, -1)
            labelv.set_selectable(True)  # Enable text selection
            self.status_grid_child.attach(labelv, 1, row, 1, 1)

        self.status_tab = self.builder.get_object("status_tab")
        self.status_tab.append(self.status_grid_child)

    def update_view(self, model, torrent, attribute):
        pass

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.info(
            "Notebook settings changed",
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
        if torrent is not None:
            self.update_notebook_status(torrent)
            self.update_notebook_options(torrent)
            self.update_notebook_peers(torrent)
