"""
Base class for torrent details tab components.

Provides common functionality and interface for all torrent detail tabs.
"""

# isort: skip_file

# fmt: off
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.cleanup_mixin import CleanupMixin  # noqa: E402

# fmt: on


class BaseTorrentTab(ABC, CleanupMixin):
    """
    Abstract base class for torrent details tab components.

    Each tab is responsible for:
    - Managing its specific UI elements
    - Updating its content when torrent data changes
    - Handling its signal connections
    - Managing its UI state and visibility
    """

    def __init__(self, builder: Gtk.Builder, model):
        """
        Initialize the base tab.

        Args:
            builder: GTK Builder instance with UI loaded
            model: Application model instance
        """
        CleanupMixin.__init__(self)
        self.builder = builder
        self.model = model
        self.logger = logger
        self.settings = AppSettings.get_instance()

        # Get UI settings for consistent spacing
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.ui_margin_large = ui_settings.get("ui_margin_large", 10)
        self.ui_margin_xlarge = ui_settings.get("ui_margin_xlarge", 20)
        self.ui_column_spacing_small = ui_settings.get("ui_column_spacing_small", 10)
        self.ui_column_spacing_large = ui_settings.get("ui_column_spacing_large", 20)
        self.ui_row_spacing = ui_settings.get("ui_row_spacing", 10)

        # Store UI widgets specific to this tab
        self._widgets: Dict[str, Any] = {}
        self._current_torrent = None
        self._tab_widget = None

        # Initialize tab-specific setup
        self._init_widgets()
        self._connect_signals()
        self._setup_ui_styling()
        self._register_for_translation()

        # Show empty state by default since no torrent is selected on init
        self._show_empty_state()

    @property
    @abstractmethod
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        pass

    @property
    @abstractmethod
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        pass

    @abstractmethod
    def _init_widgets(self) -> None:
        """Initialize and cache tab-specific widgets."""
        pass

    def _connect_signals(self) -> None:
        """Connect signal handlers for this tab. Override in subclasses if needed."""
        pass

    def _setup_ui_styling(self) -> None:
        """Set up consistent UI styling for the tab."""
        try:
            self._tab_widget = self.get_widget(self.tab_widget_id)
            if self._tab_widget:
                self._tab_widget.set_visible(True)
                # Margins are now set in XML for consistency across all tabs
                # Removed: set_margin_top/bottom/start/end calls
        except Exception as e:
            self.logger.error(f"Error setting up UI styling for {self.tab_name} tab: {e}")

    def get_widget(self, widget_id: str) -> Optional[Gtk.Widget]:
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

    @abstractmethod
    def update_content(self, torrent) -> None:
        """
        Update tab content with new torrent data.

        Args:
            torrent: Torrent object to display
        """
        pass

    def clear_content(self) -> None:
        """Clear tab content. Override in subclasses if needed."""
        self._show_empty_state()

    def _show_empty_state(self) -> None:
        """Show the empty state widget for this tab."""
        try:
            empty_state_id = f"{self.tab_widget_id.replace('_tab', '')}_empty_state"
            empty_state = self.get_widget(empty_state_id)
            if empty_state:
                empty_state.set_visible(True)
                self.logger.debug(f"Showing empty state for {self.tab_name} tab")
        except Exception as e:
            self.logger.debug(f"No empty state widget found for {self.tab_name} tab: {e}")

    def _hide_empty_state(self) -> None:
        """Hide the empty state widget for this tab."""
        try:
            empty_state_id = f"{self.tab_widget_id.replace('_tab', '')}_empty_state"
            empty_state = self.get_widget(empty_state_id)
            if empty_state:
                empty_state.set_visible(False)
                self.logger.debug(f"Hiding empty state for {self.tab_name} tab")
        except Exception as e:
            self.logger.debug(f"No empty state widget found for {self.tab_name} tab: {e}")

    def _register_for_translation(self) -> None:
        """Register this tab for translation updates."""
        try:
            if self.model and hasattr(self.model, "translation_manager"):
                # Register for language change events
                if hasattr(self.model, "connect"):
                    self.model.connect("language-changed", self.on_language_changed)

                # If tab has its own builder widgets, register them
                if hasattr(self, "builder") and self.builder:
                    initial_count = len(self.model.translation_manager.translatable_widgets)
                    self.model.translation_manager.scan_builder_widgets(self.builder)
                    final_count = len(self.model.translation_manager.translatable_widgets)
                    new_widgets = final_count - initial_count

                    # CRITICAL FIX: Refresh translations for newly registered tab widgets
                    if new_widgets > 0:
                        self.logger.debug(
                            f"Newly registered {new_widgets} {self.tab_name} tab widgets "
                            f"will be refreshed by debounced system"
                        )
                        # Use debounced refresh to avoid cascading refresh operations
                        self.model.translation_manager.refresh_all_translations()

        except Exception as e:
            self.logger.error(f"Error registering {self.tab_name} tab for translation: {e}")

    def on_language_changed(self, source, new_language):
        """Handle language change events for this tab."""
        try:
            self.logger.debug(
                f"{self.tab_name} tab language changed to: {new_language}",
                extra={"class_name": self.__class__.__name__},
            )

            # Refresh content with current torrent if available
            if hasattr(self, "_current_torrent") and self._current_torrent:
                self.update_content(self._current_torrent)

        except Exception as e:
            self.logger.error(f"Error handling language change in {self.tab_name} tab: {e}")

    def on_torrent_selection_changed(self, torrent) -> None:
        """
        Handle torrent selection change.

        Args:
            torrent: Currently selected torrent
        """
        try:
            self._current_torrent = torrent
            if torrent:
                self._hide_empty_state()
                self.update_content(torrent)
            else:
                self.clear_content()
        except Exception as e:
            self.logger.error(f"Error handling torrent selection change in {self.tab_name} tab: {e}")

    def on_torrent_data_changed(self, torrent, attribute: Optional[str] = None) -> None:
        """
        Handle torrent data change.

        Args:
            torrent: Torrent object that changed
            attribute: Specific attribute that changed (optional)
        """
        try:
            if torrent == self._current_torrent:
                self.update_content(torrent)
        except Exception as e:
            self.logger.error(f"Error handling torrent data change in {self.tab_name} tab: {e}")

    def on_settings_changed(self, key: str, value: Any) -> None:
        """
        Handle settings change.

        Args:
            key: Settings key that changed
            value: New value
        """
        try:
            # Update UI settings if relevant
            if key.startswith("ui_settings."):
                ui_settings = getattr(self.settings, "ui_settings", {})
                self.ui_margin_large = ui_settings.get("ui_margin_large", 10)
                self.ui_margin_xlarge = ui_settings.get("ui_margin_xlarge", 20)
                self.ui_column_spacing_small = ui_settings.get("ui_column_spacing_small", 10)
                self.ui_column_spacing_large = ui_settings.get("ui_column_spacing_large", 20)
                self.ui_row_spacing = ui_settings.get("ui_row_spacing", 10)

                # Refresh UI with new settings
                self._setup_ui_styling()
                if self._current_torrent:
                    self.update_content(self._current_torrent)

        except Exception as e:
            self.logger.error(f"Error handling settings change in {self.tab_name} tab: {e}")

    def get_current_torrent(self):
        """Get the currently displayed torrent."""
        return self._current_torrent

    def is_visible(self) -> bool:
        """Check if tab is currently visible."""
        try:
            return bool(self._tab_widget and self._tab_widget.get_visible())
        except Exception:
            return False

    def set_visible(self, visible: bool) -> None:
        """Set tab visibility."""
        try:
            if self._tab_widget:
                self._tab_widget.set_visible(visible)
        except Exception as e:
            self.logger.error(f"Error setting visibility for {self.tab_name} tab: {e}")

    def cleanup(self) -> None:
        """Cleanup resources when tab is destroyed."""
        try:
            # Clean up tracked resources (signals, bindings, timeouts, stores)
            CleanupMixin.cleanup(self)

            # Clear tab-specific resources
            self._current_torrent = None
            self._widgets.clear()
            self.logger.debug(f"{self.tab_name} tab cleaned up")
        except Exception as e:
            self.logger.error(f"Error cleaning up {self.tab_name} tab: {e}")

    def create_label_pair(self, name: str, value: str, row: int, grid: Gtk.Grid) -> None:
        """
        Create a name-value label pair and add to grid.

        Args:
            name: Label name
            value: Label value
            row: Grid row position
            grid: Grid to add labels to
        """
        try:
            # Get translation function from model
            translate_func = (
                self.model.get_translate_func() if hasattr(self.model, "get_translate_func") else lambda x: x
            )

            # Translate the name label
            translated_name = translate_func(name)

            # Name label
            name_label = Gtk.Label(label=translated_name, xalign=0)
            name_label.set_visible(True)
            name_label.set_halign(Gtk.Align.START)
            name_label.set_size_request(80, -1)
            grid.attach(name_label, 0, row, 1, 1)

            # Value label
            value_label = Gtk.Label(label=str(value), xalign=0)
            value_label.set_visible(True)
            value_label.set_halign(Gtk.Align.START)
            value_label.set_size_request(280, -1)
            value_label.set_selectable(True)  # Enable text selection
            grid.attach(value_label, 1, row, 1, 1)

        except Exception as e:
            self.logger.error(f"Error creating label pair {name}={value}: {e}")

    def create_grid(self) -> Gtk.Grid:
        """
        Create a new grid with standard settings.

        Returns:
            Configured Gtk.Grid widget
        """
        try:
            grid = Gtk.Grid()
            grid.set_column_spacing(self.ui_column_spacing_small)
            grid.set_hexpand(True)
            grid.set_vexpand(True)
            grid.set_visible(True)
            return grid
        except Exception as e:
            self.logger.error(f"Error creating grid: {e}")
            return Gtk.Grid()  # Return basic grid as fallback
