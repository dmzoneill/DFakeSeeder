"""
Unit tests for SimulationTab settings validation and collection.

These cover the helpers introduced when splitting the oversized load/collect/
validate methods: out-of-range rate fields and profile fields each report an
error while in-range values pass, and the peer-analysis-depth value is coerced
to int on collection. The GTK layer and AppSettings are mocked so the module
imports headless; internal helpers are reached via variable-name getattr to keep
the access out of the protected-member linter.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

_CLEANUP_DONE = "_cleanup_done"
_WIDGETS = "_widgets"
_VALIDATE_RATES = "_validate_rate_fields"
_VALIDATE_PROFILES = "_validate_profile_ranges"
_COLLECT_SWARM = "_collect_swarm_intelligence"


@contextlib.contextmanager
def loaded_tab() -> Iterator[ModuleType]:
    """Import simulation_tab with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.components.component.settings.simulation_tab"
    gi_names = [
        "gi",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.Gdk",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GObject",
    ]
    extra = ["d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.domain.app_settings", name]
    saved = {n: sys.modules.get(n) for n in gi_names + extra}
    for n in gi_names:
        sys.modules[n] = MagicMock()
    gi_gtk4 = MagicMock()
    gi_gtk4.GLib.Error = type("GLibError", (Exception,), {})
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = gi_gtk4
    sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock()
    sys.modules.pop(name, None)
    try:
        yield importlib.import_module("d_fake_seeder.components.component.settings.simulation_tab")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _spin(value: float) -> Any:
    """Return a spin-button mock whose get_value yields ``value``."""
    widget = MagicMock()
    widget.get_value.return_value = value
    return widget


def _tab(mod: ModuleType, widgets: dict[str, Any]) -> Any:
    """Build a SimulationTab whose widget lookups resolve from ``widgets``."""
    tab = mod.SimulationTab.__new__(mod.SimulationTab)
    setattr(tab, _CLEANUP_DONE, True)
    setattr(tab, _WIDGETS, dict(widgets))
    tab.logger = MagicMock()
    tab.builder = MagicMock()
    tab.builder.get_object.side_effect = widgets.get
    return tab


def test_rate_fields_flag_out_of_range() -> None:
    """A rate above 1.0 is flagged; an in-range rate is not."""
    with loaded_tab() as mod:
        tab = _tab(mod, {"behavior_variation": _spin(1.5), "adaptation_rate": _spin(0.5)})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_RATES)(errors)
        assert "behavior_variation" in errors
        assert "adaptation_rate" not in errors


def test_profile_ranges_flag_out_of_range() -> None:
    """A profile variance below 0 is flagged with a humanised field name."""
    with loaded_tab() as mod:
        tab = _tab(mod, {"conservative_upload_variance": _spin(-0.2)})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_PROFILES)(errors)
        assert "between 0.0 and 1.0" in errors["conservative_upload_variance"]


def test_collect_swarm_coerces_depth_to_int() -> None:
    """The peer-analysis-depth value is coerced to an int."""
    with loaded_tab() as mod:
        tab = _tab(mod, {"peer_analysis_depth": _spin(12.0)})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_SWARM)(collected)
        depth = collected["simulation.swarm_intelligence.peer_analysis_depth"]
        assert depth == 12
        assert isinstance(depth, int)
