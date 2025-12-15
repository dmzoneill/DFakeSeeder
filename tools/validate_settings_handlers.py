#!/usr/bin/env python3
"""
Validate Settings Handler Coverage

This script validates that all settings tabs have proper handler coverage.
Run with: DFS_DEBUG_HANDLERS=true python3 validate_settings_handlers.py

Or programmatically call print_coverage_report() on any tab.
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_tab_coverage(tab_name: str, tab_class, ui_file: str):
    """Validate a single tab's handler coverage."""
    from gi.repository import Gtk

    from d_fake_seeder.domain.app_settings import AppSettings

    # Create builder and load UI
    builder = Gtk.Builder()
    try:
        builder.add_from_file(ui_file)
    except Exception as e:
        print(f"❌ {tab_name}: Failed to load UI file: {e}")
        return None

    # Create mock app_settings
    app_settings = AppSettings()

    # Instantiate tab
    try:
        tab = tab_class(builder, app_settings)

        # Initialize the tab (this triggers auto-connect and validation)
        tab.ensure_initialized()

        # Get coverage report
        report = tab.validate_handler_coverage()

        return report

    except Exception as e:
        print(f"❌ {tab_name}: Failed to instantiate: {e}")
        import traceback

        traceback.print_exc()
        return None


def main():
    """Main validation function."""

    print("=" * 70)
    print("Settings Handler Coverage Validation")
    print("=" * 70)
    print()

    # Import tabs
    try:
        from d_fake_seeder.components.component.settings import (
            BitTorrentTab,
            ConnectionTab,
            DHTTab,
            GeneralTab,
            ProtocolExtensionsTab,
            SimulationTab,
            SpeedTab,
            WebUITab,
        )
    except ImportError as e:
        print(f"❌ Failed to import tabs: {e}")
        return 1

    # Define tabs to validate
    tabs = [
        ("Speed", SpeedTab, "d_fake_seeder/ui/settings/speed.xml"),
        ("Connection", ConnectionTab, "d_fake_seeder/ui/settings/connection.xml"),
        ("BitTorrent", BitTorrentTab, "d_fake_seeder/ui/settings/bittorrent.xml"),
        ("General", GeneralTab, "d_fake_seeder/ui/settings/general.xml"),
        ("DHT", DHTTab, "d_fake_seeder/ui/settings/dht.xml"),
        ("Protocol Extensions", ProtocolExtensionsTab, "d_fake_seeder/ui/settings/protocol_extensions.xml"),
        ("Simulation", SimulationTab, "d_fake_seeder/ui/settings/simulation.xml"),
        ("WebUI", WebUITab, "d_fake_seeder/ui/settings/webui.xml"),
    ]

    all_passed = True
    total_missing = 0
    results = []

    for name, TabClass, ui_file in tabs:
        report = validate_tab_coverage(name, TabClass, ui_file)

        if report is None:
            all_passed = False
            continue

        results.append((name, report))

        status = "✅" if not report["missing_handlers"] else "⚠️ "
        coverage = report["coverage_percent"]

        print(
            f"{status} {name:<20} Coverage: {coverage:>5.1f}%  "
            f"({report['connected_widgets']}/{report['interactive_widgets']} widgets)"
        )

        if report["missing_handlers"]:
            all_passed = False
            total_missing += len(report["missing_handlers"])

            # Show first 3 missing handlers
            for missing in report["missing_handlers"][:3]:
                print(f"     • {missing['id']}")

            if len(report["missing_handlers"]) > 3:
                print(f"     ... and {len(report['missing_handlers']) - 3} more")

    print()
    print("=" * 70)

    if all_passed:
        print("✅ ALL TABS PASSED - 100% handler coverage!")
        print("=" * 70)
        return 0
    else:
        print(f"⚠️  INCOMPLETE COVERAGE - {total_missing} widgets missing handlers")
        print()
        print("To enable automatic validation during development, run:")
        print("  export DFS_DEBUG_HANDLERS=true")
        print("  make run-debug")
        print("=" * 70)
        return 0  # Don't fail, just warn


if __name__ == "__main__":
    # Enable GTK
    import gi

    gi.require_version("Gtk", "4.0")

    sys.exit(main())
