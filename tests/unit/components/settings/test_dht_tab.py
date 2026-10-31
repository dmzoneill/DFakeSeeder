"""
Unit tests for DHTTab settings handling.

These cover the behaviour-preserving refactor that split the oversized
load/collect/validate methods into table-driven helpers: a toggle widget's
state is collected under its settings key, out-of-range routing sizes are
rejected, and the bootstrap-node check accepts host:port entries while
rejecting missing or invalid ports. The shared ``settings_module`` /
``make_settings_tab`` fixtures provide the mocked GTK import and tab builder.
"""

from typing import Any
from unittest.mock import MagicMock

_COLLECT_TOGGLES = "_collect_toggle_settings"
_VALIDATE_RANGES = "_validate_ranges"
_NODE_ERROR = "_bootstrap_node_error"
_MODULE = "d_fake_seeder.components.component.settings.dht_tab"


def test_bootstrap_node_error_accepts_and_rejects(settings_module: Any) -> None:
    """A host:port node is accepted; a missing or invalid port is rejected."""
    with settings_module(_MODULE) as mod:
        node_error = getattr(mod.DHTTab, _NODE_ERROR)
        assert node_error("router.bittorrent.com:6881") is None
        assert "should be host:port" in node_error("router.bittorrent.com")
        assert "Invalid port" in node_error("host:70000")
        assert "Invalid port" in node_error("host:abc")


def test_collect_toggle_records_active_state(settings_module: Any, make_settings_tab: Any) -> None:
    """A present toggle widget's active state is stored under its settings key."""
    with settings_module(_MODULE) as mod:
        switch = MagicMock()
        switch.get_active.return_value = True
        tab = make_settings_tab(mod.DHTTab, {"dht_enabled": switch})
        collected: dict[str, Any] = {}
        getattr(tab, _COLLECT_TOGGLES)(collected)
        assert collected["protocols.dht.enabled"] is True


def test_validate_ranges_flags_routing_table_size(settings_module: Any, make_settings_tab: Any) -> None:
    """A routing-table size outside 8-512 is reported as an error."""
    with settings_module(_MODULE) as mod:
        size_widget = MagicMock()
        size_widget.get_value.return_value = 1000
        tab = make_settings_tab(mod.DHTTab, {"routing_table_size": size_widget})
        errors: dict[str, str] = {}
        getattr(tab, _VALIDATE_RANGES)(errors)
        assert "between 8 and 512" in errors["routing_table_size"]
