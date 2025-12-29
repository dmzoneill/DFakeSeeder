"""Manage autostart desktop file for DFakeSeeder.

This module handles the creation and removal of the autostart desktop entry
file in ~/.config/autostart/ to enable/disable automatic application startup
when the user logs in.
"""

import os
from pathlib import Path
from typing import Any

from d_fake_seeder.lib.logger import logger
from d_fake_seeder.view import View

AUTOSTART_DESKTOP_CONTENT = """[Desktop Entry]
Type=Application
Name=D' Fake Seeder
Comment=BitTorrent seeding simulation tool
Exec=dfs
Icon=dfakeseeder
Terminal=false
Categories=Network;P2P;
X-GNOME-Autostart-enabled=true
"""


def get_autostart_path() -> Path:
    """Get the path to the autostart desktop file.

    Returns:
        Path to ~/.config/autostart/dfakeseeder.desktop
    """
    return Path.home() / ".config" / "autostart" / "dfakeseeder.desktop"


def enable_autostart() -> bool:
    """Create the autostart desktop file.

    Creates the autostart directory if it doesn't exist and writes
    the desktop entry file.

    Returns:
        True if successful, False otherwise
    """
    try:
        autostart_path = get_autostart_path()
        autostart_path.parent.mkdir(parents=True, exist_ok=True)
        autostart_path.write_text(AUTOSTART_DESKTOP_CONTENT)
        os.chmod(autostart_path, 0o755)
        logger.info("Autostart enabled", "AutostartManager")

        # Notify user
        if View.instance:
            View.instance.notify(
                "Autostart enabled",
                notification_type="success",
                timeout_ms=2000,
                translate=True,
            )

        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to enable autostart: {e}", "AutostartManager", exc_info=True)

        # Notify user of failure
        if View.instance:
            View.instance.notify(
                "Failed to enable autostart",
                notification_type="error",
                translate=True,
            )

        return False


def disable_autostart() -> bool:
    """Remove the autostart desktop file.

    Returns:
        True if successful (or file didn't exist), False on error
    """
    try:
        autostart_path = get_autostart_path()
        if autostart_path.exists():
            autostart_path.unlink()
            logger.info("Autostart disabled", "AutostartManager")

            # Notify user
            if View.instance:
                View.instance.notify(
                    "Autostart disabled",
                    notification_type="info",
                    timeout_ms=2000,
                    translate=True,
                )

        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"Failed to disable autostart: {e}", "AutostartManager", exc_info=True)

        # Notify user of failure
        if View.instance:
            View.instance.notify(
                "Failed to disable autostart",
                notification_type="error",
                translate=True,
            )

        return False


def is_autostart_enabled() -> bool:
    """Check if autostart is currently enabled.

    Returns:
        True if the autostart desktop file exists
    """
    return get_autostart_path().exists()


def sync_autostart(enabled: bool) -> bool:
    """Enable or disable autostart based on the setting.

    Args:
        enabled: True to enable autostart, False to disable

    Returns:
        True if the operation was successful
    """
    if enabled:
        return enable_autostart()
    return disable_autostart()


def sync_autostart_with_settings(settings: Any) -> bool:
    """Sync autostart state with the current settings.

    Args:
        settings: AppSettings instance

    Returns:
        True if the operation was successful
    """
    enabled = getattr(settings, "auto_start", False)
    return sync_autostart(enabled)
