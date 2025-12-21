"""
Notifications settings tab for the settings dialog.

Handles configuration of toast notification appearance and behavior.
"""

# isort: skip_file

# fmt: off
from typing import Any, Dict, List

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import TranslationMixin  # noqa: E402
from .settings_mixins import UtilityMixin  # noqa: E402
from .settings_mixins import ValidationMixin  # noqa: E402

# fmt: on


class NotificationsTab(BaseSettingsTab, NotificationMixin, TranslationMixin, UtilityMixin, ValidationMixin):
    """
    Notifications settings tab component.

    Manages:
    - Toast notification appearance (position, animation)
    - Timeout settings per notification type
    - Display options
    """

    # Dropdown items for translation
    POSITION_ITEMS = ["Top Left", "Top Center", "Top Right", "Bottom Left", "Bottom Center", "Bottom Right"]
    ANIMATION_ITEMS = ["None", "Fade", "Slide"]

    # Position value mapping
    POSITION_VALUES = ["top-left", "top-center", "top-right", "bottom-left", "bottom-center", "bottom-right"]
    ANIMATION_VALUES = ["none", "fade", "slide"]

    # Widget mappings for auto-connect
    WIDGET_MAPPINGS: List[Dict[str, Any]] = [
        {
            "id": "notification_enabled",
            "name": "notification_enabled",
            "setting_key": "notification_settings.enabled",
            "type": bool,
        },
        {
            "id": "notification_show_statusbar",
            "name": "notification_show_statusbar",
            "setting_key": "notification_settings.show_in_statusbar",
            "type": bool,
        },
        {
            "id": "notification_sound",
            "name": "notification_sound",
            "setting_key": "notification_settings.sound_enabled",
            "type": bool,
        },
        {
            "id": "notification_animation_duration",
            "name": "notification_animation_duration",
            "setting_key": "notification_settings.animation_duration_ms",
            "type": int,
        },
        {
            "id": "notification_max_visible",
            "name": "notification_max_visible",
            "setting_key": "notification_settings.max_visible",
            "type": int,
        },
        {
            "id": "notification_info_timeout",
            "name": "notification_info_timeout",
            "setting_key": "notification_settings.info_timeout_ms",
            "type": int,
        },
        {
            "id": "notification_success_timeout",
            "name": "notification_success_timeout",
            "setting_key": "notification_settings.success_timeout_ms",
            "type": int,
        },
        {
            "id": "notification_warning_timeout",
            "name": "notification_warning_timeout",
            "setting_key": "notification_settings.warning_timeout_ms",
            "type": int,
        },
        {
            "id": "notification_error_timeout",
            "name": "notification_error_timeout",
            "setting_key": "notification_settings.error_timeout_ms",
            "type": int,
        },
    ]

    @property
    def tab_name(self) -> str:
        return "Notifications"

    def _init_widgets(self) -> None:
        """Initialize and cache notification widgets."""
        self.logger.trace("Initializing Notifications tab widgets")

        # Get widgets from builder
        widget_ids = [
            "notification_enabled",
            "notification_position",
            "notification_animation",
            "notification_animation_duration",
            "notification_max_visible",
            "notification_show_statusbar",
            "notification_sound",
            "notification_info_timeout",
            "notification_success_timeout",
            "notification_warning_timeout",
            "notification_error_timeout",
            "notification_test_button",
            "notification_reset_button",
        ]

        for widget_id in widget_ids:
            widget = self.builder.get_object(widget_id)
            if widget:
                self._widgets[widget_id] = widget
            else:
                self.logger.trace(f"Widget not found: {widget_id}")

    def _load_settings(self) -> None:
        """Load notification settings into UI."""
        self.logger.trace("Loading Notifications settings")

        try:
            notification_settings = self.app_settings.get("notification_settings", {})
            if notification_settings is None:
                notification_settings = {}

            # Load position dropdown
            position_dropdown = self.get_widget("notification_position")
            if position_dropdown:
                position = notification_settings.get("position", "top-right")
                try:
                    idx = self.POSITION_VALUES.index(position)
                    position_dropdown.set_selected(idx)
                except ValueError:
                    position_dropdown.set_selected(2)  # Default: top-right

            # Load animation dropdown
            animation_dropdown = self.get_widget("notification_animation")
            if animation_dropdown:
                animation = notification_settings.get("animation", "slide")
                try:
                    idx = self.ANIMATION_VALUES.index(animation)
                    animation_dropdown.set_selected(idx)
                except ValueError:
                    animation_dropdown.set_selected(2)  # Default: slide

            # Load enabled switch
            enabled_switch = self.get_widget("notification_enabled")
            if enabled_switch:
                self.set_switch_state(enabled_switch, notification_settings.get("enabled", True))

            # Load other switches
            statusbar_switch = self.get_widget("notification_show_statusbar")
            if statusbar_switch:
                self.set_switch_state(statusbar_switch, notification_settings.get("show_in_statusbar", True))

            sound_switch = self.get_widget("notification_sound")
            if sound_switch:
                self.set_switch_state(sound_switch, notification_settings.get("sound_enabled", False))

            # Load spin buttons
            spin_mappings = [
                ("notification_animation_duration", "animation_duration_ms", 300),
                ("notification_max_visible", "max_visible", 3),
                ("notification_info_timeout", "info_timeout_ms", 3000),
                ("notification_success_timeout", "success_timeout_ms", 3000),
                ("notification_warning_timeout", "warning_timeout_ms", 5000),
                ("notification_error_timeout", "error_timeout_ms", 0),
            ]

            for widget_id, setting_key, default in spin_mappings:
                spin = self.get_widget(widget_id)
                if spin:
                    value = notification_settings.get(setting_key, default)
                    spin.set_value(value)

        except Exception as e:
            self.logger.error(f"Error loading notification settings: {e}")

    def _connect_signals(self) -> None:
        """Connect notification tab signals."""
        self.logger.trace("Connecting Notifications tab signals")

        # Position dropdown
        position_dropdown = self.get_widget("notification_position")
        if position_dropdown:
            self.track_signal(
                position_dropdown,
                position_dropdown.connect("notify::selected", self.on_position_changed),
            )

        # Animation dropdown
        animation_dropdown = self.get_widget("notification_animation")
        if animation_dropdown:
            self.track_signal(
                animation_dropdown,
                animation_dropdown.connect("notify::selected", self.on_animation_changed),
            )

        # Test button
        test_button = self.get_widget("notification_test_button")
        if test_button:
            self.track_signal(
                test_button,
                test_button.connect("clicked", self.on_test_clicked),
            )

        # Reset button
        reset_button = self.get_widget("notification_reset_button")
        if reset_button:
            self.track_signal(
                reset_button,
                reset_button.connect("clicked", self.on_reset_clicked),
            )

    def _setup_dependencies(self) -> None:
        """Setup widget dependencies."""
        self.update_dependencies()

    def update_dependencies(self) -> None:
        """Update widget sensitivity based on enabled state."""
        enabled = True
        enabled_switch = self.get_widget("notification_enabled")
        if enabled_switch:
            enabled = enabled_switch.get_active()

        # Disable other widgets when notifications are disabled
        dependent_widgets = [
            "notification_position",
            "notification_animation",
            "notification_animation_duration",
            "notification_max_visible",
            "notification_show_statusbar",
            "notification_sound",
            "notification_info_timeout",
            "notification_success_timeout",
            "notification_warning_timeout",
            "notification_error_timeout",
            "notification_test_button",
        ]

        for widget_id in dependent_widgets:
            widget = self.get_widget(widget_id)
            if widget:
                widget.set_sensitive(enabled)

    def on_position_changed(self, dropdown: Gtk.DropDown, param: Any) -> None:
        """Handle position change."""
        if self._loading_settings:
            return

        idx = dropdown.get_selected()
        if 0 <= idx < len(self.POSITION_VALUES):
            position = self.POSITION_VALUES[idx]
            self.logger.trace(f"Notification position changed to: {position}")

    def on_animation_changed(self, dropdown: Gtk.DropDown, param: Any) -> None:
        """Handle animation change."""
        if self._loading_settings:
            return

        idx = dropdown.get_selected()
        if 0 <= idx < len(self.ANIMATION_VALUES):
            animation = self.ANIMATION_VALUES[idx]
            self.logger.trace(f"Notification animation changed to: {animation}")

    def on_test_clicked(self, button: Gtk.Button) -> None:
        """Show test notifications."""
        self.logger.trace("Test notification button clicked")

        # Try to show test notifications using the View's notification manager
        try:
            from d_fake_seeder.view import View

            if View.instance and hasattr(View.instance, "notification_manager"):
                nm = View.instance.notification_manager
                nm.show_info(self._("This is an info notification"))
                nm.show_success(self._("This is a success notification"))
                nm.show_warning(self._("This is a warning notification"))
                nm.show_error(self._("This is an error notification"))
            else:
                self.show_notification(self._("Test notifications sent"), "info")
        except Exception as e:
            self.logger.error(f"Error showing test notifications: {e}")
            self.show_notification(self._("Could not show test notifications"), "error")

    def on_reset_clicked(self, button: Gtk.Button) -> None:
        """Reset notification settings to defaults."""
        self._reset_tab_defaults()

    def _reset_tab_defaults(self) -> None:
        """Reset Notifications tab to default values."""
        try:
            # Reset enabled
            enabled_switch = self.get_widget("notification_enabled")
            if enabled_switch:
                self.set_switch_state(enabled_switch, True)

            # Reset position (top-right = index 2)
            position_dropdown = self.get_widget("notification_position")
            if position_dropdown:
                position_dropdown.set_selected(2)

            # Reset animation (slide = index 2)
            animation_dropdown = self.get_widget("notification_animation")
            if animation_dropdown:
                animation_dropdown.set_selected(2)

            # Reset spin buttons
            spin_defaults = [
                ("notification_animation_duration", 300),
                ("notification_max_visible", 3),
                ("notification_info_timeout", 3000),
                ("notification_success_timeout", 3000),
                ("notification_warning_timeout", 5000),
                ("notification_error_timeout", 0),
            ]

            for widget_id, default in spin_defaults:
                spin = self.get_widget(widget_id)
                if spin:
                    spin.set_value(default)

            # Reset switches
            statusbar_switch = self.get_widget("notification_show_statusbar")
            if statusbar_switch:
                self.set_switch_state(statusbar_switch, True)

            sound_switch = self.get_widget("notification_sound")
            if sound_switch:
                self.set_switch_state(sound_switch, False)

            self.update_dependencies()
            self.show_notification(self._("Notification settings reset to defaults"), "success")

        except Exception as e:
            self.logger.error(f"Error resetting Notifications tab: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current notification settings."""
        settings: Dict[str, Any] = {}

        try:
            # Position
            position_dropdown = self.get_widget("notification_position")
            if position_dropdown:
                idx = position_dropdown.get_selected()
                if 0 <= idx < len(self.POSITION_VALUES):
                    settings["notification_settings.position"] = self.POSITION_VALUES[idx]

            # Animation
            animation_dropdown = self.get_widget("notification_animation")
            if animation_dropdown:
                idx = animation_dropdown.get_selected()
                if 0 <= idx < len(self.ANIMATION_VALUES):
                    settings["notification_settings.animation"] = self.ANIMATION_VALUES[idx]

            # Enabled
            enabled_switch = self.get_widget("notification_enabled")
            if enabled_switch:
                settings["notification_settings.enabled"] = enabled_switch.get_active()

            # Show in statusbar
            statusbar_switch = self.get_widget("notification_show_statusbar")
            if statusbar_switch:
                settings["notification_settings.show_in_statusbar"] = statusbar_switch.get_active()

            # Sound
            sound_switch = self.get_widget("notification_sound")
            if sound_switch:
                settings["notification_settings.sound_enabled"] = sound_switch.get_active()

            # Spin buttons
            spin_mappings = [
                ("notification_animation_duration", "notification_settings.animation_duration_ms"),
                ("notification_max_visible", "notification_settings.max_visible"),
                ("notification_info_timeout", "notification_settings.info_timeout_ms"),
                ("notification_success_timeout", "notification_settings.success_timeout_ms"),
                ("notification_warning_timeout", "notification_settings.warning_timeout_ms"),
                ("notification_error_timeout", "notification_settings.error_timeout_ms"),
            ]

            for widget_id, setting_key in spin_mappings:
                spin = self.get_widget(widget_id)
                if spin:
                    settings[setting_key] = int(spin.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting notification settings: {e}")

        return settings

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace("NotificationsTab update view")
        self.model = model

        # Translate dropdown items
        self.translate_dropdown_items("notification_position", self.POSITION_ITEMS)
        self.translate_dropdown_items("notification_animation", self.ANIMATION_ITEMS)
