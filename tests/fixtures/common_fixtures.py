"""
Common reusable fixtures for DFakeSeeder tests

Provides frequently used fixtures that can be imported by test modules.
All fixtures follow TESTING_PLAN.md guidelines:
- NO autouse fixtures
- Use unittest.mock.MagicMock (NOT monkeypatch for mocking)
- Real filesystem with tmp_path (NOT pyfakefs)
"""

import pytest

# =============================================================================
# Torrent Fixtures
# =============================================================================


@pytest.fixture
def sample_torrent_metadata():
    """
    Provide sample torrent metadata for testing.

    Returns:
        dict: Sample torrent metadata dictionary
    """
    from tests.fixtures.mock_data import SAMPLE_TORRENT_DICT

    return SAMPLE_TORRENT_DICT.copy()


@pytest.fixture
def multi_file_torrent_metadata():
    """
    Provide sample multi-file torrent metadata for testing.

    Returns:
        dict: Sample multi-file torrent metadata dictionary
    """
    from tests.fixtures.mock_data import SAMPLE_MULTI_FILE_TORRENT_DICT

    return SAMPLE_MULTI_FILE_TORRENT_DICT.copy()


# =============================================================================
# Peer Fixtures
# =============================================================================


@pytest.fixture
def sample_peer_data():
    """
    Provide sample peer data for testing.

    Returns:
        dict: Sample peer data dictionary
    """
    from tests.fixtures.mock_data import SAMPLE_PEER_DATA

    return SAMPLE_PEER_DATA.copy()


@pytest.fixture
def sample_connection_peer_data():
    """
    Provide sample connection peer data for testing.

    Returns:
        dict: Sample connection peer data dictionary
    """
    from tests.fixtures.mock_data import SAMPLE_CONNECTION_PEER_DATA

    return SAMPLE_CONNECTION_PEER_DATA.copy()


# =============================================================================
# Tracker Fixtures
# =============================================================================


@pytest.fixture
def sample_tracker_response():
    """
    Provide sample tracker response data for testing.

    Returns:
        dict: Sample tracker response dictionary
    """
    from tests.fixtures.mock_data import SAMPLE_TRACKER_RESPONSE

    return SAMPLE_TRACKER_RESPONSE.copy()


@pytest.fixture
def sample_tracker_error():
    """
    Provide sample tracker error response for testing.

    Returns:
        dict: Sample tracker error response
    """
    from tests.fixtures.mock_data import SAMPLE_TRACKER_ERROR_RESPONSE

    return SAMPLE_TRACKER_ERROR_RESPONSE.copy()


# =============================================================================
# Protocol Fixtures
# =============================================================================


@pytest.fixture
def sample_info_hash():
    """
    Provide sample info_hash for testing.

    Returns:
        bytes: 20-byte sample info_hash
    """
    from tests.fixtures.mock_data import SAMPLE_INFO_HASH

    return SAMPLE_INFO_HASH


@pytest.fixture
def sample_peer_id():
    """
    Provide sample peer_id for testing.

    Returns:
        bytes: 20-byte sample peer_id
    """
    from tests.fixtures.mock_data import SAMPLE_PEER_ID

    return SAMPLE_PEER_ID
