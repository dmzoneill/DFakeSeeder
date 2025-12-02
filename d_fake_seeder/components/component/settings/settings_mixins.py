"""
Mixin classes for settings dialog functionality.

These mixins provide reusable functionality that can be composed
into different settings tab classes.
"""

# isort: skip_file

# fmt: off
import random
import secrets
import string
from typing import Any, Callable, Dict, List, Optional, Protocol

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib  # noqa: E402
from gi.repository import Gtk  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.constants import SIZE_UNITS_BASIC  # noqa: E402

# fmt: on


class WidgetProviderProtocol(Protocol):
    """Protocol defining the interface for classes that provide widget access."""

    def get_widget(self, widget_id: str) -> Optional[Gtk.Widget]:
        """Get a widget by ID."""
        ...


class NotificationMixin:
    """
    Mixin for showing notifications in settings dialogs.

    Provides standardized notification display with different types
    and automatic timeout handling.
    """

    def show_notification(self, message: str, notification_type: str = "info", timeout: int = 3000) -> None:
        """
        Show a notification message.

        Args:
            message: Message to display
            notification_type: Type of notification ('info', 'success', 'warning', 'error')
            timeout: Timeout in milliseconds
        """
        try:
            # Get or create notification overlay
            overlay = getattr(self, "_notification_overlay", None)
            if not overlay:
                overlay = self._create_notification_overlay()

            # Create notification label
            notification_label = Gtk.Label(label=message)
            notification_label.set_halign(Gtk.Align.CENTER)
            notification_label.set_valign(Gtk.Align.START)

            # Add CSS classes based on type
            style_classes = {
                "info": "notification-info",
                "success": "notification-success",
                "warning": "notification-warning",
                "error": "notification-error",
            }

            css_class = style_classes.get(notification_type, "notification-info")
            notification_label.add_css_class(css_class)

            # Add to overlay
            overlay.add_overlay(notification_label)
            notification_label.show()

            # Auto-hide after timeout
            GLib.timeout_add(timeout, lambda: (self._hide_notification(notification_label), False)[1])

            logger.debug(f"Notification shown: {message} ({notification_type})")

        except Exception as e:
            logger.error(f"Error showing notification: {e}")

    def _create_notification_overlay(self) -> Gtk.Overlay:
        """Create notification overlay if it doesn't exist."""
        # This should be implemented by the class using this mixin
        # to integrate with their specific UI structure
        raise NotImplementedError("Notification overlay creation must be implemented by the using class")

    def _hide_notification(self, notification_label: Gtk.Label) -> bool:
        """
        Hide and remove a notification label.

        Args:
            notification_label: Label to hide

        Returns:
            False to stop the timeout callback
        """
        try:
            notification_label.hide()
            # Remove from parent if possible
            parent = notification_label.get_parent()
            if parent and hasattr(parent, "remove_overlay"):
                parent.remove_overlay(notification_label)
        except Exception as e:
            logger.error(f"Error hiding notification: {e}")

        return False  # Stop the timeout


class ValidationMixin:
    """
    Mixin for input validation in settings dialogs.

    Provides common validation methods and error handling.
    """

    def validate_port(self, port_value: Any) -> Dict[str, str]:
        """
        Validate a port number.

        Args:
            port_value: Port value to validate

        Returns:
            Dictionary with validation errors (empty if valid)
        """
        try:
            port = int(port_value)
            if port < 1 or port > 65535:
                return {"port": "Port must be between 1 and 65535"}
            return {}
        except (ValueError, TypeError):
            return {"port": "Port must be a valid number"}

    def validate_url(self, url_value: str) -> Dict[str, str]:
        """
        Validate a URL.

        Args:
            url_value: URL to validate

        Returns:
            Dictionary with validation errors (empty if valid)
        """
        if not url_value:
            return {}  # Empty URL might be valid depending on context

        # Basic URL validation
        if not (url_value.startswith("http://") or url_value.startswith("https://")):
            return {"url": "URL must start with http:// or https://"}

        return {}

    def validate_positive_number(self, value: Any, field_name: str = "value") -> Dict[str, str]:
        """
        Validate a positive number.

        Args:
            value: Value to validate
            field_name: Field name for error messages

        Returns:
            Dictionary with validation errors (empty if valid)
        """
        try:
            num = float(value)
            if num < 0:
                return {field_name: "Value must be positive"}
            return {}
        except (ValueError, TypeError):
            return {field_name: "Value must be a valid number"}

    def validate_range(self, value: Any, min_val: float, max_val: float, field_name: str = "value") -> Dict[str, str]:
        """
        Validate a value is within a specific range.

        Args:
            value: Value to validate
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            field_name: Field name for error messages

        Returns:
            Dictionary with validation errors (empty if valid)
        """
        try:
            num = float(value)
            if num < min_val or num > max_val:
                return {field_name: "Value must be between {} and {}".format(min_val, max_val)}
            return {}
        except (ValueError, TypeError):
            return {field_name: "Value must be a valid number"}


class KeyboardShortcutMixin:
    """
    Mixin for keyboard shortcut handling in settings dialogs.

    Provides common keyboard shortcut setup and handling.
    """

    def setup_tab_shortcuts(self, shortcuts: Dict[str, Callable]) -> None:
        """
        Set up keyboard shortcuts for this tab.

        Args:
            shortcuts: Dictionary of key_combination -> callback function
        """
        try:
            # Get the window to add shortcuts to
            window = getattr(self, "window", None)
            if not window:
                logger.warning("No window available for keyboard shortcuts")
                return

            # Add shortcuts
            for key_combo, callback in shortcuts.items():
                self._add_keyboard_shortcut(window, key_combo, callback)

            logger.debug(f"Set up {len(shortcuts)} keyboard shortcuts")

        except Exception as e:
            logger.error(f"Error setting up keyboard shortcuts: {e}")

    def _add_keyboard_shortcut(self, window: Gtk.Window, key_combo: str, callback: Callable) -> None:
        """
        Add a single keyboard shortcut.

        Args:
            window: Window to add shortcut to
            key_combo: Key combination (e.g., '<Ctrl>s')
            callback: Function to call when shortcut is pressed
        """
        try:
            # This is a simplified implementation
            # In a real implementation, you'd parse key_combo and set up proper GTK accelerators
            logger.debug(f"Would set up shortcut: {key_combo}")
            # TODO: Implement actual GTK accelerator setup
        except Exception as e:
            logger.error(f"Error adding keyboard shortcut {key_combo}: {e}")


class UtilityMixin:
    """
    Mixin for common utility functions in settings dialogs.

    Provides helper methods for common operations.
    """

    def generate_random_port(self, min_port: int = 49152, max_port: int = 65535) -> int:
        """
        Generate a random port number in the given range.

        Args:
            min_port: Minimum port number
            max_port: Maximum port number

        Returns:
            Random port number
        """
        return random.randint(min_port, max_port)

    def generate_secure_password(self, length: int = 16) -> str:
        """
        Generate a secure random password.

        Args:
            length: Length of password to generate

        Returns:
            Secure random password
        """
        # Use secure random generator
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        return password

    def format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes into human-readable string.

        Args:
            bytes_value: Number of bytes

        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        try:
            from .util.format_helpers import format_size

            return format_size(bytes_value)
        except Exception:
            # Fallback formatting
            units = SIZE_UNITS_BASIC
            size = float(bytes_value)
            unit_index = 0

            while size >= 1024 and unit_index < len(units) - 1:
                size /= 1024
                unit_index += 1

            return f"{size:.1f} {units[unit_index]}"

    def update_widget_sensitivity(self, widget_id: str, sensitive: bool) -> None:
        """
        Update widget sensitivity (enabled/disabled state).

        Args:
            widget_id: ID of widget to update
            sensitive: Whether widget should be sensitive
        """
        try:
            widget = self.get_widget(widget_id)  # type: ignore[attr-defined]
            if widget:
                widget.set_sensitive(sensitive)
        except Exception as e:
            logger.error(f"Error updating widget sensitivity for {widget_id}: {e}")

    def update_widget_visibility(self, widget_id: str, visible: bool) -> None:
        """
        Update widget visibility.

        Args:
            widget_id: ID of widget to update
            visible: Whether widget should be visible
        """
        try:
            widget = self.get_widget(widget_id)  # type: ignore[attr-defined]
            if widget:
                widget.set_visible(visible)
        except Exception as e:
            logger.error(f"Error updating widget visibility for {widget_id}: {e}")


class TranslationMixin:
    """
    Mixin for translating dropdown items that are defined in XML.

    GTK4 doesn't automatically translate <item translatable="yes"> elements at runtime,
    so this mixin provides methods to programmatically translate dropdown options.
    """

    # Type annotations for expected attributes from the class this mixin is mixed into
    logger: Any  # Expected to be provided by the class using this mixin
    builder: Any  # Expected to be provided by the class using this mixin

    def __init__(self, *args, **kwargs):
        """Initialize the translation mixin."""
        super().__init__(*args, **kwargs)
        self._language_change_connected = False

    def translate_dropdown_items(self, dropdown_id: str, items: Optional[List[Any]] = None) -> None:
        """
        Translate and update dropdown items.

        Args:
            dropdown_id: ID of the dropdown widget
            items: Optional list of strings to translate. If None, uses stored original items
        """
        try:
            # Skip language dropdown - it's managed separately
            if dropdown_id in ["settings_language", "language_dropdown"]:
                self.logger.debug(f"Skipping translation for language dropdown: {dropdown_id}")
                return

            dropdown = self.get_widget(dropdown_id)  # type: ignore[attr-defined]
            if not dropdown:
                self.logger.debug(f"Dropdown widget not found: {dropdown_id}")
                return

            # Store current selection index to preserve it
            current_selection = dropdown.get_selected()

            # Get translation function if available
            translate_func = (
                self.model.get_translate_func()
                if hasattr(self, "model") and hasattr(self.model, "get_translate_func")
                else lambda x: x
            )

            # Initialize original items cache if not exists
            if not hasattr(self, "_original_dropdown_items"):
                self._original_dropdown_items: Dict[str, List[Any]] = {}

            # If no items provided, use cached original items or extract and cache them
            if items is None:
                if dropdown_id in self._original_dropdown_items:
                    # Use cached original items
                    items = self._original_dropdown_items[dropdown_id]
                    self.logger.debug(f"Using cached original items for {dropdown_id}")
                else:
                    # Extract current items and cache them as original
                    items = self._extract_dropdown_items(dropdown)
                    if not items:
                        self.logger.debug(f"No items found in dropdown {dropdown_id}")
                        return

                    # Cache these as the original items
                    self._original_dropdown_items[dropdown_id] = items.copy()
                    self.logger.debug(f"Cached original items for {dropdown_id}")

            # Translate all items
            translated_items = [translate_func(item) for item in items]

            # Create new StringList with translated items
            string_list = Gtk.StringList()
            for item in translated_items:
                string_list.append(item)

            # Update dropdown model
            dropdown.set_model(string_list)

            # Restore previous selection if valid
            if 0 <= current_selection < len(items):
                dropdown.set_selected(current_selection)

            self.logger.debug(f"Successfully translated dropdown {dropdown_id} with {len(items)} items")

        except Exception as e:
            self.logger.error(f"Error translating dropdown {dropdown_id}: {e}", exc_info=True)

    def _extract_dropdown_items(self, dropdown) -> list:
        """
        Extract the original string items from a dropdown widget.

        Args:
            dropdown: Gtk.DropDown widget

        Returns:
            List of original string items from the dropdown
        """
        try:
            model = dropdown.get_model()
            if not model:
                return []

            # For Gtk.StringList model
            if hasattr(model, "get_n_items") and hasattr(model, "get_string"):
                items = []
                n_items = model.get_n_items()
                for i in range(n_items):
                    item_text = model.get_string(i)
                    if item_text:
                        items.append(item_text)
                return items

            logger.debug(f"Unsupported dropdown model type: {type(model)}")
            return []

        except Exception as e:
            logger.error(f"Error extracting dropdown items: {e}")
            return []

    def translate_all_dropdowns(self) -> None:
        """
        Automatically discover and translate all dropdown widgets in this tab.

        This method dynamically finds all Gtk.DropDown widgets and translates their items,
        avoiding the need for hard-coded dropdown lists. It preserves the current selection
        and only translates items that exist in the dropdown models.

        Note: The language dropdown (settings_language) is excluded as it's managed
        dynamically by the GeneralTab._populate_language_dropdown() method.
        """
        tab_name = getattr(self, "tab_name", "Unknown")

        # Only proceed if we have translation capability
        if not (hasattr(self, "model") and hasattr(self.model, "get_translate_func")):
            self.logger.debug("No translation capability available")
            return

        # Discover all dropdown widgets dynamically
        dropdowns_found = 0
        dropdowns_translated = 0

        try:
            cached_widgets = getattr(self, "_widgets", {})

            # Get all cached widgets and check for dropdowns
            for widget_id, widget in cached_widgets.items():
                if widget and hasattr(widget, "__class__") and "DropDown" in str(widget.__class__):
                    dropdowns_found += 1

                    # Skip language dropdowns - they're managed separately
                    if widget_id in ["settings_language", "language_dropdown"]:
                        self.logger.debug(f"Skipping special language dropdown: {widget_id}")
                        continue

                    # Translate this dropdown using its current items
                    try:
                        self.translate_dropdown_items(widget_id)
                        dropdowns_translated += 1
                        self.logger.debug(f"Translated dropdown: {widget_id}")
                    except Exception as e:
                        self.logger.error(f"Failed to translate dropdown {widget_id}: {e}")

            # Also check for any dropdowns that might not be cached yet
            if hasattr(self, "builder") and self.builder:
                self._discover_and_translate_uncached_dropdowns()

            self.logger.debug(
                f"Dropdown translation completed for {tab_name}: {dropdowns_translated}/{dropdowns_found} translated"
            )

        except Exception as e:
            self.logger.error(f"Error during dropdown discovery and translation: {e}", exc_info=True)

        # Connect to language change signal if not already connected
        self._connect_language_change_signal()

    def _discover_and_translate_uncached_dropdowns(self) -> None:
        """
        Discover and translate dropdown widgets that haven't been cached yet.

        This method scans the builder for DropDown widgets that might not have been
        accessed through get_widget() yet, ensuring comprehensive translation coverage.
        """
        try:
            # Get all objects from builder
            objects = self.builder.get_objects()

            for obj in objects:
                # Check if this is a DropDown widget
                if hasattr(obj, "__class__") and "DropDown" in str(obj.__class__):
                    # Try to get the widget ID
                    widget_id = None
                    if hasattr(obj, "get_buildable_id"):
                        widget_id = obj.get_buildable_id()

                    if widget_id:
                        # Skip if already processed or if it's a language dropdown
                        if widget_id in getattr(self, "_widgets", {}) or widget_id in [
                            "settings_language",
                            "language_dropdown",
                        ]:
                            continue

                        # Cache the widget and translate it
                        if hasattr(self, "_widgets"):
                            self._widgets[widget_id] = obj

                        try:
                            self.translate_dropdown_items(widget_id)
                            logger.debug(f"Discovered and translated uncached dropdown: {widget_id}")
                        except Exception as e:
                            logger.error(f"Failed to translate discovered dropdown {widget_id}: {e}")

        except Exception as e:
            logger.error(f"Error discovering uncached dropdowns: {e}")

    def translate_common_dropdowns(self) -> None:
        """
        Legacy method for backward compatibility.

        Now delegates to the dynamic translate_all_dropdowns() method.
        """
        self.translate_all_dropdowns()

    def _connect_language_change_signal(self) -> None:
        """Connect to language change signal to refresh dropdown translations."""
        # Safety check: initialize the attribute if it doesn't exist (for tabs with broken MRO)
        if not hasattr(self, "_language_change_connected"):
            self._language_change_connected = False

        if self._language_change_connected or not hasattr(self, "model") or not self.model:
            return

        try:
            # Connect to the model's language change signal
            if hasattr(self.model, "connect"):
                self.model.connect("language-changed", self._on_language_changed)
                self._language_change_connected = True
                logger.debug("Connected to language-changed signal for dropdown translation")
        except Exception as e:
            logger.error(f"Error connecting to language change signal: {e}")

    def _on_language_changed(self, source, new_language):
        """Handle language change events by refreshing dropdown translations."""
        try:
            logger.debug(f"Refreshing dropdown translations for language: {new_language}")
            # Dynamically translate all dropdowns
            self.translate_all_dropdowns()
        except Exception as e:
            logger.error(f"Error refreshing dropdown translations on language change: {e}")
