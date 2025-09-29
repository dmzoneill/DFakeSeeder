#!/usr/bin/env python3
"""
Test AppIndicator3 with a simple system icon to rule out icon issues
"""

import signal

try:
    import gi

    gi.require_version("Gtk", "3.0")
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3, GLib, Gtk

    print("✓ AppIndicator3 available")

    # Create indicator with a guaranteed system icon
    indicator = AppIndicator3.Indicator.new(
        "test-simple",
        "applications-utilities",  # Standard system icon
        AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
    )

    print("✓ Indicator created with system icon")

    # Create minimal menu
    menu = Gtk.Menu()
    item = Gtk.MenuItem(label="Test Working")
    item.connect("activate", lambda x: Gtk.main_quit())
    menu.append(item)
    menu.show_all()

    indicator.set_menu(menu)
    indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

    print("🎯 Simple tray test should show utilities icon")
    print("⏰ Running for 10 seconds...")

    def auto_quit():
        print("⏰ Auto-quitting...")
        Gtk.main_quit()
        return False

    GLib.timeout_add_seconds(10, auto_quit)
    signal.signal(signal.SIGINT, lambda s, f: Gtk.main_quit())

    Gtk.main()
    print("✅ Simple test completed")

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback

    traceback.print_exc()
