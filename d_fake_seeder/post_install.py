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

from lib.logger import logger
from lib.util.constants import DEFAULT_ICON_SIZES


def get_package_dir():
    """Get the installed package directory."""
    try:
        import d_fake_seeder

        return Path(d_fake_seeder.__file__).parent
    except ImportError:
        logger.debug("Error: d_fake_seeder package not found. Please install it first.", "UnknownClass")
        sys.exit(1)


def install_icons(package_dir, home_dir):
    """Install application icons to user icon directories."""
    icon_source = package_dir / "images" / "dfakeseeder.png"
    if not icon_source.exists():
        logger.debug("Warning: Icon file not found at ...", "UnknownClass")
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
            logger.debug("✓ Installed icon: ...", "UnknownClass")
            installed_any = True
        except Exception:
            logger.debug("Warning: Could not install icon to ...: ...", "UnknownClass")
    return installed_any


def install_desktop_file(package_dir, home_dir):
    """Install desktop file to user applications directory."""
    desktop_source = package_dir / "dfakeseeder.desktop"
    if not desktop_source.exists():
        logger.debug("Warning: Desktop file not found at ...", "UnknownClass")
        return False
    desktop_dir = home_dir / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    desktop_target = desktop_dir / "dfakeseeder.desktop"
    try:
        # Read and modify desktop file to use correct paths
        with open(desktop_source, "r") as f:
            content = f.read()
        # Update Exec path to use the console script
        content = content.replace(
            'Exec=env LOG_LEVEL=DEBUG bash -c "cd /home/daoneill/src/DFakeSeeder/'
            'd_fake_seeder && pipenv run python3 dfakeseeder.py"',
            "Exec=dfs",
        )
        # Ensure icon name is correct
        if "Icon=" in content:
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("Icon="):
                    lines[i] = "Icon=dfakeseeder"
                    break
            content = "\n".join(lines)
        with open(desktop_target, "w") as f:
            f.write(content)
        # Make desktop file executable
        os.chmod(desktop_target, 0o755)
        logger.debug("✓ Installed desktop file: ...", "UnknownClass")
        return True
    except Exception:
        logger.debug("Warning: Could not install desktop file to ...: ...", "UnknownClass")
        return False


def update_caches(home_dir):
    """Update desktop and icon caches."""
    icon_dir = home_dir / ".local" / "share" / "icons" / "hicolor"
    desktop_dir = home_dir / ".local" / "share" / "applications"
    # Update icon cache
    try:
        subprocess.run(["gtk-update-icon-cache", str(icon_dir)], check=False, capture_output=True)
        logger.debug("✓ Updated icon cache", "UnknownClass")
    except FileNotFoundError:
        logger.debug("Info: gtk-update-icon-cache not available (this is optional)", "UnknownClass")
    except Exception:
        logger.debug("Info: Could not update icon cache: ...", "UnknownClass")
    # Update desktop database
    try:
        subprocess.run(
            ["update-desktop-database", str(desktop_dir)],
            check=False,
            capture_output=True,
        )
        logger.debug("✓ Updated desktop database", "UnknownClass")
    except FileNotFoundError:
        logger.debug("Info: update-desktop-database not available (this is optional)", "UnknownClass")
    except Exception:
        logger.debug("Info: Could not update desktop database: ...", "UnknownClass")


def install_desktop_integration():
    """Main function to install desktop integration."""
    logger.debug("Installing D' Fake Seeder desktop integration...", "UnknownClass")
    try:
        package_dir = get_package_dir()
        home_dir = Path.home()
        logger.debug("Package directory: ...", "UnknownClass")
        logger.debug("Home directory: ...", "UnknownClass")
        # Install components
        icons_installed = install_icons(package_dir, home_dir)
        desktop_installed = install_desktop_file(package_dir, home_dir)
        if icons_installed or desktop_installed:
            # Update caches
            update_caches(home_dir)
            logger.debug("\n✅ Desktop integration installed successfully!", "UnknownClass")
            logger.debug("\nThe application should now appear in your application menu", "UnknownClass")
            logger.debug("and show proper icons in the taskbar when launched.", "UnknownClass")
            logger.debug("\nYou can launch it from:", "UnknownClass")
            logger.debug("  • Application menu (search for 'D' Fake Seeder')", "UnknownClass")
            logger.debug("  • Command line: dfs", "UnknownClass")
            logger.debug("  • Desktop launcher: gtk-launch dfakeseeder", "UnknownClass")
        else:
            logger.debug("\n❌ Could not install desktop integration files.", "UnknownClass")
            logger.debug("The application will still work from the command line with 'dfs'", "UnknownClass")
    except Exception:
        logger.debug("\n❌ Error during desktop integration installation: ...", "UnknownClass")
        logger.debug("The application will still work from the command line with 'dfs'", "UnknownClass")
        sys.exit(1)


def uninstall_desktop_integration():
    """Remove desktop integration files."""
    logger.debug("Removing D' Fake Seeder desktop integration...", "UnknownClass")
    home_dir = Path.home()
    removed_any = False
    # Remove desktop file
    desktop_file = home_dir / ".local" / "share" / "applications" / "dfakeseeder.desktop"
    if desktop_file.exists():
        try:
            desktop_file.unlink()
            logger.debug("✓ Removed desktop file: ...", "UnknownClass")
            removed_any = True
        except Exception:
            logger.debug("Warning: Could not remove desktop file: ...", "UnknownClass")
    # Remove icons
    icon_base = home_dir / ".local" / "share" / "icons" / "hicolor"
    sizes = DEFAULT_ICON_SIZES
    for size in sizes:
        icon_file = icon_base / size / "apps" / "dfakeseeder.png"
        if icon_file.exists():
            try:
                icon_file.unlink()
                logger.debug("✓ Removed icon: ...", "UnknownClass")
                removed_any = True
            except Exception:
                logger.debug("Warning: Could not remove icon: ...", "UnknownClass")
    if removed_any:
        update_caches(home_dir)
        logger.debug("\n✅ Desktop integration removed successfully!", "UnknownClass")
    else:
        logger.debug("\n✓ No desktop integration files found to remove.", "UnknownClass")


def main():
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
