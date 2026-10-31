"""Shared fixtures for component unit tests.

Provides a single headless-import environment that mocks the GTK stack and
AppSettings so component modules can be imported without a display, keeping the
boilerplate in one place across the component test modules.
"""

import contextlib
import sys
from collections.abc import Callable, Iterator
from typing import Any
from unittest.mock import MagicMock

import pytest

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
def _component_env(module_name: str) -> Iterator[None]:
    """Mock the GTK layer and AppSettings so a component module imports headless."""
    extra = ["d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.domain.app_settings", module_name]
    saved = {name: sys.modules.get(name) for name in (*_GI_MODULES, *extra)}
    for name in _GI_MODULES:
        sys.modules[name] = MagicMock()
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = MagicMock()
    sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock()
    sys.modules.pop(module_name, None)
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is not None:
                sys.modules[name] = module
            else:
                sys.modules.pop(name, None)


@pytest.fixture
def component_module() -> Callable[[str], Any]:
    """Return a context manager that mocks GTK/AppSettings around a fresh import."""
    return _component_env
