"""XDG Base Directory helpers for Flatpak compatibility.

Provides functions that respect XDG_CONFIG_HOME, XDG_DATA_HOME, and
XDG_CACHE_HOME environment variables.  On native pip/rpm/deb installs
these variables are typically unset, so the functions fall back to the
standard ~/.config, ~/.local/share, and ~/.cache paths — identical to
the previous hardcoded behaviour.

Inside a Flatpak sandbox XDG_CONFIG_HOME is set to
~/.var/app/ie.fio.dfakeseeder/config/ (and similar for data/cache),
so using these helpers instead of hardcoded paths makes the application
work correctly in both environments.

No new dependencies: uses only ``os`` and ``pathlib``.
"""

import os

_APP_DIR = "dfakeseeder"


def get_config_dir() -> str:
    """Return the application config directory.

    Returns ``$XDG_CONFIG_HOME/dfakeseeder`` when the variable is set
    (Flatpak), otherwise ``~/.config/dfakeseeder`` (native).
    """
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, _APP_DIR)


def get_data_dir() -> str:
    """Return the XDG data base directory.

    Returns ``$XDG_DATA_HOME`` when set, otherwise ``~/.local/share``.
    """
    return os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")


def get_cache_dir() -> str:
    """Return the XDG cache base directory.

    Returns ``$XDG_CACHE_HOME`` when set, otherwise ``~/.cache``.
    """
    return os.environ.get("XDG_CACHE_HOME") or os.path.join(os.path.expanduser("~"), ".cache")


def is_flatpak() -> bool:
    """Return True if running inside a Flatpak sandbox."""
    return os.path.isfile("/.flatpak-info") or "FLATPAK_ID" in os.environ
