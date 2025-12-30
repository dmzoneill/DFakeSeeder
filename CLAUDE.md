# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 🚨 CRITICAL: Read This First

### Do NOT Modify Without Permission
- **`.github/` workflows** - Always ask before modifying. Consider upstream dispatch at: https://github.com/dmzoneill/dmzoneill/blob/main/.github/workflows/dispatch.yaml
- **Translation JSON files** (`tools/translations/{en,de,es,...}.json`) - NEVER modify directly. Update the `*_fallbacks_to_translate.json` files instead, then run `make translate-workflow`
- **Generated files** (`components/ui/generated/*.xml`) - These are auto-generated. Modify source XML files instead
- **External dependencies** - Never add new libraries without asking first

### Legacy Code Warning
If you encounter legacy patterns (deprecated signals, old naming conventions, etc.), **DO NOT replicate them**. Instead, prompt the user and explain what you found.

---

## 📋 Quick Reference

### Common Tasks Cheat Sheet

| Task | Command / Location |
|------|-------------------|
| **Run app (dev)** | `make run-debug-venv` |
| **Lint code** | `make lint` (or `make super-lint` for comprehensive) |
| **Run tests** | `make test-venv` |
| **Add a setting** | 1. Add to `d_fake_seeder/config/default.json` 2. Add property/setter in `d_fake_seeder/domain/app_settings.py` |
| **Add UI component** | Create XML in `components/ui/`, use xi:include in parent XML |
| **Add translation** | Run `make translate-workflow` (uses `tools/translation_build_manager.py`) |
| **Build packages** | `make deb` / `make rpm` / `make flatpak` |

### Key File Locations

| Purpose | Path |
|---------|------|
| Main entry point | `d_fake_seeder/dfakeseeder.py` |
| Settings singleton | `d_fake_seeder/domain/app_settings.py` |
| Default config | `d_fake_seeder/config/default.json` |
| Logger | `d_fake_seeder/lib/logger.py` |
| UI components | `d_fake_seeder/components/component/` |
| UI XML files | `d_fake_seeder/components/ui/` |
| Translation manager | `tools/translation_build_manager.py` |
| Test fixtures | `tests/conftest.py` |

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `DFS_PATH` | Path to d_fake_seeder package (set automatically) |
| `DFS_SETTINGS` | Override settings.json path |
| `LOG_LEVEL` | Set logging level (DEBUG, INFO, etc.) |

---

## ⛔ Anti-Patterns (What NOT to Do)

### Never Do This
```python
# ❌ DON'T use print statements
print("Debug message")

# ✅ DO use the logger
from d_fake_seeder.lib.logger import logger
logger.debug("Debug message")
```

```python
# ❌ DON'T create new utility files without checking existing ones
# Check lib/util/ first!

# ❌ DON'T add dependencies without asking
# pip install some-new-library  

# ❌ DON'T modify generated XML files
# Edit source files in components/ui/notebook/, components/ui/settings/, etc.

# ❌ DON'T modify translation JSON files directly
# Use fallback files and make translate-workflow
```

### Logging Levels
```python
logger.trace("Ultra-verbose, function entry/exit")  # TRACE (5)
logger.debug("Normal diagnostic info")              # DEBUG (10) ← DEFAULT FOR NEW CODE
logger.info("User-visible events, milestones")      # INFO (20)
logger.warning("Unexpected but recoverable")        # WARNING (30)
logger.error("Errors needing attention", exc_info=True)  # ERROR (40)
```

### GTK4 CSS Gotchas

**GTK4 does NOT support `!important`** - Unlike web CSS, GTK4's CSS parser ignores `!important` declarations entirely. They will not override theme styles.

```css
/* ❌ DON'T - GTK4 ignores !important */
.my-widget {
    background-color: #2d2d2d !important;
}

/* ✅ DO - Use higher priority CssProvider in code */
```

**For widgets that need guaranteed styling (especially backgrounds on Gtk.Frame):**
```python
# Apply inline CSS with high priority
css_provider = Gtk.CssProvider()
css_provider.load_from_string("""
    frame {
        background-color: #2d2d2d;
        border-radius: 12px;
    }
""")
widget.get_style_context().add_provider(
    css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 100
)
```

**Other GTK4 CSS differences from web CSS:**
- No `box-shadow` spread radius (only offset-x, offset-y, blur-radius, color)
- Limited pseudo-classes (`:hover`, `:active`, `:focus`, `:checked`, `:disabled`)
- `@media` queries work but are limited
- Colors must be hex (`#rrggbb`) or `rgba()` - named colors may not work

---

## ✅ Required Patterns

### Adding New Settings
1. Add default value to `d_fake_seeder/config/default.json`
2. Add property/setter pair in `d_fake_seeder/domain/app_settings.py`:
```python
@property
def my_new_setting(self) -> Any:
    return self.get("category.my_new_setting", default_value)

@my_new_setting.setter
def my_new_setting(self, value: Any) -> None:
    self.set("category.my_new_setting", value)
```

### Adding UI Components
1. Create XML file in `components/ui/` (appropriate subfolder)
2. Use `xi:include` to include in parent XML
3. Create Python component extending `Component` or `CleanupMixin`
4. Track all signals with `self.track_signal(obj, handler_id)`

### Writing Tests
- **Every new function needs a test**
- Use **standalone test functions** (no test classes)
- Use `unittest.mock.patch` via `mocker` fixture (NOT `monkeypatch`)
- Use real filesystem with `tmp_path` (NOT pyfakefs)
- Follow Arrange-Act-Assert pattern

```python
def test_my_function(mock_settings, tmp_path):
    # Arrange
    expected = "value"
    
    # Act
    result = my_function()
    
    # Assert
    assert result == expected
```

### Translation Workflow
```bash
# Full workflow (extract → sync → build → validate)
make translate-workflow

# Or manually:
python3 tools/translation_build_manager.py extract
python3 tools/translation_build_manager.py sync
python3 tools/translation_build_manager.py sync-keys
python3 tools/translation_build_manager.py identify-fallbacks
python3 tools/translation_build_manager.py translate-fallbacks
python3 tools/translation_build_manager.py update-from-fallbacks
python3 tools/translation_build_manager.py build
python3 tools/translation_build_manager.py analyze
```

---

## 🧵 Threading & Async Considerations

### Important
- Many threads can be running simultaneously
- Use thread managers where possible (they're tracked for cleanup)
- On shutdown, threads are terminated as part of cleanup procedure
- Use `SharedAsyncExecutor` for async work when appropriate
- Track timeouts with `self.track_timeout(source_id)` for proper cleanup

---

## 🧪 Test Fixtures Available

Use these fixtures from `tests/conftest.py`:

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

---

## ⚠️ Common Gotchas

### 1. Circular Import with Logger
The logger imports AppSettings which imports logger. Use lazy import pattern:
```python
# In app_settings.py - logger is accessed via property with lazy import
@property
def logger(self) -> Any:
    if AppSettings._logger is None:
        from d_fake_seeder.lib.logger import logger
        AppSettings._logger = logger
    return AppSettings._logger
```

### 2. Signal Handler Loops
When handling `settings-value-changed`, modifying settings can trigger the signal again:
```python
# BAD - can cause infinite loop
def on_setting_changed(self, source, key, value):
    self.settings.set(key, modified_value)  # Triggers signal again!

# GOOD - check if value actually changed
def on_setting_changed(self, source, key, value):
    if value != self.cached_value:
        self.cached_value = value
        # Process...
```

### 3. Weak Reference in CleanupMixin
Objects passed to `track_signal()` use weak references. If the object is garbage collected, the cleanup is skipped silently. Keep strong references to objects that need signal cleanup.

### 4. GLib.timeout_add Returns Before Callback
```python
# The timeout ID is returned immediately
timer_id = GLib.timeout_add(1000, callback)  # Returns right away
self.track_timeout(timer_id)  # Track it for cleanup!
```

### 5. AppSettings Singleton Across Tests
AppSettings is a singleton - use the `file_path` parameter in tests:
```python
# In tests, reinitialize with different path
settings = AppSettings(file_path=str(tmp_path / "settings.json"))
```

### 6. Translation Files
- **NEVER** edit `tools/translations/{en,de,...}.json` directly
- **DO** edit `tools/translations/*_fallbacks_to_translate.json`
- Then run `make translate-workflow` or `python3 tools/translation_build_manager.py update-from-fallbacks`

---

## 🏗️ Component Hierarchy

The UI component hierarchy follows a consistent pattern with `CleanupMixin` at the base:

```
CleanupMixin (d_fake_seeder/lib/util/cleanup_mixin.py)
│   - Tracks signals, bindings, timeouts, stores
│   - Provides cleanup() method for resource management
│
└── Component (d_fake_seeder/components/component/base_component.py)
    │   - Abstract: handle_model_changed(), handle_attribute_changed(),
    │               handle_settings_changed(), update_view()
    │   - Has set_model() with auto signal tracking
    │
    ├── BaseSettingsTab (settings/base_tab.py)
    │   └── AdvancedTab, BitTorrentTab, ConnectionTab, DHTTab,
    │       GeneralTab, MultiTrackerTab, PeerProtocolTab,
    │       ProtocolExtensionsTab, SimulationTab, SpeedTab, WebUITab
    │
    ├── BaseTorrentTab (torrent_details/base_tab.py)
    │   │   - Abstract: tab_name, tab_widget_id, _init_widgets(), update_content()
    │   └── DetailsTab, FilesTab, StatusTab, TrackersTab, OptionsTab,
    │       LogTab, MonitoringTab, IncomingConnectionsTab, OutgoingConnectionsTab
    │
    ├── TorrentDetailsNotebook
    └── Torrents, Toolbar, States, Statusbar, Sidebar
```

### Key Design Principles

1. **Single cleanup chain**: All UI components inherit `CleanupMixin` through `Component`
2. **Consistent tab pattern**: Both `BaseSettingsTab` and `BaseTorrentTab` extend `Component`
3. **Specialized abstracts**: Each tab base defines domain-specific abstract methods
4. **Resource tracking**: Use `track_signal()`, `track_binding()`, `track_timeout()`, `track_store()`

---

## 🔨 Code Style

### Formatting Tools
- **Black**: Line length 120, Python 3.11+
- **isort**: Import ordering (profile: black)
- **flake8**: Linting
- **mypy**: Type checking

### Commands
```bash
make lint          # Run all formatters
make super-lint    # Comprehensive linting (Docker-based)
```

### Standard Import Pattern
All files follow this pattern for GTK4 imports:
```python
# isort: skip_file

# fmt: off
import other_stdlib_imports
from typing import Any

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402
from gi.repository import GLib, GObject  # noqa: E402

from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402

# fmt: on
```

**Why?** The `# fmt: off` blocks prevent Black from reordering `gi.require_version()` calls, which must come before GTK imports.

---

## 📡 GObject Signals

### Defined Signals

| Class | Signal | Parameters | Purpose |
|-------|--------|------------|---------|
| `Model` | `data-changed` | `(object, object)` | Torrent data modified |
| `Model` | `selection-changed` | `(object, object)` | Torrent selection changed |
| `Model` | `language-changed` | `(str,)` | UI language changed |
| `Torrent` | `attribute-changed` | `(object, object)` | Torrent attribute modified |
| `AppSettings` | `settings-value-changed` | `(str, object)` | Setting value changed (preferred) |
| `AppSettings` | `settings-attribute-changed` | `(str, object)` | Setting attribute changed |
| `AppSettings` | `setting-changed` | `(str, object)` | Legacy - use settings-value-changed |
| `AppSettings` | `attribute-changed` | `(str, object)` | Legacy - use settings-attribute-changed |

### Connecting to Signals
```python
# Always track signals for cleanup!
handler_id = self.model.connect("data-changed", self.on_data_changed)
self.track_signal(self.model, handler_id)

# Or inline (common pattern in settings tabs):
self.track_signal(
    widget,
    widget.connect("value-changed", self.on_value_changed),
)
```

### Emitting Signals
```python
# In GObject subclasses with __gsignals__ defined:
self.emit("data-changed", torrent, attribute)
```

---

## 🧩 Available Mixins

### Core Mixins

| Mixin | Location | Purpose |
|-------|----------|---------|
| `CleanupMixin` | `lib/util/cleanup_mixin.py` | Signal/binding/timeout cleanup tracking |
| `ColumnTranslationMixin` | `lib/util/column_translation_mixin.py` | Column header translation |

### Settings Tab Mixins (compose these for settings tabs)

| Mixin | Location | Purpose |
|-------|----------|---------|
| `NotificationMixin` | `components/component/settings/settings_mixins.py` | Show UI notifications |
| `ValidationMixin` | `components/component/settings/settings_mixins.py` | Input validation |
| `TranslationMixin` | `components/component/settings/settings_mixins.py` | Translation helpers |
| `UtilityMixin` | `components/component/settings/settings_mixins.py` | Utility functions |
| `KeyboardShortcutMixin` | `components/component/settings/settings_mixins.py` | Keyboard shortcuts |

### Torrent Tab Mixins

| Mixin | Location | Purpose |
|-------|----------|---------|
| `DataUpdateMixin` | `components/component/torrent_details/tab_mixins.py` | Data refresh handling |
| `UIUtilityMixin` | `components/component/torrent_details/tab_mixins.py` | UI utility functions |
| `PerformanceMixin` | `components/component/torrent_details/tab_mixins.py` | Performance tracking |

### Typical Usage Pattern
```python
# Settings tab (compose multiple mixins):
class MySettingsTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    pass

# Torrent details tab:
class MyDetailsTab(BaseTorrentTab, DataUpdateMixin, UIUtilityMixin):
    pass

# Main component with columns:
class MyComponent(Component, ColumnTranslationMixin):
    pass
```

---

## 🔌 D-Bus Interface

The main app and tray communicate via D-Bus.

### D-Bus Details
- **Service**: `ie.fio.dfakeseeder`
- **Object Path**: `/ie/fio/dfakeseeder`
- **Interface**: `ie.fio.dfakeseeder`

### Key Files

| File | Purpose |
|------|---------|
| `lib/util/dbus_unifier.py` | D-Bus server (main app) |
| `lib/dbus_client.py` | D-Bus client (tray app) |
| `dfakeseeder_tray.py` | Tray application |

### D-Bus Signals Emitted
- `SettingsChanged` - When settings are modified (forwarded from AppSettings)

---

## 🗂️ File Naming Conventions

| Pattern | Examples | Usage |
|---------|----------|-------|
| `*_tab.py` | `general_tab.py`, `status_tab.py` | Settings/details tabs |
| `*_mixin.py` | `cleanup_mixin.py`, `column_translation_mixin.py` | Mixin classes |
| `*_manager.py` | `peer_protocol_manager.py`, `connection_manager.py` | Manager/coordinator classes |
| `*_seeder.py` | `http_seeder.py`, `udp_seeder.py`, `dht_seeder.py` | Protocol-specific seeders |
| `base_*.py` | `base_tab.py`, `base_component.py`, `base_seeder.py` | Base classes |

---

## 🎨 GTK Widget ID Conventions

Widget IDs in XML files follow these patterns:
- **Settings widgets**: `listening_port`, `upnp_enabled`, `proxy_type`
- **Buttons**: `random_port_button`, `search_clear`
- **Containers**: `settings_notebook`, `torrent_details_notebook`
- **Labels**: `status_label`, `peers_count_label`

Access widgets via builder:
```python
widget = self.builder.get_object("widget_id")
# Or with caching (settings tabs):
widget = self.get_widget("widget_id")
```

---

## Overview

DFakeSeeder is a Python GTK4 desktop application that simulates torrent seeding activity. It's built using the Model-View-Controller (MVC) architecture pattern and supports both HTTP and UDP tracker protocols with advanced peer-to-peer networking capabilities and comprehensive settings management.

### About the Name

The name "D' Fake Seeder" is a playful nod to the Irish English accent. In Irish pronunciation, the "th" sound in "the" is often rendered as a hard "d" sound - so "the" becomes "de" or "d'". This linguistic quirk gives us "D' Fake Seeder" instead of "The Fake Seeder", celebrating the project's Irish heritage while describing exactly what it does: simulates (fakes) torrent seeding activity.

## Development Commands

### Running the Application
```bash
# Setup pipenv environment (first time)
make setup-venv

# Development run with pipenv (recommended)
make run-debug-venv

# Development run with debug output
make run-debug

# Run in Docker with debug output
make run-debug-docker

# Production run
make run
```text
### Building and Testing
```bash
# Setup pipenv environment
make setup-venv

# Install dependencies (with pipenv)
make required

# Run linting and code formatting (with pipenv)
make lint

# Run tests (with pipenv)
make test-venv

# Run tests in Docker
make test-docker

# Clean build artifacts
make clean

# Clean pipenv environment
make clean-venv

# Clean everything
make clean-all
```text
### UI Building
```bash
# Build UI with XInclude compilation
make ui-build

# Install icons to system directories
make icons
```text
### Package Building
```bash
# Build Debian package
make deb

# Build RPM package
make rpm

# Build Docker image
make docker

# Build Flatpak
make flatpak
```text
## Desktop Integration

The application includes comprehensive desktop integration features for better user experience after PyPI installation.

### Features
- Application icon in system icon theme
- Desktop file for application menu integration
- Proper taskbar icon display when launched via desktop environments
- Launch shortcuts via application menus

### Installation Commands
```bash
# Install from PyPI
pip install d-fake-seeder

# Install desktop integration (optional)
dfs-install-desktop

# Uninstall desktop integration
dfs-uninstall-desktop
```text
### Launch Methods
```bash
# Command line
dfs                    # Short command
dfakeseeder           # Original command

# Desktop environment
gtk-launch dfakeseeder  # Desktop launcher
# Or search "D' Fake Seeder" in application menu
```text
### File Locations
- **Icons**: `~/.local/share/icons/hicolor/{size}/apps/dfakeseeder.png`
- **Desktop File**: `~/.local/share/applications/dfakeseeder.desktop`
- **Application ID**: `ie.fio.dfakeseeder`

### Verification
```bash
# Check icon installation
ls ~/.local/share/icons/hicolor/*/apps/dfakeseeder.png

# Check desktop file
ls ~/.local/share/applications/dfakeseeder.desktop

# Update caches manually if needed
gtk-update-icon-cache ~/.local/share/icons/hicolor/
update-desktop-database ~/.local/share/applications/
```text
### Compatibility
Tested with GNOME Shell, KDE Plasma, XFCE, MATE, Cinnamon. Compatible with any XDG-compliant desktop environment.

## Architecture

The application follows MVC pattern with these core components:

### Main Application (`d_fake_seeder/dfakeseeder.py`)
- Entry point using Typer CLI framework
- Initializes GTK4 application with application ID "ie.fio.dfakeseeder"
- Creates and coordinates Model, View, and Controller instances
- Handles dynamic module loading with `importlib.util.find_spec`
- Sets `DFS_PATH` environment variable for resource location

### Model (`d_fake_seeder/model.py`)
- Manages torrent data using GObject signals
- Emits `data-changed` and `selection-changed` signals
- Maintains `torrent_list` and `torrent_list_attributes` (Gio.ListStore)
- Implements search filtering with fuzzy matching
- Aggregates tracker statistics across all torrents
- Creates filtered ListStore for search results

### View (`d_fake_seeder/view.py`)
- GTK4 user interface built from XML UI files in `d_fake_seeder/components/ui/`
- Main UI compiled to `components/ui/generated/generated.xml`
- Manages splash screen with fade animation
- Creates hamburger menu with about dialog
- Coordinates multiple UI components: toolbar, notebook, torrents, states, statusbar
- Handles peer connection events for UI updates
- Implements CSS styling and icon theming

### Controller (`d_fake_seeder/controller.py`)
- Coordinates between Model and View
- Initializes GlobalPeerManager for peer-to-peer networking
- Loads torrents from `~/.config/dfakeseeder/torrents/`
- Sets up connection callbacks for UI updates
- Manages application flow and user interactions

### Core Libraries

#### Logging System
- **Enhanced Logger** (`d_fake_seeder/lib/logger.py`): Centralized logging with automatic timestamping and performance tracking
- **Performance Context Managers**: `logger.performance.operation_context()` for automatic timing of operations
- **Structured Logging**: Consistent class name context and message formatting across entire codebase
- **Debug Capabilities**: Conditional debug output and widget discovery printing
- **Error Handling**: Proper exception logging with `exc_info=True` for full stack traces

#### Settings System
- **AppSettings** (`d_fake_seeder/domain/app_settings.py`): Unified GObject-based singleton with signal system, file watching, and thread-safe operations
- **SettingsDialog** (`d_fake_seeder/components/component/settings/settings_dialog.py`): Comprehensive tabbed settings UI

#### Peer-to-Peer Networking (`d_fake_seeder/domain/torrent/`)
- `global_peer_manager.py`: Central peer connection coordinator
- `peer_connection.py`: BitTorrent peer protocol implementation (BEP-003)
- `peer_server.py`: Incoming connection server
- `peer_protocol_manager.py`: Protocol state management
- `torrent_peer_manager.py`: Per-torrent peer handling
- `bittorrent_message.py`: BitTorrent message parsing

#### Torrent Management
- `torrent.py`: Core torrent file parsing with multi-threaded workers
- `file.py`: Torrent file bencode parsing
- `seeder.py`: Main seeding coordination logic
- `seeders/`: Protocol-specific implementations
  - `http_seeder.py`: HTTP tracker communication
  - `udp_seeder.py`: UDP tracker communication
  - `base_seeder.py`: Common seeder functionality
  - `dht_seeder.py`: DHT protocol implementation

#### UI Components (`d_fake_seeder/components/component/`)
- `toolbar.py`: Application toolbar with search functionality
- `torrents.py`: Torrent list view with column management
- `statusbar.py`: Status information display
- `states.py`: Application state management
- `sidebar.py`: Category filtering sidebar
- `settings/`: Comprehensive settings interface with modular tabs
  - `settings_dialog.py`: Main settings dialog coordinator
  - `*_tab.py`: Individual settings category tabs (General, Connection, Peer Protocol, etc.)
- `torrent_details/`: Modular torrent details interface
  - `notebook.py`: Torrent details tab coordinator
  - `*_tab.py`: Individual detail tabs (Status, Files, Peers, etc.)
  - `incoming_connections_tab.py` / `outgoing_connections_tab.py`: Peer connection displays

## Settings and Configuration

### Configuration Files
- Default config: `d_fake_seeder/config/default.json` (comprehensive defaults with 178 lines)
- User config: `~/.config/dfakeseeder/settings.json` (auto-created from default)
- Torrent directory: `~/.config/dfakeseeder/torrents/`

### Settings Architecture
- Unified `AppSettings` singleton (`d_fake_seeder/domain/app_settings.py`)
- Three-layer data structure: defaults → user settings → transient data (torrents)
- Thread-safe operation with `threading.Lock`
- GObject signal system for real-time settings updates
- File watching with `watchdog` for automatic reload
- Nested attribute access with dot notation support
- Debounced saves (1 second delay to prevent excessive disk writes)
- Settings validation and export/import functionality

### Enhanced Configuration Structure
```json
{
  "peer_protocol": {
    "handshake_timeout_seconds": 30.0,
    "message_read_timeout_seconds": 60.0,
    "keep_alive_interval_seconds": 120.0,
    "contact_interval_seconds": 300.0
  },
  "seeders": {
    "port_range_min": 1025,
    "port_range_max": 65000,
    "udp_timeout_seconds": 5,
    "http_timeout_seconds": 10
  },
  "ui_settings": {
    "splash_display_duration_seconds": 2,
    "notification_timeout_min_ms": 2000
  },
  "seeding_profiles": {
    "conservative": { "upload_limit": 50, "max_connections": 100 },
    "balanced": { "upload_limit": 200, "max_connections": 200 },
    "aggressive": { "upload_limit": 0, "max_connections": 500 }
  }
}
```text
### Key Settings Categories
- **Application Behavior**: Auto-start, minimize to tray, window management
- **Interface**: Theme selection, language, window persistence
- **Connection**: Listening port, UPnP, connection limits, proxy settings
- **Peer Protocol**: Timeout settings, keep-alive intervals, handshake configuration
- **BitTorrent Protocol**: DHT, PEX, user agent, announce intervals
- **Speed Management**: Upload/download limits, alternative speeds, scheduler
- **Web UI**: HTTP interface, authentication, security settings
- **Advanced**: Logging levels, disk cache, performance tuning, debug options

## UI Development

### UI Architecture
- Modular XML-based UI with XInclude system
- Main UI: `d_fake_seeder/components/ui/ui.xml` → `components/ui/generated/generated.xml`
- Component UIs: `components/ui/notebook/`, `components/ui/settings/`, `components/ui/window/`
- CSS styling: `components/ui/css/styles.css`

### Settings UI Structure
- Multi-tab interface with comprehensive configuration options:
  - **General**: Application behavior, themes, language, configuration management
  - **Connection**: Network ports, proxy settings, connection limits, UPnP
  - **Peer Protocol**: Timeout settings, keep-alive intervals, seeder configuration
  - **BitTorrent**: DHT, PEX, encryption, user agent settings
  - **Speed**: Upload/download limits, alternative speeds, scheduler
  - **Advanced**: Logging, performance, expert settings, keyboard shortcuts
- Generated UI: `components/ui/generated/settings_generated.xml` (compiled from modular components)
- Modular XML components in `d_fake_seeder/components/ui/settings/`:
  - `general.xml`: Application behavior and interface preferences
  - `connection.xml`: Network configuration and proxy settings
  - `peer_protocol.xml`: Protocol timeouts and seeder parameters
  - `advanced.xml`: Expert settings with search functionality

### Icon System
- Application icons in multiple sizes: 16×16 to 256×256
- Desktop integration with XDG icon theme
- Icon installation via `make icons`

## Project Structure

```text
d_fake_seeder/                 # Main package (284 Python files)
├── dfakeseeder.py             # Main application entry point (Typer CLI)
├── dfakeseeder_tray.py        # System tray application
├── model.py                   # Data model with GObject signals
├── view.py                    # GTK4 UI coordinator
├── controller.py              # MVC controller with peer manager
├── post_install.py            # Desktop integration script
├── setup_helper.py            # Installation helper
│
├── domain/                    # Business logic layer
│   ├── app_settings.py        # Unified settings singleton
│   ├── torrent/               # BitTorrent implementation
│   │   ├── global_peer_manager.py  # Central peer coordinator
│   │   ├── peer_connection.py      # Peer protocol (BEP-003)
│   │   ├── torrent.py              # Core torrent handling
│   │   ├── seeder.py               # Main seeding logic
│   │   ├── seeders/                # Protocol implementations
│   │   │   ├── http_seeder.py
│   │   │   ├── udp_seeder.py
│   │   │   ├── dht_seeder.py
│   │   │   └── base_seeder.py
│   │   ├── protocols/              # Protocol extensions
│   │   │   ├── dht/                # DHT implementation
│   │   │   ├── extensions/         # BEP extensions (PEX, metadata)
│   │   │   └── transport/          # uTP transport
│   │   ├── simulation/             # Traffic simulation
│   │   └── model/                  # Data models
│   └── translation_manager/   # i18n system (package)
│
├── components/                # UI layer
│   ├── component/             # Python UI components
│   │   ├── base_component.py  # Component base class
│   │   ├── toolbar.py, torrents.py, statusbar.py, states.py, sidebar.py
│   │   ├── settings/          # Settings dialog tabs (13 files)
│   │   │   ├── settings_dialog.py
│   │   │   ├── base_tab.py, settings_mixins.py
│   │   │   └── *_tab.py       # general, connection, speed, etc.
│   │   └── torrent_details/   # Torrent details tabs (12 files)
│   │       ├── notebook.py, base_tab.py, tab_mixins.py
│   │       └── *_tab.py       # status, files, peers, log, etc.
│   ├── ui/                    # GTK4 XML UI definitions
│   │   ├── ui.xml, settings.xml  # Main templates
│   │   ├── generated/         # ⚠️ DO NOT EDIT - auto-generated
│   │   ├── settings/          # Settings dialog XML
│   │   ├── notebook/          # Tab XML components
│   │   ├── window/            # Window layouts
│   │   └── css/               # Stylesheets
│   ├── images/                # Icons and assets
│   ├── locale/                # Translations (21 languages)
│   │   ├── dfakeseeder.pot    # Translation template
│   │   └── {lang}/LC_MESSAGES/  # PO/MO files
│   └── widgets/               # Custom GTK widgets
│
├── lib/                       # Infrastructure
│   ├── logger.py              # Enhanced logging system
│   ├── dbus_client.py         # D-Bus client for tray
│   ├── seeding_profile_manager.py
│   ├── metrics_collector.py
│   ├── handlers/              # Event handlers
│   └── util/                  # Utility modules (21 files)
│       ├── cleanup_mixin.py, column_translation_mixin.py
│       ├── dbus_unifier.py    # D-Bus server
│       └── helpers, constants, format_helpers, etc.
│
└── config/                    # Default configuration
    └── default.json           # Comprehensive defaults (360 lines)
```text
## Dependency Management

### Pipenv (Primary)
- `Pipfile` and `Pipfile.lock` for dependency management
- Python 3.11+ requirement
- Virtual environment automation
- Development and production dependency separation

### Poetry (Legacy)
- `pyproject.toml` configuration present but not actively used
- Provides CLI scripts: `dfs`, `dfakeseeder`, `dfs-install-desktop`, `dfs-uninstall-desktop`
- Version management and build configuration

## Packaging and Installation

### Installation Scripts
- `post_install.py`: Automated desktop integration for PyPI installations
- Icon installation to `~/.local/share/icons/hicolor/`
- Desktop file generation following XDG standards
- Comprehensive Makefile targets for system integration

### Packaging Support
- **Debian**: `.deb` package building
- **RPM**: `.rpm` package building
- **Flatpak**: Containerized app packaging
- **Docker**: Containerized development and deployment

## Development Notes

### Technology Stack
- GTK4 with PyGObject bindings
- Asyncio for peer-to-peer networking
- GObject signals for event handling
- Typer for CLI interface
- Watchdog for file monitoring

### Code Quality
- Black, flake8, and isort for code formatting (via `make lint`)
- Pytest testing framework
- Comprehensive logging with structured output
- Thread-safe design with proper locking

### Build System
- Comprehensive Makefile with 50+ targets for complete development workflow
- **UI Building**: XInclude XML processing with xmllint validation (`make ui-build`)
- **Icon Installation**: Multi-size icon copying to system directories (`make icons`)
- **Pipenv Integration**: Virtual environment management with all `-venv` targets
- **Quality Assurance**: Automated linting, formatting, and testing
- **Packaging**: Multi-format support (deb, rpm, flatpak, docker)
- **Development**: Debug modes, logging configuration, environment setup

## Recent Architectural Enhancements

### Advanced Peer-to-Peer Networking
- **GlobalPeerManager**: Central coordinator for all peer connections with background worker threads
- **Real-time Connection Monitoring**: Live display of incoming/outgoing peer connections
- **BitTorrent Protocol Implementation**: Full BEP-003 compliance with proper handshakes
- **Asynchronous Networking**: Socket-based connections with asyncio support
- **Connection Pooling**: Efficient resource management with configurable limits

### Enhanced Settings System
- **Multi-Tab Settings Interface**: Comprehensive configuration with specialized tabs
- **Real-time Validation**: Settings validation with immediate feedback
- **Configuration Profiles**: Predefined seeding profiles (conservative, balanced, aggressive)
- **Search Functionality**: Built-in settings search with keyboard shortcuts
- **Export/Import**: Configuration backup and restore capabilities

### Runtime Language Translation System ✅ **COMPLETED**
- **TranslationManager**: Complete internationalization system with automatic widget translation
- **21 Language Support**: Full infrastructure for en, es, fr, de, it, pt, ru, zh, ja, ko, ar, hi, nl, sv, pl, bn, fa, ga, id, tr, vi
- **Runtime Language Switching**: Dynamic language changes without application restart
- **Column Header Translation**: Automatic translation of table/list column headers
- **Settings Dialog Translation**: Complete translation of all settings interface elements
- **GTK Integration**: Proper GTK translation domain binding for UI elements
- **Translation Tools**: Automated string extraction and compilation utilities
- **Locale Infrastructure**: Full locale directory structure with PO/MO file management

### UI Architecture Improvements
- **Modular Component System**: Reusable UI components with clear separation
- **Signal-Based Communication**: GObject signals for loose coupling between components
- **Responsive Design**: Automatic pane resizing and layout adaptation
- **Animated Elements**: Splash screen fade effects and smooth transitions
- **Theme Support**: CSS-based styling with theme switching capabilities

## Architectural Validation & Structure Analysis

### Package Structure Assessment (Updated 2025-12)

**Status: EXCELLENT** ✅ - Well-organized with clear separation of concerns.

#### Directory Organization

```text
d_fake_seeder/
├── model.py, view.py, controller.py    # Core MVC components (root level)
├── domain/                              # Business logic layer
│   ├── app_settings.py                  # Unified settings singleton
│   ├── torrent/                         # BitTorrent implementation (40+ files)
│   │   ├── seeders/                     # Protocol implementations (4 files)
│   │   ├── protocols/                   # Protocol extensions (DHT, PEX, etc.)
│   │   ├── simulation/                  # Traffic simulation
│   │   └── model/                       # Data models (6 files)
│   └── translation_manager/             # i18n system (package)
├── components/                          # UI layer
│   ├── component/                       # Python UI components
│   │   ├── settings/                    # Settings tabs (13 files)
│   │   └── torrent_details/             # Detail tabs (12 files)
│   ├── ui/                              # GTK XML definitions
│   └── locale/                          # Translations (21 languages)
└── lib/                                 # Infrastructure
    ├── logger.py                        # Enhanced logging
    ├── util/                            # Utilities (21 files)
    └── handlers/                        # Event handlers
```text
#### MVC Pattern Integrity: **MAINTAINED** ✅
- **Model Layer** (`model.py`, `domain/`): Pure data management with GObject signals
- **View Layer** (`view.py`, `components/`): Clean UI coordination with modular architecture
- **Controller Layer** (`controller.py`): Proper MVC coordination with GlobalPeerManager integration
- **Minimal Coupling**: Notification patterns used appropriately without violating MVC principles

#### Code Quality Metrics
- **Total Python files**: 284 across the package
- **Naming consistency**: ✅ `*Tab` suffix, `*_tab.py` file pattern
- **Inheritance patterns**: ✅ Proper use of base classes and mixins
- **Import dependencies**: ✅ Clean structure with lazy imports where needed
- **Component architecture**: ✅ Single responsibility principle maintained

## ✅ Completed Major Features

This section documents major features that have been fully implemented and are considered complete.

### 🌍 Internationalization & Localization System (2024-09-27)

**Status: COMPLETE** - Full i18n/l10n implementation with runtime language switching

#### Core Implementation
- **TranslationManager** (`domain/translation_manager/`): Complete automatic widget translation system (package with GTK3/GTK4 implementations)
- **ColumnTranslations** (`lib/util/column_translations.py`): Centralized column header translation
- **ColumnTranslationMixin** (`lib/util/column_translation_mixin.py`): Reusable column translation functionality

#### Language Support
- **21 Languages**: en, es, fr, de, it, pt, ru, zh, ja, ko, ar, hi, nl, sv, pl, bn, fa, ga, id, tr, vi
- **Complete Infrastructure**: PO/MO files, gettext integration, locale detection
- **Build System**: Advanced translation build manager with validation and compilation

#### UI Translation Features
- **Runtime Language Switching**: Change language without application restart
- **Settings Dialog Translation**: Complete multi-tab settings interface translation
- **Column Header Translation**: Dynamic table/list column header updates
- **GTK Integration**: Proper translation domain binding for all UI elements
- **Signal-Based Updates**: Automatic UI refresh on language changes

#### Translation Fixes Implemented
- **Settings Signal Loop Prevention**: Fixed infinite loops in settings dialog translation
- **Signal Connection Management**: Proper GTK signal block/unblock patterns
- **Translation Function Timing**: Fixed column translation update timing issues
- **Static Method Bug Fixes**: Corrected undefined variable issues in translation utilities

#### Development Tools
- **Translation Build Manager**: Advanced build system with quality gates
- **String Extraction**: Automated extraction from Python and XML sources
- **Validation Tools**: Translation completeness and quality checking
- **Makefile Integration**: Complete build system integration

### 🔧 Runtime Translation Infrastructure (2024-09-27)

**Status: COMPLETE** - All translation system bugs resolved, fully functional

#### Architecture Achievements
- **Component Isolation**: Settings tabs prevented from creating translation loops
- **Signal Management**: Proper GTK signal handling for dropdown widgets
- **Translation Timing**: Correct sequencing of translation function registration
- **Error Resilience**: Graceful handling of missing translations and edge cases

#### Technical Implementations
- **TranslationMixin Isolation**: Prevented auto-connection in settings components
- **Handler Block/Unblock**: Proper GTK signal management patterns
- **Translation Function Lifecycle**: Correct timing of function updates during language changes
- **Debug Infrastructure**: Comprehensive debug output for troubleshooting

#### User Experience
- **Seamless Language Changes**: Instant UI updates without glitches
- **Consistent Behavior**: All UI elements translate uniformly
- **No Application Restart**: Full functionality without restart requirements
- **Fallback Handling**: Graceful degradation for incomplete translations

### 📝 Development Planning System (2024-09-27)

**Status: COMPLETE** - Comprehensive planning documentation established

#### Planning Documentation
- **plans/LOCALIZATION_PLAN.md**: Detailed implementation roadmap (moved to plans/completed/)
- **docs/LOCALIZATION.md**: Comprehensive system documentation
- **docs/FEATURE_COMPARISON.md**: Industry analysis and feature recommendations
- **plans/PROTOCOL_INTEGRATION_PLAN.md**: Advanced BitTorrent protocol enhancement roadmap
- **docs/CONFIGURATION.md**: Configuration system documentation
- **docs/PACKAGING.md**: Packaging and distribution documentation
- **docs/PERFORMANCE_AUDIT_2025-10-05.md**: Performance analysis and optimization recommendations

#### Planning Achievements
- **Foundation Analysis**: Complete assessment of existing capabilities
- **Implementation Roadmaps**: Detailed technical implementation plans
- **Industry Research**: Comprehensive analysis of competing solutions
- **Technical Specifications**: Detailed architectural recommendations

## Recent Improvements (2025-09-28)

### ✅ **Logging System Overhaul - COMPLETED**

**Comprehensive logging standardization across the entire DFakeSeeder codebase:**

#### **Enhanced Logger Infrastructure**
- **Automatic Timestamping**: All log messages now include precise timing information
- **Performance Context Managers**: `logger.performance.operation_context()` for automatic operation timing
- **Simplified API**: Removed confusing timing methods, standardized on `logger.debug()` and `logger.info()`
- **Structured Context**: Consistent class name context throughout all components

#### **Print Statement Cleanup**
- **849 Print Statements Replaced**: Automated replacement of debug print statements with proper logger calls
- **Code Quality**: Removed all commented print statements and replaced `traceback.print_exc()` with proper error logging
- **Consistency**: Uniform logging patterns across all Python files

#### **Technical Improvements**
- **Manual Timing Removal**: Eliminated redundant manual timing code in favor of automatic logger timing
- **Error Handling**: Enhanced exception logging with `exc_info=True` for complete stack traces
- **Debug Optimization**: Conditional debug output to prevent performance impact in production
- **Recursion Safety**: Special handling in log display components to prevent logging recursion

#### **Files Enhanced**
- `d_fake_seeder/lib/logger.py` - Core logging infrastructure with performance tracking
- `d_fake_seeder/domain/translation_manager/` - Translation system timing optimization
- `d_fake_seeder/view.py` - UI component initialization timing
- `d_fake_seeder/model.py` - Model operations and language switching timing
- **All Python files** - Comprehensive print statement replacement and error handling improvements

#### **Benefits Achieved**
- **Zero Print Statements**: Clean codebase with no debug print clutter
- **Consistent Performance Tracking**: Automatic timing for all operations
- **Enhanced Debugging**: Structured logging with class context and timing information
- **Improved Maintainability**: Centralized logging configuration and standardized patterns
- **Better Error Reporting**: Complete exception information with stack traces

---

*Features marked as complete have been fully implemented, tested, and documented. They represent stable, production-ready functionality that no longer requires active development.*