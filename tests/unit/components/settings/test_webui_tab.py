"""
Unit tests for WebUITab settings handling.

These cover the helpers introduced when splitting the oversized load/collect/
validate/reset methods: the interface check distinguishes a malformed quad from
an out-of-range octet, switch states collect as booleans, and ports coerce to
int. The shared ``settings_module`` / ``make_settings_tab`` fixtures provide the
mocked GTK import and tab builder.
"""

from typing import Any
from unittest.mock import MagicMock

_INTERFACE_ERROR = "_interface_error"
_COLLECT_BOOLS = "_collect_webui_bools"
_COLLECT_INTS = "_collect_webui_ints"
_MODULE = "d_fake_seeder.components.component.settings.webui_tab"


def test_interface_error_distinguishes_format_and_range(settings_module: Any) -> None:
    """A valid quad passes; a short quad is a format error; a big octet is a range error."""
    with settings_module(_MODULE) as mod:
        interface_error = getattr(mod.WebUITab, _INTERFACE_ERROR)
        assert interface_error("192.168.1.10") is None
        assert interface_error("1.2.3") == "Invalid IP address format"
        assert interface_error("1.2.3.300") == "Invalid IP address"


def test_collect_bools_records_active_state(settings_module: Any, make_settings_tab: Any) -> None:
    """A present switch widget's active state is stored under its nested key."""
    with settings_module(_MODULE) as mod:
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = make_settings_tab(mod.WebUITab, {"enable_webui": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_BOOLS)(collected)
        assert collected["webui.enabled"] is True


def test_collect_ints_coerces_port(settings_module: Any, make_settings_tab: Any) -> None:
    """The port spin value is coerced to an int under its nested key."""
    with settings_module(_MODULE) as mod:
        port = MagicMock()
        port.get_value.return_value = 8080.0
        tab = make_settings_tab(mod.WebUITab, {"webui_port": port})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_INTS)(collected)
        assert collected["webui.port"] == 8080
        assert isinstance(collected["webui.port"], int)
