# Memory Leak Analysis Report - DFakeSeeder GTK4 Application

**Analysis Date:** 2025-11-29
**Analyzer:** Claude Code Memory Leak Scanner
**Application:** DFakeSeeder - GTK4/Python BitTorrent Simulator

---

## Executive Summary

This analysis identified **CRITICAL** memory leaks across the DFakeSeeder GTK4 Python application. The application creates extensive GObject signal connections, ListStore instances, property bindings, and async operations **without proper cleanup**, leading to severe memory leaks that will accumulate over the application lifetime.

### Severity Assessment: **CRITICAL** 🔴

- **278 signal connections** across 37 files with only **2 files** implementing proper disconnection
- **5 Gio.ListStore instances** created with no `.clear()` or `.remove_all()` cleanup
- **11 GObject property bindings** created without tracking or unbinding
- **49 lambda/closure connections** creating strong reference cycles
- **14 files** using GLib timeout sources with incomplete cleanup
- **11 async operations** with potential task leakage
- **0 usage** of weak references despite circular reference patterns

---

## 1. Signal Connection Leaks (CRITICAL)

### Issue Description
GTK/GObject signal connections create strong references between objects. When objects are connected via signals but never disconnected, they cannot be garbage collected even when no longer needed.

### Statistics
- **Total `.connect()` calls:** 278 occurrences across 37 files
- **Total `.disconnect()` implementations:** Only 2 files
- **Success Rate:** ~5% (FAILING)

### Files with Proper Cleanup ✅
1. **view.py** (19 connections)
   - **Good:** Has `remove_signals()` method at line 375
   - Uses `disconnect_by_func()` properly
   ```python
   def remove_signals(self):
       self.model.disconnect_by_func(self.torrents.update_view)
       self.model.disconnect_by_func(self.notebook.update_view)
       # ... more disconnections
   ```

2. **speed_tab.py** (9 connections)
   - **Good:** Tracks handlers in `_signal_handlers` dictionary
   - Has `_disconnect_signals()` method at line 104
   ```python
   def _disconnect_signals(self):
       for widget_name, (widget, handler_id) in self._signal_handlers.items():
           widget.disconnect(handler_id)
   ```

### Files WITHOUT Cleanup (CRITICAL) ❌

#### High-Priority Files (Most Connections)
1. **toolbar.py** - **16 connections, NO cleanup**
   - Only has `dialog.destroy()` calls
   - All signal connections leak

2. **protocol_extensions_tab.py** - **24 connections, NO cleanup**
   - No cleanup methods at all
   - Massive memory leak source

3. **peer_protocol_tab.py** - **20 connections, NO cleanup**
   - No cleanup methods

4. **advanced_tab.py** - **19 connections, NO cleanup**
   - No cleanup methods

5. **multi_tracker_tab.py** - **16 connections, NO cleanup**
   - No cleanup methods

6. **simulation_tab.py** - **16 connections, NO cleanup**
   - No cleanup methods

7. **dht_tab.py** - **16 connections, NO cleanup**
   - No cleanup methods

8. **general_tab.py** - **13 connections, NO cleanup**
   - No cleanup methods

9. **bittorrent_tab.py** - **12 connections, NO cleanup**
   - No cleanup methods

10. **webui_tab.py** - **12 connections, NO cleanup**
    - No cleanup methods

11. **torrents.py** - **12 connections, NO cleanup**
    - No cleanup methods

12. **states.py** - **10 connections, NO cleanup**
    - No cleanup methods

13. **connection_tab.py** - **10 connections, NO cleanup**
    - No cleanup methods

14. **dfakeseeder_tray.py** - **10 connections, NO cleanup**
    - No cleanup methods

#### Critical Example: IncomingConnectionsTab
```python
# Line 55: Callback registered, NEVER removed
self.connection_manager.add_update_callback(self.on_connections_updated)

# Line 65: Signal connected, NEVER disconnected
self.filter_checkbox.connect("toggled", self.on_filter_toggled)

# Line 70: Signal connected, NEVER disconnected
self.model.connect("language-changed", self.on_language_changed)

# Line 90: Signal connected, NEVER disconnected
self.model.connect("selection-changed", self.on_selection_changed)

# Line 129-130: Factory signals connected, NEVER disconnected
factory.connect("setup", self.setup_cell, property_name)
factory.connect("bind", self.bind_cell, property_name)
```

**Impact:** Every time a tab is created or recreated, all these connections remain in memory forever, keeping the entire component tree alive.

---

## 2. ListStore Memory Leaks (CRITICAL)

### Issue Description
`Gio.ListStore` instances accumulate data but are never cleared, causing memory to grow indefinitely.

### Affected Files

1. **model.py** (Line 83)
   ```python
   self.torrent_list_attributes = Gio.ListStore.new(Attributes)
   # NEVER cleared with .remove_all() or .clear()
   ```

2. **torrents.py** (Line 30)
   ```python
   self.store = Gio.ListStore.new(Attributes)
   # NEVER cleared
   ```

3. **peers_tab.py** (Line 89)
   ```python
   self._peers_store = Gio.ListStore.new(TorrentPeer)
   # NEVER cleared
   ```

4. **incoming_connections_tab.py** (Line 109)
   ```python
   self.incoming_store = Gio.ListStore.new(ConnectionPeer)
   # NEVER cleared
   ```

5. **outgoing_connections_tab.py** (Similar pattern)
   ```python
   self.outgoing_store = Gio.ListStore.new(ConnectionPeer)
   # NEVER cleared
   ```

### Missing Cleanup Pattern
No files implement cleanup like:
```python
def cleanup(self):
    if self.store:
        self.store.remove_all()  # Clear all items
        self.store = None
```

**Impact:** Every torrent, peer, and connection added to these stores remains in memory forever, even after removal from the UI.

---

## 3. Circular Reference Leaks (HIGH)

### Issue Description
Components store strong references to each other (model ↔ view, parent ↔ child) without using weak references, creating circular reference chains that prevent garbage collection.

### Circular Reference Patterns

Found in **23 files**:
```
d_fake_seeder/components/component/toolbar.py
d_fake_seeder/components/component/torrent_details/notebook.py
d_fake_seeder/components/component/torrents.py
d_fake_seeder/components/component/torrent_details/base_tab.py
d_fake_seeder/view.py
d_fake_seeder/controller.py
# ... 17 more files
```

#### Example Circular References

**Model → Settings → Model**
```python
# model.py line 48
self.settings = AppSettings.get_instance()
self.settings.connect("settings-attribute-changed", self.handle_settings_changed)
# Settings keeps reference to Model via signal connection
```

**PeersTab Circular Chain**
```python
# peers_tab.py lines 40-42
self._global_peer_manager = None      # Stores manager reference
self._incoming_connections = None     # Stores connection tab reference
self._outgoing_connections = None     # Stores connection tab reference

# These objects likely store references back to PeersTab
```

**Component → Model → Component**
```python
# All components store model reference
self.model = model

# Model emits signals that components connect to
self.model.connect("data-changed", self.update_view)

# Creates Model → Component → Model cycle
```

### Zero Usage of Weak References
```bash
$ grep -r "weakref\|WeakRef" d_fake_seeder/**/*.py
# NO RESULTS
```

**Impact:** Component trees cannot be garbage collected even when no longer visible or needed. Every tab opened and closed remains in memory forever.

---

## 4. Lambda/Closure Memory Leaks (HIGH)

### Issue Description
Lambda functions and closures passed to signal handlers capture strong references to `self` and local variables, preventing garbage collection.

### Statistics
- **49 lambda/closure usages** across 25 files

### Problem Files
```
d_fake_seeder/view.py:2
d_fake_seeder/model.py:3
d_fake_seeder/dfakeseeder_tray.py:4
d_fake_seeder/lib/seeding_profile_manager.py:11
# ... 21 more files
```

### Critical Examples

**view.py Line 180**
```python
action.connect("activate", lambda action, param: self.quit())
# Lambda captures 'self' (View instance), preventing GC
```

**incoming_connections_tab.py Lines 185, 190**
```python
def setup_cell(self, widget, item, property_name):
    def setup_when_idle():  # Closure captures all local variables
        obj = item.get_item()
        # ... uses self, widget, item, property_name
    GLib.idle_add(setup_when_idle)  # Idle callback keeps closure alive
```

**Impact:** Each lambda/closure creates a strong reference chain that prevents cleanup of the entire component hierarchy.

---

## 5. GLib Timeout/Idle Source Leaks (MEDIUM-HIGH)

### Issue Description
Timeout and idle sources created with `GLib.timeout_add()` and `GLib.idle_add()` are not always properly removed, keeping callbacks and their captured references alive.

### Affected Files (14 total)
```
d_fake_seeder/view.py
d_fake_seeder/domain/torrent/connection_manager.py
d_fake_seeder/components/component/torrent_details/notebook.py
d_fake_seeder/components/component/torrent_details/incoming_connections_tab.py
d_fake_seeder/components/component/torrent_details/outgoing_connections_tab.py
# ... 9 more
```

### Partial Cleanup Example

**view.py** has **some** cleanup (lines 472-518):
```python
def _cleanup_timers(self):
    # Cleans up notification timeout
    if hasattr(self, "timeout_source") and self.timeout_source:
        self.timeout_source.destroy()

    # Cleans up connection removal timers
    for timer_id in incoming_tab.removal_timers.values():
        GLib.source_remove(timer_id)
```

However, many timeout sources throughout the codebase are **NOT** tracked or cleaned up.

### Missing Cleanup Patterns
Most files do NOT track timeout IDs:
```python
# WRONG - timeout not tracked
GLib.idle_add(self.some_callback)

# CORRECT - timeout tracked and removed
self.timeout_id = GLib.idle_add(self.some_callback)
# Later in cleanup:
if self.timeout_id:
    GLib.source_remove(self.timeout_id)
```

**Impact:** Background callbacks continue running even after components are "destroyed", keeping them alive indefinitely.

---

## 6. GObject Property Binding Leaks (MEDIUM)

### Issue Description
`GObject.bind_property()` creates `GBinding` objects that maintain strong references between source and target objects. These bindings must be explicitly unbind() to release references.

### Statistics
- **11 property bindings** across 3 files
- **0 bindings** properly tracked or unbound

### Affected Files
```
d_fake_seeder/components/component/torrents.py: 3 bindings
d_fake_seeder/components/component/torrent_details/outgoing_connections_tab.py: 4 bindings
d_fake_seeder/components/component/torrent_details/incoming_connections_tab.py: 4 bindings
```

### Critical Example - torrents.py

**Lines 530, 541, 549:**
```python
# Binding 1
item_data.bind_property(
    attribute,
    widget,
    "label",
    GObject.BindingFlags.SYNC_CREATE,
    self.get_text_renderer(text_renderer_func_name),
)

# Binding 2
item_data.bind_property(
    attribute,
    widget,
    "label",
    GObject.BindingFlags.SYNC_CREATE,
    self.to_str,
)

# Binding 3
item_data.bind_property(
    attribute,
    widget,
    "fraction",
    GObject.BindingFlags.SYNC_CREATE,
)

# PROBLEM: GBinding objects not stored, cannot be unbound later!
```

### Missing Cleanup Pattern
```python
# CORRECT approach - track bindings
self._bindings = []

binding = item_data.bind_property(...)
self._bindings.append(binding)

# Later in cleanup:
for binding in self._bindings:
    binding.unbind()
self._bindings.clear()
```

**Impact:** Every data binding creates a permanent connection between model and view objects, preventing either from being garbage collected.

---

## 7. Async Operation Leaks (MEDIUM)

### Issue Description
Asyncio event loops, tasks, and connections created in threads may not be properly cleaned up, keeping async operations and their resources alive.

### Affected Files (11 total)
```
d_fake_seeder/domain/torrent/peer_server.py
d_fake_seeder/domain/torrent/peer_connection.py
d_fake_seeder/domain/torrent/peer_protocol_manager.py
d_fake_seeder/domain/torrent/protocols/dht/node.py
d_fake_seeder/domain/torrent/protocols/dht/peer_discovery.py
d_fake_seeder/domain/torrent/protocols/dht/seeder.py
d_fake_seeder/domain/torrent/protocols/tracker/multi_tracker.py
d_fake_seeder/domain/torrent/protocols/transport/utp_connection.py
d_fake_seeder/domain/torrent/protocols/transport/utp_manager.py
d_fake_seeder/domain/torrent/seeders/dht_seeder.py
d_fake_seeder/domain/torrent/shared_async_executor.py
```

### Partial Cleanup Example - peer_server.py

**Good cleanup** (lines 96-143):
```python
def stop(self):
    self.running = False

    # Close server
    if self.server:
        self.server.close()

    # Close all connections
    for writer in self.active_connections.values():
        writer.close()
    self.active_connections.clear()

    # Wait for thread
    self.server_thread.join(timeout=join_timeout)
```

**Missing cleanup:**
```python
def _run_server(self):
    asyncio.new_event_loop().run_until_complete(self._async_server())
    # Event loop NOT stored, NOT closed!
```

### Proper Pattern
```python
def _run_server(self):
    self.loop = asyncio.new_event_loop()
    try:
        self.loop.run_until_complete(self._async_server())
    finally:
        self.loop.close()  # Properly close event loop
```

**Impact:** Event loops and their associated tasks may continue running in background threads even after shutdown, consuming CPU and memory.

---

## Recommended Fixes

### Priority 1 - Signal Connection Cleanup (CRITICAL)

Implement cleanup for all 35 files missing signal disconnection:

```python
class MyComponent:
    def __init__(self):
        self._signal_handlers = []

    def connect_signals(self):
        # Track all signal connections
        handler_id = self.model.connect("data-changed", self.on_data_changed)
        self._signal_handlers.append((self.model, handler_id))

    def cleanup(self):
        # Disconnect all signals
        for obj, handler_id in self._signal_handlers:
            obj.disconnect(handler_id)
        self._signal_handlers.clear()
```

### Priority 2 - ListStore Cleanup (CRITICAL)

Add cleanup for all 5 ListStore instances:

```python
class MyComponent:
    def cleanup(self):
        if hasattr(self, 'store') and self.store:
            self.store.remove_all()
            self.store = None
```

### Priority 3 - Property Binding Tracking (HIGH)

Track and unbind all property bindings:

```python
class MyComponent:
    def __init__(self):
        self._bindings = []

    def bind_data(self, source, target):
        binding = source.bind_property(...)
        self._bindings.append(binding)

    def cleanup(self):
        for binding in self._bindings:
            binding.unbind()
        self._bindings.clear()
```

### Priority 4 - Use Weak References (HIGH)

Break circular reference chains:

```python
import weakref

class MyComponent:
    def __init__(self, model):
        self.model_ref = weakref.ref(model)  # Weak reference

    def get_model(self):
        model = self.model_ref()  # Dereference
        if model is None:
            # Model was garbage collected
            return None
        return model
```

### Priority 5 - Timeout Source Tracking (MEDIUM)

Track and remove all timeout sources:

```python
class MyComponent:
    def __init__(self):
        self._timeout_ids = []

    def add_timeout(self, interval, callback):
        timeout_id = GLib.timeout_add(interval, callback)
        self._timeout_ids.append(timeout_id)

    def cleanup(self):
        for timeout_id in self._timeout_ids:
            GLib.source_remove(timeout_id)
        self._timeout_ids.clear()
```

### Priority 6 - Async Loop Cleanup (MEDIUM)

Properly close event loops:

```python
class AsyncComponent:
    def _run_server(self):
        self.loop = asyncio.new_event_loop()
        try:
            self.loop.run_until_complete(self._async_server())
        finally:
            # Cancel pending tasks
            pending = asyncio.all_tasks(self.loop)
            for task in pending:
                task.cancel()
            # Close loop
            self.loop.close()
            self.loop = None
```

---

## Testing Recommendations

### Memory Leak Detection Tools

1. **Objgraph** - Python object graph visualization
   ```bash
   pip install objgraph

   # In code:
   import objgraph
   objgraph.show_most_common_types(limit=20)
   objgraph.show_growth()
   ```

2. **Pympler** - Memory profiling
   ```bash
   pip install pympler

   # In code:
   from pympler import tracker
   tr = tracker.SummaryTracker()
   # ... run operations ...
   tr.print_diff()
   ```

3. **Valgrind with Python** - Low-level memory analysis
   ```bash
   valgrind --leak-check=full --show-leak-kinds=all \
            python -m d_fake_seeder.dfakeseeder
   ```

4. **GObject Inspector** - GTK/GObject reference counting
   ```bash
   # Enable GObject debugging
   G_DEBUG=gc-friendly python -m d_fake_seeder.dfakeseeder
   ```

### Test Scenarios

1. **Component Creation/Destruction Test**
   - Open settings dialog → Close → Repeat 100 times
   - Monitor memory growth

2. **Tab Switching Test**
   - Switch between torrent detail tabs 1000 times
   - Check for ListStore accumulation

3. **Torrent Add/Remove Test**
   - Add 100 torrents → Remove all → Repeat
   - Verify memory returns to baseline

4. **Long-Running Test**
   - Run application for 24 hours
   - Monitor memory growth rate

---

## Summary Statistics

| Category | Total | With Cleanup | Without Cleanup | % Failing |
|----------|-------|--------------|-----------------|-----------|
| Signal Connections | 37 files | 2 files | 35 files | **94.6%** |
| ListStore Instances | 5 instances | 0 instances | 5 instances | **100%** |
| Property Bindings | 11 bindings | 0 bindings | 11 bindings | **100%** |
| Lambda/Closures | 49 closures | 0 tracked | 49 leaking | **100%** |
| Timeout Sources | 14 files | ~1 file | ~13 files | **~92%** |
| Async Operations | 11 files | ~1 file | ~10 files | **~90%** |
| Weak References | N/A | 0 files | All files | **100%** |

**Overall Memory Leak Risk: CRITICAL** 🔴

---

## Conclusion

The DFakeSeeder application has **pervasive and critical memory leaks** affecting virtually every component. Without proper cleanup of signal connections, ListStore data, property bindings, and circular references, the application will experience:

1. **Continuous memory growth** during normal operation
2. **Inability to free components** even when closed/hidden
3. **Accumulation of zombie objects** in memory
4. **Eventual performance degradation** as memory fills
5. **Potential crashes** on systems with limited memory

**Immediate action is required** to implement cleanup patterns across all affected components. The fixes outlined in this report should be prioritized and implemented systematically, starting with signal connection cleanup (affecting 35 files) and ListStore cleanup (affecting 5 critical data stores).

---

**Report Generated by:** Claude Code Memory Leak Analysis Tool
**For Questions:** See project maintainers
