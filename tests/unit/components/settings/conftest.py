"""
Shared pytest fixtures for the settings-tab unit tests.

Every settings-tab test needs to import a GTK-dependent module headless, so the
GTK stack (``gi`` + ``gi.repository.*``), the ``gi_gtk4`` bootstrap and
``AppSettings`` are replaced with mocks before import and restored afterwards.
Centralising that setup here keeps the individual test modules free of the
duplicated boilerplate that previously tripped the duplicate-code checks.
"""

import contextlib
import importlib
import sys
from collections.abc import Callable, Iterator
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock

import pytest

_CLEANUP_DONE = "_cleanup_done"
_WIDGETS = "_widgets"

_GI_MODULES = (
    "gi",
    "gi.repository",
    "gi.repository.Gtk",
    "gi.repository.Gdk",
    "gi.repository.Gio",
    "gi.repository.GLib",
    "gi.repository.GObject",
)


@contextlib.contextmanager
def _load_settings_module(module_name: str, *, real_glib_error: bool = True) -> Iterator[ModuleType]:
    """Import ``module_name`` with the GTK layer and AppSettings mocked, then restore.

    When ``real_glib_error`` is true the mocked ``gi_gtk4.GLib.Error`` is a real
    ``Exception`` subclass so narrowed ``except (... GLib.Error)`` clauses stay valid.
    """
    extra = ["d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.domain.app_settings", module_name]
    saved = {name: sys.modules.get(name) for name in (*_GI_MODULES, *extra)}
    for name in _GI_MODULES:
        sys.modules[name] = MagicMock()
    gi_gtk4 = MagicMock()
    if real_glib_error:
        gi_gtk4.GLib.Error = type("GLibError", (Exception,), {})
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = gi_gtk4
    sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock()
    sys.modules.pop(module_name, None)
    try:
        yield importlib.import_module(module_name)
    finally:
        for name, module in saved.items():
            if module is not None:
                sys.modules[name] = module
            else:
                sys.modules.pop(name, None)


@pytest.fixture
def settings_module() -> Callable[..., Any]:
    """Return a context manager that imports a settings module with GTK/AppSettings mocked."""
    return _load_settings_module


@pytest.fixture
def make_settings_tab() -> Callable[[Any, dict[str, Any]], Any]:
    """Return a builder for a settings-tab instance backed by a widget map.

    The instance is created without running ``__init__`` (avoiding GTK), with
    ``_cleanup_done`` set so CleanupMixin.__del__ stays quiet, a cached widget
    map, and a builder whose ``get_object`` resolves from that same map.
    """

    def _build(cls: Any, widgets: dict[str, Any]) -> Any:
        tab = cls.__new__(cls)
        setattr(tab, _CLEANUP_DONE, True)
        setattr(tab, _WIDGETS, dict(widgets))
        tab.logger = MagicMock()
        tab.app_settings = MagicMock()
        tab.builder = MagicMock()
        tab.builder.get_object.side_effect = widgets.get
        return tab

    return _build
