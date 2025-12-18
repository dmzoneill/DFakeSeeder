#!/usr/bin/env python3
"""
Post-install script for D' Fake Seeder desktop integration.
This script installs desktop files and icons to provide proper
desktop environment integration after PyPI installation.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

# fmt: off
from typing import Any

from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.constants import DEFAULT_ICON_SIZES

# fmt: on


def get_package_dir() -> Any:
    """Get the installed package directory."""
    try:
        import d_fake_seeder

        return Path(d_fake_seeder.__file__).parent
    except ImportError:
        logger.trace(
            "Error: d_fake_seeder package not found. Please install it first.",
            "UnknownClass",
        )
        sys.exit(1)


def install_icons(package_dir: Any, home_dir: Any) -> Any:
    """Install application icons to user icon directories."""
    icon_source = package_dir / "components" / "images" / "dfakeseeder.png"
    if not icon_source.exists():
        logger.error(f"Warning: Icon file not found at {icon_source}", "UnknownClass")
        return False
    icon_base = home_dir / ".local" / "share" / "icons" / "hicolor"
    # Install to multiple sizes for better compatibility
    sizes = DEFAULT_ICON_SIZES
    installed_any = False
    for size in sizes:
        target_dir = icon_base / size / "apps"
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / "dfakeseeder.png"
        try:
            shutil.copy2(icon_source, target_file)
            logger.trace("✓ Installed icon: ...", "UnknownClass")
            installed_any = True
        except Exception:
            logger.warning("Warning: Could not install icon to ...: ...", "UnknownClass")
    return installed_any


def install_desktop_file(package_dir: Any, home_dir: Any) -> Any:
    """Install desktop file to user applications directory."""
    # Try template file first (for PyPI installations), then fall back to dev desktop file
    desktop_template = package_dir / "dfakeseeder.desktop.template"
    desktop_source = package_dir / "dfakeseeder.desktop"

    # Prefer template if it exists (PyPI installation)
    if desktop_template.exists():
        source_file = desktop_template
    elif desktop_source.exists():
        source_file = desktop_source
    else:
        logger.warning("Warning: No desktop file found", "UnknownClass")
        return False

    desktop_dir = home_dir / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_target = desktop_dir / "dfakeseeder.desktop"

    try:
        # Read desktop file
        with open(source_file, "r") as f:
            content = f.read()

        # If using the dev desktop file, update paths
        if source_file == desktop_source:
            # Replace dev-specific Exec with console script
            content = content.replace(
                "Exec=env LOG_LEVEL=DEBUG /usr/bin/python3 dfakeseeder.py",
                "Exec=dfs",
            )
            # Remove dev-specific Path
            lines = content.split("\n")
            content = "\n".join([line for line in lines if not line.startswith("Path=")])

        # Ensure icon name is correct
        if "Icon=" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("Icon="):
                    lines[i] = "Icon=dfakeseeder"
                    break
            content = "\n".join(lines)

        # Write to target
        with open(desktop_target, "w") as f:
            f.write(content)

        # Make desktop file executable
        os.chmod(desktop_target, 0o755)
        logger.trace("✓ Installed desktop file: ...", "UnknownClass")
        return True
    except Exception:
        logger.warning("Warning: Could not install desktop file to ...: ...", "UnknownClass")
        return False


def install_tray_desktop_file(package_dir: Any, home_dir: Any) -> Any:
    """Install tray autostart desktop file."""
    tray_desktop_source = package_dir / "desktop" / "dfakeseeder-tray.desktop"
    if not tray_desktop_source.exists():
        logger.error("Warning: Tray desktop file not found", "UnknownClass")
        return False

    autostart_dir = home_dir / ".config" / "autostart"
    autostart_dir.mkdir(parents=True, exist_ok=True)
    tray_desktop_target = autostart_dir / "dfakeseeder-tray.desktop"

    try:
        # Copy tray desktop file to autostart directory
        shutil.copy2(tray_desktop_source, tray_desktop_target)
        # Make executable
        os.chmod(tray_desktop_target, 0o755)
        logger.trace("✓ Installed tray autostart file", "UnknownClass")
        return True
    except Exception:
        logger.warning("Warning: Could not install tray desktop file", "UnknownClass")
        return False


def update_caches(home_dir: Any) -> None:
    """Update desktop and icon caches."""
    icon_dir = home_dir / ".local" / "share" / "icons" / "hicolor"
    desktop_dir = home_dir / ".local" / "share" / "applications"
    gnome_cache_dir = home_dir / ".cache" / "gnome-shell"

    # Clear GNOME Shell cache to ensure desktop file changes are picked up
    if gnome_cache_dir.exists():
        try:
            shutil.rmtree(gnome_cache_dir)
            logger.trace("✓ Cleared GNOME Shell cache", "UnknownClass")
        except Exception:
            logger.trace(
                "Info: Could not clear GNOME Shell cache (this is optional)",
                "UnknownClass",
            )

    # Update icon cache
    try:
        subprocess.run(["gtk-update-icon-cache", str(icon_dir)], check=False, capture_output=True)
        logger.trace("✓ Updated icon cache", "UnknownClass")
    except FileNotFoundError:
        logger.trace(
            "Info: gtk-update-icon-cache not available (this is optional)",
            "UnknownClass",
        )
    except Exception:
        logger.trace("Info: Could not update icon cache: ...", "UnknownClass")
    # Update desktop database
    try:
        subprocess.run(
            ["update-desktop-database", str(desktop_dir)],
            check=False,
            capture_output=True,
        )
        logger.trace("✓ Updated desktop database", "UnknownClass")
    except FileNotFoundError:
        logger.trace(
            "Info: update-desktop-database not available (this is optional)",
            "UnknownClass",
        )
    except Exception:
        logger.trace("Info: Could not update desktop database: ...", "UnknownClass")


def install_desktop_integration() -> Any:
    """Main function to install desktop integration."""
    logger.trace("Installing D' Fake Seeder desktop integration...", "UnknownClass")
    try:
        package_dir = get_package_dir()
        home_dir = Path.home()
        logger.trace("Package directory: ...", "UnknownClass")
        logger.trace("Home directory: ...", "UnknownClass")
        # Install components
        icons_installed = install_icons(package_dir, home_dir)
        desktop_installed = install_desktop_file(package_dir, home_dir)
        tray_installed = install_tray_desktop_file(package_dir, home_dir)

        if icons_installed or desktop_installed or tray_installed:
            # Update caches
            update_caches(home_dir)
            logger.info("\n✅ Desktop integration installed successfully!", "UnknownClass")
            logger.trace(
                "\nThe application should now appear in your application menu",
                "UnknownClass",
            )
            logger.trace("and show proper icons in the taskbar when launched.", "UnknownClass")
            if tray_installed:
                logger.trace("System tray will start automatically on login.", "UnknownClass")

            # GNOME Shell refresh instructions
            logger.trace(
                "\n⚠️  GNOME Shell users: To ensure changes take effect immediately:",
                "UnknownClass",
            )
            logger.trace(
                "  • Press Alt+F2, type 'r', and press Enter to restart GNOME Shell",
                "UnknownClass",
            )
            logger.trace("  • Or log out and log back in", "UnknownClass")

            logger.trace("\nYou can launch it from:", "UnknownClass")
            logger.trace("  • Application menu (search for 'D' Fake Seeder')", "UnknownClass")
            logger.trace("  • Command line: dfs", "UnknownClass")
            logger.trace("  • Desktop launcher: gtk-launch dfakeseeder", "UnknownClass")
            if tray_installed:
                logger.trace("  • System tray (automatic)", "UnknownClass")
        else:
            logger.error("\n❌ Could not install desktop integration files.", "UnknownClass")
            logger.trace(
                "The application will still work from the command line with 'dfs'",
                "UnknownClass",
            )
    except Exception:
        logger.error("\n❌ Error during desktop integration installation: ...", "UnknownClass")
        logger.trace(
            "The application will still work from the command line with 'dfs'",
            "UnknownClass",
        )
        sys.exit(1)


def uninstall_desktop_integration() -> Any:
    """Remove desktop integration files."""
    logger.trace("Removing D' Fake Seeder desktop integration...", "UnknownClass")
    home_dir = Path.home()
    removed_any = False
    # Remove desktop file
    desktop_file = home_dir / ".local" / "share" / "applications" / "dfakeseeder.desktop"
    if desktop_file.exists():
        try:
            desktop_file.unlink()
            logger.trace("✓ Removed desktop file: ...", "UnknownClass")
            removed_any = True
        except Exception:
            logger.warning("Warning: Could not remove desktop file: ...", "UnknownClass")

    # Remove tray autostart file
    tray_file = home_dir / ".config" / "autostart" / "dfakeseeder-tray.desktop"
    if tray_file.exists():
        try:
            tray_file.unlink()
            logger.trace("✓ Removed tray autostart file", "UnknownClass")
            removed_any = True
        except Exception:
            logger.warning("Warning: Could not remove tray autostart file", "UnknownClass")
    # Remove icons
    icon_base = home_dir / ".local" / "share" / "icons" / "hicolor"
    sizes = DEFAULT_ICON_SIZES
    for size in sizes:
        icon_file = icon_base / size / "apps" / "dfakeseeder.png"
        if icon_file.exists():
            try:
                icon_file.unlink()
                logger.trace("✓ Removed icon: ...", "UnknownClass")
                removed_any = True
            except Exception:
                logger.warning("Warning: Could not remove icon: ...", "UnknownClass")
    if removed_any:
        update_caches(home_dir)
        logger.info("\n✅ Desktop integration removed successfully!", "UnknownClass")
    else:
        logger.trace("\n✓ No desktop integration files found to remove.", "UnknownClass")


def main() -> Any:
    """Command line interface."""
    import argparse

    parser = argparse.ArgumentParser(description="Install or remove D' Fake Seeder desktop integration")
    parser.add_argument(
        "action",
        choices=["install", "uninstall"],
        nargs="?",
        default="install",
        help="Action to perform (default: install)",
    )
    args = parser.parse_args()
    if args.action == "install":
        install_desktop_integration()
    elif args.action == "uninstall":
        uninstall_desktop_integration()


if __name__ == "__main__":
    main()
