#!/usr/bin/env python3
"""
Test AppIndicator3 with system Python to verify it works
"""

import os
import signal

try:
    import gi

    gi.require_version("Gtk", "3.0")  # AppIndicator3 requires GTK3
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3, GLib, Gtk

    print("✓ Successfully imported AppIndicator3 and GTK3")

    class SystemTrayTest:
        def __init__(self):
            # Create the indicator
            self.indicator = AppIndicator3.Indicator.new(
                "dfakeseeder-system-test",
                "application-default-icon",
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )

            print("✓ AppIndicator3.Indicator created")

            # Try to set the DFakeSeeder icon
            icon_path = "/home/daoneill/src/DFakeSeeder/d_fake_seeder/images/dfakeseeder.png"
            if os.path.exists(icon_path):
                self.indicator.set_icon_full(icon_path, "D' Fake Seeder")
                print(f"✓ Set custom icon: {icon_path}")
            else:
                self.indicator.set_icon("application-default-icon")
                print("⚠️ Using fallback icon: application-default-icon")

            # Create simple menu
            menu = Gtk.Menu()

            # Test item
            test_item = Gtk.MenuItem(label="✓ Tray is working!")
            test_item.set_sensitive(False)
            menu.append(test_item)

            # Separator
            separator = Gtk.SeparatorMenuItem()
            menu.append(separator)

            # Quit item
            quit_item = Gtk.MenuItem(label="Quit Test")
            quit_item.connect("activate", self.on_quit)
            menu.append(quit_item)

            menu.show_all()
            self.indicator.set_menu(menu)

            # Set status to active to show the indicator
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            print("🎯 AppIndicator should now be visible in your system tray")
            print("🖱️ Right-click the tray icon to see the test menu")
            print("⏰ Will run for 15 seconds, then auto-quit")

        def on_quit(self, widget):
            print("🚪 Quit requested from tray menu")
            Gtk.main_quit()

        def run(self):
            # Set up auto-quit after 15 seconds
            def auto_quit():
                print("⏰ Auto-quitting after 15 seconds...")
                Gtk.main_quit()
                return False

            GLib.timeout_add_seconds(15, auto_quit)

            # Handle Ctrl+C gracefully
            signal.signal(signal.SIGINT, lambda s, f: Gtk.main_quit())

            print("🔄 Starting GTK main loop...")
            Gtk.main()
            print("✅ Tray test completed")

    # Create and run the test
    if __name__ == "__main__":
        test = SystemTrayTest()
        test.run()

except ImportError as e:
    print(f"✗ Import error: {e}")
    print("AppIndicator3 not available - this confirms the issue")
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
