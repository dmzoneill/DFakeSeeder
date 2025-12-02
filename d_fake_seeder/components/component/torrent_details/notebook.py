"""
Main torrent details notebook component.
Coordinates all torrent details tabs and provides the main interface.
"""

# isort: skip_file

# fmt: off
from typing import Any, List, Optional

import gi

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

# Import tab configuration system
from d_fake_seeder.lib.util.tab_config import (
    get_essential_tab_classes,
    get_lazy_load_tab_classes,
    get_torrent_details_tab_classes,
)

from .details_tab import DetailsTab
from .files_tab import FilesTab
from .incoming_connections_tab import IncomingConnectionsTab
from .log_tab import LogTab
from .monitoring_tab import MonitoringTab
from .options_tab import OptionsTab
from .outgoing_connections_tab import OutgoingConnectionsTab
from .peers_tab import PeersTab

# Import all tab classes
from .status_tab import StatusTab
from .trackers_tab import TrackersTab

gi.require_version("Gtk", "4.0")

# fmt: on


class TorrentDetailsNotebook(Component):
    """
    Main torrent details notebook with tabbed interface.
    Coordinates multiple torrent details tabs and manages the overall details experience.
    Uses composition pattern with specialized tab classes for maintainability.
    """

    def __init__(self, builder, model):
        """Initialize the torrent details notebook."""
        with logger.performance.operation_context("notebook_init", self.__class__.__name__):
            logger.debug("TorrentDetailsNotebook.__init__() started", self.__class__.__name__)
            super().__init__()
            logger.debug("TorrentDetailsNotebook startup", self.__class__.__name__)
            with logger.performance.operation_context("basic_setup", self.__class__.__name__):
                self.builder = builder
                self.model = model
                self.settings = AppSettings.get_instance()
                # Get main notebook widget
                self.notebook = self.builder.get_object("notebook1")
                # Get UI settings
                ui_settings = getattr(self.settings, "ui_settings", {})
                self.ui_margin_large = ui_settings.get("ui_margin_large", 10)
                logger.debug("Basic setup completed", self.__class__.__name__)
            # PERFORMANCE OPTIMIZATION: Use lazy loading for tabs
            # Only create essential tabs immediately, defer others to background
            with logger.performance.operation_context("tab_setup", self.__class__.__name__):
                self.tabs: List[Any] = []
                # Create module mapping for tab configuration
                self._module_mapping = {
                    "StatusTab": StatusTab,
                    "FilesTab": FilesTab,
                    "DetailsTab": DetailsTab,
                    "OptionsTab": OptionsTab,
                    "PeersTab": PeersTab,
                    "TrackersTab": TrackersTab,
                    "LogTab": LogTab,
                    "MonitoringTab": MonitoringTab,
                }
                # Load tab configuration
                try:
                    self._lazy_tab_classes = get_torrent_details_tab_classes(self._module_mapping)
                    logger.debug(
                        f"Loaded {len(self._lazy_tab_classes)} tabs from configuration",
                        self.__class__.__name__,
                    )
                except Exception as e:
                    logger.debug(
                        f"Warning: Could not load tab config ({e}), using fallback",
                        self.__class__.__name__,
                    )
                    self._lazy_tab_classes = [
                        StatusTab,
                        FilesTab,
                        DetailsTab,
                        OptionsTab,
                        PeersTab,
                        TrackersTab,
                        LogTab,
                        MonitoringTab,
                    ]
                self._initialize_essential_tabs_only()
                logger.debug("Essential tab initialization completed", self.__class__.__name__)
            # PERFORMANCE OPTIMIZATION: Defer connection components to background
            # These are only needed when viewing peer connections
            with logger.performance.operation_context("connections_setup", self.__class__.__name__):
                self.incoming_connections = None
                self.outgoing_connections = None
                self._schedule_background_component_creation()
                logger.debug(
                    "Connection components scheduled for background creation",
                    self.__class__.__name__,
                )
            # Set up connection callbacks (will be applied when components are created)
            with logger.performance.operation_context("callbacks_setup", self.__class__.__name__):
                # Note: Connection callbacks will be set up in background creation
                # Connect to settings changes
                self.settings.connect("attribute-changed", self.handle_settings_changed)
                # Set up model event handlers
                self._setup_model_handlers()
                logger.debug("Callbacks setup completed", self.__class__.__name__)
            # Current torrent tracking
            self._current_torrent = None
            self._initialization_complete = False
            self._startup_selection_processed = False
            # Mark initialization as complete
            with logger.performance.operation_context("initialization_completion", self.__class__.__name__):
                self._complete_initialization()
                logger.debug("Initialization completion", self.__class__.__name__)
            logger.debug("TorrentDetailsNotebook.__init__() completed", self.__class__.__name__)

    def register_for_translation(self):
        """Register notebook widgets for translation when model is available."""
        try:
            if self.model and hasattr(self.model, "translation_manager"):
                # Connect to language change signal only once
                if hasattr(self.model, "connect") and not hasattr(self, "_language_signal_connected"):
                    self.model.connect("language-changed", self.on_language_changed)
                    self._language_signal_connected = True
                # Get initial widget count
                initial_count = len(self.model.translation_manager.translatable_widgets)
                # Register individual tabs for translation if they have builders
                for tab in self.tabs:
                    try:
                        if hasattr(tab, "builder") and tab.builder:
                            self.model.translation_manager.scan_builder_widgets(tab.builder)
                            logger.debug(f"Scanned {tab.tab_name} tab widgets for translation")
                        elif hasattr(tab, "register_for_translation"):
                            tab.register_for_translation()
                            logger.debug(f"Registered {tab.tab_name} tab for translation")
                    except Exception as e:
                        logger.warning(f"Could not register {tab.tab_name} tab for translation: {e}")
                # Register connection tabs
                try:
                    if hasattr(self.incoming_connections, "builder") and self.incoming_connections.builder:
                        self.model.translation_manager.scan_builder_widgets(self.incoming_connections.builder)
                        logger.debug("Scanned incoming connections tab widgets for translation")
                    if hasattr(self.outgoing_connections, "builder") and self.outgoing_connections.builder:
                        self.model.translation_manager.scan_builder_widgets(self.outgoing_connections.builder)
                        logger.debug("Scanned outgoing connections tab widgets for translation")
                except Exception as e:
                    logger.warning(f"Could not register connection tabs for translation: {e}")
                # Get final widget count and refresh translations if new widgets were registered
                final_count = len(self.model.translation_manager.translatable_widgets)
                new_widgets = final_count - initial_count
                # CRITICAL FIX: Refresh translations for newly registered notebook widgets
                # This ensures that notebook and tab widgets get translated with the correct language
                if new_widgets > 0:
                    logger.debug(
                        f"Newly registered {new_widgets} notebook widgets will be refreshed by debounced system",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Use debounced refresh to avoid cascading refresh operations
                    self.model.translation_manager.refresh_all_translations()
                logger.debug(
                    f"Registered torrent details notebook and all tabs for translation updates "
                    f"({new_widgets} new widgets)",
                    extra={"class_name": self.__class__.__name__},
                )
        except Exception as e:
            logger.error(f"Error registering notebook for translation: {e}")

    def on_language_changed(self, source, new_language):
        """Handle language change events."""
        try:
            logger.debug(
                f"Notebook language changed to: {new_language}",
                extra={"class_name": self.__class__.__name__},
            )
            # Update notebook tab labels first
            if self.model and hasattr(self.model, "translation_manager"):
                self._update_notebook_tab_labels()
            # Refresh tab content with current torrent if available
            # This ensures dynamic content gets updated with new translations
            if self._current_torrent:
                logger.debug(f"Refreshing all tabs after language change to {new_language}")
                # Update all tabs to refresh their content with new language
                for tab in self.tabs:
                    try:
                        if hasattr(tab, "on_language_changed"):
                            # Call individual tab's language change handler
                            tab.on_language_changed(source, new_language)
                        else:
                            # Fallback: refresh content if tab doesn't have language handler
                            if hasattr(tab, "on_torrent_selection_changed"):
                                tab.on_torrent_selection_changed(self._current_torrent)
                    except Exception as e:
                        logger.error(f"Error updating {tab.tab_name} tab after language change: {e}")
        except Exception as e:
            logger.error(f"Error handling language change in notebook: {e}")

    def _update_notebook_tab_labels(self):
        """Manually update notebook tab labels with current translations."""
        try:
            if not self.model or not hasattr(self.model, "get_translate_func"):
                return
            translate = self.model.get_translate_func()
            # Map of tab positions to their translation keys
            tab_labels = [
                ("Details", 0),
                ("Status", 1),
                ("Options", 2),
                ("Files", 3),
                ("Peers", 4),
                ("Incoming", 5),
                ("Outgoing", 6),
                ("Trackers", 7),
                ("Log", 8),
            ]
            for label_key, tab_index in tab_labels:
                try:
                    # Get the tab label widget
                    tab_label_widget = self.notebook.get_tab_label(self.notebook.get_nth_page(tab_index))
                    if tab_label_widget and hasattr(tab_label_widget, "set_text"):
                        translated_text = translate(label_key)
                        tab_label_widget.set_text(translated_text)
                        logger.debug(f"Updated tab {tab_index} label to: {translated_text}")
                except Exception as e:
                    logger.warning(f"Could not update tab label {label_key}: {e}")
        except Exception as e:
            logger.error(f"Error updating notebook tab labels: {e}")

    def _initialize_tabs(self) -> None:
        """Initialize all torrent details tab components."""

        try:
            # Create tab instances in order matching the notebook
            tab_classes = [
                StatusTab,
                FilesTab,
                DetailsTab,
                OptionsTab,
                PeersTab,
                TrackersTab,
                LogTab,
            ]
            for i, tab_class in enumerate(tab_classes):
                try:
                    logger.debug("Creating ...", "TorrentDetailsNotebook")
                    tab = tab_class(self.builder, self.model)  # type: ignore[abstract]
                    self.tabs.append(tab)
                    logger.debug(
                        f"{tab_class.__name__} created successfully",
                        "TorrentDetailsNotebook",
                    )
                    logger.debug(f"Initialized {tab.tab_name} tab")
                except Exception as e:
                    logger.debug(
                        f"ERROR creating {tab_class.__name__}: {e}",
                        "TorrentDetailsNotebook",
                    )
                    logger.error(f"Error initializing {tab_class.__name__}: {e}")
            # Set up special dependencies for peers tab
            self._setup_peers_tab_dependencies()
            logger.debug(
                "Peers tab dependencies setup completed (took {(deps_end - deps_start)*1000:.1f}ms)",
                "UnknownClass",
            )
            logger.debug(f"Initialized {len(self.tabs)} torrent details tabs")
        except Exception as e:
            logger.error(f"Error initializing torrent details tabs: {e}")

    def _initialize_essential_tabs_only(self) -> None:
        """Initialize only essential tabs immediately for fast startup."""

        from gi.repository import GLib

        try:
            # Load essential tabs from configuration
            try:
                essential_tabs = get_essential_tab_classes(self._module_mapping)
                logger.debug(
                    "Loaded  essential tabs from configuration",
                    "TorrentDetailsNotebook",
                )
            except Exception:
                logger.debug(
                    "Warning: Could not load essential tab config (), using fallback",
                    "TorrentDetailsNotebook",
                )
                essential_tabs = [StatusTab]  # Only create the most essential tab
            for tab_class in essential_tabs:
                try:
                    logger.debug("Creating essential ...", "TorrentDetailsNotebook")
                    tab = tab_class(self.builder, self.model)  # type: ignore[abstract]
                    self.tabs.append(tab)
                    logger.debug(
                        f"Essential {tab_class.__name__} created successfully",
                        "TorrentDetailsNotebook",
                    )
                    logger.debug(f"Initialized essential {tab.tab_name} tab")
                except Exception as e:
                    logger.error(
                        f"ERROR creating essential {tab_class.__name__}: {e}",
                        extra={"class_name": "TorrentDetailsNotebook"},
                        exc_info=True,
                    )
            # Schedule remaining tabs for background creation
            try:
                remaining_tabs = get_lazy_load_tab_classes(self._module_mapping)
                logger.debug(
                    "Loaded  lazy load tabs from configuration",
                    "TorrentDetailsNotebook",
                )
            except Exception:
                logger.debug(
                    "Warning: Could not load lazy tab config (), using fallback",
                    "TorrentDetailsNotebook",
                )
                remaining_tabs = [
                    FilesTab,
                    DetailsTab,
                    OptionsTab,
                    PeersTab,
                    TrackersTab,
                    LogTab,
                    MonitoringTab,
                ]
            GLib.idle_add(self._create_remaining_tabs_background, remaining_tabs)
            logger.debug(f"Initialized {len(self.tabs)} essential tabs, {len(remaining_tabs)} scheduled for background")
        except Exception as e:
            logger.error(f"Error initializing essential tabs: {e}")

    def _create_remaining_tabs_background(self, remaining_tab_classes):
        """Create remaining tabs in background to avoid blocking startup."""
        logger.debug(
            f"Starting background tab creation for {len(remaining_tab_classes)} tabs",
            "TorrentDetailsNotebook",
        )
        try:
            created_count = 0
            for tab_class in remaining_tab_classes:
                try:
                    tab = tab_class(self.builder, self.model)  # type: ignore[abstract]
                    self.tabs.append(tab)
                    logger.debug(
                        f"Background {tab_class.__name__} created successfully",
                        "TorrentDetailsNotebook",
                    )
                    created_count += 1
                except Exception as e:
                    logger.error(
                        f"ERROR creating background {tab_class.__name__}: {e}",
                        extra={"class_name": "TorrentDetailsNotebook"},
                        exc_info=True,
                    )
            # Set up peers tab dependencies after creation
            self._setup_peers_tab_dependencies()
            logger.debug(
                f"Background tab creation completed: {created_count} tabs",
                "TorrentDetailsNotebook",
            )
        except Exception as e:
            logger.error(
                f"Background tab creation error: {e}",
                extra={"class_name": "TorrentDetailsNotebook"},
                exc_info=True,
            )
        return False  # Don't repeat this idle task

    def _schedule_background_component_creation(self):
        """Schedule creation of connection components in background."""
        from gi.repository import GLib

        GLib.idle_add(self._create_connection_components_background)

    def _create_connection_components_background(self):
        """Create connection components in background."""
        logger.debug(
            "Starting background connection component creation",
            "TorrentDetailsNotebook",
        )
        try:
            # Create connection components
            self.incoming_connections = IncomingConnectionsTab(self.builder, self.model)
            self.outgoing_connections = OutgoingConnectionsTab(self.builder, self.model)
            # Set up callbacks
            self.incoming_connections.set_count_update_callback(self.update_connection_counts)
            self.outgoing_connections.set_count_update_callback(self.update_connection_counts)
            # LAZY LOADING FIX: Connect the signals now that components exist
            self._connect_background_signals()
            logger.debug(
                "Background connection components created successfully",
                "TorrentDetailsNotebook",
            )
        except Exception:
            logger.debug(
                "Background connection component creation error:",
                "TorrentDetailsNotebook",
            )
        return False  # Don't repeat this idle task

    def _connect_background_signals(self):
        """Connect signals for background-created components."""

        try:
            if self.model and hasattr(self.model, "connect"):
                if self.incoming_connections:
                    self.model.connect("data-changed", self.incoming_connections.update_view)
                    logger.debug(
                        "Connected incoming connections signals",
                        "TorrentDetailsNotebook",
                    )
                if self.outgoing_connections:
                    self.model.connect("data-changed", self.outgoing_connections.update_view)
                    logger.debug(
                        "Connected outgoing connections signals",
                        "TorrentDetailsNotebook",
                    )
        except Exception:
            logger.debug("Error connecting background signals:", "TorrentDetailsNotebook")

    def _setup_peers_tab_dependencies(self) -> None:
        """Set up dependencies for the peers tab."""
        try:
            peers_tab = self.get_tab_by_name("Peers")
            if peers_tab:
                # Pass connection managers to peers tab
                peers_tab.set_connection_managers(
                    incoming_connections=self.incoming_connections,
                    outgoing_connections=self.outgoing_connections,
                    global_peer_manager=getattr(self, "global_peer_manager", None),
                )
        except Exception as e:
            logger.error(f"Error setting up peers tab dependencies: {e}")

    def _setup_model_handlers(self) -> None:
        """Set up model event handlers."""
        try:
            # Connect to model changes
            if hasattr(self.model, "connect"):
                self.model.connect("data-changed", self.handle_model_changed)
                self.model.connect("selection-changed", self.model_selection_changed)
        except Exception as e:
            logger.error(f"Error setting up model handlers: {e}")

    def _complete_initialization(self) -> None:
        """Complete initialization."""
        try:
            self._initialization_complete = True
            logger.debug("Notebook initialization completed")
            # Force initial tab label translation based on current language
            if self.model and hasattr(self.model, "translation_manager"):
                current_lang = self.model.translation_manager.get_current_language()
                if current_lang:
                    logger.debug(f"Applying startup translations for language: {current_lang}")
                    self._update_notebook_tab_labels()
        except Exception as e:
            logger.error(f"Error completing notebook initialization: {e}")

    def set_global_peer_manager(self, global_peer_manager) -> None:
        """
        Set the global peer manager for peer data.
        Args:
            global_peer_manager: Global peer manager instance
        """
        try:
            self.global_peer_manager = global_peer_manager
            # Update peers tab with the manager
            peers_tab = self.get_tab_by_name("Peers")
            if peers_tab:
                peers_tab.set_connection_managers(
                    incoming_connections=self.incoming_connections,
                    outgoing_connections=self.outgoing_connections,
                    global_peer_manager=global_peer_manager,
                )
        except Exception as e:
            logger.error(f"Error setting global peer manager: {e}")

    def update_all_tabs(self, torrent) -> None:
        """
        Update all tabs with new torrent data.
        Args:
            torrent: Torrent object to display
        """
        try:
            self._current_torrent = torrent
            if not torrent:
                # Clear all tabs if no torrent selected
                for tab in self.tabs:
                    tab.clear_content()
                return
            # Update each tab
            for tab in self.tabs:
                try:
                    tab.on_torrent_selection_changed(torrent)
                except Exception as e:
                    logger.error(f"Error updating {tab.tab_name} tab: {e}")
        except Exception as e:
            logger.error(f"Error updating all tabs: {e}")

    def refresh_current_torrent(self) -> None:
        """Refresh all tabs with current torrent data."""
        try:
            if self._current_torrent:
                self.update_all_tabs(self._current_torrent)
        except Exception as e:
            logger.error(f"Error refreshing current torrent: {e}")

    def get_tab_by_name(self, tab_name: str) -> Optional[Any]:
        """
        Get a specific tab by name.
        Args:
            tab_name: Name of the tab
        Returns:
            Tab instance or None if not found
        """
        try:
            for tab in self.tabs:
                if tab.tab_name == tab_name:
                    return tab
            return None
        except Exception as e:
            logger.error(f"Error getting tab by name {tab_name}: {e}")
            return None

    def get_all_tab_names(self) -> List[str]:
        """
        Get names of all tabs.
        Returns:
            List of tab names
        """
        try:
            return [tab.tab_name for tab in self.tabs]
        except Exception as e:
            logger.error(f"Error getting tab names: {e}")
            return []

    def get_current_torrent(self):
        """Get the currently displayed torrent."""
        return self._current_torrent

    # Event handlers
    def handle_settings_changed(self, source, key, value) -> None:
        """
        Handle settings changes.
        Args:
            source: Settings source
            key: Settings key
            value: New value
        """
        try:
            # Notify all tabs about settings changes
            for tab in self.tabs:
                try:
                    tab.on_settings_changed(key, value)
                except Exception as e:
                    logger.error(f"Error handling settings change in {tab.tab_name} tab: {e}")
        except Exception as e:
            logger.error(f"Error handling settings changed: {e}")

    def handle_model_changed(self, source, data_obj, data_changed) -> None:
        """Handle model data changes."""
        try:
            # Refresh current torrent if model data changed
            if self._current_torrent and data_obj:
                if hasattr(data_obj, "id") and data_obj.id == self._current_torrent.id:
                    self.refresh_current_torrent()
        except Exception as e:
            logger.error(f"Error handling model changed: {e}")

    def handle_attribute_changed(self, source, key, value) -> None:
        """Handle attribute changes."""
        try:
            # Notify tabs about attribute changes
            for tab in self.tabs:
                try:
                    if hasattr(tab, "on_torrent_data_changed"):
                        tab.on_torrent_data_changed(self._current_torrent, key)
                except Exception as e:
                    logger.error(f"Error handling attribute change in {tab.tab_name} tab: {e}")
        except Exception as e:
            logger.error(f"Error handling attribute changed: {e}")

    def model_selection_changed(self, source, model, torrent) -> None:
        """
        Handle model selection changes.
        Args:
            source: Selection source
            model: Model instance
            torrent: Selected torrent
        """
        try:
            # Always update tabs - let the individual tabs handle initialization
            self.update_all_tabs(torrent)
            self._startup_selection_processed = True  # Mark as processed
        except Exception as e:
            logger.error(f"Error handling model selection changed: {e}")

    def update_connection_counts(self) -> None:
        """Update connection counts (called by connection components)."""
        try:
            # Get connection counts with safety checks for lazy loading
            incoming_count = 0
            outgoing_count = 0
            if self.incoming_connections and hasattr(self.incoming_connections, "all_connections"):
                incoming_count = len(self.incoming_connections.all_connections)
            if self.outgoing_connections and hasattr(self.outgoing_connections, "all_connections"):
                outgoing_count = len(self.outgoing_connections.all_connections)
            logger.debug(f"Connection counts updated: incoming={incoming_count}, outgoing={outgoing_count}")
            # Refresh peers tab if it's the current torrent
            if self._current_torrent:
                peers_tab = self.get_tab_by_name("Peers")
                if peers_tab:
                    peers_tab.update_content(self._current_torrent)
        except Exception as e:
            logger.error(f"Error updating connection counts: {e}")

    def get_incoming_connections(self):
        """Get the incoming connections component (may be None if not yet created)."""
        return self.incoming_connections

    def get_outgoing_connections(self):
        """Get the outgoing connections component (may be None if not yet created)."""
        return self.outgoing_connections

    def set_model(self, model):
        """Set model for notebook and all its tabs."""
        try:
            logger.debug(
                "TorrentDetailsNotebook set_model",
                extra={"class_name": self.__class__.__name__},
            )
            # Update notebook model
            self.model = model
            # Re-establish signal connections now that model is available
            self._setup_model_handlers()
            # Update all tab models
            for tab in self.tabs:
                try:
                    if hasattr(tab, "set_model"):
                        tab.set_model(model)
                    elif hasattr(tab, "model"):
                        tab.model = model
                    logger.debug(f"Updated model for {tab.tab_name} tab")
                except Exception as e:
                    logger.error(f"Error setting model for {tab.tab_name} tab: {e}")
            # Update connection tab models (with lazy loading safety checks)
            try:
                if self.incoming_connections:
                    if hasattr(self.incoming_connections, "set_model"):
                        self.incoming_connections.set_model(model)
                    elif hasattr(self.incoming_connections, "model"):
                        self.incoming_connections.model = model
                if self.outgoing_connections:
                    if hasattr(self.outgoing_connections, "set_model"):
                        self.outgoing_connections.set_model(model)
                    elif hasattr(self.outgoing_connections, "model"):
                        self.outgoing_connections.model = model
                logger.debug("Updated model for connection tabs (if available)")
            except Exception as e:
                logger.error(f"Error setting model for connection tabs: {e}")
            # Re-register for translations now that model is available
            if model and hasattr(model, "translation_manager"):
                self.register_for_translation()
                logger.debug("Re-registered notebook for translations after model update")
        except Exception as e:
            logger.error(f"Error setting model for notebook: {e}")

    def cleanup(self) -> None:
        """Cleanup resources when notebook is destroyed."""
        try:
            # Cleanup all tabs
            for tab in self.tabs:
                try:
                    tab.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up {tab.tab_name} tab: {e}")
            # Clear references
            self.tabs.clear()
            self._current_torrent = None
            logger.debug("Torrent details notebook cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up notebook: {e}")

    # Utility methods for external access
    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        return len(self.tabs)

    def is_tab_visible(self, tab_name: str) -> bool:
        """
        Check if a specific tab is visible.
        Args:
            tab_name: Name of the tab
        Returns:
            True if tab is visible
        """
        try:
            tab = self.get_tab_by_name(tab_name)
            return tab.is_visible() if tab else False
        except Exception:
            return False

    def set_tab_visible(self, tab_name: str, visible: bool) -> None:
        """
        Set tab visibility.
        Args:
            tab_name: Name of the tab
            visible: Whether tab should be visible
        """
        try:
            tab = self.get_tab_by_name(tab_name)
            if tab:
                tab.set_visible(visible)
        except Exception as e:
            logger.error(f"Error setting tab visibility for {tab_name}: {e}")

    def update_view(self, model, torrent, attribute):
        """
        Update view based on model changes.
        Args:
            model: Model instance
            torrent: Torrent object
            attribute: Changed attribute
        """
        try:
            logger.debug(
                "Torrent details notebook update view",
                extra={"class_name": self.__class__.__name__},
            )
            # CRITICAL: Only update tabs if the torrent is the currently selected one
            # Don't update tabs just because a torrent was added or changed
            if torrent and self._current_torrent and hasattr(torrent, "id") and hasattr(self._current_torrent, "id"):
                if torrent.id == self._current_torrent.id:
                    self.update_all_tabs(torrent)
                    logger.debug(f"Updated tabs for currently selected torrent: {torrent.id}")
                else:
                    logger.debug(
                        f"Ignoring update for torrent {torrent.id} - not currently selected "
                        f"(current: {self._current_torrent.id})"
                    )
            elif not self._current_torrent:
                logger.debug("Ignoring update - no torrent currently selected")
        except Exception as e:
            logger.error(f"Error updating view: {e}")
