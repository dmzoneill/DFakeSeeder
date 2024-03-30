import logging

import gi
from lib.logger import logger
from lib.settings import Settings

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import GLib, Gtk  # noqa


class Notebook:
    def __init__(self, builder, model):
        logger.info(
            "Notebook view startup",
            extra={"class_name": self.__class__.__name__},
        )
        self.builder = builder
        self.model = model

        self.selected_path = None

        self.notebook = self.builder.get_object("notebook1")
        self.torrents_treeview = self.builder.get_object("treeview1")
        self.peers_treeview = self.builder.get_object("peers_treeview")
        self.log_scroll = self.builder.get_object("log_scroll")
        self.log_viewer = self.builder.get_object("log_viewer")
        self.setup_log_viewer_handler(self.log_viewer)
        # self.log_viewer.connect("size-allocate", self.on_size_allocate)

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

        self.status_tab = self.builder.get_object("status_tab")
        self.notebook.set_current_page(0)
        self.notebook.page_num(self.status_tab)
        # label_widget =
        # self.notebook.get_tab_label(self.notebook.get_nth_page(0))
        # self.notebook.set_current_page(
        #     self.notebook.page_num(label_widget.get_parent())
        # )

        # Connect the signals
        self.selection = self.torrents_treeview.get_selection()
        self.selection.connect("changed", self.on_selection_changed)
        # self.torrents_treeview.connect("row-activated",
        # self.on_row_activated)

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        # tab children
        self.status_grid_child = None
        self.options_grid_children = []

    def set_model(self, model):
        self.model = model

    # def on_size_allocate(self, widget, allocation):
    #     adj = self.log_scroll.get_vadjustment()
    #     adj.set_value(adj.get_upper() - adj.get_page_size())

    def setup_log_viewer_handler(self, text_view):
        def update_textview(record):
            msg = f"{record.levelname}: {record.getMessage()}\n"
            GLib.idle_add(lambda: self.update_text_buffer(text_view, msg))

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
            start_iter = buffer.get_iter_at_line(end_line - 1000)
            buffer.delete(start_iter, buffer.get_start_iter())

    def get_selected_torrent(self):
        logger.info(
            "Notebook get selected torrent",
            extra={"class_name": self.__class__.__name__},
        )

        # Get the currently selected item
        selection = self.torrents_treeview.get_selection()
        lmodel, tree_iter = selection.get_selected()

        if tree_iter is None:
            return

        # Get the index of the selected item
        index = int(lmodel.get_path(tree_iter).get_indices()[0]) + 1

        # Remove the torrent from self.model.torrent_list
        for torrent in self.model.torrent_list:
            if torrent.id == index:
                return torrent

        return False

    def on_selection_changed(self, selection):
        logger.debug(
            "Notebook selection changed",
            extra={"class_name": self.__class__.__name__},
        )
        model, iter = selection.get_selected()
        if iter is not None:
            self.selected_path = model.get_path(iter)

        if self.selected_path is None:
            return

        if iter is None:
            return

        torrent = model.get_path(iter).get_indices()[0]
        if torrent is not None:
            self.update_notebook_status(torrent)
            self.update_notebook_options(torrent)
            self.update_notebook_peers(torrent)

    def update_notebook_peers(self, id):
        logger.info(
            "Notebook update peers",
            extra={"class_name": self.__class__.__name__},
        )
        torrent = self.model.get_liststore_item(id)

        store = self.peers_treeview.get_model()

        if store is None:
            store = Gtk.ListStore(str, str, float, float, float)
            self.peers_treeview.set_model(store)

        num_rows = len(store)
        num_peers = len(torrent.get_seeder().peers)

        if num_rows != num_peers:
            store.clear()

            for peer in torrent.get_seeder().peers:
                client = (
                    torrent.get_seeder().clients[peer]
                    if peer in torrent.get_seeder().clients
                    else ""
                )
                row = [str(peer), client, 0.0, 0.0, 0.0]
                store.append(row)

            self.peers_treeview.set_model(store)

    def update_notebook_options(self, torrent):
        grid = self.builder.get_object("options_grid")

        for child in self.options_grid_children:
            grid.remove(child)
            child.unparent()
        self.options_grid_children = []

        source = None
        for torrent_obj in self.model.torrent_list:
            if torrent_obj.id == torrent + 1:
                source = torrent_obj
                break

        def on_value_changed(widget, *args):
            attribute = args[-1]
            if isinstance(widget, Gtk.Switch):
                value = widget.get_active()
            else:
                adjustment = widget.get_adjustment()
                value = adjustment.get_value()
            setattr(source, attribute, value)
            source.emit("attribute-changed", source, {attribute: value})

        row = 0
        for index, attribute in enumerate(self.settings.editwidgets):
            col = 0 if index % 2 == 0 else 2

            widget_type = self.settings.editwidgets[attribute]
            widget_class = eval(widget_type)
            dynamic_widget = widget_class()
            dynamic_widget.set_visible(True)
            dynamic_widget.set_hexpand(True)
            if isinstance(dynamic_widget, Gtk.Switch):
                dynamic_widget.set_active(getattr(source, attribute))
                # Connect "state-set" signal for Gtk.Switch
                dynamic_widget.connect("state-set", on_value_changed, attribute)
            else:
                adjustment = Gtk.Adjustment(
                    value=getattr(source, attribute),
                    upper=getattr(source, attribute) * 10,
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

        compatible_attributes, store = self.model.get_liststore()

        if self.status_grid_child is not None:
            self.status_tab.remove(self.status_grid_child)
            self.status_grid_child.unparent()

        self.status_grid_child = Gtk.Grid()
        self.status_grid_child.set_column_spacing(10)
        self.status_grid_child.set_hexpand(True)
        self.status_grid_child.set_vexpand(True)
        self.status_grid_child.set_visible(True)

        # Create columns and add them to the TreeView
        for attribute_index, attribute in enumerate(compatible_attributes):
            row = attribute_index

            labeln = Gtk.Label(label=attribute, xalign=0)
            labeln.set_visible(True)
            # labeln.set_margin_left(10)
            labeln.set_halign(Gtk.Align.START)
            labeln.set_size_request(80, -1)
            self.status_grid_child.attach(labeln, 0, row, 1, 1)

            selected_iter = store.get_iter(self.selected_path)
            val = str(store.get_value(selected_iter, attribute_index))
            labelv = Gtk.Label(label=val, xalign=0)
            labelv.set_visible(True)
            # labelv.set_margin_left(10)
            labelv.set_halign(Gtk.Align.START)
            labeln.set_size_request(280, -1)
            labelv.set_selectable(True)  # Enable text selection
            self.status_grid_child.attach(labelv, 1, row, 1, 1)

        self.status_tab.append(self.status_grid_child)

    def update_view(self, model, _, torrent, attribute):
        pass

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Notebook settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)
