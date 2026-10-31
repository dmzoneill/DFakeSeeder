"""
Unit tests for PeerProtocolTab settings validation.

These exercise the port/transaction-id range validation after the broad-except
narrowing and import cleanup: an inverted seeder port range and an inverted
transaction-id range each produce an error, while a well-ordered pair does not.
The shared ``settings_module`` / ``make_settings_tab`` fixtures provide the
mocked GTK import and tab builder.
"""

import importlib
from typing import Any
from unittest.mock import MagicMock

_VALIDATE = "_validate_tab_settings"
_MODULE = "d_fake_seeder.components.component.settings.peer_protocol_tab"


def _spin(value: int) -> Any:
    """Return a spin-button mock whose get_value yields ``value``."""
    widget = MagicMock()
    widget.get_value.return_value = value
    return widget


def test_inverted_ranges_report_errors(settings_module: Any, make_settings_tab: Any) -> None:
    """Inverted seeder-port and transaction-id ranges each raise an error."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.peer_protocol_tab")
        widgets = {
            "seeder_port_min": _spin(6889),
            "seeder_port_max": _spin(6881),
            "transaction_id_min": _spin(100),
            "transaction_id_max": _spin(10),
        }
        errors = getattr(make_settings_tab(mod.PeerProtocolTab, widgets), _VALIDATE)()
        assert "seeder_port_range" in errors
        assert "transaction_id_range" in errors


def test_ordered_ranges_pass(settings_module: Any, make_settings_tab: Any) -> None:
    """Well-ordered ranges produce no validation errors."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.peer_protocol_tab")
        widgets = {
            "seeder_port_min": _spin(6881),
            "seeder_port_max": _spin(6889),
            "transaction_id_min": _spin(10),
            "transaction_id_max": _spin(100),
        }
        errors = getattr(make_settings_tab(mod.PeerProtocolTab, widgets), _VALIDATE)()
        assert errors == {}
