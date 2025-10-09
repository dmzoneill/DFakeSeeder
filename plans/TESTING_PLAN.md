# DFakeSeeder Testing Plan

**Status:** In Progress
**Created:** 2025-10-09
**Last Updated:** 2025-10-09

## Overview

This document outlines a comprehensive testing strategy for DFakeSeeder, covering both unit tests and integration tests to ensure code quality, reliability, and maintainability.

## Testing Philosophy

### Core Principles
1. **Separation of Concerns**: Business logic tests are completely separate from UI rendering tests
2. **Real over Mocks**: Use real filesystem (`tmp_path`) and real test data whenever possible
3. **Explicit Dependencies**: All fixtures must be explicitly requested in test signatures (NO `autouse` fixtures)
4. **Mirror Source Structure**: Test directory structure exactly mirrors `d_fake_seeder/` source structure
5. **No Module Mocking**: Never mock `sys.modules` or similar Python internals
6. **No Test Classes**: Use standalone test functions to avoid shared state and context pollution
7. **Minimal Mocking**: Mock only external dependencies (network, external services), use real implementations for internal components
8. **Test Isolation**: Each test is completely independent - randomized test order should never cause failures
9. **Programmatic Test Data**: Generate test data in fixtures, don't rely on external files
10. **100% Coverage Target**: Aim for complete code coverage with strict enforcement

### Testing Goals
1. **Code Quality**: Maintain high code coverage (target: 100%)
2. **Reliability**: Catch regressions early in development
3. **Documentation**: Tests serve as executable documentation
4. **Confidence**: Enable safe refactoring and feature additions
5. **CI/CD Ready**: Tests should run quickly and reliably in automated pipelines
6. **Fast Feedback**: Unit tests complete in seconds, integration tests in minutes

## Technology Stack

### Core Testing Framework
- **pytest 7.4+**: Primary testing framework
- **pytest-cov 4.1+**: Code coverage reporting (strict 100% enforcement)
- **pytest-mock 3.11+**: Enhanced mocking capabilities (wrapper around unittest.mock)
- **pytest-asyncio 0.21+**: Async/await testing support
- **pytest-timeout 2.1+**: Test timeout enforcement
- **pytest-xdist 3.3+**: Parallel test execution
- **pytest-randomly 3.12+**: Randomize test order to catch hidden dependencies

### Additional Tools
- **hypothesis 6.82+**: Property-based testing for edge cases
- **freezegun 1.2+**: Time/date mocking
- **bencodepy**: For generating valid torrent file test data

### Mocking Strategy
- **unittest.mock.patch**: Primary mocking approach for patching imports and dependencies
- **unittest.mock.MagicMock**: Use for creating mock objects with automatic attribute/method mocking
- **pytest-mock (mocker fixture)**: Wrapper around unittest.mock for automatic cleanup
- **NO monkeypatch**: Avoid pytest's monkeypatch fixture - use unittest.mock.patch instead
- **NO responses library**: Use unittest.mock for HTTP mocking
- **NO pyfakefs**: Use pytest's real `tmp_path` fixtures
- **NO sys.modules mocking**: Never mock Python module system

## Test Organization Principles

### No Test Classes
- **Use standalone test functions only** - no `class Test*` constructs
- Test classes create shared context that can leak between tests
- Each test function is completely isolated with its own setup/teardown

### No Parametrized Tests
- **Write separate test functions** for different scenarios
- Don't use `@pytest.mark.parametrize` - creates coupling between test cases
- Each test function should test one specific scenario
- Makes debugging easier - you know exactly which scenario failed

### Standard Assertions
- **Use plain pytest assertions** - `assert x == y`
- No additional assertion libraries (assertpy, pytest-assert-utils, etc.)
- Pytest's assertion rewriting provides excellent error messages

### Exception Testing
- **Use `pytest.raises`** context manager for exception testing
- Don't use try-except blocks in tests
- Example: `with pytest.raises(ValueError, match="Invalid torrent")`

### Fixture Cleanup
- **Use yield fixtures** for explicit cleanup
- Don't rely solely on garbage collection
- Ensures proper teardown even if test fails

```python
@pytest.fixture
def temp_watch_dir(tmp_path):
    """Create and cleanup watch directory"""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()

    yield watch_dir

    # Explicit cleanup (if needed beyond tmp_path auto-cleanup)
    # Additional cleanup code here
```

### Test Naming Convention
- **Balanced verbosity**: Descriptive but not excessively long
- Pattern: `test_<component>_<scenario>_<expected_behavior>`
- Examples:
  - ✅ `test_torrent_parser_handles_single_file`
  - ✅ `test_watcher_copies_new_torrent_to_config_dir`
  - ❌ `test_torrent_folder_watcher_processes_new_torrent_file_added_to_watch_directory_and_copies_to_config` (too long)
  - ❌ `test_watcher` (too vague)

## Strict Test Constraints

### Unit Test Timeout: 100ms (Enforced)

**Unit tests MUST complete within 100 milliseconds**

```ini
# pytest.ini - Global timeout for all tests
[pytest]
timeout = 0.1  # 100ms timeout applies to test body only
timeout_func_only = true  # Don't include fixture setup/teardown
```

**Integration tests override with explicit timeout:**

```python
@pytest.mark.timeout(5)  # 5 second timeout for this integration test
def test_complete_torrent_lifecycle(tmp_path):
    """Integration tests set explicit timeouts"""
    # ... test code ...
```

**Rationale:**
- Unit tests must be blazingly fast
- Forces proper mocking (no real I/O, network, or sleep)
- Timeout violations FAIL the test immediately
- Slow tests indicate improper test design

### Maximum 20 Lines Per Unit Test (Guideline)

**Keep unit tests compact and focused**

✅ **GOOD - Concise and focused:**
```python
def test_watcher_copies_file(tmp_path, mock_model):
    """Short, focused test under 20 lines"""
    # Arrange
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    test_torrent = watch_dir / "test.torrent"
    test_torrent.write_bytes(b"d8:announce...")

    watcher = TorrentFolderWatcher(mock_model, mock_settings)

    # Act
    watcher.process_torrent_file(str(test_torrent))

    # Assert
    config_dir = tmp_path / ".config" / "dfakeseeder" / "torrents"
    assert (config_dir / "test.torrent").exists()
```

❌ **BAD - Too long, testing too much:**
```python
def test_watcher_complete_workflow(tmp_path, mock_model):
    """Test is too long - should be split"""
    # 50+ lines of setup, multiple scenarios, many assertions
    # This should be 3-4 separate tests!
```

**Line counting:**
- Guideline, not hard rule
- Don't count blank lines or comments
- Focus on keeping tests **simple and focused**

**When approaching 20 lines:**
- Sign you're testing too much
- Split into multiple focused tests
- Extract complex setup to fixtures

**Integration tests exempt:**
- Can be longer for complex workflows
- Still aim for clarity and focus

### Custom Pytest Check (Optional)

**Enforce constraints automatically:**

```python
# conftest.py - Optional custom check
import ast
import inspect

def pytest_collection_modifyitems(items):
    """Check test constraints"""
    for item in items:
        # Only check unit tests
        if "unit" not in str(item.fspath):
            continue

        # Get test source code
        source = inspect.getsource(item.function)
        lines = [l for l in source.split('\n') if l.strip() and not l.strip().startswith('#')]

        # Check line count (guideline warning, not failure)
        if len(lines) > 20:
            item.add_marker(pytest.mark.warn(f"Test has {len(lines)} lines (guideline: <20)"))

        # Count assert statements
        tree = ast.parse(source)
        assert_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert))

        if assert_count > 3:
            item.add_marker(pytest.mark.xfail(reason=f"Too many assertions: {assert_count} (max: 3)"))
```

### Constraint Summary

| Constraint | Unit Tests | Integration Tests |
|-----------|-----------|-------------------|
| **Timeout** | 100ms (enforced) | Explicit per-test |
| **Assertions** | Flexible | Flexible |
| **Line Count** | ~20 lines (guideline) | Flexible |
| **Enforcement** | Strict (fails build) | Relaxed |

**Philosophy:**
- Unit tests are **laser-focused** on ONE thing
- Fast feedback requires **fast tests**
- Constraints force **better design**
- Split complex tests into **multiple simple tests**

## Common Testing Pitfalls to AVOID

### ❌ DON'T: Use autouse Fixtures
```python
# BAD: Auto-applies to all tests in scope
@pytest.fixture(autouse=True)
def setup_environment():
    # This runs for EVERY test whether needed or not
    pass
```

### ✅ DO: Explicit Fixture Requests
```python
# GOOD: Only used when explicitly requested
@pytest.fixture
def temp_config_dir(tmp_path):
    config_dir = tmp_path / ".config" / "dfakeseeder"
    config_dir.mkdir(parents=True)
    return config_dir

def test_settings_loading(temp_config_dir):
    # Explicitly requests the fixture
    settings = Settings(str(temp_config_dir))
```

### ❌ DON'T: Use pytest's monkeypatch
```python
# BAD: Using monkeypatch fixture
def test_settings_loading(monkeypatch):
    monkeypatch.setattr('os.path.exists', lambda x: True)
```

### ✅ DO: Use unittest.mock.patch via mocker
```python
# GOOD: Using unittest.mock.patch via pytest-mock
def test_settings_loading(mocker):
    mocker.patch('os.path.exists', return_value=True)
```

### ❌ DON'T: Mock sys.modules
```python
# BAD: Breaks Python module system
def test_import_handling(mocker):
    mocker.patch('sys.modules', {'somemodule': None})
```

### ✅ DO: Mock at Import Point
```python
# GOOD: Mock where the module is used
def test_import_handling(mocker):
    mocker.patch('d_fake_seeder.domain.torrent.protocols.tracker.http_seeder.requests.get')
```

### ❌ DON'T: Use Fake Filesystem Libraries
```python
# BAD: Uses pyfakefs which can cause issues
def test_file_operations(fs):
    fs.create_file('/fake/path/file.txt')
```

### ✅ DO: Use Real Temporary Directories
```python
# GOOD: Uses real filesystem with pytest tmp_path
def test_file_operations(tmp_path):
    test_file = tmp_path / "file.txt"
    test_file.write_text("content")
```

### ❌ DON'T: Test UI Rendering Details
```python
# BAD: Testing GTK widget rendering
def test_button_color():
    button = Gtk.Button()
    assert button.get_style_context().has_class("blue")
```

### ✅ DO: Test Business Logic Only
```python
# GOOD: Testing button click handler logic
def test_button_handler(mocker):
    toolbar = Toolbar(mock_model)
    mock_handler = mocker.Mock()
    toolbar.on_add_torrent_clicked = mock_handler

    # Simulate button click (don't render GTK)
    toolbar.on_add_torrent_clicked(None)
    mock_handler.assert_called_once()
```

## Test Structure

### Directory Organization

**IMPORTANT**: Test structure mirrors the source code structure in `d_fake_seeder/` to maintain consistency and navigability.

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── domain/             # Domain logic tests (mirrors d_fake_seeder/domain/)
│   │   ├── torrent/
│   │   │   ├── test_torrent.py
│   │   │   ├── test_global_peer_manager.py
│   │   │   ├── test_peer_connection.py
│   │   │   ├── test_peer_server.py
│   │   │   ├── protocols/
│   │   │   │   ├── tracker/
│   │   │   │   │   ├── test_http_seeder.py
│   │   │   │   │   ├── test_udp_seeder.py
│   │   │   │   │   ├── test_dht_seeder.py
│   │   │   │   │   └── test_multi_tracker.py
│   │   │   │   └── transport/
│   │   │   │       └── test_utp_connection.py
│   │   │   └── simulation/
│   │   │       └── test_swarm_intelligence.py
│   │   ├── test_app_settings.py
│   │   └── test_translation_manager.py
│   │
│   ├── lib/                # Library/utility tests (mirrors d_fake_seeder/lib/)
│   │   ├── test_model.py
│   │   ├── test_view.py    # View coordination logic only, NOT GTK rendering
│   │   ├── test_controller.py
│   │   ├── test_logger.py
│   │   ├── test_settings.py
│   │   ├── handlers/
│   │   │   └── test_torrent_folder_watcher.py
│   │   ├── util/
│   │   │   ├── test_helpers.py
│   │   │   ├── test_constants.py
│   │   │   └── test_column_translations.py
│   │   └── component/      # UI component logic tests (NOT rendering)
│   │       ├── test_toolbar.py
│   │       ├── test_statusbar.py
│   │       ├── test_torrents.py
│   │       ├── test_states.py
│   │       ├── settings/
│   │       │   ├── test_general_tab.py
│   │       │   ├── test_connection_tab.py
│   │       │   └── test_peer_protocol_tab.py
│   │       └── torrent_details/
│   │           ├── test_status_tab.py
│   │           ├── test_files_tab.py
│   │           └── test_peers_tab.py
│   │
│   └── tools/              # Testing tool scripts
│       └── test_translation_build_manager.py

├── integration/            # Integration tests (slower, multi-component)
│   ├── test_torrent_lifecycle.py
│   ├── test_peer_protocol_flow.py
│   ├── test_tracker_communication.py
│   ├── test_watch_folder_integration.py
│   ├── test_settings_persistence.py
│   ├── test_translation_system.py
│   └── test_dbus_integration.py

├── fixtures/               # Shared test fixtures
│   ├── __init__.py
│   ├── sample_torrents/    # Real .torrent files for testing
│   │   ├── single_file.torrent
│   │   ├── multi_file.torrent
│   │   └── README.md       # Documentation of test torrent files
│   ├── mock_data.py        # Mock data generators
│   └── common_fixtures.py  # Pytest fixtures (NO autouse fixtures)

├── conftest.py            # Pytest configuration
└── README.md              # Testing documentation
```

## Testing Criteria

### Unit Tests

**Characteristics:**
- **Fast**: Individual tests run in <100ms
- **Isolated**: No external dependencies (network, database, GTK rendering)
- **Focused**: Test single functions/methods/classes
- **Deterministic**: Same input always produces same output
- **Independent**: Tests can run in any order
- **Real Filesystem**: Use `tmp_path` fixtures, not fake filesystem libraries

**Coverage Requirements:**
- All components: 100% (strictly enforced)
- No exceptions - all code paths must be tested
- UI component logic: 100% (logic only, not GTK rendering)

**Naming Convention:**
```python
def test_<component>_<scenario>_<expected_behavior>():
    """
    Test that <component> <expected_behavior> when <scenario>
    """
```

**Example:**
```python
def test_torrent_folder_watcher_copies_file_when_new_torrent_added(tmp_path):
    """
    Test that TorrentFolderWatcher copies torrent file to config directory
    when a new .torrent file is added to the watch folder
    """
    # Setup: Create watch directory
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    config_dir = tmp_path / ".config" / "dfakeseeder" / "torrents"
    config_dir.mkdir(parents=True)

    # Create test torrent file
    test_torrent = watch_dir / "test.torrent"
    test_torrent.write_bytes(b"d8:announce...")

    # Test: Process the file
    watcher = TorrentFolderWatcher(mock_model, mock_settings)
    watcher.process_torrent_file(str(test_torrent))

    # Verify: File was copied
    assert (config_dir / "test.torrent").exists()
```

### Integration Tests

**Characteristics:**
- **Realistic**: Test real component interactions
- **Slower**: May take several seconds per test
- **Real Dependencies**: Use real filesystem, mocked network
- **End-to-End Scenarios**: Test complete workflows
- **State Management**: Clean up after each test

**Coverage Requirements:**
- Critical workflows: 100%
- Feature interactions: 80%+
- Error scenarios: 70%+

**Naming Convention:**
```python
def test_<workflow>_<scenario>_<expected_outcome>():
    """
    Integration test for <workflow> that verifies <expected_outcome>
    when <scenario>
    """
```

## Test Categories

### 1. Domain Logic Tests (Unit)

**Priority: HIGH**

Test core business logic without UI or external dependencies:

- **Torrent Management**
  - Torrent file parsing (bencode)
  - Torrent metadata extraction
  - Torrent lifecycle (add, remove, pause, resume)
  - Peer list management

- **Protocol Implementations**
  - HTTP tracker communication (mock with unittest.mock)
  - UDP tracker communication (mock with unittest.mock)
  - DHT protocol operations
  - Multi-tracker failover
  - µTP connection management
  - BitTorrent message parsing

- **Peer-to-Peer Networking**
  - Peer connection establishment (mock sockets)
  - Handshake validation
  - Keep-alive mechanism
  - BitTorrent message exchange
  - Connection pooling

- **Settings Management**
  - Configuration loading/saving (use tmp_path)
  - Settings validation
  - Default value handling
  - Settings migration

### 2. Library/Utility Tests (Unit)

**Priority: MEDIUM**

Test helper functions and utilities:

- **File Watchers**
  - Watch folder monitoring (use tmp_path)
  - File event handling
  - Duplicate detection
  - File copying logic

- **Translation System**
  - Language switching
  - Widget translation (logic only, not GTK rendering)
  - Column header translation
  - Fallback handling

- **Logging**
  - Performance tracking
  - Context management
  - Log level filtering

- **Utilities**
  - Format helpers (human bytes, time conversion)
  - Fuzzy matching
  - Constants validation

### 3. Component Tests (Unit)

**Priority: MEDIUM**

**IMPORTANT**: Test UI component *logic* only, NOT GTK rendering:

- **Toolbar**
  - Button click handlers (logic)
  - File selection logic
  - Torrent addition/removal (business logic)

- **Settings Dialog**
  - Tab navigation (logic)
  - Settings updates (data changes)
  - Validation logic

- **Torrent Details**
  - Tab switching (logic)
  - Data display logic
  - Peer connection updates (data flow)

### 4. Integration Tests

**Priority: HIGH**

Test complete workflows and component interactions with **specific test scenarios**:

#### 4.1 Torrent Lifecycle Integration

**File:** `tests/integration/test_torrent_lifecycle.py`

**Test:** `test_complete_torrent_lifecycle_from_add_to_remove`
```python
@pytest.mark.integration
@pytest.mark.timeout(10)
def test_complete_torrent_lifecycle_from_add_to_remove(tmp_path):
    """
    Integration test: Complete torrent workflow from addition through removal

    Verifies:
    - Torrent file parsing (bencodepy)
    - Model update and signal emission
    - GlobalPeerManager integration
    - File cleanup on removal

    Uses REAL components:
    - Actual Torrent class (bencode parsing)
    - Actual Model (GObject signals)
    - Actual GlobalPeerManager

    Mocks ONLY external network:
    - HTTP tracker requests (unittest.mock)
    - Socket connections (unittest.mock)
    """
    # Arrange: Create real torrent file
    torrent_file = tmp_path / "test.torrent"
    # ... (use bencodepy to create valid torrent)

    model = Model()  # Real model
    peer_manager = GlobalPeerManager()  # Real peer manager

    # Mock only network requests
    mock_tracker = mocker.patch('requests.get')
    mock_tracker.return_value.content = b'd8:completei10e...'

    # Act 1: Add torrent
    model.add_torrent(str(torrent_file))

    # Assert 1: Verify torrent added to model
    assert len(model.torrents) == 1
    assert model.torrents[0].filename == "test.torrent"

    # Act 2: Add to peer manager
    peer_manager.add_torrent(model.torrents[0])

    # Assert 2: Verify peer manager has torrent
    assert model.torrents[0].info_hash in peer_manager.torrents

    # Act 3: Remove torrent
    model.remove_torrent(model.torrents[0])
    peer_manager.remove_torrent(model.torrents[0])

    # Assert 3: Verify complete cleanup
    assert len(model.torrents) == 0
    assert model.torrents[0].info_hash not in peer_manager.torrents
```

**Expected Duration:** 3-5 seconds
**Mock Strategy:** Mock ONLY network (tracker HTTP requests, socket connections)
**Real Components:** Torrent, Model, GlobalPeerManager, Settings (with tmp_path)

---

#### 4.2 Watch Folder Integration

**File:** `tests/integration/test_watch_folder_integration.py`

**Test:** `test_watch_folder_automatic_torrent_addition`
```python
@pytest.mark.integration
@pytest.mark.timeout(15)
def test_watch_folder_automatic_torrent_addition(tmp_path):
    """
    Integration test: Watch folder monitors directory and auto-adds torrents

    Verifies:
    - Watchdog file monitoring
    - File copy to config directory
    - Model integration
    - GlobalPeerManager integration
    - Duplicate detection
    - File deletion (if configured)

    Uses REAL components:
    - Actual TorrentFolderWatcher (watchdog.Observer)
    - Actual Model
    - Actual GlobalPeerManager
    - Real filesystem (tmp_path)

    Mocks: Nothing (pure integration test)
    """
    # Arrange: Setup real directories
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    config_dir = tmp_path / ".config" / "dfakeseeder" / "torrents"
    config_dir.mkdir(parents=True)

    settings = AppSettings()
    settings.watch_folder = {
        'enabled': True,
        'path': str(watch_dir),
        'delete_added_torrents': True,
        'auto_start_torrents': True
    }

    model = Model()
    peer_manager = GlobalPeerManager()
    watcher = TorrentFolderWatcher(model, settings, peer_manager)

    # Act 1: Start watcher
    watcher.start()

    # Act 2: Add torrent file to watch folder
    torrent_file = watch_dir / "ubuntu.torrent"
    # ... create valid torrent with bencodepy
    torrent_file.write_bytes(torrent_data)

    # Wait for watchdog to detect (typically 1-2 seconds)
    time.sleep(2)

    # Assert 1: Torrent copied to config directory
    assert (config_dir / "ubuntu.torrent").exists()
    assert (config_dir / "ubuntu.torrent").read_bytes() == torrent_data

    # Assert 2: Torrent added to model
    assert len(model.torrents) == 1
    assert model.torrents[0].filename == "ubuntu.torrent"

    # Assert 3: Torrent added to peer manager
    assert model.torrents[0].info_hash in peer_manager.torrents

    # Assert 4: Source file deleted (per settings)
    assert not torrent_file.exists()

    # Cleanup
    watcher.stop()
    peer_manager.stop()
```

**Expected Duration:** 5-10 seconds (includes watchdog detection time)
**Mock Strategy:** NO MOCKING - pure integration test with real filesystem
**Real Components:** TorrentFolderWatcher, watchdog.Observer, Model, GlobalPeerManager

---

#### 4.3 Peer Protocol Flow Integration

**File:** `tests/integration/test_peer_protocol_flow.py`

**Test:** `test_incoming_peer_connection_handshake_flow`
```python
@pytest.mark.integration
@pytest.mark.timeout(10)
@pytest.mark.asyncio
async def test_incoming_peer_connection_handshake_flow():
    """
    Integration test: Complete peer connection handshake workflow

    Verifies:
    - PeerServer accepts connections
    - PeerConnection performs handshake
    - BitTorrent message exchange
    - Keep-alive mechanism
    - Connection cleanup

    Uses REAL components:
    - Actual PeerServer (asyncio socket server)
    - Actual PeerConnection (BEP-003 implementation)
    - Actual BitTorrent message parsing

    Mocks ONLY:
    - External peer IP (use localhost)
    """
    # Arrange: Create real peer server
    server = PeerServer(port=6881)
    await server.start()

    # Create real torrent
    torrent = create_test_torrent()  # Real Torrent object

    # Act 1: Incoming connection from "peer" (actually test client)
    reader, writer = await asyncio.open_connection('127.0.0.1', 6881)

    # Act 2: Send handshake
    handshake_msg = PeerConnection.build_handshake(torrent.info_hash, b'-TE0001-')
    writer.write(handshake_msg)
    await writer.drain()

    # Assert 1: Server responds with handshake
    response = await reader.read(68)  # Handshake is 68 bytes
    assert len(response) == 68
    assert response[28:48] == torrent.info_hash

    # Act 3: Send bitfield message
    bitfield_msg = b'\x00\x00\x00\x02\x05\xff'  # Have all pieces
    writer.write(bitfield_msg)
    await writer.drain()

    # Assert 2: Server processes bitfield
    await asyncio.sleep(0.5)
    # Verify server tracked peer state

    # Cleanup
    writer.close()
    await writer.wait_closed()
    await server.stop()
```

**Expected Duration:** 3-5 seconds
**Mock Strategy:** Use localhost instead of real external peers
**Real Components:** PeerServer, PeerConnection, BitTorrent message parsing, asyncio

---

#### 4.4 Tracker Communication Integration

**File:** `tests/integration/test_tracker_communication.py`

**Test:** `test_http_tracker_announce_and_peer_discovery`
```python
@pytest.mark.integration
@pytest.mark.timeout(10)
def test_http_tracker_announce_and_peer_discovery(mocker):
    """
    Integration test: HTTP tracker announce and peer list update

    Verifies:
    - HTTPSeeder announce logic
    - Bencode response parsing
    - Peer list extraction
    - GlobalPeerManager peer addition

    Uses REAL components:
    - Actual HTTPSeeder
    - Actual bencode parser
    - Actual GlobalPeerManager

    Mocks ONLY:
    - HTTP requests (unittest.mock)
    """
    # Arrange: Mock HTTP tracker response
    mock_response = mocker.patch('requests.get')
    tracker_response = bencodepy.encode({
        b'interval': 1800,
        b'complete': 42,
        b'incomplete': 15,
        b'peers': b'\xc0\xa8\x01\x02\x1a\xe1'  # Compact peer format
    })
    mock_response.return_value.content = tracker_response
    mock_response.return_value.status_code = 200

    # Create real components
    torrent = create_test_torrent()
    seeder = HTTPSeeder(torrent, 'http://tracker.example.com/announce')
    peer_manager = GlobalPeerManager()

    # Act: Perform announce
    result = seeder.announce()

    # Assert 1: Response parsed correctly
    assert result['complete'] == 42
    assert result['incomplete'] == 15
    assert result['interval'] == 1800

    # Assert 2: Peers extracted from compact format
    peers = seeder.parse_peers(result['peers'])
    assert len(peers) == 1
    assert peers[0]['ip'] == '192.168.1.2'
    assert peers[0]['port'] == 6881

    # Act 2: Add peers to manager
    for peer_info in peers:
        peer_manager.add_peer_for_torrent(torrent, peer_info)

    # Assert 3: Peer manager tracks discovered peers
    assert len(peer_manager.get_peers(torrent.info_hash)) == 1
```

**Expected Duration:** 2-3 seconds
**Mock Strategy:** Mock ONLY HTTP requests (unittest.mock.patch for requests.get)
**Real Components:** HTTPSeeder, bencodepy parser, GlobalPeerManager

---

#### 4.5 Settings Persistence Integration

**File:** `tests/integration/test_settings_persistence.py`

**Test:** `test_settings_save_and_reload_with_file_watching`
```python
@pytest.mark.integration
@pytest.mark.timeout(10)
def test_settings_save_and_reload_with_file_watching(tmp_path):
    """
    Integration test: Settings save/load with watchdog file monitoring

    Verifies:
    - Settings save to JSON file
    - File watching detects changes
    - Automatic reload
    - GObject signal emission

    Uses REAL components:
    - Actual Settings (file I/O)
    - Actual watchdog.Observer
    - Real filesystem (tmp_path)

    Mocks: Nothing
    """
    # Arrange: Create settings with real file
    config_file = tmp_path / "settings.json"
    settings = Settings(config_path=str(config_file))

    # Track signal emissions
    signal_emissions = []
    def on_setting_changed(source, key, value):
        signal_emissions.append((key, value))

    settings.connect('attribute-changed', on_setting_changed)

    # Act 1: Change and save setting
    settings.upload_speed = 100
    settings.save()

    # Assert 1: File written correctly
    assert config_file.exists()
    with open(config_file, 'r') as f:
        saved_data = json.load(f)
    assert saved_data['upload_speed'] == 100

    # Act 2: Create new Settings instance (simulates app restart)
    settings2 = Settings(config_path=str(config_file))

    # Assert 2: Settings loaded correctly
    assert settings2.upload_speed == 100

    # Act 3: Modify file directly (simulates external edit)
    with open(config_file, 'w') as f:
        saved_data['upload_speed'] = 200
        json.dump(saved_data, f)

    # Wait for watchdog to detect change
    time.sleep(2)

    # Assert 3: Settings auto-reloaded
    assert settings.upload_speed == 200
    assert ('upload_speed', 200) in signal_emissions
```

**Expected Duration:** 5-8 seconds (includes watchdog detection)
**Mock Strategy:** NO MOCKING - pure integration with real filesystem and file watching
**Real Components:** Settings, watchdog.Observer, GObject signals, JSON file I/O

---

### Integration Test Summary

| Test | Duration | Mocks | Real Components | Assertions |
|------|----------|-------|-----------------|------------|
| Torrent Lifecycle | 3-5s | Network only | Torrent, Model, GlobalPeerManager | 3 per stage |
| Watch Folder | 5-10s | None | TorrentFolderWatcher, watchdog, Model | 4 total |
| Peer Protocol | 3-5s | Use localhost | PeerServer, PeerConnection, asyncio | 2-3 per stage |
| Tracker Communication | 2-3s | HTTP requests | HTTPSeeder, bencodepy, GlobalPeerManager | 3 total |
| Settings Persistence | 5-8s | None | Settings, watchdog, GObject signals | 3 total |

**Total Expected Integration Test Time:** 20-30 seconds for all tests

## Test Infrastructure

### Required Dependencies

```toml
[dev-dependencies]
pytest = "^7.4.0"
pytest-cov = "^4.1.0"
pytest-mock = "^3.11.1"        # Wrapper around unittest.mock
pytest-asyncio = "^0.21.1"
pytest-timeout = "^2.1.0"
pytest-xdist = "^3.3.1"        # Parallel test execution
pytest-randomly = "^3.12.0"    # Randomize test order
hypothesis = "^6.82.0"         # Property-based testing
freezegun = "^1.2.2"           # Time mocking
bencodepy = "^0.9.5"           # For generating test torrent files

# NOTE: We do NOT use:
# - responses (use unittest.mock instead)
# - pyfakefs (use tmp_path instead)
# - pytest-parametrize (write separate test functions)
```

### Pytest Configuration

**conftest.py:**
```python
import pytest
import os
from pathlib import Path
from unittest.mock import MagicMock, Mock

# IMPORTANT: NO autouse fixtures!
# All fixtures must be explicitly requested in test signatures
# Use unittest.mock.MagicMock for flexible mocks with automatic attributes


@pytest.fixture
def temp_config_dir(tmp_path):
    """
    Create temporary config directory structure

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
    Create a valid sample torrent file

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
    Create mock AppSettings instance using MagicMock

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
    Create mock GlobalPeerManager using MagicMock

    Returns: MagicMock object with add_torrent and remove_torrent methods
    """
    manager = MagicMock()
    manager.torrents = {}
    return manager


@pytest.fixture
def mock_model():
    """
    Create mock Model instance using MagicMock

    Returns: MagicMock object with torrent management methods
    """
    model = MagicMock()
    model.torrents = []
    model.get_torrents.return_value = []
    return model
```

**pytest.ini:**
```ini
[pytest]
minversion = 7.0
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Code coverage settings - STRICT 100% enforcement
addopts =
    -ra
    --strict-markers
    --cov=d_fake_seeder
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=100
    -v
    -p pytest_randomly

# STRICT timeout enforcement - 100ms for unit tests
timeout = 0.1
timeout_func_only = true  # Only test function body, not fixtures

# Test markers
markers =
    unit: Unit tests (fast, isolated, <100ms)
    integration: Integration tests (slower, multi-component, explicit timeout)
    slow: Tests that take >1 second
    network: Tests requiring network mocking
    ui: Tests involving GTK UI component logic (not rendering)
    async: Tests using asyncio

# Async configuration
asyncio_mode = auto

# Randomize test order to catch hidden dependencies
# Use --randomly-seed=<number> to reproduce specific test order
```

## Detailed Test Writing Guidelines

### 1. Patch Where Imported (Not Where Defined)

✅ **DO:**
```python
def test_http_tracker_announce(mocker):
    """Patch where requests is imported, not where it's defined"""
    # Patch at import location in http_seeder module
    mock_response = MagicMock()
    mock_response.content = b'd8:completei10e'

    mocker.patch('d_fake_seeder.domain.torrent.protocols.tracker.http_seeder.requests.get',
                 return_value=mock_response)
```

❌ **DON'T:**
```python
def test_http_tracker_announce(mocker):
    """Don't patch at the definition location"""
    mocker.patch('requests.get', return_value=mock_response)  # Wrong!
```

### 2. Arrange-Act-Assert with Explicit Comments

✅ **DO:**
```python
def test_watcher_copies_torrent_to_config_dir(tmp_path, mock_model):
    """Use clear AAA structure with comment markers"""
    # Arrange
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    config_dir = tmp_path / ".config" / "dfakeseeder" / "torrents"
    config_dir.mkdir(parents=True)

    test_torrent = watch_dir / "test.torrent"
    test_torrent.write_bytes(b"d8:announce...")

    watcher = TorrentFolderWatcher(mock_model, mock_settings)

    # Act
    watcher.process_torrent_file(str(test_torrent))

    # Assert
    assert (config_dir / "test.torrent").exists()
    assert (config_dir / "test.torrent").read_bytes() == b"d8:announce..."
```

❌ **DON'T:**
```python
def test_watcher_copies_torrent_to_config_dir(tmp_path, mock_model):
    """Don't mix setup and assertions without clear structure"""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    test_torrent = watch_dir / "test.torrent"
    test_torrent.write_bytes(b"d8:announce...")
    watcher = TorrentFolderWatcher(mock_model, mock_settings)
    watcher.process_torrent_file(str(test_torrent))
    assert (tmp_path / ".config" / "dfakeseeder" / "torrents" / "test.torrent").exists()
```

### 3. Set Mock Return Values in Tests (Not Fixtures)

✅ **DO:**
```python
@pytest.fixture
def mock_model():
    """Generic mock - no return values set"""
    return MagicMock()

def test_model_adds_torrent(mock_model):
    """Set return values right before use"""
    # Arrange
    mock_model.get_torrents.return_value = []
    mock_model.torrent_count = 0

    # Act
    mock_model.add_torrent("/path/to/test.torrent")

    # Assert
    mock_model.add_torrent.assert_called_once_with("/path/to/test.torrent")
```

❌ **DON'T:**
```python
@pytest.fixture
def mock_model():
    """Don't set specific return values in fixtures"""
    model = MagicMock()
    model.get_torrents.return_value = []  # Too specific!
    model.torrent_count = 0
    return model
```

### 4. Multiple Separate Assertions (Not Combined)

✅ **DO:**
```python
def test_torrent_parsing(sample_torrent_file):
    """Separate assertions for clear error messages"""
    # Arrange
    torrent = Torrent(str(sample_torrent_file))

    # Act
    # (parsing happens in __init__)

    # Assert - max 3 assertions
    assert torrent.name == "test_file.txt"
    assert torrent.piece_length == 16384
    assert torrent.announce == "http://tracker.example.com:8080/announce"
```

❌ **DON'T:**
```python
def test_torrent_parsing(sample_torrent_file):
    """Don't combine assertions with 'and'"""
    torrent = Torrent(str(sample_torrent_file))
    assert torrent.name == "test_file.txt" and torrent.piece_length == 16384  # Which failed?
```

### 5. Verify File Contents (Not Just Existence)

✅ **DO:**
```python
def test_watcher_copies_file_correctly(tmp_path, mock_model):
    """Verify both existence and contents"""
    # Arrange
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    config_dir = tmp_path / ".config" / "dfakeseeder" / "torrents"
    config_dir.mkdir(parents=True)

    original_content = b"d8:announce33:http://tracker.example.com/announce"
    test_torrent = watch_dir / "test.torrent"
    test_torrent.write_bytes(original_content)

    # Act
    watcher = TorrentFolderWatcher(mock_model, mock_settings)
    watcher.process_torrent_file(str(test_torrent))

    # Assert
    copied_file = config_dir / "test.torrent"
    assert copied_file.exists()
    assert copied_file.read_bytes() == original_content
```

❌ **DON'T:**
```python
def test_watcher_copies_file_correctly(tmp_path, mock_model):
    """Don't just check existence"""
    # ... setup code ...
    watcher.process_torrent_file(str(test_torrent))
    assert (config_dir / "test.torrent").exists()  # File could be empty or corrupted!
```

### 6. Use `with` for Single Patches, Assignment for Multiple

✅ **DO - Single Patch:**
```python
def test_single_network_call(mocker):
    """Use with statement for single patch"""
    # Arrange
    with mocker.patch('d_fake_seeder.domain.torrent.protocols.tracker.http_seeder.requests.get') as mock_get:
        mock_get.return_value.content = b'd8:completei10e'

        # Act
        seeder = HTTPSeeder(tracker_url='http://tracker.example.com')
        result = seeder.announce()

        # Assert
        assert result['complete'] == 10
```

✅ **DO - Multiple Patches:**
```python
def test_multiple_patches(mocker):
    """Use return value assignment for multiple patches to avoid deep nesting"""
    # Arrange
    mock_get = mocker.patch('d_fake_seeder.domain.torrent.protocols.tracker.http_seeder.requests.get')
    mock_post = mocker.patch('d_fake_seeder.domain.torrent.protocols.tracker.http_seeder.requests.post')
    mock_sleep = mocker.patch('time.sleep')

    mock_get.return_value.content = b'd8:completei10e'
    mock_post.return_value.status_code = 200

    # Act
    seeder = HTTPSeeder(tracker_url='http://tracker.example.com')
    result = seeder.announce_with_retry()

    # Assert
    assert mock_get.called
    assert mock_post.called
    assert mock_sleep.called
```

❌ **DON'T:**
```python
def test_multiple_patches(mocker):
    """Don't nest multiple with statements"""
    with mocker.patch('requests.get') as mock_get:
        with mocker.patch('requests.post') as mock_post:
            with mocker.patch('time.sleep') as mock_sleep:
                # Too deeply nested!
                pass
```

### 7. Flexible Mock Assertions

✅ **DO:**
```python
def test_model_called_with_correct_path(mocker, tmp_path):
    """Use flexible assertions when exact match not needed"""
    # Arrange
    mock_model = MagicMock()
    torrent_file = tmp_path / "test.torrent"
    torrent_file.write_bytes(b"d8:announce...")

    # Act
    add_torrent_from_watch_folder(mock_model, str(torrent_file))

    # Assert - verify called, check path ends correctly
    assert mock_model.add_torrent.called
    call_path = mock_model.add_torrent.call_args[0][0]
    assert call_path.endswith("test.torrent")
```

### 8. Test Both Async and Sync Patterns When Relevant

✅ **DO:**
```python
@pytest.mark.asyncio
async def test_peer_connection_async(mocker):
    """Test async usage pattern"""
    # Arrange
    mock_reader = AsyncMock()
    mock_writer = AsyncMock()
    mock_reader.read.return_value = b'\x13BitTorrent protocol...'

    # Act
    connection = PeerConnection('127.0.0.1', 6881)
    result = await connection.handshake(mock_reader, mock_writer)

    # Assert
    assert result.success is True

def test_peer_connection_sync_wrapper():
    """Test synchronous wrapper if provided"""
    # Arrange
    connection = PeerConnection('127.0.0.1', 6881)

    # Act
    result = connection.handshake_blocking()  # Sync wrapper

    # Assert
    assert result.success is True
```

### 9. Minimal Valid Test Data

✅ **DO:**
```python
@pytest.fixture
def minimal_torrent_file(tmp_path):
    """Create minimal valid torrent for fast tests"""
    import bencodepy

    torrent_file = tmp_path / "minimal.torrent"
    torrent_data = {
        b'announce': b'http://tracker.example.com/announce',
        b'info': {
            b'name': b'test.txt',
            b'piece length': 16384,
            b'pieces': b'\x00' * 20,  # Minimal fake hash
            b'length': 1024,
        }
    }
    torrent_file.write_bytes(bencodepy.encode(torrent_data))
    return torrent_file
```

❌ **DON'T:**
```python
@pytest.fixture
def realistic_torrent_file(tmp_path):
    """Don't create unnecessarily complex test data"""
    # Don't generate real piece hashes, multi-file structures, etc.
    # unless specifically testing those features
    pass
```

### 10. Verify Exception Type and Message

✅ **DO:**
```python
def test_invalid_torrent_raises_error(tmp_path):
    """Verify both exception type and message"""
    # Arrange
    invalid_file = tmp_path / "invalid.torrent"
    invalid_file.write_bytes(b"not a valid torrent")

    # Act & Assert
    with pytest.raises(ValueError, match="Invalid torrent file.*bencode"):
        Torrent(str(invalid_file))
```

❌ **DON'T:**
```python
def test_invalid_torrent_raises_error(tmp_path):
    """Don't just check exception type"""
    invalid_file = tmp_path / "invalid.torrent"
    invalid_file.write_bytes(b"not a valid torrent")

    with pytest.raises(ValueError):  # What was the error message?
        Torrent(str(invalid_file))
```

## Testing Best Practices

### 1. Test Isolation with Real Filesystem

✅ **DO:**
```python
def test_watch_folder_adds_torrent(tmp_path, mock_model, mock_settings):
    """Each test creates its own isolated real filesystem"""
    # Setup real directories
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    config_dir = tmp_path / ".config" / "dfakeseeder" / "torrents"
    config_dir.mkdir(parents=True)

    # Update mock settings with real paths
    mock_settings.watch_folder['path'] = str(watch_dir)

    # Create real test file
    test_torrent = watch_dir / "test.torrent"
    test_torrent.write_bytes(b"d8:announce...")

    # Test with real filesystem
    watcher = TorrentFolderWatcher(mock_model, mock_settings)
    watcher.process_torrent_file(str(test_torrent))

    # Verify with real file operations
    assert (config_dir / "test.torrent").exists()
```

❌ **DON'T:**
```python
def test_watch_folder_adds_torrent(fs):  # pyfakefs
    """Don't use fake filesystem libraries"""
    fs.create_file('/fake/watch/test.torrent')
    # This can cause issues with real file operations
```

### 2. Test Data Generation

✅ **DO:**
```python
@pytest.fixture
def valid_torrent_data():
    """Generate test data inline or in fixtures"""
    import bencodepy
    return {
        'info': {
            'name': 'test.txt',
            'piece length': 16384,
            'pieces': b'\x00' * 20,
        },
        'announce': 'http://tracker.example.com/announce'
    }

def test_torrent_parsing(valid_torrent_data, tmp_path):
    """Use generated data in tests"""
    import bencodepy

    torrent_file = tmp_path / "test.torrent"
    torrent_file.write_bytes(bencodepy.encode(valid_torrent_data))

    torrent = Torrent(str(torrent_file))
    assert torrent.name == "test.txt"
```

❌ **DON'T:**
```python
def test_torrent_parsing():
    """Don't hardcode paths or assume external files exist"""
    torrent = Torrent('/path/to/some/torrent.torrent')  # Fragile!
```

### 3. Network Mocking with unittest.mock.patch and MagicMock

✅ **DO:**
```python
from unittest.mock import MagicMock

def test_tracker_announce(mocker):
    """Mock network requests with unittest.mock.patch via pytest-mock"""
    # Create mock response using MagicMock
    mock_response = MagicMock()
    mock_response.content = b'd8:completei10e10:incompletei5ee'
    mock_response.status_code = 200

    # Patch at the point of use with mocker.patch (unittest.mock.patch wrapper)
    mocker.patch('d_fake_seeder.domain.torrent.protocols.tracker.http_seeder.requests.get',
                 return_value=mock_response)

    # Test
    seeder = HTTPSeeder(tracker_url='http://tracker.example.com')
    result = seeder.announce()

    # Verify
    assert result['complete'] == 10
    assert result['incomplete'] == 5
```

❌ **DON'T:**
```python
def test_tracker_announce():
    """Don't make real network calls in unit tests"""
    result = announce_to_tracker('http://real-tracker.com')  # Slow and fragile!
```

❌ **DON'T:**
```python
def test_tracker_announce(responses):
    """Don't use responses library - use unittest.mock instead"""
    responses.add(responses.GET, 'http://tracker.example.com', ...)
```

❌ **DON'T:**
```python
def test_tracker_announce(monkeypatch):
    """Don't use monkeypatch - use mocker.patch instead"""
    monkeypatch.setattr('requests.get', lambda *args: ...)
```

### 4. UI Component Testing (Logic Only)

✅ **DO:**
```python
from unittest.mock import MagicMock

def test_toolbar_add_torrent_handler(mocker, mock_model):
    """Test button handler logic, not GTK rendering"""
    # Create toolbar without rendering
    toolbar = Toolbar(mock_model)

    # Mock file chooser dialog using MagicMock
    mock_dialog = MagicMock()
    mock_dialog.run.return_value = Gtk.ResponseType.OK
    mock_dialog.get_filename.return_value = "/tmp/test.torrent"

    # Use mocker.patch (unittest.mock.patch wrapper)
    mocker.patch.object(Gtk, 'FileChooserDialog', return_value=mock_dialog)

    # Test the handler logic
    toolbar.on_add_torrent_clicked(None)

    # Verify business logic executed
    mock_model.add_torrent.assert_called_once_with("/tmp/test.torrent")
```

❌ **DON'T:**
```python
def test_toolbar_button_appearance():
    """Don't test GTK widget rendering details"""
    toolbar = Toolbar(model)
    button = toolbar.add_button

    # Testing visual appearance is fragile and slow
    assert button.get_style_context().has_class("suggested-action")
    assert button.get_label() == "Add Torrent"
```

### 5. Async Testing

✅ **DO:**
```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_peer_connection_handshake(mocker):
    """Test async peer connection logic"""
    # Mock async socket operations using AsyncMock
    mock_reader = AsyncMock()
    mock_writer = AsyncMock()

    mock_reader.read.return_value = b'\x13BitTorrent protocol...'

    # Test async function
    connection = PeerConnection('127.0.0.1', 6881)
    result = await connection.handshake(mock_reader, mock_writer)

    assert result.success is True
    mock_writer.write.assert_called()
```

### 6. Clear Assertions

✅ **DO:**
```python
def test_torrent_addition(mock_model, sample_torrent_file):
    """Clear, specific assertions"""
    initial_count = len(mock_model.torrents)

    mock_model.add_torrent(str(sample_torrent_file))

    # Multiple specific assertions
    assert len(mock_model.torrents) == initial_count + 1
    assert mock_model.torrents[-1].filename == "sample.torrent"
    assert mock_model.add_torrent.called is True
```

❌ **DON'T:**
```python
def test_torrent_addition(mock_model):
    """Vague assertions"""
    mock_model.add_torrent("/tmp/test.torrent")
    assert mock_model.torrents  # What are we testing?
```

## GTK GUI Automation Testing (Optional)

### Overview

While unit and integration tests focus on business logic, **GUI automation tests** verify the actual user interface behavior by launching the real application and simulating user interactions. These are end-to-end (E2E) tests similar to Cypress for web applications.

**⚠️ Important**: GUI automation tests are **optional** and should supplement (not replace) the comprehensive unit and integration tests described in this plan.

### Technology: Dogtail with pytest-xvfb

**DFakeSeeder uses Dogtail** - the standard GTK automation framework that uses accessibility APIs (AT-SPI) to interact with GTK applications. Combined with pytest-xvfb for headless execution, this provides a complete GUI testing solution.

#### Installation

```bash
# System dependencies (Fedora/RHEL)
sudo dnf install python3-dogtail

# System dependencies (Ubuntu/Debian)
sudo apt-get install python3-dogtail at-spi2-core xvfb

# Python packages
pip install dogtail pytest-xvfb
```

#### Capabilities
- Launch GTK applications via subprocess
- Find widgets by accessibility name, role, or label
- Simulate user interactions (clicks, keyboard input, drag-and-drop)
- Verify widget properties and states
- Take screenshots on test failure for debugging
- Run headlessly in CI/CD using Xvfb virtual display

#### Example Test: Add Torrent Workflow

```python
import pytest
from dogtail.tree import root
from dogtail.config import config
import subprocess
import time

@pytest.mark.gui
@pytest.mark.timeout(30)  # GUI tests need longer timeout
def test_add_torrent_via_gui():
    """
    GUI automation test: Add torrent through actual UI

    Process tested:
    1. Launch application via subprocess
    2. Find "Add Torrent" button using accessibility tree
    3. Click button to open file chooser dialog
    4. Enter torrent file path
    5. Submit file selection
    6. Verify torrent appears in list

    NOTE: This is an E2E test - much slower than unit tests
    """
    # Configure dogtail search parameters
    config.searchCutoffCount = 20
    config.searchWarningThreshold = 3

    # Launch application
    app_process = subprocess.Popen(['dfakeseeder'])
    time.sleep(2)  # Wait for app to start

    try:
        # Find application window via accessibility API
        app = root.application('dfakeseeder')

        # Find and click "Add Torrent" button
        add_button = app.child('Add Torrent', roleName='push button')
        add_button.click()

        # Wait for file chooser dialog to appear
        time.sleep(0.5)
        file_dialog = app.child('Select Torrent File', roleName='dialog')

        # Enter file path in text entry
        path_entry = file_dialog.child(roleName='text')
        path_entry.text = '/tmp/test.torrent'

        # Click Open button to submit
        open_button = file_dialog.child('Open', roleName='push button')
        open_button.click()

        # Verify torrent appears in list
        time.sleep(1)
        torrent_list = app.child('Torrents', roleName='tree table')
        assert 'test.torrent' in torrent_list.text

    finally:
        # Cleanup - terminate application
        app_process.terminate()
        app_process.wait(timeout=5)
```

#### Headless Execution with pytest-xvfb

GUI tests can run without a physical display using Xvfb (virtual framebuffer):

```python
@pytest.mark.gui
@pytest.mark.xvfb  # Automatically runs in virtual display
def test_settings_dialog_headless():
    """Test settings dialog in headless mode for CI/CD"""
    # Same test code as above - pytest-xvfb handles virtual display
    app_process = subprocess.Popen(['dfakeseeder'])
    # ... rest of test
```

### GUI Test Organization

```
tests/
├── gui/                      # GUI automation tests (optional)
│   ├── conftest.py          # GUI test configuration
│   ├── test_torrent_workflow_gui.py
│   ├── test_settings_dialog_gui.py
│   ├── test_toolbar_interactions_gui.py
│   └── screenshots/         # Failure screenshots
│       └── .gitignore       # Don't commit screenshots
```

### Best Practices for GUI Tests

#### 1. Minimal GUI Test Coverage

**GUI tests are expensive** - use sparingly:

✅ **DO test via GUI:**
- Critical user workflows (add torrent → verify in list)
- Settings dialog interaction flow
- Menu navigation
- Dialog responses

❌ **DON'T test via GUI:**
- Business logic (use unit tests)
- Edge cases (use unit tests)
- Error handling (use unit tests)
- Performance (use unit tests)

**Target:** 5-10 critical GUI tests, not hundreds

#### 2. Separate Markers and Execution

```python
# pytest.ini
markers =
    gui: GUI automation tests (very slow, requires display)
```

```makefile
# Makefile
test-gui:
	pipenv run pytest tests/gui -v -m gui

test-gui-headless:
	pipenv run pytest tests/gui -v -m gui --xvfb
```

**Run separately from unit/integration tests:**
```bash
# Regular tests (fast)
make test-all

# GUI tests (slow, optional)
make test-gui
```

#### 3. Longer Timeouts

GUI tests are inherently slow:

```python
@pytest.mark.gui
@pytest.mark.timeout(60)  # 60 second timeout for GUI test
def test_complete_user_workflow():
    """GUI tests need much longer timeouts"""
    pass
```

#### 4. Accessibility Requirements

**For Dogtail/LDTP to work**, widgets must have:
- Proper accessibility labels
- Unique accessible names
- Correct role assignments

```python
# Good - Accessible GTK widget
button = Gtk.Button(label="Add Torrent")
button.set_name("add-torrent-button")  # Unique identifier

# Bad - No accessibility info
button = Gtk.Button()
button.set_icon_name("list-add")  # Icon only, no label
```

#### 5. Retry Logic

GUI tests can be flaky - add retry logic:

```python
from dogtail.utils import retry

@pytest.mark.gui
def test_dialog_appears():
    """Test with automatic retry"""

    @retry(tries=3, delay=1)
    def wait_for_dialog():
        dialog = app.child('Settings', roleName='dialog')
        assert dialog.showing

    wait_for_dialog()
```

#### 6. Screenshot on Failure

```python
# conftest.py for GUI tests
import pytest
from dogtail.utils import screenshot

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on GUI test failure"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        if "gui" in item.keywords:
            screenshot_path = f"tests/gui/screenshots/{item.name}.png"
            screenshot(screenshot_path)
            print(f"Screenshot saved: {screenshot_path}")
```

### GUI Test Scope

GUI automation tests verify **end-to-end user workflows** through the actual GTK interface, including:
- Toolbar button interactions and file chooser dialogs
- Settings dialog navigation and tab switching
- Context menu actions and confirmation dialogs
- Search functionality and list filtering
- Window state management and persistence

**For detailed GUI test scenarios**, see **[GUI_TESTING_PLAN.md](GUI_TESTING_PLAN.md)** which contains comprehensive test specifications for all GUI workflows.

**DO NOT test with GUI automation:**
- Business logic (covered by unit tests)
- Error handling (covered by unit tests)
- Network communication (covered by integration tests)
- File system operations (covered by integration tests)

### Recommended Testing Pyramid

```
         GUI Tests (E2E)
        /  5-10 tests   \
       /   Very Slow     \
      /___________________\
     Integration Tests
    /   20-30 tests      \
   /      Slower          \
  /_________________________\
         Unit Tests
    /  100+ tests         \
   /    Very Fast          \
  /___________________________\
```

**Ratio:** 100 unit : 20 integration : 5 GUI tests

### CI/CD Considerations

**GUI tests in CI require:**
- Virtual display (Xvfb)
- Accessibility services running
- GTK libraries installed
- Much longer build times

**Recommendation:** Run GUI tests:
- ✅ Nightly builds
- ✅ Release branches
- ❌ NOT on every commit (too slow)
- ❌ NOT in pull request checks (too slow)

### Example GitHub Actions Workflow

```yaml
# Separate workflow for GUI tests (runs nightly)
name: GUI Tests (Nightly)

on:
  schedule:
    - cron: '0 2 * * *'  # 2 AM daily
  workflow_dispatch:      # Manual trigger

jobs:
  gui-tests:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          libgirepository1.0-dev \
          python3-dogtail \
          xvfb \
          at-spi2-core

    - name: Install Python dependencies
      run: |
        pip install pipenv
        pipenv install --dev

    - name: Run GUI tests with Xvfb
      run: |
        xvfb-run -a pipenv run pytest tests/gui -v -m gui --timeout=120

    - name: Upload screenshots on failure
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: gui-test-screenshots
        path: tests/gui/screenshots/*.png
```

### GUI Testing Summary

**DFakeSeeder GUI automation uses:**
- **Dogtail**: GTK automation framework (THE prescribed tool)
- **pytest-xvfb**: Headless execution for CI/CD
- **20-30 comprehensive test scenarios**: See [GUI_TESTING_PLAN.md](GUI_TESTING_PLAN.md) for complete specifications

**Testing approach:**
- Target: 20-30 total GUI tests covering all critical user workflows
- Run separately from unit/integration tests (Makefile target: `make test-gui`)
- Execute in CI/CD via nightly builds only (not on every commit)
- Each test validates one complete end-to-end user workflow
- All tests must include cleanup (terminate app process)

**Test execution:**
```bash
# Local execution (requires display)
make test-gui

# Headless execution (CI/CD)
make test-gui-headless

# Or directly with pytest
pipenv run pytest tests/gui -v -m gui --xvfb
```

**For detailed test scenarios, implementation examples, and infrastructure setup**, see **[GUI_TESTING_PLAN.md](GUI_TESTING_PLAN.md)**.

**Remember:** GUI tests supplement (not replace) the comprehensive unit and integration testing that forms the foundation of the test suite.

## Priority Tests for Initial Implementation

### Phase 1: Foundation (Week 1)

**Goal**: Establish test infrastructure and cover critical new features

1. **Test Infrastructure Setup**
   - Configure pytest with pytest.ini
   - Create conftest.py with common fixtures
   - Set up coverage reporting
   - Configure CI/CD pipeline

2. **Critical Unit Tests** (NEW FEATURES)
   - `tests/unit/lib/handlers/test_torrent_folder_watcher.py`
     - Test file watching and event handling
     - Test torrent file copying logic
     - Test duplicate detection
     - Test integration with GlobalPeerManager

   - `tests/unit/domain/torrent/test_torrent.py`
     - Test bencode parsing
     - Test metadata extraction
     - Test file path handling

3. **Core Data Management**
   - `tests/unit/lib/test_model.py`
     - Test torrent addition/removal
     - Test signal emission
     - Test search filtering

   - `tests/unit/domain/test_app_settings.py`
     - Test settings loading/saving (use tmp_path)
     - Test GObject signal system
     - Test watch_folder configuration

4. **Basic Integration Test**
   - `tests/integration/test_watch_folder_integration.py`
     - End-to-end watch folder workflow
     - Test with real files and directories (tmp_path)
     - Test GlobalPeerManager integration

### Phase 2: Protocol Testing (Week 2)

**Goal**: Validate networking and protocol implementations

1. **Protocol Unit Tests**
   - `tests/unit/domain/torrent/protocols/tracker/test_http_seeder.py`
     - Test tracker announce logic
     - Mock HTTP requests with unittest.mock
     - Test response parsing

   - `tests/unit/domain/torrent/protocols/tracker/test_udp_seeder.py`
     - Test UDP protocol implementation
     - Mock socket operations
     - Test binary message format

   - `tests/unit/domain/torrent/protocols/tracker/test_multi_tracker.py`
     - Test tier system
     - Test failover logic
     - Test announce coordination

   - `tests/unit/domain/torrent/protocols/transport/test_utp_connection.py`
     - Test µTP packet handling
     - Test congestion control
     - Test connection state management

2. **Integration Tests**
   - `tests/integration/test_tracker_communication.py`
     - Multi-tracker workflow
     - Failover scenarios
     - DHT integration

   - `tests/integration/test_torrent_lifecycle.py`
     - Complete torrent workflow
     - Seeding coordination
     - Peer connection management

### Phase 3: Full Coverage (Week 3)

**Goal**: Complete test coverage for all components

1. **Remaining Unit Tests**
   - UI component logic tests (NO rendering)
   - Translation system tests
   - Utility function tests
   - Logger tests

2. **Remaining Integration Tests**
   - D-Bus integration
   - Settings persistence
   - Translation workflow
   - Performance tests

## Coverage Targets

| Component | Target Coverage |
|-----------|----------------|
| **Overall** | **100%** |
| Domain Logic | 100% |
| Protocol Implementations | 100% |
| File Handlers | 100% |
| Settings Management | 100% |
| Translation System | 100% |
| UI Component Logic | 100% |

**Note**: 100% coverage is enforced via `--cov-fail-under=100` in pytest.ini

## Makefile Targets

### Test Execution Targets

Add these targets to the project Makefile for flexible test execution:

```makefile
# Test targets
.PHONY: test test-unit test-integration test-fast test-all test-coverage

# Run all tests (unit + integration)
test-all:
	pipenv run pytest tests/ -v

# Run unit tests only (fast feedback during development)
test-unit:
	pipenv run pytest tests/unit -v -m "not slow"

# Run integration tests only
test-integration:
	pipenv run pytest tests/integration -v

# Run fast unit tests (excludes slow tests)
test-fast:
	pipenv run pytest tests/unit -v -m "not slow" -x

# Run tests with coverage report
test-coverage:
	pipenv run pytest tests/ --cov --cov-report=html --cov-report=term-missing

# Run tests in parallel for speed
test-parallel:
	pipenv run pytest tests/ -n auto -v

# Run specific test file
test-file:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=path/to/test_file.py"; \
		exit 1; \
	fi
	pipenv run pytest $(FILE) -v

# Run tests with specific seed for reproducibility
test-seed:
	@if [ -z "$(SEED)" ]; then \
		echo "Usage: make test-seed SEED=12345"; \
		exit 1; \
	fi
	pipenv run pytest tests/ -v --randomly-seed=$(SEED)
```

### Usage Examples

```bash
# Development workflow - fast unit tests
make test-unit

# Before commit - run all tests
make test-all

# Check coverage
make test-coverage

# Run specific test file
make test-file FILE=tests/unit/lib/handlers/test_torrent_folder_watcher.py

# Reproduce specific test run
make test-seed SEED=12345

# Fast parallel execution
make test-parallel
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
name: Tests

on: [push, pull_request]

jobs:
  # Run unit tests first for fast feedback
  unit-tests:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y libgirepository1.0-dev

    - name: Install dependencies
      run: |
        pip install pipenv
        pipenv install --dev

    - name: Run fast unit tests
      run: pipenv run pytest tests/unit -v -m "not slow" --cov=d_fake_seeder --cov-report=xml

    - name: Run slow unit tests
      run: pipenv run pytest tests/unit -v -m "slow"

    - name: Upload unit test coverage
      uses: codecov/codecov-action@v3
      with:
        flags: unit

  # Run integration tests after unit tests pass
  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests  # Only run if unit tests pass
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y libgirepository1.0-dev

    - name: Install dependencies
      run: |
        pip install pipenv
        pipenv install --dev

    - name: Run integration tests
      run: pipenv run pytest tests/integration -v --cov=d_fake_seeder --cov-report=xml

    - name: Upload integration test coverage
      uses: codecov/codecov-action@v3
      with:
        flags: integration

  # Final coverage check across all tests
  coverage-check:
    runs-on: ubuntu-latest
    needs: [unit-tests, integration-tests]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.12"

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y libgirepository1.0-dev

    - name: Install dependencies
      run: |
        pip install pipenv
        pipenv install --dev

    - name: Run all tests with coverage
      run: pipenv run pytest tests/ --cov=d_fake_seeder --cov-report=html --cov-report=term-missing --cov-fail-under=100

    - name: Upload final coverage report
      uses: codecov/codecov-action@v3
      with:
        flags: all
```

## Maintenance

### Regular Tasks

1. **Weekly**: Review test coverage reports
2. **Per PR**: All new code includes tests
3. **Monthly**: Review and update test fixtures
4. **Quarterly**: Audit slow tests and optimize

### Test Quality Metrics

- **Test execution time**:
  - Unit tests: <30 seconds
  - Integration tests: <3 minutes
  - Full suite: <5 minutes
- **Flaky test rate**: 0% (randomized order catches dependencies)
- **Code coverage**: 100% (strictly enforced)
- **Test-to-code ratio**: ~1:1 (lines of test code : lines of production code)
- **Test isolation**: 100% (tests pass in any order with any random seed)

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-mock Documentation](https://pytest-mock.readthedocs.io/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [GTK Testing Guide](https://pygobject.readthedocs.io/en/latest/guide/testing.html)

---

## Summary of Key Decisions

### Testing Approach
✅ **Standalone test functions** (no test classes)
✅ **Separate test functions** (no parametrize)
✅ **Standard pytest assertions** (no additional libraries)
✅ **pytest.raises for exceptions** (verify type AND message)
✅ **Yield fixtures** for explicit cleanup
✅ **Balanced test naming** (descriptive but concise)
✅ **Arrange-Act-Assert** with explicit comment markers

### Mocking Strategy
✅ **Patch where imported** (not where defined)
✅ **unittest.mock.patch** via mocker fixture
✅ **MagicMock** for creating mock objects
✅ **AsyncMock** for async operations
✅ **Set return values in tests** (not in fixtures)
✅ **with for single patch**, assignment for multiple
✅ **Flexible assertions** (assert_called, call_args)
❌ **NO monkeypatch** fixture
❌ **NO responses** library
❌ **NO pyfakefs**
❌ **NO deep nesting** of with statements

### Test Data & Assertions
✅ **Programmatic generation** in fixtures
✅ **Real filesystem** with tmp_path
✅ **Minimal valid data** (not realistic/complex)
✅ **bencodepy** for torrent file generation
✅ **Verify file contents** (not just existence)
✅ **Separate assertions** (not combined with and)
❌ **NO external test data files**

### Test Organization
✅ **Mirror source structure** exactly
✅ **100% coverage** strictly enforced
✅ **Randomized test order** to catch dependencies
✅ **Separate make targets** for unit/integration tests
✅ **Sequential CI/CD** (unit tests → integration tests → coverage check)
✅ **Test async AND sync** patterns when relevant

### Quality Targets
- **Unit tests**: <30 seconds execution time
- **Integration tests**: <3 minutes execution time
- **Code coverage**: 100% (no exceptions)
- **Flaky tests**: 0% (perfect isolation)
- **Test-to-code ratio**: 1:1

**Next Steps:**
1. Create test infrastructure (conftest.py, pytest.ini)
2. Implement Phase 1 tests (watch folder, torrent parsing)
3. Add Makefile targets (test-unit, test-integration, test-all)
4. Set up CI/CD pipeline with separate jobs
5. Achieve 100% coverage
6. Establish test maintenance workflow
