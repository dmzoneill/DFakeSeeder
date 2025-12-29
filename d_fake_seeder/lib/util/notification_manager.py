"""
Notification Manager - Manages toast notifications with queue and positioning.

Handles:
- Notification queue (max visible, FIFO)
- Positioning (corners, top/bottom center)
- Animations (fade, slide)
- Auto-dismiss timeouts per notification type
"""

# isort: skip_file

# fmt: off
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.notification_widget import (  # noqa: E402
    NotificationType,
    NotificationWidget,
)

# fmt: on


class NotificationPosition(Enum):
    """Position for notification stack."""

    TOP_LEFT = "top-left"
    TOP_CENTER = "top-center"
    TOP_RIGHT = "top-right"
    BOTTOM_LEFT = "bottom-left"
    BOTTOM_CENTER = "bottom-center"
    BOTTOM_RIGHT = "bottom-right"


class NotificationAnimation(Enum):
    """Animation style for notifications."""

    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"


# Default notification settings
DEFAULT_NOTIFICATION_SETTINGS = {
    "enabled": True,
    "position": "top-right",
    "animation": "slide",
    "animation_duration": 300,
    "max_visible": 3,
    "show_in_statusbar": True,
    "sound_enabled": False,
    # Per-type timeouts (ms, 0 = manual dismiss)
    "info_timeout": 3000,
    "success_timeout": 3000,
    "warning_timeout": 5000,
    "error_timeout": 0,
}


class NotificationManager:
    """
    Manages a queue of toast notifications.

    Features:
    - Queue system with max visible limit
    - Configurable positioning
    - Animation support (fade, slide)
    - Per-type timeout configuration
    - Non-blocking (doesn't interfere with keyboard)
    """

    def __init__(self, overlay: Gtk.Overlay, statusbar_callback: Optional[Callable] = None) -> None:
        """
        Initialize the notification manager.

        Args:
            overlay: The Gtk.Overlay to attach notifications to
            statusbar_callback: Optional callback to also show in statusbar
        """
        self.overlay = overlay
        self.statusbar_callback = statusbar_callback
        self.settings = AppSettings.get_instance()

        # Active notifications
        self._notifications: List[NotificationWidget] = []
        self._queue: List[Dict[str, Any]] = []

        # Container for notifications (positioned via CSS)
        # can_target=True: allows child widgets to receive mouse events
        # focusable=False: doesn't steal keyboard focus
        self._container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._container.set_can_target(True)
        self._container.set_can_focus(False)
        self._container.set_focusable(False)
        self._container.add_css_class("notification-container")

        # Add container to overlay
        self.overlay.add_overlay(self._container)

        # Apply initial position
        self._apply_position()

        # Connect to settings changes
        self.settings.connect("attribute-changed", self._on_settings_changed)

        logger.trace(
            "NotificationManager initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _get_settings(self) -> Dict[str, Any]:
        """Get notification settings with defaults."""
        notification_settings = self.settings.get("notification_settings", {})
        if notification_settings is None:
            notification_settings = {}
        # Merge with defaults
        result = DEFAULT_NOTIFICATION_SETTINGS.copy()
        result.update(notification_settings)
        return result

    def _apply_position(self) -> None:
        """Apply the current position setting to the container."""
        settings = self._get_settings()
        position = settings.get("position", "top-right")

        # Remove old position classes
        for pos in NotificationPosition:
            self._container.remove_css_class(f"notification-position-{pos.value}")

        # Add new position class
        self._container.add_css_class(f"notification-position-{position}")

        # Set alignment based on position
        if "left" in position:
            self._container.set_halign(Gtk.Align.START)
        elif "right" in position:
            self._container.set_halign(Gtk.Align.END)
        else:
            self._container.set_halign(Gtk.Align.CENTER)

        if "top" in position:
            self._container.set_valign(Gtk.Align.START)
        else:
            self._container.set_valign(Gtk.Align.END)

        # Margins
        self._container.set_margin_start(16)
        self._container.set_margin_end(16)
        self._container.set_margin_top(16)
        self._container.set_margin_bottom(16)

    def _on_settings_changed(self, source: Any, key: str, value: Any) -> None:
        """Handle settings changes."""
        if key.startswith("notification_settings"):
            self._apply_position()

    def show(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        message: str,
        notification_type: NotificationType = NotificationType.INFO,
        action_label: Optional[str] = None,
        action_callback: Optional[Callable[[], None]] = None,
        timeout_ms: Optional[int] = None,
    ) -> Optional[NotificationWidget]:
        """
        Show a notification.

        Args:
            message: The notification message
            notification_type: Type of notification
            action_label: Optional action button label
            action_callback: Optional action button callback
            timeout_ms: Override timeout (None = use settings)

        Returns:
            The NotificationWidget if shown, None if queued or disabled
        """
        settings = self._get_settings()

        # Check if notifications are enabled
        if not settings.get("enabled", True):
            # Still update statusbar if enabled
            if settings.get("show_in_statusbar", True) and self.statusbar_callback:
                self.statusbar_callback(message)
            return None

        # Determine timeout
        if timeout_ms is None:
            # Settings use info_timeout_ms format
            type_key = f"{notification_type.value}_timeout_ms"
            timeout_ms = settings.get(type_key, 3000)

        # Check max visible
        max_visible = settings.get("max_visible", 3)
        if len(self._notifications) >= max_visible:
            # Queue the notification
            self._queue.append(
                {
                    "message": message,
                    "type": notification_type,
                    "action_label": action_label,
                    "action_callback": action_callback,
                    "timeout_ms": timeout_ms,
                }
            )
            logger.trace(
                f"Notification queued (max {max_visible} visible): {message[:30]}...",
                extra={"class_name": self.__class__.__name__},
            )
            return None

        # Create notification widget
        widget = NotificationWidget(
            message=message,
            notification_type=notification_type,
            action_label=action_label,
            action_callback=action_callback,
            show_close_button=True,
        )

        # Connect closed signal
        widget.connect("closed", self._on_notification_closed)

        # Apply animation class
        animation = settings.get("animation", "slide")
        if animation != "none":
            widget.add_css_class(f"notification-{animation}-in")

        # Add to container and track
        self._notifications.append(widget)
        self._container.append(widget)

        # Set auto-dismiss
        if timeout_ms > 0:
            widget.set_auto_dismiss(timeout_ms)

        # Also show in statusbar if enabled
        if settings.get("show_in_statusbar", True) and self.statusbar_callback:
            self.statusbar_callback(message)

        logger.trace(
            f"Notification shown: {notification_type.value} - {message[:30]}...",
            extra={"class_name": self.__class__.__name__},
        )

        return widget

    def _on_notification_closed(self, widget: NotificationWidget) -> None:
        """Handle notification closed."""
        # Remove from tracking
        if widget in self._notifications:
            self._notifications.remove(widget)

        # Remove from container
        self._container.remove(widget)

        # Cleanup widget
        widget.cleanup()

        # Show next queued notification with a small delay
        # This gives visual feedback that the X button worked
        if self._queue:
            queued = self._queue.pop(0)

            # 300ms delay before showing next notification
            def _deferred_show() -> bool:
                self._show_from_queue(queued)
                return False  # Don't repeat

            GLib.timeout_add(300, _deferred_show)

    def _show_from_queue(self, queued: Dict[str, Any]) -> None:
        """
        Show a notification from the queue, bypassing the queue check.
        This prevents infinite re-queuing when multiple notifications close together.
        """
        settings = self._get_settings()

        # Check if we can still show (another notification might have appeared)
        max_visible = settings.get("max_visible", 3)
        if len(self._notifications) >= max_visible:
            # Put it back at the FRONT of the queue (it was already waiting)
            self._queue.insert(0, queued)
            return

        # Create notification widget
        widget = NotificationWidget(
            message=queued["message"],
            notification_type=queued["type"],
            action_label=queued.get("action_label"),
            action_callback=queued.get("action_callback"),
            show_close_button=True,
        )

        # Connect closed signal
        widget.connect("closed", self._on_notification_closed)

        # Apply animation class
        animation = settings.get("animation", "slide")
        if animation != "none":
            widget.add_css_class(f"notification-{animation}-in")

        # Add to container and tracking
        self._container.append(widget)
        self._notifications.append(widget)

        # Set auto-dismiss
        timeout_ms = queued.get("timeout_ms", 3000)
        if timeout_ms > 0:
            widget.set_auto_dismiss(timeout_ms)

        # Also update statusbar
        if settings.get("show_in_statusbar", True) and self.statusbar_callback:
            self.statusbar_callback(queued["message"])

    def show_info(self, message: str, **kwargs: Any) -> Optional[NotificationWidget]:
        """Show an info notification."""
        return self.show(message, NotificationType.INFO, **kwargs)

    def show_success(self, message: str, **kwargs: Any) -> Optional[NotificationWidget]:
        """Show a success notification."""
        return self.show(message, NotificationType.SUCCESS, **kwargs)

    def show_warning(self, message: str, **kwargs: Any) -> Optional[NotificationWidget]:
        """Show a warning notification."""
        return self.show(message, NotificationType.WARNING, **kwargs)

    def show_error(self, message: str, **kwargs: Any) -> Optional[NotificationWidget]:
        """Show an error notification."""
        return self.show(message, NotificationType.ERROR, **kwargs)

    def dismiss_all(self) -> None:
        """Dismiss all visible notifications."""
        for widget in self._notifications.copy():
            widget.dismiss()
        self._queue.clear()

    def cleanup(self) -> None:
        """Clean up all resources."""
        self.dismiss_all()
        if self._container.get_parent():
            self.overlay.remove_overlay(self._container)
