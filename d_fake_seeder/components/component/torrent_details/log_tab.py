"""
Log tab for torrent details.

Displays application log messages in a scrollable text view with batched updates.
"""

# isort: skip_file

# fmt: off
import logging
from typing import List, Optional

import gi

from .base_tab import BaseTorrentTab
from .tab_mixins import PerformanceMixin, UIUtilityMixin

gi.require_version("Gtk", "4.0")
from gi.repository import GLib  # noqa: E402
from gi.repository import Gtk  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class LogTab(BaseTorrentTab, UIUtilityMixin, PerformanceMixin):
    """
    Log tab component for displaying application log messages.

    Captures log messages and displays them in a text view with performance optimizations.
    """

    def __init__(self, builder: Gtk.Builder, model):
        """Initialize the log tab."""
        super().__init__(builder, model)
        PerformanceMixin.__init__(self)

        # Log batching for performance
        self._log_message_queue: List[str] = []
        self._log_flush_timer = None
        self._log_handler: Optional[logging.StreamHandler] = None

        # Get log buffer limit from settings
        ui_settings = getattr(self.settings, "ui_settings", {})
        self._log_buffer_max_lines = ui_settings.get("log_buffer_max_lines", 1000)

        # Set up log handler
        self._setup_log_viewer_handler()

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Log"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "log_tab"

    def _init_widgets(self) -> None:
        """Initialize Log tab widgets."""
        # Cache the log widgets
        self._log_scroll = self.get_widget("log_scroll")
        self._log_viewer = self.get_widget("log_viewer")

    def clear_content(self) -> None:
        """Clear the log tab content."""
        try:
            if self._log_viewer:
                buffer = self._log_viewer.get_buffer()
                buffer.set_text("")

        except Exception as e:
            self.logger.error(f"Error clearing log tab content: {e}")

    def update_content(self, torrent) -> None:
        """
        Update log tab content.

        Note: Log tab content is updated continuously via log handler,
        not based on torrent selection.

        Args:
            torrent: Torrent object (not used for log tab)
        """
        # Log tab doesn't need torrent-specific updates
        # Content is updated via the log handler
        pass

    def _setup_log_viewer_handler(self) -> None:
        """Set up log handler to capture messages for the log viewer."""
        try:

            def update_textview(record):
                """Update text view with log record."""
                msg = f"{record.levelname}: {record.getMessage()}\n"
                self._queue_log_message(msg)

            # Create and configure handler
            self._log_handler = logging.StreamHandler()
            self._log_handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
            self._log_handler.setLevel(logging.DEBUG)
            self._log_handler.emit = update_textview  # type: ignore[method-assign]

            # Add handler to the main logger
            logger.addHandler(self._log_handler)

            self.logger.debug("Log viewer handler set up successfully")

        except Exception as e:
            self.logger.error(f"Error setting up log viewer handler: {e}")

    def _queue_log_message(self, message: str) -> None:
        """
        Queue a log message for batched updates.

        Args:
            message: Log message to queue
        """
        try:
            self._log_message_queue.append(message)

            # Schedule flush if not already scheduled
            if self._log_flush_timer is None:
                # Use a fraction of tickspeed for responsive log updates
                flush_delay = max(1, int(getattr(self.settings, "tickspeed", 3) / 3))
                self._log_flush_timer = GLib.timeout_add_seconds(flush_delay, self._flush_log_messages)

        except Exception as e:
            self.logger.error(f"Error queuing log message: {e}")

    def _flush_log_messages(self) -> bool:
        """
        Flush queued log messages to the text view.

        Returns:
            False to stop the timer
        """
        try:
            if self._log_message_queue and self._log_viewer:
                # Combine all queued messages
                combined_msg = "".join(self._log_message_queue)
                self._log_message_queue.clear()

                # Single UI update for all messages
                GLib.idle_add(lambda: (self._update_text_buffer(combined_msg), False)[1])

        except Exception as e:
            self.logger.error(f"Error flushing log messages: {e}")

        # Reset timer
        self._log_flush_timer = None
        return False  # Don't repeat

    def _update_text_buffer(self, msg: str) -> bool:
        """
        Update the text buffer with new log messages.

        Args:
            msg: Message to add

        Returns:
            False to stop idle callback
        """
        try:
            if not self._log_viewer:
                return False

            buffer = self._log_viewer.get_buffer()

            # Insert message at cursor position
            buffer.insert_at_cursor(msg)

            # Trim buffer if it gets too long
            _, end_iter = buffer.get_bounds()
            end_line = end_iter.get_line()

            if end_line > self._log_buffer_max_lines:
                start_iter = buffer.get_start_iter()
                start_iter.set_line(end_line - self._log_buffer_max_lines)
                buffer.delete(start_iter, buffer.get_start_iter())

            # Auto-scroll to bottom
            mark = buffer.get_insert()
            self._log_viewer.scroll_mark_onscreen(mark)

        except Exception as e:
            # Use logger error to capture this properly
            logger.error(f"Error updating text buffer: {e}", "LogTab", exc_info=True)

        return False  # Stop idle callback

    def set_log_level(self, level: int) -> None:
        """
        Set the log level for the handler.

        Args:
            level: Logging level (e.g., logging.DEBUG, logging.INFO)
        """
        try:
            if self._log_handler:
                self._log_handler.setLevel(level)
                self.logger.info(f"Log level set to {logging.getLevelName(level)}")

        except Exception as e:
            self.logger.error(f"Error setting log level: {e}")

    def add_manual_message(self, message: str, level: str = "INFO") -> None:
        """
        Manually add a message to the log.

        Args:
            message: Message to add
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        try:
            formatted_msg = f"{level}: {message}\n"
            self._queue_log_message(formatted_msg)

        except Exception as e:
            self.logger.error(f"Error adding manual message: {e}")

    def save_log_to_file(self, file_path: str) -> bool:
        """
        Save current log content to file.

        Args:
            file_path: Path to save log file

        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._log_viewer:
                return False

            buffer = self._log_viewer.get_buffer()
            start_iter, end_iter = buffer.get_bounds()
            text = buffer.get_text(start_iter, end_iter, False)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)

            self.logger.info(f"Log saved to {file_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving log to file: {e}")
            return False

    def get_log_content(self) -> str:
        """
        Get current log content.

        Returns:
            Log content as string
        """
        try:
            if not self._log_viewer:
                return ""

            buffer = self._log_viewer.get_buffer()
            start_iter, end_iter = buffer.get_bounds()
            return buffer.get_text(start_iter, end_iter, False)

        except Exception as e:
            self.logger.error(f"Error getting log content: {e}")
            return ""

    def get_line_count(self) -> int:
        """
        Get current number of lines in log.

        Returns:
            Number of lines
        """
        try:
            if not self._log_viewer:
                return 0

            buffer = self._log_viewer.get_buffer()
            return buffer.get_line_count()

        except Exception as e:
            self.logger.error(f"Error getting line count: {e}")
            return 0

    def cleanup(self) -> None:
        """Cleanup resources when tab is destroyed."""
        try:
            # Remove log handler
            if self._log_handler:
                logger.removeHandler(self._log_handler)
                self._log_handler = None

            # Cancel pending timer
            if self._log_flush_timer:
                GLib.source_remove(self._log_flush_timer)
                self._log_flush_timer = None

            # Clear message queue
            self._log_message_queue.clear()

            # Call parent cleanup
            super().cleanup()

        except Exception as e:
            self.logger.error(f"Error cleaning up log tab: {e}")
