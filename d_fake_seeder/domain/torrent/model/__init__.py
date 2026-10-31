"""Torrent model package.

Declares the required GObject typelib version once, before any submodule
imports ``gi.repository`` names, so submodules can keep their imports at the
top of the file (no E402) without each repeating ``gi.require_version``.
"""

import gi

gi.require_version("GObject", "2.0")
