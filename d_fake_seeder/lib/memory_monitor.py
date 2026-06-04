"""
Memory Monitor for DFakeSeeder.

Periodically snapshots memory usage using tracemalloc and psutil,
and inspects key objects for unbounded growth. Logs results via the app logger.

Usage: Start early in Controller.__init__() with:
    from d_fake_seeder.lib.memory_monitor import MemoryMonitor
    self.memory_monitor = MemoryMonitor(controller=self)
    self.memory_monitor.start()

Set DFS_MEMORY_DEEP=1 for expensive gc.get_objects() scans and higher
tracemalloc frame depth (useful for chasing specific leaks but slows the app).
"""

import gc
import os
import sys
import threading
import time
import tracemalloc
from typing import Any, Dict, List, Optional, Tuple


class MemoryMonitor:
    """Monitors memory usage and reports on potential leaks."""

    def __init__(
        self,
        controller: Any = None,
        interval_seconds: int = 30,
        top_n: int = 20,
    ) -> None:
        self.controller = controller
        self.interval = interval_seconds
        self.top_n = top_n
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._process: Any = None
        self._snapshots: List[Dict[str, Any]] = []
        self._tick = 0

        self._deep_mode = os.environ.get("DFS_MEMORY_DEEP", "") == "1"
        self._use_tracemalloc = self._deep_mode
        self._tracemalloc_frames = 10 if self._deep_mode else 1
        self._startup_delay = 15 if self._deep_mode else 60
        self._deep_scan_interval = 1 if self._deep_mode else 5

    def start(self) -> None:
        """Start tracemalloc (deferred) and the monitoring thread."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="MemoryMonitor")
        self._thread.start()

    def stop(self) -> None:
        """Stop the monitoring thread and tracemalloc."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        if tracemalloc.is_tracing():
            tracemalloc.stop()

    def _run(self) -> None:
        """Main monitoring loop."""
        self._stop_event.wait(self._startup_delay)
        if self._stop_event.is_set():
            return

        try:
            import psutil

            self._process = psutil.Process(os.getpid())
        except ImportError:
            self._process = None

        if self._use_tracemalloc:
            tracemalloc.start(self._tracemalloc_frames)

        while not self._stop_event.is_set():
            try:
                self._tick += 1
                report = self._collect_report()
                self._snapshots.append(report)
                self._print_report(report)
            except Exception as e:
                print(f"[MemoryMonitor] Error: {e}", file=sys.stderr)

            self._stop_event.wait(self.interval)

    def _collect_report(self) -> Dict[str, Any]:
        """Collect a full memory report."""
        report: Dict[str, Any] = {
            "tick": self._tick,
            "timestamp": time.time(),
        }

        if self._process:
            mem = self._process.memory_info()
            report["rss_mb"] = mem.rss / (1024 * 1024)
            report["vms_mb"] = mem.vms / (1024 * 1024)
        else:
            report["rss_mb"] = 0.0
            report["vms_mb"] = 0.0

        if tracemalloc.is_tracing():
            snapshot = tracemalloc.take_snapshot()
            snapshot = snapshot.filter_traces(
                [
                    tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
                    tracemalloc.Filter(False, "<frozen importlib._bootstrap_external>"),
                    tracemalloc.Filter(False, "<unknown>"),
                ]
            )
            report["top_allocs"] = snapshot.statistics("lineno", cumulative=False)[: self.top_n]
            report["top_files"] = snapshot.statistics("filename")[: self.top_n]

            traced_current, traced_peak = tracemalloc.get_traced_memory()
            report["traced_current_mb"] = traced_current / (1024 * 1024)
            report["traced_peak_mb"] = traced_peak / (1024 * 1024)
        else:
            report["top_allocs"] = []
            report["top_files"] = []
            report["traced_current_mb"] = 0.0
            report["traced_peak_mb"] = 0.0

        report["suspect_objects"] = self._inspect_controller_objects()

        do_deep_scan = self._tick % self._deep_scan_interval == 0
        if do_deep_scan:
            report["suspect_objects"].extend(self._inspect_large_containers())

        report["gc_counts"] = gc.get_count()

        return report

    def _inspect_controller_objects(self) -> List[Dict[str, Any]]:
        """Inspect objects reachable from the controller (cheap targeted scan)."""
        results: List[Dict[str, Any]] = []
        if not self.controller:
            return results

        model = getattr(self.controller, "model", None)
        if model:
            tlist = getattr(model, "torrent_list", None)
            if tlist:
                results.append(
                    {
                        "name": "model.torrent_list",
                        "type": type(tlist).__name__,
                        "size": len(tlist) if hasattr(tlist, "__len__") else "?",
                    }
                )

            torrents = getattr(model, "torrents", None) or []
            for i, t in enumerate(torrents[:5]):
                seeder = getattr(t, "seeder", None)
                if seeder:
                    for attr_name in ("peer_data", "info", "peers"):
                        obj = getattr(seeder, attr_name, None)
                        if obj and hasattr(obj, "__len__"):
                            results.append(
                                {
                                    "name": f"torrent[{i}].seeder.{attr_name}",
                                    "type": type(obj).__name__,
                                    "size": len(obj),
                                }
                            )

                seeders = getattr(t, "seeders", None)
                if seeders:
                    for j, s in enumerate(seeders[:3]):
                        for attr_name in ("peer_data", "info"):
                            obj = getattr(s, attr_name, None)
                            if obj and hasattr(obj, "__len__"):
                                results.append(
                                    {
                                        "name": f"torrent[{i}].seeders[{j}].{attr_name}",
                                        "type": type(obj).__name__,
                                        "size": len(obj),
                                    }
                                )

                ppm = getattr(t, "peer_protocol_manager", None)
                if ppm:
                    for attr_name in ("peers", "peer_contact_history"):
                        obj = getattr(ppm, attr_name, None)
                        if obj and hasattr(obj, "__len__"):
                            results.append(
                                {
                                    "name": f"torrent[{i}].ppm.{attr_name}",
                                    "type": type(obj).__name__,
                                    "size": len(obj),
                                }
                            )

        gpm = getattr(self.controller, "global_peer_manager", None)
        if gpm:
            conn_mgr = getattr(gpm, "connection_manager", None)
            if conn_mgr:
                for attr_name in (
                    "all_incoming_connections",
                    "all_outgoing_connections",
                    "incoming_failed_times",
                    "outgoing_failed_times",
                    "update_callbacks",
                ):
                    obj = getattr(conn_mgr, attr_name, None)
                    if obj and hasattr(obj, "__len__"):
                        results.append(
                            {
                                "name": f"gpm.conn_mgr.{attr_name}",
                                "type": type(obj).__name__,
                                "size": len(obj),
                            }
                        )

            stats = getattr(gpm, "_per_manager_stats", None)
            if stats and hasattr(stats, "__len__"):
                results.append(
                    {
                        "name": "gpm._per_manager_stats",
                        "type": type(stats).__name__,
                        "size": len(stats),
                    }
                )

        return results

    def _inspect_large_containers(self) -> List[Dict[str, Any]]:
        """Find the largest dicts, lists, and sets in memory.

        Expensive — uses gc.get_objects(). Only called every Nth tick
        (every tick in deep mode).
        """
        results: List[Dict[str, Any]] = []
        large_containers: List[Tuple[int, str, int]] = []

        for obj in gc.get_objects():
            try:
                if isinstance(obj, dict) and len(obj) > 500:
                    large_containers.append((len(obj), "dict", id(obj)))
                elif isinstance(obj, (list, set)) and len(obj) > 500:
                    large_containers.append((len(obj), type(obj).__name__, id(obj)))
            except (TypeError, ReferenceError):
                continue

        large_containers.sort(reverse=True)
        for size, ctype, obj_id in large_containers[: self.top_n]:
            results.append(
                {
                    "name": f"large_{ctype}@{obj_id:#x}",
                    "type": ctype,
                    "size": size,
                }
            )

        return results

    def _print_report(self, report: Dict[str, Any]) -> None:
        """Print a formatted memory report."""
        lines = [
            "",
            "=" * 80,
            f"  MEMORY REPORT #{report['tick']}  |  RSS: {report['rss_mb']:.1f} MB  |  "
            f"VMS: {report['vms_mb']:.1f} MB  |  "
            f"Traced: {report['traced_current_mb']:.1f} MB (peak: {report['traced_peak_mb']:.1f} MB)",
            f"  GC counts: {report['gc_counts']}",
            "=" * 80,
        ]

        if len(self._snapshots) >= 2:
            prev = self._snapshots[-2]
            rss_delta = report["rss_mb"] - prev["rss_mb"]
            traced_delta = report["traced_current_mb"] - prev["traced_current_mb"]
            lines.append(f"  Delta since last: RSS {rss_delta:+.1f} MB  |  " f"Traced {traced_delta:+.1f} MB")

        if report["top_allocs"]:
            lines.append("")
            lines.append("  TOP ALLOCATIONS BY LINE:")
            lines.append("  " + "-" * 76)
            for stat in report["top_allocs"]:
                lines.append(f"  {stat}")

        if report["top_files"]:
            lines.append("")
            lines.append("  TOP ALLOCATIONS BY FILE:")
            lines.append("  " + "-" * 76)
            for stat in report["top_files"]:
                lines.append(f"  {stat}")

        if report["suspect_objects"]:
            lines.append("")
            lines.append("  TRACKED OBJECTS:")
            lines.append("  " + "-" * 76)
            for obj_info in report["suspect_objects"]:
                if "error" in obj_info:
                    lines.append(f"  ERROR: {obj_info['name']}: {obj_info['error']}")
                else:
                    lines.append(f"  {obj_info['name']:50s} {obj_info['type']:8s} size={obj_info['size']}")

        lines.append("=" * 80)
        lines.append("")

        print("\n".join(lines), file=sys.stderr)
