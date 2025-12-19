"""
Monitoring Tab - Real-time system metrics visualization.

Displays comprehensive metrics about the running application including
CPU, memory, file descriptors, network, threads, and more.
"""

# isort: skip_file

# fmt: off
from typing import Any
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk  # noqa: E402

from d_fake_seeder.components.component.torrent_details.base_tab import (  # noqa: E402
    BaseTorrentTab,
)
from d_fake_seeder.components.widgets.live_graph import LiveGraph  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402

try:
    from d_fake_seeder.lib.metrics_collector import MetricsCollector  # noqa: E402
except ImportError as e:
    logger.warning(
        f"MetricsCollector not available: {e}",
        extra={"class_name": "MonitoringTab"},
    )
    MetricsCollector = None  # type: ignore[assignment, misc]

# fmt: on


class MonitoringTab(BaseTorrentTab):
    """
    Monitoring tab showing real-time system metrics.

    Displays:
    - CPU usage
    - Memory (RSS/USS)
    - File descriptors
    - Network connections
    - Threads
    - Disk I/O
    - Network I/O
    - Torrent statistics
    """

    @property
    def tab_name(self) -> str:
        return "Monitoring"

    @property
    def tab_widget_id(self) -> str:
        return "monitoring_tab"

    def _init_widgets(self) -> None:
        """Initialize monitoring tab widgets."""
        logger.trace(
            "🔧 MONITORING TAB: Starting initialization",
            extra={"class_name": self.__class__.__name__},
        )

        # Get refresh interval from settings (default 2 seconds)
        self.refresh_interval = self.settings.get("ui_settings.monitoring_refresh_interval", 2) if self.settings else 2

        # Create main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.main_box.set_vexpand(True)
        # Don't set hexpand - let the container control horizontal sizing
        # self.main_box.set_hexpand(True)  # Removed to prevent width propagation

        # Create header bar with refresh interval slider
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        header_box.set_margin_start(12)
        header_box.set_margin_end(12)
        header_box.set_margin_top(6)

        # Refresh label
        refresh_label = Gtk.Label(label="Refresh Interval:")
        header_box.append(refresh_label)

        # Refresh slider (1-10 seconds)
        self.refresh_adjustment = Gtk.Adjustment(
            value=self.refresh_interval, lower=1, upper=10, step_increment=1, page_increment=1, page_size=0
        )
        self.refresh_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=self.refresh_adjustment)
        self.refresh_slider.set_digits(0)
        self.refresh_slider.set_draw_value(True)
        self.refresh_slider.set_value_pos(Gtk.PositionType.RIGHT)
        self.refresh_slider.set_hexpand(False)
        self.refresh_slider.set_size_request(150, -1)
        self.refresh_slider.connect("value-changed", self._on_refresh_interval_changed)
        header_box.append(self.refresh_slider)

        # Seconds label
        seconds_label = Gtk.Label(label="seconds")
        header_box.append(seconds_label)

        self.main_box.append(header_box)

        # Create main container as a scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        # Don't expand horizontally - prevents forcing window width
        self.scrolled_window.set_hexpand(False)
        # Allow horizontal scrolling if needed, but prefer shrinking
        self.scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # CRITICAL: Prevent natural width from propagating up and forcing window resize
        self.scrolled_window.set_propagate_natural_width(False)
        self.scrolled_window.set_propagate_natural_height(False)

        # Responsive layout configuration
        self.TILE_MIN_WIDTH = 250  # Minimum width per tile in pixels
        self.TILE_SPACING = 12  # Gap between tiles
        self.current_columns = 4  # Track current column count for change detection

        # Create FlowBox for responsive tile layout
        self.flowbox = Gtk.FlowBox()
        # Use homogeneous for uniform tile sizes
        self.flowbox.set_homogeneous(True)
        self.flowbox.set_row_spacing(self.TILE_SPACING)
        self.flowbox.set_column_spacing(self.TILE_SPACING)
        self.flowbox.set_margin_start(12)
        self.flowbox.set_margin_end(12)
        self.flowbox.set_margin_top(12)
        self.flowbox.set_margin_bottom(12)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_max_children_per_line(4)
        self.flowbox.set_min_children_per_line(2)
        self.flowbox.set_valign(Gtk.Align.START)

        # Add CSS class for animations
        self.flowbox.add_css_class("monitoring-flowbox")

        # Track tile frames for responsive adjustments
        self.tile_frames: list = []

        # Connect to size-allocate to dynamically adjust columns
        self.flowbox.connect("notify::allocation", self._on_flowbox_size_changed)

        self.scrolled_window.set_child(self.flowbox)
        self.main_box.append(self.scrolled_window)

        # Initialize metrics collector
        try:
            if MetricsCollector:  # type: ignore[truthy-function]
                logger.trace(
                    "🔧 MONITORING TAB: Creating MetricsCollector instance",
                    extra={"class_name": self.__class__.__name__},
                )
                self.metrics_collector = MetricsCollector()
                # Check if process was found
                if self.metrics_collector and self.metrics_collector.process:
                    logger.trace(
                        f"✅ MONITORING TAB: MetricsCollector found DFakeSeeder process "
                        f"(PID: {self.metrics_collector.process.pid})",
                        extra={"class_name": self.__class__.__name__},
                    )
                elif self.metrics_collector and not self.metrics_collector.process:
                    logger.trace(
                        "⚠️ MONITORING TAB: MetricsCollector initialized but no DFakeSeeder process found - will retry",
                        extra={"class_name": self.__class__.__name__},
                    )
            else:
                logger.trace(
                    "⚠️ MONITORING TAB: MetricsCollector class not available (import failed)",
                    extra={"class_name": self.__class__.__name__},
                )
                self.metrics_collector = None
        except Exception as e:
            logger.error(
                f"❌ MONITORING TAB: Failed to initialize MetricsCollector: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            self.metrics_collector = None  # type: ignore[assignment]

        # Create metric tiles
        logger.trace(
            "🔧 MONITORING TAB: Creating 8 metric tiles "
            "(CPU, Memory, FD, Connections, Threads, Disk I/O, Network I/O, Torrents)",
            extra={"class_name": self.__class__.__name__},
        )
        self._create_metric_tiles()
        tile_count = len(self.tile_frames)
        logger.trace(
            f"✅ MONITORING TAB: Created all metric tiles - flowbox has {tile_count} tiles",
            extra={"class_name": self.__class__.__name__},
        )

        # Start update timer using configured refresh interval
        self.update_timer = GLib.timeout_add_seconds(self.refresh_interval, self._update_metrics)
        self.track_timeout(self.update_timer)
        logger.trace(
            f"⏱️ MONITORING TAB: Started update timer ({self.refresh_interval} second interval)",
            extra={"class_name": self.__class__.__name__},
        )

        # Get the monitoring_tab container from the builder and add our main box to it
        monitoring_container = self.builder.get_object("monitoring_tab")
        if monitoring_container:
            # Make sure widgets are visible
            self.main_box.set_visible(True)
            self.scrolled_window.set_visible(True)
            self.flowbox.set_visible(True)

            monitoring_container.append(self.main_box)
            self._tab_widget = monitoring_container
            logger.trace(
                "✅ MONITORING TAB: Added monitoring widgets to container",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            # Fallback: just use the main box directly
            self._tab_widget = self.main_box
            logger.warning(
                "⚠️ MONITORING TAB: monitoring_tab container not found, using scrolled window directly",
                extra={"class_name": self.__class__.__name__},
            )

        logger.trace(
            "✅ MONITORING TAB: Initialization complete - monitoring tab is ready",
            extra={"class_name": self.__class__.__name__},
        )

    def _on_refresh_interval_changed(self, slider: Any) -> None:
        """Handle refresh interval slider change."""
        new_interval = int(slider.get_value())
        if new_interval != self.refresh_interval:
            self.refresh_interval = new_interval

            # Cancel existing timer
            if hasattr(self, "update_timer") and self.update_timer:
                GLib.source_remove(self.update_timer)

            # Start new timer with updated interval
            self.update_timer = GLib.timeout_add_seconds(self.refresh_interval, self._update_metrics)
            self.track_timeout(self.update_timer)

            # Save to settings using proper settings API
            if self.settings:
                self.settings.set("ui_settings.monitoring_refresh_interval", new_interval)

            logger.trace(
                f"⏱️ MONITORING TAB: Refresh interval changed to {new_interval} seconds",
                extra={"class_name": self.__class__.__name__},
            )

    def _create_metric_tiles(self) -> None:
        """Create all 8 metric visualization tiles (responsive layout: 4x2, 3x3, or 2x4)."""
        # Create tiles in order - FlowBox will handle layout
        self._create_cpu_tile()
        self._create_memory_tile()
        self._create_fd_tile()
        self._create_connections_tile()
        self._create_threads_tile()
        self._create_disk_io_tile()
        self._create_network_io_tile()
        self._create_torrent_stats_tile()

    def _on_flowbox_size_changed(self, flowbox: Any, param: Any) -> None:
        """Handle flowbox size changes to adjust column count."""
        allocation = flowbox.get_allocation()
        if allocation.width <= 0:
            return

        # Calculate available width (minus margins)
        available_width = allocation.width - 24  # 12px margin on each side

        # Calculate how many tiles can fit
        # Each tile needs TILE_MIN_WIDTH + spacing
        tile_with_spacing = self.TILE_MIN_WIDTH + self.TILE_SPACING
        possible_columns = max(2, available_width // tile_with_spacing)

        # Clamp to valid range (2-4 columns)
        new_columns = min(4, max(2, possible_columns))

        # Only update if changed (prevents unnecessary reflows)
        if new_columns != self.current_columns:
            self.current_columns = new_columns
            self.flowbox.set_max_children_per_line(new_columns)
            logger.trace(
                f"📐 MONITORING TAB: Responsive layout changed to {new_columns} columns "
                f"(width: {available_width}px)",
                extra={"class_name": self.__class__.__name__},
            )

    def _create_metric_tile(self, title: Any, graph_series: Any) -> Any:
        """
        Create a metric tile with graph and value labels.

        Args:
            title: Tile title
            graph_series: List of (series_name, color) tuples

        Returns:
            Dictionary with tile widgets
        """
        # Tile frame - constrain width to prevent forcing window size
        frame = Gtk.Frame()
        frame.set_css_classes(["metric-tile"])
        # Set minimum tile width
        frame.set_size_request(self.TILE_MIN_WIDTH, 150)
        # Allow tiles to expand to fill available space
        frame.set_hexpand(True)

        # Add CSS class for smooth transitions
        frame.add_css_class("monitoring-tile")

        # Vertical box for tile content
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)

        # Title label
        title_label = Gtk.Label()
        title_label.set_markup(f"<b>{title}</b>")
        title_label.set_xalign(0)
        vbox.append(title_label)

        # Live graph - DON'T expand horizontally to prevent forcing window size
        graph = LiveGraph(max_samples=30, auto_scale=False, show_grid=True)
        # Allow graph to expand within tile
        graph.set_size_request(-1, 60)  # Minimum height only
        graph.set_hexpand(True)  # Expand to fill tile width

        # Add series to graph
        for series_name, color in graph_series:
            graph.add_series(series_name, color)

        vbox.append(graph)

        # Value labels container
        values_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)

        # Create value labels for each series
        value_labels = {}
        for series_name, _ in graph_series:
            label = Gtk.Label()
            label.set_xalign(0)
            label.set_markup(f"<small>{series_name}: --</small>")
            values_box.append(label)
            value_labels[series_name] = label

        vbox.append(values_box)

        frame.set_child(vbox)

        # Add to flowbox (FlowBox requires FlowBoxChild wrapper)
        self.flowbox.append(frame)

        # Track frame for later reference
        self.tile_frames.append(frame)

        return {
            "frame": frame,
            "graph": graph,
            "value_labels": value_labels,
        }

    def _create_cpu_tile(self) -> None:
        """Create CPU usage tile."""
        self.cpu_tile = self._create_metric_tile("CPU Usage", [("CPU %", (0.2, 0.8, 0.2))])  # Green

    def _create_memory_tile(self) -> None:
        """Create memory usage tile."""
        self.memory_tile = self._create_metric_tile(
            "Memory Usage",
            [
                ("RSS", (0.8, 0.2, 0.2)),  # Red
                ("USS", (0.2, 0.2, 0.8)),  # Blue
            ],
        )
        # Memory uses auto-scale and MB units
        self.memory_tile["graph"].auto_scale = True

        # Add VMS as text-only label (not graphed - too large compared to RSS/USS)
        vms_label = Gtk.Label()
        vms_label.set_xalign(0)
        vms_label.set_markup("<small>VMS: --</small>")
        # Find the values_box and append the VMS label
        frame_child = self.memory_tile["frame"].get_child()
        if frame_child:
            # Get the last child (values_box)
            child = frame_child.get_first_child()
            while child:
                next_child = child.get_next_sibling()
                if next_child is None:
                    # This is the values_box
                    child.append(vms_label)
                    break
                child = next_child
        self.memory_tile["value_labels"]["VMS"] = vms_label

    def _create_fd_tile(self) -> None:
        """Create file descriptors tile."""
        self.fd_tile = self._create_metric_tile(
            "File Descriptors",
            [
                ("Total FDs", (0.6, 0.4, 0.8)),  # Purple
                ("Files", (0.2, 0.8, 0.8)),  # Cyan
                ("Sockets", (0.8, 0.8, 0.2)),  # Yellow
            ],
        )
        self.fd_tile["graph"].max_value = 200

    def _create_connections_tile(self) -> None:
        """Create network connections tile."""
        self.connections_tile = self._create_metric_tile(
            "Network Connections",
            [
                ("Total", (0.2, 0.8, 0.2)),  # Green
                ("Established", (0.2, 0.2, 0.8)),  # Blue
                ("Listen", (0.8, 0.2, 0.2)),  # Red
            ],
        )
        self.connections_tile["graph"].max_value = 50

    def _create_threads_tile(self) -> None:
        """Create threads count tile."""
        self.threads_tile = self._create_metric_tile("Threads", [("Thread Count", (0.8, 0.4, 0.2))])  # Orange
        self.threads_tile["graph"].max_value = 100

    def _create_disk_io_tile(self) -> None:
        """Create disk I/O tile."""
        self.disk_io_tile = self._create_metric_tile(
            "Disk I/O (MB/s)",
            [
                ("Read", (0.2, 0.8, 0.2)),  # Green
                ("Write", (0.8, 0.2, 0.2)),  # Red
            ],
        )
        self.disk_io_tile["graph"].max_value = 10
        self.disk_io_last_read = 0
        self.disk_io_last_write = 0

    def _create_network_io_tile(self) -> None:
        """Create network I/O tile."""
        self.network_io_tile = self._create_metric_tile(
            "Network I/O (KB/s)",
            [
                ("Receiving", (0.2, 0.2, 0.8)),  # Blue
                ("Sending", (0.8, 0.6, 0.2)),  # Orange
            ],
        )
        self.network_io_tile["graph"].max_value = 100
        self.net_io_last_recv = 0
        self.net_io_last_sent = 0

    def _create_torrent_stats_tile(self) -> None:
        """Create torrent statistics tile."""
        self.torrent_tile = self._create_metric_tile(
            "Torrent Statistics",
            [
                ("Total Torrents", (0.6, 0.2, 0.8)),  # Purple
                ("Active Peers", (0.2, 0.8, 0.6)),  # Teal
            ],
        )
        self.torrent_tile["graph"].max_value = 20

    def _update_metrics(self) -> Any:
        """Update all metrics from collector."""
        # Only update if the tab widget is visible (mapped)
        # This prevents layout recalculation when the tab is not shown
        if hasattr(self, "_tab_widget") and self._tab_widget:
            if not self._tab_widget.get_mapped():
                # Tab is not visible, skip update to prevent layout issues
                return True  # Keep timer running

        if not self.metrics_collector:
            logger.trace(
                "📊 MONITORING TAB: Update skipped - no metrics collector",
                extra={"class_name": self.__class__.__name__},
            )
            return True  # Keep timer running  # type: ignore

        # Retry initializing process if not found initially
        if not self.metrics_collector.process:
            logger.trace(
                "🔍 MONITORING TAB: Attempting to initialize process...",
                extra={"class_name": self.__class__.__name__},
            )
            try:
                self.metrics_collector._initialize_process()
                if self.metrics_collector.process:
                    logger.trace(
                        f"✅ MONITORING TAB: Initialized process (PID: {self.metrics_collector.process.pid})",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    logger.trace(
                        "🔍 MONITORING TAB: Process not initialized yet, will retry",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return True  # Keep trying  # type: ignore
            except Exception as e:
                logger.trace(
                    f"⚠️ MONITORING TAB: Error initializing process: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                return True  # Keep trying  # type: ignore

        try:
            metrics = self.metrics_collector.collect_metrics()

            # Log every 10th update to avoid spam
            if not hasattr(self, "_update_count"):
                self._update_count = 0
            self._update_count += 1

            if self._update_count % 10 == 0:
                logger.trace(
                    f"📊 MONITORING TAB: Metrics update #{self._update_count} - "
                    f"CPU: {metrics.get('cpu_percent', 0):.1f}%, "
                    f"RSS: {metrics.get('memory_rss_mb', 0):.1f}MB, "
                    f"FDs: {metrics.get('fd_count', 0)}, "
                    f"Conns: {metrics.get('connections_total', 0)}",
                    extra={"class_name": self.__class__.__name__},
                )

            # Update CPU tile
            cpu_percent = metrics.get("cpu_percent", 0)
            self.cpu_tile["graph"].update_series("CPU %", cpu_percent)
            self.cpu_tile["value_labels"]["CPU %"].set_markup(f"<small>CPU %: <b>{cpu_percent:.1f}%</b></small>")

            # Update Memory tile
            rss_mb = metrics.get("memory_rss_mb", 0)
            uss_mb = metrics.get("memory_uss_mb", 0)
            vms_mb = metrics.get("memory_vms_mb", 0)

            self.memory_tile["graph"].update_series("RSS", rss_mb)
            self.memory_tile["graph"].update_series("USS", uss_mb)
            # VMS is text-only (not graphed - too large compared to RSS/USS)

            self.memory_tile["value_labels"]["RSS"].set_markup(f"<small>RSS: <b>{rss_mb:.1f} MB</b></small>")
            self.memory_tile["value_labels"]["USS"].set_markup(f"<small>USS: <b>{uss_mb:.1f} MB</b></small>")
            self.memory_tile["value_labels"]["VMS"].set_markup(f"<small>VMS: <b>{vms_mb:.1f} MB</b></small>")

            # Update File Descriptors tile
            fd_count = metrics.get("fd_count", 0)
            fd_files = metrics.get("fd_files", 0)
            fd_sockets = metrics.get("fd_sockets", 0)

            self.fd_tile["graph"].update_series("Total FDs", fd_count)
            self.fd_tile["graph"].update_series("Files", fd_files)
            self.fd_tile["graph"].update_series("Sockets", fd_sockets)

            self.fd_tile["value_labels"]["Total FDs"].set_markup(f"<small>Total FDs: <b>{fd_count}</b></small>")
            self.fd_tile["value_labels"]["Files"].set_markup(f"<small>Files: <b>{fd_files}</b></small>")
            self.fd_tile["value_labels"]["Sockets"].set_markup(f"<small>Sockets: <b>{fd_sockets}</b></small>")

            # Update Network Connections tile
            conn_total = metrics.get("connections_total", 0)
            conn_established = metrics.get("connections_established", 0)
            conn_listen = metrics.get("connections_listen", 0)

            self.connections_tile["graph"].update_series("Total", conn_total)
            self.connections_tile["graph"].update_series("Established", conn_established)
            self.connections_tile["graph"].update_series("Listen", conn_listen)

            self.connections_tile["value_labels"]["Total"].set_markup(f"<small>Total: <b>{conn_total}</b></small>")
            self.connections_tile["value_labels"]["Established"].set_markup(
                f"<small>Established: <b>{conn_established}</b></small>"
            )
            self.connections_tile["value_labels"]["Listen"].set_markup(f"<small>Listen: <b>{conn_listen}</b></small>")

            # Update Threads tile
            thread_count = metrics.get("threads_count", 0)
            self.threads_tile["graph"].update_series("Thread Count", thread_count)
            self.threads_tile["value_labels"]["Thread Count"].set_markup(
                f"<small>Thread Count: <b>{thread_count}</b></small>"
            )

            # Update Disk I/O tile (calculate rate)
            io_read_bytes = metrics.get("io_read_bytes", 0)
            io_write_bytes = metrics.get("io_write_bytes", 0)

            # Calculate MB/s using actual refresh interval
            interval = self.refresh_interval if self.refresh_interval > 0 else 2
            read_rate = (io_read_bytes - self.disk_io_last_read) / (1024 * 1024 * interval)
            write_rate = (io_write_bytes - self.disk_io_last_write) / (1024 * 1024 * interval)

            self.disk_io_tile["graph"].update_series("Read", max(0, read_rate))
            self.disk_io_tile["graph"].update_series("Write", max(0, write_rate))

            self.disk_io_tile["value_labels"]["Read"].set_markup(
                f"<small>Read: <b>{max(0, read_rate):.2f} MB/s</b></small>"
            )
            self.disk_io_tile["value_labels"]["Write"].set_markup(
                f"<small>Write: <b>{max(0, write_rate):.2f} MB/s</b></small>"
            )

            self.disk_io_last_read = io_read_bytes
            self.disk_io_last_write = io_write_bytes

            # Update Network I/O tile (calculate rate)
            net_bytes_recv = metrics.get("net_bytes_recv", 0)
            net_bytes_sent = metrics.get("net_bytes_sent", 0)

            # Calculate KB/s using actual refresh interval
            interval = self.refresh_interval if self.refresh_interval > 0 else 2
            recv_rate = (net_bytes_recv - self.net_io_last_recv) / (1024 * interval)
            send_rate = (net_bytes_sent - self.net_io_last_sent) / (1024 * interval)

            self.network_io_tile["graph"].update_series("Receiving", max(0, recv_rate))
            self.network_io_tile["graph"].update_series("Sending", max(0, send_rate))

            self.network_io_tile["value_labels"]["Receiving"].set_markup(
                f"<small>Receiving: <b>{max(0, recv_rate):.1f} KB/s</b></small>"
            )
            self.network_io_tile["value_labels"]["Sending"].set_markup(
                f"<small>Sending: <b>{max(0, send_rate):.1f} KB/s</b></small>"
            )

            self.net_io_last_recv = net_bytes_recv
            self.net_io_last_sent = net_bytes_sent

            # Update Torrent Statistics tile
            if self.model:
                torrent_count = len(self.model.torrent_list) if hasattr(self.model, "torrent_list") else 0
                self.torrent_tile["graph"].update_series("Total Torrents", torrent_count)
                self.torrent_tile["value_labels"]["Total Torrents"].set_markup(
                    f"<small>Total Torrents: <b>{torrent_count}</b></small>"
                )

                # TODO: Get active peer count when available
                # For now use connection count as proxy
                active_peers = conn_established
                self.torrent_tile["graph"].update_series("Active Peers", active_peers)
                self.torrent_tile["value_labels"]["Active Peers"].set_markup(
                    f"<small>Active Peers: <b>{active_peers}</b></small>"
                )

        except Exception as e:
            logger.error(
                f"❌ MONITORING TAB: Error updating metrics: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

        return True  # Keep timer running  # type: ignore

    def _connect_signals(self) -> None:
        """Connect monitoring tab signals."""
        pass  # No signals needed for monitoring tab

    def _setup_ui_styling(self) -> None:
        """Setup CSS styling for monitoring tab."""
        pass  # Styling handled via CSS classes

    def _register_for_translation(self) -> None:
        """Register widgets for translation."""
        pass  # Monitoring tab uses English metric names

    def _show_empty_state(self) -> None:
        """Show empty state (monitoring tab always shows data)."""
        pass  # Always show metrics

    def update_view(self, *args: Any) -> None:
        """Update view (called by notebook)."""
        pass  # Updates happen via timer

    def model_selection_changed(self, *args: Any) -> None:
        """Handle torrent selection change."""
        pass  # Monitoring tab doesn't depend on torrent selection

    def update_content(self, torrent: Any) -> None:
        """
        Update tab content with torrent data.

        Args:
            torrent: Torrent object (not used - monitoring shows system-wide metrics)
        """
        # Store torrent reference if needed, but monitoring tab shows
        # system-wide metrics that are updated by timer, not per-torrent metrics
        self._current_torrent = torrent

    def get_widget(self) -> Any:  # type: ignore[override]
        """Get the main widget for this tab."""
        return self._tab_widget
