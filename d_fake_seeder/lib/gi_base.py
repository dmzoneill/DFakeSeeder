"""Central, GTK-version-neutral GObject Introspection bootstrap.

Some modules are imported by *both* the GTK 4 application and the GTK 3 tray
process and only need version-neutral namespaces (``Gio``, ``GLib``,
``GObject``). They must not pull in a GTK version pin, which would raise
``ValueError`` in whichever process pins the other GTK major version. Import
those namespaces from here::

    from d_fake_seeder.lib.gi_base import Gio, GLib, GObject

Each namespace is loaded with :func:`importlib.import_module` (a function call,
not an ``import`` statement) so this module stays free of E402 on its own. The
re-exports are typed ``Any`` because the typelib members are resolved
dynamically at runtime by PyGObject.
"""

from importlib import import_module
from typing import Any

import gi

gi.require_version("Gio", "2.0")

Gio: Any = import_module("gi.repository.Gio")
GLib: Any = import_module("gi.repository.GLib")
GObject: Any = import_module("gi.repository.GObject")

__all__ = ["GLib", "GObject", "Gio"]
