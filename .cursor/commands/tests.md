# Run Tests

Run the test suite for DFakeSeeder.

## Commands
```bash
# Run tests with pipenv (recommended)
make test-venv

# Run tests in Docker
make test-docker

# Run specific test file
pipenv run pytest tests/unit/test_specific.py -v

# Run tests matching a pattern
pipenv run pytest -k "test_name_pattern" -v
```

## Test Writing Guidelines

### Use Standalone Functions (No Test Classes)
```python
def test_my_function(mock_settings, tmp_path):
    # Arrange
    expected = "value"
    
    # Act
    result = my_function()
    
    # Assert
    assert result == expected
```

### Available Fixtures (from `tests/conftest.py`)
| Fixture | Purpose |
|---------|---------|
| `temp_config_dir` | Creates temp `~/.config/dfakeseeder/` with torrents subfolder |
| `sample_torrent_file` | Creates a valid minimal .torrent file |
| `mock_settings` | MagicMock of AppSettings with sensible defaults |
| `mock_global_peer_manager` | MagicMock of GlobalPeerManager |
| `mock_model` | MagicMock of Model with translation support |
| `clean_environment` | Cleans DFS_* environment variables |

### Test Markers
```python
@pytest.mark.unit           # Fast, isolated tests (<100ms)
@pytest.mark.integration    # Multi-component tests
@pytest.mark.slow           # Tests taking >1 second
@pytest.mark.requires_gtk   # Need GTK initialization
@pytest.mark.requires_network  # Need network access
```

### Mocking Rules
- Use `unittest.mock.patch` via `mocker` fixture (NOT `monkeypatch`)
- Use real filesystem with `tmp_path` (NOT pyfakefs)
- Every new function needs a test

## Key Files
- Test configuration: `pytest.ini`
- Fixtures: `tests/conftest.py`
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- E2E tests: `tests/e2e/`

