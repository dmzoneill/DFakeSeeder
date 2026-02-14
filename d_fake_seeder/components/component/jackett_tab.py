# fmt: off
# isort: skip_file
"""
Jackett Tab - Torrent search integration via Jackett API.

Allows users to search for torrents using Jackett's Torznab API
and add results directly to DFakeSeeder.
"""

import os
import threading
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, Optional, List, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, GObject, Gtk  # noqa: E402

from d_fake_seeder.components.component.base_component import Component  # noqa: E402
from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.xdg_paths import get_config_dir  # noqa: E402

# fmt: on


class JackettSearchResult(GObject.Object):
    """GObject wrapper for Jackett search result display."""

    __gtype_name__ = "JackettSearchResult"

    def __init__(
        self,
        title: str,
        size: int,
        seeders: int,
        leechers: int,
        category: str,
        indexer: str,
        download_url: str,
        magnet_url: str,
        info_url: str,
        publish_date: str,
    ) -> None:
        super().__init__()
        self._title = title
        self._size = size
        self._size_str = self._format_bytes(size)
        self._seeders = seeders
        self._leechers = leechers
        self._category = category
        self._indexer = indexer
        self._download_url = download_url
        self._magnet_url = magnet_url
        self._info_url = info_url
        self._publish_date = publish_date

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human readable string."""
        if bytes_val < 1024:
            return f"{bytes_val} B"
        elif bytes_val < 1024 * 1024:
            return f"{bytes_val / 1024:.1f} KB"
        elif bytes_val < 1024 * 1024 * 1024:
            return f"{bytes_val / (1024 * 1024):.1f} MB"
        else:
            return f"{bytes_val / (1024 * 1024 * 1024):.2f} GB"

    @GObject.Property(type=str)
    def title(self) -> str:
        return self._title

    @GObject.Property(type=int)
    def size(self) -> int:
        return self._size

    @GObject.Property(type=str)
    def size_str(self) -> str:
        return self._size_str

    @GObject.Property(type=int)
    def seeders(self) -> int:
        return self._seeders

    @GObject.Property(type=int)
    def leechers(self) -> int:
        return self._leechers

    @GObject.Property(type=str)
    def category(self) -> str:
        return self._category

    @GObject.Property(type=str)
    def indexer(self) -> str:
        return self._indexer

    @GObject.Property(type=str)
    def download_url(self) -> str:
        return self._download_url

    @GObject.Property(type=str)
    def magnet_url(self) -> str:
        return self._magnet_url

    @GObject.Property(type=str)
    def info_url(self) -> str:
        return self._info_url

    @GObject.Property(type=str)
    def publish_date(self) -> str:
        return self._publish_date


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

        # Search state
        self._is_searching = False
        self._search_results: List[JackettSearchResult] = []

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
        """Build the Jackett tab UI."""
        # === HEADER SECTION ===
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_halign(Gtk.Align.FILL)

        # Title
        title_label = Gtk.Label(label=self._("Jackett Torrent Search"))
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.append(title_label)

        # Connection status indicator
        self.status_indicator = Gtk.Label(label="●")
        self.status_indicator.add_css_class("dim-label")
        self.status_indicator.set_halign(Gtk.Align.END)
        header_box.append(self.status_indicator)

        self.status_label = Gtk.Label(label=self._("Not Configured"))
        self.status_label.add_css_class("dim-label")
        self.status_label.set_halign(Gtk.Align.END)
        header_box.append(self.status_label)

        self.container.append(header_box)

        # === CONFIGURATION SECTION ===
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
        self.api_url_entry = Gtk.Entry()
        self.api_url_entry.set_hexpand(True)
        self.api_url_entry.set_placeholder_text("http://localhost:9117")
        jackett_settings = self.settings.get("jackett_settings", {})
        self.api_url_entry.set_text(jackett_settings.get("api_url", "http://localhost:9117"))
        self.api_url_entry.connect("changed", self._on_config_changed)
        config_grid.attach(self.api_url_entry, 1, 0, 2, 1)

        # API Key row
        config_grid.attach(Gtk.Label(label=self._("API Key:"), halign=Gtk.Align.END), 0, 1, 1, 1)
        self.api_key_entry = Gtk.Entry()
        self.api_key_entry.set_hexpand(True)
        self.api_key_entry.set_placeholder_text(self._("Enter your Jackett API key"))
        self.api_key_entry.set_visibility(False)  # Hide API key
        self.api_key_entry.set_text(jackett_settings.get("api_key", ""))
        self.api_key_entry.connect("changed", self._on_config_changed)
        config_grid.attach(self.api_key_entry, 1, 1, 1, 1)

        # Show/Hide API key button
        self.show_key_button = Gtk.Button()
        self.show_key_button.set_icon_name("view-reveal-symbolic")
        self.show_key_button.set_tooltip_text(self._("Show/Hide API Key"))
        self.show_key_button.connect("clicked", self._on_toggle_key_visibility)
        config_grid.attach(self.show_key_button, 2, 1, 1, 1)

        # Test connection button
        self.test_button = Gtk.Button(label=self._("Test Connection"))
        self.test_button.connect("clicked", self._on_test_connection)
        config_grid.attach(self.test_button, 0, 2, 1, 1)

        # Save config button
        self.save_config_button = Gtk.Button(label=self._("Save Configuration"))
        self.save_config_button.add_css_class("suggested-action")
        self.save_config_button.connect("clicked", self._on_save_config)
        config_grid.attach(self.save_config_button, 1, 2, 1, 1)

        config_frame.set_child(config_grid)
        self.container.append(config_frame)

        # === SEARCH SECTION ===
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

        self.search_entry = Gtk.Entry()
        self.search_entry.set_hexpand(True)
        self.search_entry.set_placeholder_text(self._("Enter search query..."))
        self.search_entry.connect("activate", self._on_search_activated)
        search_input_box.append(self.search_entry)

        # Category dropdown
        self.category_dropdown = Gtk.DropDown()
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
        self.category_dropdown.set_model(category_list)
        self.category_dropdown.set_selected(0)
        search_input_box.append(self.category_dropdown)

        # Search button
        self.search_button = Gtk.Button(label=self._("Search"))
        self.search_button.add_css_class("suggested-action")
        self.search_button.connect("clicked", self._on_search_clicked)
        search_input_box.append(self.search_button)

        search_box.append(search_input_box)

        # Search status label
        self.search_status_label = Gtk.Label(label="")
        self.search_status_label.set_halign(Gtk.Align.START)
        self.search_status_label.add_css_class("dim-label")
        search_box.append(self.search_status_label)

        search_frame.set_child(search_box)
        self.container.append(search_frame)

        # === RESULTS SECTION ===
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
        self.results_store = Gio.ListStore.new(JackettSearchResult)

        # Create selection model
        self.selection_model = Gtk.SingleSelection.new(self.results_store)

        # Create column view
        self.column_view = Gtk.ColumnView.new(self.selection_model)
        self.column_view.set_show_row_separators(True)
        self.column_view.set_show_column_separators(True)
        self.column_view.add_css_class("data-table")

        # Add columns
        self._add_column(self._("Title"), "title", self._title_factory, expand=True)
        self._add_column(self._("Size"), "size_str", self._text_factory)
        self._add_column(self._("S"), "seeders", self._seeders_factory)
        self._add_column(self._("L"), "leechers", self._leechers_factory)
        self._add_column(self._("Category"), "category", self._text_factory)
        self._add_column(self._("Indexer"), "indexer", self._text_factory)
        self._add_column(self._("Date"), "publish_date", self._text_factory)
        self._add_action_column()

        scrolled.set_child(self.column_view)
        results_frame.set_child(scrolled)
        self.container.append(results_frame)

        # Update status
        self._update_connection_status()

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
        self.column_view.append_column(column)

    def _add_action_column(self) -> None:
        """Add action column with download button."""
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._setup_action_cell)
        factory.connect("bind", self._bind_action_cell)

        column = Gtk.ColumnViewColumn.new(self._("Action"), factory)
        column.set_resizable(False)
        self.column_view.append_column(column)

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
            except Exception:
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
        visible = self.api_key_entry.get_visibility()
        self.api_key_entry.set_visibility(not visible)
        if visible:
            button.set_icon_name("view-reveal-symbolic")
        else:
            button.set_icon_name("view-conceal-symbolic")

    def _on_config_changed(self, entry: Gtk.Entry) -> None:
        """Handle config entry changes."""
        pass  # Just marks that config has been modified

    def _on_save_config(self, button: Gtk.Button) -> None:
        """Save Jackett configuration to settings."""
        try:
            api_url = self.api_url_entry.get_text().strip()
            api_key = self.api_key_entry.get_text().strip()

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

        except Exception as e:
            logger.error(
                f"Error saving Jackett config: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_test_connection(self, button: Gtk.Button) -> None:
        """Test connection to Jackett API."""
        self.test_button.set_sensitive(False)
        self.test_button.set_label(self._("Testing..."))

        def test_thread() -> None:
            try:
                api_url = self.api_url_entry.get_text().strip().rstrip("/")
                api_key = self.api_key_entry.get_text().strip()

                if not api_url or not api_key:
                    GLib.idle_add(self._show_test_result, False, self._("Missing API URL or Key"))
                    return

                # Test by fetching indexers
                url = f"{api_url}/api/v2.0/indexers/all/results/torznab/api?apikey={api_key}&t=caps"

                req = urllib.request.Request(url)
                req.add_header("User-Agent", "DFakeSeeder/1.0")

                with urllib.request.urlopen(req, timeout=10) as response:
                    if response.status == 200:
                        GLib.idle_add(self._show_test_result, True, self._("Connection successful!"))
                    else:
                        GLib.idle_add(self._show_test_result, False, f"HTTP {response.status}")

            except urllib.error.HTTPError as e:
                GLib.idle_add(self._show_test_result, False, f"HTTP Error: {e.code}")
            except urllib.error.URLError as e:
                GLib.idle_add(self._show_test_result, False, f"Connection Error: {e.reason}")
            except Exception as e:
                GLib.idle_add(self._show_test_result, False, str(e))

        thread = threading.Thread(target=test_thread, daemon=True)
        thread.start()

    def _show_test_result(self, success: bool, message: str) -> bool:
        """Show test connection result."""
        self.test_button.set_sensitive(True)
        self.test_button.set_label(self._("Test Connection"))

        from d_fake_seeder.view import View

        if View.instance:
            if success:
                View.instance.notify(message, notification_type="success")
                self._update_connection_status(connected=True)
            else:
                View.instance.notify(f"{self._('Connection failed')}: {message}", notification_type="error")
                self._update_connection_status(connected=False)

        return False

    def _update_connection_status(self, connected: Optional[bool] = None) -> None:
        """Update connection status indicator."""
        jackett_settings = self.settings.get("jackett_settings", {})
        api_key = jackett_settings.get("api_key", "")

        if connected is True:
            self.status_indicator.set_text("●")
            self.status_indicator.remove_css_class("dim-label")
            self.status_indicator.remove_css_class("error")
            self.status_indicator.add_css_class("success")
            self.status_label.set_text(self._("Connected"))
            self.status_label.remove_css_class("dim-label")
            self.status_label.add_css_class("success")
        elif connected is False:
            self.status_indicator.set_text("●")
            self.status_indicator.remove_css_class("dim-label")
            self.status_indicator.remove_css_class("success")
            self.status_indicator.add_css_class("error")
            self.status_label.set_text(self._("Connection Failed"))
            self.status_label.remove_css_class("dim-label")
            self.status_label.add_css_class("error")
        elif api_key:
            self.status_indicator.set_text("●")
            self.status_indicator.remove_css_class("success")
            self.status_indicator.remove_css_class("error")
            self.status_indicator.add_css_class("dim-label")
            self.status_label.set_text(self._("Configured"))
            self.status_label.add_css_class("dim-label")
        else:
            self.status_indicator.set_text("●")
            self.status_indicator.remove_css_class("success")
            self.status_indicator.remove_css_class("error")
            self.status_indicator.add_css_class("dim-label")
            self.status_label.set_text(self._("Not Configured"))
            self.status_label.add_css_class("dim-label")

    def _on_search_activated(self, entry: Gtk.Entry) -> None:
        """Handle Enter key in search entry."""
        self._on_search_clicked(None)

    def _on_search_clicked(self, button: Optional[Gtk.Button]) -> None:
        """Perform search via Jackett API."""
        query = self.search_entry.get_text().strip()
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
        selected_idx = self.category_dropdown.get_selected()
        category = category_map.get(selected_idx, "")

        # Start search
        self._is_searching = True
        self.search_button.set_sensitive(False)
        self.search_button.set_label(self._("Searching..."))
        self.search_status_label.set_text(self._("Searching..."))
        self.results_store.remove_all()

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
            except Exception as e:
                logger.error(
                    f"Jackett search error: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                GLib.idle_add(self._display_search_results, [], str(e))

        thread = threading.Thread(target=search_thread, daemon=True)
        thread.start()

    def _parse_torznab_results(self, xml_data: str, max_results: int) -> List[Dict]:
        """Parse Torznab XML response."""
        results = []
        try:
            # Torznab namespace
            ns = {
                "torznab": "http://torznab.com/schemas/2015/feed",
                "atom": "http://www.w3.org/2005/Atom",
            }

            root = ET.fromstring(xml_data)

            # Find all items
            items = root.findall(".//item")

            for item in items[:max_results]:
                try:
                    title = item.findtext("title", "")

                    # Get size from torznab:attr or enclosure
                    size = 0
                    for attr in item.findall("torznab:attr", ns):
                        if attr.get("name") == "size":
                            size = int(attr.get("value", 0))
                            break

                    if not size:
                        enclosure = item.find("enclosure")
                        if enclosure is not None:
                            size = int(enclosure.get("length", 0))

                    # Get seeders and leechers
                    seeders = 0
                    leechers = 0
                    for attr in item.findall("torznab:attr", ns):
                        name = attr.get("name", "")
                        value = attr.get("value", "0")
                        if name == "seeders":
                            seeders = int(value)
                        elif name == "peers":
                            leechers = max(0, int(value) - seeders)

                    # Get category
                    category = item.findtext("category", "")

                    # Get indexer (from jackettindexer or source)
                    indexer = ""
                    for attr in item.findall("torznab:attr", ns):
                        if attr.get("name") == "jackettindexer":
                            indexer = attr.get("value", "")
                            break
                    if not indexer:
                        indexer = item.findtext("source", "Unknown")

                    # Get download URL
                    download_url = item.findtext("link", "")

                    # Get magnet URL
                    magnet_url = ""
                    for attr in item.findall("torznab:attr", ns):
                        if attr.get("name") == "magneturl":
                            magnet_url = attr.get("value", "")
                            break

                    # Get info URL
                    info_url = item.findtext("guid", "") or item.findtext("comments", "")

                    # Get publish date
                    pub_date = item.findtext("pubDate", "")
                    # Simplify date display
                    if pub_date:
                        try:
                            # Try to extract just date part
                            date_parts = pub_date.split(" ")[0:3]
                            pub_date = " ".join(date_parts)
                        except Exception:
                            pass

                    results.append(
                        {
                            "title": title,
                            "size": size,
                            "seeders": seeders,
                            "leechers": leechers,
                            "category": category,
                            "indexer": indexer,
                            "download_url": download_url,
                            "magnet_url": magnet_url,
                            "info_url": info_url,
                            "publish_date": pub_date,
                        }
                    )

                except Exception as e:
                    logger.trace(
                        f"Error parsing result item: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    continue

        except ET.ParseError as e:
            logger.error(
                f"XML parse error: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return results

    def _display_search_results(self, results: List[Dict], error: Optional[str]) -> bool:
        """Display search results in the UI."""
        self._is_searching = False
        self.search_button.set_sensitive(True)
        self.search_button.set_label(self._("Search"))

        if error:
            self.search_status_label.set_text(f"{self._('Error')}: {error}")
            from d_fake_seeder.view import View

            if View.instance:
                View.instance.notify(
                    f"{self._('Search failed')}: {error}",
                    notification_type="error",
                )
            return False

        # Clear and populate results
        self.results_store.remove_all()

        for result in results:
            item = JackettSearchResult(
                title=result["title"],
                size=result["size"],
                seeders=result["seeders"],
                leechers=result["leechers"],
                category=result["category"],
                indexer=result["indexer"],
                download_url=result["download_url"],
                magnet_url=result["magnet_url"],
                info_url=result["info_url"],
                publish_date=result["publish_date"],
            )
            self.results_store.append(item)

        count = len(results)
        self.search_status_label.set_text(f"{count} {self._('result' if count == 1 else 'results')} {self._('found')}")

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
                        self._show_add_result, False, self._("Magnet links not yet supported. Use .torrent URL.")
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
            except Exception as e:
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

        except Exception as e:
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
                View.instance.notify(f"{self._('Failed to add torrent')}: {message}", notification_type="error")

        return False

    def _on_settings_changed(self, source: Any, key: str, value: Any) -> None:
        """Handle settings changes."""
        if key.startswith("jackett_settings"):
            self._update_connection_status()
            # Update UI fields from settings
            jackett_settings = self.settings.get("jackett_settings", {})
            self.api_url_entry.set_text(jackett_settings.get("api_url", "http://localhost:9117"))
            self.api_key_entry.set_text(jackett_settings.get("api_key", ""))

    # === ABSTRACT METHOD IMPLEMENTATIONS ===

    def handle_model_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle model data changes."""
        pass  # Jackett tab doesn't depend on torrent model changes

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle attribute changes."""
        pass

    def handle_settings_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle settings changes."""
        pass

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update the view."""
        pass  # Jackett tab is independent of torrent selection

    def cleanup(self) -> None:
        """Cleanup resources."""
        super().cleanup()
