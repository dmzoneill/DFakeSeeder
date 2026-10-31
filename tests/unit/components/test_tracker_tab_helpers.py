"""
Unit tests for TrackerTab's formatting and speed helpers.

These cover the behaviour-preserving refactor that extracted human-readable
byte/speed/last-activity formatting and the upload/download speed differential
into focused helpers. The GTK stack is mocked so the component imports headless;
the pure helpers run on an instance built without ``__init__``.
"""

import importlib
import time
from types import SimpleNamespace
from typing import Any

_MODULE = "d_fake_seeder.components.component.tracker_tab"

_CLEANUP_DONE = "_cleanup_done"
_RUNTIME = "_runtime"
_FORMAT_BYTES = "_format_bytes"
_FORMAT_SPEED = "_format_speed"
_FORMAT_LAST_ACTIVITY = "_format_last_activity"
_COMPUTE_SPEEDS = "_compute_speeds"


def _make_tracker(mod: Any) -> Any:
    """Build a TrackerTab without running __init__, with empty speed-tracking state."""
    tab = mod.TrackerTab.__new__(mod.TrackerTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _RUNTIME, SimpleNamespace(server=None, timer_id=None, prev_stats={}, last_update_time=time.time()))
    return tab


def test_format_bytes_scales_units(component_module: Any) -> None:
    """Bytes are formatted into B/KB/MB/GB at the expected thresholds."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        fmt = getattr(mod.TrackerTab, _FORMAT_BYTES)
        assert fmt(512) == "512 B"
        assert fmt(2048) == "2.0 KB"
        assert fmt(5 * 1024 * 1024) == "5.0 MB"
        assert fmt(3 * 1024 * 1024 * 1024) == "3.00 GB"


def test_format_speed_scales_units(component_module: Any) -> None:
    """Speed is formatted into B/s, KB/s and MB/s at the expected thresholds."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        fmt = getattr(mod.TrackerTab, _FORMAT_SPEED)
        assert fmt(500) == "500 B/s"
        assert fmt(2048) == "2.0 KB/s"
        assert fmt(5 * 1024 * 1024) == "5.0 MB/s"


def test_format_last_activity_buckets_elapsed_time(component_module: Any) -> None:
    """Elapsed time since last announce is bucketed into seconds/minutes/hours."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        fmt = getattr(mod.TrackerTab, _FORMAT_LAST_ACTIVITY)
        now = time.time()
        assert fmt(now - 5).endswith("s ago")
        assert fmt(now - 120) == "2m ago"
        assert fmt(now - 7200) == "2h ago"


def test_compute_speeds_uses_differentials(component_module: Any) -> None:
    """The first sample reports zero speed and stores state; the next yields a rate."""
    with component_module(_MODULE):
        mod = importlib.import_module(_MODULE)
        tab = _make_tracker(mod)
        compute = getattr(tab, _COMPUTE_SPEEDS)

        first = compute("abcd", uploaded=1000, downloaded=2000, time_delta=1.0)
        assert first == (0.0, 0.0)
        assert getattr(tab, _RUNTIME).prev_stats["abcd"] == {"uploaded": 1000, "downloaded": 2000}

        up, down = compute("abcd", uploaded=3000, downloaded=2000, time_delta=2.0)
        assert up == 1000.0  # (3000 - 1000) / 2.0
        assert down == 0.0  # no download progress
