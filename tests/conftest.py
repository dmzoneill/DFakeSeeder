"""
Pytest configuration and shared fixtures for DFakeSeeder tests.

IMPORTANT: NO autouse fixtures!
All fixtures must be explicitly requested in test signatures.
"""

import sys
from pathlib import Path

# Add project root to Python path so tests can import d_fake_seeder
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Create temporary config directory structure.

    Usage: Explicitly request in test signature
    Example: def test_settings(temp_config_dir):
    """
    config_dir = tmp_path / ".config" / "dfakeseeder"
    config_dir.mkdir(parents=True)

    # Create subdirectories
    (config_dir / "torrents").mkdir()
    (config_dir / "logs").mkdir()

    return config_dir


@pytest.fixture
def sample_torrent_file(tmp_path):
    """
    Create a valid sample torrent file.

    Returns: Path to .torrent file with valid bencode data
    """
    torrent_file = tmp_path / "sample.torrent"

    # Create minimal valid torrent file
    import bencodepy
    torrent_data = {
        b'announce': b'http://tracker.example.com:8080/announce',
        b'info': {
            b'name': b'test_file.txt',
            b'piece length': 16384,
            b'pieces': b'\x00' * 20,
            b'length': 1024,
        }
    }

    torrent_file.write_bytes(bencodepy.encode(torrent_data))
    return torrent_file


@pytest.fixture
def mock_settings():
    """
    Create mock AppSettings instance using MagicMock.

    Returns: MagicMock object with common settings attributes
    """
    settings = MagicMock()
    settings.watch_folder = {
        'enabled': True,
        'path': '/tmp/watch',
        'delete_added_torrents': False,
        'auto_start_torrents': True
    }
    settings.peer_protocol = {
        'handshake_timeout_seconds': 30.0,
        'keep_alive_interval_seconds': 120.0
    }
    return settings


@pytest.fixture
def mock_global_peer_manager():
    """
    Create mock GlobalPeerManager using MagicMock.

    Returns: MagicMock object with add_torrent and remove_torrent methods
    """
    manager = MagicMock()
    manager.torrents = {}
    return manager


@pytest.fixture
def mock_model():
    """
    Create mock Model instance using MagicMock.

    Returns: MagicMock object with torrent management methods
    """
    model = MagicMock()
    model.torrents = []
    model.get_torrents.return_value = []
    return model
