"""
Outgoing Connections Component

Manages the UI for displaying outgoing peer connections, showing information
about peers that we've initiated connections to.
"""

# isort: skip_file

# fmt: off
import gi

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.connection_manager import get_connection_manager
from d_fake_seeder.domain.torrent.model.connection_peer import ConnectionPeer
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin

from ..base_component import Component

gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")

from gi.repository import Gio  # noqa: E402
from gi.repository import GLib, GObject, Gtk  # noqa: E402

# fmt: on


class OutgoingConnectionsTab(Component, ColumnTranslationMixin):
    """Component for managing outgoing connections display"""

    def __init__(self, builder, model):
        super().__init__()
        ColumnTranslationMixin.__init__(self)

        logger.debug(
            "OutgoingConnectionsTab view startup",
            extra={"class_name": self.__class__.__name__},
        )
        self.builder = builder
        self.model = model

        # Get UI elements
        self.outgoing_columnview = self.builder.get_object("outgoing_columnview")
        self.filter_checkbox = self.builder.get_object("outgoing_filter_selected_checkbox")

        # Initialize the column view
        self.init_outgoing_column_view()

        # Use centralized connection manager
        self.connection_manager = get_connection_manager()

        # Data store for UI display (filtered view)
        self.outgoing_connections = {}  # ip:port -> ConnectionPeer (filtered for display)
        self.selected_torrent = None
        self.count_update_callback = None  # Callback to update connection counts

        # Register for connection updates
        self.connection_manager.add_update_callback(self.on_connections_updated)

        # Load byte formatting thresholds from settings
        settings = AppSettings.get_instance()
        ui_settings = getattr(settings, "ui_settings", {})
        self.kb_threshold = ui_settings.get("byte_format_threshold_kb", 1024)
        self.mb_threshold = ui_settings.get("byte_format_threshold_mb", 1048576)
        self.gb_threshold = ui_settings.get("byte_format_threshold_gb", 1073741824)

        # Connect checkbox signal
        self.track_signal(
            self.filter_checkbox,
            self.filter_checkbox.connect("toggled", self.on_filter_toggled),
        )

        # Connect to model selection changes
        if hasattr(self.model, "connect"):
            self.track_signal(
                self.model,
                self.model.connect("selection-changed", self.on_selection_changed),
            )

        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.track_signal(
                    self.model,
                    self.model.connect("language-changed", self.on_language_changed),
                )
                logger.debug(
                    "Connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.debug(
                    f"Could not connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    def on_connections_updated(self):
        """Called when the connection manager updates connections"""
        # Update the display by reapplying the filter
        self.apply_filter()

        # Notify count changed if callback is set
        self._notify_count_changed()

    def set_count_update_callback(self, callback):
        """Set the callback to be called when connection count changes"""
        self.count_update_callback = callback

    def _notify_count_changed(self):
        """Notify connection count changed (handled by main data-changed signal)"""
        # Connection count updates now handled by main data-changed signal
        # to respect tickspeed intervals and prevent UI flooding
        pass

    def init_outgoing_column_view(self):
        """Initialize the outgoing connections column view"""
        logger.debug(
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

            # Register column for translation instead of using hardcoded title
            self.register_translatable_column(self.outgoing_columnview, column, property_name, "outgoing_connections")

            # Create sorter for the column
            if property_name in [
                "connection_time",
                "bytes_downloaded",
                "download_rate",
                "requests_sent",
                "pieces_received",
            ]:
                property_expression = Gtk.PropertyExpression.new(ConnectionPeer, None, property_name)
                sorter = Gtk.NumericSorter.new(property_expression)
            elif property_name in [
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

    def setup_cell(self, widget, item, property_name):
        """Setup cell widget based on property type"""

        def setup_when_idle():
            obj = item.get_item()
            if obj is None:
                return

            # Use appropriate widget type
            if property_name in ["handshake_complete", "am_interested", "peer_choking"]:
                widget_obj = Gtk.CheckButton()
                widget_obj.set_sensitive(False)  # Read-only
            else:
                widget_obj = Gtk.Label()
                # Align based on text direction (RTL for Arabic, Hebrew, etc.)
                text_direction = widget_obj.get_direction()
                if text_direction == Gtk.TextDirection.RTL:
                    widget_obj.set_xalign(1)  # Right align for RTL
                else:
                    widget_obj.set_xalign(0)  # Left align for LTR

            item.set_child(widget_obj)

        GLib.idle_add(setup_when_idle)

    def bind_cell(self, widget, item, property_name):
        """Bind cell data to widget"""

        def bind_when_idle():
            try:
                # Early validation - exit immediately if any required objects are None
                if item is None:
                    return

                child = item.get_child()
                obj = item.get_item()

                # Check if both child and obj are valid before proceeding
                if obj is None or child is None:
                    return

                # Validate that obj has the property we're trying to bind
                if not hasattr(obj, property_name):
                    return

                # Re-check validity right before each operation to handle race conditions
                if property_name in [
                    "handshake_complete",
                    "am_interested",
                    "peer_choking",
                ]:
                    # Double check before binding - ensure child has expected properties
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, property_name)
                        and hasattr(child, "active")
                        and hasattr(obj, "bind_property")
                    ):
                        try:
                            binding = obj.bind_property(
                                property_name,
                                child,
                                "active",
                                GObject.BindingFlags.SYNC_CREATE,
                            )
                            self.track_binding(binding)
                        except Exception as e:
                            logger.error(
                                f"Error binding boolean property {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name == "connection_time":
                    # Format timestamp with additional checks
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, "connection_time")
                        and hasattr(child, "set_text")
                    ):
                        import datetime

                        try:
                            dt = datetime.datetime.fromtimestamp(obj.connection_time)
                            child.set_text(dt.strftime("%H:%M:%S"))
                        except Exception as e:
                            logger.error(
                                f"Error formatting connection time: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name in [
                    "bytes_downloaded",
                    "download_rate",
                    "requests_sent",
                    "pieces_received",
                ]:
                    # Format bytes/rates/counts with additional checks
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, property_name)
                        and hasattr(child, "set_text")
                    ):
                        try:
                            value = getattr(obj, property_name)
                            if property_name == "bytes_downloaded":
                                child.set_text(self.format_bytes(value))
                            elif property_name == "download_rate":
                                child.set_text(f"{value:.1f} B/s")
                            elif property_name in ["requests_sent", "pieces_received"]:
                                child.set_text(str(value))
                        except Exception as e:
                            logger.error(
                                f"Error formatting {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name == "status":
                    # Format status with visual indicators
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(child, "set_text")
                        and hasattr(child, "add_css_class")
                    ):
                        try:
                            status = getattr(obj, property_name, "unknown")
                            status_icons = {
                                "connecting": "🔌",
                                "connected": "✅",
                                "failed": "❌",
                                "disconnected": "🔴",
                            }
                            icon = status_icons.get(status, "❓")
                            child.set_text(f"{icon} {status.title()}")

                            # Set color based on status
                            if status == "failed":
                                child.add_css_class("error")
                            elif status == "connected":
                                child.add_css_class("success")
                        except Exception as e:
                            logger.error(
                                f"Error formatting status: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name in ["address", "client"]:
                    # Direct text setting for address and client fields
                    if obj is not None and child is not None and hasattr(child, "set_text"):
                        try:
                            value = getattr(obj, property_name, "")
                            if property_name == "address" and hasattr(obj, "port"):
                                # Combine address and port for display
                                port = getattr(obj, "port", 0)
                                if value and port:
                                    child.set_text(f"{value}:{port}")
                                elif value:
                                    child.set_text(value)
                                else:
                                    child.set_text("")
                            else:
                                child.set_text(str(value) if value else "")
                        except Exception as e:
                            logger.error(
                                f"Error formatting {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name == "failure_reason":
                    # Only show failure reason if status is failed
                    if obj is not None and child is not None and hasattr(child, "set_text"):
                        try:
                            status = getattr(obj, "status", "")
                            if status == "failed":
                                reason = getattr(obj, property_name, "")
                                child.set_text(reason if reason else "Unknown error")
                            else:
                                child.set_text("")
                        except Exception as e:
                            logger.error(
                                f"Error formatting failure reason: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                else:
                    # Default property binding with additional checks
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, property_name)
                        and hasattr(child, "label")
                        and hasattr(obj, "bind_property")
                    ):
                        try:
                            binding = obj.bind_property(
                                property_name,
                                child,
                                "label",
                                GObject.BindingFlags.SYNC_CREATE,
                                Component.to_str,
                            )
                            self.track_binding(binding)
                        except Exception as e:
                            logger.error(
                                f"Error binding default property {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
            except Exception as e:
                logger.error(
                    f"Error binding cell {property_name}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        GLib.idle_add(bind_when_idle)

    def format_bytes(self, bytes_value):
        """Format bytes in human readable format using configurable thresholds"""
        if bytes_value < self.kb_threshold:
            return f"{bytes_value} B"
        elif bytes_value < self.mb_threshold:
            return f"{bytes_value / self.kb_threshold:.1f} KB"
        elif bytes_value < self.gb_threshold:
            return f"{bytes_value / self.mb_threshold:.1f} MB"
        else:
            return f"{bytes_value / self.gb_threshold:.1f} GB"

    def on_filter_toggled(self, checkbox):
        """Handle filter checkbox toggle"""
        logger.debug(
            f"Outgoing connections filter toggled: {checkbox.get_active()}",
            extra={"class_name": self.__class__.__name__},
        )
        self.apply_filter()

    def on_selection_changed(self, source, model, torrent):
        """Handle model selection change"""
        self.selected_torrent = torrent
        logger.debug(
            f"Outgoing connections selection changed: " f"{torrent.id if torrent else 'None'}",
            extra={"class_name": self.__class__.__name__},
        )
        self.apply_filter()

    def apply_filter(self):
        """Apply the current filter to the connections"""
        try:
            filter_enabled = self.filter_checkbox.get_active()

            # Determine which connections should be shown
            connections_to_show = []
            for (
                connection_key,
                connection_peer,
            ) in self.connection_manager.get_all_outgoing_connections().items():
                should_show = True

                if filter_enabled and self.selected_torrent:
                    # Only show connections for the selected torrent
                    should_show = connection_peer.torrent_hash == self.selected_torrent.id

                if should_show and connection_key not in self.outgoing_connections:
                    # Only add if not already shown to avoid duplicates
                    connections_to_show.append((connection_key, connection_peer))

            # Schedule the filter update in idle to avoid snapshot issues
            def update_filter_when_idle():
                try:
                    # Clear current displayed connections
                    self.outgoing_connections.clear()

                    # Clear the store safely
                    self.outgoing_store.remove_all()

                    # Add filtered connections
                    for connection_key, connection_peer in connections_to_show:
                        try:
                            # Check if peer is still valid before adding
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
                return False  # Don't repeat

            GLib.idle_add(update_filter_when_idle)

            # Notify that the count changed
            self._notify_count_changed()

        except Exception as e:
            logger.error(
                f"Error applying filter: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def add_outgoing_connection(self, address: str, port: int, torrent_hash: str = "", **kwargs):
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

    def update_outgoing_connection(self, address: str, port: int, **kwargs):
        """Update an existing outgoing connection"""
        # Delegate to centralized connection manager
        self.connection_manager.update_outgoing_connection(address, port, **kwargs)

        # Apply current filter to update display
        self.apply_filter()

    def remove_outgoing_connection(self, address: str, port: int):
        """Remove an outgoing connection"""
        # Delegate to centralized connection manager
        self.connection_manager.remove_outgoing_connection(address, port)

        # Apply current filter to update display
        self.apply_filter()

    def clear_connections(self):
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
    def all_connections(self):
        """Property for backward compatibility - delegates to connection manager"""
        return self.connection_manager.get_all_outgoing_connections()

    def handle_model_changed(self, source, data_obj, data_changed):
        """Handle model changes"""
        logger.debug(
            "OutgoingConnections model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute changes"""
        logger.debug(
            "OutgoingConnections attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, data_changed):
        """Handle settings changes"""
        logger.debug(
            "OutgoingConnections settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view"""
        logger.debug(
            "OutgoingConnections update view",
            extra={"class_name": self.__class__.__name__},
        )

    def on_language_changed(self, source=None, new_language=None):
        """Handle language change events for column translation."""
        try:
            logger.debug(
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
