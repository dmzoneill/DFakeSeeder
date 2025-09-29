#!/usr/bin/env python3
"""
GTK3 Tray Subprocess for DFakeSeeder

Standalone GTK3 process that provides system tray functionality
and communicates with main GTK4 process via D-Bus.
"""
import argparse
import os
import signal
import sys
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import gi  # noqa: E402

gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")

from gi.repository import AppIndicator3, GLib, Gtk  # noqa: E402
from lib.component.dbus_manager import DBusClientManager  # noqa: E402


class GTK3TrayClient:
    """
    GTK3 system tray client that communicates with main application via D-Bus.

    Provides AppIndicator3-based system tray with menu and status updates.
    Completely separate from main GTK4 process to avoid version conflicts.
    """

    # D-Bus configuration (matches server)
    SERVICE_NAME = "ie.fio.dfakeseeder"
    OBJECT_PATH = "/ie/fio/dfakeseeder/tray"
    INTERFACE_NAME = "ie.fio.dfakeseeder.Tray"

    def __init__(self, icon_path: Optional[str] = None, debug: bool = False):
        """
        Initialize GTK3 tray client.

        Args:
            icon_path: Path to custom tray icon
            debug: Enable debug logging
        """
        self.debug = debug
        self.icon_path = icon_path
        self.indicator: Optional[AppIndicator3.Indicator] = None
        self.menu: Optional[Gtk.Menu] = None
        self.status_item: Optional[Gtk.MenuItem] = None
        self.dbus_client: Optional[DBusClientManager] = None

        # Initialize D-Bus connection
        self.setup_dbus()

        # Initialize tray indicator
        self.setup_indicator()

        # Set up signal handlers for clean shutdown
        self.setup_signal_handlers()

        if self.debug:
            print("GTK3 Tray Client initialized successfully")

    def setup_dbus(self):
        """Initialize D-Bus client connection."""
        try:
            self.dbus_client = DBusClientManager(self.SERVICE_NAME, self.OBJECT_PATH, self.INTERFACE_NAME)

            # Register signal handlers
            self.dbus_client.register_signal_handler("status_changed", self.on_status_changed)
            self.dbus_client.register_signal_handler("torrent_count_changed", self.on_torrent_count_changed)
            self.dbus_client.register_signal_handler("application_closing", self.on_application_closing)

            # Test connection with ping
            result = self.dbus_client.call_method("ping", "tray_client")
            if result and "Pong" in result:
                if self.debug:
                    print(f"D-Bus connection successful: {result}")
            else:
                print("Warning: D-Bus connection may not be working properly")

        except Exception as e:
            print(f"Error setting up D-Bus: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()

    def setup_indicator(self):
        """Initialize AppIndicator3 system tray."""
        try:
            # Create indicator
            self.indicator = AppIndicator3.Indicator.new(
                "dfakeseeder", self.get_icon_name(), AppIndicator3.IndicatorCategory.APPLICATION_STATUS
            )

            # Set icon if custom path provided
            if self.icon_path and os.path.exists(self.icon_path):
                self.indicator.set_icon_full(self.icon_path, "D' Fake Seeder")
                if self.debug:
                    print(f"Using custom icon: {self.icon_path}")

            # Create menu
            self.create_menu()

            # Activate indicator
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

            if self.debug:
                print("AppIndicator3 tray set up successfully")

        except Exception as e:
            print(f"Error setting up AppIndicator3: {e}")
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
            show_item = Gtk.MenuItem(label="Show D' Fake Seeder")
            show_item.connect("activate", self.on_show_clicked)
            self.menu.append(show_item)

            # Separator
            separator1 = Gtk.SeparatorMenuItem()
            self.menu.append(separator1)

            # Status item (disabled)
            self.status_item = Gtk.MenuItem(label="Status: Connecting...")
            self.status_item.set_sensitive(False)
            self.menu.append(self.status_item)

            # Torrent count item (disabled)
            self.torrent_count_item = Gtk.MenuItem(label="Torrents: --")
            self.torrent_count_item.set_sensitive(False)
            self.menu.append(self.torrent_count_item)

            # Separator
            separator2 = Gtk.SeparatorMenuItem()
            self.menu.append(separator2)

            # Quit item
            quit_item = Gtk.MenuItem(label="Quit")
            quit_item.connect("activate", self.on_quit_clicked)
            self.menu.append(quit_item)

            # Show all and attach to indicator
            self.menu.show_all()
            if self.indicator:
                self.indicator.set_menu(self.menu)

            # Request initial status
            GLib.timeout_add(1000, self.request_initial_status)

            if self.debug:
                print("Tray menu created successfully")

        except Exception as e:
            print(f"Error creating menu: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()

    def request_initial_status(self) -> bool:
        """Request initial status from main application."""
        try:
            if self.dbus_client:
                status = self.dbus_client.call_method("get_status")
                if status:
                    self.update_status_display(status)
                    return False  # Don't repeat timeout

        except Exception as e:
            if self.debug:
                print(f"Error requesting initial status: {e}")

        # Try again in 5 seconds if failed
        return True

    def on_show_clicked(self, widget):
        """Handle 'Show' menu item click."""
        try:
            if self.debug:
                print("Show window requested from tray")

            if self.dbus_client:
                result = self.dbus_client.call_method("show_window")
                if self.debug and result:
                    print(f"Show window result: {result}")

        except Exception as e:
            print(f"Error showing window: {e}")

    def on_quit_clicked(self, widget):
        """Handle 'Quit' menu item click."""
        try:
            if self.debug:
                print("Quit requested from tray")

            if self.dbus_client:
                result = self.dbus_client.call_method("quit_application")
                if self.debug and result:
                    print(f"Quit result: {result}")

            # Exit tray process after short delay
            GLib.timeout_add(500, self.quit_tray)

        except Exception as e:
            print(f"Error quitting application: {e}")
            self.quit_tray()

    def on_status_changed(self, new_status):
        """Handle status change signal from main application."""
        if self.debug:
            print(f"Status changed signal received: {new_status}")

        GLib.idle_add(self.update_status_display, new_status)

    def on_torrent_count_changed(self, count_info):
        """Handle torrent count change signal from main application."""
        if self.debug:
            print(f"Torrent count changed signal received: {count_info}")

        GLib.idle_add(self.update_torrent_count_display, count_info)

    def on_application_closing(self):
        """Handle application closing signal from main application."""
        if self.debug:
            print("Application closing signal received")

        GLib.idle_add(self.quit_tray)

    def update_status_display(self, status_text: str):
        """Update status display in menu."""
        try:
            if self.status_item:
                self.status_item.set_label(f"Status: {status_text}")

        except Exception as e:
            if self.debug:
                print(f"Error updating status display: {e}")

    def update_torrent_count_display(self, count_info: str):
        """Update torrent count display in menu."""
        try:
            if hasattr(self, "torrent_count_item") and self.torrent_count_item:
                self.torrent_count_item.set_label(f"Torrents: {count_info}")

        except Exception as e:
            if self.debug:
                print(f"Error updating torrent count display: {e}")

    def setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown."""

        def signal_handler(signum, frame):
            if self.debug:
                print(f"Received signal {signum}, shutting down...")
            self.quit_tray()

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    def quit_tray(self) -> bool:
        """Quit the tray application."""
        try:
            if self.debug:
                print("Shutting down tray client...")

            if self.dbus_client:
                self.dbus_client.disconnect()

            Gtk.main_quit()

        except Exception as e:
            print(f"Error during tray shutdown: {e}")

        return False  # Don't repeat if called from timeout

    def run(self):
        """Start the GTK3 main loop."""
        try:
            if self.debug:
                print("Starting GTK3 tray main loop...")

            Gtk.main()

        except KeyboardInterrupt:
            if self.debug:
                print("Keyboard interrupt received")
            self.quit_tray()

        except Exception as e:
            print(f"Error in main loop: {e}")
            if self.debug:
                import traceback

                traceback.print_exc()


def main():
    """Main entry point for the tray subprocess."""
    parser = argparse.ArgumentParser(description="DFakeSeeder GTK3 Tray Client")
    parser.add_argument("--icon", help="Path to custom tray icon")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--dfs-path", help="DFakeSeeder installation path")
    parser.add_argument("--test-mode", action="store_true", help="Test mode - check dependencies and exit")

    args = parser.parse_args()

    # Test mode - just check if dependencies are available
    if args.test_mode:
        try:
            # Test GTK3 and AppIndicator3 imports
            import gi

            gi.require_version("Gtk", "3.0")
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3, Gtk  # noqa: F401

            print("GTK3 and AppIndicator3 dependencies available")
            sys.exit(0)
        except Exception as e:
            print(f"Dependencies not available: {e}")
            sys.exit(1)

    # Set up path if provided
    if args.dfs_path:
        sys.path.insert(0, args.dfs_path)

    try:
        # Create and run tray client
        tray_client = GTK3TrayClient(icon_path=args.icon, debug=args.debug)
        tray_client.run()

    except Exception as e:
        print(f"Fatal error in tray client: {e}")
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
