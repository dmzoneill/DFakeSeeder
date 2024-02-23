import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Pango
import time
from lib.settings import Settings
from lib.logger import logger
from lib.torrent.attributes import Attributes
from lib.util.helpers import (
    humanbytes,
    convert_seconds_to_hours_mins_seconds,
    add_kb,
    add_percent,
)


class Torrents:
    def __init__(self, builder, model):
        logger.info(
            "Torrents view startup", extra={"class_name": self.__class__.__name__}
        )
        self.builder = builder
        self.model = model

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
        self.torrents_treeview.connect("button-press-event", self.column_selection_menu)
        self.column_selection_menu = Gtk.Menu()
        self.column_selection_menu.connect("destroy", self.destroy_menu)

    def destroy_menu(self):
        for item in self.column_selection_menu.get_children():
            self.column_selection_menu.remove(item)
            item.destroy()

    def column_selection_menu(self, widget, event):
        if event.button == 3:  # Right click
            self.update_column_menu()
            self.column_selection_menu.popup(
                None, None, None, None, event.button, event.time
            )
            self.column_selection_menu.show_all()

    def update_column_menu(self):
        ATTRIBUTES = Attributes
        attributes = list(vars(ATTRIBUTES)["__annotations__"].keys())

        self.column_selection_menu.foreach(Gtk.Widget.destroy)
        for attr in attributes:
            item = Gtk.CheckMenuItem(attr)
            if attr == "id":
                for column in self.torrents_treeview.get_columns():
                    if column.get_title() == "#":
                        item.set_active(True)
                        break
            else:
                for column in self.torrents_treeview.get_columns():
                    if column.get_title() == attr:
                        item.set_active(True)
                        break

            item.connect("toggled", self.on_column_checkbox_toggled)
            self.column_selection_menu.append(item)
        self.column_selection_menu.show_all()

    def on_column_checkbox_toggled(self, widget):
        checked_items = []
        all_unchecked = True

        ATTRIBUTES = Attributes
        attributes = list(vars(ATTRIBUTES)["__annotations__"].keys())

        column_titles = [column if column != "#" else "id" for column in attributes]

        for title in column_titles:
            if title == "#":
                title = "id"
            for item in self.column_selection_menu.get_children():
                if item.get_label() == title and item.get_active():
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
        value = model.get_value(iter, attribute_index)  # Get the value from the model
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
                        cell_renderer, "text", compatible_attributes.index(attribute)
                    )
                    column.set_cell_data_func(
                        cell_renderer, self.format_progress_text, attribute_index
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
                            cell_renderer, self.render_humanbytes, attribute_index
                        )
                    elif (
                        text_renderer_func_name
                        == "convert_seconds_to_hours_mins_seconds"
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
                        cell_renderer, "text", compatible_attributes.index(attribute)
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
            "Torrents update view", extra={"class_name": self.__class__.__name__}
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

        # Update existing model and insert or remove rows
        # for row in store:
        #     filepath_attr_index = compatible_attributes.index("filepath")
        #     filepath = row[filepath_attr_index]
        #     model_iter = model.get_iter_first()
        #     found = False
        #     while model_iter is not None:
        #         if model.get_value(model_iter, filepath_attr_index) == filepath:
        #             found = True
        #             for i, attr in enumerate(compatible_attributes):
        #                 model.set_value(model_iter, i, row[i])
        #             break
        #         model_iter = model.iter_next(model_iter)

        #     if not found:
        #         new_row = [None] * len(compatible_attributes)
        #         for i, attr in enumerate(compatible_attributes):
        #             new_row[i] = row[i]
        #         model.append(new_row)

        # # Remove rows not found in store
        # to_remove = []
        # model_iter = model.get_iter_first()
        # while model_iter is not None:
        #     if model.get_value(model_iter, filepath_attr_index) not in [
        #         row[filepath_attr_index] for row in store
        #     ]:
        #         to_remove.append(model_iter)
        #     model_iter = model.iter_next(model_iter)

        # for iter_to_remove in to_remove:
        #     model.remove(iter_to_remove)

    # # Method to update the TreeView with compatible attributes
    # def update_view(self, model, torrent, attribute):
    #     logger.debug(
    #         "Torrents update view", extra={"class_name": self.__class__.__name__}
    #     )
    #     tree_model_sort = self.torrents_treeview.get_model()
    #     if tree_model_sort is not None:
    #         prev_sort_column, prev_sort_order = tree_model_sort.get_sort_column_id()
    #         if prev_sort_column is not None and prev_sort_order is not None:
    #             self.sort_column = prev_sort_column
    #             self.sort_order = prev_sort_order

    #     compatible_attributes, store = self.model.get_liststore()

    #     if len(compatible_attributes) != len(self.torrents_treeview.get_columns()):
    #         # Clear existing columns in the TreeView
    #         for column in self.torrents_treeview.get_columns():
    #             self.torrents_treeview.remove_column(column)
    #             for cell_renderer in column.get_cell_renderers():
    #                 column.clear_attributes(cell_renderer)
    #                 column.remove(cell_renderer)
    #                 cell_renderer.destroy()
    #             column.destroy()

    #         renderers = self.settings.cellrenderers
    #         textrenderers = self.settings.textrenderers

    #         # Create columns and add them to the TreeView
    #         for attribute_index, attribute in enumerate(compatible_attributes):
    #             column = Gtk.TreeViewColumn("#" if attribute == "id" else attribute)
    #             column.set_reorderable(True)
    #             column.set_clickable(True)
    #             column.set_resizable(True)
    #             column.set_sort_indicator(True)
    #             column.set_sizing(Gtk.TreeViewColumnSizing.GROW_ONLY)
    #             cell_renderer = None

    #             if attribute in renderers:
    #                 renderer_string = renderers[attribute]
    #                 renderer_class = eval(renderer_string)
    #                 cell_renderer = renderer_class()
    #                 column.pack_start(cell_renderer, True)
    #                 column.set_sort_indicator(True)
    #                 column.set_sort_order(Gtk.SortType.ASCENDING)
    #                 column.add_attribute(
    #                     cell_renderer, "text", compatible_attributes.index(attribute)
    #                 )
    #                 column.set_cell_data_func(
    #                     cell_renderer, self.format_progress_text, attribute_index
    #                 )
    #             elif attribute in textrenderers:
    #                 text_renderer_func_name = textrenderers[attribute]
    #                 cell_renderer = Gtk.CellRendererText()
    #                 cell_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
    #                 column.pack_start(cell_renderer, True)
    #                 column.set_sort_indicator(True)
    #                 column.set_sort_order(Gtk.SortType.ASCENDING)
    #                 column.add_attribute(
    #                     cell_renderer,
    #                     "text",
    #                     compatible_attributes.index(attribute),
    #                 )
    #                 if text_renderer_func_name == "humanbytes":
    #                     column.set_cell_data_func(
    #                         cell_renderer, self.render_humanbytes, attribute_index
    #                     )
    #                 elif (
    #                     text_renderer_func_name
    #                     == "convert_seconds_to_hours_mins_seconds"
    #                 ):
    #                     column.set_cell_data_func(
    #                         cell_renderer, self.render_seconds, attribute_index
    #                     )

    #             else:
    #                 cell_renderer = Gtk.CellRendererText()
    #                 cell_renderer.set_property("ellipsize", Pango.EllipsizeMode.END)
    #                 column.pack_start(cell_renderer, True)
    #                 column.set_sort_indicator(True)
    #                 column.set_sort_order(Gtk.SortType.ASCENDING)
    #                 column.add_attribute(
    #                     cell_renderer, "text", compatible_attributes.index(attribute)
    #                 )

    #             self.torrents_treeview.append_column(column)

    #     # Set the model for the TreeView and make them sortable
    #     columns = self.torrents_treeview.get_columns()
    #     for i, column in enumerate(columns):
    #         column = self.torrents_treeview.get_column(i)
    #         column.set_sort_column_id(i)
    #     self.torrents_treeview.set_model(store)

    #     if self.sort_column is not None:
    #         tree_model_sort = self.torrents_treeview.get_model()
    #         tree_model_sort.set_sort_column_id(self.sort_column, self.sort_order)

    #     # Enable row selection
    #     self.selection = self.torrents_treeview.get_selection()
    #     self.selection.set_mode(
    #         Gtk.SelectionMode.SINGLE
    #     )  # or Gtk.SelectionMode.MULTIPLE

    #     # Connect the signals
    #     try:
    #         self.torrents_treeview.disconnect_by_func(self.on_row_activated)
    #     except:
    #         pass

    #     try:
    #         self.selection.disconnect_by_func(self.on_selection_changed)
    #     except:
    #         pass

    #     # self.torrents_treeview.connect("row-activated", self.on_row_activated)
    #     self.selection.connect("changed", self.on_selection_changed)

    #     # Reselect the previously selected item if it still exists
    #     if self.selected_path:
    #         self.selection.select_path(self.selected_path)

    # def on_row_activated(self, treeview, path, column):
    #     logger.debug(
    #         "Torrents view row activate", extra={"class_name": self.__class__.__name__}
    #     )
    #     selection = treeview.get_selection()
    #     model, iter = selection.get_selected()
    #     if iter is not None:
    #         self.selected_path = model.get_path(iter)

    #     self.selected_path = model.get_path(iter)

    #     if iter is None:
    #         return

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
