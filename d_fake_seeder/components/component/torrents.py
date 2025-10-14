import time

import gi

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.model.attributes import Attributes
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin
from d_fake_seeder.lib.util.helpers import add_kb, add_percent, convert_seconds_to_hours_mins_seconds, humanbytes

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")
from gi.repository import Gio  # noqa: E402
from gi.repository import GLib, GObject, Gtk  # noqa: E402


class Torrents(Component, ColumnTranslationMixin):
    def __init__(self, builder, model):
        logger.debug("Torrents.__init__() started", "Torrents")
        super().__init__()
        ColumnTranslationMixin.__init__(self)
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
        self.settings = AppSettings.get_instance()
        # Store handler ID so we can block it during column toggling to prevent deadlock
        self._attribute_handler_id = self.settings.connect("attribute-changed", self.handle_attribute_changed)
        # Load UI margin and spacing settings
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.ui_margin_small = ui_settings.get("ui_margin_small", 1)
        self.ui_margin_medium = ui_settings.get("ui_margin_medium", 8)
        self.torrents_columnview = self.builder.get_object("columnview1")
        logger.debug("Basic initialization completed (took ms)", "Torrents")
        # Create a gesture recognizer
        gesture_start = time.time()
        gesture = Gtk.GestureClick.new()
        gesture.connect("released", self.main_menu)
        gesture.set_button(3)
        # Create an action group
        self.action_group = Gio.SimpleActionGroup()
        self.stateful_actions = {}
        # Insert the action group into the window
        self.window.insert_action_group("app", self.action_group)
        # Attach the gesture to the columnView
        self.torrents_columnview.add_controller(gesture)
        gesture_end = time.time()
        logger.debug(
            f"Gesture and action setup completed (took {(gesture_end - gesture_start)*1000:.1f}ms)", "Torrents"
        )
        # ordering, sorting etc
        self.torrents_columnview.set_reorderable(True)
        self.torrents_columnview.set_show_column_separators(True)
        self.torrents_columnview.set_show_row_separators(True)
        # Enable keyboard navigation
        self.torrents_columnview.set_can_focus(True)
        self.torrents_columnview.set_focusable(True)
        # Add keyboard event controller for arrow key navigation
        self.keyboard_controller = Gtk.EventControllerKey.new()
        self.keyboard_controller.connect("key-pressed", self.on_key_pressed)
        self.torrents_columnview.add_controller(self.keyboard_controller)
        logger.debug("UI setup completed (took ms)", "Torrents")
        logger.debug("About to call update_columns()", "Torrents")
        self.update_columns()
        logger.debug("update_columns() completed (took {(columns_end - columns_start)*1000:.1f}ms)", "Torrents")
        logger.debug("Torrents.__init__() TOTAL TIME: ms", "Torrents")

    def _(self, text):
        """Get translation function from model's TranslationManager"""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def main_menu(self, gesture, n_press, x, y):
        rect = self.torrents_columnview.get_allocation()
        rect.width = 0
        rect.height = 0
        rect.x = x
        rect.y = y
        ATTRIBUTES = Attributes
        attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
        menu = Gio.Menu.new()
        # Create submenus
        queue_submenu = Gio.Menu()
        queue_submenu.append(self._("Top"), "app.queue_top")
        queue_submenu.append(self._("Up"), "app.queue_up")
        queue_submenu.append(self._("Down"), "app.queue_down")
        queue_submenu.append(self._("Bottom"), "app.queue_bottom")
        # Add menu items and submenus to the main menu
        menu.append(self._("Pause"), "app.pause")
        menu.append(self._("Resume"), "app.resume")
        menu.append(self._("Update Tracker"), "app.update_tracker")
        menu.append_submenu(self._("Queue"), queue_submenu)
        columns_menu = Gio.Menu.new()
        # Build a mapping from column objects to their attribute names (not translated titles!)
        # Use the tracking dict we maintain for translations
        column_to_attr = {}
        if self.torrents_columnview in self._translatable_columns:
            for col, prop_name, col_type in self._translatable_columns[self.torrents_columnview]:
                column_to_attr[col] = prop_name

        # Get list of visible column attribute names
        visible_column_attrs = set()
        for column in self.torrents_columnview.get_columns():
            if column.get_visible():
                # Use our tracking dict to get the attribute name
                attr_name = column_to_attr.get(column, None)
                if attr_name:
                    visible_column_attrs.add(attr_name)

        # Create or update stateful actions for each attribute
        for attribute in attributes:
            # Check if this attribute's column is visible
            state = attribute in visible_column_attrs
            if attribute not in self.stateful_actions.keys():
                # Create new action
                self.stateful_actions[attribute] = Gio.SimpleAction.new_stateful(
                    f"toggle_{attribute}",
                    None,
                    GLib.Variant.new_boolean(state),
                )
                self.stateful_actions[attribute].connect("change-state", self.on_stateful_action_change_state)
                self.action_group.add_action(self.stateful_actions[attribute])
            else:
                # Update existing action state to match current column visibility
                self.stateful_actions[attribute].set_state(GLib.Variant.new_boolean(state))
        # Iterate over attributes and add toggle items for each one
        for attribute in attributes:
            # Use translated column name for menu items
            from lib.util.column_translations import ColumnTranslations

            translated_name = ColumnTranslations.get_column_title("torrent", attribute)
            toggle_item = Gio.MenuItem.new(label=translated_name)
            toggle_item.set_detailed_action(f"app.toggle_{attribute}")
            columns_menu.append_item(toggle_item)
        menu.append_submenu(self._("Columns"), columns_menu)
        self.popover = Gtk.PopoverMenu().new_from_model(menu)
        self.popover.set_parent(self.torrents_columnview)
        self.popover.set_has_arrow(False)
        self.popover.set_halign(Gtk.Align.START)
        self.popover.set_pointing_to(rect)
        self.popover.popup()

    def on_stateful_action_change_state(self, action, value):
        logger.info("🔵 COLUMN TOGGLE: START", extra={"class_name": self.__class__.__name__})

        # Prevent re-entry if this handler is triggered by settings changes
        if hasattr(self, "_updating_columns") and self._updating_columns:
            logger.info("🔵 COLUMN TOGGLE: RE-ENTRY DETECTED, SKIPPING", extra={"class_name": self.__class__.__name__})
            return

        try:
            self._updating_columns = True
            logger.info("🔵 COLUMN TOGGLE: Set _updating_columns flag", extra={"class_name": self.__class__.__name__})

            logger.info(
                f"🔵 COLUMN TOGGLE: Action={action.get_name()}, Value={value.get_boolean()}",
                extra={"class_name": self.__class__.__name__},
            )
            self.stateful_actions[action.get_name()[len("toggle_") :]].set_state(  # noqa: E203
                GLib.Variant.new_boolean(value.get_boolean())
            )
            logger.info("🔵 COLUMN TOGGLE: Action state updated", extra={"class_name": self.__class__.__name__})

            checked_items = []
            all_unchecked = True
            ATTRIBUTES = Attributes
            attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
            column_titles = [column if column != "#" else "id" for column in attributes]
            logger.info(
                f"🔵 COLUMN TOGGLE: Total attributes={len(attributes)}", extra={"class_name": self.__class__.__name__}
            )

            for title in column_titles:
                for k, v in self.stateful_actions.items():
                    if k == title and v.get_state().get_boolean():
                        checked_items.append(title)
                        all_unchecked = False
                        break
            logger.info(
                f"🔵 COLUMN TOGGLE: Checked items={checked_items}", extra={"class_name": self.__class__.__name__}
            )

            # Update column visibility FIRST, before saving to settings
            # This prevents the settings save from triggering signals that query the ColumnView
            # while we're still in the middle of processing the menu action
            visible_set = set(checked_items) if checked_items else set(attributes)
            logger.info(f"🔵 COLUMN TOGGLE: Visible set={visible_set}", extra={"class_name": self.__class__.__name__})

            # If all unchecked, update all stateful actions to checked (since all columns will be visible)
            if all_unchecked:
                logger.info(
                    "🔵 COLUMN TOGGLE: All unchecked, setting all actions to True",
                    extra={"class_name": self.__class__.__name__},
                )
                for title in column_titles:
                    if title in self.stateful_actions:
                        self.stateful_actions[title].set_state(GLib.Variant.new_boolean(True))

            # Build reverse mapping: column object -> property_name (attribute)
            logger.info("🔵 COLUMN TOGGLE: Building column mapping...", extra={"class_name": self.__class__.__name__})
            column_to_attr = {}
            if self.torrents_columnview in self._translatable_columns:
                for col, prop_name, col_type in self._translatable_columns[self.torrents_columnview]:
                    column_to_attr[col] = prop_name
            logger.info(
                f"🔵 COLUMN TOGGLE: Column mapping built, {len(column_to_attr)} columns",
                extra={"class_name": self.__class__.__name__},
            )

            logger.info(
                "🔵 COLUMN TOGGLE: About to call get_columns()...", extra={"class_name": self.__class__.__name__}
            )
            columns = self.torrents_columnview.get_columns()
            logger.info(
                f"🔵 COLUMN TOGGLE: get_columns() returned {len(columns)} columns",
                extra={"class_name": self.__class__.__name__},
            )

            for idx, column in enumerate(columns):
                logger.info(
                    f"🔵 COLUMN TOGGLE: Processing column {idx}...", extra={"class_name": self.__class__.__name__}
                )
                # Get the attribute name from our tracking dict (not the translated title!)
                column_id = column_to_attr.get(column, None)
                if column_id is None:
                    logger.info(
                        f"🔵 COLUMN TOGGLE: Column {idx} not in mapping, getting title...",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Fallback: try to extract from title if not registered
                    title = column.get_title()
                    logger.info(
                        f"🔵 COLUMN TOGGLE: Column {idx} title={title}", extra={"class_name": self.__class__.__name__}
                    )
                    column_id = "id" if title == "#" else title
                logger.info(
                    f"🔵 COLUMN TOGGLE: Column {idx} id={column_id}, setting visibility...",
                    extra={"class_name": self.__class__.__name__},
                )
                column.set_visible(column_id in visible_set or not checked_items)
                logger.info(
                    f"🔵 COLUMN TOGGLE: Column {idx} visibility set", extra={"class_name": self.__class__.__name__}
                )

            logger.info(
                "🔵 COLUMN TOGGLE: All column visibility updated", extra={"class_name": self.__class__.__name__}
            )

            # Now save to settings AFTER column visibility is updated
            # CRITICAL: Block the attribute-changed signal handler to prevent re-entry
            # The signal handler calls get_sorter() which can deadlock during menu processing
            logger.info(
                "🔵 COLUMN TOGGLE: About to block signal handler...", extra={"class_name": self.__class__.__name__}
            )
            if hasattr(self, "_attribute_handler_id"):
                self.settings.handler_block(self._attribute_handler_id)
                logger.info("🔵 COLUMN TOGGLE: Signal handler blocked", extra={"class_name": self.__class__.__name__})
            else:
                logger.warning(
                    "🔵 COLUMN TOGGLE: No _attribute_handler_id found!", extra={"class_name": self.__class__.__name__}
                )

            try:
                logger.info(
                    "🔵 COLUMN TOGGLE: About to save settings...", extra={"class_name": self.__class__.__name__}
                )
                if all_unchecked or len(checked_items) == len(attributes):
                    logger.info("🔵 COLUMN TOGGLE: Saving empty columns", extra={"class_name": self.__class__.__name__})
                    self.settings.columns = ""
                else:
                    checked_items.sort(key=lambda x: column_titles.index(x))
                    columns_str = ",".join(checked_items)
                    logger.info(
                        f"🔵 COLUMN TOGGLE: Saving columns={columns_str}", extra={"class_name": self.__class__.__name__}
                    )
                    self.settings.columns = columns_str
                logger.info("🔵 COLUMN TOGGLE: Settings saved", extra={"class_name": self.__class__.__name__})
            finally:
                # Unblock the handler
                logger.info(
                    "🔵 COLUMN TOGGLE: About to unblock signal handler...",
                    extra={"class_name": self.__class__.__name__},
                )
                if hasattr(self, "_attribute_handler_id"):
                    self.settings.handler_unblock(self._attribute_handler_id)
                    logger.info(
                        "🔵 COLUMN TOGGLE: Signal handler unblocked", extra={"class_name": self.__class__.__name__}
                    )
        finally:
            logger.info(
                "🔵 COLUMN TOGGLE: Clearing _updating_columns flag", extra={"class_name": self.__class__.__name__}
            )
            self._updating_columns = False
            logger.info("🔵 COLUMN TOGGLE: COMPLETE", extra={"class_name": self.__class__.__name__})

    def update_columns(self):
        logger.debug("update_columns() started", "Torrents")
        # ULTRA-FAST STARTUP: Create minimal columns for immediate display
        # Defer full column creation to background task
        # Only create the ID column initially for basic functionality
        existing_columns = {col.get_title(): col for col in self.torrents_columnview.get_columns()}
        # Ensure ID column exists for basic functionality
        if "#" not in existing_columns:
            logger.debug("Creating minimal ID column for immediate display", "Torrents")
            # Step 1: Create column
            id_column = Gtk.ColumnViewColumn()
            id_column.set_resizable(True)
            logger.debug("Step 1 - Column creation: ms", "Torrents")
            # Step 2: Factory setup
            column_factory = Gtk.SignalListItemFactory()
            column_factory.connect("setup", self.setup_column_factory, "id")
            column_factory.connect("bind", self.bind_column_factory, "id")
            id_column.set_factory(column_factory)
            logger.debug("Step 2 - Factory setup: ms", "Torrents")
            # Step 3: Sorter setup
            try:
                id_expression = Gtk.PropertyExpression.new(Attributes, None, "id")
                id_sorter = Gtk.NumericSorter.new(id_expression)
                id_column.set_sorter(id_sorter)
            except Exception:
                pass
            logger.debug("Step 3 - Sorter setup: ms", "Torrents")
            # Step 4: Append to columnview
            self.torrents_columnview.append_column(id_column)
            logger.debug("Step 4 - Append column: ms", "Torrents")
            # Step 5: Register for translation
            self.register_translatable_column(self.torrents_columnview, id_column, "id", "torrent")
            logger.debug("Step 5 - Translation registration: {(step5_end - step5_start)*1000:.1f}ms", "Torrents")
        logger.debug("Minimal column setup completed (took {(minimal_end - minimal_start)*1000:.1f}ms)", "Torrents")

        # Schedule full column creation in background using GLib.idle_add
        def create_remaining_columns():
            return self._create_remaining_columns_background()

        GLib.idle_add(create_remaining_columns)
        logger.debug("update_columns() IMMEDIATE RETURN: ms", "Torrents")

    def _create_remaining_columns_background(self):
        """Create remaining columns in background to avoid blocking startup"""
        logger.debug("Starting background column creation", "Torrents")
        try:
            # Get all attributes
            ATTRIBUTES = Attributes
            attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
            attributes.remove("id")
            attributes.insert(0, "id")
            # Parse visible columns
            visible_columns = self.settings.columns.split(",") if self.settings.columns.strip() else []
            if not visible_columns:
                visible_columns = attributes
            visible_set = set(visible_columns)
            existing_columns = {col.get_title(): col for col in self.torrents_columnview.get_columns()}
            # Create remaining columns
            created_count = 0
            for attribute in attributes:
                if attribute == "id":
                    continue  # Already created
                column_title = attribute
                if column_title not in existing_columns:
                    # Create column with minimal overhead
                    column = Gtk.ColumnViewColumn()
                    column.set_resizable(True)
                    # Factory setup
                    column_factory = Gtk.SignalListItemFactory()
                    column_factory.connect("setup", self.setup_column_factory, attribute)
                    column_factory.connect("bind", self.bind_column_factory, attribute)
                    column.set_factory(column_factory)
                    # Property and sorter setup
                    try:
                        prop = Attributes.find_property(attribute)
                        attribute_type = prop.value_type.fundamental if prop else GObject.TYPE_STRING
                        attribute_expression = Gtk.PropertyExpression.new(Attributes, None, attribute)
                        if attribute_type == GObject.TYPE_STRING:
                            sorter = Gtk.StringSorter.new(attribute_expression)
                        else:
                            sorter = Gtk.NumericSorter.new(attribute_expression)
                        column.set_sorter(sorter)
                    except Exception:
                        pass
                    self.torrents_columnview.append_column(column)
                    # Translation registration
                    self.register_translatable_column(self.torrents_columnview, column, attribute, "torrent")
                    created_count += 1
                # Set visibility
                column = (
                    self.torrents_columnview.get_columns()[-1]
                    if created_count > 0
                    else existing_columns.get(column_title)
                )
                if column:
                    column.set_visible(attribute in visible_set)
            logger.debug(f"Background column creation completed: {created_count} columns", "Torrents")
        except Exception:
            logger.debug("Background column creation error:", "Torrents")
        return False  # Don't repeat this idle task

    def setup_column_factory(self, factory, item, attribute):
        # PERFORMANCE FIX: Remove GLib.idle_add() bottleneck - execute immediately
        # Create and configure the appropriate widget based on the attribute
        renderers = self.settings.cellrenderers
        widget = None
        if attribute in renderers:
            # If using a custom renderer
            widget_string = renderers[attribute]
            widget_class = eval(widget_string)
            widget = widget_class()
            widget.set_margin_top(self.ui_margin_small)
            widget.set_margin_bottom(self.ui_margin_small)
            widget.set_margin_start(self.ui_margin_small)
            widget.set_margin_end(self.ui_margin_small)
            widget.set_vexpand(True)
            # Set minimum height for progress bars to make them more visible
            if isinstance(widget, Gtk.ProgressBar):
                # Remove size constraints that might conflict with CSS
                widget.set_valign(Gtk.Align.FILL)  # Fill available space
                widget.set_vexpand(True)  # Allow vertical expansion
                # Add CSS styling to make progress bar more prominent
                widget.add_css_class("thick-progress-bar")
                # Set margin to give more breathing room
                widget.set_margin_top(self.ui_margin_medium)
                widget.set_margin_bottom(self.ui_margin_medium)
        else:
            # Default widget (e.g., Gtk.Label)
            widget = Gtk.Label()
            widget.set_hexpand(True)  # Make the widget expand horizontally
            widget.set_halign(Gtk.Align.START)  # Align text to the left
            widget.set_vexpand(True)
        # Set the child widget for the item
        item.set_child(widget)

    def bind_column_factory(self, factory, item, attribute):
        # PERFORMANCE FIX: Remove GLib.idle_add() bottleneck - execute immediately
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
                item_data.bind_property(
                    attribute,
                    widget,
                    "fraction",
                    GObject.BindingFlags.SYNC_CREATE,
                )
            # Add more cases for other widget types as needed

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

    def set_model(self, model):
        """Set the model for the torrents component."""
        logger.info("Torrents set_model", extra={"class_name": self.__class__.__name__})
        self.model = model
        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.model.connect("language-changed", self.on_language_changed)
                logger.debug(
                    "Successfully connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.error(
                    f"FAILED to connect to language-changed signal: {e}", extra={"class_name": self.__class__.__name__}
                )
        # Update the view if model is set
        if self.model:
            self.update_model()

    def update_model(self):
        # Use filtered liststore if search is active
        if hasattr(self.model, "get_filtered_liststore"):
            self.store = self.model.get_filtered_liststore()
        else:
            self.store = self.model.get_liststore()
        self.sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        self.sort_model = Gtk.SortListModel.new(self.store, self.sorter)
        self.selection = Gtk.SingleSelection.new(self.sort_model)
        # Connect to the notify::selected signal which fires when selection changes
        try:
            self.selection.connect("notify::selected", self.on_selection_changed)
        except Exception as e:
            logger.error(f"Failed to connect notify::selected signal: {e}")
            # Try alternative signal names
            try:
                self.selection.connect("selection-changed", self.on_selection_changed_old)
                logger.info("Connected to selection-changed signal as fallback")
            except Exception as e2:
                logger.error(f"All signal connections failed: {e2}")
        self.torrents_columnview.set_model(self.selection)
        # Auto-select the first torrent if available
        if self.sort_model.get_n_items() > 0:
            logger.info(
                "Auto-selecting first torrent",
                extra={"class_name": self.__class__.__name__},
            )
            self.selection.set_selected(0)

            # Use idle to defer the manual emission until after all components are initialized
            # This fixes the issue where details show "Unknown" on first load
            def emit_selection_after_idle():
                item = self.sort_model.get_item(0)
                if item and self.model:
                    logger.info(
                        f"Manually emitting selection-changed for first torrent: {item.name}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.model.emit("selection-changed", self.model, item)
                return False  # Don't repeat

            # Use idle to ensure components are ready
            GLib.idle_add(emit_selection_after_idle)

    # Method to update the ColumnView with compatible attributes
    def update_view(self, model, torrent, updated_attributes):
        logger.info(
            f"📺 VIEW RECEIVED SIGNAL: torrent={getattr(torrent, 'name', 'Unknown') if torrent else 'None'}, "
            f"attributes={updated_attributes}",
            extra={"class_name": self.__class__.__name__},
        )
        self.model = model
        # Check if this is a filter update
        if updated_attributes == "filter":
            logger.debug(
                "Filter update detected - refreshing model",
                extra={"class_name": self.__class__.__name__},
            )
            self.update_model()
            return
        # Check if the model is initialized
        current_model = self.torrents_columnview.get_model()
        if current_model is None:
            logger.info(
                "📺 VIEW: No current model, initializing with update_model()",
                extra={"class_name": self.__class__.__name__},
            )
            self.update_model()
        else:
            logger.info(
                "📺 VIEW: Column view has model, torrent update should be visible",
                extra={"class_name": self.__class__.__name__},
            )

    def on_selection_changed(self, selection, pspec):
        selected_position = selection.get_selected()
        logger.debug(f"Torrent selection changed to position {selected_position}")
        # Get the selected item from SingleSelection
        selected_item = selection.get_selected_item()
        if selected_item is not None:
            self.model.emit(
                "selection-changed",
                self.model,
                selected_item,
            )
        else:
            # No selection - emit with None to trigger hide of bottom pane
            self.model.emit(
                "selection-changed",
                self.model,
                None,
            )

    def on_selection_changed_old(self, selection, position, item):
        """Fallback method for old selection-changed signal."""
        logger.debug(f"Torrent selection changed at position {position}")
        # Get the selected item from SingleSelection
        selected_item = selection.get_selected_item()
        if selected_item is not None:
            self.model.emit(
                "selection-changed",
                self.model,
                selected_item,
            )
        else:
            # No selection - emit with None to trigger hide of bottom pane
            self.model.emit(
                "selection-changed",
                self.model,
                None,
            )

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        sorter.changed(0)

    def handle_attribute_changed(self, source, key, value):
        logger.info(
            f"🔴 ATTRIBUTE CHANGED: key={key}, value={value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Skip if we're in the middle of a column toggle operation
        if hasattr(self, "_updating_columns") and self._updating_columns:
            logger.info(
                "🔴 ATTRIBUTE CHANGED: Skipping due to _updating_columns flag",
                extra={"class_name": self.__class__.__name__},
            )
            return

        logger.info(
            "🔴 ATTRIBUTE CHANGED: About to call get_sorter()...", extra={"class_name": self.__class__.__name__}
        )
        sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        logger.info(
            "🔴 ATTRIBUTE CHANGED: get_sorter() returned, calling changed(0)...",
            extra={"class_name": self.__class__.__name__},
        )
        sorter.changed(0)
        logger.info("🔴 ATTRIBUTE CHANGED: COMPLETE", extra={"class_name": self.__class__.__name__})

    def on_key_pressed(self, controller, keyval, keycode, state):
        """Handle keyboard events for navigation"""
        from gi.repository import Gdk

        # Get current selection
        current_position = self.selection.get_selected()
        total_items = self.sort_model.get_n_items()
        if total_items == 0:
            return False
        # Handle Up arrow key
        if keyval == Gdk.KEY_Up:
            if current_position > 0:
                self.selection.set_selected(current_position - 1)
            return True  # Event handled
        # Handle Down arrow key
        elif keyval == Gdk.KEY_Down:
            if current_position < total_items - 1:
                self.selection.set_selected(current_position + 1)
            return True  # Event handled
        # Handle Home key
        elif keyval == Gdk.KEY_Home:
            self.selection.set_selected(0)
            return True  # Event handled
        # Handle End key
        elif keyval == Gdk.KEY_End:
            self.selection.set_selected(total_items - 1)
            return True  # Event handled
        # Let other keys pass through
        return False

    def model_selection_changed(self, source, model, torrent):
        logger.debug(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
