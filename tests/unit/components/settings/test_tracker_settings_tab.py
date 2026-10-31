"""
Unit tests for TrackerSettingsTab settings handling.

These cover the behaviour-preserving refactor that split the oversized
load/collect/validate methods into table-driven helpers: a toggle widget's
state is collected under its settings key, out-of-range and privileged ports
are rejected, and the IPv4 check accepts dotted quads while rejecting malformed
addresses. The shared ``settings_module`` / ``make_settings_tab`` fixtures
provide the mocked GTK import and tab builder.
"""

import importlib
from typing import Any
from unittest.mock import MagicMock

_COLLECT_TOGGLES = "_collect_toggle_settings"
_VALIDATE_PORTS = "_validate_ports"
_IS_VALID_IPV4 = "_is_valid_ipv4"
_MODULE = "d_fake_seeder.components.component.settings.tracker_settings_tab"


def test_is_valid_ipv4_accepts_and_rejects(settings_module: Any) -> None:
    """The dotted-quad check accepts valid octets and rejects malformed input."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.tracker_settings_tab")
        check = getattr(mod.TrackerSettingsTab, _IS_VALID_IPV4)
        assert check("192.168.0.1") is True
        assert check("0.1.2.3") is True
        assert check("255.255.255.255") is True
        assert check("256.1.1.1") is False
        assert check("1.2.3") is False
        assert check("a.b.c.d") is False


def test_collect_toggle_records_active_state(settings_module: Any, make_settings_tab: Any) -> None:
    """A present toggle widget's active state is stored under its settings key."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.tracker_settings_tab")
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = make_settings_tab(mod.TrackerSettingsTab, {"tracker_enabled": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_TOGGLES)(collected)
        assert collected["tracker_settings.enabled"] is True


def test_validate_ports_flags_range_and_privilege(settings_module: Any, make_settings_tab: Any) -> None:
    """Ports outside 1-65535 report a range error; low ports report a privilege error."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.tracker_settings_tab")
        http = MagicMock()
        http.get_value.return_value = 70000
        udp = MagicMock()
        udp.get_value.return_value = 80
        tab = make_settings_tab(mod.TrackerSettingsTab, {"http_port": http, "udp_port": udp})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_PORTS)(errors)
        assert "between 1 and 65535" in errors["http_port"]
        assert "root privileges" in errors["udp_port"]
