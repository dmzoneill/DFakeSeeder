# Single Instance Implementation

DFakeSeeder implements comprehensive single-instance protection using **four complementary methods** to ensure only one instance of the main application and tray runs at a time.

## 📋 Table of Contents

- [Overview](#overview)
- [Implementation Methods](#implementation-methods)
  - [Method 1: GTK4 Application Registration](#method-1-gtk4-application-registration-main-app-only)
  - [Method 2: D-Bus Service Check](#method-2-d-bus-service-check)
  - [Method 3: Unix Socket Lock](#method-3-unix-socket-lock)
  - [Method 4: PID File Lock](#method-4-pid-file-lock)
- [Defense-in-Depth Strategy](#defense-in-depth-strategy)
- [User Experience](#user-experience)
- [Testing](#testing)
- [Technical Implementation](#technical-implementation)

## Overview

The single-instance system prevents multiple instances of:
- **Main Application** (`dfakeseeder.py`): GTK4-based torrent seeding application
- **Tray Application** (`dfakeseeder_tray.py`): GTK3-based system tray interface

Each application uses multiple detection methods in a **layered defense-in-depth** approach.

## Implementation Methods

### Method 1: GTK4 Application Registration (Main App Only)

**Technology**: GTK4 built-in single-instance support

**How it works**:
- GTK4's `Gtk.Application` automatically provides single-instance behavior
- When a second instance starts, GTK4 forwards the `activate` signal to the existing instance
- The existing instance presents its window instead of creating a new one

**Advantages**:
- ✅ Built-in, no custom code needed
- ✅ Reliable within GTK4 applications
- ✅ Automatically focuses existing window
- ✅ Cross-desktop compatible

**Limitations**:
- ⚠️ Only available in GTK4 (not GTK3 tray)
- ⚠️ Relies on GTK application framework

**Implementation**:
```python
class DFakeSeeder(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="ie.fio.dfakeseeder",
            flags=Gio.ApplicationFlags.FLAGS_NONE,  # Default: single instance
        )
        self.ui_initialized = False

    def do_activate(self):
        if self.ui_initialized:
            # Another instance tried to start - present existing window
            self.view.window.present()
            self._show_already_running_dialog()
            return

        # First instance - initialize UI
        # ... normal initialization ...
        self.ui_initialized = True
```

**User Feedback**: GTK4 AlertDialog with message about existing instance

### Method 2: D-Bus Service Check

**Technology**: D-Bus session bus service registration

**How it works**:
- Main application registers D-Bus service: `ie.fio.dfakeseeder`
- Before GTK initialization, check if service is already registered
- If registered, another instance exists

**Advantages**:
- ✅ Fast detection (no file I/O)
- ✅ Automatic cleanup when process dies
- ✅ Can detect running instance before GTK initialization
- ✅ Works across different desktop environments

**Limitations**:
- ⚠️ Requires D-Bus (standard on Linux)
- ⚠️ Only works for main app (tray doesn't register D-Bus service)

**Implementation**:
```python
class DBusSingleInstance(SingleInstanceChecker):
    def is_already_running(self) -> bool:
        connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        try:
            name_owner = connection.call_sync(
                "org.freedesktop.DBus",
                "/org/freedesktop/DBus",
                "org.freedesktop.DBus",
                "GetNameOwner",
                GLib.Variant("(s)", ("ie.fio.dfakeseeder",)),
                ...
            )
            if name_owner:
                return True  # Service already registered
        except GLib.Error as e:
            if "NameHasNoOwner" in str(e):
                return False  # No instance running
        return False
```

**User Feedback**: Console message before GTK initialization

### Method 3: Unix Socket Lock

**Technology**: Abstract Unix domain socket in Linux namespace

**How it works**:
- Create abstract Unix socket with name `\0dfakeseeder_<app_name>`
- Abstract sockets exist only in memory (no filesystem entry)
- Socket binding is atomic - only one process can bind
- Socket is automatically released when process dies

**Advantages**:
- ✅ Most robust - automatic cleanup on crash
- ✅ No stale locks possible
- ✅ Atomic operation (race-condition free)
- ✅ Works for both main app and tray
- ✅ No filesystem cleanup needed

**Limitations**:
- ⚠️ Linux-specific (abstract namespace)
- ⚠️ Fallback needed for other platforms

**Implementation**:
```python
class SocketLock(SingleInstanceChecker):
    def __init__(self, name: str):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket_address = f"\0dfakeseeder_{name}"  # Abstract namespace

    def is_already_running(self) -> bool:
        try:
            self.socket.bind(self.socket_address)
            self.socket.listen(1)
            return False  # Successfully acquired lock
        except OSError:
            return True   # Another instance holds lock
```

**User Feedback**: Included in multi-method detection message

### Method 4: PID File Lock

**Technology**: Traditional PID file with active process checking

**How it works**:
- Create lock file at `~/.config/dfakeseeder/<app_name>.lock`
- Write current process ID to file
- Check if PID in file refers to running process
- Remove stale lock files automatically

**Advantages**:
- ✅ Cross-platform compatible
- ✅ Language-agnostic
- ✅ Simple and well-understood
- ✅ Works for both main app and tray

**Limitations**:
- ⚠️ Stale locks possible (mitigated by PID checking)
- ⚠️ Requires file system access
- ⚠️ Small race condition window

**Implementation**:
```python
class PIDFileLock(SingleInstanceChecker):
    def is_already_running(self) -> bool:
        if self.lockfile.exists():
            pid = int(self.lockfile.read_text().strip())
            if self._is_process_running(pid):
                return True  # Instance running
            else:
                self.lockfile.unlink()  # Remove stale lock

        # Create lock file
        self.lockfile.write_text(str(os.getpid()))
        return False

    def _is_process_running(self, pid: int) -> bool:
        try:
            os.kill(pid, 0)  # Signal 0 = check if process exists
            return True
        except OSError:
            return False
```

**User Feedback**: Included in multi-method detection message

## Defense-in-Depth Strategy

The multi-method approach provides **layered protection**:

### Main Application Check Order:

1. **D-Bus Check** (fastest, pre-GTK)
   - Detects existing instance before GTK initialization
   - Exits early if another instance detected

2. **Socket Lock** (most robust)
   - Atomic lock acquisition
   - Automatic cleanup on crash

3. **PID File Lock** (fallback safety)
   - Additional verification
   - Cross-platform compatibility

4. **GTK4 Registration** (framework level)
   - Final layer within GTK framework
   - Handles case where previous checks fail

### Tray Application Check Order:

1. **Socket Lock** (primary, GTK3 has no built-in support)
2. **PID File Lock** (secondary safety)

**Note**: Tray skips D-Bus check since it doesn't register a D-Bus service.

## User Experience

### When Second Instance Detected:

**Main Application**:
- Console message with detection method
- GTK4 AlertDialog if GTK initialized
- Existing window brought to front
- Clean exit with code 0

**Tray Application**:
- GTK3 MessageDialog with detection method
- Console fallback if dialog fails
- Clean exit with code 0

### Dialog Messages:

**Main App** (GTK4):
```
Title: DFakeSeeder Already Running

Message: DFakeSeeder is already running. The existing window
has been brought to front.

Detection method: <method_name>

[OK]
```

**Tray App** (GTK3):
```
Title: DFakeSeeder Tray Already Running

Message: Another instance of DFakeSeeder Tray is already running.

Detection method: <method_name>

Please check your system tray.

[OK]
```

## Testing

### Manual Testing:

```bash
# Test main application
make run-debug &
sleep 3
make run-debug  # Should detect existing instance

# Test tray application
python3 d_fake_seeder/dfakeseeder_tray.py &
sleep 3
python3 d_fake_seeder/dfakeseeder_tray.py  # Should detect existing instance
```

### Automated Testing:

```bash
# Run comprehensive test suite
./test_single_instance.sh
```

The test script verifies:
1. GTK4 single instance for main app
2. D-Bus detection for main app
3. Socket lock for main app
4. PID file lock for main app
5. Socket + PID lock for tray app

### Expected Output:

```
==========================================
DFakeSeeder Single Instance Test Suite
==========================================

Test 1: GTK4 Single Instance (Main App)
✓ PASS: First instance started successfully
✓ PASS: Second instance was blocked

Test 2: D-Bus Detection (Main App)
✓ PASS: D-Bus service registered
✓ PASS: Second instance detected existing instance

Test 3: Socket Lock (Main App)
✓ PASS: Socket lock prevented second instance

Test 4: PID File Lock (Main App)
✓ PASS: PID file lock prevented second instance

Test 5: Tray Application Single Instance
✓ PASS: Socket/PID lock prevented second instance

==========================================
Tests Passed: 10
Tests Failed: 0
All tests passed! ✓
==========================================
```

## Technical Implementation

### File Structure:

```
d_fake_seeder/
├── lib/util/single_instance.py       # Core implementation
├── dfakeseeder.py                     # Main app with all 4 methods
└── dfakeseeder_tray.py               # Tray app with Socket + PID

test_single_instance.sh                # Automated test suite
```

### Lock File Locations:

- Main app socket: `\0dfakeseeder_main` (abstract)
- Main app PID: `~/.config/dfakeseeder/dfakeseeder-main.lock`
- Tray socket: `\0dfakeseeder_tray` (abstract)
- Tray PID: `~/.config/dfakeseeder/dfakeseeder-tray.lock`

### Cleanup:

All methods implement automatic cleanup:
- **GTK4**: Framework handles cleanup
- **D-Bus**: Service automatically unregistered on exit
- **Socket**: Kernel releases socket on process exit
- **PID File**: `atexit` handler removes file

### Error Handling:

Each method gracefully handles errors:
- Failed checks log debug message
- Returns `False` (no existing instance)
- Next method in chain is tried
- No single point of failure

## Benefits

1. **Reliability**: Four independent methods ensure detection
2. **Performance**: D-Bus check exits early before GTK initialization
3. **Robustness**: Socket lock prevents stale locks
4. **Compatibility**: PID file works across platforms
5. **User-Friendly**: Clear dialogs explain what happened
6. **Fail-Safe**: Multiple layers prevent edge cases

## Conclusion

The four-method approach provides comprehensive single-instance protection:
- **GTK4 registration** handles framework-level detection
- **D-Bus check** provides fast pre-GTK detection
- **Socket lock** offers robust, crash-safe protection
- **PID file** ensures cross-platform compatibility

This defense-in-depth strategy ensures DFakeSeeder and its tray application never run multiple instances, providing a polished user experience.
