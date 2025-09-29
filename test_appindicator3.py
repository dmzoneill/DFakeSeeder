#!/usr/bin/env python3
"""
Test native AppIndicator3 integration with GNOME Shell
This tests the Phase 2 approach using native AppIndicator3
"""

import os
import signal

try:
    import gi

    gi.require_version("Gtk", "3.0")  # AppIndicator3 requires GTK3
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3, GLib, Gtk

    print("✓ Successfully imported AppIndicator3 and GTK3")

    class AppIndicatorTest:
        def __init__(self):
            # Create the indicator
            self.indicator = AppIndicator3.Indicator.new(
                "dfakeseeder-test",  # Unique ID
                "application-default-icon",  # Icon name (will try to load custom later)
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )

            print("✓ AppIndicator3.Indicator created")

            # Set status to active to show the indicator
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            print("✓ Indicator status set to ACTIVE")

            # Try to set a custom icon
            self.set_custom_icon()

            # Create the menu
            self.create_menu()

            print("🎯 AppIndicator should now be visible in your system tray")
            print("🖱️ Try right-clicking the tray icon to see the menu")
            print("⏰ Will run for 30 seconds, then auto-quit")

        def set_custom_icon(self):
            """Try to set a custom icon for the indicator"""
            # Try to find the DFakeSeeder icon
            icon_paths = [
                "/home/daoneill/src/DFakeSeeder/d_fake_seeder/images/dfakeseeder.png",
                "/usr/share/icons/hicolor/48x48/apps/dfakeseeder.png",
                "application-default-icon",  # Fallback
            ]

            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    # For file paths, use set_icon_full
                    self.indicator.set_icon_full(icon_path, "D' Fake Seeder")
                    print(f"✓ Set custom icon: {icon_path}")
                    return

            # Use fallback icon name
            self.indicator.set_icon("application-default-icon")
            print("⚠️ Using fallback icon: application-default-icon")

        def create_menu(self):
            """Create the context menu for the indicator"""
            menu = Gtk.Menu()

            # Show D' Fake Seeder item
            show_item = Gtk.MenuItem(label="Show D' Fake Seeder")
            show_item.connect("activate", self.on_show_window)
            menu.append(show_item)

            # Separator
            separator1 = Gtk.SeparatorMenuItem()
            menu.append(separator1)

            # Status item (disabled)
            status_item = Gtk.MenuItem(label="Status: Running")
            status_item.set_sensitive(False)
            menu.append(status_item)

            # Separator
            separator2 = Gtk.SeparatorMenuItem()
            menu.append(separator2)

            # Quit item
            quit_item = Gtk.MenuItem(label="Quit")
            quit_item.connect("activate", self.on_quit)
            menu.append(quit_item)

            # Show all menu items
            menu.show_all()

            # Set the menu on the indicator
            self.indicator.set_menu(menu)
            print("✓ Menu created and attached to indicator")

        def on_show_window(self, widget):
            """Handle show window request"""
            print("🖥️ Show window requested from AppIndicator menu")

        def on_quit(self, widget):
            """Handle quit request"""
            print("🚪 Quit requested from AppIndicator menu")
            Gtk.main_quit()

        def run(self):
            """Run the indicator"""

            # Set up auto-quit after 30 seconds
            def auto_quit():
                print("⏰ Auto-quitting after 30 seconds...")
                Gtk.main_quit()
                return False  # Don't repeat

            GLib.timeout_add_seconds(30, auto_quit)

            # Handle Ctrl+C gracefully
            signal.signal(signal.SIGINT, lambda s, f: Gtk.main_quit())

            print("🔄 Starting GTK main loop...")
            Gtk.main()
            print("✅ AppIndicator test completed")

    # Create and run the test
    if __name__ == "__main__":
        test = AppIndicatorTest()
        test.run()

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure AppIndicator3 development packages are installed:")
    print("sudo dnf install libappindicator-gtk3-devel gobject-introspection-devel")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
