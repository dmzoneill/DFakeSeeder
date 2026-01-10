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
sys.modules['gi'] = gi_mock
sys.modules['gi.repository'] = MagicMock()
sys.modules['gi.repository.Gtk'] = MagicMock()
sys.modules['gi.repository.Gdk'] = MagicMock()
sys.modules['gi.repository.Gio'] = MagicMock()
sys.modules['gi.repository.GLib'] = MagicMock()
sys.modules['gi.repository.GioUnix'] = MagicMock()
sys.modules['gi.repository.Adw'] = MagicMock()

# Mock UI components that view.py imports
sys.modules['d_fake_seeder.components.component.sidebar'] = MagicMock()
sys.modules['d_fake_seeder.components.component.topbar'] = MagicMock()
sys.modules['d_fake_seeder.components.component.mainview'] = MagicMock()
sys.modules['d_fake_seeder.components.component.torrentlist'] = MagicMock()
sys.modules['d_fake_seeder.components.component.statusbar'] = MagicMock()
sys.modules['d_fake_seeder.components.component.infobar'] = MagicMock()
sys.modules['d_fake_seeder.components.component.dialogues'] = MagicMock()
sys.modules['d_fake_seeder.components.component.settings'] = MagicMock()

# Mock AppSettings module before it gets imported
mock_app_settings = MagicMock()
mock_app_settings.get_instance = MagicMock()
sys.modules['d_fake_seeder.domain.app_settings'] = MagicMock(AppSettings=mock_app_settings)


def test_torrent_stop_with_none_view_instance(tmp_path, monkeypatch):
    """
    Test that torrent.stop() handles View.instance=None gracefully.

    Arrange:
        - Create a minimal torrent instance
        - Set View.instance to None (simulating shutdown state)

    Act:
        - Call torrent.stop()

    Assert:
        - No AttributeError is raised
        - Torrent stops gracefully
    """
    # Arrange - create minimal torrent file
    from d_fake_seeder.domain.torrent.torrent import Torrent
    from d_fake_seeder.view import View

    torrent_data = {
        "announce": "http://tracker.example.com:6969/announce",
        "info": {
            "name": "test_torrent",
            "piece length": 16384,
            "pieces": b"\\x00" * 20,
            "length": 1024,
        },
    }

    # Create torrent file
    try:
        import bencodepy

        encoded = bencodepy.encode(torrent_data)
    except ImportError:
        # Fallback bencoding
        def bencode(obj):
            if isinstance(obj, int):
                return f"i{obj}e".encode()
            elif isinstance(obj, bytes):
                return f"{len(obj)}:".encode() + obj
            elif isinstance(obj, str):
                return f"{len(obj)}:{obj}".encode()
            elif isinstance(obj, dict):
                items = []
                for key in sorted(obj.keys()):
                    items.append(bencode(key))
                    items.append(bencode(obj[key]))
                return b"d" + b"".join(items) + b"e"

        encoded = bencode(torrent_data)

    torrent_path = tmp_path / "test.torrent"
    torrent_path.write_bytes(encoded)

    # Mock AppSettings to avoid file system dependencies
    mock_settings = MagicMock()
    mock_settings.torrents = {}
    mock_settings.upload_speed = 50
    mock_settings.download_speed = 500
    mock_settings.announce_interval = 1800
    mock_settings.threshold = 100
    mock_settings.tickspeed = 10
    mock_settings.ui_settings = {
        "error_sleep_interval_seconds": 5.0,
        "seeder_retry_interval_divisor": 2,
        "async_sleep_interval_seconds": 1.0,
        "seeder_retry_count": 5,
    }

    with patch(
        "d_fake_seeder.domain.torrent.torrent.AppSettings.get_instance",
        return_value=mock_settings,
    ):
        # Create torrent instance
        torrent = Torrent(str(torrent_path))

        # Simulate shutdown state - View.instance becomes None
        View.instance = None

        # Act & Assert - should not raise AttributeError
        try:
            torrent.stop()
            # If we get here without exception, the fix is working
            assert True
        except AttributeError as e:
            if "'NoneType' object has no attribute 'notify'" in str(e):
                pytest.fail(f"Bug not fixed: {e}")
            else:
                raise  # Re-raise if it's a different AttributeError


def test_torrent_restart_worker_with_none_view_instance(tmp_path):
    """
    Test that torrent.restart_worker() handles View.instance=None gracefully.

    Arrange:
        - Create a minimal torrent instance
        - Set View.instance to None (simulating shutdown state)

    Act:
        - Call torrent.restart_worker(False) to stop workers

    Assert:
        - No AttributeError is raised
        - Workers stop gracefully
    """
    # Arrange
    from d_fake_seeder.domain.torrent.torrent import Torrent
    from d_fake_seeder.view import View

    torrent_data = {
        "announce": "http://tracker.example.com:6969/announce",
        "info": {
            "name": "test_torrent",
            "piece length": 16384,
            "pieces": b"\\x00" * 20,
            "length": 1024,
        },
    }

    # Create torrent file
    try:
        import bencodepy

        encoded = bencodepy.encode(torrent_data)
    except ImportError:
        # Fallback bencoding
        def bencode(obj):
            if isinstance(obj, int):
                return f"i{obj}e".encode()
            elif isinstance(obj, bytes):
                return f"{len(obj)}:".encode() + obj
            elif isinstance(obj, str):
                return f"{len(obj)}:{obj}".encode()
            elif isinstance(obj, dict):
                items = []
                for key in sorted(obj.keys()):
                    items.append(bencode(key))
                    items.append(bencode(obj[key]))
                return b"d" + b"".join(items) + b"e"

        encoded = bencode(torrent_data)

    torrent_path = tmp_path / "test.torrent"
    torrent_path.write_bytes(encoded)

    # Mock AppSettings
    mock_settings = MagicMock()
    mock_settings.torrents = {}
    mock_settings.upload_speed = 50
    mock_settings.download_speed = 500
    mock_settings.announce_interval = 1800
    mock_settings.threshold = 100
    mock_settings.tickspeed = 10
    mock_settings.ui_settings = {
        "error_sleep_interval_seconds": 5.0,
        "seeder_retry_interval_divisor": 2,
        "async_sleep_interval_seconds": 1.0,
        "seeder_retry_count": 5,
    }

    with patch(
        "d_fake_seeder.domain.torrent.torrent.AppSettings.get_instance",
        return_value=mock_settings,
    ):
        # Create torrent instance
        torrent = Torrent(str(torrent_path))

        # Simulate shutdown state - View.instance becomes None
        View.instance = None

        # Act & Assert - should not raise AttributeError
        try:
            torrent.restart_worker(False)  # Stop workers
            # If we get here without exception, the fix is working
            assert True
        except AttributeError as e:
            if "'NoneType' object has no attribute 'notify'" in str(e):
                pytest.fail(f"Bug not fixed: {e}")
            else:
                raise  # Re-raise if it's a different AttributeError
