"""
Mixin classes for torrent details tab functionality.

These mixins provide reusable functionality that can be composed
into different torrent details tab classes.
"""

# isort: skip_file

# fmt: off
from typing import Any, Callable, Optional

import gi

from d_fake_seeder.lib.logger import logger

gi.require_version("Gtk", "4.0")
from gi.repository import GLib  # noqa: E402
from gi.repository import Gtk  # noqa: E402

# fmt: on


class DataUpdateMixin:
    """
    Mixin for handling data updates and model changes.

    Provides standardized data update patterns and change notifications.
    """

    def setup_data_binding(self, model, callback: Callable) -> None:
        """
        Set up data binding to model changes.

        Args:
            model: Model to bind to
            callback: Callback function for changes
        """
        try:
            if hasattr(model, "connect"):
                model.connect("data-changed", callback)
                model.connect("selection-changed", callback)
            logger.debug(f"Data binding set up for {getattr(self, 'tab_name', 'unknown')} tab")
        except Exception as e:
            logger.error(f"Error setting up data binding: {e}")

    def safe_get_property(self, obj: Any, property_name: str, default: Any = "") -> Any:
        """
        Safely get a property from an object with fallback.

        Args:
            obj: Object to get property from
            property_name: Name of property
            default: Default value if property doesn't exist

        Returns:
            Property value or default
        """
        try:
            # First try direct attribute access (works for Torrent class with __getattr__)
            if hasattr(obj, property_name):
                return getattr(obj, property_name)
            # Fallback to GObject get_property for actual GObject instances
            elif hasattr(obj, "get_property"):
                return obj.get_property(property_name)
            else:
                return default
        except Exception as e:
            logger.warning(f"Error getting property {property_name}: {e}")
            return default

    def format_property_value(self, value: Any) -> str:
        """
        Format a property value for display.

        Args:
            value: Value to format

        Returns:
            Formatted string
        """
        try:
            if value is None:
                return "N/A"
            elif isinstance(value, bool):
                # Get translation function from model if available
                translate_func = (
                    self.model.get_translate_func()
                    if hasattr(self, "model") and hasattr(self.model, "get_translate_func")
                    else lambda x: x
                )
                return translate_func("Yes") if value else translate_func("No")
            elif isinstance(value, (int, float)):
                return str(value)
            else:
                return str(value)
        except Exception:
            return "N/A"

    def batch_update(self, update_func: Callable, *args, **kwargs) -> None:
        """
        Perform batch update with idle scheduling for better performance.

        Args:
            update_func: Function to call for update
            *args: Arguments for update function
            **kwargs: Keyword arguments for update function
        """

        def update_when_idle():
            try:
                update_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in batch update: {e}")
            return False  # Don't repeat

        GLib.idle_add(update_when_idle)


class UIUtilityMixin:
    """
    Mixin for common UI utility functions.

    Provides helper methods for creating and managing UI elements.
    """

    def remove_all_children(self, container: Gtk.Widget) -> None:
        """
        Remove all children from a container widget.

        Args:
            container: Container to clear
        """
        try:
            if hasattr(container, "remove"):
                # For containers that support direct removal
                child = container.get_first_child()
                while child:
                    next_child = child.get_next_sibling()
                    container.remove(child)
                    child = next_child
            elif hasattr(container, "get_children"):
                # For older GTK versions
                for child in container.get_children():
                    container.remove(child)
        except Exception as e:
            logger.error(f"Error removing children from container: {e}")

    def create_scrolled_window(self, child: Gtk.Widget) -> Gtk.ScrolledWindow:
        """
        Create a scrolled window with standard settings.

        Args:
            child: Child widget to add

        Returns:
            Configured ScrolledWindow
        """
        try:
            scrolled = Gtk.ScrolledWindow()
            scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
            scrolled.set_hexpand(True)
            scrolled.set_vexpand(True)
            scrolled.set_child(child)
            return scrolled
        except Exception as e:
            logger.error(f"Error creating scrolled window: {e}")
            return Gtk.ScrolledWindow()

    def create_list_view(self, model: Optional[Any] = None) -> Gtk.ListView:
        """
        Create a list view with standard settings.

        Args:
            model: Optional model to set

        Returns:
            Configured ListView
        """
        try:
            list_view = Gtk.ListView()
            if model:
                list_view.set_model(model)
            list_view.set_hexpand(True)
            list_view.set_vexpand(True)
            return list_view
        except Exception as e:
            logger.error(f"Error creating list view: {e}")
            return Gtk.ListView()

    def create_column_view(self) -> Gtk.ColumnView:
        """
        Create a column view with standard settings.

        Returns:
            Configured ColumnView
        """
        try:
            column_view = Gtk.ColumnView()
            column_view.set_hexpand(True)
            column_view.set_vexpand(True)
            column_view.set_reorderable(True)
            return column_view
        except Exception as e:
            logger.error(f"Error creating column view: {e}")
            return Gtk.ColumnView()

    def create_text_view(self, editable: bool = False) -> Gtk.TextView:
        """
        Create a text view with standard settings.

        Args:
            editable: Whether text should be editable

        Returns:
            Configured TextView
        """
        try:
            text_view = Gtk.TextView()
            text_view.set_editable(editable)
            text_view.set_cursor_visible(editable)
            text_view.set_hexpand(True)
            text_view.set_vexpand(True)
            text_view.set_wrap_mode(Gtk.WrapMode.WORD)
            return text_view
        except Exception as e:
            logger.error(f"Error creating text view: {e}")
            return Gtk.TextView()

    def create_progress_bar(self) -> Gtk.ProgressBar:
        """
        Create a progress bar with standard settings.

        Returns:
            Configured ProgressBar
        """
        try:
            progress_bar = Gtk.ProgressBar()
            progress_bar.set_hexpand(True)
            progress_bar.set_show_text(True)
            return progress_bar
        except Exception as e:
            logger.error(f"Error creating progress bar: {e}")
            return Gtk.ProgressBar()

    def create_grid(self) -> Gtk.Grid:
        """
        Create a grid with standard settings.

        Uses consistent spacing values matching the Details tab:
        - row-spacing: 8px
        - column-spacing: 15px
        - margins: 0px (parent container already has 20px margins)

        Returns:
            Configured Grid
        """
        try:
            grid = Gtk.Grid()
            grid.set_column_spacing(15)  # Match details_grid: 15px
            grid.set_row_spacing(8)  # Match details_grid: 8px
            grid.set_hexpand(True)
            grid.set_vexpand(True)
            # DO NOT add margins - parent container (status_tab/files_tab/trackers_tab) already has 20px margins
            return grid
        except Exception as e:
            logger.error(f"Error creating grid: {e}")
            return Gtk.Grid()

    def create_label_pair(self, label_text: str, value_text: str, row: int, grid: Gtk.Grid) -> None:
        """
        Create a label pair (name and value) and add to grid.

        Args:
            label_text: Text for the label
            value_text: Text for the value
            row: Row number in grid
            grid: Grid to add to
        """
        try:
            # Create label for the name
            name_label = Gtk.Label(label=label_text)
            name_label.set_halign(Gtk.Align.START)
            name_label.set_hexpand(True)
            name_label.set_selectable(True)

            # Create label for the value
            value_label = Gtk.Label(label=value_text)
            value_label.set_halign(Gtk.Align.END)
            value_label.set_hexpand(False)
            value_label.set_selectable(True)

            # Add to grid
            grid.attach(name_label, 0, row, 1, 1)
            grid.attach(value_label, 1, row, 1, 1)

        except Exception as e:
            logger.error(f"Error creating label pair: {e}")

    def set_widget_margins(self, widget: Gtk.Widget, margin: int = 10) -> None:
        """
        Set standard margins on a widget.

        Args:
            widget: Widget to set margins on
            margin: Margin size
        """
        try:
            widget.set_margin_top(margin)
            widget.set_margin_bottom(margin)
            widget.set_margin_start(margin)
            widget.set_margin_end(margin)
        except Exception as e:
            logger.error(f"Error setting widget margins: {e}")

    def create_info_label(self, text: str, selectable: bool = True) -> Gtk.Label:
        """
        Create an info label with standard settings.

        Args:
            text: Label text
            selectable: Whether text should be selectable

        Returns:
            Configured Label
        """
        try:
            label = Gtk.Label(label=text)
            label.set_selectable(selectable)
            label.set_halign(Gtk.Align.START)
            label.set_valign(Gtk.Align.START)
            label.set_wrap(True)
            label.set_xalign(0)
            return label
        except Exception as e:
            logger.error(f"Error creating info label: {e}")
            return Gtk.Label()

    def update_text_buffer(self, text_view: Gtk.TextView, text: str, max_lines: int = 1000) -> None:
        """
        Update text view buffer with line limit for performance.

        Args:
            text_view: TextView to update
            text: Text to add
            max_lines: Maximum lines to keep
        """
        try:
            buffer = text_view.get_buffer()

            # Add new text
            end_iter = buffer.get_end_iter()
            buffer.insert(end_iter, text)

            # Trim buffer if too long
            line_count = buffer.get_line_count()
            if line_count > max_lines:
                lines_to_remove = line_count - max_lines
                start_iter = buffer.get_start_iter()
                remove_end_iter = buffer.get_iter_at_line(lines_to_remove)
                buffer.delete(start_iter, remove_end_iter)

            # Auto-scroll to bottom
            mark = buffer.get_insert()
            text_view.scroll_mark_onscreen(mark)

        except Exception as e:
            logger.error(f"Error updating text buffer: {e}")


class PerformanceMixin:
    """
    Mixin for performance optimization in tabs.

    Provides methods for efficient updates and resource management.
    """

    def __init__(self):
        self._update_pending = False
        self._last_update_time = 0
        self._update_queue = []

    def debounced_update(self, update_func: Callable, delay_ms: int = 100) -> None:
        """
        Perform debounced update to avoid excessive refreshes.

        Args:
            update_func: Function to call for update
            delay_ms: Delay in milliseconds
        """

        def delayed_update():
            try:
                if self._update_pending:
                    update_func()
                    self._update_pending = False
            except Exception as e:
                logger.error(f"Error in debounced update: {e}")
            return False  # Don't repeat

        self._update_pending = True
        GLib.timeout_add(delay_ms, delayed_update)

    def queue_update(self, update_func: Callable, *args, **kwargs) -> None:
        """
        Queue an update for batch processing.

        Args:
            update_func: Function to call
            *args: Arguments for function
            **kwargs: Keyword arguments for function
        """
        self._update_queue.append((update_func, args, kwargs))

        # Process queue on next idle
        GLib.idle_add(self._process_update_queue)

    def _process_update_queue(self) -> bool:
        """Process queued updates."""
        try:
            while self._update_queue:
                update_func, args, kwargs = self._update_queue.pop(0)
                update_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error processing update queue: {e}")

        return False  # Don't repeat

    def is_visible_in_viewport(self, widget: Gtk.Widget) -> bool:
        """
        Check if widget is visible in current viewport.

        Args:
            widget: Widget to check

        Returns:
            True if visible
        """
        try:
            # Basic visibility check
            if not widget.get_visible():
                return False

            # Check if parent notebook tab is active
            parent = widget.get_parent()
            while parent:
                if isinstance(parent, Gtk.Notebook):
                    current_page = parent.get_current_page()
                    widget_page = parent.page_num(widget)
                    return current_page == widget_page
                parent = parent.get_parent()

            return True
        except Exception:
            return True  # Assume visible if can't determine
