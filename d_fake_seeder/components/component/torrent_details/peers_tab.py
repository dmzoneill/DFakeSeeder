"""
Peers tab for torrent details.

Displays torrent peer information in a column view with sorting capabilities.
"""

# isort: skip_file

# fmt: off
from typing import Any, Dict, List

import gi

from d_fake_seeder.domain.torrent.model.torrent_peer import TorrentPeer
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin

from .base_tab import BaseTorrentTab
from .tab_mixins import DataUpdateMixin, PerformanceMixin, UIUtilityMixin

gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")
from gi.repository import Gio  # noqa: E402
from gi.repository import GObject, Gtk  # noqa: E402

# fmt: on


class PeersTab(
    BaseTorrentTab,
    DataUpdateMixin,
    UIUtilityMixin,
    PerformanceMixin,
    ColumnTranslationMixin,
):
    """
    Peers tab component for displaying torrent peer information.

    Shows peer data in a sortable column view with data from multiple sources.
    """

    def __init__(self, builder: Gtk.Builder, model):
        """Initialize the peers tab."""
        # Initialize mixins BEFORE calling super().__init__() because
        # BaseTorrentTab.__init__() calls _init_widgets() which needs
        # ColumnTranslationMixin._translatable_columns to exist
        PerformanceMixin.__init__(self)
        ColumnTranslationMixin.__init__(self)

        super().__init__(builder, model)

        self._global_peer_manager = None
        self._incoming_connections = None
        self._outgoing_connections = None
        self._peers_store = None
        self._sort_model = None
        self._selection = None

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Peers"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "peers_tab"

    def _init_widgets(self) -> None:
        """Initialize Peers tab widgets."""
        # Cache the peers column view widget and content container
        self._peers_columnview = self.get_widget("peers_columnview")
        self._peers_content = self.get_widget("peers_content")
        self._init_peers_column_view()

    def set_connection_managers(
        self,
        incoming_connections=None,
        outgoing_connections=None,
        global_peer_manager=None,
    ):
        """
        Set connection managers for peer data sources.

        Args:
            incoming_connections: Incoming connections component
            outgoing_connections: Outgoing connections component
            global_peer_manager: Global peer manager
        """
        self._incoming_connections = incoming_connections
        self._outgoing_connections = outgoing_connections
        self._global_peer_manager = global_peer_manager

    def _init_peers_column_view(self) -> None:
        """Initialize the peers column view with sortable columns."""
        try:
            self.logger.debug(
                "Initializing peers column view",
                extra={"class_name": self.__class__.__name__},
            )

            if not self._peers_columnview:
                self.logger.error("Peers column view not found")
                return

            self.logger.debug(f"Peers column view widget: {self._peers_columnview}")

            # Create list store for peer data
            self._peers_store = Gio.ListStore.new(TorrentPeer)
            self.track_store(self._peers_store)  # Track for automatic cleanup
            self.logger.debug(f"Created peers store: {self._peers_store}")

            # Get TorrentPeer properties for columns
            properties = [prop.name for prop in TorrentPeer.list_properties()]
            self.logger.debug(f"Creating {len(properties)} peer columns: {properties}")

            # Create columns for each property
            for property_name in properties:
                self._create_peer_column(property_name)

            # Set up sorting
            sorter = Gtk.ColumnView.get_sorter(self._peers_columnview)
            self._sort_model = Gtk.SortListModel.new(self._peers_store, sorter)
            self._selection = Gtk.SingleSelection.new(self._sort_model)
            self._peers_columnview.set_model(self._selection)

            self.logger.debug(f"Peers column view initialized successfully with {len(properties)} columns")

        except Exception as e:
            self.logger.error(f"Error initializing peers column view: {e}", exc_info=True)

    def on_language_changed(self, source=None, new_language=None):
        """Handle language change events for column translation."""
        try:
            # Call parent method for general tab translation
            super().on_language_changed(source, new_language)

            # Refresh column translations
            self.refresh_column_translations()

        except Exception as e:
            self.logger.error(f"Error handling language change in {self.tab_name} tab: {e}")

    def _create_peer_column(self, property_name: str) -> None:
        """
        Create a column for a peer property.

        Args:
            property_name: Property name for the column
        """
        try:
            # Create factory for the column
            factory = Gtk.SignalListItemFactory()
            self.track_signal(
                factory,
                factory.connect("setup", self._setup_column_item, property_name),
            )
            self.track_signal(factory, factory.connect("bind", self._bind_column_item, property_name))

            # Create column
            column = Gtk.ColumnViewColumn.new(None, factory)

            # Set column properties for visibility
            column.set_expand(True)
            column.set_resizable(True)

            # Register column for translation instead of setting title directly
            self.register_translatable_column(self._peers_columnview, column, property_name, "peer")

            # Create sorter for the column
            property_expression = Gtk.PropertyExpression.new(TorrentPeer, None, property_name)
            sorter = self._create_property_sorter(property_name, property_expression)
            if sorter:
                column.set_sorter(sorter)

            # Add column to view
            if self._peers_columnview is not None:
                self._peers_columnview.append_column(column)
                self.logger.debug(f"Added peer column: {property_name}")

        except Exception as e:
            self.logger.error(f"Error creating peer column {property_name}: {e}")

    def _create_property_sorter(self, property_name: str, property_expression):
        """
        Create appropriate sorter based on property type.

        Args:
            property_name: Property name
            property_expression: Property expression

        Returns:
            Appropriate sorter for the property type
        """
        try:
            property_spec = TorrentPeer.find_property(property_name)
            if not property_spec:
                return None

            property_type = property_spec.value_type.fundamental

            if property_type == GObject.TYPE_STRING:
                return Gtk.StringSorter.new(property_expression)
            elif property_type in [GObject.TYPE_FLOAT, GObject.TYPE_DOUBLE]:
                return Gtk.NumericSorter.new(property_expression)
            elif property_type == GObject.TYPE_BOOLEAN:
                return Gtk.NumericSorter.new(property_expression)
            else:
                return Gtk.StringSorter.new(property_expression)

        except Exception as e:
            self.logger.error(f"Error creating sorter for {property_name}: {e}")
            return None

    def _show_empty_state(self) -> None:
        """Show the empty state and hide the content."""
        try:
            # Call parent to show empty state widget
            super()._show_empty_state()

            # Hide the peers content
            if self._peers_content:
                self._peers_content.set_visible(False)
                self.logger.debug("Hiding peers content")
        except Exception as e:
            self.logger.error(f"Error showing empty state: {e}")

    def _hide_empty_state(self) -> None:
        """Hide the empty state and show the content."""
        try:
            # Call parent to hide empty state widget
            super()._hide_empty_state()

            # Show the peers content
            if self._peers_content:
                self._peers_content.set_visible(True)
                self.logger.debug("Showing peers content")
        except Exception as e:
            self.logger.error(f"Error hiding empty state: {e}")

    def clear_content(self) -> None:
        """Clear the peers tab content."""
        try:
            if self._peers_store:
                self._peers_store.remove_all()
                self.logger.debug(f"Cleared peers store (now has {self._peers_store.get_n_items()} items)")

            # Show empty state
            super().clear_content()

        except Exception as e:
            self.logger.error(f"Error clearing peers tab content: {e}")

    def update_content(self, torrent) -> None:
        """
        Update peers tab content with torrent peer data.

        Args:
            torrent: Torrent object to display
        """
        try:
            torrent_id = torrent.id if torrent else "None"
            self.logger.debug(
                f"Updating peers tab for torrent {torrent_id}",
                extra={"class_name": self.__class__.__name__},
            )

            if not torrent:
                self.logger.debug("No torrent provided, clearing content")
                self.clear_content()
                return

            # Hide empty state when showing content
            self._hide_empty_state()

            # Collect peer data from all sources
            peer_data = self._collect_peer_data(torrent)
            self.logger.debug(f"Collected {len(peer_data)} peers for torrent {torrent_id}")

            # Update peers store with new data
            self._update_peers_store(peer_data)

            final_count = self._peers_store.get_n_items() if self._peers_store else 0
            self.logger.debug(f"Peers tab updated: {final_count} peers now in store")

        except Exception as e:
            self.logger.error(f"Error updating peers tab content: {e}", exc_info=True)

    def _collect_peer_data(self, torrent) -> list:
        """
        Collect peer data from all available sources.

        Args:
            torrent: Torrent object

        Returns:
            List of peer data dictionaries
        """
        try:
            peer_data: List[Dict[str, Any]] = []

            # Get data from global peer manager
            global_peer_count = self._add_global_peer_data(torrent, peer_data)

            # Get data from legacy seeder if global manager has no data
            legacy_peer_count = self._add_legacy_peer_data(torrent, peer_data)

            # Add data from active connections
            connection_peer_count = self._add_connection_peer_data(torrent, peer_data)

            self.logger.debug(
                f"Collected peer data for torrent {torrent.id}: "
                f"global={global_peer_count}, legacy={legacy_peer_count}, "
                f"connections={connection_peer_count}, total={len(peer_data)}",
                extra={"class_name": self.__class__.__name__},
            )

            return peer_data

        except Exception as e:
            self.logger.error(f"Error collecting peer data: {e}")
            return []

    def _add_global_peer_data(self, torrent, peer_data: list) -> int:
        """
        Add peer data from global peer manager.

        Args:
            torrent: Torrent object
            peer_data: List to add peer data to

        Returns:
            Number of peers added
        """
        try:
            if not self._global_peer_manager:
                return 0

            global_peers = self._global_peer_manager.get_torrent_peers(str(torrent.id))
            peer_data.extend(global_peers)
            return len(global_peers)

        except Exception as e:
            self.logger.error(f"Error getting peers from global peer manager: {e}")
            return 0

    def _add_legacy_peer_data(self, torrent, peer_data: list) -> int:
        """
        Add peer data from legacy seeder if no global data.

        Args:
            torrent: Torrent object
            peer_data: List to add peer data to

        Returns:
            Number of peers added
        """
        try:
            # Only use legacy data if no global data exists
            if peer_data:
                return 0

            if not hasattr(torrent, "get_seeder") or not torrent.get_seeder():
                return 0

            seeder = torrent.get_seeder()
            if not hasattr(seeder, "peers"):
                return 0

            legacy_count = 0
            for peer in seeder.peers:
                client = seeder.clients[peer] if hasattr(seeder, "clients") and peer in seeder.clients else "Unknown"
                peer_data.append(
                    {
                        "address": str(peer),
                        "client": client,
                        "connected": False,
                        "is_seed": False,
                        "upload_rate": 0.0,
                        "download_rate": 0.0,
                        "progress": 0.0,
                    }
                )
                legacy_count += 1

            return legacy_count

        except Exception as e:
            self.logger.error(f"Error adding legacy peer data: {e}")
            return 0

    def _add_connection_peer_data(self, torrent, peer_data: list) -> int:
        """
        Add peer data from active connections.

        Args:
            torrent: Torrent object
            peer_data: List to add peer data to

        Returns:
            Number of peers added
        """
        try:
            if not self._incoming_connections or not self._outgoing_connections:
                return 0

            connection_addresses = set()

            # Collect addresses from incoming connections
            for (
                conn_key,
                conn_peer,
            ) in self._incoming_connections.all_connections.items():
                if hasattr(conn_peer, "torrent_hash") and conn_peer.torrent_hash == str(torrent.id):
                    address = f"{conn_peer.address}:{conn_peer.port}"
                    connection_addresses.add(address)

            # Collect addresses from outgoing connections
            for (
                conn_key,
                conn_peer,
            ) in self._outgoing_connections.all_connections.items():
                if hasattr(conn_peer, "torrent_hash") and conn_peer.torrent_hash == str(torrent.id):
                    address = f"{conn_peer.address}:{conn_peer.port}"
                    connection_addresses.add(address)

            # Add connection peers not already in peer_data
            existing_addresses = {peer.get("address", "") for peer in peer_data}
            connection_count = 0

            for address in connection_addresses:
                if address not in existing_addresses:
                    peer_data.append(
                        {
                            "address": address,
                            "client": "Connected Peer",
                            "connected": True,
                            "is_seed": False,
                            "upload_rate": 0.0,
                            "download_rate": 0.0,
                            "progress": 0.0,
                        }
                    )
                    connection_count += 1

            return connection_count

        except Exception as e:
            self.logger.error(f"Error adding connection peer data: {e}")
            return 0

    def _update_peers_store(self, peer_data: list) -> None:
        """
        Update the peers store with new data.

        Args:
            peer_data: List of peer data dictionaries
        """
        try:
            if not self._peers_store:
                return

            # Get current model info
            current_model = self._peers_columnview.get_model()
            num_rows = current_model.get_n_items() if current_model else 0
            num_peers = len(peer_data)

            # Only update if the count changed (optimization)
            if num_rows != num_peers:
                self._peers_store.remove_all()

                # Add new peer data
                for peer in peer_data:
                    try:
                        row = TorrentPeer(
                            address=peer.get("address", ""),
                            client=peer.get("client", "Unknown"),
                            country="",  # Country not provided yet
                            progress=peer.get("progress", 0.0),
                            down_speed=peer.get("download_rate", 0.0),
                            up_speed=peer.get("upload_rate", 0.0),
                            seed=peer.get("is_seed", False),
                            peer_id="",  # Peer ID not provided yet
                        )
                        self._peers_store.append(row)
                    except Exception as e:
                        self.logger.error(f"Error creating TorrentPeer row: {e}")

                # Ensure model is set
                if self._peers_columnview.get_model() != self._selection:
                    self._peers_columnview.set_model(self._selection)

        except Exception as e:
            self.logger.error(f"Error updating peers store: {e}")

    # Column setup/bind callbacks
    def _setup_column_item(self, widget, item, property_name: str) -> None:
        """Setup callback for column items."""

        def setup_when_idle():
            try:
                label = Gtk.Label()
                label.set_hexpand(True)
                # Align based on text direction (RTL for Arabic, Hebrew, etc.)
                text_direction = label.get_direction()
                if text_direction == Gtk.TextDirection.RTL:
                    label.set_halign(Gtk.Align.END)
                else:
                    label.set_halign(Gtk.Align.START)
                item.set_child(label)
            except Exception as e:
                self.logger.error(f"Error in setup callback: {e}")
            return False

        self.batch_update(setup_when_idle)

    def _bind_column_item(self, widget, item, property_name: str) -> None:
        """Bind callback for column items."""

        def bind_when_idle():
            try:
                child = item.get_child()
                if not child:
                    return False

                list_item = item.get_item()
                if not list_item:
                    return False

                value = self.safe_get_property(list_item, property_name.replace("-", "_"), "")
                formatted_value = self.format_property_value(value)
                child.set_text(str(formatted_value))

            except Exception as e:
                self.logger.error(f"Error in bind callback: {e}")
            return False

        self.batch_update(bind_when_idle)

    def get_peer_count(self) -> int:
        """
        Get the number of peers currently displayed.

        Returns:
            Number of peers
        """
        try:
            if self._peers_store:
                return self._peers_store.get_n_items()
            return 0
        except Exception:
            return 0
