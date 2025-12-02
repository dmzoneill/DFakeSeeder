"""
Files tab for torrent details.

Displays torrent file listing with file paths and sizes.
"""

# isort: skip_file

# fmt: off
import gi

from d_fake_seeder.lib.util.constants import SIZE_UNITS_BASIC

from .base_tab import BaseTorrentTab
from .tab_mixins import DataUpdateMixin, UIUtilityMixin

gi.require_version("Gtk", "4.0")

# fmt: on


class FilesTab(BaseTorrentTab, DataUpdateMixin, UIUtilityMixin):
    """
    Files tab component for displaying torrent file information.

    Shows all files in the torrent with their paths and sizes.
    """

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Files"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "files_tab"

    def _init_widgets(self) -> None:
        """Initialize Files tab widgets."""
        # Cache the main tab widget
        self._files_tab = self.get_widget("files_tab")
        self._files_grid_child = None

    def clear_content(self) -> None:
        """Clear the files tab content."""
        try:
            # Clear ALL children from the files tab, not just the grid
            if self._files_tab:
                self.remove_all_children(self._files_tab)
            self._files_grid_child = None

        except Exception as e:
            self.logger.error(f"Error clearing files tab content: {e}")

    def _remove_current_grid(self) -> None:
        """Remove the current grid child from the files tab."""
        try:
            # Clear ALL children to prevent accumulation
            if self._files_tab:
                self.remove_all_children(self._files_tab)
            self._files_grid_child = None

        except Exception as e:
            self.logger.error(f"Error removing files grid child: {e}")

    def update_content(self, attributes) -> None:
        """
        Update files tab content with torrent file data.

        Args:
            attributes: Attributes object from the torrent list
        """
        try:
            self.logger.debug(
                f"🔄 FILES TAB: Starting update_content for attributes: {attributes}",
                extra={"class_name": self.__class__.__name__},
            )

            if attributes is None:
                self.logger.warning(
                    "🚨 FILES TAB: Received None attributes in update_content",
                    extra={"class_name": self.__class__.__name__},
                )
                self.clear_content()
                return

            # Remove existing content
            self.logger.debug(
                "📂 FILES TAB: Removing existing grid content",
                extra={"class_name": self.__class__.__name__},
            )
            self._remove_current_grid()

            # Create new grid
            self.logger.debug(
                "🏗️ FILES TAB: Creating new grid",
                extra={"class_name": self.__class__.__name__},
            )
            self._files_grid_child = self.create_grid()

            # Get torrent files
            self.logger.debug(
                "🔍 FILES TAB: Calling _get_torrent_files()",
                extra={"class_name": self.__class__.__name__},
            )
            files_data = self._get_torrent_files(attributes)
            self.logger.debug(
                f"📊 FILES TAB: Retrieved {len(files_data) if files_data else 0} files from torrent",
                extra={"class_name": self.__class__.__name__},
            )

            if not files_data:
                self._show_no_files_message()
                return

            # Create grid rows for each file
            for file_index, (fullpath, length) in enumerate(files_data):
                self._create_file_row(fullpath, length, file_index)

            # Add the grid to the tab
            if self._files_tab:
                self._files_tab.append(self._files_grid_child)

        except Exception as e:
            self.logger.error(f"Error updating files tab content: {e}")

    def _get_torrent_files(self, attributes) -> list:
        """
        Get files from the torrent.

        Args:
            attributes: Attributes object from the torrent list

        Returns:
            List of (fullpath, length) tuples
        """
        try:
            self.logger.debug(
                "🚀 FILES TAB: _get_torrent_files() started",
                extra={"class_name": self.__class__.__name__},
            )

            if not attributes:
                self.logger.warning(
                    "🚨 FILES TAB: No attributes provided to _get_torrent_files",
                    extra={"class_name": self.__class__.__name__},
                )
                return []

            self.logger.debug(
                f"🔍 FILES TAB: Attributes object type: {type(attributes)}",
                extra={"class_name": self.__class__.__name__},
            )
            self.logger.debug(
                f"🔍 FILES TAB: Attributes has get_torrent_file method: {hasattr(attributes, 'get_torrent_file')}",
                extra={"class_name": self.__class__.__name__},
            )

            # Get the actual Torrent object from the model using the attributes
            self.logger.debug(
                "🔍 FILES TAB: Getting torrent object from model using attributes",
                extra={"class_name": self.__class__.__name__},
            )
            torrent = self.model.get_torrent_by_attributes(attributes)
            if not torrent:
                self.logger.warning(
                    f"🚨 FILES TAB: No torrent found for attributes {getattr(attributes, 'id', 'unknown')}",
                    extra={"class_name": self.__class__.__name__},
                )
                return []

            self.logger.debug(
                f"✅ FILES TAB: Found torrent object: {type(torrent)}",
                extra={"class_name": self.__class__.__name__},
            )
            self.logger.debug(
                f"🔍 FILES TAB: Torrent has get_torrent_file method: {hasattr(torrent, 'get_torrent_file')}",
                extra={"class_name": self.__class__.__name__},
            )

            # Get torrent file and extract files directly from the torrent
            self.logger.debug(
                "📁 FILES TAB: Calling torrent.get_torrent_file()",
                extra={"class_name": self.__class__.__name__},
            )
            torrent_file = torrent.get_torrent_file()
            self.logger.debug(
                f"📁 FILES TAB: Torrent file retrieved: {torrent_file} (type: {type(torrent_file)})",
                extra={"class_name": self.__class__.__name__},
            )
            if not torrent_file:
                self.logger.warning(
                    f"🚨 FILES TAB: No torrent file found for torrent {getattr(torrent, 'id', 'unknown')}",
                    extra={"class_name": self.__class__.__name__},
                )
                return []

            self.logger.debug(
                f"📋 FILES TAB: Torrent file has get_files method: {hasattr(torrent_file, 'get_files')}",
                extra={"class_name": self.__class__.__name__},
            )

            # Get multi-file torrent files
            self.logger.debug(
                "📂 FILES TAB: Calling torrent_file.get_files()",
                extra={"class_name": self.__class__.__name__},
            )
            files = list(torrent_file.get_files())
            self.logger.debug(
                f"📂 FILES TAB: Multi-file torrent files: {len(files)} files",
                extra={"class_name": self.__class__.__name__},
            )

            if files:
                self.logger.debug(
                    f"📝 FILES TAB: Sample file data: {files[0] if files else 'none'}",
                    extra={"class_name": self.__class__.__name__},
                )

            # If no files (single-file torrent), get the single file info
            if not files:
                self.logger.debug(
                    "🔍 FILES TAB: No multi-file data, checking single file",
                    extra={"class_name": self.__class__.__name__},
                )
                single_file_info = torrent_file.get_single_file_info()
                self.logger.debug(
                    f"📄 FILES TAB: Single file info: {single_file_info}",
                    extra={"class_name": self.__class__.__name__},
                )
                if single_file_info:
                    # Use the torrent name as the filename for single-file torrents
                    filename = getattr(attributes, "name", "unknown.file")
                    files = [(filename, single_file_info)]
                    self.logger.debug(
                        f"✅ FILES TAB: Created single file entry: {files}",
                        extra={"class_name": self.__class__.__name__},
                    )

            self.logger.debug(
                f"🎯 FILES TAB: Final files list: {len(files)} files - {files[:2] if files else 'empty'}",
                extra={"class_name": self.__class__.__name__},
            )
            return files

        except Exception as e:
            self.logger.error(f"Error getting torrent files: {e}")
            return []

    def _create_file_row(self, fullpath: str, length: str, row: int) -> None:
        """
        Create a row in the grid for a torrent file.

        Args:
            fullpath: Full file path
            length: File size/length
            row: Row position in grid
        """
        try:
            # Format the file size for better display
            formatted_length = self._format_file_size(length)

            # Create the label pair for file path and size
            self.create_label_pair(fullpath, formatted_length, row, self._files_grid_child)

        except Exception as e:
            self.logger.error(f"Error creating file row for {fullpath}: {e}")

    def _format_file_size(self, size_str: str) -> str:
        """
        Format file size for display.

        Args:
            size_str: Size as string

        Returns:
            Formatted size string
        """
        try:
            # If it's already a formatted string, return as-is
            if isinstance(size_str, str) and not size_str.isdigit():
                return size_str

            # Convert to integer and format
            size_bytes = int(size_str)
            return self._bytes_to_human_readable(size_bytes)

        except (ValueError, TypeError):
            return str(size_str)

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
                from lib.util.format_helpers import format_size

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

    def _show_no_files_message(self) -> None:
        """Show a message when no files are available."""
        try:
            # Create a grid if it doesn't exist
            if not self._files_grid_child:
                self._files_grid_child = self.create_grid()

            message_label = self.create_info_label("No files available for this torrent.")
            self.set_widget_margins(message_label, self.ui_margin_large)

            # Add message to the grid instead of directly to the tab
            if self._files_grid_child:
                self._files_grid_child.attach(message_label, 0, 0, 2, 1)

            # Add the grid to the tab
            if self._files_tab and self._files_grid_child:
                self._files_tab.append(self._files_grid_child)

        except Exception as e:
            self.logger.error(f"Error showing no files message: {e}")

    def get_file_count(self) -> int:
        """
        Get the number of files in the current torrent.

        Returns:
            Number of files
        """
        try:
            if self._current_torrent:
                files_data = self._get_torrent_files(self._current_torrent)
                return len(files_data)
            return 0
        except Exception:
            return 0

    def get_total_size(self) -> int:
        """
        Get the total size of all files.

        Returns:
            Total size in bytes
        """
        try:
            if not self._current_torrent:
                return 0

            files_data = self._get_torrent_files(self._current_torrent)
            total_size = 0

            for _, size_str in files_data:
                try:
                    total_size += int(size_str)
                except (ValueError, TypeError):
                    continue

            return total_size

        except Exception as e:
            self.logger.error(f"Error calculating total size: {e}")
            return 0
