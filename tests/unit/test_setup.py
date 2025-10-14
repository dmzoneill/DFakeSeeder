"""
Basic setup verification tests

These tests verify that the test infrastructure is working correctly.
"""


def test_pytest_is_working():
    """Test that pytest is configured and running correctly."""
    # Arrange
    expected = True

    # Act
    result = True

    # Assert
    assert result == expected


def test_temp_config_dir_fixture(temp_config_dir):
    """Test that temp_config_dir fixture works correctly."""
    # Arrange - fixture provides temp_config_dir
    torrents_dir = temp_config_dir / "torrents"

    # Act - check directories exist
    config_exists = temp_config_dir.exists()
    torrents_exists = torrents_dir.exists()

    # Assert
    assert config_exists
    assert torrents_exists
    assert temp_config_dir.is_dir()


def test_sample_torrent_file_fixture(sample_torrent_file):
    """Test that sample_torrent_file fixture works correctly."""
    # Arrange - fixture provides sample_torrent_file

    # Act - check file exists and has content
    file_exists = sample_torrent_file.exists()
    file_size = sample_torrent_file.stat().st_size

    # Assert
    assert file_exists
    assert file_size > 0
    assert sample_torrent_file.suffix == ".torrent"


def test_mock_settings_fixture(mock_settings):
    """Test that mock_settings fixture works correctly."""
    # Arrange - fixture provides mock_settings

    # Act - access mock attributes
    tickspeed = mock_settings.tickspeed
    language = mock_settings.language

    # Assert
    assert tickspeed == 10
    assert language == "en"
    assert hasattr(mock_settings, "peer_protocol")


def test_mock_model_fixture(mock_model):
    """Test that mock_model fixture works correctly."""
    # Arrange - fixture provides mock_model

    # Act - access mock attributes
    torrent_list = mock_model.torrent_list
    translate_func = mock_model.get_translate_func()

    # Assert
    assert torrent_list == []
    assert translate_func("test") == "test"
    assert hasattr(mock_model, "translation_manager")


def test_mock_global_peer_manager_fixture(mock_global_peer_manager):
    """Test that mock_global_peer_manager fixture works correctly."""
    # Arrange - fixture provides mock_global_peer_manager

    # Act - call mock methods
    connection_count = mock_global_peer_manager.get_global_connection_count()
    active_count = mock_global_peer_manager.get_global_active_connection_count()

    # Assert
    assert connection_count == 0
    assert active_count == 0
    assert hasattr(mock_global_peer_manager, "connection_manager")


def test_mock_data_import():
    """Test that mock_data module can be imported."""
    # Arrange & Act
    import sys
    from pathlib import Path

    test_dir = Path(__file__).parent.parent
    if str(test_dir) not in sys.path:
        sys.path.insert(0, str(test_dir))

    from fixtures import mock_data

    # Assert
    assert hasattr(mock_data, "SAMPLE_TORRENT_DICT")
    assert hasattr(mock_data, "SAMPLE_TRACKER_RESPONSE")
    assert hasattr(mock_data, "SAMPLE_SETTINGS")


def test_common_fixtures_import():
    """Test that common_fixtures module can be imported."""
    # Arrange & Act
    import sys
    from pathlib import Path

    test_dir = Path(__file__).parent.parent
    if str(test_dir) not in sys.path:
        sys.path.insert(0, str(test_dir))

    from fixtures import common_fixtures

    # Assert
    assert hasattr(common_fixtures, "sample_torrent_metadata")
    assert hasattr(common_fixtures, "sample_peer_data")
