import gi
from lib.component.component import Component
from lib.logger import logger
from lib.settings import Settings
from lib.torrent.model.attributes import Attributes
from lib.util.helpers import (
    add_kb,
    add_percent,
    convert_seconds_to_hours_mins_seconds,
    humanbytes,
)

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gio, GLib, GObject, Gtk  # noqa


class Torrents(Component):

    def __init__(self, builder, model):
        logger.info(
            "Torrents view startup",
            extra={"class_name": self.__class__.__name__},
        )
        self.builder = builder
        self.model = model
        self.store = Gio.ListStore.new(Attributes)

        # window
        self.window = self.builder.get_object("main_window")

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_attribute_changed)

        self.torrents_columnview = self.builder.get_object("columnview1")

        # Create a gesture recognizer
        gesture = Gtk.GestureClick.new()
        gesture.connect("released", self.column_selection_menu)
        gesture.set_button(3)

        # Create an action group
        self.action_group = Gio.SimpleActionGroup()
        self.stateful_actions = {}

        # Insert the action group into the window
        self.window.insert_action_group("app", self.action_group)

        # Attach the gesture to the columnView
        self.torrents_columnview.add_controller(gesture)

        # ordering, sorting etc
        self.torrents_columnview.set_reorderable(True)
        self.torrents_columnview.set_show_column_separators(True)
        self.torrents_columnview.set_show_row_separators(True)

        self.update_columns()

    def column_selection_menu(self, gesture, n_press, x, y):
        rect = self.torrents_columnview.get_allocation()
        rect.width = 0
        rect.height = 0
        rect.x = x
        rect.y = y

        ATTRIBUTES = Attributes
        attributes = [
            prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)
        ]

        menu = Gio.Menu.new()

        # Check if the attribute is a visible column in the columnview
        visible_columns = [
            "id" if column.get_title() == "#" else column.get_title()
            for column in self.torrents_columnview.get_columns()
            if column.get_visible()
        ]

        # Create a stateful action for each attribute
        for attribute in attributes:
            if attribute not in self.stateful_actions.keys():
                state = attribute in visible_columns

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
        self.popover.set_parent(self.torrents_columnview)
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
        attributes = [
            prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)
        ]

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

        self.update_columns()

    def update_columns(self):
        ATTRIBUTES = Attributes
        attributes = [
            prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)
        ]

        attributes.remove("id")
        attributes.insert(0, "id")

        # Parse self.settings.columns into a list of column names
        visible_columns = (
            self.settings.columns.split(",") if self.settings.columns.strip() else []
        )

        # If the list is empty, set all columns to visible
        if not visible_columns:
            visible_columns = attributes

        # Add or update columns based on attributes
        for _, attribute in enumerate(attributes):
            column_title = "#" if attribute == "id" else attribute
            column = next(
                (
                    col
                    for col in self.torrents_columnview.get_columns()
                    if col.get_title() == column_title
                ),
                None,
            )

            if column is None:
                # Create the column if it doesn't exist
                column = Gtk.ColumnViewColumn()
                column.set_title(column_title)
                column.set_resizable(True)

                # Create a custom factory for the column
                column_factory = Gtk.SignalListItemFactory()
                column_factory.connect("setup", self.setup_column_factory, attribute)
                column_factory.connect("bind", self.bind_column_factory, attribute)
                column.set_factory(column_factory)

                # Get the type of the attribute
                attribute_type = Attributes.find_property(
                    attribute
                ).value_type.fundamental

                # Create an expression for the attribute
                attribute_expression = Gtk.PropertyExpression.new(
                    Attributes, None, attribute
                )

                # Create a sorter based on the attribute type
                if attribute_type == GObject.TYPE_STRING:
                    sorter = Gtk.StringSorter.new(attribute_expression)
                elif (
                    attribute_type == GObject.TYPE_LONG
                    or attribute_type == GObject.TYPE_BOOLEAN
                ):
                    sorter = Gtk.NumericSorter.new(attribute_expression)

                # Set the sorter on the column
                column.set_sorter(sorter)

                self.torrents_columnview.append_column(column)

            # Set the visibility of the column
            column.set_visible(attribute in visible_columns)

    def setup_column_factory(self, factory, item, attribute):
        def setup_when_idle():
            # Create and configure the appropriate widget based on the attribute
            renderers = self.settings.cellrenderers
            widget = None

            if attribute in renderers:
                # If using a custom renderer
                widget_string = renderers[attribute]
                widget_class = eval(widget_string)
                widget = widget_class()
                widget.set_margin_top(1)
                widget.set_margin_bottom(1)
                widget.set_margin_start(1)
                widget.set_margin_end(1)
                widget.set_vexpand(True)
            else:
                # Default widget (e.g., Gtk.Label)
                widget = Gtk.Label()
                widget.set_hexpand(True)  # Make the widget expand horizontally
                widget.set_halign(Gtk.Align.START)  # Align text to the left

            # Set the child widget for the item
            item.set_child(widget)

        GLib.idle_add(setup_when_idle)

    def bind_column_factory(self, factory, item, attribute):
        def bind_when_idle():
            textrenderers = self.settings.textrenderers

            # Get the widget associated with the item
            widget = item.get_child()

            # Get the item's data
            item_data = item.get_item()

            # Use appropriate widget based on the attribute
            if attribute in textrenderers:
                # If the attribute has a text renderer defined
                text_renderer_func_name = textrenderers[attribute]

                # Bind the attribute to the widget's label property
                item_data.bind_property(
                    attribute,
                    widget,
                    "label",
                    GObject.BindingFlags.SYNC_CREATE,
                    self.get_text_renderer(text_renderer_func_name),
                )
            else:
                # For non-text attributes, handle appropriately
                if isinstance(widget, Gtk.Label):
                    # Bind the attribute to the widget's label property
                    item_data.bind_property(
                        attribute,
                        widget,
                        "label",
                        GObject.BindingFlags.SYNC_CREATE,
                        self.to_str,
                    )
                elif isinstance(widget, Gtk.ProgressBar):
                    # Bind the attribute to the widget's fraction property
                    item_data.bind_property(
                        attribute, widget, "fraction", GObject.BindingFlags.SYNC_CREATE
                    )
                # Add more cases for other widget types as needed

        GLib.idle_add(bind_when_idle)

    def get_text_renderer(self, func_name):
        # Map function names to functions
        # fmt: off
        TEXT_RENDERERS = {
            "add_kb": add_kb,
            "add_percent": add_percent,
            "convert_seconds_to_hours_mins_seconds":
                convert_seconds_to_hours_mins_seconds,
            "humanbytes": humanbytes,
        }

        def text_renderer(bind, from_value):
            func = TEXT_RENDERERS[func_name]
            return func(from_value)

        return text_renderer

    def update_model(self):
        self.store = self.model.get_liststore()
        self.sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        self.sort_model = Gtk.SortListModel.new(self.store, self.sorter)
        self.selection = Gtk.SingleSelection.new(self.sort_model)
        self.selection.connect("selection-changed", self.on_selection_changed)
        self.torrents_columnview.set_model(self.selection)

    # Method to update the ColumnView with compatible attributes
    def update_view(self, model, torrent, updated_attributes):
        logger.debug(
            "Torrents update view",
            extra={"class_name": self.__class__.__name__},
        )

        self.model = model

        # Check if the model is initialized
        model = self.torrents_columnview.get_model()
        if model is None:
            self.update_model()

    def on_selection_changed(self, selection, position, item):
        item = selection.get_selected_item()
        if item is not None:
            self.model.emit("selection-changed", self.model, item)

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )

        sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        sorter.changed(0)

    def handle_attribute_changed(self, source, key, value):
        logger.debug(
            "Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

        sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        sorter.changed(0)

    def model_selection_changed(self, source, model, torrent):
        logger.debug(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
