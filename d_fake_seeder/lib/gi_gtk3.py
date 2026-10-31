"""Central GObject Introspection bootstrap for the GTK 3 tray process.

The system-tray helper runs as a separate process built on GTK 3 and
AppIndicator3. Importing this module pins those typelib versions and
re-exports the ``gi.repository`` namespaces it needs, so the tray can do::

    from d_fake_seeder.lib.gi_gtk3 import Gtk, AppIndicator3, Notify

without per-import ``# noqa: E402``. Keeping the GTK 3 pins in a dedicated
module (separate from :mod:`d_fake_seeder.lib.gi_gtk4`) ensures a version is
only required in the process that actually imports it. The re-exports are typed
``Any`` because the typelib members are resolved dynamically at runtime.
"""

from importlib import import_module
from typing import Any

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Notify", "0.7")
gi.require_version("Gio", "2.0")

Gdk: Any = import_module("gi.repository.Gdk")
Gtk: Any = import_module("gi.repository.Gtk")
AppIndicator3: Any = import_module("gi.repository.AppIndicator3")
Notify: Any = import_module("gi.repository.Notify")
Gio: Any = import_module("gi.repository.Gio")
GLib: Any = import_module("gi.repository.GLib")

__all__ = ["AppIndicator3", "GLib", "Gdk", "Gio", "Gtk", "Notify"]
