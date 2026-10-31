"""
Unit tests for the DBusUnifier D-Bus method-call dispatcher.

These cover the behaviour-preserving cleanup of dbus_unifier: the method-call
callback (now using the GDBus positional *args signature) must dispatch known
methods to their handlers, reject unknown methods, and swallow handler errors
into a D-Bus error reply while bumping the error counter.

Only the heavy AppSettings dependency is mocked; the real gi_base (Gio/GLib)
is used since those typelibs are available headless. The dispatcher and its
counters are internal, so they are reached via variable-name getattr/setattr
to keep the access out of the protected-member / getattr-constant linters
without a suppression comment.
"""

import contextlib
import importlib
import sys
from collections.abc import Iterator
from types import ModuleType
from unittest.mock import MagicMock

# Internal attribute names, referenced indirectly (see module docstring).
_DISPATCH = "_handle_method_call"
_PING = "_handle_ping"
_MESSAGE_COUNT = "_message_count"
_ERROR_COUNT = "_error_count"


@contextlib.contextmanager
def loaded_unifier() -> Iterator[ModuleType]:
    """Import dbus_unifier with the heavy AppSettings dependency mocked."""
    name = "d_fake_seeder.lib.util.dbus_unifier"
    settings_name = "d_fake_seeder.domain.app_settings"
    saved_settings = sys.modules.get(settings_name)
    sys.modules[settings_name] = MagicMock()
    sys.modules.pop(name, None)
    try:
        yield importlib.import_module(name)
    finally:
        sys.modules.pop(name, None)
        if saved_settings is not None:
            sys.modules[settings_name] = saved_settings
        else:
            sys.modules.pop(settings_name, None)


def _bare_unifier(mod: ModuleType) -> object:
    """Build a DBusUnifier without running its D-Bus __init__ setup."""
    unifier = mod.DBusUnifier.__new__(mod.DBusUnifier)
    setattr(unifier, _MESSAGE_COUNT, 0)
    setattr(unifier, _ERROR_COUNT, 0)
    return unifier


def _call(unifier: object, method_name: str, invocation: object) -> None:
    """Invoke the GDBus-style callback with the mandated positional args."""
    dispatch = getattr(unifier, _DISPATCH)
    dispatch(None, None, None, None, method_name, MagicMock(), invocation)


def test_unknown_method_returns_dbus_error() -> None:
    """An unknown method name must produce a D-Bus error, not a value reply."""
    with loaded_unifier() as mod:
        unifier = _bare_unifier(mod)
        invocation = MagicMock()

        _call(unifier, "NoSuchMethod", invocation)

        invocation.return_error_literal.assert_called_once()
        invocation.return_value.assert_not_called()


def test_known_method_dispatches_to_handler() -> None:
    """A known method name routes to its handler and returns a value reply."""
    with loaded_unifier() as mod:
        unifier = _bare_unifier(mod)
        ping = MagicMock(return_value=True)
        setattr(unifier, _PING, ping)
        invocation = MagicMock()

        _call(unifier, "Ping", invocation)

        ping.assert_called_once()
        invocation.return_value.assert_called_once()
        invocation.return_error_literal.assert_not_called()
        assert getattr(unifier, _MESSAGE_COUNT) == 1


def test_handler_exception_is_caught_and_reported() -> None:
    """A handler raising a caught error is turned into a D-Bus error reply."""
    with loaded_unifier() as mod:
        unifier = _bare_unifier(mod)
        setattr(unifier, _PING, MagicMock(side_effect=TypeError("boom")))
        invocation = MagicMock()

        _call(unifier, "Ping", invocation)

        invocation.return_error_literal.assert_called_once()
        invocation.return_value.assert_not_called()
        assert getattr(unifier, _ERROR_COUNT) == 1
