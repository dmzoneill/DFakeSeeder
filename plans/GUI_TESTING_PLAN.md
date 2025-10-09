# DFakeSeeder GUI Testing Plan

**Status:** In Progress
**Created:** 2025-10-09
**Last Updated:** 2025-10-09
**Parent Plan:** [TESTING_PLAN.md](TESTING_PLAN.md)

## Overview

This document specifies comprehensive GUI automation test scenarios for DFakeSeeder using **Dogtail** (GTK automation framework) with **pytest-xvfb** (headless execution support).

GUI tests verify end-to-end user workflows by launching the actual application and simulating real user interactions through the GTK accessibility API (AT-SPI).

## Technology Stack

- **Dogtail**: GTK automation framework using accessibility APIs
- **pytest-xvfb**: Headless execution for CI/CD
- **pytest 7.4+**: Test framework with GUI markers
- **Subprocess**: Application launch and process management

## Test Organization

```
tests/
└── gui/                              # GUI automation tests
    ├── conftest.py                   # GUI-specific fixtures and hooks
    ├── test_torrent_workflow_gui.py  # Torrent management workflows
    ├── test_settings_dialog_gui.py   # Settings dialog interactions
    ├── test_toolbar_gui.py           # Toolbar and menu interactions
    ├── test_search_gui.py            # Search and filtering workflows
    ├── test_window_state_gui.py      # Window management workflows
    └── screenshots/                  # Failure screenshots (gitignored)
        └── .gitignore
```

## GUI Test Constraints

- **Timeout**: 60 seconds per test (GUI tests are slow)
- **Execution**: Run separately from unit/integration tests
- **Target Count**: 20-30 total GUI tests maximum
- **CI/CD**: Nightly builds only, NOT on every commit
- **Cleanup**: Every test must terminate the application process

## Test Scenarios

### Category 1: Torrent Management Workflows

#### Test 1.1: Add Torrent via Toolbar Button
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_add_torrent_via_toolbar_button`

**Process:**
1. Launch DFakeSeeder application
2. Wait for main window to appear
3. Find "Add Torrent" toolbar button
4. Click button to open file chooser
5. Enter path to test torrent file
6. Click "Open" to submit
7. Verify torrent appears in torrent list

**Validates:**
- Toolbar button click interaction
- File chooser dialog opens correctly
- File path entry accepts input
- Torrent list updates with new entry
- Application doesn't crash during workflow

---

#### Test 1.2: Add Torrent via Menu
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_add_torrent_via_menu`

**Process:**
1. Launch application
2. Open "File" menu
3. Click "Add Torrent" menu item
4. File chooser dialog opens
5. Select torrent file
6. Verify torrent added to list

**Validates:**
- Menu navigation
- Menu item click handling
- Same file chooser behavior as toolbar
- Consistent torrent addition behavior

---

#### Test 1.3: Remove Torrent via Context Menu
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_remove_torrent_via_context_menu`

**Process:**
1. Launch application with pre-loaded torrent
2. Find torrent in list view
3. Right-click torrent row
4. Context menu appears
5. Click "Remove" option
6. Confirmation dialog appears
7. Click "Yes" to confirm
8. Verify torrent removed from list

**Validates:**
- Right-click context menu
- Menu item selection
- Confirmation dialog behavior
- List view update after removal
- Proper cleanup

---

#### Test 1.4: Remove Torrent via Toolbar Button
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_remove_torrent_via_toolbar_button`

**Process:**
1. Launch application with pre-loaded torrent
2. Select torrent in list
3. Click "Remove" toolbar button
4. Confirm deletion in dialog
5. Verify torrent removed

**Validates:**
- Toolbar button for removal
- Selection state handling
- Confirmation dialog
- Consistent removal behavior

---

#### Test 1.5: Pause and Resume Torrent
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_pause_and_resume_torrent`

**Process:**
1. Launch with active torrent
2. Right-click torrent
3. Select "Pause"
4. Verify status changes to "Paused"
5. Right-click again
6. Select "Resume"
7. Verify status changes to "Seeding"

**Validates:**
- Pause/Resume menu items
- Status column updates
- State persistence during session

---

#### Test 1.6: Select Multiple Torrents
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_select_multiple_torrents`

**Process:**
1. Launch with 3+ torrents
2. Click first torrent
3. Hold Ctrl, click second torrent
4. Hold Ctrl, click third torrent
5. Verify all three selected
6. Right-click selection
7. Verify context menu shows "Remove 3 Torrents"

**Validates:**
- Multi-selection with Ctrl key
- Selection state visual feedback
- Context menu adapts to selection count

---

### Category 2: Settings Dialog Workflows

#### Test 2.1: Open Settings via Menu
**File:** `test_settings_dialog_gui.py`
**Function:** `test_open_settings_via_menu`

**Process:**
1. Launch application
2. Click hamburger menu
3. Click "Preferences"
4. Verify Settings dialog opens
5. Verify dialog is modal
6. Verify all tabs visible

**Validates:**
- Menu navigation
- Dialog opening
- Modal behavior
- Tab bar rendering

---

#### Test 2.2: Navigate Settings Tabs
**File:** `test_settings_dialog_gui.py`
**Function:** `test_navigate_settings_tabs`

**Process:**
1. Open Settings dialog
2. Click "General" tab → verify content
3. Click "Connection" tab → verify content
4. Click "Peer Protocol" tab → verify content
5. Click "Advanced" tab → verify content
6. Return to "General" tab

**Validates:**
- Tab switching
- Tab content loads correctly
- No crashes during navigation
- Previous tab content clears properly

---

#### Test 2.3: Change General Settings
**File:** `test_settings_dialog_gui.py`
**Function:** `test_change_general_settings`

**Process:**
1. Open Settings dialog
2. Navigate to "General" tab
3. Find "Language" dropdown
4. Change from "English" to "Spanish"
5. Click "Apply"
6. Verify UI updates to Spanish
7. Change back to English
8. Click "OK" to close

**Validates:**
- Dropdown widget interaction
- Settings change application
- Live UI updates
- Settings persistence

---

#### Test 2.4: Change Connection Settings
**File:** `test_settings_dialog_gui.py`
**Function:** `test_change_connection_settings`

**Process:**
1. Open Settings dialog
2. Navigate to "Connection" tab
3. Find "Listening Port" spin button
4. Change value from 6881 to 7777
5. Click "Apply"
6. Reopen settings
7. Verify port shows 7777

**Validates:**
- Spin button interaction
- Settings persistence
- Settings reload from file

---

#### Test 2.5: Cancel Settings Changes
**File:** `test_settings_dialog_gui.py`
**Function:** `test_cancel_settings_changes`

**Process:**
1. Open Settings dialog
2. Change listening port to 9999
3. Click "Cancel"
4. Reopen settings
5. Verify port still shows original value

**Validates:**
- Cancel button behavior
- Changes not persisted on cancel
- Settings rollback

---

#### Test 2.6: Reset Settings to Default
**File:** `test_settings_dialog_gui.py`
**Function:** `test_reset_settings_to_default`

**Process:**
1. Change multiple settings
2. Open Settings dialog
3. Navigate to "Advanced" tab
4. Click "Reset to Defaults" button
5. Confirmation dialog appears
6. Click "Yes"
7. Verify all settings return to defaults

**Validates:**
- Reset button functionality
- Confirmation dialog
- Settings restoration
- UI updates reflect defaults

---

### Category 3: Toolbar and Menu Interactions

#### Test 3.1: All Toolbar Buttons Clickable
**File:** `test_toolbar_gui.py`
**Function:** `test_all_toolbar_buttons_clickable`

**Process:**
1. Launch application
2. Find all toolbar buttons
3. Verify each button:
   - Has accessible name
   - Is clickable (no crash)
   - Shows appropriate response

**Validates:**
- All toolbar buttons functional
- Accessibility labels present
- No crashes on click

---

#### Test 3.2: Hamburger Menu Navigation
**File:** `test_toolbar_gui.py`
**Function:** `test_hamburger_menu_navigation`

**Process:**
1. Launch application
2. Click hamburger menu button
3. Verify menu opens
4. Verify menu items:
   - "Preferences"
   - "About"
   - "Quit"
5. Click outside menu to close
6. Verify menu closes

**Validates:**
- Menu toggle behavior
- Menu item visibility
- Menu dismiss on outside click

---

#### Test 3.3: About Dialog
**File:** `test_toolbar_gui.py`
**Function:** `test_about_dialog`

**Process:**
1. Open hamburger menu
2. Click "About"
3. About dialog opens
4. Verify dialog contains:
   - Application name
   - Version number
   - Copyright
   - License
5. Click "Close"
6. Verify dialog closes

**Validates:**
- About dialog opening
- Dialog content rendering
- Dialog closing

---

#### Test 3.4: Quit via Menu
**File:** `test_toolbar_gui.py`
**Function:** `test_quit_via_menu`

**Process:**
1. Launch application
2. Open hamburger menu
3. Click "Quit"
4. Confirmation dialog may appear (if enabled)
5. Confirm quit
6. Verify application closes

**Validates:**
- Quit menu item
- Optional confirmation dialog
- Graceful application shutdown

---

### Category 4: Search and Filtering Workflows

#### Test 4.1: Search by Torrent Name
**File:** `test_search_gui.py`
**Function:** `test_search_by_torrent_name`

**Process:**
1. Launch with 5+ torrents loaded
2. Find search entry in toolbar
3. Type partial torrent name
4. Verify list filters to matching torrents
5. Clear search
6. Verify full list restored

**Validates:**
- Search entry interaction
- Live filtering as typing
- Filter matching behavior
- Clear functionality

---

#### Test 4.2: Search with No Results
**File:** `test_search_gui.py`
**Function:** `test_search_with_no_results`

**Process:**
1. Launch with torrents
2. Enter search term with no matches
3. Verify empty list message appears
4. Clear search
5. Verify torrents return

**Validates:**
- Empty state handling
- Empty message visibility
- Recovery from empty state

---

#### Test 4.3: Search Case Insensitivity
**File:** `test_search_gui.py`
**Function:** `test_search_case_insensitivity`

**Process:**
1. Launch with torrent "Ubuntu.torrent"
2. Search "ubuntu" (lowercase)
3. Verify torrent found
4. Search "UBUNTU" (uppercase)
5. Verify torrent found

**Validates:**
- Case-insensitive search
- Consistent matching behavior

---

#### Test 4.4: Search Fuzzy Matching
**File:** `test_search_gui.py`
**Function:** `test_search_fuzzy_matching`

**Process:**
1. Launch with torrent "Debian-12-amd64.iso.torrent"
2. Search "dbian 12"
3. Verify torrent found with fuzzy matching
4. Search "debian amd"
5. Verify torrent found

**Validates:**
- Fuzzy matching algorithm
- Substring matching
- Word order flexibility

---

### Category 5: Window State and Management

#### Test 5.1: Window Resize Persistence
**File:** `test_window_state_gui.py`
**Function:** `test_window_resize_persistence`

**Process:**
1. Launch application
2. Resize window to 1200×800
3. Close application
4. Relaunch application
5. Verify window opens at 1200×800

**Validates:**
- Window size tracking
- Settings save on close
- Settings restore on launch

---

#### Test 5.2: Window Position Persistence
**File:** `test_window_state_gui.py`
**Function:** `test_window_position_persistence`

**Process:**
1. Launch application
2. Move window to position (100, 100)
3. Close application
4. Relaunch
5. Verify window appears at (100, 100)

**Validates:**
- Window position tracking
- Position settings persistence

---

#### Test 5.3: Maximize and Restore
**File:** `test_window_state_gui.py`
**Function:** `test_maximize_and_restore`

**Process:**
1. Launch application
2. Maximize window
3. Verify window fills screen
4. Restore window
5. Verify window returns to previous size

**Validates:**
- Maximize button
- Window state changes
- Restore functionality

---

#### Test 5.4: Minimize to Tray (if enabled)
**File:** `test_window_state_gui.py`
**Function:** `test_minimize_to_tray`

**Process:**
1. Enable "Minimize to tray" in settings
2. Minimize window
3. Verify window hidden
4. Verify tray icon visible
5. Click tray icon
6. Verify window restored

**Validates:**
- Minimize to tray setting
- Window hiding
- Tray icon creation
- Tray icon click handling

---

#### Test 5.5: Close to Tray (if enabled)
**File:** `test_window_state_gui.py`
**Function:** `test_close_to_tray`

**Process:**
1. Enable "Close to tray" in settings
2. Click window close button (X)
3. Verify window hidden (not quit)
4. Verify tray icon visible
5. Click tray icon → "Quit"
6. Verify application quits

**Validates:**
- Close to tray setting
- Window close interception
- Tray menu interaction
- Quit from tray

---

### Category 6: Torrent Details Workflows

#### Test 6.1: Open Torrent Details
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_open_torrent_details`

**Process:**
1. Launch with torrents
2. Double-click torrent row
3. Verify details pane expands
4. Verify details tabs visible:
   - Status
   - Files
   - Peers
   - Trackers

**Validates:**
- Double-click handling
- Details pane expansion
- Tab visibility

---

#### Test 6.2: Navigate Torrent Details Tabs
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_navigate_torrent_details_tabs`

**Process:**
1. Open torrent details
2. Click "Status" tab → verify content
3. Click "Files" tab → verify file list
4. Click "Peers" tab → verify peer list
5. Click "Trackers" tab → verify tracker list

**Validates:**
- Tab switching in details pane
- Tab content rendering
- No crashes during navigation

---

#### Test 6.3: Close Torrent Details
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_close_torrent_details`

**Process:**
1. Open torrent details
2. Find close button or pane toggle
3. Click to close
4. Verify details pane collapses

**Validates:**
- Close button functionality
- Pane collapse animation
- Layout adjustment

---

### Category 7: Drag and Drop Workflows

#### Test 7.1: Drag Torrent File to Window
**File:** `test_toolbar_gui.py`
**Function:** `test_drag_torrent_file_to_window`

**Process:**
1. Launch application
2. Simulate drag of .torrent file from file manager
3. Drop onto application window
4. Verify torrent added to list

**Validates:**
- Drag and drop support
- File type validation
- Automatic torrent addition

---

#### Test 7.2: Drag Invalid File to Window
**File:** `test_toolbar_gui.py`
**Function:** `test_drag_invalid_file_to_window`

**Process:**
1. Launch application
2. Simulate drag of non-torrent file
3. Drop onto window
4. Verify error message appears
5. Verify no invalid entry in list

**Validates:**
- File type validation
- Error handling for invalid files
- User feedback on errors

---

### Category 8: Keyboard Shortcuts

#### Test 8.1: Ctrl+O to Add Torrent
**File:** `test_toolbar_gui.py`
**Function:** `test_keyboard_shortcut_add_torrent`

**Process:**
1. Launch application
2. Focus main window
3. Press Ctrl+O
4. Verify file chooser opens
5. Select torrent
6. Verify torrent added

**Validates:**
- Keyboard shortcut handling
- File chooser via shortcut
- Same behavior as toolbar button

---

#### Test 8.2: Delete Key to Remove Torrent
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_keyboard_shortcut_delete_torrent`

**Process:**
1. Launch with torrents
2. Select torrent
3. Press Delete key
4. Confirmation dialog appears
5. Press Enter to confirm
6. Verify torrent removed

**Validates:**
- Delete key handling
- Keyboard navigation in dialogs
- Torrent removal via keyboard

---

#### Test 8.3: Ctrl+F to Focus Search
**File:** `test_search_gui.py`
**Function:** `test_keyboard_shortcut_focus_search`

**Process:**
1. Launch application
2. Press Ctrl+F
3. Verify search entry receives focus
4. Type search term
5. Verify filtering works

**Validates:**
- Search shortcut
- Focus management
- Keyboard-only workflow

---

#### Test 8.4: Escape to Clear Search
**File:** `test_search_gui.py`
**Function:** `test_keyboard_shortcut_clear_search`

**Process:**
1. Enter search term
2. Press Escape key
3. Verify search cleared
4. Verify focus returns to list

**Validates:**
- Escape key handling
- Search clearing
- Focus restoration

---

### Category 9: Accessibility and Localization

#### Test 9.1: Tab Navigation Through Interface
**File:** `test_toolbar_gui.py`
**Function:** `test_tab_navigation`

**Process:**
1. Launch application
2. Press Tab repeatedly
3. Verify focus moves through:
   - Toolbar buttons
   - Search entry
   - Torrent list
   - Details pane (if open)
4. Verify focus visible
5. Verify focus order logical

**Validates:**
- Tab navigation
- Focus indicators
- Logical tab order
- Accessibility compliance

---

#### Test 9.2: Screen Reader Labels
**File:** `test_toolbar_gui.py`
**Function:** `test_screen_reader_labels`

**Process:**
1. Launch application
2. Query accessibility tree
3. Verify all widgets have:
   - Accessible name
   - Accessible role
   - Accessible description (where appropriate)

**Validates:**
- Accessibility API compliance
- Widget labeling
- Screen reader support

---

#### Test 9.3: Language Switching (Spanish)
**File:** `test_settings_dialog_gui.py`
**Function:** `test_language_switch_spanish`

**Process:**
1. Launch application
2. Open Settings
3. Change language to Spanish
4. Apply changes
5. Verify UI elements show Spanish:
   - Menu items
   - Toolbar tooltips
   - Column headers
   - Dialog titles
6. Change back to English

**Validates:**
- Runtime language switching
- Translation coverage
- No untranslated strings
- No layout issues with longer text

---

### Category 10: Error Handling and Edge Cases

#### Test 10.1: Add Corrupted Torrent File
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_add_corrupted_torrent_file`

**Process:**
1. Create invalid torrent file
2. Attempt to add via toolbar
3. Verify error dialog appears
4. Verify error message is clear
5. Click OK to dismiss
6. Verify application remains stable

**Validates:**
- Error detection
- User-friendly error messages
- Error recovery
- Application stability

---

#### Test 10.2: Add Duplicate Torrent
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_add_duplicate_torrent`

**Process:**
1. Add torrent to list
2. Attempt to add same torrent again
3. Verify duplicate warning appears
4. Choose to skip
5. Verify only one instance in list

**Validates:**
- Duplicate detection
- Warning dialog
- User choice handling
- List integrity

---

#### Test 10.3: Remove All Torrents
**File:** `test_torrent_workflow_gui.py`
**Function:** `test_remove_all_torrents`

**Process:**
1. Launch with 3 torrents
2. Select all (Ctrl+A)
3. Press Delete
4. Confirm removal
5. Verify empty list
6. Verify empty state message
7. Add new torrent
8. Verify works correctly

**Validates:**
- Select all functionality
- Bulk deletion
- Empty state handling
- Recovery from empty state

---

#### Test 10.4: Window Too Small
**File:** `test_window_state_gui.py`
**Function:** `test_window_minimum_size`

**Process:**
1. Launch application
2. Attempt to resize below minimum
3. Verify window stops at minimum size
4. Verify UI still usable
5. Verify no overlapping widgets

**Validates:**
- Minimum window size enforcement
- Layout adaptability
- UI usability at minimum size

---

## Test Infrastructure

### conftest.py for GUI Tests

```python
import pytest
import subprocess
import time
from dogtail.tree import root
from dogtail.config import config
from dogtail.utils import screenshot

# Configure Dogtail
config.searchCutoffCount = 20
config.searchWarningThreshold = 3


@pytest.fixture
def dfakeseeder_app():
    """
    Launch DFakeSeeder application and return app handle

    Provides automatic cleanup on test completion
    """
    # Launch application
    app_process = subprocess.Popen(['dfakeseeder'])
    time.sleep(2)  # Wait for app to start

    # Get application handle via accessibility API
    app = root.application('dfakeseeder')

    yield app

    # Cleanup - terminate application
    app_process.terminate()
    try:
        app_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        app_process.kill()


@pytest.fixture
def dfakeseeder_with_torrents(tmp_path):
    """
    Launch DFakeSeeder with pre-loaded test torrents

    Creates 3 test torrent files and loads them
    """
    import bencodepy

    # Create test torrents
    torrents = []
    for i in range(3):
        torrent_file = tmp_path / f"test_{i}.torrent"
        torrent_data = {
            b'announce': b'http://tracker.example.com/announce',
            b'info': {
                b'name': f'Test Torrent {i}'.encode(),
                b'piece length': 16384,
                b'pieces': b'\x00' * 20,
                b'length': 1024 * (i + 1),
            }
        }
        torrent_file.write_bytes(bencodepy.encode(torrent_data))
        torrents.append(str(torrent_file))

    # Launch application
    app_process = subprocess.Popen(['dfakeseeder'])
    time.sleep(2)

    app = root.application('dfakeseeder')

    # Add torrents via GUI
    for torrent_path in torrents:
        add_button = app.child('Add Torrent', roleName='push button')
        add_button.click()
        time.sleep(0.5)

        file_dialog = app.child('Select Torrent File', roleName='dialog')
        path_entry = file_dialog.child(roleName='text')
        path_entry.text = torrent_path

        open_button = file_dialog.child('Open', roleName='push button')
        open_button.click()
        time.sleep(0.5)

    yield app

    # Cleanup
    app_process.terminate()
    try:
        app_process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        app_process.kill()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Take screenshot on GUI test failure"""
    outcome = yield
    rep = outcome.get_result()

    if rep.when == "call" and rep.failed:
        if "gui" in item.keywords:
            screenshot_path = f"tests/gui/screenshots/{item.name}.png"
            try:
                screenshot(screenshot_path)
                print(f"Screenshot saved: {screenshot_path}")
            except Exception as e:
                print(f"Failed to save screenshot: {e}")
```

### pytest.ini Markers

```ini
markers =
    gui: GUI automation tests (very slow, requires display or xvfb)
```

## Makefile Targets

```makefile
# GUI test targets
.PHONY: test-gui test-gui-headless

# Run GUI tests with display
test-gui:
	pipenv run pytest tests/gui -v -m gui

# Run GUI tests headlessly (CI/CD)
test-gui-headless:
	pipenv run pytest tests/gui -v -m gui --xvfb
```

## CI/CD Integration

```yaml
# .github/workflows/gui-tests-nightly.yml
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

## Test Execution Guidelines

### Local Development

```bash
# Run all GUI tests (requires display)
make test-gui

# Run specific GUI test file
pipenv run pytest tests/gui/test_torrent_workflow_gui.py -v

# Run specific test function
pipenv run pytest tests/gui/test_torrent_workflow_gui.py::test_add_torrent_via_toolbar_button -v

# Run with verbose Dogtail output
pipenv run pytest tests/gui -v -s -m gui
```

### CI/CD Execution

```bash
# Headless execution
make test-gui-headless

# Or directly
xvfb-run -a pipenv run pytest tests/gui -v -m gui
```

## Best Practices

### DO:
- Use explicit waits (`time.sleep()`) after actions that trigger UI updates
- Verify widgets via accessibility tree (name, role, visible state)
- Include cleanup in `finally` blocks or fixtures
- Test one complete user workflow per test function
- Take screenshots on failure for debugging
- Use descriptive widget names for better test maintainability

### DON'T:
- Test business logic (covered by unit tests)
- Test internal application state (use integration tests)
- Make assumptions about timing (add explicit waits)
- Share state between tests (use fixtures for setup)
- Commit failure screenshots to repository
- Run GUI tests on every commit (too slow for CI/CD)

## Test Coverage Target

- **Total GUI Tests**: 20-30 tests
- **Critical Workflows**: 100% coverage
- **Execution Time**: 5-10 minutes for full GUI test suite
- **CI/CD Frequency**: Nightly builds only

## Maintenance

### Weekly:
- Review GUI test failures from nightly builds
- Update screenshots reference if UI changes
- Verify accessibility labels on new widgets

### Per Release:
- Run full GUI test suite locally
- Update tests for UI/UX changes
- Verify all tests pass before release

### Quarterly:
- Audit slow GUI tests and optimize
- Review test coverage for new features
- Update Dogtail/pytest-xvfb versions

---

**Next Steps:**
1. Implement conftest.py with fixtures
2. Create test files for each category
3. Implement first 5 critical tests (torrent add, settings, search, window state, quit)
4. Set up Makefile targets
5. Configure CI/CD nightly builds
6. Expand to full 20-30 test coverage
