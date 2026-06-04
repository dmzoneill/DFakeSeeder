"""
Notification Widget - Toast-style notification component.

A modern, animated notification toast with support for different types,
icons, and optional action buttons.
"""

# isort: skip_file

# fmt: off
from enum import Enum
from typing import Callable, Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib, GObject  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class NotificationType(Enum):
    """Notification severity/type."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


# Icons for each notification type
NOTIFICATION_ICONS = {
    NotificationType.INFO: "dialog-information-symbolic",
    NotificationType.SUCCESS: "emblem-ok-symbolic",
    NotificationType.WARNING: "dialog-warning-symbolic",
    NotificationType.ERROR: "dialog-error-symbolic",
}

# Fallback emoji icons if symbolic icons unavailable
NOTIFICATION_EMOJI = {
    NotificationType.INFO: "ℹ️",
    NotificationType.SUCCESS: "✅",
    NotificationType.WARNING: "⚠️",
    NotificationType.ERROR: "❌",
}


class NotificationWidget(Gtk.Frame):
    """
    A single toast notification widget.

    Uses Gtk.Frame as base for proper background rendering in GTK4.

    Features:
    - Icon based on notification type
    - Message text with optional markup
    - Close button
    - Optional action button
    - CSS styling for different types
    - Non-focusable (doesn't interfere with keyboard)
    """

    __gsignals__ = {
        "closed": (GObject.SignalFlags.RUN_FIRST, None, ()),
        "action-clicked": (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    def __init__(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable[[], None]] = None,
        show_close_button: bool = True,
    ) -> None:
        """
        Initialize notification widget.

        Args:
            message: The notification message text
            notification_type: Type of notification (info, success, warning, error)
            action_label: Optional label for action button
            action_callback: Optional callback when action button clicked
            show_close_button: Whether to show the close (X) button
        """
        super().__init__()

        self.message = message
        self.notification_type = notification_type
        self.action_callback = action_callback
        self._timeout_id: Optional[int] = None

        # CRITICAL: Block clicks but don't steal keyboard focus
        # can_target=True: captures mouse events (prevents click-through)
        # focusable=False: doesn't steal keyboard focus
        self.set_can_target(True)
        self.set_can_focus(False)
        self.set_focusable(False)

        # Add CSS classes for styling
        self.add_css_class("notification-toast")
        self.add_css_class(f"notification-{notification_type.value}")

        # Apply inline CSS for background - GTK4 Frame needs this approach
        self._apply_background_style(notification_type)

        # Margins on the frame
        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(4)
        self.set_margin_bottom(4)

        # Create inner box for content
        # can_target=True: allows buttons inside to be clickable
        self._content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self._content_box.set_can_target(True)
        self._content_box.set_can_focus(False)
        self.set_child(self._content_box)

        self._build_ui(message, notification_type, action_label, show_close_button)

        logger.trace(
            f"NotificationWidget created: {notification_type.value} - {message[:30]}...",
            extra={"class_name": self.__class__.__name__},
        )

    def _apply_background_style(self, notification_type: NotificationType) -> None:
        """Apply inline CSS for background color - GTK4 requires this approach."""
        # Background colors for each notification type
        bg_colors = {
            NotificationType.INFO: "#2a3a4d",
            NotificationType.SUCCESS: "#2a3d2a",
            NotificationType.WARNING: "#3d3a2a",
            NotificationType.ERROR: "#3d2a2a",
        }
        border_colors = {
            NotificationType.INFO: "#3584e4",
            NotificationType.SUCCESS: "#33d17a",
            NotificationType.WARNING: "#f6d32d",
            NotificationType.ERROR: "#e01b24",
        }

        bg_color = bg_colors.get(notification_type, "#2d2d2d")
        border_color = border_colors.get(notification_type, "#3584e4")

        # Create inline CSS for this specific widget
        css = f"""
            frame {{
                background-color: {bg_color};
                border-radius: 12px;
                border-left: 5px solid {border_color};
                padding: 12px 16px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            }}
            frame > box {{
                background-color: {bg_color};
            }}
            label {{
                color: #ffffff;
            }}
        """

        # Apply CSS provider to this widget
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string(css)
        self.get_style_context().add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 100)

    def _build_ui(
        self,
        message: str,
        notification_type: NotificationType,
        action_label: Optional[str],
        show_close_button: bool,
    ) -> None:
        """Build the notification UI."""
        # Icon
        icon_name = NOTIFICATION_ICONS.get(notification_type, "dialog-information-symbolic")
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(24)
        icon.add_css_class("notification-icon")
        icon.set_can_target(False)
        icon.set_can_focus(False)
        self._content_box.append(icon)

        # Message label (expandable)
        label = Gtk.Label(label=message)
        label.set_wrap(True)
        label.set_wrap_mode(2)  # WORD_CHAR
        label.set_max_width_chars(50)
        label.set_xalign(0)
        label.set_hexpand(True)
        label.add_css_class("notification-message")
        label.set_can_target(False)
        label.set_can_focus(False)
        self._content_box.append(label)

        # Action button (optional)
        if action_label:
            action_btn = Gtk.Button(label=action_label)
            action_btn.add_css_class("notification-action")
            action_btn.add_css_class("flat")
            # Action button CAN be clicked
            action_btn.set_can_target(True)
            action_btn.set_can_focus(False)  # But not keyboard focused
            action_btn.connect("clicked", self._on_action_clicked)
            self._content_box.append(action_btn)

        # Close button
        if show_close_button:
            close_btn = Gtk.Button()
            close_btn.set_icon_name("window-close-symbolic")
            close_btn.add_css_class("notification-close")
            close_btn.add_css_class("flat")
            close_btn.add_css_class("circular")
            # Close button CAN be clicked
            close_btn.set_can_target(True)
            close_btn.set_can_focus(False)  # But not keyboard focused
            close_btn.connect("clicked", self._on_close_clicked)
            self._content_box.append(close_btn)

    def _on_close_clicked(self, button: Gtk.Button) -> None:
        """Handle close button click."""
        self.dismiss()

    def _on_action_clicked(self, button: Gtk.Button) -> None:
        """Handle action button click."""
        if self.action_callback:
            try:
                self.action_callback()
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(f"Error in notification action callback: {e}", exc_info=True)
        self.emit("action-clicked")
        self.dismiss()

    def dismiss(self) -> None:
        """Dismiss the notification."""
        self._cancel_timeout()
        # Add fade-out animation class
        self.add_css_class("notification-closing")
        # Emit closed signal after brief animation delay
        GLib.timeout_add(200, self._emit_closed)

    def _emit_closed(self) -> bool:
        """Emit the closed signal."""
        self.emit("closed")
        return False  # Don't repeat

    def set_auto_dismiss(self, timeout_ms: int) -> None:
        """
        Set auto-dismiss timeout.

        Args:
            timeout_ms: Milliseconds before auto-dismiss (0 = no auto-dismiss)
        """
        self._cancel_timeout()
        if timeout_ms > 0:
            self._timeout_id = GLib.timeout_add(timeout_ms, self._on_timeout)

    def _on_timeout(self) -> bool:
        """Handle auto-dismiss timeout."""
        self._timeout_id = None
        self.dismiss()
        return False  # Don't repeat

    def _cancel_timeout(self) -> None:
        """Cancel any pending timeout."""
        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

    def cleanup(self) -> None:
        """Clean up resources."""
        self._cancel_timeout()
