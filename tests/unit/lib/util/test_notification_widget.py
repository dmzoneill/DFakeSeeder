"""
Unit tests for NotificationWidget action-callback handling.

These cover the behaviour-preserving cleanup of notification_widget: the action
button handler must invoke the user callback, emit the "action-clicked" signal
and dismiss the toast, and must keep doing so even when the callback raises one
of the narrowed exception types (previously a blind ``except Exception``).

The GTK layer is mocked so the widget imports headless; ``Gtk.Frame`` is given a
real stub base class since a MagicMock cannot be subclassed.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock


class _GError(Exception):
    """Real stand-in for GLib.Error used in the narrowed except tuple."""


# Internal handler name, referenced indirectly to avoid protected-member lint.
_ON_ACTION_CLICKED = "_on_action_clicked"


def _click(widget: Any) -> None:
    """Invoke the internal action-clicked handler."""
    handler = getattr(widget, _ON_ACTION_CLICKED)
    handler(MagicMock())


@contextlib.contextmanager
def loaded_widget() -> Iterator[ModuleType]:
    """Import notification_widget with the GTK layer mocked."""
    name = "d_fake_seeder.lib.util.notification_widget"
    gi_names = [
        "gi",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.Gdk",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GObject",
    ]
    extra = ["d_fake_seeder.lib.gi_gtk4", name]
    saved = {n: sys.modules.get(n) for n in gi_names + extra}

    for n in gi_names:
        sys.modules[n] = MagicMock()
    gtk4 = MagicMock()
    gtk4.Gtk.Frame = type("Frame", (), {"__init__": lambda self: None})
    gtk4.GLib.Error = _GError
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = gtk4
    sys.modules.pop(name, None)
    try:
        yield importlib.import_module("d_fake_seeder.lib.util.notification_widget")
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _bare_widget(mod: ModuleType) -> Any:
    """Build a NotificationWidget with emit/dismiss stubbed, no GTK __init__."""
    widget = mod.NotificationWidget.__new__(mod.NotificationWidget)
    widget.emit = MagicMock()
    widget.dismiss = MagicMock()
    return widget


def test_action_callback_invoked_then_emit_and_dismiss() -> None:
    """A successful callback is run, then the signal is emitted and toast dismissed."""
    with loaded_widget() as mod:
        widget = _bare_widget(mod)
        widget.action_callback = MagicMock()

        _click(widget)

        widget.action_callback.assert_called_once()
        widget.emit.assert_called_once_with("action-clicked")
        widget.dismiss.assert_called_once()


def test_callback_error_is_swallowed_and_flow_continues() -> None:
    """A callback raising a narrowed error is logged, not propagated; flow continues."""
    with loaded_widget() as mod:
        widget = _bare_widget(mod)
        widget.action_callback = MagicMock(side_effect=TypeError("boom"))

        _click(widget)

        widget.emit.assert_called_once_with("action-clicked")
        widget.dismiss.assert_called_once()
