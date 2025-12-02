"""
Base class for settings tab components.

Provides common functionality and interface for all settings tabs.
"""

# isort: skip_file

# fmt: off
from abc import abstractmethod
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa

from d_fake_seeder.domain.app_settings import AppSettings  # noqa
from d_fake_seeder.lib.logger import logger  # noqa

from ..base_component import Component  # noqa

# fmt: on


class BaseSettingsTab(Component):
    """
    Abstract base class for settings tab components.

    Each tab is responsible for:
    - Managing its specific UI elements
    - Handling its signal connections
    - Loading and saving its settings
    - Providing validation and dependencies
    """

    def __init__(self, builder: Gtk.Builder, app_settings: AppSettings):
        """
        Initialize the base tab.

        Args:
            builder: GTK Builder instance with UI loaded
            app_settings: Application settings instance
        """
        logger.debug("Starting initialization for", "BaseTab")
        super().__init__()

        self.builder = builder
        self.app_settings = app_settings
        self.logger = logger

        # Store UI widgets specific to this tab
        self._widgets: Dict[str, Any] = {}

        # Initialize tab-specific setup
        logger.debug("About to call _init_widgets for", "BaseTab")
        self._init_widgets()
        logger.debug("Completed _init_widgets for", "BaseTab")

        # Load settings BEFORE connecting signals to avoid circular loops
        logger.debug("About to call _load_settings for", "BaseTab")
        self._load_settings()
        logger.debug("Completed _load_settings for", "BaseTab")

        # Connect signals AFTER loading settings
        logger.debug("About to call _connect_signals for", "BaseTab")
        self._connect_signals()
        logger.debug("Completed _connect_signals for", "BaseTab")

        logger.debug("About to call _setup_dependencies for", "BaseTab")
        self._setup_dependencies()
        logger.debug("Completed _setup_dependencies for", "BaseTab")
        logger.debug("===== FULLY COMPLETED  =====", "BaseTab")

    @property
    @abstractmethod
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        pass

    @abstractmethod
    def _init_widgets(self) -> None:
        """Initialize and cache tab-specific widgets."""
        pass

    @abstractmethod
    def _connect_signals(self) -> None:
        """Connect all signal handlers for this tab."""
        pass

    def _disconnect_signals(self) -> None:
        """
        Disconnect signal handlers for this tab's widgets.

        NOTE: If you tracked signals using track_signal(), you don't need to override this.
        The cleanup() method will automatically disconnect tracked signals.

        Override this only if you need custom disconnection logic.
        """
        # Default implementation - subclasses should override if they need custom disconnection
        pass

    def cleanup(self) -> None:
        """
        Clean up all resources used by this tab.

        This method:
        1. Calls _disconnect_signals() for custom disconnection logic
        2. Calls CleanupMixin.cleanup() to clean tracked resources
        3. Clears widget cache
        """
        logger.debug(
            f"Cleaning up {self.tab_name} tab",
            extra={"class_name": self.__class__.__name__},
        )

        # Call custom disconnection logic first
        try:
            self._disconnect_signals()
        except Exception as e:
            logger.warning(
                f"Error in _disconnect_signals for {self.tab_name}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        # Call parent cleanup to handle tracked resources
        super().cleanup()

        # Clear widget cache
        self._widgets.clear()

        logger.debug(
            f"{self.tab_name} tab cleanup completed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def _load_settings(self) -> None:
        """Load current settings into UI widgets."""
        pass

    @abstractmethod
    def _setup_dependencies(self) -> None:
        """Set up dependencies between UI elements."""
        pass

    def get_widget(self, widget_id: str) -> Gtk.Widget:
        """
        Get a widget by ID, with caching.

        Args:
            widget_id: GTK widget ID

        Returns:
            The requested widget or None if not found
        """
        if widget_id not in self._widgets:
            self._widgets[widget_id] = self.builder.get_object(widget_id)

        return self._widgets[widget_id]

    def save_settings(self) -> Dict[str, Any]:
        """
        Save current UI state to settings.

        Returns:
            Dictionary of settings that were changed
        """
        try:
            changed_settings = self._collect_settings()

            # Handle None return (should return empty dict instead)
            if changed_settings is None:
                self.logger.warning(f"{self.tab_name} _collect_settings returned None, using empty dict")
                changed_settings = {}

            for key, value in changed_settings.items():
                self.app_settings.set(key, value)

            self.logger.debug(f"{self.tab_name} tab settings saved: {len(changed_settings)} items")
            return changed_settings

        except Exception as e:
            self.logger.error(f"Error saving {self.tab_name} tab settings: {e}")
            return {}

    @abstractmethod
    def _collect_settings(self) -> Dict[str, Any]:
        """
        Collect current settings from UI widgets.

        Returns:
            Dictionary of setting_key -> value pairs
        """
        pass

    def validate_settings(self) -> Dict[str, str]:
        """
        Validate current settings.

        Returns:
            Dictionary of field_name -> error_message for any validation errors
        """
        try:
            return self._validate_tab_settings()
        except Exception as e:
            self.logger.error(f"Error validating {self.tab_name} tab settings: {e}")
            return {"general": f"Validation error: {e}"}

    def _validate_tab_settings(self) -> Dict[str, str]:
        """
        Tab-specific validation logic.

        Returns:
            Dictionary of validation errors
        """
        # Default implementation - no validation errors
        return {}

    def update_dependencies(self) -> None:
        """Update UI element dependencies."""
        try:
            self._update_tab_dependencies()
        except Exception as e:
            self.logger.error(f"Error updating {self.tab_name} tab dependencies: {e}")

    def _update_tab_dependencies(self) -> None:
        """Tab-specific dependency update logic. Override in subclasses."""
        pass

    def reset_to_defaults(self) -> None:
        """Reset tab settings to default values."""
        try:
            self._reset_tab_defaults()
            self.logger.debug(f"{self.tab_name} tab reset to defaults")
        except Exception as e:
            self.logger.error(f"Error resetting {self.tab_name} tab to defaults: {e}")

    def _reset_tab_defaults(self) -> None:
        """Tab-specific reset logic. Override in subclasses."""
        pass

    def on_setting_changed(self, widget: Gtk.Widget, *args) -> None:
        """
        Generic setting change handler.

        Args:
            widget: Widget that changed
            *args: Additional arguments from signal
        """
        try:
            # Update dependencies when settings change
            self.update_dependencies()

            # Log the change for debugging
            widget_name = getattr(widget, "get_name", lambda: "unknown")()
            self.logger.debug(f"{self.tab_name} tab setting changed: {widget_name}")

        except Exception as e:
            self.logger.error(f"Error handling setting change in {self.tab_name} tab: {e}")
