"""
Shared base for the incoming/outgoing connections tabs.

Both tabs show :class:`ConnectionPeer` rows from the central connection manager in a
sortable column view, optionally filtered to the selected torrent. Subclasses only
describe their direction (widget ids, columns, manager accessors and log labels).
"""

from dataclasses import dataclass
from typing import Any, ClassVar

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.connection_manager import get_connection_manager
from d_fake_seeder.domain.torrent.model.connection_peer import ConnectionPeer
from d_fake_seeder.lib.gi_gtk4 import Gio, GLib, Gtk
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin

from .base_tab import BaseTorrentTab
from .connection_cells_mixin import ConnectionCellsMixin

# Errors GTK/GObject calls and connection bookkeeping may raise in the UI handlers
UI_ERRORS: tuple[type[BaseException], ...] = (AttributeError, TypeError, ValueError, KeyError, GLib.Error)


@dataclass
class ConnectionView:
    """GTK objects backing the connections column view."""

    columnview: Any = None
    filter_checkbox: Any = None
    store: Any = None
    sort_model: Any = None
    selection: Any = None


@dataclass
class ConnectionTabState:
    """Selection and callback state of a connections tab."""

    selected_torrent: Any = None
    count_update_callback: Any = None


class ConnectionsTabBase(ConnectionCellsMixin, BaseTorrentTab, ColumnTranslationMixin):
    """Common behaviour for the incoming and outgoing connections tabs."""

    DIRECTION: ClassVar[str] = ""  # "incoming" or "outgoing"
    LOG_NAME: ClassVar[str] = ""  # e.g. "IncomingConnections"
    TAB_TITLE: ClassVar[str] = ""
    COLUMNS: ClassVar[tuple[tuple[str, str], ...]] = ()
    # Incoming historically (re)connects selection-changed on every connection update
    SELECTION_SIGNAL_ON_UPDATE: ClassVar[bool] = False

    @property
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        return self.TAB_TITLE

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return f"{self.DIRECTION}_connections_tab"

    def __init__(self, builder: Any, model: Any) -> None:
        ColumnTranslationMixin.__init__(self)
        # Use centralized connection manager (needed before parent __init__)
        self.connection_manager = get_connection_manager()
        # Data store for UI display (filtered view): ip:port -> ConnectionPeer
        self.connections: dict[str, Any] = {}
        self.view = ConnectionView()
        self.state = ConnectionTabState()
        # Initialize parent (calls _init_widgets, _connect_signals, etc.)
        super().__init__(builder, model)
        logger.trace(f"{self.LOG_NAME}Tab view startup", extra={"class_name": self.__class__.__name__})

    def _manager_call(self, action: str, *args: Any, **kwargs: Any) -> Any:
        """Call ``connection_manager.<action>`` with the direction substituted for ``{d}``."""
        return getattr(self.connection_manager, action.format(d=self.DIRECTION))(*args, **kwargs)

    def _init_widgets(self) -> None:
        """Initialize and cache tab-specific widgets."""
        self.view.columnview = self.builder.get_object(f"{self.DIRECTION}_columnview")
        self.view.filter_checkbox = self.builder.get_object(f"{self.DIRECTION}_filter_selected_checkbox")
        self.init_column_view()

        # Load byte formatting thresholds from settings
        ui_settings = getattr(AppSettings.get_instance(), "ui_settings", {})
        self.kb_threshold = ui_settings.get("byte_format_threshold_kb", 1024)
        self.mb_threshold = ui_settings.get("byte_format_threshold_mb", 1048576)
        self.gb_threshold = ui_settings.get("byte_format_threshold_gb", 1073741824)

    def _connect_selection_signal(self) -> None:
        model: Any = self.model
        if hasattr(model, "connect"):
            self.track_signal(model, model.connect("selection-changed", self.on_selection_changed))

    def _connect_signals(self) -> None:
        """Connect signal handlers for this tab."""
        self.connection_manager.add_update_callback(self.on_connections_updated)
        checkbox = self.view.filter_checkbox
        self.track_signal(checkbox, checkbox.connect("toggled", self.on_filter_toggled))

        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.track_signal(self.model, self.model.connect("language-changed", self.on_language_changed))
                logger.trace(
                    "Connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except UI_ERRORS as e:
                logger.trace(
                    f"Could not connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
        if not self.SELECTION_SIGNAL_ON_UPDATE:
            self._connect_selection_signal()

    def update_content(self, torrent: Any) -> None:
        """Update tab content when torrent selection changes (applies the current filter)."""
        self.state.selected_torrent = torrent
        self.apply_filter()

    def on_connections_updated(self) -> None:
        """Called when the connection manager updates connections"""
        self.apply_filter()
        self._notify_count_changed()
        if self.SELECTION_SIGNAL_ON_UPDATE:
            self._connect_selection_signal()

    def set_count_update_callback(self, callback: Any) -> None:
        """Set the callback to be called when connection count changes"""
        self.state.count_update_callback = callback

    def _notify_count_changed(self) -> Any:
        """Notify connection count changed (handled by main data-changed signal)"""
        # Connection count updates are handled by the main data-changed signal
        # to respect tickspeed intervals and prevent UI flooding

    def _make_column(self, property_name: str) -> Any:
        """Create a translatable, sortable column for ``property_name``."""
        factory = Gtk.SignalListItemFactory()
        self.track_signal(factory, factory.connect("setup", self.setup_cell, property_name))
        self.track_signal(factory, factory.connect("bind", self.bind_cell, property_name))
        column = Gtk.ColumnViewColumn.new(None, factory)
        column.set_expand(True)
        column.set_resizable(True)
        # Register column for translation instead of using hardcoded title
        self.register_translatable_column(self.view.columnview, column, property_name, f"{self.DIRECTION}_connections")
        numeric = (
            property_name == "connection_time"
            or property_name in self.BOOL_PROPERTIES
            or property_name in self.COUNT_PROPERTIES
            or property_name in (self.BYTES_PROPERTY, self.RATE_PROPERTY)
        )
        property_expression = Gtk.PropertyExpression.new(ConnectionPeer, None, property_name)
        sorter_class = Gtk.NumericSorter if numeric else Gtk.StringSorter
        column.set_sorter(sorter_class.new(property_expression))
        return column

    def init_column_view(self) -> None:
        """Initialize the connections column view"""
        logger.trace(f"{self.LOG_NAME} init columnview", extra={"class_name": self.__class__.__name__})
        self.view.store = Gio.ListStore.new(ConnectionPeer)
        self.track_store(self.view.store)  # Track for automatic cleanup
        for property_name, _title in self.COLUMNS:
            self.view.columnview.append_column(self._make_column(property_name))

        # Set up sorting and selection
        sorter = Gtk.ColumnView.get_sorter(self.view.columnview)
        self.view.sort_model = Gtk.SortListModel.new(self.view.store, sorter)
        self.view.selection = Gtk.SingleSelection.new(self.view.sort_model)
        self.view.columnview.set_model(self.view.selection)

    def on_filter_toggled(self, checkbox: Any) -> None:
        """Handle filter checkbox toggle"""
        logger.trace(
            f"{self.TAB_TITLE.split()[0]} connections filter toggled: {checkbox.get_active()}",
            extra={"class_name": self.__class__.__name__},
        )
        self.apply_filter()

    def on_selection_changed(self, _source: Any, _model: Any, torrent: Any) -> None:
        """Handle model selection change"""
        self.state.selected_torrent = torrent
        logger.trace(
            f"{self.TAB_TITLE.split()[0]} connections selection changed: {torrent.id if torrent else 'None'}",
            extra={"class_name": self.__class__.__name__},
        )
        self.apply_filter()

    def _connections_to_show(self) -> list[tuple[str, Any]]:
        """Connections matching the filter that are not already displayed."""
        # Use _current_torrent from BaseTorrentTab if selected_torrent not set
        selected = self.state.selected_torrent or self._current_torrent
        filter_hash = None
        if self.view.filter_checkbox.get_active() and selected:
            filter_hash = selected.torrent_file.get_info_hash_hex()
        return [
            (key, peer)
            for key, peer in self.all_connections.items()
            if (filter_hash is None or peer.torrent_hash == filter_hash) and key not in self.connections
        ]

    def _refresh_store(self, connections_to_show: list[tuple[str, Any]]) -> bool:
        """Replace the displayed rows (runs in idle to avoid snapshot issues)."""
        try:
            # Detach model to prevent O(n²) re-sort on each append
            self.view.columnview.set_model(None)
            self.connections.clear()
            self.view.store.remove_all()
            for connection_key, connection_peer in connections_to_show:
                try:
                    if connection_key in self.all_connections:
                        self.connections[connection_key] = connection_peer
                        self.view.store.append(connection_peer)
                except UI_ERRORS as e:
                    logger.error(
                        f"Error adding connection {connection_key} to store: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )
        except UI_ERRORS as e:
            logger.error(f"Error updating filter in idle: {e}", extra={"class_name": self.__class__.__name__})
        finally:
            self.view.columnview.set_model(self.view.selection)
        return False  # Don't repeat

    def apply_filter(self) -> Any:
        """Apply the current filter to the connections"""
        try:
            connections_to_show = self._connections_to_show()
            GLib.idle_add(self._refresh_store, connections_to_show)
            self._notify_count_changed()
        except UI_ERRORS as e:
            logger.error(f"Error applying filter: {e}", extra={"class_name": self.__class__.__name__})

    def add_connection(self, address: str, port: int, torrent_hash: str = "", **kwargs: Any) -> None:
        """Add a new connection (defaults: connected=True; kwargs override)"""
        connection_kwargs = {"torrent_hash": torrent_hash, "connected": True, **kwargs}
        self._manager_call("add_{d}_connection", address, port, **connection_kwargs)
        self.apply_filter()

    def update_connection(self, address: str, port: int, **kwargs: Any) -> None:
        """Update an existing connection"""
        self._manager_call("update_{d}_connection", address, port, **kwargs)
        self.apply_filter()

    def remove_connection(self, address: str, port: int) -> None:
        """Remove a connection"""
        self._manager_call("remove_{d}_connection", address, port)
        self.apply_filter()

    def clear_connections(self) -> None:
        """Clear all displayed connections (the shared connection manager is untouched)"""
        self.view.store.remove_all()
        self.connections.clear()

    def get_connection_count(self) -> int:
        """Get the number of active connections (currently visible)"""
        return len(self.connections)

    def get_total_connection_count(self) -> int:
        """Get the total number of connections (including filtered)"""
        return int(self._manager_call("get_global_{d}_count"))

    @property
    def all_connections(self) -> Any:
        """Property for backward compatibility - delegates to connection manager"""
        return self._manager_call("get_all_{d}_connections")

    def on_language_changed(self, source: Any = None, new_language: Any = None) -> None:
        """Handle language change events for column translation."""
        try:
            logger.trace(
                f"{self.LOG_NAME} language changed to: {new_language}",
                extra={"class_name": self.__class__.__name__},
            )
            self.refresh_column_translations()
        except UI_ERRORS as e:
            logger.error(
                f"Error handling language change in {self.LOG_NAME}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
