"""
Outgoing Connections Component

Manages the UI for displaying outgoing peer connections, showing information
about peers that we've initiated connections to.

Now extends BaseTorrentTab for consistent hierarchy with other torrent detail tabs.
"""

# isort: skip_file

# fmt: off
from typing import Any
import gi

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.connection_manager import get_connection_manager
from d_fake_seeder.domain.torrent.model.connection_peer import ConnectionPeer
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin

from .base_tab import BaseTorrentTab
from .connection_cells_mixin import ConnectionCellsMixin

gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")

from gi.repository import Gio  # noqa: E402
from gi.repository import GLib, Gtk  # noqa: E402

# fmt: on


class OutgoingConnectionsTab(ConnectionCellsMixin, BaseTorrentTab, ColumnTranslationMixin):
    """Component for managing outgoing connections display.

    Extends BaseTorrentTab for consistent hierarchy with other torrent detail tabs.
    """

    BOOL_PROPERTIES = ("handshake_complete", "am_interested", "peer_choking")
    BYTES_PROPERTY = "bytes_downloaded"
    RATE_PROPERTY = "download_rate"
    COUNT_PROPERTIES = ("requests_sent", "pieces_received")

    @property
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        return "Outgoing Connections"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "outgoing_connections_tab"

    def __init__(self, builder: Any, model: Any) -> None:
        # Initialize ColumnTranslationMixin first
        ColumnTranslationMixin.__init__(self)

        # Use centralized connection manager (needed before parent __init__)
        self.connection_manager = get_connection_manager()

        # Data store for UI display (filtered view)
        self.outgoing_connections: dict[str, Any] = {}  # ip:port -> ConnectionPeer
        self.count_update_callback = None  # Callback to update connection counts

        # Initialize parent (calls _init_widgets, _connect_signals, etc.)
        super().__init__(builder, model)

        logger.trace(
            "OutgoingConnectionsTab view startup",
            extra={"class_name": self.__class__.__name__},
        )

    def _init_widgets(self) -> None:
        """Initialize and cache tab-specific widgets."""
        # Get UI elements
        self.outgoing_columnview = self.builder.get_object("outgoing_columnview")
        self.filter_checkbox = self.builder.get_object("outgoing_filter_selected_checkbox")

        # Initialize the column view
        self.init_outgoing_column_view()

        # Load byte formatting thresholds from settings
        settings = AppSettings.get_instance()
        ui_settings = getattr(settings, "ui_settings", {})
        self.kb_threshold = ui_settings.get("byte_format_threshold_kb", 1024)
        self.mb_threshold = ui_settings.get("byte_format_threshold_mb", 1048576)
        self.gb_threshold = ui_settings.get("byte_format_threshold_gb", 1073741824)

    def _connect_signals(self) -> None:
        """Connect signal handlers for this tab."""
        # Register for connection updates
        self.connection_manager.add_update_callback(self.on_connections_updated)

        # Connect checkbox signal
        self.track_signal(
            self.filter_checkbox,
            self.filter_checkbox.connect("toggled", self.on_filter_toggled),
        )

        # Connect to model selection changes
        if hasattr(self.model, "connect"):
            self.track_signal(
                self.model,
                self.model.connect("selection-changed", self.on_selection_changed),  # type: ignore[attr-defined]
            )

        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.track_signal(
                    self.model,
                    self.model.connect("language-changed", self.on_language_changed),
                )
                logger.trace(
                    "Connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.trace(
                    f"Could not connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    def update_content(self, torrent: Any) -> None:
        """Update tab content when torrent selection changes.

        For connection tabs, this applies the current filter with the selected torrent.
        """
        self.selected_torrent = torrent
        self.apply_filter()

    def on_connections_updated(self) -> None:
        """Called when the connection manager updates connections"""
        # Update the display by reapplying the filter
        self.apply_filter()

        # Notify count changed if callback is set
        self._notify_count_changed()

    def set_count_update_callback(self, callback: Any) -> None:
        """Set the callback to be called when connection count changes"""
        self.count_update_callback = callback

    def _notify_count_changed(self) -> Any:
        """Notify connection count changed (handled by main data-changed signal)"""
        # Connection count updates now handled by main data-changed signal
        # to respect tickspeed intervals and prevent UI flooding

    def init_outgoing_column_view(self) -> None:
        """Initialize the outgoing connections column view"""
        logger.trace(
            "OutgoingConnections init columnview",
            extra={"class_name": self.__class__.__name__},
        )

        self.outgoing_store = Gio.ListStore.new(ConnectionPeer)
        self.track_store(self.outgoing_store)  # Track for automatic cleanup

        # Define columns for outgoing connections
        columns = [
            ("address", "IP Address"),
            ("status", "Connection Status"),
            ("client", "Client"),
            ("connection_time", "Connected At"),
            ("handshake_complete", "Handshake"),
            ("am_interested", "Interested"),
            ("peer_choking", "Peer Choking"),
            ("bytes_downloaded", "Downloaded"),
            ("download_rate", "Download Rate"),
            ("requests_sent", "Requests"),
            ("pieces_received", "Pieces Received"),
            ("failure_reason", "Failure Reason"),
        ]

        for property_name, column_title in columns:
            factory = Gtk.SignalListItemFactory()
            self.track_signal(factory, factory.connect("setup", self.setup_cell, property_name))
            self.track_signal(factory, factory.connect("bind", self.bind_cell, property_name))
            column = Gtk.ColumnViewColumn.new(None, factory)
            # Expand to fill available space
            column.set_expand(True)
            column.set_resizable(True)

            # Register column for translation instead of using hardcoded title
            self.register_translatable_column(self.outgoing_columnview, column, property_name, "outgoing_connections")

            # Create sorter for the column
            if property_name in [
                "connection_time",
                "bytes_downloaded",
                "download_rate",
                "requests_sent",
                "pieces_received",
            ] or property_name in [
                "handshake_complete",
                "am_interested",
                "peer_choking",
            ]:
                property_expression = Gtk.PropertyExpression.new(ConnectionPeer, None, property_name)
                sorter = Gtk.NumericSorter.new(property_expression)
            else:
                property_expression = Gtk.PropertyExpression.new(ConnectionPeer, None, property_name)
                sorter = Gtk.StringSorter.new(property_expression)

            column.set_sorter(sorter)
            self.outgoing_columnview.append_column(column)

        # Set up sorting and selection
        sorter = Gtk.ColumnView.get_sorter(self.outgoing_columnview)
        self.sort_model = Gtk.SortListModel.new(self.outgoing_store, sorter)
        self.selection = Gtk.SingleSelection.new(self.sort_model)
        self.outgoing_columnview.set_model(self.selection)

    def on_filter_toggled(self, checkbox: Any) -> None:
        """Handle filter checkbox toggle"""
        logger.trace(
            f"Outgoing connections filter toggled: {checkbox.get_active()}",
            extra={"class_name": self.__class__.__name__},
        )
        self.apply_filter()

    def on_selection_changed(self, source: Any, model: Any, torrent: Any) -> None:
        """Handle model selection change"""
        self.selected_torrent = torrent
        logger.trace(
            f"Outgoing connections selection changed: {torrent.id if torrent else 'None'}",
            extra={"class_name": self.__class__.__name__},
        )
        self.apply_filter()

    def apply_filter(self) -> Any:
        """Apply the current filter to the connections"""
        try:
            filter_enabled = self.filter_checkbox.get_active()

            # Use _current_torrent from BaseTorrentTab if selected_torrent not set
            selected = getattr(self, "selected_torrent", None) or self._current_torrent

            # Determine which connections should be shown
            connections_to_show = []
            for (
                connection_key,
                connection_peer,
            ) in self.connection_manager.get_all_outgoing_connections().items():
                should_show = True

                if filter_enabled and selected:
                    # Only show connections for the selected torrent
                    should_show = connection_peer.torrent_hash == selected.torrent_file.get_info_hash_hex()

                if should_show and connection_key not in self.outgoing_connections:
                    # Only add if not already shown to avoid duplicates
                    connections_to_show.append((connection_key, connection_peer))

            # Schedule the filter update in idle to avoid snapshot issues
            def update_filter_when_idle() -> Any:
                try:
                    # Detach model to prevent O(n²) re-sort on each append
                    self.outgoing_columnview.set_model(None)

                    # Clear current displayed connections
                    self.outgoing_connections.clear()

                    # Clear the store safely
                    self.outgoing_store.remove_all()

                    # Add filtered connections
                    for connection_key, connection_peer in connections_to_show:
                        try:
                            if connection_key in self.connection_manager.get_all_outgoing_connections():
                                self.outgoing_connections[connection_key] = connection_peer
                                self.outgoing_store.append(connection_peer)
                        except Exception as e:
                            logger.error(
                                f"Error adding connection {connection_key} to store: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                except Exception as e:
                    logger.error(
                        f"Error updating filter in idle: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )
                finally:
                    self.outgoing_columnview.set_model(self.selection)
                return False  # Don't repeat  # type: ignore

            GLib.idle_add(update_filter_when_idle)

            # Notify that the count changed
            self._notify_count_changed()

        except Exception as e:
            logger.error(
                f"Error applying filter: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def add_outgoing_connection(self, address: str, port: int, torrent_hash: str = "", **kwargs: Any) -> None:
        """Add a new outgoing connection"""
        # Set defaults if not provided in kwargs
        connection_kwargs = {
            "torrent_hash": torrent_hash,
            "connected": True,  # Default value
            **kwargs,  # Allow kwargs to override defaults
        }

        # Delegate to centralized connection manager
        self.connection_manager.add_outgoing_connection(address, port, **connection_kwargs)

        # Apply current filter to update display
        self.apply_filter()

    def update_outgoing_connection(self, address: str, port: int, **kwargs: Any) -> None:
        """Update an existing outgoing connection"""
        # Delegate to centralized connection manager
        self.connection_manager.update_outgoing_connection(address, port, **kwargs)

        # Apply current filter to update display
        self.apply_filter()

    def remove_outgoing_connection(self, address: str, port: int) -> None:
        """Remove an outgoing connection"""
        # Delegate to centralized connection manager
        self.connection_manager.remove_outgoing_connection(address, port)

        # Apply current filter to update display
        self.apply_filter()

    def clear_connections(self) -> None:
        """Clear all outgoing connections"""
        self.outgoing_store.remove_all()
        self.outgoing_connections.clear()
        # Note: We don't clear the connection manager as it's shared

    def get_connection_count(self) -> int:
        """Get the number of active outgoing connections (currently visible)"""
        return len(self.outgoing_connections)

    def get_total_connection_count(self) -> int:
        """Get the total number of outgoing connections (including filtered)"""
        return self.connection_manager.get_global_outgoing_count()

    @property
    def all_connections(self) -> Any:
        """Property for backward compatibility - delegates to connection manager"""
        return self.connection_manager.get_all_outgoing_connections()

    def on_language_changed(self, source: Any = None, new_language: Any = None) -> None:
        """Handle language change events for column translation."""
        try:
            logger.trace(
                f"OutgoingConnections language changed to: {new_language}",
                extra={"class_name": self.__class__.__name__},
            )

            # Refresh column translations
            self.refresh_column_translations()

        except Exception as e:
            logger.error(
                f"Error handling language change in OutgoingConnections: {e}",
                extra={"class_name": self.__class__.__name__},
            )
