"""
Test torrent shutdown behavior

Verifies that torrent.stop() handles View.instance being None during shutdown
without raising AttributeError.

This was a bug where View.instance.notify() was called during shutdown after
View.instance had already been set to None, causing:
    AttributeError: 'NoneType' object has no attribute 'notify'
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

# Mock gi module and all GTK/UI components before any imports that use them
gi_mock = MagicMock()
sys.modules["gi"] = gi_mock
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.Gio"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.GioUnix"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()

# Mock UI components that view.py imports
sys.modules["d_fake_seeder.components.component.sidebar"] = MagicMock()
sys.modules["d_fake_seeder.components.component.topbar"] = MagicMock()
sys.modules["d_fake_seeder.components.component.mainview"] = MagicMock()
sys.modules["d_fake_seeder.components.component.torrentlist"] = MagicMock()
sys.modules["d_fake_seeder.components.component.statusbar"] = MagicMock()
sys.modules["d_fake_seeder.components.component.infobar"] = MagicMock()
sys.modules["d_fake_seeder.components.component.dialogues"] = MagicMock()
sys.modules["d_fake_seeder.components.component.settings"] = MagicMock()

# Mock AppSettings module before it gets imported
mock_app_settings = MagicMock()
mock_app_settings.get_instance = MagicMock()
sys.modules["d_fake_seeder.domain.app_settings"] = MagicMock(AppSettings=mock_app_settings)


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
