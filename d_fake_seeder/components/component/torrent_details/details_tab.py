"""
Details tab for torrent details.

Displays key torrent information like name, ID, file path, size, and progress.
"""

# isort: skip_file

# fmt: off
import gi

from d_fake_seeder.lib.util.constants import SIZE_UNITS_BASIC

from .base_tab import BaseTorrentTab
from .tab_mixins import DataUpdateMixin, UIUtilityMixin

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa

# fmt: on


class DetailsTab(BaseTorrentTab, DataUpdateMixin, UIUtilityMixin):
    """
    Details tab component for displaying key torrent information.

    Shows essential torrent details like name, ID, path, size, and progress.
    """

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Details"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "details_tab"

    def _init_widgets(self) -> None:
        """Initialize Details tab widgets."""
        # Cache the details grid widget
        self._details_grid = self.get_widget("details_grid")

    def clear_content(self) -> None:
        """Clear the details tab content."""
        try:
            self._clear_grid()

            # Show empty state
            super().clear_content()

        except Exception as e:
            self.logger.error(f"Error clearing details tab content: {e}")

    def _clear_grid(self) -> None:
        """Clear the grid without showing empty state (used internally)."""
        if self._details_grid:
            self.remove_all_children(self._details_grid)

    def update_content(self, torrent) -> None:
        """
        Update details tab content with torrent data.

        Args:
            torrent: Torrent object to display
        """
        try:
            self.logger.debug(
                "Updating details tab for torrent",
                extra={"class_name": self.__class__.__name__},
            )

            # Clear existing content (without showing empty state)
            self._clear_grid()

            if not self._details_grid:
                self.logger.error("Details grid not found")
                return

            # Get torrent details
            details = self._get_torrent_details(torrent)

            # Create grid rows for each detail
            for row, (label_text, value_text) in enumerate(details):
                self._create_detail_row(label_text, value_text, row)

        except Exception as e:
            self.logger.error(f"Error updating details tab content: {e}")

    def _get_torrent_details(self, torrent) -> list:
        """
        Get key torrent details for display.

        Args:
            torrent: Torrent object

        Returns:
            List of (label, value) tuples
        """
        try:
            if not torrent:
                return []

            # Get translation function from model
            translate_func = (
                self.model.get_translate_func() if hasattr(self.model, "get_translate_func") else lambda x: x
            )

            # Extract key torrent information directly from the torrent object
            # Try multiple sources for the name
            torrent_name = self.safe_get_property(torrent, "name", "")
            if not torrent_name and hasattr(torrent, "torrent_file") and torrent.torrent_file:
                torrent_name = getattr(torrent.torrent_file, "name", "Unknown")
            if not torrent_name:
                torrent_name = "Unknown"

            details = [
                (translate_func("Name"), torrent_name),
                (
                    translate_func("ID"),
                    str(self.safe_get_property(torrent, "id", "Unknown")),
                ),
                (
                    translate_func("File Path"),
                    self.safe_get_property(torrent, "filepath", "Unknown"),
                ),
                (
                    translate_func("Total Size"),
                    self._format_size(self.safe_get_property(torrent, "total_size", 0)),
                ),
                (
                    translate_func("Progress"),
                    self._format_progress(self.safe_get_property(torrent, "progress", 0)),
                ),
            ]

            # Add additional details if available
            additional_details = self._get_additional_details(torrent)
            details.extend(additional_details)

            return details

        except Exception as e:
            self.logger.error(f"Error getting torrent details: {e}")
            # Get translation function from model
            translate_func = (
                self.model.get_translate_func() if hasattr(self.model, "get_translate_func") else lambda x: x
            )
            return [(translate_func("Error"), "Unable to load torrent details")]

    def _get_additional_details(self, torrent) -> list:
        """
        Get additional torrent details.

        Args:
            torrent: Torrent object

        Returns:
            List of additional (label, value) tuples
        """
        try:
            additional = []

            # Add creation date if available
            creation_date = self.safe_get_property(torrent, "creation_date")
            if creation_date:
                additional.append(("Created", self._format_date(creation_date)))

            # Add comment if available
            comment = self.safe_get_property(torrent, "comment")
            if comment:
                additional.append(("Comment", comment))

            # Add created by if available
            created_by = self.safe_get_property(torrent, "created_by")
            if created_by:
                additional.append(("Created By", created_by))

            # Add piece length if available
            piece_length = self.safe_get_property(torrent, "piece_length")
            if piece_length:
                additional.append(("Piece Length", self._format_size(piece_length)))

            # Add number of pieces if available
            piece_count = self.safe_get_property(torrent, "piece_count")
            if piece_count:
                additional.append(("Pieces", str(piece_count)))

            return additional

        except Exception as e:
            self.logger.error(f"Error getting additional details: {e}")
            return []

    def _create_detail_row(self, label_text: str, value_text: str, row: int) -> None:
        """
        Create a row in the details grid.

        Args:
            label_text: Label text
            value_text: Value text
            row: Row position in grid
        """
        try:
            # Create label
            label = Gtk.Label(label=label_text, xalign=0)
            label.set_visible(True)
            label.set_halign(Gtk.Align.START)
            label.set_size_request(120, -1)

            # Create value label
            value = Gtk.Label(label=str(value_text), xalign=0)
            value.set_visible(True)
            value.set_halign(Gtk.Align.START)
            value.set_selectable(True)  # Enable text selection

            # Add to grid
            if self._details_grid is not None:
                self._details_grid.attach(label, 0, row, 1, 1)
                self._details_grid.attach(value, 1, row, 1, 1)

        except Exception as e:
            self.logger.error(f"Error creating detail row {label_text}={value_text}: {e}")

    def _format_size(self, size_value) -> str:
        """
        Format size value for display.

        Args:
            size_value: Size value to format

        Returns:
            Formatted size string
        """
        try:
            if not size_value or size_value == 0:
                return "0 B"

            size_bytes = int(size_value)
            return self._bytes_to_human_readable(size_bytes)

        except (ValueError, TypeError):
            return str(size_value)

    def _format_progress(self, progress_value) -> str:
        """
        Format progress value for display.

        Args:
            progress_value: Progress value to format

        Returns:
            Formatted progress string
        """
        try:
            if progress_value is None:
                return "0%"

            progress = float(progress_value)
            return f"{progress:.1f}%"

        except (ValueError, TypeError):
            return f"{progress_value}%"

    def _format_date(self, date_value) -> str:
        """
        Format date value for display.

        Args:
            date_value: Date value to format

        Returns:
            Formatted date string
        """
        try:
            # If it's already a string, return as-is
            if isinstance(date_value, str):
                return date_value

            # If it's a timestamp, format it
            import datetime

            if isinstance(date_value, (int, float)):
                dt = datetime.datetime.fromtimestamp(date_value)
                return dt.strftime("%Y-%m-%d %H:%M:%S")

            return str(date_value)

        except Exception as e:
            self.logger.error(f"Error formatting date: {e}")
            return str(date_value)

    def _bytes_to_human_readable(self, bytes_count: int) -> str:
        """
        Convert bytes to human-readable format.

        Args:
            bytes_count: Number of bytes

        Returns:
            Human-readable size string
        """
        try:
            # Try to use the localization utility if available
            try:
                from .util.format_helpers import format_size

                return format_size(bytes_count)
            except ImportError:
                pass

            # Fallback formatting
            units = SIZE_UNITS_BASIC
            size = float(bytes_count)
            unit_index = 0

            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1

            return f"{size:.1f} {units[unit_index]}"

        except Exception as e:
            self.logger.error(f"Error formatting bytes: {e}")
            return f"{bytes_count} B"

    def get_detail_value(self, label: str) -> str:
        """
        Get the current value of a specific detail.

        Args:
            label: Detail label to look up

        Returns:
            Detail value or empty string if not found
        """
        try:
            if not self._current_torrent:
                return ""

            details = self._get_torrent_details(self._current_torrent)
            for detail_label, detail_value in details:
                if detail_label == label:
                    return detail_value

            return ""

        except Exception as e:
            self.logger.error(f"Error getting detail value for {label}: {e}")
            return ""
