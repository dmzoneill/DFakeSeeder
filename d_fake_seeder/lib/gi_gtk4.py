"""Central GObject Introspection bootstrap for the GTK 4 application process.

Importing this module pins the typelib versions used by the main application
and re-exports the ``gi.repository`` namespaces, so callers can simply do::

    from d_fake_seeder.lib.gi_gtk4 import Gtk, Gdk, GLib

without repeating ``gi.require_version`` or needing per-import ``# noqa: E402``.
Each namespace is loaded with :func:`importlib.import_module` (a function call,
not an ``import`` statement) so this module stays free of E402 on its own. The
re-exports are typed ``Any`` because the typelib members are resolved
dynamically at runtime by PyGObject.
"""

from importlib import import_module
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")
gi.require_version("Gio", "2.0")

Gtk: Any = import_module("gi.repository.Gtk")
Gdk: Any = import_module("gi.repository.Gdk")
Gio: Any = import_module("gi.repository.Gio")
GLib: Any = import_module("gi.repository.GLib")
GObject: Any = import_module("gi.repository.GObject")

__all__ = ["GLib", "GObject", "Gdk", "Gio", "Gtk"]
