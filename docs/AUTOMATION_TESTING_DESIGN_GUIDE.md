# DFakeSeeder Automation Testing Design Guide

**Version**: 1.0.0
**Last Updated**: 2025-12-09
**Author**: Claude Code
**Status**: Implementation Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Testing Infrastructure Overview](#testing-infrastructure-overview)
3. [GTK4 UI Testing Architecture](#gtk4-ui-testing-architecture)
4. [Settings Dialog Test Implementation](#settings-dialog-test-implementation)
5. [Test Framework Selection & Justification](#test-framework-selection--justification)
6. [Detailed Test Scenarios](#detailed-test-scenarios)
7. [Implementation Roadmap](#implementation-roadmap)
8. [Code Examples & Templates](#code-examples--templates)
9. [CI/CD Integration](#cicd-integration)
10. [Troubleshooting & Best Practices](#troubleshooting--best-practices)

---

## 1. Executive Summary

### Purpose
This guide provides a comprehensive blueprint for implementing automated UI testing for the DFakeSeeder GTK4 application, with specific focus on testing settings dialog interactions and verifying application behavior changes.

### Key Objectives
- ✅ Click every setting in the settings dialog programmatically
- ✅ Verify that each setting change produces the expected application behavior
- ✅ Ensure settings persistence across application restarts
- ✅ Test signal propagation and UI updates
- ✅ Validate settings with edge cases and invalid inputs
- ✅ Achieve >80% test coverage for settings components

### Technology Stack
- **Testing Framework**: pytest (8.0.0+)
- **GTK Testing**: pytest-gtk + GLib.test_* utilities
- **Mocking**: pytest-mock + unittest.mock
- **Async Testing**: pytest-asyncio
- **Coverage**: pytest-cov
- **CI/CD**: GitHub Actions (Xvfb for headless GTK)

---

## 2. Testing Infrastructure Overview

### Current State Analysis

#### Existing Test Infrastructure ✅
```
tests/
├── conftest.py                 # Root pytest configuration
├── fixtures/
│   ├── common_fixtures.py      # Shared test fixtures
│   └── mock_data.py           # Mock data generators
├── unit/
│   ├── test_setup.py          # Infrastructure tests
│   └── domain/torrent/
│       └── test_torrent_shutdown.py
└── integration/               # Integration tests (empty)
```

#### Test Configuration (conftest.py)
```python
# Key Testing Principles (from conftest.py):
✅ NO test classes (standalone functions only)
✅ NO autouse fixtures (explicit fixture usage)
✅ Use unittest.mock.patch (NOT monkeypatch)
✅ Use real filesystem with tmp_path (NOT pyfakefs)
✅ 100ms timeout for unit tests
✅ Arrange-Act-Assert pattern
```

#### Pytest Markers
```python
@pytest.mark.unit              # Fast, isolated tests (<100ms)
@pytest.mark.integration       # Multi-component tests
@pytest.mark.slow             # Tests >1 second
@pytest.mark.requires_gtk     # Tests needing GTK initialization
@pytest.mark.requires_network # Tests needing network
```

### Gap Analysis

#### Missing Components ⚠️
1. **GTK UI Testing Infrastructure**
   - No GTK test fixtures
   - No UI interaction helpers
   - No headless display configuration

2. **Settings Testing**
   - No settings dialog tests
   - No settings persistence tests
   - No signal propagation tests

3. **Integration Tests**
   - Empty integration test directory
   - No end-to-end workflow tests

---

## 3. GTK4 UI Testing Architecture

### GTK4 Testing Challenges

#### Challenge 1: Display Server Requirement
GTK4 applications require a display server to initialize widgets.

**Solutions**:
- **Development**: Use Xvfb (X Virtual Frame Buffer)
- **CI/CD**: GitHub Actions with `xvfb-run`
- **Containerized**: Docker with virtual display

#### Challenge 2: Async Event Loop
GTK uses GLib main loop for events and signals.

**Solutions**:
- Use `GLib.MainLoop` for async operations
- Implement timeout-based event processing
- Use `GLib.idle_add()` for deferred execution

#### Challenge 3: Widget Accessibility
Need to access widgets programmatically for testing.

**Solutions**:
- Use `Gtk.Builder.get_object()` with widget IDs
- Implement widget introspection helpers
- Create custom widget query functions

### GTK Test Infrastructure Design

#### Architecture Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                   Test Execution Environment                 │
├─────────────────────────────────────────────────────────────┤
│  Xvfb Virtual Display (or Wayland equivalent)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Pytest Test Runner                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      GTK Test Fixtures (conftest.py)                 │  │
│  │  - gtk_app: Application instance                     │  │
│  │  - gtk_builder: UI builder                           │  │
│  │  - settings_dialog: Settings window                  │  │
│  │  - mock_app_settings: Settings backend               │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      UI Interaction Helpers                          │  │
│  │  - click_widget()                                    │  │
│  │  - set_switch_state()                                │  │
│  │  - select_dropdown_item()                            │  │
│  │  - enter_text()                                      │  │
│  │  - wait_for_signal()                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      DFakeSeeder Application Under Test              │  │
│  │  ┌────────────────┐  ┌──────────────────┐           │  │
│  │  │ SettingsDialog │  │  AppSettings     │           │  │
│  │  └────────────────┘  └──────────────────┘           │  │
│  │           │                    │                      │  │
│  │           ▼                    ▼                      │  │
│  │  ┌────────────────────────────────────┐             │  │
│  │  │   Individual Settings Tabs         │             │  │
│  │  │  - GeneralTab                      │             │  │
│  │  │  - ConnectionTab                   │             │  │
│  │  │  - PeerProtocolTab                 │             │  │
│  │  │  - SpeedTab                        │             │  │
│  │  │  - AdvancedTab                     │             │  │
│  │  └────────────────────────────────────┘             │  │
│  └──────────────────────────────────────────────────────┘  │
│                         │                                   │
│                         ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │      Assertion & Verification Layer                  │  │
│  │  - verify_setting_applied()                          │  │
│  │  - verify_ui_updated()                               │  │
│  │  - verify_signal_emitted()                           │  │
│  │  - verify_persistence()                              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Settings Dialog Test Implementation

### Settings Architecture Analysis

#### Settings Dialog Structure
```
SettingsDialog (settings_dialog.py)
├── settings_window (GtkWindow)
└── settings_notebook (GtkNotebook)
    ├── GeneralTab
    │   ├── settings_auto_start (GtkSwitch)
    │   ├── settings_start_minimized (GtkSwitch)
    │   ├── settings_minimize_to_tray (GtkSwitch)
    │   ├── settings_language (GtkDropDown)
    │   ├── settings_theme (GtkDropDown)
    │   ├── settings_color_scheme (GtkDropDown)
    │   └── settings_seeding_profile (GtkDropDown)
    ├── ConnectionTab
    │   ├── settings_listening_port (GtkSpinButton)
    │   ├── settings_enable_upnp (GtkSwitch)
    │   ├── settings_max_connections (GtkSpinButton)
    │   └── settings_proxy_* (various)
    ├── PeerProtocolTab
    │   ├── settings_handshake_timeout (GtkSpinButton)
    │   ├── settings_message_timeout (GtkSpinButton)
    │   └── settings_keepalive_interval (GtkSpinButton)
    ├── SpeedTab
    │   ├── settings_upload_speed (GtkSpinButton)
    │   ├── settings_download_speed (GtkSpinButton)
    │   └── settings_alternative_speed_* (various)
    ├── BitTorrentTab
    │   ├── settings_enable_dht (GtkSwitch)
    │   ├── settings_enable_pex (GtkSwitch)
    │   └── settings_user_agent (GtkComboBoxText)
    ├── AdvancedTab
    │   ├── settings_log_level (GtkDropDown)
    │   ├── settings_tickspeed (GtkSpinButton)
    │   └── settings_debug_mode (GtkSwitch)
    └── ... (additional tabs)
```

#### Settings Signal Flow
```
User Interaction
    │
    ▼
Widget Signal Emitted (e.g., "state-set", "notify::selected")
    │
    ▼
Tab Signal Handler (e.g., on_auto_start_changed)
    │
    ▼
AppSettings.set(key, value)
    │
    ▼
AppSettings emits "attribute-changed" signal
    │
    ▼
Application Components React
    │
    ├─► UI updates
    ├─► Settings file written
    └─► Behavior changes applied
```

### Test Strategy

#### Testing Levels
1. **Unit Tests**: Individual widget interactions
2. **Integration Tests**: Full settings dialog workflows
3. **End-to-End Tests**: Settings persistence across restarts

#### Coverage Goals
```
Component                    Target Coverage
─────────────────────────────────────────────
SettingsDialog               95%
Individual Settings Tabs     90%
AppSettings                  95%
Settings Persistence         100%
Signal Propagation           90%
UI Updates                   85%
─────────────────────────────────────────────
Overall Target               90%
```

---

## 5. Test Framework Selection & Justification

### Primary Framework: pytest

**Justification**:
- ✅ Already integrated (pytest 8.0.0+)
- ✅ Rich plugin ecosystem
- ✅ Excellent fixture system
- ✅ Parallel test execution (pytest-xdist)
- ✅ Clear test output and reporting

### GTK Testing Libraries

#### Option 1: pytest-gtk (Recommended)
```bash
pip install pytest-gtk
```

**Pros**:
- Native pytest integration
- Provides `gtk_app` fixture
- Handles GLib event loop
- Xvfb integration

**Cons**:
- Limited documentation
- May need custom helpers

#### Option 2: dogtail (Alternative)
```bash
pip install dogtail
```

**Pros**:
- Full accessibility tree navigation
- Record/playback capabilities
- Well-documented

**Cons**:
- Heavyweight
- Requires AT-SPI
- Slower execution

**Decision**: Use pytest-gtk + custom helpers for optimal control

### Mock Strategy

#### What to Mock
```python
✅ Mock: External services (network, filesystem writes outside tmp_path)
✅ Mock: Heavy initialization (torrent loading, peer connections)
✅ Mock: Time-dependent operations (GLib.timeout_add)

❌ Don't Mock: GTK widgets (test real widgets)
❌ Don't Mock: AppSettings (test real settings behavior)
❌ Don't Mock: Signal system (test real signal propagation)
```

---

## 6. Detailed Test Scenarios

### 6.1 General Tab Tests

#### Test: Auto-Start Setting

**Test ID**: `test_general_tab_auto_start_toggle`

**Objective**: Verify that toggling auto-start switch updates AppSettings and persists to disk.

**Preconditions**:
- Settings dialog is open
- General tab is active
- Auto-start is initially off

**Test Steps**:
```python
def test_general_tab_auto_start_toggle(settings_dialog, mock_app_settings, tmp_path):
    """Test auto-start toggle updates settings and persists."""
    # Arrange
    general_tab = settings_dialog.tabs[0]  # Assuming GeneralTab is first
    auto_start_widget = general_tab.get_widget("auto_start")
    settings_file = tmp_path / "settings.json"

    # Verify initial state
    assert auto_start_widget.get_active() == False
    assert mock_app_settings.get("auto_start") == False

    # Act - Toggle the switch
    click_switch(auto_start_widget, True)
    process_gtk_events()  # Process GTK event loop

    # Assert - Verify AppSettings updated
    assert mock_app_settings.get("auto_start") == True

    # Assert - Verify signal emitted
    assert_signal_emitted(
        mock_app_settings,
        "attribute-changed",
        ["auto_start", True]
    )

    # Assert - Verify persistence
    wait_for_file_write(settings_file)
    saved_settings = json.loads(settings_file.read_text())
    assert saved_settings["auto_start"] == True

    # Act - Toggle back
    click_switch(auto_start_widget, False)
    process_gtk_events()

    # Assert - Verify reverted
    assert mock_app_settings.get("auto_start") == False
```

**Expected Results**:
- ✅ Widget state changes to active
- ✅ AppSettings.auto_start becomes True
- ✅ "attribute-changed" signal emitted
- ✅ Settings file updated on disk
- ✅ Toggling back reverses changes

**Error Cases**:
- Settings file write failure
- Signal handler exception
- Invalid state transition

---

#### Test: Language Selection

**Test ID**: `test_general_tab_language_selection`

**Objective**: Verify language dropdown selection updates UI language and persists.

**Test Steps**:
```python
@pytest.mark.requires_gtk
def test_general_tab_language_selection(
    settings_dialog,
    mock_app_settings,
    mock_model,
    tmp_path
):
    """Test language selection updates UI and persists."""
    # Arrange
    general_tab = settings_dialog.tabs[0]
    language_dropdown = general_tab.get_widget("language_dropdown")

    # Supported languages from language_config.py
    languages = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja"]

    for lang_code in languages:
        # Act - Select language
        select_dropdown_by_id(language_dropdown, lang_code)
        process_gtk_events()

        # Assert - Settings updated
        assert mock_app_settings.get("language") == lang_code

        # Assert - Model notified (for UI translation refresh)
        mock_model.translation_manager.set_language.assert_called_with(lang_code)

        # Assert - Persistence
        wait_for_file_write(tmp_path / "settings.json")
        settings = json.loads((tmp_path / "settings.json").read_text())
        assert settings["language"] == lang_code
```

**Expected Results**:
- ✅ Dropdown selection updates
- ✅ AppSettings.language changes
- ✅ TranslationManager.set_language() called
- ✅ UI widgets refresh with new language
- ✅ Settings persisted to disk

---

#### Test: Theme and Color Scheme

**Test ID**: `test_general_tab_theme_color_scheme`

**Objective**: Verify theme style and color scheme changes apply to UI.

**Test Steps**:
```python
@pytest.mark.requires_gtk
def test_general_tab_theme_color_scheme(settings_dialog, mock_app_settings):
    """Test theme and color scheme changes apply to main window."""
    # Arrange
    general_tab = settings_dialog.tabs[0]
    theme_dropdown = general_tab.get_widget("settings_theme")
    color_scheme_dropdown = general_tab.get_widget("settings_color_scheme")
    main_window = settings_dialog.parent_window

    # Test Theme Styles
    theme_styles = ["system", "deluge", "modern_chunky"]
    for theme in theme_styles:
        # Act
        select_dropdown_by_string(theme_dropdown, theme)
        process_gtk_events()

        # Assert - CSS class applied
        assert has_css_class(main_window, f"theme-{theme}")
        assert mock_app_settings.get("ui_settings.theme_style") == theme

    # Test Color Schemes
    color_schemes = ["auto", "light", "dark"]
    for scheme in color_schemes:
        # Act
        select_dropdown_by_string(color_scheme_dropdown, scheme)
        process_gtk_events()

        # Assert - Color scheme applied
        if scheme == "dark":
            assert has_css_class(main_window, "dark")
        elif scheme == "light":
            assert not has_css_class(main_window, "dark")

        assert mock_app_settings.get("ui_settings.color_scheme") == scheme
```

**Expected Results**:
- ✅ Theme CSS classes applied to main window
- ✅ Color scheme changes window appearance
- ✅ Settings updated in AppSettings
- ✅ Visual changes are visible (for manual verification)

---

### 6.2 Connection Tab Tests

#### Test: Listening Port Configuration

**Test ID**: `test_connection_tab_listening_port`

**Objective**: Verify listening port spin button updates port and validates range.

**Test Steps**:
```python
@pytest.mark.requires_gtk
def test_connection_tab_listening_port(settings_dialog, mock_app_settings):
    """Test listening port configuration with validation."""
    # Arrange
    connection_tab = get_tab_by_name(settings_dialog, "Connection")
    port_spinbutton = connection_tab.get_widget("settings_listening_port")

    # Test valid ports
    valid_ports = [6881, 8080, 51413, 6969, 7000]
    for port in valid_ports:
        # Act
        set_spinbutton_value(port_spinbutton, port)
        process_gtk_events()

        # Assert
        assert mock_app_settings.get("seeders.listening_port") == port
        assert port_spinbutton.get_value() == port

    # Test edge cases
    edge_cases = [
        (1024, True, "Minimum valid port"),
        (65535, True, "Maximum valid port"),
        (1023, False, "Below minimum"),
        (65536, False, "Above maximum"),
        (-1, False, "Negative port"),
        (0, False, "Zero port"),
    ]

    for port, should_succeed, description in edge_cases:
        # Act
        try:
            set_spinbutton_value(port_spinbutton, port)
            process_gtk_events()

            if should_succeed:
                # Assert - Valid port accepted
                assert mock_app_settings.get("seeders.listening_port") == port
            else:
                # Assert - Invalid port rejected
                pytest.fail(f"Should have rejected invalid port: {description}")
        except ValueError:
            # Assert - Exception raised for invalid port
            if should_succeed:
                pytest.fail(f"Should have accepted valid port: {description}")
```

**Expected Results**:
- ✅ Valid ports (1024-65535) accepted
- ✅ Invalid ports rejected with error
- ✅ Port setting updated in AppSettings
- ✅ Validation messages displayed to user

---

#### Test: UPnP Toggle

**Test ID**: `test_connection_tab_upnp_toggle`

**Test Steps**:
```python
@pytest.mark.requires_gtk
def test_connection_tab_upnp_toggle(settings_dialog, mock_app_settings, mocker):
    """Test UPnP toggle affects port forwarding."""
    # Arrange
    connection_tab = get_tab_by_name(settings_dialog, "Connection")
    upnp_switch = connection_tab.get_widget("settings_enable_upnp")

    # Mock UPnP port mapping service
    mock_upnp_service = mocker.patch(
        "d_fake_seeder.domain.torrent.upnp_manager.UPnPManager"
    )

    # Act - Enable UPnP
    click_switch(upnp_switch, True)
    process_gtk_events()

    # Assert
    assert mock_app_settings.get("connection.enable_upnp") == True
    mock_upnp_service.enable_port_forwarding.assert_called_once()

    # Act - Disable UPnP
    click_switch(upnp_switch, False)
    process_gtk_events()

    # Assert
    assert mock_app_settings.get("connection.enable_upnp") == False
    mock_upnp_service.disable_port_forwarding.assert_called_once()
```

**Expected Results**:
- ✅ UPnP service enabled/disabled
- ✅ Port forwarding configured
- ✅ Setting persisted

---

### 6.3 Speed Tab Tests

#### Test: Upload/Download Speed Limits

**Test ID**: `test_speed_tab_speed_limits`

**Test Steps**:
```python
@pytest.mark.requires_gtk
def test_speed_tab_speed_limits(settings_dialog, mock_app_settings):
    """Test upload/download speed limit configuration."""
    # Arrange
    speed_tab = get_tab_by_name(settings_dialog, "Speed")
    upload_spinbutton = speed_tab.get_widget("settings_upload_speed")
    download_spinbutton = speed_tab.get_widget("settings_download_speed")

    # Test speed configurations
    speed_configs = [
        (50, 500, "Conservative"),
        (200, 2000, "Balanced"),
        (0, 0, "Unlimited"),
        (1000, 10000, "Aggressive"),
    ]

    for upload, download, description in speed_configs:
        # Act
        set_spinbutton_value(upload_spinbutton, upload)
        set_spinbutton_value(download_spinbutton, download)
        process_gtk_events()

        # Assert
        assert mock_app_settings.get("upload_speed") == upload
        assert mock_app_settings.get("download_speed") == download

        # Verify traffic simulator uses new limits
        # (Would need to check actual traffic pattern generation)
```

**Expected Results**:
- ✅ Speed limits updated
- ✅ Traffic simulator respects new limits
- ✅ Zero (0) interpreted as unlimited

---

### 6.4 Peer Protocol Tab Tests

#### Test: Timeout Settings

**Test ID**: `test_peer_protocol_tab_timeouts`

**Test Steps**:
```python
@pytest.mark.requires_gtk
def test_peer_protocol_tab_timeouts(settings_dialog, mock_app_settings):
    """Test peer protocol timeout configurations."""
    # Arrange
    peer_protocol_tab = get_tab_by_name(settings_dialog, "Peer Protocol")

    timeout_widgets = {
        "handshake": peer_protocol_tab.get_widget("settings_handshake_timeout"),
        "message_read": peer_protocol_tab.get_widget("settings_message_timeout"),
        "keepalive": peer_protocol_tab.get_widget("settings_keepalive_interval"),
    }

    # Test timeout configurations
    timeout_configs = {
        "handshake": [10.0, 30.0, 60.0, 120.0],
        "message_read": [30.0, 60.0, 120.0, 300.0],
        "keepalive": [60.0, 120.0, 180.0, 300.0],
    }

    for timeout_type, widget in timeout_widgets.items():
        for timeout_value in timeout_configs[timeout_type]:
            # Act
            set_spinbutton_value(widget, timeout_value)
            process_gtk_events()

            # Assert
            settings_key = f"peer_protocol.{timeout_type}_timeout_seconds"
            assert mock_app_settings.get(settings_key) == timeout_value
```

**Expected Results**:
- ✅ Timeout values updated
- ✅ Peer connections use new timeouts
- ✅ Values validated (positive numbers only)

---

### 6.5 Advanced Tab Tests

#### Test: Log Level Selection

**Test ID**: `test_advanced_tab_log_level`

**Test Steps**:
```python
@pytest.mark.requires_gtk
def test_advanced_tab_log_level(settings_dialog, mock_app_settings, mocker):
    """Test log level changes update logger configuration."""
    # Arrange
    advanced_tab = get_tab_by_name(settings_dialog, "Advanced")
    log_level_dropdown = advanced_tab.get_widget("settings_log_level")

    # Mock logger reconfiguration
    mock_logger = mocker.patch("d_fake_seeder.lib.logger.logger.setLevel")

    # Test log levels
    log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    for level in log_levels:
        # Act
        select_dropdown_by_string(log_level_dropdown, level)
        process_gtk_events()

        # Assert
        assert mock_app_settings.get("logging.level") == level
        mock_logger.assert_called_with(getattr(logging, level))
```

**Expected Results**:
- ✅ Log level updated
- ✅ Logger reconfigured
- ✅ New log messages use correct level

---

### 6.6 Integration Tests

#### Test: Settings Persistence Across Restart

**Test ID**: `test_settings_persistence_across_restart`

**Test Steps**:
```python
@pytest.mark.integration
@pytest.mark.slow
def test_settings_persistence_across_restart(tmp_path):
    """Test that settings persist across application restarts."""
    # Arrange - First application instance
    config_dir = tmp_path / "dfakeseeder"
    config_dir.mkdir()

    app1 = create_test_app(config_dir)
    settings_dialog1 = open_settings_dialog(app1)

    # Act - Change multiple settings
    settings_changes = {
        "auto_start": True,
        "language": "es",
        "listening_port": 7000,
        "upload_speed": 200,
        "enable_dht": False,
        "log_level": "DEBUG",
    }

    for setting_key, value in settings_changes.items():
        apply_setting(settings_dialog1, setting_key, value)

    # Close dialog and app
    settings_dialog1.window.close()
    app1.quit()
    process_gtk_events()

    # Act - Create new application instance
    app2 = create_test_app(config_dir)
    settings_dialog2 = open_settings_dialog(app2)

    # Assert - All settings persisted
    for setting_key, expected_value in settings_changes.items():
        actual_value = get_setting_value(settings_dialog2, setting_key)
        assert actual_value == expected_value, \
            f"Setting {setting_key} not persisted: expected {expected_value}, got {actual_value}"

    # Cleanup
    app2.quit()
```

**Expected Results**:
- ✅ All settings persist to settings.json
- ✅ New app instance loads settings correctly
- ✅ UI reflects persisted settings

---

#### Test: Signal Propagation Chain

**Test ID**: `test_signal_propagation_chain`

**Test Steps**:
```python
@pytest.mark.integration
def test_signal_propagation_chain(settings_dialog, mock_app_settings, mocker):
    """Test that setting changes propagate through signal chain."""
    # Arrange - Set up signal listeners
    signal_log = []

    def on_attribute_changed(instance, key, value):
        signal_log.append(("attribute-changed", key, value))

    def on_ui_updated(instance):
        signal_log.append(("ui-updated",))

    mock_app_settings.connect("attribute-changed", on_attribute_changed)
    settings_dialog.parent_window.connect("ui-updated", on_ui_updated)

    # Act - Change a setting
    general_tab = settings_dialog.tabs[0]
    auto_start_widget = general_tab.get_widget("auto_start")
    click_switch(auto_start_widget, True)
    process_gtk_events(iterations=10)  # Allow signal propagation

    # Assert - Signal chain completed
    assert ("attribute-changed", "auto_start", True) in signal_log
    assert ("ui-updated",) in signal_log

    # Assert - Signal order correct
    attr_changed_idx = signal_log.index(("attribute-changed", "auto_start", True))
    ui_updated_idx = signal_log.index(("ui-updated",))
    assert attr_changed_idx < ui_updated_idx, "UI should update after settings change"
```

**Expected Results**:
- ✅ Signals emitted in correct order
- ✅ All listeners notified
- ✅ No signal loops or deadlocks

---

### 6.7 Error Handling Tests

#### Test: Invalid Settings Rejection

**Test ID**: `test_invalid_settings_rejection`

**Test Steps**:
```python
@pytest.mark.unit
def test_invalid_settings_rejection(settings_dialog, mock_app_settings):
    """Test that invalid settings are rejected with appropriate errors."""
    # Test cases: (tab_name, widget_id, invalid_value, error_type)
    invalid_cases = [
        ("Connection", "settings_listening_port", -1, ValueError),
        ("Connection", "settings_listening_port", 999999, ValueError),
        ("Connection", "settings_max_connections", 0, ValueError),
        ("Speed", "settings_upload_speed", -100, ValueError),
        ("Peer Protocol", "settings_handshake_timeout", 0, ValueError),
    ]

    for tab_name, widget_id, invalid_value, expected_error in invalid_cases:
        # Arrange
        tab = get_tab_by_name(settings_dialog, tab_name)
        widget = tab.get_widget(widget_id)
        original_value = get_widget_value(widget)

        # Act & Assert
        with pytest.raises(expected_error):
            set_widget_value(widget, invalid_value)
            process_gtk_events()

        # Assert - Original value unchanged
        assert get_widget_value(widget) == original_value

        # Assert - Error notification shown to user
        # (Would check for error dialog or status message)
```

**Expected Results**:
- ✅ Invalid values rejected
- ✅ Appropriate exceptions raised
- ✅ User notified of error
- ✅ Settings remain unchanged

---

## 7. Implementation Roadmap

### Phase 1: Foundation (Week 1)

#### Tasks
1. **Install GTK Testing Dependencies**
   ```bash
   pip install pytest-gtk
   pip install pyvirtualdisplay  # For Xvfb control
   ```

2. **Create GTK Test Fixtures** (`tests/fixtures/gtk_fixtures.py`)
   - `gtk_display`: Virtual display fixture
   - `gtk_app`: Application instance
   - `gtk_builder`: UI builder
   - `settings_dialog`: Settings dialog instance

3. **Create UI Interaction Helpers** (`tests/helpers/gtk_helpers.py`)
   - `click_switch(widget, state)`
   - `select_dropdown_item(widget, index)`
   - `set_spinbutton_value(widget, value)`
   - `process_gtk_events(iterations=5)`
   - `wait_for_signal(instance, signal_name, timeout=1.0)`

4. **Update CI/CD Configuration**
   - Add Xvfb to GitHub Actions
   - Configure virtual display for tests

**Deliverables**:
- ✅ GTK test fixtures working
- ✅ Basic UI interaction helpers
- ✅ CI/CD running GTK tests

---

### Phase 2: Settings Tab Tests (Week 2-3)

#### Tasks
1. **General Tab Tests** (5 tests)
   - Auto-start toggle
   - Start minimized toggle
   - Language selection
   - Theme selection
   - Color scheme selection

2. **Connection Tab Tests** (4 tests)
   - Listening port
   - UPnP toggle
   - Max connections
   - Proxy configuration

3. **Speed Tab Tests** (3 tests)
   - Upload speed limit
   - Download speed limit
   - Alternative speed configuration

4. **Peer Protocol Tab Tests** (3 tests)
   - Handshake timeout
   - Message read timeout
   - Keep-alive interval

**Deliverables**:
- ✅ 15+ unit tests for settings tabs
- ✅ >80% coverage of settings components

---

### Phase 3: Integration Tests (Week 4)

#### Tasks
1. **Settings Persistence Tests** (3 tests)
   - Settings persist across restart
   - Settings file corruption handling
   - Migration from old settings format

2. **Signal Propagation Tests** (2 tests)
   - Signal chain verification
   - Signal loop prevention

3. **Full Settings Workflow Tests** (2 tests)
   - Open settings → change multiple → save → verify
   - Settings import/export

**Deliverables**:
- ✅ 7+ integration tests
- ✅ End-to-end settings workflows tested

---

### Phase 4: Error Handling & Edge Cases (Week 5)

#### Tasks
1. **Validation Tests** (5 tests)
   - Invalid port numbers
   - Out-of-range values
   - Invalid file paths
   - Malformed settings files
   - Concurrent settings changes

2. **Error Recovery Tests** (3 tests)
   - Settings file recovery
   - Default fallback behavior
   - Error notification system

**Deliverables**:
- ✅ 8+ error handling tests
- ✅ Comprehensive edge case coverage

---

### Phase 5: Performance & Optimization (Week 6)

#### Tasks
1. **Performance Tests**
   - Settings load time
   - UI responsiveness during changes
   - Parallel test execution optimization

2. **Test Suite Optimization**
   - Reduce test execution time
   - Parallel test execution
   - Test data cleanup

**Deliverables**:
- ✅ Full test suite runs in <5 minutes
- ✅ Parallel execution working
- ✅ 90%+ overall test coverage

---

## 8. Code Examples & Templates

### 8.1 GTK Test Fixtures

**File**: `tests/fixtures/gtk_fixtures.py`

```python
"""
GTK-specific test fixtures for DFakeSeeder UI testing.
Provides virtual display, GTK app, and settings dialog fixtures.
"""

import os
import pytest
from pathlib import Path
from pyvirtualdisplay import Display

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib

from d_fake_seeder.dfakeseeder import DFakeSeeder
from d_fake_seeder.components.component.settings.settings_dialog import SettingsDialog
from d_fake_seeder.domain.app_settings import AppSettings


@pytest.fixture(scope="session")
def virtual_display():
    """
    Create a virtual X display for GTK testing.

    Uses Xvfb to create a headless display server.
    This fixture has session scope to avoid overhead of starting/stopping display.

    Returns:
        Display: pyvirtualdisplay Display instance
    """
    # Start virtual display
    display = Display(visible=False, size=(1920, 1080))
    display.start()

    yield display

    # Cleanup
    display.stop()


@pytest.fixture
def gtk_app(virtual_display, tmp_path, clean_environment):
    """
    Create a DFakeSeeder application instance for testing.

    Args:
        virtual_display: Virtual X display fixture
        tmp_path: Temporary directory for config files
        clean_environment: Environment cleanup fixture

    Returns:
        DFakeSeeder: Application instance
    """
    # Set config directory to temp path
    config_dir = tmp_path / "dfakeseeder"
    config_dir.mkdir()
    torrents_dir = config_dir / "torrents"
    torrents_dir.mkdir()

    # Set environment
    os.environ["DFS_PATH"] = str(Path(__file__).parent.parent.parent / "d_fake_seeder")
    os.environ["XDG_CONFIG_HOME"] = str(tmp_path)

    # Create minimal settings file
    settings_file = config_dir / "settings.json"
    settings_file.write_text("""{
        "language": "en",
        "tickspeed": 10,
        "listening_port": 6881,
        "upload_speed": 50,
        "download_speed": 500
    }""")

    # Initialize application
    app = DFakeSeeder()

    # Don't run main loop - we'll control event processing manually

    yield app

    # Cleanup
    app.quit()
    process_gtk_events()  # Process any pending quit events


@pytest.fixture
def mock_app_settings(tmp_path):
    """
    Create a real AppSettings instance with temporary config directory.

    Note: We use a real AppSettings instance instead of mocking to test
    actual settings behavior including persistence and signal emission.

    Returns:
        AppSettings: Application settings instance
    """
    # Set config directory
    config_dir = tmp_path / "dfakeseeder"
    config_dir.mkdir(exist_ok=True)

    # Create settings instance
    settings = AppSettings.get_instance()
    settings._config_dir = config_dir  # Override config directory

    yield settings

    # Cleanup
    AppSettings._instance = None  # Reset singleton for next test


@pytest.fixture
def gtk_builder(gtk_app):
    """
    Create a GTK Builder instance with settings UI loaded.

    Returns:
        Gtk.Builder: Builder with settings UI
    """
    builder = Gtk.Builder()
    ui_file = os.environ["DFS_PATH"] + "/components/ui/generated/settings_generated.xml"
    builder.add_from_file(ui_file)

    return builder


@pytest.fixture
def settings_dialog(gtk_app, gtk_builder, mock_app_settings):
    """
    Create a SettingsDialog instance for testing.

    Returns:
        SettingsDialog: Settings dialog instance
    """
    # Create mock main window
    main_window = Gtk.Window()

    # Create settings dialog
    dialog = SettingsDialog(
        parent_window=main_window,
        app=gtk_app,
        model=gtk_app.model
    )

    # Show window (required for widget interaction)
    dialog.window.present()
    process_gtk_events()

    yield dialog

    # Cleanup
    dialog.window.close()
    process_gtk_events()


# Helper function (not a fixture)
def process_gtk_events(iterations=5):
    """
    Process pending GTK events.

    This is necessary to allow signal handlers to run and
    UI updates to complete after programmatic widget changes.

    Args:
        iterations: Number of event loop iterations to process
    """
    context = GLib.MainContext.default()
    for _ in range(iterations):
        while context.iteration(False):
            pass
```

---

### 8.2 UI Interaction Helpers

**File**: `tests/helpers/gtk_helpers.py`

```python
"""
Helper functions for GTK UI interaction in tests.
Provides high-level functions for clicking, typing, and verifying UI state.
"""

import time
from typing import Any, Optional, Callable
from gi.repository import Gtk, GLib


def click_switch(switch: Gtk.Switch, state: bool) -> None:
    """
    Click a GTK Switch widget to set it to the specified state.

    Args:
        switch: The GTK Switch widget
        state: Desired state (True = on, False = off)
    """
    if switch.get_active() != state:
        switch.set_active(state)
        switch.emit("state-set", state)


def select_dropdown_by_index(dropdown: Gtk.DropDown, index: int) -> None:
    """
    Select an item in a GTK DropDown by index.

    Args:
        dropdown: The GTK DropDown widget
        index: Index of item to select (0-based)

    Raises:
        ValueError: If index is out of range
    """
    model = dropdown.get_model()
    if index < 0 or index >= model.get_n_items():
        raise ValueError(f"Index {index} out of range for dropdown with {model.get_n_items()} items")

    dropdown.set_selected(index)
    dropdown.emit("notify::selected")


def select_dropdown_by_string(dropdown: Gtk.DropDown, value: str) -> None:
    """
    Select an item in a GTK DropDown by string value.

    Args:
        dropdown: The GTK DropDown widget
        value: String value to select

    Raises:
        ValueError: If value not found in dropdown
    """
    model = dropdown.get_model()

    for i in range(model.get_n_items()):
        item = model.get_item(i)
        # Get string from StringObject (GTK4 pattern)
        item_string = item.get_string() if hasattr(item, 'get_string') else str(item)

        if item_string.lower() == value.lower():
            dropdown.set_selected(i)
            dropdown.emit("notify::selected")
            return

    raise ValueError(f"Value '{value}' not found in dropdown")


def set_spinbutton_value(spinbutton: Gtk.SpinButton, value: float) -> None:
    """
    Set the value of a GTK SpinButton.

    Args:
        spinbutton: The GTK SpinButton widget
        value: Value to set

    Raises:
        ValueError: If value is outside allowed range
    """
    adjustment = spinbutton.get_adjustment()
    min_val = adjustment.get_lower()
    max_val = adjustment.get_upper()

    if value < min_val or value > max_val:
        raise ValueError(f"Value {value} outside allowed range [{min_val}, {max_val}]")

    spinbutton.set_value(value)
    spinbutton.emit("value-changed")


def enter_text(entry: Gtk.Entry, text: str) -> None:
    """
    Enter text into a GTK Entry widget.

    Args:
        entry: The GTK Entry widget
        text: Text to enter
    """
    entry.set_text(text)
    entry.emit("changed")


def click_button(button: Gtk.Button) -> None:
    """
    Click a GTK Button widget.

    Args:
        button: The GTK Button widget
    """
    button.emit("clicked")


def get_widget_value(widget: Gtk.Widget) -> Any:
    """
    Get the current value from a widget.

    Supports: Switch, SpinButton, Entry, DropDown

    Args:
        widget: The GTK widget

    Returns:
        Current widget value

    Raises:
        TypeError: If widget type is not supported
    """
    if isinstance(widget, Gtk.Switch):
        return widget.get_active()
    elif isinstance(widget, Gtk.SpinButton):
        return widget.get_value()
    elif isinstance(widget, Gtk.Entry):
        return widget.get_text()
    elif isinstance(widget, Gtk.DropDown):
        return widget.get_selected()
    else:
        raise TypeError(f"Unsupported widget type: {type(widget)}")


def set_widget_value(widget: Gtk.Widget, value: Any) -> None:
    """
    Set the value of a widget.

    Automatically dispatches to the appropriate setter function.

    Args:
        widget: The GTK widget
        value: Value to set
    """
    if isinstance(widget, Gtk.Switch):
        click_switch(widget, value)
    elif isinstance(widget, Gtk.SpinButton):
        set_spinbutton_value(widget, value)
    elif isinstance(widget, Gtk.Entry):
        enter_text(widget, value)
    elif isinstance(widget, Gtk.DropDown):
        if isinstance(value, int):
            select_dropdown_by_index(widget, value)
        else:
            select_dropdown_by_string(widget, value)
    else:
        raise TypeError(f"Unsupported widget type: {type(widget)}")


def has_css_class(widget: Gtk.Widget, class_name: str) -> bool:
    """
    Check if a widget has a specific CSS class.

    Args:
        widget: The GTK widget
        class_name: CSS class name to check

    Returns:
        True if widget has the class, False otherwise
    """
    return widget.has_css_class(class_name)


def wait_for_signal(
    instance: Any,
    signal_name: str,
    timeout: float = 1.0,
    verify_args: Optional[Callable] = None
) -> bool:
    """
    Wait for a GObject signal to be emitted.

    Args:
        instance: GObject instance that emits the signal
        signal_name: Name of the signal to wait for
        timeout: Maximum time to wait in seconds
        verify_args: Optional function to verify signal arguments

    Returns:
        True if signal was emitted and verified, False if timeout

    Example:
        >>> def verify_changed(key, value):
        ...     return key == "language" and value == "es"
        >>> wait_for_signal(settings, "attribute-changed", verify_args=verify_changed)
    """
    signal_received = [False]

    def on_signal(*args):
        if verify_args is None or verify_args(*args):
            signal_received[0] = True

    handler_id = instance.connect(signal_name, on_signal)

    # Wait for signal with timeout
    start_time = time.time()
    while not signal_received[0] and (time.time() - start_time) < timeout:
        process_gtk_events(iterations=1)
        time.sleep(0.01)

    instance.disconnect(handler_id)

    return signal_received[0]


def process_gtk_events(iterations: int = 5) -> None:
    """
    Process pending GTK events.

    Args:
        iterations: Number of event loop iterations
    """
    context = GLib.MainContext.default()
    for _ in range(iterations):
        while context.iteration(False):
            pass


def wait_for_file_write(file_path, timeout: float = 1.0) -> bool:
    """
    Wait for a file to be written.

    Useful for waiting for async settings persistence.

    Args:
        file_path: Path to the file
        timeout: Maximum time to wait in seconds

    Returns:
        True if file exists, False if timeout
    """
    from pathlib import Path

    start_time = time.time()
    while not Path(file_path).exists() and (time.time() - start_time) < timeout:
        time.sleep(0.01)

    return Path(file_path).exists()


def assert_signal_emitted(
    instance: Any,
    signal_name: str,
    expected_args: Optional[list] = None
) -> None:
    """
    Assert that a signal was emitted with expected arguments.

    This is a verification helper for use in assertions.

    Args:
        instance: GObject instance
        signal_name: Signal name
        expected_args: Expected signal arguments

    Raises:
        AssertionError: If signal not emitted or args don't match
    """
    def verify_args(*args):
        if expected_args is None:
            return True
        return list(args) == expected_args

    result = wait_for_signal(instance, signal_name, verify_args=verify_args)
    assert result, f"Signal '{signal_name}' not emitted with expected args: {expected_args}"


def get_tab_by_name(settings_dialog, tab_name: str):
    """
    Get a settings tab by name.

    Args:
        settings_dialog: SettingsDialog instance
        tab_name: Name of the tab (e.g., "General", "Connection")

    Returns:
        Tab instance

    Raises:
        ValueError: If tab not found
    """
    for tab in settings_dialog.tabs:
        if tab.tab_name == tab_name:
            return tab

    raise ValueError(f"Tab '{tab_name}' not found")
```

---

### 8.3 Example Test File

**File**: `tests/integration/test_settings_general_tab.py`

```python
"""
Integration tests for Settings Dialog - General Tab.

Tests the following functionality:
- Auto-start toggle
- Start minimized toggle
- Language selection
- Theme selection
- Color scheme selection
- Settings persistence
"""

import pytest
import json
from pathlib import Path

from tests.helpers.gtk_helpers import (
    click_switch,
    select_dropdown_by_string,
    process_gtk_events,
    wait_for_signal,
    wait_for_file_write,
    get_tab_by_name,
)


@pytest.mark.integration
@pytest.mark.requires_gtk
class TestGeneralTabSettings:
    """Test suite for General Tab settings."""

    def test_auto_start_toggle_updates_settings(
        self, settings_dialog, mock_app_settings, tmp_path
    ):
        """Test that auto-start toggle updates AppSettings and persists."""
        # Arrange
        general_tab = get_tab_by_name(settings_dialog, "General")
        auto_start_widget = general_tab.get_widget("auto_start")
        settings_file = tmp_path / "dfakeseeder" / "settings.json"

        # Verify initial state
        assert auto_start_widget.get_active() == False
        assert mock_app_settings.get("auto_start") == False

        # Act - Enable auto-start
        click_switch(auto_start_widget, True)
        process_gtk_events()

        # Assert - Settings updated
        assert mock_app_settings.get("auto_start") == True

        # Assert - Signal emitted
        assert wait_for_signal(
            mock_app_settings,
            "attribute-changed",
            verify_args=lambda key, val: key == "auto_start" and val == True
        )

        # Assert - Persistence
        wait_for_file_write(settings_file)
        settings_data = json.loads(settings_file.read_text())
        assert settings_data["auto_start"] == True

        # Act - Disable auto-start
        click_switch(auto_start_widget, False)
        process_gtk_events()

        # Assert - Reverted
        assert mock_app_settings.get("auto_start") == False

    def test_start_minimized_toggle(self, settings_dialog, mock_app_settings):
        """Test start minimized toggle."""
        # Arrange
        general_tab = get_tab_by_name(settings_dialog, "General")
        start_minimized_widget = general_tab.get_widget("start_minimized")

        # Act
        click_switch(start_minimized_widget, True)
        process_gtk_events()

        # Assert
        assert mock_app_settings.get("start_minimized") == True

    @pytest.mark.parametrize("language_code", ["en", "es", "fr", "de", "it", "pt"])
    def test_language_selection(
        self, settings_dialog, mock_app_settings, language_code
    ):
        """Test language selection for multiple languages."""
        # Arrange
        general_tab = get_tab_by_name(settings_dialog, "General")
        language_dropdown = general_tab.get_widget("language_dropdown")

        # Act
        select_dropdown_by_string(language_dropdown, language_code)
        process_gtk_events()

        # Assert
        assert mock_app_settings.get("language") == language_code

        # Assert - Translation manager notified
        # (Would verify UI updates if model.translation_manager accessible)

    @pytest.mark.parametrize("theme", ["system", "deluge", "modern_chunky"])
    def test_theme_selection(self, settings_dialog, mock_app_settings, theme):
        """Test theme selection."""
        # Arrange
        general_tab = get_tab_by_name(settings_dialog, "General")
        theme_dropdown = general_tab.get_widget("settings_theme")

        # Act
        select_dropdown_by_string(theme_dropdown, theme)
        process_gtk_events()

        # Assert
        assert mock_app_settings.get("ui_settings.theme_style") == theme

    @pytest.mark.parametrize("scheme", ["auto", "light", "dark"])
    def test_color_scheme_selection(self, settings_dialog, mock_app_settings, scheme):
        """Test color scheme selection."""
        # Arrange
        general_tab = get_tab_by_name(settings_dialog, "General")
        color_scheme_dropdown = general_tab.get_widget("settings_color_scheme")
        main_window = settings_dialog.parent_window

        # Act
        select_dropdown_by_string(color_scheme_dropdown, scheme)
        process_gtk_events()

        # Assert - Settings updated
        assert mock_app_settings.get("ui_settings.color_scheme") == scheme

        # Assert - CSS class applied (if dark mode)
        if scheme == "dark":
            assert main_window.has_css_class("dark")
        elif scheme == "light":
            assert not main_window.has_css_class("dark")
```

---

### 8.4 Makefile Test Targets

Add to existing `Makefile`:

```makefile
# GTK UI Testing Targets

.PHONY: test-ui
test-ui: ## Run GTK UI tests with Xvfb
	xvfb-run -a pytest tests/integration/test_settings_*.py -v -m requires_gtk

.PHONY: test-ui-fast
test-ui-fast: ## Run GTK UI tests in parallel
	xvfb-run -a pytest tests/integration/test_settings_*.py -v -m requires_gtk -n auto

.PHONY: test-settings
test-settings: ## Run all settings-related tests
	xvfb-run -a pytest tests/ -v -k "settings"

.PHONY: test-settings-coverage
test-settings-coverage: ## Run settings tests with coverage report
	xvfb-run -a pytest tests/ -v -k "settings" --cov=d_fake_seeder/components/component/settings --cov-report=html

.PHONY: test-ui-debug
test-ui-debug: ## Run UI tests with verbose output and no capture
	xvfb-run -a pytest tests/integration/test_settings_*.py -vvs -m requires_gtk --log-cli-level=DEBUG
```

Usage:
```bash
make test-ui                    # Run all UI tests
make test-settings              # Run settings tests
make test-settings-coverage     # Generate coverage report
make test-ui-debug             # Debug UI tests
```

---

## 9. CI/CD Integration

### GitHub Actions Configuration

**File**: `.github/workflows/ui-tests.yml`

```yaml
name: GTK UI Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  ui-tests:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          xvfb \
          libgirepository1.0-dev \
          libcairo2-dev \
          gir1.2-gtk-4.0 \
          python3-gi \
          python3-gi-cairo

    - name: Install Python dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pipenv
        pipenv install --dev

    - name: Run GTK UI tests
      run: |
        xvfb-run -a pipenv run pytest tests/integration/ \
          -v \
          -m requires_gtk \
          --cov=d_fake_seeder/components/component/settings \
          --cov-report=xml \
          --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
        flags: ui-tests
        name: ui-tests-${{ matrix.python-version }}
```

---

## 10. Troubleshooting & Best Practices

### Common Issues

#### Issue 1: "cannot open display" Error

**Symptom**:
```
Gtk-WARNING **: cannot open display:
```

**Solution**:
```bash
# Ensure Xvfb is running
xvfb-run -a pytest tests/

# Or start Xvfb manually
Xvfb :99 -screen 0 1920x1080x24 &
export DISPLAY=:99
pytest tests/
```

---

#### Issue 2: GTK Initialization Fails

**Symptom**:
```
gi.repository.GLib.Error: gtk-builder-error-quark
```

**Solution**:
```python
# Ensure GTK version is correctly specified
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk

# Verify UI file path is correct
ui_file = Path(__file__).parent / "ui" / "settings.xml"
assert ui_file.exists(), f"UI file not found: {ui_file}"
```

---

#### Issue 3: Signals Not Emitting

**Symptom**:
```
AssertionError: Signal 'attribute-changed' not emitted
```

**Solution**:
```python
# Process GTK events after widget interaction
click_switch(widget, True)
process_gtk_events(iterations=10)  # Increase iterations

# Or use explicit signal waiting
wait_for_signal(instance, "attribute-changed", timeout=2.0)
```

---

#### Issue 4: Settings Not Persisting

**Symptom**:
Settings changes not written to file

**Solution**:
```python
# Allow time for async file write
wait_for_file_write(settings_file, timeout=2.0)

# Or force synchronous write in tests
mock_app_settings._save_sync()  # If method exists
```

---

### Best Practices

#### 1. Use Real Widgets, Mock Services

```python
# ✅ Good: Test real GTK widgets
def test_widget_interaction(settings_dialog):
    widget = settings_dialog.builder.get_object("settings_auto_start")
    click_switch(widget, True)

# ❌ Bad: Mock GTK widgets
def test_widget_interaction(mocker):
    mock_widget = mocker.MagicMock(spec=Gtk.Switch)
```

#### 2. Process Events After Interactions

```python
# ✅ Good: Always process events
click_switch(widget, True)
process_gtk_events()
assert settings.get("auto_start") == True

# ❌ Bad: No event processing
click_switch(widget, True)
assert settings.get("auto_start") == True  # May fail
```

#### 3. Use Explicit Waits

```python
# ✅ Good: Explicit wait for async operations
wait_for_signal(settings, "attribute-changed")
wait_for_file_write(settings_file)

# ❌ Bad: Sleep with arbitrary timeout
import time
time.sleep(1)  # Unreliable
```

#### 4. Isolate Tests with Fixtures

```python
# ✅ Good: Each test gets fresh fixtures
def test_a(settings_dialog, mock_app_settings):
    # Settings are isolated

def test_b(settings_dialog, mock_app_settings):
    # New settings instance, no contamination

# ❌ Bad: Shared state
settings = AppSettings.get_instance()

def test_a():
    settings.set("key", "value1")

def test_b():
    # Contaminated by test_a!
```

#### 5. Test Both Positive and Negative Cases

```python
# ✅ Good: Test valid and invalid inputs
@pytest.mark.parametrize("port,should_succeed", [
    (6881, True),
    (65535, True),
    (-1, False),
    (999999, False),
])
def test_port_validation(settings_dialog, port, should_succeed):
    # Test both success and failure
```

---

## Appendix A: Complete Test Coverage Matrix

| Component | Widget | Test Case | Priority | Status |
|-----------|--------|-----------|----------|--------|
| **GeneralTab** | | | | |
| | settings_auto_start | Toggle on/off | High | Planned |
| | settings_start_minimized | Toggle on/off | High | Planned |
| | settings_minimize_to_tray | Toggle on/off | Medium | Planned |
| | settings_language | Select each language | High | Planned |
| | settings_theme | Select each theme | Medium | Planned |
| | settings_color_scheme | Select each scheme | Medium | Planned |
| | settings_seeding_profile | Select each profile | High | Planned |
| **ConnectionTab** | | | | |
| | settings_listening_port | Valid ports | High | Planned |
| | settings_listening_port | Invalid ports | High | Planned |
| | settings_enable_upnp | Toggle on/off | Medium | Planned |
| | settings_max_connections | Various values | High | Planned |
| | settings_proxy_* | Proxy configuration | Low | Planned |
| **SpeedTab** | | | | |
| | settings_upload_speed | Various speeds | High | Planned |
| | settings_download_speed | Various speeds | High | Planned |
| | settings_alternative_speed_* | Alternative speeds | Medium | Planned |
| **PeerProtocolTab** | | | | |
| | settings_handshake_timeout | Valid timeouts | High | Planned |
| | settings_message_timeout | Valid timeouts | High | Planned |
| | settings_keepalive_interval | Valid intervals | Medium | Planned |
| **BitTorrentTab** | | | | |
| | settings_enable_dht | Toggle on/off | High | Planned |
| | settings_enable_pex | Toggle on/off | High | Planned |
| | settings_user_agent | Select agents | Medium | Planned |
| **AdvancedTab** | | | | |
| | settings_log_level | Each log level | Medium | Planned |
| | settings_tickspeed | Various values | High | Planned |
| | settings_debug_mode | Toggle on/off | Low | Planned |

**Total Test Cases**: 35+
**Estimated Implementation Time**: 6 weeks
**Target Coverage**: 90%

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Xvfb** | X Virtual Frame Buffer - headless X server for testing |
| **pytest** | Python testing framework |
| **GTK4** | GIMP Toolkit version 4 - UI framework |
| **GLib** | Low-level core library (event loop, signals) |
| **Fixture** | pytest concept for test setup/teardown |
| **Signal** | GObject notification mechanism |
| **AppSettings** | DFakeSeeder settings management class |
| **SettingsDialog** | Main settings UI component |
| **Builder** | GTK UI construction from XML |
| **Widget** | GTK UI element (button, switch, etc.) |

---

## Document Changelog

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-09 | Claude Code | Initial comprehensive design guide |

---

**End of Document**
