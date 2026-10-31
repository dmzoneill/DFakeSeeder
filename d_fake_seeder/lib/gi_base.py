"""Central, GTK-version-neutral GObject Introspection bootstrap.

Some modules are imported by *both* the GTK 4 application and the GTK 3 tray
process and only need version-neutral namespaces (``Gio``, ``GLib``,
``GObject``). They must not pull in a GTK version pin, which would raise
``ValueError`` in whichever process pins the other GTK major version. Import
those namespaces from here::

    from d_fake_seeder.lib.gi_base import Gio, GLib, GObject

Each namespace is loaded with :func:`importlib.import_module` (a function call,
not an ``import`` statement) so this module stays free of E402 on its own.
"""

from importlib import import_module

import gi

gi.require_version("Gio", "2.0")

Gio = import_module("gi.repository.Gio")
GLib = import_module("gi.repository.GLib")
GObject = import_module("gi.repository.GObject")

__all__ = ["Gio", "GLib", "GObject"]
