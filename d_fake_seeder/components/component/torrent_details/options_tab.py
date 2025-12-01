"""
Options tab for torrent details.

Displays editable torrent options with dynamic widgets based on configuration.
"""

# fmt: off
from typing import Any, List

import gi

from .base_tab import BaseTorrentTab
from .tab_mixins import DataUpdateMixin, UIUtilityMixin

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa

# fmt: on


class OptionsTab(BaseTorrentTab, DataUpdateMixin, UIUtilityMixin):
    """
    Options tab component for displaying and editing torrent options.

    Creates dynamic widgets based on settings configuration for editable attributes.
    """

    def __init__(self, builder: Gtk.Builder, model):
        """Initialize the options tab."""
        super().__init__(builder, model)
        self._options_grid_children: List[Any] = []

        # Connect to language change signal for translation updates
        if hasattr(self.model, "connect"):
            self.track_signal(model, model.connect("language-changed", self.on_language_changed))

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Options"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "options_tab"

    def _init_widgets(self) -> None:
        """Initialize Options tab widgets."""
        # Cache the options grid widget
        self._options_grid = self.get_widget("options_grid")

    def clear_content(self) -> None:
        """Clear the options tab content."""
        try:
            # Remove all child widgets
            for child in self._options_grid_children:
                try:
                    if self._options_grid and child.get_parent() == self._options_grid:
                        self._options_grid.remove(child)
                    elif child.get_parent():
                        # Remove from actual parent if different
                        child.get_parent().remove(child)
                except Exception as e:
                    self.logger.error(f"Error removing options grid child: {e}")

            self._options_grid_children = []

        except Exception as e:
            self.logger.error(f"Error clearing options tab content: {e}")

    def update_content(self, torrent) -> None:
        """
        Update options tab content with torrent data.

        Args:
            torrent: Torrent object to display
        """
        try:
            self.logger.debug(
                "Updating options tab for torrent",
                extra={"class_name": self.__class__.__name__},
            )

            # Store current torrent for language change handling
            self._current_torrent = torrent

            # Clear existing content
            self.clear_content()

            if not self._options_grid:
                self.logger.error("Options grid not found")
                return

            if not torrent:
                self._current_torrent = None
                self._show_no_options_message()
                return

            # Get editable widgets configuration
            edit_widgets = self._get_edit_widgets_config()

            if not edit_widgets:
                self._show_no_options_message()
                return

            # Create dynamic widgets for each editable attribute
            self._create_option_widgets(torrent, edit_widgets)

        except Exception as e:
            self.logger.error(f"Error updating options tab content: {e}")

    def _get_edit_widgets_config(self) -> dict:
        """
        Get editable widgets configuration from settings.

        Returns:
            Dictionary of attribute -> widget_type mappings
        """
        try:
            if hasattr(self.settings, "editwidgets"):
                return self.settings.editwidgets
            return {}
        except Exception as e:
            self.logger.error(f"Error getting edit widgets config: {e}")
            return {}

    def _create_option_widgets(self, torrent, edit_widgets: dict) -> None:
        """
        Create dynamic option widgets based on configuration.

        Args:
            torrent: Torrent object
            edit_widgets: Widget configuration dictionary
        """
        try:
            row = 0

            for index, attribute in enumerate(edit_widgets):
                # Arrange widgets in 2 columns
                col = 0 if index % 2 == 0 else 2

                # Create the dynamic widget
                widget_type = edit_widgets[attribute]
                dynamic_widget = self._create_dynamic_widget(torrent, attribute, widget_type)

                if not dynamic_widget:
                    continue

                # Create label
                label = self._create_option_label(attribute)

                # Add to grid
                if self._options_grid is not None:
                    self._options_grid.attach(label, col, row, 1, 1)
                    self._options_grid.attach(dynamic_widget, col + 1, row, 1, 1)

                # Track children for cleanup
                self._options_grid_children.append(label)
                self._options_grid_children.append(dynamic_widget)

                # Move to next row after every 2 widgets
                if col == 2:
                    row += 1

        except Exception as e:
            self.logger.error(f"Error creating option widgets: {e}")

    def _create_dynamic_widget(self, torrent, attribute: str, widget_type: str):
        """
        Create a dynamic widget for a torrent attribute.

        Args:
            torrent: Torrent object
            attribute: Attribute name
            widget_type: Widget type string

        Returns:
            Created widget or None
        """
        try:
            # Safely evaluate widget type
            widget_class = self._get_widget_class(widget_type)
            if not widget_class:
                return None

            # Create widget instance
            dynamic_widget = widget_class()
            dynamic_widget.set_visible(True)
            dynamic_widget.set_hexpand(True)

            # Configure widget based on type
            if isinstance(dynamic_widget, Gtk.Switch):
                self._configure_switch_widget(dynamic_widget, torrent, attribute)
            else:
                self._configure_adjustment_widget(dynamic_widget, torrent, attribute)

            return dynamic_widget

        except Exception as e:
            self.logger.error(f"Error creating dynamic widget for {attribute}: {e}")
            return None

    def _get_widget_class(self, widget_type: str):
        """
        Get widget class from type string safely.

        Args:
            widget_type: Widget type string

        Returns:
            Widget class or None
        """
        try:
            # Safe evaluation of widget types - only allow known GTK widgets
            allowed_widgets = {
                "Gtk.Switch": Gtk.Switch,
                "Gtk.SpinButton": Gtk.SpinButton,
                "Gtk.Scale": Gtk.Scale,
                "Gtk.Entry": Gtk.Entry,
            }

            return allowed_widgets.get(widget_type)

        except Exception as e:
            self.logger.error(f"Error getting widget class for {widget_type}: {e}")
            return None

    def _configure_switch_widget(self, widget: Gtk.Switch, torrent, attribute: str) -> None:
        """
        Configure a switch widget.

        Args:
            widget: Switch widget
            torrent: Torrent object
            attribute: Attribute name
        """
        try:
            # Set initial value
            current_value = self.safe_get_property(torrent, attribute, False)
            widget.set_active(bool(current_value))

            # Connect signal
            self.track_signal(
                widget,
                widget.connect("state-set", self._on_switch_value_changed, torrent, attribute),
            )

        except Exception as e:
            self.logger.error(f"Error configuring switch widget for {attribute}: {e}")

    def _configure_adjustment_widget(self, widget, torrent, attribute: str) -> None:
        """
        Configure an adjustment-based widget (SpinButton, Scale).

        Args:
            widget: Widget with adjustment
            torrent: Torrent object
            attribute: Attribute name
        """
        try:
            # Get current value
            current_value = self.safe_get_property(torrent, attribute, 0)

            # Create adjustment
            adjustment = Gtk.Adjustment(
                value=float(current_value),
                upper=float(current_value) * 10 if current_value > 0 else 100,
                lower=0,
                step_increment=1,
                page_increment=10,
            )

            # Set adjustment
            widget.set_adjustment(adjustment)

            # Configure additional properties
            if hasattr(widget, "set_wrap"):
                widget.set_wrap(True)

            # Connect signal
            self.track_signal(
                widget,
                widget.connect(
                    "value-changed",
                    self._on_adjustment_value_changed,
                    torrent,
                    attribute,
                ),
            )

        except Exception as e:
            self.logger.error(f"Error configuring adjustment widget for {attribute}: {e}")

    def _create_option_label(self, attribute: str) -> Gtk.Label:
        """
        Create a label for an option.

        Args:
            attribute: Attribute name

        Returns:
            Configured label widget
        """
        try:
            # Get translation function from model
            translate_func = (
                self.model.get_translate_func() if hasattr(self.model, "get_translate_func") else lambda x: x
            )

            # Create mapping of attribute names to translatable display strings
            # This ensures fresh translations on each call, respecting language changes
            attribute_display_map = {
                "name": translate_func("Name"),
                "filepath": translate_func("File Path"),
                "total_size": translate_func("Total Size"),
                "progress": translate_func("Progress"),
                "created": translate_func("Created"),
                "comment": translate_func("Comment"),
                "created_by": translate_func("Created By"),
                "piece_length": translate_func("Piece Length"),
                "pieces": translate_func("Pieces"),
                "id": translate_func("ID"),
                "size": translate_func("Size"),
                "session_downloaded": translate_func("Session Downloaded"),
                "session_uploaded": translate_func("Session Uploaded"),
                "total_downloaded": translate_func("Total Downloaded"),
                "total_uploaded": translate_func("Total Uploaded"),
                "upload_speed": translate_func("Upload Speed"),
                "download_speed": translate_func("Download Speed"),
                "seeders": translate_func("Seeders"),
                "leechers": translate_func("Leechers"),
                "announce_interval": translate_func("Announce Interval"),
                "next_update": translate_func("Next Update"),
                "threshold": translate_func("Threshold"),
                "small_torrent_limit": translate_func("Small Torrent Limit"),
                "uploading": translate_func("Uploading"),
                "active": translate_func("Active"),
                "ratio": translate_func("Ratio"),
                "availability": translate_func("Availability"),
                "private": translate_func("Private"),
                "added": translate_func("Added"),
                "completed": translate_func("Completed"),
                "label": translate_func("Label"),
                "eta": translate_func("ETA"),
                "priority": translate_func("Priority"),
                "status": translate_func("Status"),
                "tracker": translate_func("Tracker"),
                "download_limit": translate_func("Download Limit"),
                "upload_limit": translate_func("Upload Limit"),
                "sequential_download": translate_func("Sequential Download"),
                "super_seeding": translate_func("Super Seeding"),
                "force_start": translate_func("Force Start"),
            }

            # Use mapped display name or fallback to translated attribute name
            if attribute in attribute_display_map:
                display_text = attribute_display_map[attribute]
            else:
                # Fallback: translate the attribute name directly
                display_text = translate_func(attribute.replace("_", " ").title())

            label = Gtk.Label()
            label.set_text(display_text)
            label.set_name(f"label_{attribute}")
            label.set_visible(True)
            label.set_hexpand(True)
            label.set_halign(Gtk.Align.START)
            return label

        except Exception as e:
            self.logger.error(f"Error creating option label for {attribute}: {e}")
            return Gtk.Label()

    def _show_no_options_message(self) -> None:
        """Show a message when no options are available."""
        try:
            # Get translation function from model
            translate_func = (
                self.model.get_translate_func() if hasattr(self.model, "get_translate_func") else lambda x: x
            )

            message_text = translate_func("No editable options available for this torrent.")
            message_label = self.create_info_label(message_text)
            self.set_widget_margins(message_label, self.ui_margin_large)

            if self._options_grid:
                self._options_grid.attach(message_label, 0, 0, 2, 1)
                self._options_grid_children.append(message_label)

        except Exception as e:
            self.logger.error(f"Error showing no options message: {e}")

    # Signal handlers
    def _on_switch_value_changed(self, widget: Gtk.Switch, state: bool, torrent, attribute: str) -> None:
        """
        Handle switch value change.

        Args:
            widget: Switch widget
            state: New state
            torrent: Torrent object
            attribute: Attribute name
        """
        try:
            setattr(torrent, attribute, state)
            self.logger.debug(f"Updated {attribute} to {state}")
        except Exception as e:
            self.logger.error(f"Error updating switch value for {attribute}: {e}")

    def _on_adjustment_value_changed(self, widget, torrent, attribute: str) -> None:
        """
        Handle adjustment value change.

        Args:
            widget: Widget with adjustment
            torrent: Torrent object
            attribute: Attribute name
        """
        try:
            adjustment = widget.get_adjustment()
            value = adjustment.get_value()
            setattr(torrent, attribute, value)
            self.logger.debug(f"Updated {attribute} to {value}")
        except Exception as e:
            self.logger.error(f"Error updating adjustment value for {attribute}: {e}")

    def get_option_count(self) -> int:
        """
        Get the number of options displayed.

        Returns:
            Number of options
        """
        try:
            edit_widgets = self._get_edit_widgets_config()
            return len(edit_widgets)
        except Exception:
            return 0

    def on_language_changed(self, source=None, new_language=None):
        """
        Handle language change events by refreshing the options content.

        Args:
            source: Event source
            new_language: New language code
        """
        try:
            self.logger.debug(f"Language changed to {new_language}, refreshing options tab content")
            # Refresh content to update all labels with new translations
            if hasattr(self, "_current_torrent") and self._current_torrent:
                self.update_content(self._current_torrent)
        except Exception as e:
            self.logger.error(f"Error handling language change in options tab: {e}")
