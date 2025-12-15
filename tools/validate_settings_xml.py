#!/usr/bin/env python3
"""Quick test script to verify settings_generated.xml loads correctly"""

import os
import sys

# Add project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402


def test_settings_xml():
    """Test loading the settings XML file"""
    print("=" * 70)
    print("Testing settings_generated.xml")
    print("=" * 70)

    xml_path = "d_fake_seeder/components/ui/generated/settings_generated.xml"

    # Check file exists
    if not os.path.exists(xml_path):
        print(f"❌ ERROR: File not found: {xml_path}")
        return False

    print(f"✅ File exists: {xml_path}")
    print(f"   File size: {os.path.getsize(xml_path)} bytes")
    print()

    # Try to load with Gtk.Builder
    print("Loading XML with Gtk.Builder...")
    try:
        builder = Gtk.Builder()
        builder.add_from_file(xml_path)
        print("✅ XML loaded successfully")
    except Exception as e:
        print(f"❌ ERROR loading XML: {e}")
        import traceback

        traceback.print_exc()
        return False

    print()

    # Try to get main objects
    print("Checking main objects...")

    # Check main window
    try:
        settings_window = builder.get_object("settings_window")
        if settings_window:
            print(f"✅ settings_window found: {type(settings_window).__name__}")
        else:
            print("❌ ERROR: settings_window is None")
            return False
    except Exception as e:
        print(f"❌ ERROR getting settings_window: {e}")
        return False

    # Check notebook
    try:
        notebook = builder.get_object("settings_notebook")
        if notebook:
            print(f"✅ settings_notebook found: {type(notebook).__name__}")
        else:
            print("⚠️  WARNING: settings_notebook is None")
    except Exception as e:
        print(f"⚠️  WARNING getting settings_notebook: {e}")

    # Check button box
    try:
        button_box = builder.get_object("settings_button_box")
        if button_box:
            print(f"✅ settings_button_box found: {type(button_box).__name__}")
        else:
            print("❌ ERROR: settings_button_box is None")
            return False
    except Exception as e:
        print(f"❌ ERROR getting settings_button_box: {e}")
        return False

    print()

    # Check all four buttons
    print("Checking action buttons...")
    buttons = {
        "settings_reset_button": "Reset to Defaults",
        "settings_cancel_button": "Cancel",
        "settings_apply_button": "Apply",
        "settings_ok_button": "OK",
    }

    all_buttons_found = True
    for button_id, button_label in buttons.items():
        try:
            button = builder.get_object(button_id)
            if button:
                label = button.get_label()
                print(f"✅ {button_id} found: '{label}'")
            else:
                print(f"❌ ERROR: {button_id} is None")
                all_buttons_found = False
        except Exception as e:
            print(f"❌ ERROR getting {button_id}: {e}")
            all_buttons_found = False

    print()
    print("=" * 70)

    if all_buttons_found:
        print("✅ SUCCESS: All components loaded successfully!")
        print("   The settings_generated.xml file is valid and complete.")
        return True
    else:
        print("❌ FAILURE: Some components failed to load")
        return False


if __name__ == "__main__":
    success = test_settings_xml()
    sys.exit(0 if success else 1)
