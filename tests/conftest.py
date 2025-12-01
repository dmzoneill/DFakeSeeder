"""
Root conftest.py for DFakeSeeder test suite

Provides base fixtures and configuration for all tests according to TESTING_PLAN.md:
- NO test classes (use standalone functions)
- NO autouse fixtures (all fixtures must be explicitly requested)
- Use unittest.mock.patch via mocker fixture (NOT monkeypatch)
- Use real filesystem with tmp_path (NOT pyfakefs)
- 100ms timeout for unit tests
- Standalone test functions with Arrange-Act-Assert pattern
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Create a temporary configuration directory for tests.

    Uses pytest's tmp_path (real filesystem) NOT pyfakefs.
    Each test gets an isolated config directory that is automatically cleaned up.

    Returns:
        Path: Temporary directory for configuration files
    """
    # Arrange - create config structure
    config_dir = tmp_path / "dfakeseeder"
    config_dir.mkdir()
    torrents_dir = config_dir / "torrents"
    torrents_dir.mkdir()

    return config_dir


@pytest.fixture
def sample_torrent_file(tmp_path):
    """
    Create a minimal valid torrent file for testing.

    Uses bencodepy to generate valid torrent data.

    Returns:
        Path: Path to the generated torrent file
    """
    # Arrange - create minimal torrent structure
    torrent_data = {
        "announce": "http://tracker.example.com:6969/announce",
        "info": {
            "name": "test_torrent",
            "piece length": 16384,
            "pieces": b"\x00" * 20,  # Single piece hash (20 bytes)
            "length": 1024,  # Single file torrent
        },
    }

    # Use bencodepy to encode
    try:
        import bencodepy

        encoded = bencodepy.encode(torrent_data)
    except ImportError:
        # Fallback to manual bencoding if bencodepy not available
        # Simple bencoding implementation for test purposes
        def bencode(obj):
            if isinstance(obj, int):
                return f"i{obj}e".encode()
            elif isinstance(obj, bytes):
                return f"{len(obj)}:".encode() + obj
            elif isinstance(obj, str):
                return f"{len(obj)}:{obj}".encode()
            elif isinstance(obj, list):
                return b"l" + b"".join(bencode(item) for item in obj) + b"e"
            elif isinstance(obj, dict):
                items = []
                for key in sorted(obj.keys()):
                    items.append(bencode(key))
                    items.append(bencode(obj[key]))
                return b"d" + b"".join(items) + b"e"

        encoded = bencode(torrent_data)

    # Act - write to file
    torrent_path = tmp_path / "test.torrent"
    torrent_path.write_bytes(encoded)

    return torrent_path


# =============================================================================
# Mock Fixtures (using unittest.mock NOT monkeypatch)
# =============================================================================


@pytest.fixture
def mock_settings():
    """
    Create a mock AppSettings instance for testing.

    Uses unittest.mock.MagicMock (NOT monkeypatch).
    Provides common settings attributes with sensible defaults.

    Returns:
        MagicMock: Mock AppSettings object with default attributes
    """
    # Arrange - create mock with common attributes
    settings = MagicMock()
    settings.tickspeed = 10
    settings.language = "en"
    settings.listening_port = 6881
    settings.max_incoming_connections = 100
    settings.max_outgoing_connections = 100
    settings.enable_dht = True
    settings.enable_pex = True
    settings.upload_speed = 50
    settings.download_speed = 500
    settings.announce_interval = 1800

    # Mock nested settings
    settings.peer_protocol = {
        "handshake_timeout_seconds": 30.0,
        "message_read_timeout_seconds": 60.0,
        "keep_alive_interval_seconds": 120.0,
    }

    settings.ui_settings = {
        "splash_display_duration_seconds": 2,
        "notification_timeout_min_ms": 2000,
    }

    return settings


@pytest.fixture
def mock_global_peer_manager():
    """
    Create a mock GlobalPeerManager instance for testing.

    Uses unittest.mock.MagicMock (NOT monkeypatch).

    Returns:
        MagicMock: Mock GlobalPeerManager object
    """
    # Arrange - create mock
    manager = MagicMock()
    manager.connection_manager = MagicMock()
    manager.get_global_connection_count.return_value = 0
    manager.get_global_active_connection_count.return_value = 0

    return manager


@pytest.fixture
def mock_model():
    """
    Create a mock Model instance for testing.

    Uses unittest.mock.MagicMock (NOT monkeypatch).

    Returns:
        MagicMock: Mock Model object
    """
    # Arrange - create mock
    model = MagicMock()
    model.torrent_list = []
    model.torrent_list_attributes = MagicMock()
    model.translation_manager = MagicMock()
    model.get_translate_func.return_value = lambda x: x

    return model


# =============================================================================
# Environment Cleanup
# =============================================================================


@pytest.fixture
def clean_environment(monkeypatch):
    """
    Clean environment variables that might interfere with tests.

    Note: This is one of the few cases where monkeypatch is acceptable,
    as it's cleaning up environment state, not mocking behavior.

    Returns:
        None
    """
    # Arrange - remove DFakeSeeder environment variables
    env_vars = ["DFS_PATH", "DFS_SETTINGS", "DFS_LOG_LEVEL"]
    for var in env_vars:
        monkeypatch.delenv(var, raising=False)


# =============================================================================
# Test Utilities
# =============================================================================


def create_test_settings_file(config_dir: Path, settings: dict = None):
    """
    Helper function to create a settings.json file in the config directory.

    Args:
        config_dir: Path to configuration directory
        settings: Dictionary of settings to write (uses defaults if None)

    Returns:
        Path: Path to the created settings file
    """
    # Arrange - default settings if none provided
    if settings is None:
        settings = {
            "language": "en",
            "tickspeed": 10,
            "listening_port": 6881,
            "upload_speed": 50,
            "download_speed": 500,
        }

    # Act - write settings file
    settings_file = config_dir / "settings.json"
    settings_file.write_text(json.dumps(settings, indent=4))

    return settings_file


# =============================================================================
# Pytest Hooks
# =============================================================================


def pytest_configure(config):
    """
    Pytest configuration hook.

    Registers custom markers and sets up test environment.
    """
    # Register custom markers (prevents warnings about unknown markers)
    config.addinivalue_line("markers", "unit: Unit tests (fast, isolated, <100ms)")
    config.addinivalue_line("markers", "integration: Integration tests (slower, multi-component)")
    config.addinivalue_line("markers", "slow: Tests that take >1 second")
    config.addinivalue_line("markers", "requires_gtk: Tests requiring GTK initialization")
    config.addinivalue_line("markers", "requires_network: Tests requiring network access")
