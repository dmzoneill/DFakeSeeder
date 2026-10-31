"""
Unit tests for the BaseSettingsTab model/attribute/settings change handlers.

BaseSettingsTab implements the handlers inherited as abstract from Component
(handle_model_changed / handle_attribute_changed / handle_settings_changed /
update_view), resolving the W0223 abstract-method gap for every settings tab.
Settings tabs are widget-driven, so these events are behaviour-preservingly
traced. The handlers are exercised as unbound calls on a stub ``self`` to avoid
GTK instantiation; the shared ``settings_module`` fixture provides the mocked
import (base_tab does not need the real GLib.Error shim).
"""

import importlib
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

_MODULE = "d_fake_seeder.components.component.settings.base_tab"


def _stub() -> SimpleNamespace:
    """A minimal stand-in self with just the attributes the handlers touch."""
    return SimpleNamespace(logger=MagicMock())


def test_handle_model_changed_traces(settings_module: Any) -> None:
    """handle_model_changed logs a trace and does not raise."""
    with settings_module(_MODULE, real_glib_error=False):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        stub = _stub()
        assert mod.BaseSettingsTab.handle_model_changed(stub, "src", "data", "changed") is None
        stub.logger.trace.assert_called_once()


def test_handle_attribute_changed_traces(settings_module: Any) -> None:
    """handle_attribute_changed logs a trace and does not raise."""
    with settings_module(_MODULE, real_glib_error=False):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        stub = _stub()
        assert mod.BaseSettingsTab.handle_attribute_changed(stub, "src", "key", "value") is None
        stub.logger.trace.assert_called_once()


def test_handle_settings_changed_traces(settings_module: Any) -> None:
    """handle_settings_changed logs a trace and does not raise."""
    with settings_module(_MODULE, real_glib_error=False):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        stub = _stub()
        assert mod.BaseSettingsTab.handle_settings_changed(stub, "src", "data", "changed") is None
        stub.logger.trace.assert_called_once()


def test_update_view_traces(settings_module: Any) -> None:
    """update_view logs a trace and does not raise."""
    with settings_module(_MODULE, real_glib_error=False):
        mod = importlib.import_module("d_fake_seeder.components.component.settings.base_tab")
        stub = _stub()
        assert mod.BaseSettingsTab.update_view(stub, "model", "torrent", "attr") is None
        stub.logger.trace.assert_called_once()
