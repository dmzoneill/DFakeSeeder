"""
Status tab for torrent details.

Displays torrent attributes and status information in a grid layout.
"""

# isort: skip_file

# fmt: off
import gi

from d_fake_seeder.domain.torrent.model.attributes import Attributes

from .base_tab import BaseTorrentTab
from .tab_mixins import DataUpdateMixin, UIUtilityMixin

gi.require_version("Gtk", "4.0")
from gi.repository import GObject  # noqa

# fmt: on


class StatusTab(BaseTorrentTab, DataUpdateMixin, UIUtilityMixin):
    """
    Status tab component for displaying torrent status information.

    Shows all torrent attributes in a name-value grid format.
    """

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Status"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "status_tab"

    def _init_widgets(self) -> None:
        """Initialize Status tab widgets."""
        # Cache the main tab widget
        self._status_tab = self.get_widget("status_tab")
        self._status_grid_child = None

    def clear_content(self) -> None:
        """Clear the status tab content."""
        try:
            if self._status_grid_child is not None:
                self._remove_current_grid()
                self._status_grid_child = None

            # Show empty state
            super().clear_content()

        except Exception as e:
            self.logger.error(f"Error clearing status tab content: {e}")

    def _remove_current_grid(self) -> None:
        """Remove the current grid child from the status tab."""
        try:
            if self._status_grid_child is None:
                return

            if self._status_tab and self._status_grid_child.get_parent() == self._status_tab:
                self._status_tab.remove(self._status_grid_child)
            elif self._status_grid_child.get_parent():
                # If it has a different parent, remove from that parent
                self._status_grid_child.get_parent().remove(self._status_grid_child)

        except Exception as e:
            self.logger.error(f"Error removing status grid child: {e}")

    def update_content(self, torrent) -> None:
        """
        Update status tab content with torrent data.

        Args:
            torrent: Torrent object to display
        """
        try:
            import traceback

            torrent_name = getattr(torrent, "name", "None") if torrent else "None"
            self.logger.debug(
                f"🔍 STATUS TAB update_content called with torrent: {torrent_name}",
                extra={"class_name": self.__class__.__name__},
            )
            self.logger.debug(f"Call stack:\n{''.join(traceback.format_stack())}")

            # Remove existing content
            self._remove_current_grid()

            # Create new grid
            self._status_grid_child = self.create_grid()

            if not torrent:
                self._show_no_data_message()
                return

            # Get all compatible attributes from the torrent
            compatible_attributes = self._get_compatible_attributes()

            # Create grid rows for each attribute
            for attribute_index, attribute in enumerate(compatible_attributes):
                self._create_attribute_row(torrent, attribute, attribute_index)

            # Add the grid to the tab
            if self._status_tab:
                self._status_tab.append(self._status_grid_child)

        except Exception as e:
            self.logger.error(f"Error updating status tab content: {e}")

    def _show_no_data_message(self) -> None:
        """Show a message when no torrent data is available."""
        try:
            message_label = self.create_info_label("No torrent data available.")
            self.set_widget_margins(message_label, self.ui_margin_large)

            if self._status_tab:
                self._status_tab.append(message_label)

        except Exception as e:
            self.logger.error(f"Error showing no data message: {e}")

    def _get_compatible_attributes(self) -> list:
        """
        Get list of compatible attributes from the Attributes class.

        Returns:
            List of attribute names
        """
        try:
            ATTRIBUTES = Attributes
            return [prop.name.replace("-", "_") for prop in GObject.list_properties(ATTRIBUTES)]
        except Exception as e:
            self.logger.error(f"Error getting compatible attributes: {e}")
            return []

    def _create_attribute_row(self, torrent, attribute: str, row: int) -> None:
        """
        Create a row in the grid for a torrent attribute.

        Args:
            torrent: Torrent object
            attribute: Attribute name
            row: Row position in grid
        """
        try:
            # Get attribute value safely
            value = self.safe_get_property(torrent, attribute, "N/A")
            formatted_value = self.format_property_value(value)

            # Convert attribute name to human-readable display string
            display_name = self._convert_attribute_to_display_name(attribute)

            # Create the label pair
            self.create_label_pair(display_name, formatted_value, row, self._status_grid_child)

        except Exception as e:
            self.logger.error(f"Error creating attribute row for {attribute}: {e}")

    def _convert_attribute_to_display_name(self, attribute: str) -> str:
        """
        Convert attribute name to human-readable display string.

        Args:
            attribute: Raw attribute name (e.g., "filepath", "total_size")

        Returns:
            Display string for the attribute (e.g., "File Path", "Total Size")
        """
        # Get translation function from model
        translate_func = self.model.get_translate_func() if hasattr(self.model, "get_translate_func") else lambda x: x

        # Mapping of attribute names to translatable display strings
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
            # Add more mappings as needed
        }

        # Return the mapped display name or a formatted version of the attribute
        if attribute in attribute_display_map:
            return attribute_display_map[attribute]
        else:
            # Fallback: convert underscore_case to Title Case
            return attribute.replace("_", " ").title()

    def get_attribute_count(self) -> int:
        """
        Get the number of attributes displayed.

        Returns:
            Number of attributes
        """
        try:
            return len(self._get_compatible_attributes())
        except Exception:
            return 0

    def get_attribute_value(self, attribute: str) -> str:
        """
        Get the current value of a specific attribute.

        Args:
            attribute: Attribute name

        Returns:
            Formatted attribute value
        """
        try:
            if self._current_torrent:
                value = self.safe_get_property(self._current_torrent, attribute, "N/A")
                return self.format_property_value(value)
            return "N/A"
        except Exception as e:
            self.logger.error(f"Error getting attribute value for {attribute}: {e}")
            return "N/A"
