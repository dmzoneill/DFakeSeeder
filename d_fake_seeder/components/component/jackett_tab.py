"""
Jackett Tab - Torrent search integration via Jackett API.

Allows users to search for torrents using Jackett's Torznab API
and add results directly to DFakeSeeder.
"""

import os
import threading
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from types import SimpleNamespace
from typing import Any

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.gi_gtk4 import Gio, GLib, GObject, Gtk
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.xdg_paths import get_config_dir

# Narrowed replacement for the previous broad ``except Exception`` clauses: the
# search/config/add paths touch settings, networking, XML parsing, GLib and the
# filesystem, so these are the failures worth swallowing defensively.
_JACKETT_ERRORS = (AttributeError, TypeError, ValueError, KeyError, IndexError, OSError, GLib.Error)


class JackettSearchResult(GObject.Object):
    """GObject wrapper exposing a Jackett result's display fields as bindable properties.

    The payload is a plain ``dict`` so the row carries its display values without
    the wrapper itself accumulating that many instance attributes.
    """

    __gtype_name__ = "JackettSearchResult"

    def __init__(self, data: dict) -> None:
        super().__init__()
        self._data = dict(data)
        self._data["size_str"] = self._format_bytes(self._data["size"])

    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes to human readable string."""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        if bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        if bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.1f} MB"
        return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"

    @GObject.Property(type=str)
    def title(self) -> str:
        """Torrent title."""
        return self._data["title"]

    @GObject.Property(type=int)
    def size(self) -> int:
        """Size in bytes."""
        return self._data["size"]

    @GObject.Property(type=str)
    def size_str(self) -> str:
        """Human-readable size."""
        return self._data["size_str"]

    @GObject.Property(type=int)
    def seeders(self) -> int:
        """Number of seeders."""
        return self._data["seeders"]

    @GObject.Property(type=int)
    def leechers(self) -> int:
        """Number of leechers."""
        return self._data["leechers"]

    @GObject.Property(type=str)
    def category(self) -> str:
        """Torznab category label."""
        return self._data["category"]

    @GObject.Property(type=str)
    def indexer(self) -> str:
        """Indexer that produced the result."""
        return self._data["indexer"]

    @GObject.Property(type=str)
    def download_url(self) -> str:
        """Direct .torrent download URL."""
        return self._data["download_url"]

    @GObject.Property(type=str)
    def magnet_url(self) -> str:
        """Magnet URI, if provided."""
        return self._data["magnet_url"]

    @GObject.Property(type=str)
    def info_url(self) -> str:
        """Details/comments URL."""
        return self._data["info_url"]

    @GObject.Property(type=str)
    def publish_date(self) -> str:
        """Publication date string."""
        return self._data["publish_date"]


class JackettTab(Component):
    """
    Jackett tab for searching torrents via Jackett API.

    Features:
    - Search input with category filter
    - Results display with torrent info
    - Download/add torrent functionality
    - Configurable Jackett connection
    """

    def __init__(self, builder: Any, model: Any) -> None:
        """Initialize the Jackett tab."""
        super().__init__()

        logger.trace(
            "JackettTab initializing",
            extra={"class_name": self.__class__.__name__},
        )

        self.builder = builder
        self.model = model
        self.settings = AppSettings.get_instance()

        # Get the jackett tab content container
        self.container = self.builder.get_object("jackett_tab_content")
        if not self.container:
            logger.error(
                "jackett_tab_content not found in builder",
                extra={"class_name": self.__class__.__name__},
            )
            return

        # Clear placeholder content
        while self.container.get_first_child():
            self.container.remove(self.container.get_first_child())

        # Set container properties
        self.container.set_orientation(Gtk.Orientation.VERTICAL)
        self.container.set_spacing(12)
        self.container.set_margin_start(16)
        self.container.set_margin_end(16)
        self.container.set_margin_top(16)
        self.container.set_margin_bottom(16)
        self.container.set_halign(Gtk.Align.FILL)
        self.container.set_valign(Gtk.Align.FILL)

        # Display widgets and the list-view objects are grouped so the component
        # stays within the instance-attribute limit.
        self._widgets: dict[str, Any] = {}
        self._view = SimpleNamespace(store=None, selection=None, column=None)

        # Build UI
        self._build_ui()

        # Connect to settings changes
        self.settings.connect("attribute-changed", self._on_settings_changed)

        logger.debug(
            "JackettTab initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _(self, text: Any) -> Any:
        """Get translation function from model's TranslationManager."""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text

    def _build_ui(self) -> None:
        """Build the Jackett tab UI from its component sections."""
        self._build_header_section()
        self._build_config_section()
        self._build_search_section()
        self._build_results_section()
        self._update_connection_status()

    def _build_header_section(self) -> None:
        """Build the title/status header row."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_halign(Gtk.Align.FILL)

        # Title
        title_label = Gtk.Label(label=self._("Jackett Torrent Search"))
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.append(title_label)

        # Connection status indicator
        self._widgets["status_indicator"] = Gtk.Label(label="●")
        self._widgets["status_indicator"].add_css_class("dim-label")
        self._widgets["status_indicator"].set_halign(Gtk.Align.END)
        header_box.append(self._widgets["status_indicator"])

        self._widgets["status_label"] = Gtk.Label(label=self._("Not Configured"))
        self._widgets["status_label"].add_css_class("dim-label")
        self._widgets["status_label"].set_halign(Gtk.Align.END)
        header_box.append(self._widgets["status_label"])

        self.container.append(header_box)

    def _build_config_section(self) -> None:
        """Build the Jackett configuration frame."""
        config_frame = Gtk.Frame()
        config_frame.set_label(self._("Jackett Configuration"))
        config_frame.set_margin_top(8)

        config_grid = Gtk.Grid()
        config_grid.set_row_spacing(8)
        config_grid.set_column_spacing(16)
        config_grid.set_margin_start(12)
        config_grid.set_margin_end(12)
        config_grid.set_margin_top(12)
        config_grid.set_margin_bottom(12)

        # API URL row
        config_grid.attach(Gtk.Label(label=self._("API URL:"), halign=Gtk.Align.END), 0, 0, 1, 1)
        self._widgets["api_url_entry"] = Gtk.Entry()
        self._widgets["api_url_entry"].set_hexpand(True)
        self._widgets["api_url_entry"].set_placeholder_text("http://localhost:9117")
        jackett_settings = self.settings.get("jackett_settings", {})
        self._widgets["api_url_entry"].set_text(jackett_settings.get("api_url", "http://localhost:9117"))
        self._widgets["api_url_entry"].connect("changed", self._on_config_changed)
        config_grid.attach(self._widgets["api_url_entry"], 1, 0, 2, 1)

        # API Key row
        config_grid.attach(Gtk.Label(label=self._("API Key:"), halign=Gtk.Align.END), 0, 1, 1, 1)
        self._widgets["api_key_entry"] = Gtk.Entry()
        self._widgets["api_key_entry"].set_hexpand(True)
        self._widgets["api_key_entry"].set_placeholder_text(self._("Enter your Jackett API key"))
        self._widgets["api_key_entry"].set_visibility(False)  # Hide API key
        self._widgets["api_key_entry"].set_text(jackett_settings.get("api_key", ""))
        self._widgets["api_key_entry"].connect("changed", self._on_config_changed)
        config_grid.attach(self._widgets["api_key_entry"], 1, 1, 1, 1)

        # Show/Hide API key button
        self._widgets["show_key_button"] = Gtk.Button()
        self._widgets["show_key_button"].set_icon_name("view-reveal-symbolic")
        self._widgets["show_key_button"].set_tooltip_text(self._("Show/Hide API Key"))
        self._widgets["show_key_button"].connect("clicked", self._on_toggle_key_visibility)
        config_grid.attach(self._widgets["show_key_button"], 2, 1, 1, 1)

        # Test connection button
        self._widgets["test_button"] = Gtk.Button(label=self._("Test Connection"))
        self._widgets["test_button"].connect("clicked", self._on_test_connection)
        config_grid.attach(self._widgets["test_button"], 0, 2, 1, 1)

        # Save config button
        self._widgets["save_config_button"] = Gtk.Button(label=self._("Save Configuration"))
        self._widgets["save_config_button"].add_css_class("suggested-action")
        self._widgets["save_config_button"].connect("clicked", self._on_save_config)
        config_grid.attach(self._widgets["save_config_button"], 1, 2, 1, 1)

        config_frame.set_child(config_grid)
        self.container.append(config_frame)

    def _build_search_section(self) -> None:
        """Build the search input frame."""
        search_frame = Gtk.Frame()
        search_frame.set_label(self._("Search"))
        search_frame.set_margin_top(8)

        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        search_box.set_margin_start(12)
        search_box.set_margin_end(12)
        search_box.set_margin_top(12)
        search_box.set_margin_bottom(12)

        # Search input row
        search_input_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        search_input_box.set_hexpand(True)

        self._widgets["search_entry"] = Gtk.Entry()
        self._widgets["search_entry"].set_hexpand(True)
        self._widgets["search_entry"].set_placeholder_text(self._("Enter search query..."))
        self._widgets["search_entry"].connect("activate", self._on_search_activated)
        search_input_box.append(self._widgets["search_entry"])

        # Category dropdown
        self._widgets["category_dropdown"] = Gtk.DropDown()
        category_list = Gtk.StringList.new(
            [
                self._("All"),
                self._("Movies"),
                self._("TV"),
                self._("Music"),
                self._("Games"),
                self._("Software"),
                self._("Anime"),
                self._("Books"),
            ]
        )
        self._widgets["category_dropdown"].set_model(category_list)
        self._widgets["category_dropdown"].set_selected(0)
        search_input_box.append(self._widgets["category_dropdown"])

        # Search button
        self._widgets["search_button"] = Gtk.Button(label=self._("Search"))
        self._widgets["search_button"].add_css_class("suggested-action")
        self._widgets["search_button"].connect("clicked", self._on_search_clicked)
        search_input_box.append(self._widgets["search_button"])

        search_box.append(search_input_box)

        # Search status label
        self._widgets["search_status_label"] = Gtk.Label(label="")
        self._widgets["search_status_label"].set_halign(Gtk.Align.START)
        self._widgets["search_status_label"].add_css_class("dim-label")
        search_box.append(self._widgets["search_status_label"])

        search_frame.set_child(search_box)
        self.container.append(search_frame)

    def _build_results_section(self) -> None:
        """Build the results column view frame."""
        results_frame = Gtk.Frame()
        results_frame.set_label(self._("Search Results"))
        results_frame.set_margin_top(8)
        results_frame.set_vexpand(True)

        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(300)

        # Create list store
        self._view.store = Gio.ListStore.new(JackettSearchResult)

        # Create selection model
        self._view.selection = Gtk.SingleSelection.new(self._view.store)

        # Create column view
        self._view.column = Gtk.ColumnView.new(self._view.selection)
        self._view.column.set_show_row_separators(True)
        self._view.column.set_show_column_separators(True)
        self._view.column.add_css_class("data-table")

        # Add columns
        self._add_column(self._("Title"), "title", self._title_factory, expand=True)
        self._add_column(self._("Size"), "size_str", self._text_factory)
        self._add_column(self._("S"), "seeders", self._seeders_factory)
        self._add_column(self._("L"), "leechers", self._leechers_factory)
        self._add_column(self._("Category"), "category", self._text_factory)
        self._add_column(self._("Indexer"), "indexer", self._text_factory)
        self._add_column(self._("Date"), "publish_date", self._text_factory)
        self._add_action_column()

        scrolled.set_child(self._view.column)
        results_frame.set_child(scrolled)
        self.container.append(results_frame)

    def _add_column(
        self,
        title: str,
        property_name: str,
        factory_func: Any,
        expand: bool = False,
    ) -> None:
        """Add a column to the column view."""
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", lambda f, item: self._setup_cell(item))
        factory.connect("bind", lambda f, item: factory_func(item, property_name))

        column = Gtk.ColumnViewColumn.new(title, factory)
        column.set_resizable(True)
        if expand:
            column.set_expand(True)
        self._view.column.append_column(column)

    def _add_action_column(self) -> None:
        """Add action column with download button."""
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_action_cell)
        factory.connect("bind", self._bind_action_cell)

        column = Gtk.ColumnViewColumn.new(self._("Action"), factory)
        column.set_resizable(False)
        self._view.column.append_column(column)

    def _setup_cell(self, item: Gtk.ListItem) -> None:
        """Setup a cell with a label."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(8)
        label.set_margin_end(8)
        label.set_ellipsize(3)  # PANGO_ELLIPSIZE_END
        item.set_child(label)

    def _setup_action_cell(self, factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        """Setup action cell with download button."""
        button = Gtk.Button()
        button.set_icon_name("list-add-symbolic")
        button.set_tooltip_text(self._("Add to Downloads"))
        button.add_css_class("flat")
        item.set_child(button)

    def _bind_action_cell(self, factory: Gtk.SignalListItemFactory, item: Gtk.ListItem) -> None:
        """Bind action cell to result item."""
        button = item.get_child()
        result = item.get_item()
        if button and result:
            # Disconnect previous handler if any
            try:
                button.disconnect_by_func(self._on_add_torrent)
            except _JACKETT_ERRORS:
                pass
            button.connect("clicked", self._on_add_torrent, result)

    def _title_factory(self, item: Gtk.ListItem, prop: str) -> None:
        """Factory for title column with tooltip."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            title = obj.get_property("title")
            label.set_text(title or "-")
            label.set_tooltip_text(title)
            label.set_max_width_chars(50)

    def _text_factory(self, item: Gtk.ListItem, prop: str) -> None:
        """Factory for text columns."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            value = obj.get_property(prop)
            label.set_text(str(value) if value else "-")

    def _seeders_factory(self, item: Gtk.ListItem, prop: str) -> None:
        """Factory for seeders column with color coding."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            seeders = obj.get_property("seeders")
            label.set_text(str(seeders))
            # Color code based on seeder count
            label.remove_css_class("success")
            label.remove_css_class("warning")
            label.remove_css_class("error")
            if seeders >= 10:
                label.add_css_class("success")
            elif seeders >= 1:
                label.add_css_class("warning")
            else:
                label.add_css_class("error")

    def _leechers_factory(self, item: Gtk.ListItem, prop: str) -> None:
        """Factory for leechers column."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            leechers = obj.get_property("leechers")
            label.set_text(str(leechers))

    def _on_toggle_key_visibility(self, button: Gtk.Button) -> None:
        """Toggle API key visibility."""
        visible = self._widgets["api_key_entry"].get_visibility()
        self._widgets["api_key_entry"].set_visibility(not visible)
        if visible:
            button.set_icon_name("view-reveal-symbolic")
        else:
            button.set_icon_name("view-conceal-symbolic")

    def _on_config_changed(self, entry: Gtk.Entry) -> None:
        """Handle config entry changes (no-op; config is read on save)."""

    def _on_save_config(self, button: Gtk.Button) -> None:
        """Save Jackett configuration to settings."""
        try:
            api_url = self._widgets["api_url_entry"].get_text().strip()
            api_key = self._widgets["api_key_entry"].get_text().strip()

            # Update settings
            self.settings.set("jackett_settings.api_url", api_url)
            self.settings.set("jackett_settings.api_key", api_key)
            self.settings.set("jackett_settings.enabled", bool(api_key))

            # Update status
            self._update_connection_status()

            # Show notification
            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(
                    self._("Jackett configuration saved"),
                    notification_type="success",
                )

            logger.info(
                "Jackett configuration saved",
                extra={"class_name": self.__class__.__name__},
            )

        except _JACKETT_ERRORS as e:
            logger.error(
                f"Error saving Jackett config: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_test_connection(self, button: Gtk.Button) -> None:
        """Test connection to Jackett API."""
        self._widgets["test_button"].set_sensitive(False)
        self._widgets["test_button"].set_label(self._("Testing..."))

        def test_thread() -> None:
            try:
                api_url = self._widgets["api_url_entry"].get_text().strip().rstrip("/")
                api_key = self._widgets["api_key_entry"].get_text().strip()

                if not api_url or not api_key:
                    GLib.idle_add(self._show_test_result, False, self._("Missing API URL or Key"))
                    return

                # Test by fetching indexers
                url = f"{api_url}/api/v2.0/indexers/all/results/torznab/api?apikey={api_key}&t=caps"

                req = urllib.request.Request(url)
                req.add_header("User-Agent", "DFakeSeeder/1.0")

                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        GLib.idle_add(
                            self._show_test_result,
                            True,
                            self._("Connection successful!"),
                        )
                    else:
                        GLib.idle_add(self._show_test_result, False, f"HTTP {response.status}")

            except urllib.error.HTTPError as e:
                GLib.idle_add(self._show_test_result, False, f"HTTP Error: {e.code}")
            except urllib.error.URLError as e:
                GLib.idle_add(self._show_test_result, False, f"Connection Error: {e.reason}")
            except _JACKETT_ERRORS as e:
                GLib.idle_add(self._show_test_result, False, str(e))

        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()

    def _show_test_result(self, success: bool, message: str) -> bool:
        """Show test connection result."""
        self._widgets["test_button"].set_sensitive(True)
        self._widgets["test_button"].set_label(self._("Test Connection"))

        from d_fake_seeder.view import View

        if View.instance:
            if success:
                View.instance.notify(message, notification_type="success")
                self._update_connection_status(connected=True)
            else:
                View.instance.notify(
                    f"{self._('Connection failed')}: {message}",
                    notification_type="error",
                )
                self._update_connection_status(connected=False)

        return False

    def _update_connection_status(self, connected: bool | None = None) -> None:
        """Update connection status indicator."""
        jackett_settings = self.settings.get("jackett_settings", {})
        api_key = jackett_settings.get("api_key", "")

        if connected is True:
            self._widgets["status_indicator"].set_text("●")
            self._widgets["status_indicator"].remove_css_class("dim-label")
            self._widgets["status_indicator"].remove_css_class("error")
            self._widgets["status_indicator"].add_css_class("success")
            self._widgets["status_label"].set_text(self._("Connected"))
            self._widgets["status_label"].remove_css_class("dim-label")
            self._widgets["status_label"].add_css_class("success")
        elif connected is False:
            self._widgets["status_indicator"].set_text("●")
            self._widgets["status_indicator"].remove_css_class("dim-label")
            self._widgets["status_indicator"].remove_css_class("success")
            self._widgets["status_indicator"].add_css_class("error")
            self._widgets["status_label"].set_text(self._("Connection Failed"))
            self._widgets["status_label"].remove_css_class("dim-label")
            self._widgets["status_label"].add_css_class("error")
        elif api_key:
            self._widgets["status_indicator"].set_text("●")
            self._widgets["status_indicator"].remove_css_class("success")
            self._widgets["status_indicator"].remove_css_class("error")
            self._widgets["status_indicator"].add_css_class("dim-label")
            self._widgets["status_label"].set_text(self._("Configured"))
            self._widgets["status_label"].add_css_class("dim-label")
        else:
            self._widgets["status_indicator"].set_text("●")
            self._widgets["status_indicator"].remove_css_class("success")
            self._widgets["status_indicator"].remove_css_class("error")
            self._widgets["status_indicator"].add_css_class("dim-label")
            self._widgets["status_label"].set_text(self._("Not Configured"))
            self._widgets["status_label"].add_css_class("dim-label")

    def _on_search_activated(self, entry: Gtk.Entry) -> None:
        """Handle Enter key in search entry."""
        self._on_search_clicked(None)

    def _on_search_clicked(self, button: Gtk.Button | None) -> None:
        """Perform search via Jackett API."""
        query = self._widgets["search_entry"].get_text().strip()
        if not query:
            return

        jackett_settings = self.settings.get("jackett_settings", {})
        api_url = jackett_settings.get("api_url", "").strip().rstrip("/")
        api_key = jackett_settings.get("api_key", "").strip()

        if not api_url or not api_key:
            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(
                    self._("Please configure Jackett API URL and Key first"),
                    notification_type="warning",
                )
            return

        # Get selected category
        category_map = {
            0: "",  # All
            1: "2000",  # Movies
            2: "5000",  # TV
            3: "3000",  # Music
            4: "4000",  # Games
            5: "4000",  # Software
            6: "5070",  # Anime
            7: "7000",  # Books
        }
        selected_idx = self._widgets["category_dropdown"].get_selected()
        category = category_map.get(selected_idx, "")

        # Start search
        self._widgets["search_button"].set_sensitive(False)
        self._widgets["search_button"].set_label(self._("Searching..."))
        self._widgets["search_status_label"].set_text(self._("Searching..."))
        self._view.store.remove_all()

        def search_thread() -> None:
            try:
                # Build search URL
                params = {
                    "apikey": api_key,
                    "q": query,
                    "t": "search",
                }
                if category:
                    params["cat"] = category

                url = f"{api_url}/api/v2.0/indexers/all/results/torznab/api?{urllib.parse.urlencode(params)}"

                req = urllib.request.Request(url)
                req.add_header("User-Agent", "DFakeSeeder/1.0")

                timeout = jackett_settings.get("timeout_seconds", 30)
                max_results = jackett_settings.get("max_results", 100)

                with urllib.request.urlopen(req, timeout=timeout) as response:
                    if response.status == 200:
                        xml_data = response.read().decode("utf-8")
                        results = self._parse_torznab_results(xml_data, max_results)
                        GLib.idle_add(self._display_search_results, results, None)
                    else:
                        GLib.idle_add(self._display_search_results, [], f"HTTP {response.status}")

            except urllib.error.HTTPError as e:
                GLib.idle_add(self._display_search_results, [], f"HTTP Error: {e.code}")
            except urllib.error.URLError as e:
                GLib.idle_add(self._display_search_results, [], f"Connection Error: {e.reason}")
            except _JACKETT_ERRORS as e:
                logger.error(
                    f"Jackett search error: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                GLib.idle_add(self._display_search_results, [], str(e))

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

    def _parse_torznab_results(self, xml_data: str, max_results: int) -> list[dict]:
        """Parse a Torznab XML response into a list of result dicts."""
        results: list[dict] = []
        try:
            ns = {
                "torznab": "http://torznab.com/schemas/2015/feed",
                "atom": "http://www.w3.org/2005/Atom",
            }
            root = ET.fromstring(xml_data)
            for item in root.findall(".//item")[:max_results]:
                parsed = self._parse_item(item, ns)
                if parsed is not None:
                    results.append(parsed)
        except ET.ParseError as e:
            logger.error(
                f"XML parse error: {e}",
                extra={"class_name": self.__class__.__name__},
            )
        return results

    def _parse_item(self, item: Any, ns: dict) -> dict | None:
        """Parse a single Torznab ``item`` element into a result dict, or None on error."""
        try:
            attrs = self._attr_values(item, ns)
            seeders, leechers = self._parse_peers(attrs)
            return {
                "title": item.findtext("title", ""),
                "size": self._parse_size(item, attrs),
                "seeders": seeders,
                "leechers": leechers,
                "category": item.findtext("category", ""),
                "indexer": attrs.get("jackettindexer") or item.findtext("source", "Unknown"),
                "download_url": item.findtext("link", ""),
                "magnet_url": attrs.get("magneturl", ""),
                "info_url": item.findtext("guid", "") or item.findtext("comments", ""),
                "publish_date": self._simplify_date(item.findtext("pubDate", "")),
            }
        except _JACKETT_ERRORS as e:
            logger.trace(
                f"Error parsing result item: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    @staticmethod
    def _attr_values(item: Any, ns: dict) -> dict:
        """Collect the torznab:attr name->value pairs on an item."""
        return {attr.get("name", ""): attr.get("value", "") for attr in item.findall("torznab:attr", ns)}

    @staticmethod
    def _parse_size(item: Any, attrs: dict) -> int:
        """Resolve a result's size from the torznab size attr or the enclosure length."""
        raw_size = attrs.get("size")
        if raw_size:
            return int(raw_size)
        enclosure = item.find("enclosure")
        if enclosure is not None:
            return int(enclosure.get("length", 0))
        return 0

    @staticmethod
    def _parse_peers(attrs: dict) -> tuple:
        """Resolve (seeders, leechers) from the torznab seeders/peers attrs."""
        seeders = int(attrs.get("seeders", 0) or 0)
        raw_peers = attrs.get("peers")
        leechers = max(0, int(raw_peers) - seeders) if raw_peers else 0
        return seeders, leechers

    @staticmethod
    def _simplify_date(pub_date: str) -> str:
        """Trim a pubDate string to its leading day/date tokens for display."""
        if not pub_date:
            return pub_date
        return " ".join(pub_date.split(" ")[0:3])

    def _display_search_results(self, results: list[dict], error: str | None) -> bool:
        """Display search results in the UI."""
        self._widgets["search_button"].set_sensitive(True)
        self._widgets["search_button"].set_label(self._("Search"))

        if error:
            self._widgets["search_status_label"].set_text(f"{self._('Error')}: {error}")
            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(
                    f"{self._('Search failed')}: {error}",
                    notification_type="error",
                )
            return False

        # Clear and populate results
        self._view.store.remove_all()

        for result in results:
            self._view.store.append(JackettSearchResult(result))

        count = len(results)
        self._widgets["search_status_label"].set_text(
            f"{count} {self._('result' if count == 1 else 'results')} {self._('found')}"
        )

        logger.info(
            f"Jackett search returned {count} results",
            extra={"class_name": self.__class__.__name__},
        )

        return False

    def _on_add_torrent(self, button: Gtk.Button, result: JackettSearchResult) -> None:
        """Add a torrent from search results."""
        download_url = result.get_property("download_url")
        magnet_url = result.get_property("magnet_url")
        title = result.get_property("title")

        if not download_url and not magnet_url:
            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(
                    self._("No download URL available for this torrent"),
                    notification_type="warning",
                )
            return

        # Prefer .torrent file URL over magnet
        url = download_url if download_url else magnet_url

        logger.info(
            f"Adding torrent from Jackett: {title}",
            extra={"class_name": self.__class__.__name__},
        )

        # Download and add in background
        def add_torrent_thread() -> None:
            try:
                if url.startswith("magnet:"):
                    # For magnet links, we would need magnet support
                    # For now, show a message
                    GLib.idle_add(
                        self._show_add_result,
                        False,
                        self._("Magnet links not yet supported. Use .torrent URL."),
                    )
                    return

                # Download the .torrent file
                jackett_settings = self.settings.get("jackett_settings", {})
                timeout = jackett_settings.get("timeout_seconds", 30)

                req = urllib.request.Request(url)
                req.add_header("User-Agent", "DFakeSeeder/1.0")

                with urllib.request.urlopen(req, timeout=timeout) as response:
                    torrent_data = response.read()

                # Save to torrents directory
                torrents_dir = os.path.join(get_config_dir(), "torrents")
                os.makedirs(torrents_dir, exist_ok=True)

                # Clean filename
                safe_title = "".join(c for c in title if c.isalnum() or c in " -_.").strip()[:100]
                filename = f"{safe_title}.torrent"
                filepath = os.path.join(torrents_dir, filename)

                # Avoid overwriting
                counter = 1
                while os.path.exists(filepath):
                    filename = f"{safe_title}_{counter}.torrent"
                    filepath = os.path.join(torrents_dir, filename)
                    counter += 1

                with open(filepath, "wb") as f:
                    f.write(torrent_data)

                # Add to model
                GLib.idle_add(self._add_torrent_to_model, filepath, title)

            except urllib.error.HTTPError as e:
                GLib.idle_add(self._show_add_result, False, f"HTTP Error: {e.code}")
            except urllib.error.URLError as e:
                GLib.idle_add(self._show_add_result, False, f"Connection Error: {e.reason}")
            except _JACKETT_ERRORS as e:
                logger.error(
                    f"Error adding torrent: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                GLib.idle_add(self._show_add_result, False, str(e))

        thread = threading.Thread(target=add_torrent_thread, daemon=True)
        thread.start()

    def _add_torrent_to_model(self, filepath: str, title: str) -> bool:
        """Add downloaded torrent to the model."""
        try:
            from d_fake_seeder.view import View

            if View.instance and hasattr(View.instance, "app"):
                controller = getattr(View.instance.app, "controller", None)
                if controller and hasattr(controller, "add_torrent"):
                    controller.add_torrent(filepath)
                    self._show_add_result(True, f"{self._('Added')}: {title}")
                    return False

            # Fallback: try to add via model directly
            if self.model and hasattr(self.model, "add_torrent"):
                self.model.add_torrent(filepath)
                self._show_add_result(True, f"{self._('Added')}: {title}")
            else:
                self._show_add_result(False, self._("Could not add torrent - controller not available"))

        except _JACKETT_ERRORS as e:
            logger.error(
                f"Error adding torrent to model: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self._show_add_result(False, str(e))

        return False

    def _show_add_result(self, success: bool, message: str) -> bool:
        """Show add torrent result notification."""
        from d_fake_seeder.view import View

        if View.instance:
            if success:
                View.instance.notify(message, notification_type="success")
            else:
                View.instance.notify(
                    f"{self._('Failed to add torrent')}: {message}",
                    notification_type="error",
                )

        return False

    def _on_settings_changed(self, source: Any, key: str, value: Any) -> None:
        """Handle settings changes."""
        if key.startswith("jackett_settings"):
            self._update_connection_status()
            # Update UI fields from settings
            jackett_settings = self.settings.get("jackett_settings", {})
            self._widgets["api_url_entry"].set_text(jackett_settings.get("api_url", "http://localhost:9117"))
            self._widgets["api_key_entry"].set_text(jackett_settings.get("api_key", ""))

    # === ABSTRACT METHOD IMPLEMENTATIONS ===

    def handle_model_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle model data changes (Jackett tab is independent of torrent model changes)."""

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle attribute changes (unused by the Jackett tab)."""

    def handle_settings_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle settings changes (updates flow via _on_settings_changed)."""

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update the view (Jackett tab is independent of torrent selection)."""
