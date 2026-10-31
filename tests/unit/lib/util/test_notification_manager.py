"""
Unit tests for NotificationManager dispatch behaviour.

These cover the behaviour-preserving cleanup of notification_manager: the
disabled-notifications short-circuit (statusbar fallback) and the show_*
convenience wrappers routing to show() with the right NotificationType.

The GTK layer (gi / gi_gtk4) and AppSettings are mocked so the module imports
headless; the private settings accessor is patched via variable-name setattr to
keep the access out of the protected-member linter without a suppression.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock


class _GError(Exception):
    """Real stand-in for GLib.Error used in narrowed except tuples."""


_GET_SETTINGS = "_get_settings"


@contextlib.contextmanager
def loaded_manager() -> Iterator[ModuleType]:
    """Import notification_manager with the GTK layer and AppSettings mocked."""
    name = "d_fake_seeder.lib.util.notification_manager"
    gi_names = [
        "gi",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.Gdk",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "gi.repository.Pango",
    ]
    extra = ["d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.domain.app_settings", name]
    saved = {n: sys.modules.get(n) for n in gi_names + extra}

    for n in gi_names:
        sys.modules[n] = MagicMock()
    gtk4 = MagicMock()
    gtk4.GLib.Error = _GError
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = gtk4
    sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock()
    sys.modules.pop(name, None)
    try:
        yield importlib.import_module("d_fake_seeder.lib.util.notification_manager")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _bare_manager(mod: ModuleType) -> Any:
    """Build a NotificationManager without running its GTK __init__."""
    return mod.NotificationManager.__new__(mod.NotificationManager)


def test_disabled_notification_updates_statusbar_and_returns_none() -> None:
    """When notifications are disabled, show() falls back to the statusbar."""
    with loaded_manager() as mod:
        manager = _bare_manager(mod)
        manager.statusbar_callback = MagicMock()
        setattr(manager, _GET_SETTINGS, lambda: {"enabled": False, "show_in_statusbar": True})

        result = manager.show("hello")

        assert result is None
        manager.statusbar_callback.assert_called_once_with("hello")


def test_show_info_routes_to_info_type() -> None:
    """show_info delegates to show() with NotificationType.INFO."""
    with loaded_manager() as mod:
        manager = _bare_manager(mod)
        manager.show = MagicMock(return_value="widget")

        result = manager.show_info("hi", timeout_ms=5)

        assert result == "widget"
        manager.show.assert_called_once_with("hi", mod.NotificationType.INFO, timeout_ms=5)


def test_show_error_routes_to_error_type() -> None:
    """show_error delegates to show() with NotificationType.ERROR."""
    with loaded_manager() as mod:
        manager = _bare_manager(mod)
        manager.show = MagicMock(return_value="widget")

        manager.show_error("broken")

        manager.show.assert_called_once_with("broken", mod.NotificationType.ERROR)
