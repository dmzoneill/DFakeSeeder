# DFakeSeeder Test Suite

Comprehensive test suite for DFakeSeeder following strict testing standards.

## Overview

This test suite follows the guidelines in `/plans/TESTING_PLAN.md` with strict requirements:

- **100% Coverage Target**: All code must have comprehensive test coverage
- **NO Test Classes**: All tests are standalone functions
- **NO Parametrize**: Separate test functions for each scenario
- **NO Autouse Fixtures**: All fixtures must be explicitly requested
- **Real Filesystem**: Uses pytest's `tmp_path` (NOT pyfakefs)
- **unittest.mock**: Uses mocker fixture and MagicMock (NOT monkeypatch for mocking)
- **100ms Timeout**: Unit tests must complete in <100ms

## Directory Structure

```text
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/             # Domain logic tests
│   ├── lib/                # Library/utility tests
│   └── components/         # Component tests
├── integration/            # Integration tests (slower, multi-component)
├── fixtures/               # Shared test data and fixtures
│   ├── sample_torrents/    # Sample torrent files
│   ├── mock_data.py        # Test data constants
│   └── common_fixtures.py  # Reusable pytest fixtures
├── conftest.py            # Root conftest with base fixtures
└── README.md              # This file
```text
## Running Tests

### Basic Test Execution

```bash
# Run all tests
make test-venv

# Run with verbose output
pipenv run pytest -v

# Run specific test file
pipenv run pytest tests/unit/domain/test_app_settings.py

# Run specific test function
pipenv run pytest tests/unit/domain/test_app_settings.py::test_app_settings_singleton

# Run tests matching pattern
pipenv run pytest -k "test_torrent"
```text
### Test Categories

```bash
# Run only unit tests
pipenv run pytest -m unit

# Run only integration tests
pipenv run pytest -m integration

# Run tests that require GTK
pipenv run pytest -m requires_gtk

# Exclude slow tests
pipenv run pytest -m "not slow"
```text
### Coverage Reports

```bash
# Run with coverage (when pytest-cov is installed)
pipenv run pytest --cov=d_fake_seeder --cov-report=html

# View coverage report
open htmlcov/index.html

# Coverage with missing lines
pipenv run pytest --cov=d_fake_seeder --cov-report=term-missing
```text
## Writing Tests

### Test Structure

All tests follow the **Arrange-Act-Assert** pattern:

```python
def test_example_functionality():
    """Test that example functionality works correctly."""
    # Arrange - Set up test data and mocks
    mock_settings = MagicMock()
    mock_settings.tickspeed = 10

    # Act - Execute the function being tested
    result = function_under_test(mock_settings)

    # Assert - Verify the expected outcome
    assert result == expected_value
    mock_settings.method_call.assert_called_once()
```text
### Naming Conventions

- Test files: `test_<module_name>.py`
- Test functions: `test_<functionality>_<scenario>`
- Fixtures: `<resource>_<variant>` (e.g., `sample_torrent_file`)

Examples:
```python
# Good test names
def test_app_settings_loads_from_file():
def test_torrent_parsing_with_invalid_data():
def test_peer_connection_timeout_handling():

# Bad test names (avoid)
def test_1():
def test_settings():
def test_torrent():
```text
### Using Fixtures

Request fixtures explicitly (NO autouse):

```python
def test_with_temp_config(temp_config_dir):
    """Test using temporary config directory."""
    # Arrange
    settings_file = temp_config_dir / "settings.json"

    # Act & Assert
    assert temp_config_dir.exists()
    assert (temp_config_dir / "torrents").exists()
```text
### Mocking with unittest.mock

Use the `mocker` fixture (pytest-mock) or `unittest.mock` directly:

```python
from unittest.mock import MagicMock, patch

def test_with_mock(mocker):
    """Test using mocker fixture."""
    # Arrange
    mock_func = mocker.patch('d_fake_seeder.module.function')
    mock_func.return_value = 42

    # Act
    result = call_function_that_uses_mocked()

    # Assert
    assert result == 42
    mock_func.assert_called_once()

def test_with_context_manager():
    """Test using patch context manager."""
    # Arrange
    with patch('d_fake_seeder.module.function') as mock_func:
        mock_func.return_value = 42

        # Act
        result = call_function_that_uses_mocked()

        # Assert
        assert result == 42
```text
### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async functionality."""
    # Arrange
    mock_result = MagicMock()

    # Act
    result = await async_function_under_test()

    # Assert
    assert result == expected_value
```text
### Test Timeouts

Unit tests have a 100ms timeout enforced in pytest.ini:

```python
# This test will timeout if it takes >100ms
def test_fast_operation():
    """Test that completes quickly."""
    result = fast_function()
    assert result is not None

# Integration tests can override timeout
@pytest.mark.timeout(5)  # 5 second timeout
def test_slow_integration():
    """Integration test with longer timeout."""
    result = slow_integration_function()
    assert result is not None
```text
## Available Fixtures

### Base Fixtures (tests/conftest.py)

- `temp_config_dir(tmp_path)`: Temporary configuration directory
- `sample_torrent_file(tmp_path)`: Valid sample torrent file
- `mock_settings()`: Mock AppSettings instance
- `mock_global_peer_manager()`: Mock GlobalPeerManager instance
- `mock_model()`: Mock Model instance
- `clean_environment()`: Clean DFakeSeeder environment variables

### Common Fixtures (tests/fixtures/common_fixtures.py)

- `sample_torrent_metadata()`: Sample torrent metadata dict
- `multi_file_torrent_metadata()`: Multi-file torrent metadata
- `sample_peer_data()`: Sample peer information
- `sample_connection_peer_data()`: Sample connection peer data
- `sample_tracker_response()`: Sample tracker HTTP response
- `sample_tracker_error()`: Sample tracker error response
- `sample_info_hash()`: 20-byte sample info_hash
- `sample_peer_id()`: 20-byte sample peer_id

### Mock Data (tests/fixtures/mock_data.py)

Constants and test data including:
- `SAMPLE_TORRENT_DICT`: Complete torrent metadata
- `SAMPLE_TRACKER_RESPONSE`: Tracker announce response
- `SAMPLE_SETTINGS`: Full settings configuration
- BitTorrent protocol constants

## Best Practices

### DO

✅ Write standalone test functions (no classes)
✅ Use Arrange-Act-Assert pattern with comments
✅ Request fixtures explicitly
✅ Use `tmp_path` for filesystem tests
✅ Use `mocker` or `unittest.mock` for mocking
✅ Keep tests under 20 lines when possible
✅ Write descriptive test names
✅ Test edge cases and error conditions
✅ Clean up resources in fixtures

### DON'T

❌ Create test classes
❌ Use `@pytest.mark.parametrize`
❌ Use autouse fixtures
❌ Use `pyfakefs`
❌ Use `monkeypatch` for mocking (use for env cleanup only)
❌ Write tests that depend on execution order
❌ Share state between tests
❌ Use hardcoded paths
❌ Skip tests without good reason

## Continuous Integration

Tests are run automatically on:
- Pull requests
- Commits to main branch
- Release builds

CI requirements:
- All tests must pass
- Coverage must meet minimum threshold
- No flake8 violations
- No test timeouts

## Troubleshooting

### Tests Running Slowly

- Check for network I/O that should be mocked
- Verify fixtures are cleaning up properly
- Use `pytest --durations=10` to find slow tests
- Consider marking slow tests with `@pytest.mark.slow`

### Import Errors

- Ensure package is installed: `pipenv install -e .`
- Check PYTHONPATH includes project root
- Verify import mode in pytest.ini

### GTK-Related Failures

- Mark tests requiring GTK: `@pytest.mark.requires_gtk`
- Consider using GTK mocks for unit tests
- Run GTK tests in separate process if needed

### Coverage Gaps

- Use `pytest --cov-report=html` to see uncovered lines
- Check for unreachable code or defensive programming
- Consider if 100% coverage is appropriate for the module

## References

- Main Testing Plan: `/plans/TESTING_PLAN.md`
- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)
