#!/usr/bin/env python3
"""
Standalone GTK3 Tray Application for DFakeSeeder

This is a simple standalone system tray application using GTK3 and AppIndicator3.
It demonstrates the tray functionality working independently without D-Bus communication.
"""
import argparse
import os
import signal
import sys
from typing import Optional

# Add parent directory to path for imports if needed
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3, GLib, Gtk  # noqa: E402


class StandaloneTrayApp:
    """
    Standalone GTK3 system tray application.

    Provides basic tray functionality with menu without requiring D-Bus communication
    or connection to the main DFakeSeeder application.
    """

    def __init__(self, icon_path: Optional[str] = None, debug: bool = False):
        """
        Initialize standalone tray application.

        Args:
            icon_path: Path to custom tray icon
            debug: Enable debug logging
        """
        self.debug = debug
        self.icon_path = icon_path
        self.indicator: Optional[AppIndicator3.Indicator] = None
        self.menu: Optional[Gtk.Menu] = None

        # Initialize tray indicator
        self.setup_indicator()

        # Set up signal handlers for clean shutdown
        self.setup_signal_handlers()

        if self.debug:
            print("✅ Standalone GTK3 Tray App initialized successfully")

    def setup_indicator(self):
        """Initialize AppIndicator3 system tray."""
        try:
            if self.debug:
                print("🔧 Setting up AppIndicator3...")

            # Create indicator
            self.indicator = AppIndicator3.Indicator.new(
                "dfakeseeder-standalone", self.get_icon_name(), AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )

            # Set icon if custom path provided
            if self.icon_path and os.path.exists(self.icon_path):
                self.indicator.set_icon_full(self.icon_path, "D' Fake Seeder")
                if self.debug:
                    print(f"🎨 Using custom icon: {self.icon_path}")

            # Create menu
            self.create_menu()

            # Activate indicator
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

            if self.debug:
                print("✅ AppIndicator3 tray set up successfully")

        except Exception as e:
            print(f"❌ Error setting up AppIndicator3: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()

    def get_icon_name(self) -> str:
        """Get appropriate icon name for the indicator."""
        # Try to find DFakeSeeder icon, fallback to generic
        possible_icons = ["dfakeseeder", "application-default-icon", "applications-system", "system-run"]

        for icon in possible_icons:
            if Gtk.IconTheme.get_default().has_icon(icon):
                return icon

        return "application-default-icon"

    def create_menu(self):
        """Create context menu for the tray indicator."""
        try:
            self.menu = Gtk.Menu()

            # Show D' Fake Seeder item
            show_item = Gtk.MenuItem(label="Show D' Fake Seeder (Demo)")
            show_item.connect("activate", self.on_show_clicked)
            self.menu.append(show_item)

            # Separator
            separator1 = Gtk.SeparatorMenuItem()
            self.menu.append(separator1)

            # Status item (disabled)
            self.status_item = Gtk.MenuItem(label="Status: Standalone Mode")
            self.status_item.set_sensitive(False)
            self.menu.append(self.status_item)

            # Info item (disabled)
            info_item = Gtk.MenuItem(label="Info: GTK3 Tray Working ✓")
            info_item.set_sensitive(False)
            self.menu.append(info_item)

            # Separator
            separator2 = Gtk.SeparatorMenuItem()
            self.menu.append(separator2)

            # About item
            about_item = Gtk.MenuItem(label="About")
            about_item.connect("activate", self.on_about_clicked)
            self.menu.append(about_item)

            # Quit item
            quit_item = Gtk.MenuItem(label="Quit Tray")
            quit_item.connect("activate", self.on_quit_clicked)
            self.menu.append(quit_item)

            # Show all and attach to indicator
            self.menu.show_all()
            if self.indicator:
                self.indicator.set_menu(self.menu)

            if self.debug:
                print("✅ Tray menu created successfully")

        except Exception as e:
            print(f"❌ Error creating menu: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()

    def on_show_clicked(self, widget):
        """Handle 'Show' menu item click."""
        if self.debug:
            print("📱 Show window requested from tray (demo only)")

        # Create a simple dialog since there's no main app to show
        dialog = Gtk.MessageDialog(
            parent=None, flags=0, message_type=Gtk.MessageType.INFO, buttons=Gtk.ButtonsType.OK, text="GTK3 Tray Demo"
        )
        dialog.format_secondary_text(
            "This is a standalone GTK3 tray application demonstration.\n\n"
            "The tray functionality is working properly with AppIndicator3.\n"
            "In the full implementation, this would communicate with the main GTK4 app via D-Bus."
        )
        dialog.run()
        dialog.destroy()

    def on_about_clicked(self, widget):
        """Handle 'About' menu item click."""
        if self.debug:
            print("ℹ️ About dialog requested from tray")

        about_dialog = Gtk.AboutDialog()
        about_dialog.set_program_name("DFakeSeeder Tray Demo")
        about_dialog.set_version("1.0.0")
        about_dialog.set_comments("Standalone GTK3 system tray demonstration")
        about_dialog.set_copyright("© 2025 DFakeSeeder Project")
        about_dialog.set_website("https://github.com/example/dfakeseeder")
        about_dialog.set_license_type(Gtk.License.APACHE_2_0)

        # Set authors
        about_dialog.set_authors(["DFakeSeeder Development Team"])

        about_dialog.run()
        about_dialog.destroy()

    def on_quit_clicked(self, widget):
        """Handle 'Quit' menu item click."""
        if self.debug:
            print("🚪 Quit requested from tray")

        # Update status before quitting
        if hasattr(self, "status_item") and self.status_item:
            self.status_item.set_label("Status: Shutting down...")

        # Exit after short delay
        GLib.timeout_add(300, self.quit_tray)

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            if self.debug:
                print(f"🔔 Received signal {signum}, shutting down...")
            self.quit_tray()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def quit_tray(self) -> bool:
        """Quit the tray application."""
        try:
            if self.debug:
                print("🧹 Shutting down standalone tray app...")

            Gtk.main_quit()

        except Exception as e:
            print(f"❌ Error during tray shutdown: {e}")

        return False  # Don't repeat if called from timeout

    def run(self):
        """Start the GTK3 main loop."""
        try:
            if self.debug:
                print("🚀 Starting GTK3 tray main loop...")

            Gtk.main()

        except KeyboardInterrupt:
            if self.debug:
                print("⌨️ Keyboard interrupt received")
            self.quit_tray()

        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()


def main():
    """Main entry point for the standalone tray application."""
    parser = argparse.ArgumentParser(description="DFakeSeeder Standalone GTK3 Tray Demo")
    parser.add_argument("--icon", help="Path to custom tray icon")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--dfs-path", help="DFakeSeeder installation path")

    args = parser.parse_args()

    # Set up path if provided
    if args.dfs_path:
        sys.path.insert(0, args.dfs_path)

    try:
        print("🔧 Starting DFakeSeeder Standalone Tray Demo...")

        # Determine icon path
        icon_path = None
        if args.icon:
            icon_path = args.icon
        elif args.dfs_path:
            potential_icon = os.path.join(args.dfs_path, "images", "dfakeseeder.png")
            if os.path.exists(potential_icon):
                icon_path = potential_icon

        # Create and run standalone tray app
        tray_app = StandaloneTrayApp(icon_path=icon_path, debug=args.debug)
        tray_app.run()

    except Exception as e:
        print(f"💥 Fatal error in standalone tray app: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
