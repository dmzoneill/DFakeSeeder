"""
Monitoring Tab - Real-time system metrics visualization.

Displays comprehensive metrics about the running application including
CPU, memory, file descriptors, network, threads, and more.
"""

# isort: skip_file

# fmt: off
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
    MetricsCollector = None

# fmt: on


class MonitoringTab(BaseTorrentTab):
    """
    Monitoring tab showing real-time system metrics.

    Displays:
    - CPU usage
    - Memory (RSS/USS/VMS)
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
        logger.debug(
            "🔧 MONITORING TAB: Starting initialization",
            extra={"class_name": self.__class__.__name__},
        )

        # Create main container as a scrolled window
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)

        # Create grid for tiles
        self.grid = Gtk.Grid()
        self.grid.set_row_spacing(12)
        self.grid.set_column_spacing(12)
        self.grid.set_margin_start(12)
        self.grid.set_margin_end(12)
        self.grid.set_margin_top(12)
        self.grid.set_margin_bottom(12)

        self.scrolled_window.set_child(self.grid)

        # Initialize metrics collector
        try:
            if MetricsCollector:
                logger.debug(
                    "🔧 MONITORING TAB: Creating MetricsCollector instance",
                    extra={"class_name": self.__class__.__name__},
                )
                self.metrics_collector = MetricsCollector()
                # Check if process was found
                if self.metrics_collector and self.metrics_collector.process:
                    logger.debug(
                        f"✅ MONITORING TAB: MetricsCollector found DFakeSeeder process "
                        f"(PID: {self.metrics_collector.process.pid})",
                        extra={"class_name": self.__class__.__name__},
                    )
                elif self.metrics_collector and not self.metrics_collector.process:
                    logger.debug(
                        "⚠️ MONITORING TAB: MetricsCollector initialized but no DFakeSeeder process found - will retry",
                        extra={"class_name": self.__class__.__name__},
                    )
            else:
                logger.debug(
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
            self.metrics_collector = None

        # Create metric tiles
        logger.debug(
            "🔧 MONITORING TAB: Creating 8 metric tiles "
            "(CPU, Memory, FD, Connections, Threads, Disk I/O, Network I/O, Torrents)",
            extra={"class_name": self.__class__.__name__},
        )
        self._create_metric_tiles()
        grid_children = (
            self.grid.observe_children().get_n_items() if hasattr(self.grid, "observe_children") else "unknown"
        )
        logger.debug(
            f"✅ MONITORING TAB: Created all metric tiles - grid has {grid_children} children",
            extra={"class_name": self.__class__.__name__},
        )

        # Start update timer (update every 2 seconds)
        self.update_timer = GLib.timeout_add_seconds(2, self._update_metrics)
        self.track_timeout(self.update_timer)
        logger.debug(
            "⏱️ MONITORING TAB: Started update timer (2 second interval)",
            extra={"class_name": self.__class__.__name__},
        )

        # Get the monitoring_tab container from the builder and add our scrolled window to it
        monitoring_container = self.builder.get_object("monitoring_tab")
        if monitoring_container:
            # Make sure widgets are visible
            self.scrolled_window.set_visible(True)
            self.grid.set_visible(True)

            monitoring_container.append(self.scrolled_window)
            self._tab_widget = monitoring_container
            logger.debug(
                "✅ MONITORING TAB: Added monitoring widgets to container",
                extra={"class_name": self.__class__.__name__},
            )
        else:
            # Fallback: just use the scrolled window directly
            self._tab_widget = self.scrolled_window
            logger.warning(
                "⚠️ MONITORING TAB: monitoring_tab container not found, using scrolled window directly",
                extra={"class_name": self.__class__.__name__},
            )

        logger.debug(
            "✅ MONITORING TAB: Initialization complete - monitoring tab is ready",
            extra={"class_name": self.__class__.__name__},
        )

    def _create_metric_tiles(self):
        """Create all metric visualization tiles in 4x2 layout."""
        # Row 0: CPU, Memory, File Descriptors, Network Connections
        self._create_cpu_tile(0, 0)
        self._create_memory_tile(0, 1)
        self._create_fd_tile(0, 2)
        self._create_connections_tile(0, 3)

        # Row 1: Threads, Disk I/O, Network I/O, Torrent Stats
        self._create_threads_tile(1, 0)
        self._create_disk_io_tile(1, 1)
        self._create_network_io_tile(1, 2)
        self._create_torrent_stats_tile(1, 3)

    def _create_metric_tile(self, row, col, title, graph_series):
        """
        Create a metric tile with graph and value labels.

        Args:
            row: Grid row position
            col: Grid column position
            title: Tile title
            graph_series: List of (series_name, color) tuples

        Returns:
            Dictionary with tile widgets
        """
        # Tile frame
        frame = Gtk.Frame()
        frame.set_css_classes(["metric-tile"])

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

        # Live graph
        graph = LiveGraph(max_samples=30, auto_scale=False, show_grid=True)
        graph.set_size_request(300, 100)

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
        self.grid.attach(frame, col, row, 1, 1)

        return {
            "frame": frame,
            "graph": graph,
            "value_labels": value_labels,
        }

    def _create_cpu_tile(self, row, col):
        """Create CPU usage tile."""
        self.cpu_tile = self._create_metric_tile(row, col, "CPU Usage", [("CPU %", (0.2, 0.8, 0.2))])  # Green

    def _create_memory_tile(self, row, col):
        """Create memory usage tile."""
        self.memory_tile = self._create_metric_tile(
            row,
            col,
            "Memory Usage",
            [
                ("RSS", (0.8, 0.2, 0.2)),  # Red
                ("USS", (0.2, 0.2, 0.8)),  # Blue
                ("VMS", (0.8, 0.6, 0.2)),  # Orange
            ],
        )
        # Memory uses auto-scale and MB units
        self.memory_tile["graph"].auto_scale = True

    def _create_fd_tile(self, row, col):
        """Create file descriptors tile."""
        self.fd_tile = self._create_metric_tile(
            row,
            col,
            "File Descriptors",
            [
                ("Total FDs", (0.6, 0.4, 0.8)),  # Purple
                ("Files", (0.2, 0.8, 0.8)),  # Cyan
                ("Sockets", (0.8, 0.8, 0.2)),  # Yellow
            ],
        )
        self.fd_tile["graph"].max_value = 200

    def _create_connections_tile(self, row, col):
        """Create network connections tile."""
        self.connections_tile = self._create_metric_tile(
            row,
            col,
            "Network Connections",
            [
                ("Total", (0.2, 0.8, 0.2)),  # Green
                ("Established", (0.2, 0.2, 0.8)),  # Blue
                ("Listen", (0.8, 0.2, 0.2)),  # Red
            ],
        )
        self.connections_tile["graph"].max_value = 50

    def _create_threads_tile(self, row, col):
        """Create threads count tile."""
        self.threads_tile = self._create_metric_tile(row, col, "Threads", [("Thread Count", (0.8, 0.4, 0.2))])  # Orange
        self.threads_tile["graph"].max_value = 100

    def _create_disk_io_tile(self, row, col):
        """Create disk I/O tile."""
        self.disk_io_tile = self._create_metric_tile(
            row,
            col,
            "Disk I/O (MB/s)",
            [
                ("Read", (0.2, 0.8, 0.2)),  # Green
                ("Write", (0.8, 0.2, 0.2)),  # Red
            ],
        )
        self.disk_io_tile["graph"].max_value = 10
        self.disk_io_last_read = 0
        self.disk_io_last_write = 0

    def _create_network_io_tile(self, row, col):
        """Create network I/O tile."""
        self.network_io_tile = self._create_metric_tile(
            row,
            col,
            "Network I/O (KB/s)",
            [
                ("Receiving", (0.2, 0.2, 0.8)),  # Blue
                ("Sending", (0.8, 0.6, 0.2)),  # Orange
            ],
        )
        self.network_io_tile["graph"].max_value = 100

    def _create_torrent_stats_tile(self, row, col):
        """Create torrent statistics tile."""
        self.torrent_tile = self._create_metric_tile(
            row,
            col,
            "Torrent Statistics",
            [
                ("Total Torrents", (0.6, 0.2, 0.8)),  # Purple
                ("Active Peers", (0.2, 0.8, 0.6)),  # Teal
            ],
        )
        self.torrent_tile["graph"].max_value = 20

    def _update_metrics(self):
        """Update all metrics from collector."""
        if not self.metrics_collector:
            logger.debug(
                "📊 MONITORING TAB: Update skipped - no metrics collector",
                extra={"class_name": self.__class__.__name__},
            )
            return True  # Keep timer running

        # Retry finding process if not found initially
        if not self.metrics_collector.process:
            logger.debug(
                "🔍 MONITORING TAB: Attempting to find DFakeSeeder process...",
                extra={"class_name": self.__class__.__name__},
            )
            try:
                self.metrics_collector._find_dfakeseeder_process()
                if self.metrics_collector.process:
                    logger.debug(
                        f"✅ MONITORING TAB: Found DFakeSeeder process (PID: {self.metrics_collector.process.pid})",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    logger.debug(
                        "🔍 MONITORING TAB: Process not found yet, will retry in 2 seconds",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return True  # Keep trying
            except Exception as e:
                logger.debug(
                    f"⚠️ MONITORING TAB: Error finding process: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                return True  # Keep trying

        try:
            metrics = self.metrics_collector.collect_metrics()

            # Log every 10th update to avoid spam
            if not hasattr(self, "_update_count"):
                self._update_count = 0
            self._update_count += 1

            if self._update_count % 10 == 0:
                logger.debug(
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
            self.memory_tile["graph"].update_series("VMS", vms_mb)

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

            # Calculate MB/s (2 second interval)
            read_rate = (io_read_bytes - self.disk_io_last_read) / (1024 * 1024 * 2)
            write_rate = (io_write_bytes - self.disk_io_last_write) / (1024 * 1024 * 2)

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

        return True  # Keep timer running

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

    def update_view(self, *args) -> None:
        """Update view (called by notebook)."""
        pass  # Updates happen via timer

    def model_selection_changed(self, *args) -> None:
        """Handle torrent selection change."""
        pass  # Monitoring tab doesn't depend on torrent selection

    def update_content(self, torrent) -> None:
        """
        Update tab content with torrent data.

        Args:
            torrent: Torrent object (not used - monitoring shows system-wide metrics)
        """
        # Store torrent reference if needed, but monitoring tab shows
        # system-wide metrics that are updated by timer, not per-torrent metrics
        self._current_torrent = torrent

    def get_widget(self):
        """Get the main widget for this tab."""
        return self._tab_widget
