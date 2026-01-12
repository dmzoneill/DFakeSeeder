"""
Test torrent shutdown behavior

Verifies that torrent.stop() handles View.instance being None during shutdown
without raising AttributeError.

This was a bug where View.instance.notify() was called during shutdown after
View.instance had already been set to None, causing:
    AttributeError: 'NoneType' object has no attribute 'notify'

Note: This test is skipped on Python <3.14 due to incompatibility between
MagicMock and typing.ForwardRef in older Python versions.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Skip test on Python < 3.14 due to MagicMock/typing incompatibility
pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="MagicMock causes SyntaxError in typing.ForwardRef on Python < 3.14",
)


@pytest.fixture(autouse=True)
def mock_gtk_modules():
    """Mock GTK and UI modules before any imports."""
    # Store original modules
    original_modules = {}
    modules_to_mock = [
        "gi",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.Gdk",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GioUnix",
        "gi.repository.Adw",
        "d_fake_seeder.components.component.sidebar",
        "d_fake_seeder.components.component.topbar",
        "d_fake_seeder.components.component.mainview",
        "d_fake_seeder.components.component.torrentlist",
        "d_fake_seeder.components.component.statusbar",
        "d_fake_seeder.components.component.infobar",
        "d_fake_seeder.components.component.dialogues",
        "d_fake_seeder.components.component.settings",
        "d_fake_seeder.domain.app_settings",
    ]

    # Save and replace with mocks
    for module_name in modules_to_mock:
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        sys.modules[module_name] = MagicMock()

    # Yield control to the test
    yield

    # Restore original modules
    for module_name in modules_to_mock:
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        elif module_name in sys.modules:
            del sys.modules[module_name]


def test_torrent_shutdown_with_none_view_instance(sample_torrent_file, mock_settings):
    """
    Test that torrent shutdown methods handle View.instance=None gracefully.

    Tests both torrent.stop() and torrent.restart_worker(False) to ensure
    they handle the shutdown state without raising AttributeError.

    Arrange:
        - Create a minimal torrent instance
        - Set View.instance to None (simulating shutdown state)

    Act:
        - Call torrent.stop()
        - Call torrent.restart_worker(False)

    Assert:
        - No AttributeError is raised
        - Torrent stops gracefully
    """
    # Arrange - extend mock_settings with missing fields
    from d_fake_seeder.domain.torrent.torrent import Torrent
    from d_fake_seeder.view import View

    mock_settings.torrents = {}
    mock_settings.threshold = 100
    mock_settings.ui_settings.update(
        {
            "error_sleep_interval_seconds": 5.0,
            "seeder_retry_interval_divisor": 2,
            "async_sleep_interval_seconds": 1.0,
            "seeder_retry_count": 5,
            "speed_variation_min": 0.2,
            "speed_variation_max": 0.8,
        }
    )

    with patch(
        "d_fake_seeder.domain.torrent.torrent.AppSettings.get_instance",
        return_value=mock_settings,
    ):
        # Create torrent instance
        torrent = Torrent(str(sample_torrent_file))

        # Simulate shutdown state - View.instance becomes None
        View.instance = None

        # Act & Assert - test torrent.stop()
        try:
            torrent.stop()
            # If we get here without exception, the fix is working
        except AttributeError as e:
            if "'NoneType' object has no attribute 'notify'" in str(e):
                pytest.fail(f"Bug not fixed in torrent.stop(): {e}")
            else:
                raise  # Re-raise if it's a different AttributeError

        # Act & Assert - test torrent.restart_worker(False)
        try:
            torrent.restart_worker(False)
            # If we get here without exception, the fix is working
        except AttributeError as e:
            if "'NoneType' object has no attribute 'notify'" in str(e):
                pytest.fail(f"Bug not fixed in torrent.restart_worker(): {e}")
            else:
                raise  # Re-raise if it's a different AttributeError
