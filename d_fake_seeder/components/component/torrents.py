# fmt: off
# isort: skip_file
from typing import Any
import time

import gi

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.model.attributes import Attributes
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin
from d_fake_seeder.lib.util.column_translations import ColumnTranslations
from d_fake_seeder.lib.util.helpers import (
    add_kb,
    add_percent,
    convert_seconds_to_hours_mins_seconds,
    format_timestamp,
    humanbytes,
)

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")
from gi.repository import Gdk, Gio, GLib, GObject, Gtk, Pango  # noqa: E402

# fmt: on


class Torrents(Component, ColumnTranslationMixin):
    def __init__(self, builder: Any, model: Any) -> None:
        logger.info("Torrents.__init__() started", "Torrents")
        super().__init__()
        ColumnTranslationMixin.__init__(self)
        logger.trace(
            "Torrents view startup",
            extra={"class_name": self.__class__.__name__},
        )
        self.builder = builder
        self.model = model
        # Track selected item ID for inline editing
        self._selected_item_id = None
        self.store = Gio.ListStore.new(Attributes)
        self.track_store(self.store)  # Track for automatic cleanup
        # window
        self.window = self.builder.get_object("main_window")
        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        # Store handler ID so we can block it during column toggling to prevent deadlock
        self.track_signal(
            self.settings,
            self.settings.connect("attribute-changed", self.handle_attribute_changed),
        )
        # Load UI margin and spacing settings
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.ui_margin_small = ui_settings.get("ui_margin_small", 1)
        self.ui_margin_medium = ui_settings.get("ui_margin_medium", 8)
        self.torrents_columnview = self.builder.get_object("columnview1")
        logger.trace("Basic initialization completed (took ms)", "Torrents")
        # Create a gesture recognizer
        gesture_start = time.time()
        gesture = Gtk.GestureClick.new()
        self.track_signal(gesture, gesture.connect("released", self.main_menu))
        gesture.set_button(3)
        # Create an action group
        self.action_group = Gio.SimpleActionGroup()
        self.stateful_actions = {}  # type: ignore[var-annotated]
        # Insert the action group into the window
        self.window.insert_action_group("app", self.action_group)
        # Attach the gesture to the columnView
        self.torrents_columnview.add_controller(gesture)
        gesture_end = time.time()
        logger.trace(
            f"Gesture and action setup completed (took {(gesture_end - gesture_start)*1000:.1f}ms)",
            "Torrents",
        )
        # ordering, sorting etc
        self.torrents_columnview.set_reorderable(True)
        self.torrents_columnview.set_show_column_separators(True)
        self.torrents_columnview.set_show_row_separators(True)
        # Enable keyboard navigation
        self.torrents_columnview.set_can_focus(True)
        self.torrents_columnview.set_focusable(True)
        logger.trace("UI setup completed (took ms)", "Torrents")
        logger.trace("About to call update_columns()", "Torrents")
        self.update_columns()
        logger.trace(
            "update_columns() completed (took {(columns_end - columns_start)*1000:.1f}ms)",
            "Torrents",
        )
        logger.trace("Torrents.__init__() TOTAL TIME: ms", "Torrents")

    def _(self, text: Any) -> Any:
        """Get translation function from model's TranslationManager"""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def main_menu(self, gesture: Any, n_press: Any, x: Any, y: Any) -> Any:
        rect = self.torrents_columnview.get_allocation()
        rect.width = 0
        rect.height = 0
        rect.x = x
        rect.y = y
        ATTRIBUTES = Attributes
        attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
        menu = Gio.Menu.new()

        # Get the currently selected torrent to determine state
        selected_item = self.selection.get_selected_item() if hasattr(self, "selection") else None
        is_active = getattr(selected_item, "active", True) if selected_item else True
        progress = getattr(selected_item, "progress", 0.0) if selected_item else 0.0
        super_seeding = getattr(selected_item, "super_seeding", False) if selected_item else False
        sequential = getattr(selected_item, "sequential_download", False) if selected_item else False

        # === BASIC ACTIONS ===
        # Pause/Resume
        if is_active:
            menu.append(self._("Pause"), "app.pause")
        else:
            menu.append(self._("Resume"), "app.resume")

        # Force Start
        menu.append(self._("Force Start"), "app.force_start")

        menu.append(self._("Update Tracker"), "app.update_tracker")
        menu.append(self._("Force Recheck"), "app.force_recheck")

        # === CONTEXT-AWARE ACTIONS ===
        if progress < 1.0:
            menu.append(self._("Force Complete"), "app.force_complete")
        if progress == 0.0:
            menu.append(self._("Set Random Progress"), "app.set_random_progress")

        # === COPY SUBMENU ===
        copy_submenu = Gio.Menu()
        copy_submenu.append(self._("Copy Name"), "app.copy_name")
        copy_submenu.append(self._("Copy Info Hash"), "app.copy_hash")
        copy_submenu.append(self._("Copy Magnet Link"), "app.copy_magnet")
        copy_submenu.append(self._("Copy Tracker URL"), "app.copy_tracker")
        menu.append_submenu(self._("Copy"), copy_submenu)

        # === PRIORITY SUBMENU ===
        priority_submenu = Gio.Menu()
        priority_submenu.append(self._("High Priority"), "app.priority_high")
        priority_submenu.append(self._("Normal Priority"), "app.priority_normal")
        priority_submenu.append(self._("Low Priority"), "app.priority_low")
        menu.append_submenu(self._("Priority"), priority_submenu)

        # === SPEED LIMITS SUBMENU ===
        speed_submenu = Gio.Menu()
        speed_submenu.append(self._("Set Upload Limit..."), "app.set_upload_limit")
        speed_submenu.append(self._("Set Download Limit..."), "app.set_download_limit")
        speed_submenu.append(self._("Reset to Global Limits"), "app.reset_limits")
        menu.append_submenu(self._("Speed Limits"), speed_submenu)

        # === TRACKER MANAGEMENT SUBMENU ===
        tracker_submenu = Gio.Menu()
        tracker_submenu.append(self._("Add Tracker..."), "app.add_tracker")
        tracker_submenu.append(self._("Edit Tracker..."), "app.edit_tracker")
        tracker_submenu.append(self._("Remove Tracker..."), "app.remove_tracker")
        menu.append_submenu(self._("Trackers"), tracker_submenu)

        # === QUEUE SUBMENU ===
        queue_submenu = Gio.Menu()
        queue_submenu.append(self._("Top"), "app.queue_top")
        queue_submenu.append(self._("Up"), "app.queue_up")
        queue_submenu.append(self._("Down"), "app.queue_down")
        queue_submenu.append(self._("Bottom"), "app.queue_bottom")
        menu.append_submenu(self._("Queue"), queue_submenu)

        # === ADVANCED OPTIONS ===
        menu.append(self._("Rename..."), "app.rename_torrent")
        menu.append(self._("Set Label..."), "app.set_label")
        menu.append(self._("Set Location..."), "app.set_location")

        # Toggle options
        if super_seeding:
            menu.append(self._("Disable Super Seeding"), "app.toggle_super_seed")
        else:
            menu.append(self._("Enable Super Seeding"), "app.toggle_super_seed")

        if sequential:
            menu.append(self._("Disable Sequential Download"), "app.toggle_sequential")
        else:
            menu.append(self._("Enable Sequential Download"), "app.toggle_sequential")

        # === SEPARATOR ===
        menu.append(self._("Properties"), "app.show_properties")

        # === REMOVAL OPTIONS ===
        remove_submenu = Gio.Menu()
        remove_submenu.append(self._("Remove Torrent"), "app.remove_torrent")
        remove_submenu.append(self._("Remove Torrent and Data"), "app.remove_torrent_and_data")
        menu.append_submenu(self._("Remove"), remove_submenu)

        # Register all actions
        self._register_menu_actions()
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

    def on_stateful_action_change_state(self, action: Any, value: Any) -> None:
        logger.trace("🔵 COLUMN TOGGLE: START", extra={"class_name": self.__class__.__name__})

        # Prevent re-entry if this handler is triggered by settings changes
        if hasattr(self, "_updating_columns") and self._updating_columns:  # type: ignore[has-type]
            logger.trace(
                "🔵 COLUMN TOGGLE: RE-ENTRY DETECTED, SKIPPING",
                extra={"class_name": self.__class__.__name__},
            )
            return

        try:
            self._updating_columns = True
            logger.trace(
                "🔵 COLUMN TOGGLE: Set _updating_columns flag",
                extra={"class_name": self.__class__.__name__},
            )

            logger.trace(
                f"🔵 COLUMN TOGGLE: Action={action.get_name()}, Value={value.get_boolean()}",
                extra={"class_name": self.__class__.__name__},
            )
            self.stateful_actions[action.get_name()[len("toggle_") :]].set_state(  # noqa: E203
                GLib.Variant.new_boolean(value.get_boolean())
            )
            logger.trace(
                "🔵 COLUMN TOGGLE: Action state updated",
                extra={"class_name": self.__class__.__name__},
            )

            checked_items = []
            all_unchecked = True
            ATTRIBUTES = Attributes
            attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
            column_titles = [column if column != "#" else "id" for column in attributes]
            logger.trace(
                f"🔵 COLUMN TOGGLE: Total attributes={len(attributes)}",
                extra={"class_name": self.__class__.__name__},
            )

            for title in column_titles:
                for k, v in self.stateful_actions.items():
                    if k == title and v.get_state().get_boolean():
                        checked_items.append(title)
                        all_unchecked = False
                        break
            logger.trace(
                f"🔵 COLUMN TOGGLE: Checked items={checked_items}",
                extra={"class_name": self.__class__.__name__},
            )

            # Update column visibility FIRST, before saving to settings
            # This prevents the settings save from triggering signals that query the ColumnView
            # while we're still in the middle of processing the menu action
            # Use sensible default if all unchecked (not all 30 columns!)
            DEFAULT_COLUMNS = [
                "id",
                "name",
                "progress",
                "upload_speed",
                "download_speed",
                "seeders",
                "leechers",
                "total_size",
            ]
            visible_set = set(checked_items) if checked_items else set(DEFAULT_COLUMNS)
            logger.trace(
                f"🔵 COLUMN TOGGLE: Visible set={visible_set}",
                extra={"class_name": self.__class__.__name__},
            )

            # If all unchecked, update all stateful actions to checked (since all columns will be visible)
            if all_unchecked:
                logger.trace(
                    "🔵 COLUMN TOGGLE: All unchecked, setting all actions to True",
                    extra={"class_name": self.__class__.__name__},
                )
                for title in column_titles:
                    if title in self.stateful_actions:
                        self.stateful_actions[title].set_state(GLib.Variant.new_boolean(True))

            # Build reverse mapping: column object -> property_name (attribute)
            logger.trace(
                "🔵 COLUMN TOGGLE: Building column mapping...",
                extra={"class_name": self.__class__.__name__},
            )
            column_to_attr = {}
            if self.torrents_columnview in self._translatable_columns:
                for col, prop_name, col_type in self._translatable_columns[self.torrents_columnview]:
                    column_to_attr[col] = prop_name
            logger.trace(
                f"🔵 COLUMN TOGGLE: Column mapping built, {len(column_to_attr)} columns",
                extra={"class_name": self.__class__.__name__},
            )

            logger.trace(
                "🔵 COLUMN TOGGLE: About to call get_columns()...",
                extra={"class_name": self.__class__.__name__},
            )
            columns = self.torrents_columnview.get_columns()
            logger.trace(
                f"🔵 COLUMN TOGGLE: get_columns() returned {len(columns)} columns",
                extra={"class_name": self.__class__.__name__},
            )

            for idx, column in enumerate(columns):
                logger.trace(
                    f"🔵 COLUMN TOGGLE: Processing column {idx}...",
                    extra={"class_name": self.__class__.__name__},
                )
                # Get the attribute name from our tracking dict (not the translated title!)
                column_id = column_to_attr.get(column, None)
                if column_id is None:
                    logger.trace(
                        f"🔵 COLUMN TOGGLE: Column {idx} not in mapping, getting title...",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Fallback: try to extract from title if not registered
                    title = column.get_title()
                    logger.trace(
                        f"🔵 COLUMN TOGGLE: Column {idx} title={title}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    column_id = "id" if title == "#" else title
                logger.trace(
                    f"🔵 COLUMN TOGGLE: Column {idx} id={column_id}, setting visibility...",
                    extra={"class_name": self.__class__.__name__},
                )
                column.set_visible(column_id in visible_set or not checked_items)
                logger.trace(
                    f"🔵 COLUMN TOGGLE: Column {idx} visibility set",
                    extra={"class_name": self.__class__.__name__},
                )

            logger.trace(
                "🔵 COLUMN TOGGLE: All column visibility updated",
                extra={"class_name": self.__class__.__name__},
            )

            # Now save to settings AFTER column visibility is updated
            # CRITICAL: Block the attribute-changed signal handler to prevent re-entry
            # The signal handler calls get_sorter() which can deadlock during menu processing
            logger.trace(
                "🔵 COLUMN TOGGLE: About to block signal handler...",
                extra={"class_name": self.__class__.__name__},
            )
            if hasattr(self, "_attribute_handler_id"):
                self.settings.handler_block(self._attribute_handler_id)
                logger.trace(
                    "🔵 COLUMN TOGGLE: Signal handler blocked",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    "🔵 COLUMN TOGGLE: No _attribute_handler_id found!",
                    extra={"class_name": self.__class__.__name__},
                )

            try:
                logger.trace(
                    "🔵 COLUMN TOGGLE: About to save settings...",
                    extra={"class_name": self.__class__.__name__},
                )
                if all_unchecked or len(checked_items) == len(attributes):
                    logger.trace(
                        "🔵 COLUMN TOGGLE: Saving empty columns",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.settings.set("columns", "")
                else:
                    checked_items.sort(key=lambda x: column_titles.index(x))
                    columns_str = ",".join(checked_items)
                    logger.trace(
                        f"🔵 COLUMN TOGGLE: Saving columns={columns_str}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.settings.set("columns", columns_str)
                logger.trace(
                    "🔵 COLUMN TOGGLE: Settings saved",
                    extra={"class_name": self.__class__.__name__},
                )
            finally:
                # Unblock the handler
                logger.trace(
                    "🔵 COLUMN TOGGLE: About to unblock signal handler...",
                    extra={"class_name": self.__class__.__name__},
                )
                if hasattr(self, "_attribute_handler_id"):
                    self.settings.handler_unblock(self._attribute_handler_id)
                    logger.trace(
                        "🔵 COLUMN TOGGLE: Signal handler unblocked",
                        extra={"class_name": self.__class__.__name__},
                    )
        finally:
            logger.trace(
                "🔵 COLUMN TOGGLE: Clearing _updating_columns flag",
                extra={"class_name": self.__class__.__name__},
            )
            self._updating_columns = False
            logger.trace(
                "🔵 COLUMN TOGGLE: COMPLETE",
                extra={"class_name": self.__class__.__name__},
            )

    def update_columns(self) -> Any:
        logger.info("update_columns() started", "Torrents")
        # ULTRA-FAST STARTUP: Create minimal columns for immediate display
        # Defer full column creation to background task
        # Only create the ID column initially for basic functionality
        existing_columns = {col.get_title(): col for col in self.torrents_columnview.get_columns()}
        # Ensure ID column exists for basic functionality
        if "#" not in existing_columns:
            logger.trace("Creating minimal ID column for immediate display", "Torrents")
            # Step 1: Create column
            id_column = Gtk.ColumnViewColumn()
            id_column.set_resizable(True)
            id_column.set_expand(True)  # Fill available space
            logger.trace("Step 1 - Column creation: ms", "Torrents")
            # Step 2: Factory setup
            column_factory = Gtk.SignalListItemFactory()
            self.track_signal(
                column_factory,
                column_factory.connect("setup", self.setup_column_factory, "id"),
            )
            self.track_signal(
                column_factory,
                column_factory.connect("bind", self.bind_column_factory, "id"),
            )
            id_column.set_factory(column_factory)
            logger.trace("Step 2 - Factory setup: ms", "Torrents")
            # Step 3: Sorter setup
            try:
                id_expression = Gtk.PropertyExpression.new(Attributes, None, "id")
                id_sorter = Gtk.NumericSorter.new(id_expression)
                id_column.set_sorter(id_sorter)
            except Exception:
                pass
            logger.trace("Step 3 - Sorter setup: ms", "Torrents")
            # Step 4: Append to columnview
            self.torrents_columnview.append_column(id_column)
            logger.trace("Step 4 - Append column: ms", "Torrents")
            # Step 5: Register for translation
            self.register_translatable_column(self.torrents_columnview, id_column, "id", "torrent")
            logger.trace(
                "Step 5 - Translation registration: {(step5_end - step5_start)*1000:.1f}ms",
                "Torrents",
            )
        logger.trace(
            "Minimal column setup completed (took {(minimal_end - minimal_start)*1000:.1f}ms)",
            "Torrents",
        )

        # Schedule full column creation in background using GLib.idle_add
        def create_remaining_columns() -> Any:
            return self._create_remaining_columns_background()

        GLib.idle_add(create_remaining_columns)
        logger.trace("update_columns() IMMEDIATE RETURN: ms", "Torrents")

    def _create_remaining_columns_background(self) -> Any:
        """Create remaining columns in background to avoid blocking startup"""
        logger.trace("Starting background column creation", "Torrents")
        try:
            # Get all attributes
            ATTRIBUTES = Attributes
            attributes = [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
            attributes.remove("id")
            attributes.insert(0, "id")
            # Parse visible columns - use sensible default if empty (not all 30 columns!)
            DEFAULT_COLUMNS = [
                "id",
                "name",
                "progress",
                "upload_speed",
                "download_speed",
                "seeders",
                "leechers",
                "total_size",
            ]
            visible_columns = self.settings.columns.split(",") if self.settings.columns.strip() else []
            if not visible_columns:
                visible_columns = DEFAULT_COLUMNS
            visible_set = set(visible_columns)
            existing_columns = {col.get_title(): col for col in self.torrents_columnview.get_columns()}
            # Create all columns, set visibility based on settings
            created_count = 0
            for attribute in attributes:
                if attribute == "id":
                    continue  # Already created
                column_title = attribute
                if column_title not in existing_columns:
                    # Create column with minimal overhead
                    column = Gtk.ColumnViewColumn()
                    column.set_resizable(True)
                    # Allow columns to expand and fill available space
                    column.set_expand(True)
                    # Factory setup
                    column_factory = Gtk.SignalListItemFactory()
                    self.track_signal(
                        column_factory,
                        column_factory.connect("setup", self.setup_column_factory, attribute),
                    )
                    self.track_signal(
                        column_factory,
                        column_factory.connect("bind", self.bind_column_factory, attribute),
                    )
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
            logger.trace(
                f"Background column creation completed: {created_count} columns",
                "Torrents",
            )
        except Exception:
            logger.error("Background column creation error:", "Torrents")
        return False  # Don't repeat this idle task  # type: ignore

    def _create_edit_widget(self, attribute: Any, widget_type_str: Any) -> Any:
        """Create an edit widget based on type string."""
        if widget_type_str == "Gtk.SpinButton":
            adj = Gtk.Adjustment(value=0, lower=0, upper=999999, step_increment=1, page_increment=10, page_size=0)
            widget = Gtk.SpinButton(adjustment=adj)
            widget.set_editable(True)
            widget.set_can_focus(True)
            return widget
        elif widget_type_str == "Gtk.Switch":
            widget = Gtk.Switch()
            widget.set_can_focus(True)
            return widget
        elif widget_type_str == "Gtk.Entry":
            widget = Gtk.Entry()
            widget.set_can_focus(True)
            return widget
        elif widget_type_str == "Gtk.DropDown":
            options = self._get_dropdown_options(attribute)
            translated_options = self._get_translated_dropdown_options(attribute)
            string_list = Gtk.StringList.new(translated_options)
            widget = Gtk.DropDown(model=string_list)
            widget.set_can_focus(True)
            widget._options = options  # Store original English options for saving
            widget._translated_options = translated_options
            return widget
        return None

    def _get_dropdown_options(self, attribute: Any) -> Any:
        """Return dropdown options for a given attribute."""
        # Base English options (used as keys)
        options_map = {
            "priority": ["low", "normal", "high"],
        }
        return options_map.get(attribute, ["option1", "option2"])

    def _get_translated_dropdown_options(self, attribute: Any) -> Any:
        """Return translated dropdown options for display."""
        options = self._get_dropdown_options(attribute)
        # Use model's translation function if available
        translate = self._get_translate_func()
        # Translation map for dropdown options
        translation_map = {
            "low": translate("Low"),
            "normal": translate("Normal"),
            "high": translate("High"),
        }
        return [translation_map.get(opt, opt) for opt in options]

    def _get_translate_func(self) -> Any:
        """Get the translation function from model or return identity."""
        if hasattr(self, "model") and self.model:
            if hasattr(self.model, "translation_manager"):
                return self.model.translation_manager.translate_func
        return lambda x: x

    def _create_inline_stack(self, attribute: Any, display_widget: Any, edit_widget: Any) -> Any:
        """Create a Stack with display and edit children."""
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        stack.set_transition_duration(100)
        stack.add_named(display_widget, "display")
        stack.add_named(edit_widget, "edit")
        stack.set_visible_child_name("display")
        stack._display_widget = display_widget
        stack._edit_widget = edit_widget
        stack._attribute = attribute
        return stack

    def _update_visible_stacks(self, selected_id: Any) -> None:
        """Update all visible Stack widgets based on selection."""

        # Iterate through all ListItem children to find Stacks
        def update_child(widget: Any) -> None:
            if isinstance(widget, Gtk.Stack) and hasattr(widget, "_bound_item_id"):
                if widget._bound_item_id == selected_id:
                    widget.set_visible_child_name("edit")
                else:
                    widget.set_visible_child_name("display")
            # Recurse into containers
            if hasattr(widget, "get_first_child"):
                child = widget.get_first_child()
                while child:
                    update_child(child)
                    child = child.get_next_sibling()

        # Start from the ColumnView
        update_child(self.torrents_columnview)

    def setup_column_factory(self, factory: Any, item: Any, attribute: Any) -> None:
        # PERFORMANCE FIX: Remove GLib.idle_add() bottleneck - execute immediately
        # Create and configure the appropriate widget based on the attribute
        renderers = self.settings.cellrenderers
        editwidgets = getattr(self.settings, "editwidgets", {})
        widget = None

        # Create Stack for editable columns
        if attribute in editwidgets:
            widget_type = editwidgets[attribute]
            display_widget = Gtk.Label()
            display_widget.set_hexpand(True)
            display_widget.set_halign(Gtk.Align.START)
            # Enable ellipsization to prevent labels from forcing window width
            display_widget.set_ellipsize(Pango.EllipsizeMode.END)
            display_widget.set_width_chars(5)  # Minimum chars before ellipsizing
            edit_widget = self._create_edit_widget(attribute, widget_type)
            if edit_widget:
                widget = self._create_inline_stack(attribute, display_widget, edit_widget)
                widget.set_margin_top(self.ui_margin_small)
                widget.set_margin_bottom(self.ui_margin_small)
                widget.set_margin_start(self.ui_margin_small)
                widget.set_margin_end(self.ui_margin_small)
                item.set_child(widget)
                return

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
            # Enable ellipsization to prevent labels from forcing window width
            widget.set_ellipsize(Pango.EllipsizeMode.END)
            widget.set_width_chars(5)  # Minimum chars before ellipsizing
        # Set the child widget for the item
        item.set_child(widget)

    def bind_column_factory(self, factory: Any, item: Any, attribute: Any) -> None:
        # PERFORMANCE FIX: Remove GLib.idle_add() bottleneck - execute immediately
        textrenderers = self.settings.textrenderers
        editwidgets = getattr(self.settings, "editwidgets", {})

        # Get the widget associated with the item
        widget = item.get_child()
        # Get the item's data
        item_data = item.get_item()

        # Handle Stack widgets for inline editing
        if isinstance(widget, Gtk.Stack) and attribute in editwidgets:
            self._bind_inline_stack(widget, item_data, attribute, textrenderers)
            # Store bound item ID and set correct mode
            item_id = getattr(item_data, "id", None)
            widget._bound_item_id = item_id
            if item_id == self._selected_item_id:
                widget.set_visible_child_name("edit")
            else:
                widget.set_visible_child_name("display")
            return

        # Use appropriate widget based on the attribute
        if attribute in textrenderers:
            # If the attribute has a text renderer defined
            text_renderer_func_name = textrenderers[attribute]
            # Bind the attribute to the widget's label property
            binding = item_data.bind_property(
                attribute,
                widget,
                "label",
                GObject.BindingFlags.SYNC_CREATE,
                self.get_text_renderer(text_renderer_func_name),
            )
            self.track_binding(binding)
        else:
            # For non-text attributes, handle appropriately
            if isinstance(widget, Gtk.Label):
                # Bind the attribute to the widget's label property
                binding = item_data.bind_property(
                    attribute,
                    widget,
                    "label",
                    GObject.BindingFlags.SYNC_CREATE,
                    self.to_str,
                )
                self.track_binding(binding)
            elif isinstance(widget, Gtk.ProgressBar):
                binding = item_data.bind_property(
                    attribute,
                    widget,
                    "fraction",
                    GObject.BindingFlags.SYNC_CREATE,
                )
                self.track_binding(binding)
            # Add more cases for other widget types as needed

    def _bind_inline_stack(self, stack: Any, item_data: Any, attribute: Any, textrenderers: Any) -> Any:
        """Bind data to both display and edit widgets in a Stack."""
        if item_data is None:
            return

        display_widget = stack._display_widget
        edit_widget = stack._edit_widget

        # Disconnect old handlers to prevent stale closures from widget recycling
        if hasattr(edit_widget, "_handler_id") and edit_widget._handler_id:
            try:
                edit_widget.disconnect(edit_widget._handler_id)
            except Exception:
                pass
            edit_widget._handler_id = None

        # Store reference to current item for handler
        edit_widget._bound_item = item_data
        edit_widget._bound_attribute = attribute

        # Get current value
        try:
            current_value = getattr(item_data, attribute, 0)
        except Exception:
            current_value = 0

        # Bind display widget
        if attribute in textrenderers:
            text_renderer_func_name = textrenderers[attribute]
            binding = item_data.bind_property(
                attribute,
                display_widget,
                "label",
                GObject.BindingFlags.SYNC_CREATE,
                self.get_text_renderer(text_renderer_func_name),
            )
            self.track_binding(binding)
        else:
            binding = item_data.bind_property(
                attribute,
                display_widget,
                "label",
                GObject.BindingFlags.SYNC_CREATE,
                self.to_str,
            )
            self.track_binding(binding)

        # Set initial value on edit widget and connect handlers
        if isinstance(edit_widget, Gtk.SpinButton):
            try:
                edit_widget.set_value(float(current_value))
            except (ValueError, TypeError):
                edit_widget.set_value(0.0)

            def on_value_changed(sb: Any) -> None:
                item = getattr(sb, "_bound_item", None)
                attr = getattr(sb, "_bound_attribute", None)
                if item and attr:
                    try:
                        setattr(item, attr, sb.get_value())
                    except Exception:
                        pass

            edit_widget._handler_id = edit_widget.connect("value-changed", on_value_changed)
        elif isinstance(edit_widget, Gtk.Switch):
            edit_widget.set_active(bool(current_value))

            def on_switch_changed(sw: Any, pspec: Any) -> None:
                item = getattr(sw, "_bound_item", None)
                attr = getattr(sw, "_bound_attribute", None)
                if item and attr:
                    try:
                        setattr(item, attr, sw.get_active())
                    except Exception:
                        pass

            edit_widget._handler_id = edit_widget.connect("notify::active", on_switch_changed)
        elif isinstance(edit_widget, Gtk.Entry):
            edit_widget.set_text(str(current_value) if current_value else "")

            def on_entry_changed(entry: Any) -> None:
                item = getattr(entry, "_bound_item", None)
                attr = getattr(entry, "_bound_attribute", None)
                if item and attr:
                    try:
                        setattr(item, attr, entry.get_text())
                    except Exception:
                        pass

            edit_widget._handler_id = edit_widget.connect("changed", on_entry_changed)
        elif isinstance(edit_widget, Gtk.DropDown):
            options = getattr(edit_widget, "_options", [])
            try:
                idx = options.index(str(current_value)) if current_value else 0
            except ValueError:
                idx = 0
            edit_widget.set_selected(idx)

            def on_dropdown_changed(dropdown: Any, pspec: Any) -> None:
                item = getattr(dropdown, "_bound_item", None)
                attr = getattr(dropdown, "_bound_attribute", None)
                opts = getattr(dropdown, "_options", [])
                if item and attr:
                    try:
                        selected_idx = dropdown.get_selected()
                        if 0 <= selected_idx < len(opts):
                            setattr(item, attr, opts[selected_idx])
                    except Exception:
                        pass

            edit_widget._handler_id = edit_widget.connect("notify::selected", on_dropdown_changed)

    def get_text_renderer(self, func_name: Any) -> Any:
        # Map function names to functions
        # fmt: off
        TEXT_RENDERERS = {
            "add_kb": add_kb,
            "add_percent": add_percent,
            "convert_seconds_to_hours_mins_seconds":
                convert_seconds_to_hours_mins_seconds,
            "format_timestamp": format_timestamp,
            "humanbytes": humanbytes,
        }

        def text_renderer(bind: Any, from_value: Any) -> Any:
            func = TEXT_RENDERERS[func_name]
            return func(from_value)
        return text_renderer

    def set_model(self, model: Any) -> None:
        """Set the model for the torrents component."""
        logger.trace("Torrents set_model", extra={"class_name": self.__class__.__name__})
        self.model = model
        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.track_signal(model, model.connect("language-changed", self.on_language_changed))
                logger.trace(
                    "Successfully connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.error(
                    f"FAILED to connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
        # Update the view if model is set
        if self.model:
            self.update_model()

    def update_model(self) -> None:
        # Use filtered liststore if search is active
        if hasattr(self.model, "get_filtered_liststore"):
            self.store = self.model.get_filtered_liststore()  # type: ignore[attr-defined]
        else:
            self.store = self.model.get_liststore()  # type: ignore[attr-defined]
        self.sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        self.sort_model = Gtk.SortListModel.new(self.store, self.sorter)

        # CRITICAL: Create SingleSelection with None model first
        # This prevents auto-selection before we can set properties
        self.selection = Gtk.SingleSelection.new(None)

        # CRITICAL: Disable automatic selection BEFORE setting the model
        # This allows detail tabs to show "No Torrent Selected" empty state on startup
        self.selection.set_autoselect(False)
        self.selection.set_can_unselect(True)

        # Now set the model after disabling autoselect
        self.selection.set_model(self.sort_model)

        # Connect to the notify::selected signal which fires when selection changes
        try:
            self.track_signal(
                self.selection,
                self.selection.connect("notify::selected", self.on_selection_changed),
            )
        except Exception as e:
            logger.error(f"Failed to connect notify::selected signal: {e}")
            # Try alternative signal names
            try:
                self.track_signal(
                    self.selection,
                    self.selection.connect("selection-changed", self.on_selection_changed_old),
                )
                logger.debug("Connected to selection-changed signal as fallback")
            except Exception as e2:
                logger.error(f"All signal connections failed: {e2}")
        self.torrents_columnview.set_model(self.selection)
        # Don't auto-select the first torrent - let user manually select
        # This allows detail tabs to show "No Torrent Selected" empty state on startup
        logger.trace(
            "Torrent list initialized - no auto-selection, user must select manually",
            extra={"class_name": self.__class__.__name__},
        )

    # Method to update the ColumnView with compatible attributes
    def update_view(self, model: Any, torrent: Any, updated_attributes: Any) -> None:
        logger.trace(
            f"📺 VIEW RECEIVED SIGNAL: torrent={getattr(torrent, 'name', 'Unknown') if torrent else 'None'}, "
            f"attributes={updated_attributes}",
            extra={"class_name": self.__class__.__name__},
        )
        self.model = model
        # Check if this is a filter update
        if updated_attributes == "filter":
            logger.trace(
                "Filter update detected - refreshing model",
                extra={"class_name": self.__class__.__name__},
            )
            self.update_model()
            return
        # Check if the model is initialized
        current_model = self.torrents_columnview.get_model()
        if current_model is None:
            logger.trace(
                "📺 VIEW: No current model, initializing with update_model()",
                extra={"class_name": self.__class__.__name__},
            )
            self.update_model()
        else:
            logger.trace(
                "📺 VIEW: Column view has model, torrent update should be visible",
                extra={"class_name": self.__class__.__name__},
            )

    def on_selection_changed(self, selection: Any, pspec: Any) -> None:
        selected_position = selection.get_selected()
        logger.debug(f"Torrent selection changed to position {selected_position}")
        # Get the selected item from SingleSelection
        selected_item = selection.get_selected_item()

        # Update selected ID and visible stacks
        new_id = getattr(selected_item, "id", None) if selected_item else None
        if new_id != self._selected_item_id:
            self._selected_item_id = new_id
            self._update_visible_stacks(new_id)

        if selected_item is not None:
            self.model.emit(  # type: ignore[attr-defined]
                "selection-changed",
                self.model,
                selected_item,
            )
        else:
            # No selection - emit with None to trigger hide of bottom pane
            self.model.emit(  # type: ignore[attr-defined]
                "selection-changed",
                self.model,
                None,
            )

    def on_selection_changed_old(self, selection: Any, position: Any, item: Any) -> None:
        """Fallback method for old selection-changed signal."""
        logger.debug(f"Torrent selection changed at position {position}")
        # Get the selected item from SingleSelection
        selected_item = selection.get_selected_item()
        if selected_item is not None:
            self.model.emit(  # type: ignore[attr-defined]
                "selection-changed",
                self.model,
                selected_item,
            )
        else:
            # No selection - emit with None to trigger hide of bottom pane
            self.model.emit(  # type: ignore[attr-defined]
                "selection-changed",
                self.model,
                None,
            )

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_model_changed(self, source: Any, data_obj: Any, data_changed: Any) -> None:
        logger.trace(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        sorter.changed(0)

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace(
            f"🔴 ATTRIBUTE CHANGED: key={key}, value={value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Skip if we're in the middle of a column toggle operation
        if hasattr(self, "_updating_columns") and self._updating_columns:
            logger.trace(
                "🔴 ATTRIBUTE CHANGED: Skipping due to _updating_columns flag",
                extra={"class_name": self.__class__.__name__},
            )
            return

        logger.trace(
            "🔴 ATTRIBUTE CHANGED: About to call get_sorter()...",
            extra={"class_name": self.__class__.__name__},
        )
        sorter = Gtk.ColumnView.get_sorter(self.torrents_columnview)
        logger.trace(
            "🔴 ATTRIBUTE CHANGED: get_sorter() returned, calling changed(0)...",
            extra={"class_name": self.__class__.__name__},
        )
        sorter.changed(0)
        logger.trace(
            "🔴 ATTRIBUTE CHANGED: COMPLETE",
            extra={"class_name": self.__class__.__name__},
        )

    def _register_menu_actions(self) -> Any:
        """Register all context menu actions if they don't exist"""
        actions = {
            # Basic actions
            "pause": self.on_pause,
            "resume": self.on_resume,
            "force_start": self.on_force_start,
            "update_tracker": self.on_update_tracker,
            "force_recheck": self.on_force_recheck,
            "force_complete": self.on_force_complete,
            "set_random_progress": self.on_set_random_progress,
            # Copy actions
            "copy_name": self.on_copy_name,
            "copy_hash": self.on_copy_hash,
            "copy_magnet": self.on_copy_magnet,
            "copy_tracker": self.on_copy_tracker,
            # Priority actions
            "priority_high": self.on_priority_high,
            "priority_normal": self.on_priority_normal,
            "priority_low": self.on_priority_low,
            # Speed limit actions
            "set_upload_limit": self.on_set_upload_limit,
            "set_download_limit": self.on_set_download_limit,
            "reset_limits": self.on_reset_limits,
            # Tracker management
            "add_tracker": self.on_add_tracker,
            "edit_tracker": self.on_edit_tracker,
            "remove_tracker": self.on_remove_tracker,
            # Queue actions
            "queue_top": self.on_queue_top,
            "queue_up": self.on_queue_up,
            "queue_down": self.on_queue_down,
            "queue_bottom": self.on_queue_bottom,
            # Advanced options
            "rename_torrent": self.on_rename_torrent,
            "set_label": self.on_set_label,
            "set_location": self.on_set_location,
            "toggle_super_seed": self.on_toggle_super_seed,
            "toggle_sequential": self.on_toggle_sequential,
            "show_properties": self.on_show_properties,
            # Remove actions
            "remove_torrent": self.on_remove_torrent,
            "remove_torrent_and_data": self.on_remove_torrent_and_data,
        }

        for action_name, handler in actions.items():
            if not self.action_group.has_action(action_name):
                action = Gio.SimpleAction.new(action_name, None)
                self.track_signal(action, action.connect("activate", handler))
                self.action_group.add_action(action)

    def _get_selected_torrent(self) -> Any:
        """Helper method to get the currently selected torrent object"""
        if not hasattr(self, "selection") or self.selection is None:
            return None, None

        selected_item = self.selection.get_selected_item()
        if selected_item is None:
            return None, None

        # Find the torrent object in the model's torrent list
        if hasattr(self.model, "torrent_list"):
            for torrent in self.model.torrent_list:  # type: ignore[attr-defined]
                if hasattr(torrent, "torrent_attributes") and torrent.torrent_attributes == selected_item:
                    return torrent, selected_item

        return None, selected_item

    # ===== BASIC ACTIONS =====

    def on_pause(self, action: Any, parameter: Any) -> None:
        """Handle pause action from context menu"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            logger.warning(
                "No torrent selected for pause",
                extra={"class_name": self.__class__.__name__},
            )
            return

        torrent_name = getattr(selected_item, "name", "Unknown")
        logger.trace(
            f"Pausing torrent: {torrent_name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.active = False

    def on_resume(self, action: Any, parameter: Any) -> None:
        """Handle resume action from context menu"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            logger.warning(
                "No torrent selected for resume",
                extra={"class_name": self.__class__.__name__},
            )
            return

        torrent_name = getattr(selected_item, "name", "Unknown")
        logger.trace(
            f"Resuming torrent: {torrent_name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.active = True

    def on_force_start(self, action: Any, parameter: Any) -> None:
        """Force start a torrent, ignoring queue limits"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Force starting torrent: {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.force_start = True
        torrent.active = True

    def on_force_recheck(self, action: Any, parameter: Any) -> None:
        """Simulate a recheck of torrent data"""
        import random

        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Force rechecking torrent: {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        # Simulate recheck by randomly adjusting progress slightly
        old_progress = torrent.progress
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        new_progress = max(0.0, min(1.0, old_progress + variation))
        torrent.progress = new_progress

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"Recheck completed for {torrent.name}: {new_progress*100:.1f}%")

    def on_force_complete(self, action: Any, parameter: Any) -> None:
        """Force torrent to 100% completion"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Force completing torrent: {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.progress = 1.0
        torrent.total_downloaded = torrent.total_size

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"{torrent.name} set to 100% complete")

    def on_set_random_progress(self, action: Any, parameter: Any) -> None:
        """Set torrent to a random realistic progress percentage"""
        import random

        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        # Generate realistic random progress (more weight towards higher percentages)
        rand = random.random()
        if rand < 0.3:
            progress = random.uniform(0.1, 0.5)
        elif rand < 0.7:
            progress = random.uniform(0.5, 0.9)
        else:
            progress = random.uniform(0.9, 0.99)

        logger.trace(
            f"Setting random progress for {torrent.name}: {progress*100:.1f}%",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.progress = progress
        torrent.total_downloaded = int(torrent.total_size * progress)

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"{torrent.name} progress set to {progress*100:.1f}%")

    def on_update_tracker(self, action: Any, parameter: Any) -> None:
        """Handle update tracker action from context menu"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            logger.warning(
                "No torrent selected for update tracker",
                extra={"class_name": self.__class__.__name__},
            )
            return

        logger.trace(
            f"Updating tracker for torrent: {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.force_tracker_update()

    # ===== COPY ACTIONS =====

    def on_copy_name(self, action: Any, parameter: Any) -> None:
        """Copy torrent name to clipboard"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(torrent.name)
        logger.trace(
            f"Copied name to clipboard: {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"Copied name: {torrent.name}")

    def on_copy_hash(self, action: Any, parameter: Any) -> None:
        """Copy torrent info hash to clipboard"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        if hasattr(torrent, "torrent_file") and hasattr(torrent.torrent_file, "file_hash"):
            info_hash = torrent.torrent_file.file_hash.hex()
            clipboard = Gdk.Display.get_default().get_clipboard()
            clipboard.set(info_hash)
            logger.trace(
                f"Copied info hash to clipboard: {info_hash}",
                extra={"class_name": self.__class__.__name__},
            )

            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(f"Copied info hash: {info_hash[:16]}...")
        else:
            logger.warning(
                "Torrent file hash not available",
                extra={"class_name": self.__class__.__name__},
            )

    def on_copy_magnet(self, action: Any, parameter: Any) -> None:
        """Copy magnet link to clipboard"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        if hasattr(torrent, "torrent_file") and hasattr(torrent.torrent_file, "file_hash"):
            info_hash = torrent.torrent_file.file_hash.hex()
            tracker_url = getattr(torrent.torrent_file, "announce", "")
            magnet_link = f"magnet:?xt=urn:btih:{info_hash}&dn={torrent.name}"
            if tracker_url:
                magnet_link += f"&tr={tracker_url}"

            clipboard = Gdk.Display.get_default().get_clipboard()
            clipboard.set(magnet_link)
            logger.trace(
                "Copied magnet link to clipboard",
                extra={"class_name": self.__class__.__name__},
            )

            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(f"Copied magnet link for {torrent.name}")
        else:
            logger.warning(
                "Torrent info not available for magnet link",
                extra={"class_name": self.__class__.__name__},
            )

    def on_copy_tracker(self, action: Any, parameter: Any) -> None:
        """Copy tracker URL to clipboard"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        if hasattr(torrent, "torrent_file") and hasattr(torrent.torrent_file, "announce"):
            tracker_url = torrent.torrent_file.announce
            clipboard = Gdk.Display.get_default().get_clipboard()
            clipboard.set(tracker_url)
            logger.trace(
                f"Copied tracker URL to clipboard: {tracker_url}",
                extra={"class_name": self.__class__.__name__},
            )

            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify("Copied tracker URL")
        else:
            logger.warning(
                "Tracker URL not available",
                extra={"class_name": self.__class__.__name__},
            )

    # ===== PRIORITY ACTIONS =====

    def on_priority_high(self, action: Any, parameter: Any) -> None:
        """Set torrent priority to high"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Setting high priority for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.priority = "high"
        # Increase speeds for high priority
        torrent.upload_speed = int(torrent.upload_speed * 1.5)
        torrent.download_speed = int(torrent.download_speed * 1.5)

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"{torrent.name} set to high priority")

    def on_priority_normal(self, action: Any, parameter: Any) -> None:
        """Set torrent priority to normal"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Setting normal priority for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.priority = "normal"
        # Reset to configured speeds
        torrent.upload_speed = self.settings.upload_speed
        torrent.download_speed = self.settings.download_speed

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"{torrent.name} set to normal priority")

    def on_priority_low(self, action: Any, parameter: Any) -> None:
        """Set torrent priority to low"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Setting low priority for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.priority = "low"
        # Decrease speeds for low priority
        torrent.upload_speed = max(1, int(torrent.upload_speed * 0.5))
        torrent.download_speed = max(1, int(torrent.download_speed * 0.5))

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"{torrent.name} set to low priority")

    # ===== SPEED LIMIT ACTIONS =====

    def on_set_upload_limit(self, action: Any, parameter: Any) -> None:
        """Show dialog to set upload limit"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        dialog = Gtk.Dialog(title=self._("Set Upload Limit"), transient_for=self.window, modal=True)
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("OK"), Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        label = Gtk.Label(label=self._("Upload limit (KB/s, 0 = unlimited):"))
        entry = Gtk.Entry()
        entry.set_text(str(torrent.upload_limit))
        content_area.append(label)
        content_area.append(entry)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                limit = int(entry.get_text())
                torrent.upload_limit = limit
                logger.trace(
                    f"Set upload limit for {torrent.name}: {limit} KB/s",
                    extra={"class_name": self.__class__.__name__},
                )
                from d_fake_seeder.view import View

                if View.instance:
                    View.instance.notify(f"Upload limit set to {limit} KB/s" if limit > 0 else "Upload limit removed")
            except ValueError:
                logger.warning(
                    "Invalid upload limit entered",
                    extra={"class_name": self.__class__.__name__},
                )

        dialog.destroy()

    def on_set_download_limit(self, action: Any, parameter: Any) -> None:
        """Show dialog to set download limit"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        dialog = Gtk.Dialog(title=self._("Set Download Limit"), transient_for=self.window, modal=True)
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("OK"), Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        label = Gtk.Label(label=self._("Download limit (KB/s, 0 = unlimited):"))
        entry = Gtk.Entry()
        entry.set_text(str(torrent.download_limit))
        content_area.append(label)
        content_area.append(entry)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            try:
                limit = int(entry.get_text())
                torrent.download_limit = limit
                logger.trace(
                    f"Set download limit for {torrent.name}: {limit} KB/s",
                    extra={"class_name": self.__class__.__name__},
                )
                from d_fake_seeder.view import View

                if View.instance:
                    View.instance.notify(
                        f"Download limit set to {limit} KB/s" if limit > 0 else "Download limit removed"
                    )
            except ValueError:
                logger.warning(
                    "Invalid download limit entered",
                    extra={"class_name": self.__class__.__name__},
                )

        dialog.destroy()

    def on_reset_limits(self, action: Any, parameter: Any) -> None:
        """Reset torrent to use global speed limits"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Resetting speed limits to global for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        torrent.upload_limit = 0
        torrent.download_limit = 0
        torrent.upload_speed = self.settings.upload_speed
        torrent.download_speed = self.settings.download_speed

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"Using global speed limits for {torrent.name}")

    # ===== TRACKER MANAGEMENT =====

    def on_add_tracker(self, action: Any, parameter: Any) -> None:
        """Add a new tracker URL"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        dialog = Gtk.Dialog(title=self._("Add Tracker"), transient_for=self.window, modal=True)
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("Add"), Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        label = Gtk.Label(label=self._("Tracker URL:"))
        entry = Gtk.Entry()
        content_area.append(label)
        content_area.append(entry)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            tracker_url = entry.get_text()
            if tracker_url and hasattr(torrent, "torrent_file"):
                if not hasattr(torrent.torrent_file, "announce_list"):
                    torrent.torrent_file.announce_list = []
                torrent.torrent_file.announce_list.append(tracker_url)
                logger.trace(
                    f"Added tracker {tracker_url} to {torrent.name}",
                    extra={"class_name": self.__class__.__name__},
                )
                from d_fake_seeder.view import View

                if View.instance:
                    View.instance.notify(f"Tracker added to {torrent.name}")

        dialog.destroy()

    def on_edit_tracker(self, action: Any, parameter: Any) -> None:
        """Edit primary tracker URL"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        current_tracker = getattr(torrent.torrent_file, "announce", "") if hasattr(torrent, "torrent_file") else ""

        dialog = Gtk.Dialog(title=self._("Edit Tracker"), transient_for=self.window, modal=True)
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("Save"), Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        label = Gtk.Label(label=self._("Tracker URL:"))
        entry = Gtk.Entry()
        entry.set_text(current_tracker)
        content_area.append(label)
        content_area.append(entry)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_tracker = entry.get_text()
            if new_tracker and hasattr(torrent, "torrent_file"):
                torrent.torrent_file.announce = new_tracker
                logger.trace(
                    f"Updated tracker for {torrent.name}: {new_tracker}",
                    extra={"class_name": self.__class__.__name__},
                )
                from d_fake_seeder.view import View

                if View.instance:
                    View.instance.notify(f"Tracker updated for {torrent.name}")

        dialog.destroy()

    def on_remove_tracker(self, action: Any, parameter: Any) -> None:
        """Remove a tracker (placeholder - would show list to choose from)"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Remove tracker requested for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify("Tracker removal not yet implemented")

    # ===== QUEUE ACTIONS =====

    def on_queue_top(self, action: Any, parameter: Any) -> None:
        """Move torrent to top of queue"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Moving {torrent.name} to top of queue",
            extra={"class_name": self.__class__.__name__},
        )
        # Set ID to 1 and shift others down
        if hasattr(self.model, "torrent_list"):
            for t in self.model.torrent_list:  # type: ignore[attr-defined]
                if t.id >= 1:
                    t.id += 1
            torrent.id = 1

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"{torrent.name} moved to top")

    def on_queue_up(self, action: Any, parameter: Any) -> None:
        """Move torrent up in queue"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None or torrent.id <= 1:
            return

        logger.trace(
            f"Moving {torrent.name} up in queue",
            extra={"class_name": self.__class__.__name__},
        )
        # Swap with previous torrent
        if hasattr(self.model, "torrent_list"):
            for t in self.model.torrent_list:  # type: ignore[attr-defined]
                if t.id == torrent.id - 1:
                    t.id += 1
                    torrent.id -= 1
                    break

    def on_queue_down(self, action: Any, parameter: Any) -> None:
        """Move torrent down in queue"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Moving {torrent.name} down in queue",
            extra={"class_name": self.__class__.__name__},
        )
        # Swap with next torrent
        if hasattr(self.model, "torrent_list"):
            for t in self.model.torrent_list:  # type: ignore[attr-defined]
                if t.id == torrent.id + 1:
                    t.id -= 1
                    torrent.id += 1
                    break

    def on_queue_bottom(self, action: Any, parameter: Any) -> None:
        """Move torrent to bottom of queue"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        logger.trace(
            f"Moving {torrent.name} to bottom of queue",
            extra={"class_name": self.__class__.__name__},
        )
        # Set ID to max + 1
        if hasattr(self.model, "torrent_list"):
            max_id = max(t.id for t in self.model.torrent_list)  # type: ignore[attr-defined]
            torrent.id = max_id + 1

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"{torrent.name} moved to bottom")

    # ===== ADVANCED OPTIONS =====

    def on_rename_torrent(self, action: Any, parameter: Any) -> None:
        """Rename the torrent"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        dialog = Gtk.Dialog(title=self._("Rename Torrent"), transient_for=self.window, modal=True)
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("Rename"), Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        label = Gtk.Label(label=self._("New name:"))
        entry = Gtk.Entry()
        entry.set_text(torrent.name)
        content_area.append(label)
        content_area.append(entry)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            new_name = entry.get_text()
            if new_name:
                old_name = torrent.name
                torrent.name = new_name
                logger.trace(
                    f"Renamed torrent from {old_name} to {new_name}",
                    extra={"class_name": self.__class__.__name__},
                )
                from d_fake_seeder.view import View

                if View.instance:
                    View.instance.notify(f"Renamed to: {new_name}")

        dialog.destroy()

    def on_set_label(self, action: Any, parameter: Any) -> None:
        """Set a label/category for the torrent"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        dialog = Gtk.Dialog(title=self._("Set Label"), transient_for=self.window, modal=True)
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("Set"), Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        label_widget = Gtk.Label(label=self._("Label:"))
        entry = Gtk.Entry()
        entry.set_text(torrent.label if hasattr(torrent, "label") else "")
        content_area.append(label_widget)
        content_area.append(entry)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            label = entry.get_text()
            torrent.label = label
            logger.trace(
                f"Set label for {torrent.name}: {label}",
                extra={"class_name": self.__class__.__name__},
            )
            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(f"Label set: {label}" if label else "Label cleared")

        dialog.destroy()

    def on_set_location(self, action: Any, parameter: Any) -> None:
        """Set download location for the torrent"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        dialog = Gtk.FileChooserDialog(
            title=self._("Set Location"),
            transient_for=self.window,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("Select"), Gtk.ResponseType.OK)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            location = dialog.get_file().get_path()
            logger.trace(
                f"Set location for {torrent.name}: {location}",
                extra={"class_name": self.__class__.__name__},
            )
            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(f"Location set to: {location}")

        dialog.destroy()

    def on_toggle_super_seed(self, action: Any, parameter: Any) -> None:
        """Toggle super seeding mode"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        torrent.super_seeding = not torrent.super_seeding
        logger.trace(
            f"Super seeding {'enabled' if torrent.super_seeding else 'disabled'} for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"Super seeding {'enabled' if torrent.super_seeding else 'disabled'}")

    def on_toggle_sequential(self, action: Any, parameter: Any) -> None:
        """Toggle sequential download mode"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        torrent.sequential_download = not torrent.sequential_download
        logger.trace(
            f"Sequential download {'enabled' if torrent.sequential_download else 'disabled'} for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )

        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"Sequential download {'enabled' if torrent.sequential_download else 'disabled'}")

    def on_show_properties(self, action: Any, parameter: Any) -> None:
        """Show torrent properties dialog"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        # For now, just log and notify - full properties dialog would be more complex
        logger.trace(
            f"Showing properties for {torrent.name}",
            extra={"class_name": self.__class__.__name__},
        )
        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(f"Properties: {torrent.name} - Full dialog not yet implemented")

    # ===== REMOVE ACTIONS =====

    def on_remove_torrent(self, action: Any, parameter: Any) -> None:
        """Remove torrent from list (keep file)"""
        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=self._("Remove Torrent?"),
        )
        dialog.format_secondary_text(f"{self._('Remove')} {torrent.name}?\n{self._('The .torrent file will be kept.')}")

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            logger.trace(
                f"Removing torrent: {torrent.name}",
                extra={"class_name": self.__class__.__name__},
            )
            if hasattr(self.model, "remove_torrent"):
                self.model.remove_torrent(torrent)  # type: ignore[attr-defined]

            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(f"Removed: {torrent.name}")

    def on_remove_torrent_and_data(self, action: Any, parameter: Any) -> None:
        """Remove torrent and delete .torrent file"""
        import os

        torrent, selected_item = self._get_selected_torrent()
        if torrent is None:
            return

        # Show confirmation dialog
        dialog = Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.YES_NO,
            text=self._("Remove Torrent and Data?"),
        )
        dialog.format_secondary_text(
            f"{self._('Remove')} {torrent.name}?\n{self._('The .torrent file will be DELETED.')}"
        )

        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            logger.trace(
                f"Removing torrent and data: {torrent.name}",
                extra={"class_name": self.__class__.__name__},
            )

            # Delete .torrent file
            if hasattr(torrent, "file_path") and os.path.exists(torrent.file_path):
                try:
                    os.remove(torrent.file_path)
                    logger.trace(
                        f"Deleted file: {torrent.file_path}",
                        extra={"class_name": self.__class__.__name__},
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to delete file: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

            if hasattr(self.model, "remove_torrent"):
                self.model.remove_torrent(torrent)  # type: ignore[attr-defined]

            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(f"Removed: {torrent.name} (file deleted)")

    def model_selection_changed(self, source: Any, model: Any, torrent: Any) -> Any:
        logger.trace(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
