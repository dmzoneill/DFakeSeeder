"""
Unit tests for d_fake_seeder.lib.util.column_translations module.

Tests column translation registration and retrieval functionality.
"""

import pytest
from d_fake_seeder.lib.util.column_translations import ColumnTranslations


def test_fallback_function_returns_input():
    """Test that fallback function returns input unchanged"""
    # Arrange
    test_input = "test_string"

    # Act
    result = ColumnTranslations._fallback_function(test_input)

    # Assert
    assert result == test_input


def test_register_translation_function_stores_function():
    """Test that register_translation_function stores the translation function"""
    # Arrange
    def mock_translate(text):
        return f"translated_{text}"

    # Act
    ColumnTranslations.register_translation_function(mock_translate)

    # Assert
    assert ColumnTranslations._translation_function == mock_translate


def test_get_translation_function_returns_registered_function():
    """Test that get_translation_function returns the registered function"""
    # Arrange
    def mock_translate(text):
        return f"translated_{text}"

    ColumnTranslations.register_translation_function(mock_translate)

    # Act
    result = ColumnTranslations._get_translation_function()

    # Assert
    assert result == mock_translate


def test_get_translation_function_returns_fallback_when_none_registered():
    """Test that get_translation_function returns fallback when no function registered"""
    # Arrange - Clear any registered function
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations._get_translation_function()

    # Assert
    assert result == ColumnTranslations._fallback_function


def test_get_torrent_column_translations_returns_dict():
    """Test that get_torrent_column_translations returns a dictionary"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_torrent_column_translations()

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_torrent_column_translations_contains_core_properties():
    """Test that torrent column translations contain core properties"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_torrent_column_translations()

    # Assert
    assert "id" in result
    assert "name" in result
    assert "progress" in result
    assert "total_size" in result
    assert "upload_speed" in result
    assert "download_speed" in result
    assert "seeders" in result
    assert "leechers" in result


def test_get_states_column_translations_returns_dict():
    """Test that get_states_column_translations returns a dictionary"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_states_column_translations()

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_states_column_translations_contains_expected_keys():
    """Test that states column translations contain expected keys"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_states_column_translations()

    # Assert
    assert "tracker" in result
    assert "count" in result
    assert "status" in result


def test_get_peer_column_translations_returns_dict():
    """Test that get_peer_column_translations returns a dictionary"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_peer_column_translations()

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_peer_column_translations_contains_expected_keys():
    """Test that peer column translations contain expected keys"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_peer_column_translations()

    # Assert
    assert "ip" in result
    assert "port" in result
    assert "client" in result
    assert "progress" in result
    assert "down_speed" in result
    assert "up_speed" in result


def test_get_incoming_connections_column_translations_returns_dict():
    """Test that get_incoming_connections_column_translations returns a dictionary"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_incoming_connections_column_translations()

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_incoming_connections_column_translations_contains_expected_keys():
    """Test that incoming connections column translations contain expected keys"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_incoming_connections_column_translations()

    # Assert
    assert "address" in result
    assert "status" in result
    assert "client" in result
    assert "handshake_complete" in result
    assert "bytes_uploaded" in result
    assert "upload_rate" in result


def test_get_outgoing_connections_column_translations_returns_dict():
    """Test that get_outgoing_connections_column_translations returns a dictionary"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_outgoing_connections_column_translations()

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_outgoing_connections_column_translations_contains_expected_keys():
    """Test that outgoing connections column translations contain expected keys"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_outgoing_connections_column_translations()

    # Assert
    assert "address" in result
    assert "status" in result
    assert "client" in result
    assert "handshake_complete" in result
    assert "bytes_downloaded" in result
    assert "download_rate" in result


def test_get_files_column_translations_returns_dict():
    """Test that get_files_column_translations returns a dictionary"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_files_column_translations()

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_files_column_translations_contains_expected_keys():
    """Test that files column translations contain expected keys"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_files_column_translations()

    # Assert
    assert "name" in result
    assert "size" in result
    assert "progress" in result
    assert "priority" in result


def test_get_trackers_column_translations_returns_dict():
    """Test that get_trackers_column_translations returns a dictionary"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_trackers_column_translations()

    # Assert
    assert isinstance(result, dict)
    assert len(result) > 0


def test_get_trackers_column_translations_contains_expected_keys():
    """Test that trackers column translations contain expected keys"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_trackers_column_translations()

    # Assert
    assert "url" in result
    assert "status" in result
    assert "tier" in result
    assert "seeds" in result
    assert "leechers" in result


def test_get_column_title_returns_translated_value_for_known_property():
    """Test that get_column_title returns translated value for known property"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_column_title("torrent", "name")

    # Assert
    # With fallback function, should return the property name
    assert result == "name"


def test_get_column_title_returns_property_name_for_unknown_type():
    """Test that get_column_title returns property name for unknown column type"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_column_title("unknown_type", "some_property")

    # Assert
    assert result == "some_property"


def test_get_column_title_returns_property_name_for_unknown_property():
    """Test that get_column_title returns property name for unknown property"""
    # Arrange
    ColumnTranslations._translation_function = None

    # Act
    result = ColumnTranslations.get_column_title("torrent", "unknown_property")

    # Assert
    assert result == "unknown_property"


def test_get_column_title_uses_custom_translation_function():
    """Test that get_column_title uses custom translation function when registered"""
    # Arrange
    def mock_translate(text):
        return f"TRANSLATED_{text}"

    ColumnTranslations.register_translation_function(mock_translate)

    # Act
    result = ColumnTranslations.get_column_title("torrent", "name")

    # Assert
    assert result == "TRANSLATED_name"


def test_translation_function_affects_all_column_types():
    """Test that registered translation function affects all column type methods"""
    # Arrange
    def mock_translate(text):
        return f"TR_{text}"

    ColumnTranslations.register_translation_function(mock_translate)

    # Act
    torrent_cols = ColumnTranslations.get_torrent_column_translations()
    states_cols = ColumnTranslations.get_states_column_translations()
    peer_cols = ColumnTranslations.get_peer_column_translations()
    files_cols = ColumnTranslations.get_files_column_translations()

    # Assert - All should have translated values
    assert all(value.startswith("TR_") for value in torrent_cols.values())
    assert all(value.startswith("TR_") for value in states_cols.values())
    assert all(value.startswith("TR_") for value in peer_cols.values())
    assert all(value.startswith("TR_") for value in files_cols.values())


def test_fallback_function_is_static_method():
    """Test that fallback function can be called without instance"""
    # Arrange
    test_value = "test"

    # Act
    result = ColumnTranslations._fallback_function(test_value)

    # Assert
    assert result == test_value


def test_register_translation_function_replaces_previous_function():
    """Test that registering a new translation function replaces the previous one"""
    # Arrange
    def first_translate(text):
        return f"first_{text}"

    def second_translate(text):
        return f"second_{text}"

    # Act
    ColumnTranslations.register_translation_function(first_translate)
    assert ColumnTranslations._translation_function == first_translate

    ColumnTranslations.register_translation_function(second_translate)

    # Assert
    assert ColumnTranslations._translation_function == second_translate
    assert ColumnTranslations._translation_function != first_translate
