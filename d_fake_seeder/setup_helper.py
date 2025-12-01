"""Setup helper for post-installation tasks."""

import subprocess
import sys
from pathlib import Path


def check_system_dependencies():
    """Check if required system dependencies are installed."""
    dependencies = {
        "GTK4": ["pkg-config", "--exists", "gtk4"],
        "LibAdwaita": ["pkg-config", "--exists", "libadwaita-1"],
        "PyGObject": None,  # Checked via Python import
    }

    missing = []

    # Check GTK4
    try:
        subprocess.run(dependencies["GTK4"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("GTK4")

    # Check LibAdwaita
    try:
        subprocess.run(dependencies["LibAdwaita"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        missing.append("LibAdwaita")

    # Check PyGObject
    try:
        import gi

        gi.require_version("Gtk", "4.0")
    except (ImportError, ValueError):
        missing.append("PyGObject/GObject Introspection")

    return missing


def print_installation_guide(missing_deps):
    """Print installation guide for missing dependencies."""
    print("\n" + "=" * 60)
    print("D' Fake Seeder - Post-Installation Setup")
    print("=" * 60)

    if missing_deps:
        print("\n⚠️  SYSTEM DEPENDENCIES REQUIRED")
        print("\nThe following system packages are missing:")
        for dep in missing_deps:
            print(f"  ❌ {dep}")

        print("\n📦 Installation Instructions:\n")

        # Detect OS and provide specific instructions
        if Path("/etc/fedora-release").exists():
            print("Fedora/RHEL:")
            print("  sudo dnf install gtk4 libadwaita python3-gobject")
        elif Path("/etc/debian_version").exists():
            print("Debian/Ubuntu:")
            print("  sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1")
        elif Path("/etc/arch-release").exists():
            print("Arch Linux:")
            print("  sudo pacman -S gtk4 libadwaita python-gobject")
        else:
            print("Please install these packages using your system package manager:")
            print("  - GTK4")
            print("  - LibAdwaita")
            print("  - PyGObject (GObject Introspection)")

        print("\n" + "=" * 60)
        return False
    else:
        print("\n✅ All system dependencies are installed!")
        print("\n" + "=" * 60)
        return True


def offer_desktop_integration():
    """Offer to install desktop integration."""
    print("\n🖥️  DESKTOP INTEGRATION")
    print("\nWould you like to install desktop integration?")
    print("This will add:")
    print("  • Application menu entry")
    print("  • Desktop icon")
    print("  • System tray support")

    # Check if running interactively
    if sys.stdin.isatty():
        try:
            response = input("\nInstall desktop integration? [Y/n]: ").strip().lower()
            if response in ("", "y", "yes"):
                return True
        except (KeyboardInterrupt, EOFError):
            print()
            return False

    # Non-interactive - show manual command
    print("\nTo install desktop integration later, run:")
    print("  dfs-install-desktop")
    return False


def run_desktop_integration():
    """Run desktop integration installation."""
    try:
        from d_fake_seeder.post_install import install_desktop_integration

        print("\nInstalling desktop integration...")
        install_desktop_integration()
        print("✅ Desktop integration installed successfully!")
        return True
    except Exception as e:
        print(f"⚠️  Desktop integration failed: {e}")
        print("You can try again later with: dfs-install-desktop")
        return False


def post_install_setup():
    """Run post-installation setup tasks."""
    print("\n" + "=" * 60)
    print("Setting up D' Fake Seeder...")
    print("=" * 60 + "\n")

    # Check system dependencies
    missing = check_system_dependencies()
    deps_ok = print_installation_guide(missing)

    if not deps_ok:
        print("\n⚠️  Please install missing dependencies before running the application.")
        print("=" * 60 + "\n")
        return

    # Offer desktop integration
    if offer_desktop_integration():
        run_desktop_integration()

    # Show launch instructions
    print("\n" + "=" * 60)
    print("🚀 LAUNCH INSTRUCTIONS")
    print("=" * 60)
    print("\nYou can now launch D' Fake Seeder:")
    print("  • Command line: dfs  or  dfakeseeder")
    print("  • With tray: dfs --with-tray")
    print("  • Application menu: Search 'D' Fake Seeder'")
    print("\nConfiguration will be created at:")
    print("  ~/.config/dfakeseeder/settings.json")
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    post_install_setup()
