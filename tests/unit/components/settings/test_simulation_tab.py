"""
Unit tests for SimulationTab settings validation and collection.

These cover the helpers introduced when splitting the oversized load/collect/
validate methods: out-of-range rate fields and profile fields each report an
error while in-range values pass, and the peer-analysis-depth value is coerced
to int on collection. The shared ``settings_module`` / ``make_settings_tab``
fixtures provide the mocked GTK import and tab builder.
"""

from typing import Any
from unittest.mock import MagicMock

_VALIDATE_RATES = "_validate_rate_fields"
_VALIDATE_PROFILES = "_validate_profile_ranges"
_COLLECT_SWARM = "_collect_swarm_intelligence"
_MODULE = "d_fake_seeder.components.component.settings.simulation_tab"


def _spin(value: float) -> Any:
    """Return a spin-button mock whose get_value yields ``value``."""
    widget = MagicMock()
    widget.get_value.return_value = value
    return widget


def test_rate_fields_flag_out_of_range(settings_module: Any, make_settings_tab: Any) -> None:
    """A rate above 1.0 is flagged; an in-range rate is not."""
    with settings_module(_MODULE) as mod:
        tab = make_settings_tab(mod.SimulationTab, {"behavior_variation": _spin(1.5), "adaptation_rate": _spin(0.5)})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_RATES)(errors)
        assert "behavior_variation" in errors
        assert "adaptation_rate" not in errors


def test_profile_ranges_flag_out_of_range(settings_module: Any, make_settings_tab: Any) -> None:
    """A profile variance below 0 is flagged with a humanised field name."""
    with settings_module(_MODULE) as mod:
        tab = make_settings_tab(mod.SimulationTab, {"conservative_upload_variance": _spin(-0.2)})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_PROFILES)(errors)
        assert "between 0.0 and 1.0" in errors["conservative_upload_variance"]


def test_collect_swarm_coerces_depth_to_int(settings_module: Any, make_settings_tab: Any) -> None:
    """The peer-analysis-depth value is coerced to an int."""
    with settings_module(_MODULE) as mod:
        tab = make_settings_tab(mod.SimulationTab, {"peer_analysis_depth": _spin(12.0)})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_SWARM)(collected)
        depth = collected["simulation.swarm_intelligence.peer_analysis_depth"]
        assert depth == 12
        assert isinstance(depth, int)
