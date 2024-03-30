import time

import gi
from lib.logger import logger
from lib.settings import Settings
from lib.torrent.attributes import Attributes
from lib.util.helpers import (
    add_kb,
    add_percent,
    convert_seconds_to_hours_mins_seconds,
    humanbytes,
)

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GLib, Gtk, Pango  # noqa


class Torrents:
    def __init__(self, builder, model):
        logger.info(
            "Torrents view startup",
            extra={"class_name": self.__class__.__name__},
        )
        self.builder = builder
        self.model = model

        # window
        self.window = self.builder.get_object("main_window")

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.sort_column = None
        self.sort_order = None
        self.selection = None
        self.selected_path = None
        self.last_selected_call_time = time.time()
        self.last_row_call_time = time.time()

        self.torrents_treeview = self.builder.get_object("treeview1")

        # Create a gesture recognizer
        gesture = Gtk.GestureClick.new()
        gesture.connect("released", self.column_selection_menu)
        gesture.set_button(3)

        # Create an action group
        self.action_group = Gio.SimpleActionGroup()
        self.stateful_actions = {}

        # Insert the action group into the window
        self.window.insert_action_group("app", self.action_group)

        # Attach the gesture to the TreeView
        self.torrents_treeview.add_controller(gesture)

    def column_selection_menu(self, gesture, n_press, x, y):
        rect = self.torrents_treeview.get_allocation()
        rect.width = 0
        rect.height = 0
        rect.x = x
        rect.y = y

        ATTRIBUTES = Attributes
        attributes = list(vars(ATTRIBUTES)["__annotations__"].keys())

        menu = Gio.Menu.new()

        # Check if the attribute is a column in the treeview
        column_titles = [
            "id" if column.get_title() == "#" else column.get_title()
            for column in self.torrents_treeview.get_columns()
        ]

        # Create a stateful action for each attribute
        for attribute in attributes:
            if attribute not in self.stateful_actions.keys():
                state = attribute in column_titles

                self.stateful_actions[attribute] = Gio.SimpleAction.new_stateful(
                    f"toggle_{attribute}", None, GLib.Variant.new_boolean(state)
                )
                self.stateful_actions[attribute].connect(
                    "change-state", self.on_stateful_action_change_state
                )

                self.action_group.add_action(self.stateful_actions[attribute])

        # Iterate over attributes and add toggle items for each one
        for attribute in attributes:
            toggle_item = Gio.MenuItem.new(label=f"{attribute}")
            toggle_item.set_detailed_action(f"app.toggle_{attribute}")
            menu.append_item(toggle_item)

        self.popover = Gtk.PopoverMenu().new_from_model(menu)
        self.popover.set_parent(self.torrents_treeview)
        self.popover.set_has_arrow(False)
        self.popover.set_halign(Gtk.Align.START)
        self.popover.set_pointing_to(rect)
        self.popover.popup()

    def on_stateful_action_change_state(self, action, value):
        self.stateful_actions[
            action.get_name()[len("toggle_") :]  # noqa: E203
        ].set_state(GLib.Variant.new_boolean(value.get_boolean()))

        checked_items = []
        all_unchecked = True

        ATTRIBUTES = Attributes
        attributes = list(vars(ATTRIBUTES)["__annotations__"].keys())

        column_titles = [column if column != "#" else "id" for column in attributes]

        for title in column_titles:
            for k, v in self.stateful_actions.items():
                if k == title and v.get_state().get_boolean():
                    checked_items.append(title)
                    all_unchecked = False
                    break

        if all_unchecked or len(checked_items) == len(attributes):
            self.settings.columns = ""
        else:
            checked_items.sort(key=lambda x: column_titles.index(x))
            self.settings.columns = ",".join(checked_items)

        self.update_view(self.model, None, None, "columnupdate")

    def set_model(self, model):
        self.model = model

    def format_progress_text(self, column, cell_renderer, model, iter, attribute_index):
        logger.debug(
            "Torrent view format progress",
            extra={"class_name": self.__class__.__name__},
        )
        # Get the value from the model
        value = model.get_value(iter, attribute_index)
        cell_renderer.set_property("text", f"{int(value)}%")
        cell_renderer.set_property("value", round(int(value)))

    def render_humanbytes(self, column, cell_renderer, model, iter, attribute_index):
        value = model.get_value(iter, attribute_index)
        if value is not None:
            cell_renderer.set_property("text", humanbytes(value))

    def render_seconds(self, column, cell_renderer, model, iter, attribute_index):
        value = model.get_value(iter, attribute_index)
        if value is not None:
            cell_renderer.set_property(
                "text", convert_seconds_to_hours_mins_seconds(value)
            )

    def render_kb(self, column, cell_renderer, model, iter, attribute_index):
        value = model.get_value(iter, attribute_index)
        if value is not None:
            cell_renderer.set_property("text", add_kb(value))

    def render_percent(self, column, cell_renderer, model, iter, attribute_index):
        value = model.get_value(iter, attribute_index)
        if value is not None:
            cell_renderer.set_property("text", add_percent(value))

    def update_columns(self):
        renderers = self.settings.cellrenderers
        textrenderers = self.settings.textrenderers

        compatible_attributes, _ = self.model.get_liststore()

        # Code to iterate columns of self.torrents_treeview
        for column in self.torrents_treeview.get_columns():
            column_title = column.get_title()
            column_title = "id" if column_title == "#" else column_title
            if column_title not in compatible_attributes:
                self.torrents_treeview.remove_column(column)

        for attribute_index, attribute in enumerate(compatible_attributes):
            column = Gtk.TreeViewColumn("#" if attribute == "id" else attribute)
            attribute_title = "#" if attribute == "id" else attribute
            if not any(
                col.get_title() == attribute_title
                for col in self.torrents_treeview.get_columns()
            ):
                column = Gtk.TreeViewColumn(attribute_title)
                column.set_reorderable(True)
                column.set_clickable(True)
                column.set_resizable(True)
                column.set_sort_indicator(True)
                column.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
                cell_renderer = None

                if attribute in renderers:
                    renderer_string = renderers[attribute]
                    renderer_class = eval(renderer_string)
                    cell_renderer = renderer_class()
                    column.pack_start(cell_renderer, True)
                    column.set_sort_indicator(True)
                    column.set_sort_order(Gtk.SortType.ASCENDING)
                    column.add_attribute(
                        cell_renderer,
                        "text",
                        compatible_attributes.index(attribute),
                    )
                    column.set_cell_data_func(
                        cell_renderer,
                        self.format_progress_text,
                        attribute_index,
                    )
                elif attribute in textrenderers:
                    text_renderer_func_name = textrenderers[attribute]
                    cell_renderer = Gtk.CellRendererText()
                    cell_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
                    column.pack_start(cell_renderer, True)
                    column.set_sort_indicator(True)
                    column.set_sort_order(Gtk.SortType.ASCENDING)
                    column.add_attribute(
                        cell_renderer,
                        "text",
                        compatible_attributes.index(attribute),
                    )
                    if text_renderer_func_name == "humanbytes":
                        column.set_cell_data_func(
                            cell_renderer,
                            self.render_humanbytes,
                            attribute_index,
                        )
                    elif (
                        text_renderer_func_name == "convert_seconds_to_hours_mins_seconds"
                    ):
                        column.set_cell_data_func(
                            cell_renderer, self.render_seconds, attribute_index
                        )
                    elif text_renderer_func_name == "add_kb":
                        column.set_cell_data_func(
                            cell_renderer, self.render_kb, attribute_index
                        )
                    elif text_renderer_func_name == "add_percent":
                        column.set_cell_data_func(
                            cell_renderer, self.render_percent, attribute_index
                        )

                else:
                    cell_renderer = Gtk.CellRendererText()
                    cell_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
                    column.pack_start(cell_renderer, True)
                    column.set_sort_indicator(True)
                    column.set_sort_order(Gtk.SortType.ASCENDING)
                    column.add_attribute(
                        cell_renderer,
                        "text",
                        compatible_attributes.index(attribute),
                    )

                self.torrents_treeview.append_column(column)

    def update_columns_sorting_ordering(self):
        # Set the model for the TreeView and make them sortable
        columns = self.torrents_treeview.get_columns()
        for i, column in enumerate(columns):
            column = self.torrents_treeview.get_column(i)
            column.set_sort_column_id(i)

        if self.sort_column is not None:
            tree_model_sort = self.torrents_treeview.get_model()
            tree_model_sort.set_sort_column_id(self.sort_column, self.sort_order)

    def repopulate_model(self):
        _, store = self.model.get_liststore()
        model = self.torrents_treeview.get_model()
        model.clear()
        if model:
            for column in self.torrents_treeview.get_columns():
                self.torrents_treeview.remove_column(column)
        self.update_columns()
        self.update_columns_sorting_ordering()
        self.torrents_treeview.set_model(store)

    # Method to update the TreeView with compatible attributes
    def update_view(self, model, _, torrent, updated_attributes):
        logger.debug(
            "Torrents update view",
            extra={"class_name": self.__class__.__name__},
        )

        if updated_attributes == "columnupdate":
            self.repopulate_model()

        if torrent is None:
            return

        if isinstance(updated_attributes, dict) and len(updated_attributes.keys()) == 0:
            return

        compatible_attributes, store = [None, None]

        # Check if the model is initialized
        model = self.torrents_treeview.get_model()
        if model is None:
            self.torrents_treeview.set_model(self.model.get_liststore_model())
            model = self.torrents_treeview.get_model()

        if updated_attributes == "add":
            compatible_attributes, store = self.model.get_liststore(torrent)
            for row in store:
                new_row = [None] * len(compatible_attributes)
                for i, attr in enumerate(compatible_attributes):
                    new_row[i] = row[i]
                model.append(new_row)
            return

        if updated_attributes == "remove":
            compatible_attributes, store = self.model.get_liststore(torrent)
            filepath_column_index = compatible_attributes.index("filepath")
            for row in self.torrents_treeview:
                if row[filepath_column_index] == torrent.filepath:
                    model.remove(row.iter)
                    return

        compatible_attributes, store = self.model.get_liststore(torrent)
        self.update_columns()
        self.update_columns_sorting_ordering()

        for row in model:
            if row[compatible_attributes.index("filepath")] == torrent.filepath:
                for key, value in updated_attributes.items():
                    try:
                        row[compatible_attributes.index(key)] = value
                    except ValueError:
                        pass

    def on_selection_changed(self, selection):
        logger.debug(
            "Torrents view row selected changed",
            extra={"class_name": self.__class__.__name__},
        )
        model, iter = selection.get_selected()

        if iter is not None:
            self.selected_path = model.get_path(iter)

        if self.selected_path is None:
            return

        if iter is None:
            return

        return False

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)
