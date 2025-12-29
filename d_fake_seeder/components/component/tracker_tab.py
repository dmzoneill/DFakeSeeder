# fmt: off
# isort: skip_file
"""
Tracker Tab - Inbuilt BitTorrent Tracker management UI.

Displays tracker status, statistics, and tracked torrents.
"""

from typing import Any, Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gio, GLib, GObject, Gtk  # noqa: E402

from d_fake_seeder.components.component.base_component import Component  # noqa: E402
from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class TrackedTorrentItem(GObject.Object):
    """GObject wrapper for tracked torrent display."""

    __gtype_name__ = "TrackedTorrentItem"

    def __init__(
        self,
        info_hash: str,
        name: str,
        seeders: int,
        leechers: int,
        completed: int,
        last_activity: str,
        is_internal: bool,
        uploaded: str = "0 B",
        downloaded: str = "0 B",
        upload_speed: str = "0 B/s",
        download_speed: str = "0 B/s",
    ) -> None:
        super().__init__()
        self._info_hash = info_hash
        self._name = name
        self._seeders = seeders
        self._leechers = leechers
        self._completed = completed
        self._last_activity = last_activity
        self._is_internal = is_internal
        self._uploaded = uploaded
        self._downloaded = downloaded
        self._upload_speed = upload_speed
        self._download_speed = download_speed

    @GObject.Property(type=str)
    def info_hash(self) -> str:
        return self._info_hash

    @GObject.Property(type=str)
    def name(self) -> str:
        return self._name

    @GObject.Property(type=int)
    def seeders(self) -> int:
        return self._seeders

    @GObject.Property(type=int)
    def leechers(self) -> int:
        return self._leechers

    @GObject.Property(type=int)
    def completed(self) -> int:
        return self._completed

    @GObject.Property(type=str)
    def last_activity(self) -> str:
        return self._last_activity

    @GObject.Property(type=bool, default=False)
    def is_internal(self) -> bool:
        return self._is_internal

    @GObject.Property(type=str)
    def uploaded(self) -> str:
        return self._uploaded

    @GObject.Property(type=str)
    def downloaded(self) -> str:
        return self._downloaded

    @GObject.Property(type=str)
    def upload_speed(self) -> str:
        return self._upload_speed

    @GObject.Property(type=str)
    def download_speed(self) -> str:
        return self._download_speed


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

        # Tracker server reference
        self._tracker_server: Any = None
        self._update_timer_id: Optional[int] = None

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
        """Build the tracker tab UI."""
        # === HEADER SECTION ===
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_halign(Gtk.Align.FILL)

        # Title
        title_label = Gtk.Label(label=self._("Inbuilt BitTorrent Tracker"))
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.append(title_label)

        # Info label (points to settings)
        info_label = Gtk.Label(label=self._("Configure in Preferences → Tracker"))
        info_label.add_css_class("dim-label")
        info_label.set_halign(Gtk.Align.END)
        header_box.append(info_label)

        self.container.append(header_box)

        # === STATUS SECTION ===
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

        # Status row
        status_grid.attach(Gtk.Label(label=self._("Status:"), halign=Gtk.Align.END), 0, 0, 1, 1)
        self.status_label = Gtk.Label(label=self._("Stopped"))
        self.status_label.set_halign(Gtk.Align.START)
        self.status_label.add_css_class("dim-label")
        status_grid.attach(self.status_label, 1, 0, 1, 1)

        # Address row
        status_grid.attach(Gtk.Label(label=self._("Address:"), halign=Gtk.Align.END), 0, 1, 1, 1)
        self.address_label = Gtk.Label(label="-")
        self.address_label.set_halign(Gtk.Align.START)
        self.address_label.set_selectable(True)
        status_grid.attach(self.address_label, 1, 1, 1, 1)

        # Uptime row
        status_grid.attach(Gtk.Label(label=self._("Uptime:"), halign=Gtk.Align.END), 0, 2, 1, 1)
        self.uptime_label = Gtk.Label(label="-")
        self.uptime_label.set_halign(Gtk.Align.START)
        status_grid.attach(self.uptime_label, 1, 2, 1, 1)

        status_frame.set_child(status_grid)
        self.container.append(status_frame)

        # === STATISTICS SECTION ===
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

        # Torrents row
        stats_grid.attach(Gtk.Label(label=self._("Tracked Torrents:"), halign=Gtk.Align.END), 0, 0, 1, 1)
        self.torrents_label = Gtk.Label(label="0")
        self.torrents_label.set_halign(Gtk.Align.START)
        stats_grid.attach(self.torrents_label, 1, 0, 1, 1)

        # Internal torrents row
        stats_grid.attach(Gtk.Label(label=self._("Internal (DFakeSeeder):"), halign=Gtk.Align.END), 0, 1, 1, 1)
        self.internal_label = Gtk.Label(label="0")
        self.internal_label.set_halign(Gtk.Align.START)
        stats_grid.attach(self.internal_label, 1, 1, 1, 1)

        # Active peers row
        stats_grid.attach(Gtk.Label(label=self._("Active Peers:"), halign=Gtk.Align.END), 0, 2, 1, 1)
        self.peers_label = Gtk.Label(label="0")
        self.peers_label.set_halign(Gtk.Align.START)
        stats_grid.attach(self.peers_label, 1, 2, 1, 1)

        # Total announces row
        stats_grid.attach(Gtk.Label(label=self._("Total Announces:"), halign=Gtk.Align.END), 0, 3, 1, 1)
        self.announces_label = Gtk.Label(label="0")
        self.announces_label.set_halign(Gtk.Align.START)
        stats_grid.attach(self.announces_label, 1, 3, 1, 1)

        stats_frame.set_child(stats_grid)
        self.container.append(stats_frame)

        # === TORRENTS LIST SECTION ===
        torrents_frame = Gtk.Frame()
        torrents_frame.set_label(self._("Tracked Torrents"))
        torrents_frame.set_margin_top(8)
        torrents_frame.set_vexpand(True)

        # Create scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)

        # Create list store
        self.torrents_store = Gio.ListStore.new(TrackedTorrentItem)

        # Create selection model
        self.selection_model = Gtk.SingleSelection.new(self.torrents_store)

        # Create column view
        self.column_view = Gtk.ColumnView.new(self.selection_model)
        self.column_view.set_show_row_separators(True)
        self.column_view.set_show_column_separators(True)
        self.column_view.add_css_class("data-table")

        # Add columns
        self._add_column(self._("Source"), "is_internal", self._source_factory)
        self._add_column(self._("Name"), "name", self._text_factory)
        self._add_column(self._("Seeders"), "seeders", self._number_factory)
        self._add_column(self._("Leechers"), "leechers", self._number_factory)
        self._add_column(self._("Uploaded"), "uploaded", self._text_factory)
        self._add_column(self._("Downloaded"), "downloaded", self._text_factory)
        self._add_column(self._("Up Speed"), "upload_speed", self._text_factory)
        self._add_column(self._("Down Speed"), "download_speed", self._text_factory)
        self._add_column(self._("Completed"), "completed", self._number_factory)
        self._add_column(self._("Last Activity"), "last_activity", self._text_factory)

        scrolled.set_child(self.column_view)
        torrents_frame.set_child(scrolled)
        self.container.append(torrents_frame)

        # Load initial settings
        self._load_settings()

    def _add_column(
        self,
        title: str,
        property_name: str,
        factory_func: Any,
    ) -> None:
        """Add a column to the column view."""
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", lambda f, item: self._setup_cell(item))
        factory.connect("bind", lambda f, item: factory_func(item, property_name))

        column = Gtk.ColumnViewColumn.new(title, factory)
        column.set_resizable(True)
        self.column_view.append_column(column)

    def _setup_cell(self, item: Gtk.ListItem) -> None:
        """Setup a cell with a label."""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        label.set_margin_start(8)
        label.set_margin_end(8)
        item.set_child(label)

    def _source_factory(self, item: Gtk.ListItem, prop: str) -> None:
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

    def _text_factory(self, item: Gtk.ListItem, prop: str) -> None:
        """Factory for text columns."""
        label = item.get_child()
        obj = item.get_item()
        if obj and label:
            value = obj.get_property(prop)
            label.set_text(str(value) if value else "-")

    def _number_factory(self, item: Gtk.ListItem, prop: str) -> None:
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
            if enabled and not self._tracker_server:
                self._start_tracker()
            elif not enabled and self._tracker_server:
                self._stop_tracker()

        except Exception as e:
            logger.warning(
                f"Failed to load tracker settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_settings_changed(self, source: Any, key: str, value: Any) -> None:
        """Handle settings changes from preferences dialog."""
        if key == "tracker_settings.enabled":
            if value and not self._tracker_server:
                self._start_tracker()
            elif not value and self._tracker_server:
                self._stop_tracker()

    def _start_tracker(self) -> None:
        """Start the inbuilt tracker."""
        try:
            from d_fake_seeder.domain.tracker import TrackerServer

            tracker_settings = getattr(self.settings, "tracker_settings", {})

            # Get security settings
            security_settings = tracker_settings.get("security", {})

            self._tracker_server = TrackerServer(
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

            if self._tracker_server.start():
                logger.info(
                    f"Inbuilt tracker started at {self._tracker_server.announce_url}",
                    extra={"class_name": self.__class__.__name__},
                )
                self._update_status()

                # Register existing torrents with the tracker (sync_on_add missed them)
                self._register_existing_torrents()

                # Show notification
                from d_fake_seeder.view import View

                if View.instance:
                    View.instance.notify(
                        self._("Tracker started"),
                        notification_type="success",
                    )
            else:
                logger.error(
                    "Failed to start tracker",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Error starting tracker: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _stop_tracker(self) -> None:
        """Stop the inbuilt tracker."""
        try:
            if self._tracker_server:
                self._tracker_server.stop()
                self._tracker_server = None
                self._update_status()

                logger.info(
                    "Inbuilt tracker stopped",
                    extra={"class_name": self.__class__.__name__},
                )

                # Show notification
                from d_fake_seeder.view import View

                if View.instance:
                    View.instance.notify(
                        self._("Tracker stopped"),
                        notification_type="info",
                    )

        except Exception as e:
            logger.error(
                f"Error stopping tracker: {e}",
                extra={"class_name": self.__class__.__name__},
            )

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

            if not self._tracker_server or not self._tracker_server.is_running:
                return

            # Get model from view
            from d_fake_seeder.view import View

            if not View.instance or not hasattr(View.instance, "model"):
                return

            model = View.instance.model
            if not model or not hasattr(model, "torrent_list"):
                return

            registered_count = 0
            for torrent in model.torrent_list:
                try:
                    # Get info_hash from torrent (info_hash_bytes property)
                    info_hash = getattr(torrent, "info_hash_bytes", None)
                    if not info_hash:
                        continue

                    # info_hash_bytes should already be bytes, but handle strings just in case
                    if isinstance(info_hash, str):
                        info_hash = bytes.fromhex(info_hash)

                    # Register with tracker
                    self._tracker_server.register_torrent(
                        info_hash=info_hash,
                        name=getattr(torrent, "name", "Unknown"),
                        total_size=getattr(torrent, "total_size", 0),
                        is_internal=True,
                    )
                    registered_count += 1

                except Exception as e:
                    logger.trace(
                        f"Failed to register torrent {getattr(torrent, 'name', 'unknown')}: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

            logger.info(
                f"Registered {registered_count} existing torrents with inbuilt tracker",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Error registering existing torrents: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _start_update_timer(self) -> None:
        """Start the periodic update timer using the app's tickspeed setting."""
        if self._update_timer_id:
            GLib.source_remove(self._update_timer_id)

        # Use the same tickspeed as the main app for consistent refresh rates
        tick_speed = getattr(self.settings, "tickspeed", 9)
        self._update_timer_id = GLib.timeout_add_seconds(tick_speed, self._update_status)

    def _update_status(self) -> bool:
        """Update the status display."""
        try:
            from d_fake_seeder.domain.tracker import TrackerServer

            tracker = TrackerServer.get_instance()

            if tracker and tracker.is_running:
                stats = tracker.get_stats()

                self.status_label.set_text(self._("Running"))
                self.status_label.remove_css_class("dim-label")
                self.status_label.add_css_class("success")

                self.address_label.set_text(stats.get("announce_url", "-"))

                uptime = stats.get("uptime", 0)
                hours, remainder = divmod(int(uptime), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.uptime_label.set_text(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

                self.torrents_label.set_text(str(stats.get("total_torrents", 0)))
                self.internal_label.set_text(str(stats.get("internal_torrents", 0)))
                self.peers_label.set_text(str(stats.get("total_peers", 0)))
                # Total announces = internal announces sent via LocalAnnouncer
                self.announces_label.set_text(str(stats.get("announces_sent", 0)))

                # Update torrents list
                self._update_torrents_list(tracker)

            else:
                self.status_label.set_text(self._("Stopped"))
                self.status_label.remove_css_class("success")
                self.status_label.add_css_class("dim-label")

                self.address_label.set_text("-")
                self.uptime_label.set_text("-")
                self.torrents_label.set_text("0")
                self.internal_label.set_text("0")
                self.peers_label.set_text("0")
                self.announces_label.set_text("0")

                # Clear torrents list
                self.torrents_store.remove_all()

        except Exception as e:
            logger.warning(
                f"Failed to update tracker status: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        return True  # Keep timer running

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

    def _format_speed(self, bytes_per_sec: float) -> str:
        """Format speed to human readable string."""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"

    def _update_torrents_list(self, tracker: Any) -> None:
        """Update the tracked torrents list."""
        import time

        try:
            self.torrents_store.remove_all()

            # Get model to look up actual torrent data
            from d_fake_seeder.view import View

            model_torrents = {}
            if View.instance and hasattr(View.instance, "model") and View.instance.model:
                for t in View.instance.model.torrent_list:
                    info_hash = getattr(t, "info_hash_bytes", None)
                    if info_hash:
                        model_torrents[info_hash] = t

            # Initialize previous stats tracking if not exists
            if not hasattr(self, "_prev_stats"):
                self._prev_stats: dict = {}
            if not hasattr(self, "_last_update_time"):
                self._last_update_time: float = time.time()

            current_time = time.time()
            time_delta = current_time - self._last_update_time
            if time_delta < 0.1:
                time_delta = 1.0  # Avoid division by very small numbers

            for torrent in tracker.torrent_registry.get_all_torrents():
                # Format last activity
                elapsed = time.time() - torrent.last_announce
                if elapsed < 60:
                    last_activity = f"{int(elapsed)}s ago"
                elif elapsed < 3600:
                    last_activity = f"{int(elapsed / 60)}m ago"
                else:
                    last_activity = f"{int(elapsed / 3600)}h ago"

                # Get data from model torrent (includes real seeders/leechers from trackers)
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

                    # Calculate speeds from differentials
                    info_hash_hex = torrent.info_hash.hex()
                    if info_hash_hex in self._prev_stats:
                        prev = self._prev_stats[info_hash_hex]
                        upload_diff = uploaded - prev.get("uploaded", 0)
                        download_diff = downloaded - prev.get("downloaded", 0)
                        if upload_diff > 0:
                            upload_speed = upload_diff / time_delta
                        if download_diff > 0:
                            download_speed = download_diff / time_delta

                    # Store current stats for next calculation
                    self._prev_stats[info_hash_hex] = {
                        "uploaded": uploaded,
                        "downloaded": downloaded,
                    }

                item = TrackedTorrentItem(
                    info_hash=torrent.info_hash.hex()[:16] + "...",
                    name=torrent.name or torrent.info_hash.hex()[:16] + "...",
                    seeders=seeders,
                    leechers=leechers,
                    completed=torrent.times_completed,
                    last_activity=last_activity,
                    is_internal=torrent.is_internal,
                    uploaded=self._format_bytes(uploaded),
                    downloaded=self._format_bytes(downloaded),
                    upload_speed=self._format_speed(upload_speed),
                    download_speed=self._format_speed(download_speed),
                )
                self.torrents_store.append(item)

            self._last_update_time = current_time

        except Exception as e:
            logger.warning(
                f"Failed to update torrents list: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    # === ABSTRACT METHOD IMPLEMENTATIONS ===

    def handle_model_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle model data changes."""
        pass  # Tracker tab doesn't depend on torrent model changes

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle attribute changes."""
        pass  # Tracker tab doesn't depend on attribute changes

    def handle_settings_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        """Handle settings changes."""
        # Could reload tracker settings here if needed
        pass

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update the view."""
        # Tracker tab updates on its own timer
        pass

    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._update_timer_id:
            GLib.source_remove(self._update_timer_id)
            self._update_timer_id = None

        super().cleanup()
