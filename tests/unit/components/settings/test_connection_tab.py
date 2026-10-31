"""
Unit tests for ConnectionTab settings handling.

These cover the proxy helpers after the broad-except narrowing and import
cleanup: toggling the auth fields propagates sensitivity to both the username
and password widgets, and collecting proxy settings maps the dropdown index to
the matching proxy type. The shared ``settings_module`` / ``make_settings_tab``
fixtures provide the mocked GTK import and tab builder.
"""

import importlib
from typing import Any
from unittest.mock import MagicMock

_UPDATE_AUTH = "_update_proxy_auth_fields"
_COLLECT_PROXY = "_collect_proxy_settings"
_MODULE = "d_fake_seeder.components.component.settings.connection_tab"


def test_update_proxy_auth_fields_propagates_sensitivity(settings_module: Any, make_settings_tab: Any) -> None:
    """Enabling auth sets both the username and password widgets sensitive."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.connection_tab")
        username = MagicMock()
        password = MagicMock()
        tab = make_settings_tab(mod.ConnectionTab, {"proxy_username": username, "proxy_password": password})
        getattr(tab, _UPDATE_AUTH)(True)
        username.set_sensitive.assert_called_once_with(True)
        password.set_sensitive.assert_called_once_with(True)


def test_collect_proxy_settings_maps_dropdown_type(settings_module: Any, make_settings_tab: Any) -> None:
    """The proxy-type dropdown index is mapped to its named type."""
    with settings_module(_MODULE):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.connection_tab")
        proxy_type = MagicMock()
        proxy_type.get_selected.return_value = 2  # socks4
        server = MagicMock()
        server.get_text.return_value = "proxy.example"
        port = MagicMock()
        port.get_value.return_value = 8080
        tab = make_settings_tab(
            mod.ConnectionTab,
            {"proxy_type": proxy_type, "proxy_server": server, "proxy_port": port},
        )
        collected = getattr(tab, _COLLECT_PROXY)()
        assert collected["type"] == "socks4"
        assert collected["server"] == "proxy.example"
        assert collected["port"] == 8080
        assert "username" not in collected
