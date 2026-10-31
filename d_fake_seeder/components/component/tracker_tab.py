"""
Tracker Tab - Inbuilt BitTorrent Tracker management UI.

Displays tracker status, statistics, and tracked torrents.
"""

import time
from types import SimpleNamespace
from typing import Any

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.gi_gtk4 import Gio, GLib, GObject, Gtk
from d_fake_seeder.lib.logger import logger

# Narrowed replacement for the previous broad ``except Exception`` clauses: the
# tracker start/stop/update paths touch settings, GLib timers, networking and
# optional imports, so these are the failures worth swallowing defensively.
_TRACKER_ERRORS = (AttributeError, TypeError, ValueError, KeyError, IndexError, OSError, GLib.Error)


class TrackedTorrentItem(GObject.Object):
    """GObject wrapper exposing a tracked torrent's display fields as bindable properties.

    The payload is a plain ``dict`` so the row carries its eleven display values
    without the wrapper itself accumulating that many instance attributes.
    """

    __gtype_name__ = "TrackedTorrentItem"

    def __init__(self, data: dict) -> None:
        super().__init__()
        self._data = data

    @GObject.Property(type=str)
    def info_hash(self) -> str:
        """Truncated info hash shown for the torrent."""
        return self._data["info_hash"]

    @GObject.Property(type=str)
    def name(self) -> str:
        """Display name of the torrent."""
        return self._data["name"]

    @GObject.Property(type=int)
    def seeders(self) -> int:
        """Number of seeders reported for the torrent."""
        return self._data["seeders"]

    @GObject.Property(type=int)
    def leechers(self) -> int:
        """Number of leechers reported for the torrent."""
        return self._data["leechers"]

    @GObject.Property(type=int)
    def completed(self) -> int:
        """Number of completed downloads recorded by the tracker."""
        return self._data["completed"]

    @GObject.Property(type=str)
    def last_activity(self) -> str:
        """Human-readable time since the last announce."""
        return self._data["last_activity"]

    @GObject.Property(type=bool, default=False)
    def is_internal(self) -> bool:
        """Whether the torrent is tracked internally by DFakeSeeder."""
        return self._data["is_internal"]

    @GObject.Property(type=str)
    def uploaded(self) -> str:
        """Formatted total uploaded bytes."""
        return self._data["uploaded"]

    @GObject.Property(type=str)
    def downloaded(self) -> str:
        """Formatted total downloaded bytes."""
        return self._data["downloaded"]

    @GObject.Property(type=str)
    def upload_speed(self) -> str:
        """Formatted upload speed."""
        return self._data["upload_speed"]

    @GObject.Property(type=str)
    def download_speed(self) -> str:
        """Formatted download speed."""
        return self._data["download_speed"]


class TrackerTab(Component):
    """
    Tracker tab showing inbuilt tracker status and management.

    Features:
    - Server on/off toggle
    - Status display (address, port, uptime)
    - Statistics (torrents, peers, announces)
    - Tracked torrents list
    """

    def __init__(self, builder: Any, model: Any) -> None:
        """Initialize the tracker tab."""
        super().__init__()

        logger.trace(
            "TrackerTab initializing",
            extra={"class_name": self.__class__.__name__},
        )

        self.builder = builder
        self.model = model
        self.settings = AppSettings.get_instance()

        # Display labels, list-view widgets and mutable runtime state are grouped
        # so the component stays within the instance-attribute limit.
        self._labels: dict[str, Any] = {}
        self._view = SimpleNamespace(store=None, selection=None, column=None)
        self._runtime = SimpleNamespace(
            server=None,
            timer_id=None,
            prev_stats={},
            last_update_time=time.time(),
        )

        # Get the tracker tab content container
        self.container = self.builder.get_object("tracker_tab_content")
        if not self.container:
            logger.error(
                "tracker_tab_content not found in builder",
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

        # Build UI
        self._build_ui()

        # Start update timer
        self._start_update_timer()

        logger.debug(
            "TrackerTab initialized",
            extra={"class_name": self.__class__.__name__},
        )

    def _(self, text: Any) -> Any:
        """Get translation function from model's TranslationManager."""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text

    def _build_ui(self) -> None:
        """Build the tracker tab UI from its component sections."""
        self._build_header_section()
        self._build_status_section()
        self._build_stats_section()
        self._build_torrents_section()

        # Load initial settings
        self._load_settings()

    def _build_header_section(self) -> None:
        """Build the title/info header row."""
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_halign(Gtk.Align.FILL)

        title_label = Gtk.Label(label=self._("Inbuilt BitTorrent Tracker"))
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.append(title_label)

        info_label = Gtk.Label(label=self._("Configure in Preferences → Tracker"))
        info_label.add_css_class("dim-label")
        info_label.set_halign(Gtk.Align.END)
        header_box.append(info_label)

        self.container.append(header_box)

    def _build_status_section(self) -> None:
        """Build the server-status frame (status/address/uptime)."""
        status_frame = Gtk.Frame()
        status_frame.set_label(self._("Server Status"))
        status_frame.set_margin_top(8)

        status_grid = Gtk.Grid()
        status_grid.set_row_spacing(8)
        status_grid.set_column_spacing(16)
        status_grid.set_margin_start(12)
        status_grid.set_margin_end(12)
        status_grid.set_margin_top(12)
        status_grid.set_margin_bottom(12)

        status_grid.attach(Gtk.Label(label=self._("Status:"), halign=Gtk.Align.END), 0, 0, 1, 1)
        status_label = Gtk.Label(label=self._("Stopped"))
        status_label.set_halign(Gtk.Align.START)
        status_label.add_css_class("dim-label")
        status_grid.attach(status_label, 1, 0, 1, 1)
        self._labels["status"] = status_label

        status_grid.attach(Gtk.Label(label=self._("Address:"), halign=Gtk.Align.END), 0, 1, 1, 1)
        address_label = Gtk.Label(label="-")
        address_label.set_halign(Gtk.Align.START)
        address_label.set_selectable(True)
        status_grid.attach(address_label, 1, 1, 1, 1)
        self._labels["address"] = address_label

        status_grid.attach(Gtk.Label(label=self._("Uptime:"), halign=Gtk.Align.END), 0, 2, 1, 1)
        uptime_label = Gtk.Label(label="-")
        uptime_label.set_halign(Gtk.Align.START)
        status_grid.attach(uptime_label, 1, 2, 1, 1)
        self._labels["uptime"] = uptime_label

        status_frame.set_child(status_grid)
        self.container.append(status_frame)

    def _build_stats_section(self) -> None:
        """Build the statistics frame (torrents/internal/peers/announces)."""
        stats_frame = Gtk.Frame()
        stats_frame.set_label(self._("Statistics"))
        stats_frame.set_margin_top(8)

        stats_grid = Gtk.Grid()
        stats_grid.set_row_spacing(8)
        stats_grid.set_column_spacing(16)
        stats_grid.set_margin_start(12)
        stats_grid.set_margin_end(12)
        stats_grid.set_margin_top(12)
        stats_grid.set_margin_bottom(12)

        rows = (
            ("torrents", self._("Tracked Torrents:"), "0"),
            ("internal", self._("Internal (DFakeSeeder):"), "0"),
            ("peers", self._("Active Peers:"), "0"),
            ("announces", self._("Total Announces:"), "0"),
        )
        for row, (key, caption, initial) in enumerate(rows):
            stats_grid.attach(Gtk.Label(label=caption, halign=Gtk.Align.END), 0, row, 1, 1)
            value_label = Gtk.Label(label=initial)
            value_label.set_halign(Gtk.Align.START)
            stats_grid.attach(value_label, 1, row, 1, 1)
            self._labels[key] = value_label

        stats_frame.set_child(stats_grid)
        self.container.append(stats_frame)

    def _build_torrents_section(self) -> None:
        """Build the tracked-torrents column view inside a scrolled frame."""
        torrents_frame = Gtk.Frame()
        torrents_frame.set_label(self._("Tracked Torrents"))
        torrents_frame.set_margin_top(8)
        torrents_frame.set_vexpand(True)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)

        self._view.store = Gio.ListStore.new(TrackedTorrentItem)
        self._view.selection = Gtk.SingleSelection.new(self._view.store)
        self._view.column = Gtk.ColumnView.new(self._view.selection)
        self._view.column.set_show_row_separators(True)
        self._view.column.set_show_column_separators(True)
        self._view.column.add_css_class("data-table")

        columns = (
            (self._("Source"), "is_internal", self._source_factory),
            (self._("Name"), "name", self._text_factory),
            (self._("Seeders"), "seeders", self._number_factory),
            (self._("Leechers"), "leechers", self._number_factory),
            (self._("Uploaded"), "uploaded", self._text_factory),
            (self._("Downloaded"), "downloaded", self._text_factory),
            (self._("Up Speed"), "upload_speed", self._text_factory),
            (self._("Down Speed"), "download_speed", self._text_factory),
            (self._("Completed"), "completed", self._number_factory),
            (self._("Last Activity"), "last_activity", self._text_factory),
        )
        for title, property_name, factory_func in columns:
            self._add_column(title, property_name, factory_func)

        scrolled.set_child(self._view.column)
        torrents_frame.set_child(scrolled)
        self.container.append(torrents_frame)

    def _add_column(self, title: str, property_name: str, factory_func: Any) -> None:
        """Add a column to the column view."""
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", lambda f, item: self._setup_cell(item))
        factory.connect("bind", lambda f, item: factory_func(item, property_name))

        column = Gtk.ColumnViewColumn.new(title, factory)
        column.set_resizable(True)
        self._view.column.append_column(column)

    def _setup_cell(self, item: Any) -> None:
        """Setup a cell with a label."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(8)
        label.set_margin_end(8)
        item.set_child(label)

    def _source_factory(self, item: Any, prop: str) -> None:
        """Factory for source column (internal/external icon)."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            is_internal = obj.get_property("is_internal")
            if is_internal:
                label.set_text("🏠 " + self._("Internal"))
                label.add_css_class("success")
            else:
                label.set_text("🌐 " + self._("External"))

    def _text_factory(self, item: Any, prop: str) -> None:
        """Factory for text columns."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            value = obj.get_property(prop)
            label.set_text(str(value) if value else "-")

    def _number_factory(self, item: Any, prop: str) -> None:
        """Factory for number columns."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            value = obj.get_property(prop)
            label.set_text(str(value))

    def _load_settings(self) -> None:
        """Load tracker settings and auto-start if enabled."""
        try:
            tracker_settings = getattr(self.settings, "tracker_settings", {})
            enabled = tracker_settings.get("enabled", False)

            # Connect to settings changes to react to enable/disable from preferences
            self.settings.connect("attribute-changed", self._on_settings_changed)

            # Auto-start if enabled
            if enabled and not self._runtime.server:
                self._start_tracker()
            elif not enabled and self._runtime.server:
                self._stop_tracker()

        except _TRACKER_ERRORS as e:
            logger.warning(
                f"Failed to load tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_settings_changed(self, source: Any, key: str, value: Any) -> None:
        """Handle settings changes from preferences dialog."""
        if key == "tracker_settings.enabled":
            if value and not self._runtime.server:
                self._start_tracker()
            elif not value and self._runtime.server:
                self._stop_tracker()

    def _start_tracker(self) -> None:
        """Start the inbuilt tracker."""
        try:
            from d_fake_seeder.domain.tracker import TrackerServer

            tracker_settings = getattr(self.settings, "tracker_settings", {})
            security_settings = tracker_settings.get("security", {})

            self._runtime.server = TrackerServer(
                bind_address=tracker_settings.get("bind_address", "0.0.0.0"),
                http_port=tracker_settings.get("http_port", 6969),
                udp_enabled=tracker_settings.get("udp_enabled", False),
                udp_port=tracker_settings.get("udp_port", 6969),
                announce_interval=tracker_settings.get("announce_interval_seconds", 1800),
                peer_timeout_multiplier=tracker_settings.get("peer_timeout_multiplier", 3),
                max_peers_per_announce=tracker_settings.get("max_peers_per_announce", 50),
                private_mode=tracker_settings.get("private_mode", False),
                enable_scrape=tracker_settings.get("enable_scrape", True),
                log_announces=tracker_settings.get("log_announces", False),
                ip_whitelist=security_settings.get("ip_whitelist", []) or None,
                ip_blacklist=security_settings.get("ip_blacklist", []) or None,
                rate_limit_per_minute=security_settings.get("rate_limit_per_minute", 60),
            )

            if self._runtime.server.start():
                logger.info(
                    f"Inbuilt tracker started at {self._runtime.server.announce_url}",
                    extra={"class_name": self.__class__.__name__},
                )
                self._update_status()

                # Register existing torrents with the tracker (sync_on_add missed them)
                self._register_existing_torrents()

                self._notify(self._("Tracker started"), "success")
            else:
                logger.error(
                    "Failed to start tracker",
                    extra={"class_name": self.__class__.__name__},
                )

        except _TRACKER_ERRORS as e:
            logger.error(
                f"Error starting tracker: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _stop_tracker(self) -> None:
        """Stop the inbuilt tracker."""
        try:
            if self._runtime.server:
                self._runtime.server.stop()
                self._runtime.server = None
                self._update_status()

                logger.info(
                    "Inbuilt tracker stopped",
                    extra={"class_name": self.__class__.__name__},
                )

                self._notify(self._("Tracker stopped"), "info")

        except _TRACKER_ERRORS as e:
            logger.error(
                f"Error stopping tracker: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    @staticmethod
    def _notify(message: str, notification_type: str) -> None:
        """Show a view notification when a view instance is available."""
        from d_fake_seeder.view import View

        if View.instance:
            View.instance.notify(message, notification_type=notification_type)

    def _register_existing_torrents(self) -> None:
        """Register all existing torrents with the inbuilt tracker.

        Called when tracker starts to sync torrents that were loaded
        before the tracker was enabled (sync_on_add missed them).
        """
        try:
            tracker_settings = getattr(self.settings, "tracker_settings", {})
            self_tracking = tracker_settings.get("self_tracking", {})

            if not self_tracking.get("enabled", True):
                logger.trace(
                    "Self-tracking disabled, skipping existing torrent registration",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            if not self._runtime.server or not self._runtime.server.is_running:
                return

            model = self._view_model()
            if model is None:
                return

            registered_count = 0
            for torrent in model.torrent_list:
                if self._register_one_torrent(torrent):
                    registered_count += 1

            logger.info(
                f"Registered {registered_count} existing torrents with inbuilt tracker",
                extra={"class_name": self.__class__.__name__},
            )

        except _TRACKER_ERRORS as e:
            logger.error(
                f"Error registering existing torrents: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _register_one_torrent(self, torrent: Any) -> bool:
        """Register a single torrent with the tracker; return whether it was registered."""
        try:
            info_hash = getattr(torrent, "info_hash_bytes", None)
            if not info_hash:
                return False

            # info_hash_bytes should already be bytes, but handle strings just in case
            if isinstance(info_hash, str):
                info_hash = bytes.fromhex(info_hash)

            self._runtime.server.register_torrent(
                info_hash=info_hash,
                name=getattr(torrent, "name", "Unknown"),
                total_size=getattr(torrent, "total_size", 0),
                is_internal=True,
            )
            return True

        except _TRACKER_ERRORS as e:
            logger.trace(
                f"Failed to register torrent {getattr(torrent, 'name', 'unknown')}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    @staticmethod
    def _view_model() -> Any:
        """Return the active model from the view singleton, or ``None``."""
        from d_fake_seeder.view import View

        if not View.instance or not hasattr(View.instance, "model"):
            return None
        model = View.instance.model
        if not model or not hasattr(model, "torrent_list"):
            return None
        return model

    def _start_update_timer(self) -> None:
        """Start the periodic update timer using the app's tickspeed setting."""
        if self._runtime.timer_id:
            GLib.source_remove(self._runtime.timer_id)

        # Use the same tickspeed as the main app for consistent refresh rates
        tick_speed = getattr(self.settings, "tickspeed", 9)
        self._runtime.timer_id = GLib.timeout_add_seconds(tick_speed, self._update_status)

    def _update_status(self) -> bool:
        """Update the status display."""
        try:
            from d_fake_seeder.domain.tracker import TrackerServer

            tracker = TrackerServer.get_instance()

            if tracker and tracker.is_running:
                self._apply_running_stats(tracker)
            else:
                self._apply_stopped_stats()

        except _TRACKER_ERRORS as e:
            logger.warning(
                f"Failed to update tracker status: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return True  # Keep timer running

    def _apply_running_stats(self, tracker: Any) -> None:
        """Populate the status/stats labels and list from a running tracker."""
        stats = tracker.get_stats()

        self._labels["status"].set_text(self._("Running"))
        self._labels["status"].remove_css_class("dim-label")
        self._labels["status"].add_css_class("success")

        self._labels["address"].set_text(stats.get("announce_url", "-"))

        uptime = stats.get("uptime", 0)
        hours, remainder = divmod(int(uptime), 3600)
        minutes, seconds = divmod(remainder, 60)
        self._labels["uptime"].set_text(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        self._labels["torrents"].set_text(str(stats.get("total_torrents", 0)))
        self._labels["internal"].set_text(str(stats.get("internal_torrents", 0)))
        self._labels["peers"].set_text(str(stats.get("total_peers", 0)))
        # Total announces = internal announces sent via LocalAnnouncer
        self._labels["announces"].set_text(str(stats.get("announces_sent", 0)))

        self._update_torrents_list(tracker)

    def _apply_stopped_stats(self) -> None:
        """Reset the status/stats labels and clear the list when stopped."""
        self._labels["status"].set_text(self._("Stopped"))
        self._labels["status"].remove_css_class("success")
        self._labels["status"].add_css_class("dim-label")

        self._labels["address"].set_text("-")
        self._labels["uptime"].set_text("-")
        for key in ("torrents", "internal", "peers", "announces"):
            self._labels[key].set_text("0")

        self._view.store.remove_all()

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

    @staticmethod
    def _format_speed(bytes_per_sec: float) -> str:
        """Format speed to human readable string."""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        if bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"

    @staticmethod
    def _format_last_activity(last_announce: float) -> str:
        """Format the elapsed time since a torrent's last announce."""
        elapsed = time.time() - last_announce
        if elapsed < 60:
            return f"{int(elapsed)}s ago"
        if elapsed < 3600:
            return f"{int(elapsed / 60)}m ago"
        return f"{int(elapsed / 3600)}h ago"

    @staticmethod
    def _collect_model_torrents() -> dict:
        """Map info-hash bytes to the matching model torrent for data lookups."""
        from d_fake_seeder.view import View

        model_torrents: dict = {}
        if View.instance and hasattr(View.instance, "model") and View.instance.model:
            for t in View.instance.model.torrent_list:
                info_hash = getattr(t, "info_hash_bytes", None)
                if info_hash:
                    model_torrents[info_hash] = t
        return model_torrents

    def _compute_speeds(self, info_hash_hex: str, uploaded: int, downloaded: int, time_delta: float) -> tuple:
        """Return (upload_speed, download_speed) from the stored differentials."""
        upload_speed = 0.0
        download_speed = 0.0
        prev = self._runtime.prev_stats.get(info_hash_hex)
        if prev:
            upload_diff = uploaded - prev.get("uploaded", 0)
            download_diff = downloaded - prev.get("downloaded", 0)
            if upload_diff > 0:
                upload_speed = upload_diff / time_delta
            if download_diff > 0:
                download_speed = download_diff / time_delta
        self._runtime.prev_stats[info_hash_hex] = {"uploaded": uploaded, "downloaded": downloaded}
        return upload_speed, download_speed

    def _make_tracked_item(self, torrent: Any, model_torrents: dict, time_delta: float) -> TrackedTorrentItem:
        """Build a :class:`TrackedTorrentItem` from a registry torrent and model data."""
        uploaded = 0
        downloaded = 0
        upload_speed = 0.0
        download_speed = 0.0
        seeders = 0
        leechers = 0

        model_torrent = model_torrents.get(torrent.info_hash)
        if model_torrent:
            uploaded = getattr(model_torrent, "total_uploaded", 0) or 0
            downloaded = getattr(model_torrent, "total_downloaded", 0) or 0
            # Get real seeders/leechers from external tracker announces
            seeders = getattr(model_torrent, "seeders", 0) or 0
            leechers = getattr(model_torrent, "leechers", 0) or 0
            upload_speed, download_speed = self._compute_speeds(
                torrent.info_hash.hex(), uploaded, downloaded, time_delta
            )

        short_hash = torrent.info_hash.hex()[:16] + "..."
        return TrackedTorrentItem(
            {
                "info_hash": short_hash,
                "name": torrent.name or short_hash,
                "seeders": seeders,
                "leechers": leechers,
                "completed": torrent.times_completed,
                "last_activity": self._format_last_activity(torrent.last_announce),
                "is_internal": torrent.is_internal,
                "uploaded": self._format_bytes(uploaded),
                "downloaded": self._format_bytes(downloaded),
                "upload_speed": self._format_speed(upload_speed),
                "download_speed": self._format_speed(download_speed),
            }
        )

    def _update_torrents_list(self, tracker: Any) -> None:
        """Update the tracked torrents list."""
        try:
            # Detach model to prevent O(n²) re-sort on each append
            self._view.column.set_model(None)
            self._view.store.remove_all()

            model_torrents = self._collect_model_torrents()

            current_time = time.time()
            time_delta = current_time - self._runtime.last_update_time
            if time_delta < 0.1:
                time_delta = 1.0  # Avoid division by very small numbers

            for torrent in tracker.torrent_registry.get_all_torrents():
                self._view.store.append(self._make_tracked_item(torrent, model_torrents, time_delta))

            self._runtime.last_update_time = current_time

        except _TRACKER_ERRORS as e:
            logger.warning(
                f"Failed to update torrents list: {e}",
                extra={"class_name": self.__class__.__name__},
            )
        finally:
            self._view.column.set_model(self._view.selection)

    # === ABSTRACT METHOD IMPLEMENTATIONS ===

    def handle_model_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle model data changes (tracker tab is independent of torrent model changes)."""

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle attribute changes (tracker tab is independent of attribute changes)."""

    def handle_settings_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle settings changes (tracker settings are reloaded via _on_settings_changed)."""

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update the view (tracker tab refreshes on its own timer)."""

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._runtime.timer_id:
            GLib.source_remove(self._runtime.timer_id)
            self._runtime.timer_id = None

        super().cleanup()
