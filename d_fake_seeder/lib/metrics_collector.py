#!/usr/bin/env python3
"""
DFakeSeeder Metrics Collector

Collects comprehensive system and application metrics for performance monitoring.
Tracks CPU, memory, file descriptors, connections, threads, and more.
"""

# fmt: off
import gc
import json
import logging
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

# fmt: on

# Setup logging (works both standalone and when imported)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class MetricsCollector:
    """Collects comprehensive metrics about the DFakeSeeder process."""

    def __init__(self, pid: Optional[int] = None):
        """
        Initialize metrics collector.

        Args:
            pid: Process ID to monitor (if None, finds dfakeseeder process)
        """
        self.pid = pid
        self.process: Optional[psutil.Process] = None
        self.baseline_metrics: Optional[Dict] = None
        self.start_time = time.time()

        self._initialize_process()

    def _initialize_process(self):
        """Initialize the process object."""
        try:
            if self.pid:
                self.process = psutil.Process(self.pid)
            else:
                # Find main dfakeseeder process (not tray, not monitoring tools)
                # Prefer Python processes over shell wrappers
                candidates = []

                for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                    try:
                        cmdline = proc.info.get("cmdline", [])
                        cmdline_str = " ".join(str(arg) for arg in cmdline).lower()

                        # Must contain dfakeseeder
                        if "dfakeseeder" not in cmdline_str:
                            continue

                        # Exclude tray app
                        if "dfakeseeder_tray" in cmdline_str or "tray" in cmdline_str:
                            continue

                        # Exclude monitoring tools
                        if "monitor" in cmdline_str or "metrics" in cmdline_str:
                            continue

                        # Add to candidates with priority
                        # Prefer python/python3 processes over shell wrappers
                        priority = 0
                        proc_name = proc.info.get("name", "").lower()
                        if "python" in proc_name:
                            priority = 10  # Highest priority for Python processes
                        elif proc_name in ["sh", "bash", "zsh"]:
                            priority = 1  # Low priority for shell wrappers

                        candidates.append((priority, proc))

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

                # Sort by priority (highest first) and pick the best candidate
                if candidates:
                    candidates.sort(key=lambda x: x[0], reverse=True)
                    self.process = candidates[0][1]
                    self.pid = self.process.pid
                    cmdline = self.process.cmdline()
                    logger.debug(f"Found DFakeSeeder main app: PID {self.pid}")
                    logger.debug(f"Process: {self.process.name()}")
                    logger.debug(f"Command: {' '.join(cmdline[:3])}")
                    if len(candidates) > 1:
                        logger.debug(f"Note: Found {len(candidates)} candidates, selected Python process")

            if self.process:
                logger.debug(f"Monitoring process: {self.process.name()} (PID: {self.pid})")
                # Capture baseline metrics
                self.baseline_metrics = self.collect_metrics()
            else:
                logger.debug("Warning: DFakeSeeder process not found")

        except Exception as e:
            logger.debug(f"Error initializing process: {e}")

    def collect_metrics(self) -> Dict:
        """
        Collect comprehensive metrics snapshot.

        Returns:
            Dictionary containing all metrics
        """
        if not self.process:
            return {
                "error": "Process not found",
                "timestamp": datetime.now().isoformat(),
            }

        try:
            metrics = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "pid": self.pid,
            }

            # CPU metrics
            metrics.update(self._collect_cpu_metrics())

            # Memory metrics
            metrics.update(self._collect_memory_metrics())

            # File descriptor metrics
            metrics.update(self._collect_fd_metrics())

            # Network connection metrics
            metrics.update(self._collect_connection_metrics())

            # Thread metrics
            metrics.update(self._collect_thread_metrics())

            # I/O metrics
            metrics.update(self._collect_io_metrics())

            # GTK/GObject metrics (if accessible)
            metrics.update(self._collect_gtk_metrics())

            # Python GC metrics
            metrics.update(self._collect_gc_metrics())

            return metrics

        except psutil.NoSuchProcess:
            return {
                "error": "Process terminated",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

    def _collect_cpu_metrics(self) -> Dict:
        """Collect CPU usage metrics."""
        try:
            cpu_times = self.process.cpu_times()
            cpu_percent = self.process.cpu_percent(interval=0.1)

            return {
                "cpu_percent": cpu_percent,
                "cpu_user_time": cpu_times.user,
                "cpu_system_time": cpu_times.system,
                "cpu_num_threads": self.process.num_threads(),
            }
        except Exception as e:
            return {"cpu_error": str(e)}

    def _collect_memory_metrics(self) -> Dict:
        """Collect memory usage metrics."""
        try:
            mem_info = self.process.memory_info()
            mem_percent = self.process.memory_percent()

            # Try to get USS (Unique Set Size) - most accurate for memory leaks
            try:
                mem_full = self.process.memory_full_info()
                uss = mem_full.uss
                pss = getattr(mem_full, "pss", None)
            except (AttributeError, psutil.AccessDenied):
                uss = None
                pss = None

            metrics = {
                "memory_rss_mb": mem_info.rss / (1024 * 1024),  # Resident Set Size
                "memory_vms_mb": mem_info.vms / (1024 * 1024),  # Virtual Memory Size
                "memory_percent": mem_percent,
                "memory_shared_mb": getattr(mem_info, "shared", 0) / (1024 * 1024),
            }

            if uss is not None:
                metrics["memory_uss_mb"] = uss / (1024 * 1024)  # Unique Set Size
            if pss is not None:
                metrics["memory_pss_mb"] = pss / (1024 * 1024)  # Proportional Set Size

            return metrics
        except Exception as e:
            return {"memory_error": str(e)}

    def _collect_fd_metrics(self) -> Dict:
        """Collect file descriptor metrics."""
        try:
            num_fds = self.process.num_fds()

            # Get FD types
            fd_types = Counter()
            try:
                for item in self.process.open_files():
                    fd_types["file"] += 1

                for conn in self.process.connections():
                    fd_types["socket"] += 1
            except (psutil.AccessDenied, AttributeError):
                pass

            # Get system FD limits
            try:
                with open("/proc/sys/fs/file-max", "r") as f:
                    system_fd_max = int(f.read().strip())
            except Exception:
                system_fd_max = None

            metrics = {
                "fd_count": num_fds,
                "fd_files": fd_types.get("file", 0),
                "fd_sockets": fd_types.get("socket", 0),
            }

            if system_fd_max:
                metrics["fd_system_max"] = system_fd_max

            return metrics
        except Exception as e:
            return {"fd_error": str(e)}

    def _collect_connection_metrics(self) -> Dict:
        """Collect network connection metrics."""
        try:
            connections = self.process.connections()

            conn_states = Counter()
            conn_types = Counter()
            local_ports = set()
            remote_ports = set()

            for conn in connections:
                conn_states[conn.status] += 1
                conn_types[str(conn.type)] += 1

                if conn.laddr:
                    local_ports.add(conn.laddr.port)
                if conn.raddr:
                    remote_ports.add(conn.raddr.port)

            return {
                "connections_total": len(connections),
                "connections_established": conn_states.get(psutil.CONN_ESTABLISHED, 0),
                "connections_listen": conn_states.get(psutil.CONN_LISTEN, 0),
                "connections_time_wait": conn_states.get(psutil.CONN_TIME_WAIT, 0),
                "connections_close_wait": conn_states.get(psutil.CONN_CLOSE_WAIT, 0),
                "connections_local_ports": len(local_ports),
                "connections_remote_ports": len(remote_ports),
                "connections_tcp": conn_types.get("1", 0),  # SOCK_STREAM = TCP
                "connections_udp": conn_types.get("2", 0),  # SOCK_DGRAM = UDP
            }
        except Exception as e:
            return {"connections_error": str(e)}

    def _collect_thread_metrics(self) -> Dict:
        """Collect thread metrics."""
        try:
            threads = self.process.threads()
            num_threads = len(threads)

            # Calculate total thread CPU time
            total_user_time = sum(t.user_time for t in threads)
            total_system_time = sum(t.system_time for t in threads)

            return {
                "threads_count": num_threads,
                "threads_user_time": total_user_time,
                "threads_system_time": total_system_time,
            }
        except Exception as e:
            return {"threads_error": str(e)}

    def _collect_io_metrics(self) -> Dict:
        """Collect I/O metrics."""
        try:
            io_counters = self.process.io_counters()

            return {
                "io_read_count": io_counters.read_count,
                "io_write_count": io_counters.write_count,
                "io_read_bytes": io_counters.read_bytes,
                "io_write_bytes": io_counters.write_bytes,
            }
        except Exception as e:
            return {"io_error": str(e)}

    def _collect_gtk_metrics(self) -> Dict:
        """Collect GTK/GObject metrics (if accessible)."""
        # This would require instrumenting the app itself
        # For now, return placeholder
        return {"gtk_note": "GTK metrics require app instrumentation"}

    def _collect_gc_metrics(self) -> Dict:
        """Collect Python garbage collector metrics."""
        try:
            # This requires access to the running Python process
            # We can try to get GC stats if we're in the same process
            metrics = {
                "gc_collections_gen0": gc.get_count()[0] if gc.get_count() else 0,
                "gc_collections_gen1": (gc.get_count()[1] if len(gc.get_count()) > 1 else 0),
                "gc_collections_gen2": (gc.get_count()[2] if len(gc.get_count()) > 2 else 0),
            }

            return metrics
        except Exception as e:
            return {"gc_error": str(e)}

    def get_metrics_delta(self, current: Dict, baseline: Dict = None) -> Dict:
        """
        Calculate delta between current and baseline metrics.

        Args:
            current: Current metrics
            baseline: Baseline metrics (uses stored baseline if None)

        Returns:
            Dictionary of deltas
        """
        if baseline is None:
            baseline = self.baseline_metrics

        if not baseline:
            return {}

        delta = {"timestamp": current["timestamp"]}

        numeric_keys = [
            "cpu_percent",
            "memory_rss_mb",
            "memory_vms_mb",
            "memory_uss_mb",
            "fd_count",
            "connections_total",
            "threads_count",
            "io_read_bytes",
            "io_write_bytes",
        ]

        for key in numeric_keys:
            if key in current and key in baseline:
                try:
                    delta[f"{key}_delta"] = current[key] - baseline[key]
                    delta[f"{key}_current"] = current[key]
                except (TypeError, KeyError):
                    pass

        return delta

    def is_healthy(self, metrics: Dict, thresholds: Dict = None) -> Tuple[bool, List[str]]:
        """
        Check if metrics indicate healthy operation.

        Args:
            metrics: Metrics to check
            thresholds: Custom thresholds (uses defaults if None)

        Returns:
            Tuple of (is_healthy, list_of_warnings)
        """
        if thresholds is None:
            thresholds = {
                "cpu_percent": 80.0,
                "memory_rss_mb": 1000.0,
                "memory_percent": 50.0,
                "fd_count": 1000,
                "connections_total": 500,
                "threads_count": 100,
            }

        warnings = []

        for key, threshold in thresholds.items():
            if key in metrics:
                value = metrics[key]
                if value > threshold:
                    warnings.append(f"{key} is {value:.2f}, exceeds threshold {threshold}")

        return len(warnings) == 0, warnings

    def format_metrics(self, metrics: Dict, include_delta: bool = True) -> str:
        """
        Format metrics as human-readable string.

        Args:
            metrics: Metrics dictionary
            include_delta: Include delta from baseline

        Returns:
            Formatted string
        """
        lines = []
        lines.append(f"=== Metrics at {metrics.get('timestamp', 'unknown')} ===")
        lines.append(f"Uptime: {metrics.get('uptime_seconds', 0):.1f}s")
        lines.append("")

        # CPU
        lines.append("CPU:")
        lines.append(f"  Usage: {metrics.get('cpu_percent', 0):.1f}%")
        lines.append(f"  User Time: {metrics.get('cpu_user_time', 0):.2f}s")
        lines.append(f"  System Time: {metrics.get('cpu_system_time', 0):.2f}s")
        lines.append("")

        # Memory
        lines.append("Memory:")
        lines.append(f"  RSS: {metrics.get('memory_rss_mb', 0):.2f} MB")
        lines.append(f"  VMS: {metrics.get('memory_vms_mb', 0):.2f} MB")
        if "memory_uss_mb" in metrics:
            lines.append(f"  USS: {metrics.get('memory_uss_mb', 0):.2f} MB")
        lines.append(f"  Percent: {metrics.get('memory_percent', 0):.2f}%")
        lines.append("")

        # File Descriptors
        lines.append("File Descriptors:")
        lines.append(f"  Total: {metrics.get('fd_count', 0)}")
        lines.append(f"  Files: {metrics.get('fd_files', 0)}")
        lines.append(f"  Sockets: {metrics.get('fd_sockets', 0)}")
        lines.append("")

        # Connections
        lines.append("Network Connections:")
        lines.append(f"  Total: {metrics.get('connections_total', 0)}")
        lines.append(f"  Established: {metrics.get('connections_established', 0)}")
        lines.append(f"  Listen: {metrics.get('connections_listen', 0)}")
        lines.append(f"  TCP: {metrics.get('connections_tcp', 0)}")
        lines.append(f"  UDP: {metrics.get('connections_udp', 0)}")
        lines.append("")

        # Threads
        lines.append("Threads:")
        lines.append(f"  Count: {metrics.get('threads_count', 0)}")
        lines.append("")

        # I/O
        lines.append("I/O:")
        lines.append(f"  Read: {metrics.get('io_read_bytes', 0) / (1024*1024):.2f} MB")
        lines.append(f"  Write: {metrics.get('io_write_bytes', 0) / (1024*1024):.2f} MB")
        lines.append("")

        # Delta from baseline
        if include_delta and self.baseline_metrics:
            delta = self.get_metrics_delta(metrics)
            if delta:
                lines.append("Delta from baseline:")
                for key, value in delta.items():
                    if key != "timestamp" and "_delta" in key:
                        lines.append(f"  {key}: {value:+.2f}")
                lines.append("")

        # Health check
        healthy, warnings = self.is_healthy(metrics)
        if not healthy:
            lines.append("⚠️  WARNINGS:")
            for warning in warnings:
                lines.append(f"  - {warning}")
        else:
            lines.append("✅ All metrics within healthy ranges")

        return "\n".join(lines)


if __name__ == "__main__":
    # Test the collector
    collector = MetricsCollector()

    if collector.process:
        print("\nCollecting metrics...")
        metrics = collector.collect_metrics()
        print(collector.format_metrics(metrics))

        # Save to file
        output_file = Path(__file__).parent / "test_metrics.json"
        with open(output_file, "w") as f:
            json.dump(metrics, f, indent=2)
        print(f"\nMetrics saved to: {output_file}")
    else:
        print("Could not find DFakeSeeder process. Is it running?")
