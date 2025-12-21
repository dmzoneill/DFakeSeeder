# Component Hierarchy Refactoring Plan

## Overview

Standardize the inheritance pattern across all UI components by making `BaseTorrentTab` extend `Component` (like `BaseSettingsTab` already does), and moving connection tabs to use `BaseTorrentTab`.

## Current State (Inconsistent)

```
CleanupMixin
├── Component
│   ├── BaseSettingsTab → (11 settings tabs) ✓ Good
│   ├── TorrentDetailsNotebook
│   ├── OutgoingConnectionsTab  ⚠️ Should use BaseTorrentTab
│   ├── IncomingConnectionsTab  ⚠️ Should use BaseTorrentTab
│   └── Torrents, Toolbar, States, Statusbar, Sidebar
│
└── BaseTorrentTab  ⚠️ Skips Component!
    └── DetailsTab, FilesTab, StatusTab, TrackersTab,
        OptionsTab, LogTab, MonitoringTab
```

## Target State (Consistent)

```
CleanupMixin
└── Component
    ├── BaseSettingsTab
    │   └── (11 settings tabs)
    │
    ├── BaseTorrentTab  ← NOW extends Component
    │   └── DetailsTab, FilesTab, StatusTab, TrackersTab,
    │       OptionsTab, LogTab, MonitoringTab,
    │       IncomingConnectionsTab, OutgoingConnectionsTab
    │
    └── Torrents, Toolbar, States, Statusbar, Sidebar, TorrentDetailsNotebook
```

## Benefits

| Goal | How It Helps |
|------|--------------|
| **Consistency** | All tab bases follow `XxxTab(Component)` pattern |
| **Maintainability** | Add cleanup/model features once in `Component`, all tabs get it |
| **Extensibility** | New tab types can extend `Component` or an existing base |
| **Doesn't resist change** | Clear extension points, no duplicate code to update |

---

## Phase 1: Refactor BaseTorrentTab to Extend Component

### File: `d_fake_seeder/components/component/torrent_details/base_tab.py`

### Changes Required:

1. **Change inheritance**: `class BaseTorrentTab(ABC, CleanupMixin)` → `class BaseTorrentTab(Component)`

2. **Update imports**:
   - Remove: `from d_fake_seeder.lib.util.cleanup_mixin import CleanupMixin`
   - Add: `from d_fake_seeder.components.component.base_component import Component`

3. **Update `__init__`**:
   ```python
   # BEFORE
   def __init__(self, builder: Gtk.Builder, model: Any) -> None:
       CleanupMixin.__init__(self)
       self.builder = builder
       self.model = model
       self.logger = logger
       ...

   # AFTER
   def __init__(self, builder: Gtk.Builder, model: Any) -> None:
       super().__init__()  # Calls Component.__init__() which calls CleanupMixin.__init__()
       self.builder = builder
       self.model = model  # Keep for now, but could use Component's set_model() later
       self.logger = logger
       ...
   ```

4. **Implement Component's abstract methods** (with sensible defaults):
   ```python
   def handle_model_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
       """Handle model data changes - delegates to on_torrent_data_changed."""
       pass  # Tab uses on_torrent_data_changed instead

   def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
       """Handle attribute changes."""
       pass  # Not used by tabs

   def handle_settings_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
       """Handle settings changes - delegates to on_settings_changed."""
       pass  # Tab uses on_settings_changed(key, value) instead

   def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
       """Update view - delegates to update_content."""
       if torrent:
           self.update_content(torrent)
   ```

5. **Update cleanup method**:
   ```python
   # BEFORE
   def cleanup(self) -> None:
       try:
           CleanupMixin.cleanup(self)
           ...

   # AFTER  
   def cleanup(self) -> None:
       try:
           super().cleanup()  # Calls Component.cleanup() → CleanupMixin.cleanup()
           ...
   ```

---

## Phase 2: Migrate Connection Tabs to BaseTorrentTab

### Files:
- `d_fake_seeder/components/component/torrent_details/incoming_connections_tab.py`
- `d_fake_seeder/components/component/torrent_details/outgoing_connections_tab.py`

### Changes Required for Each:

1. **Change inheritance**:
   ```python
   # BEFORE
   class IncomingConnectionsTab(Component, ColumnTranslationMixin):
   
   # AFTER
   class IncomingConnectionsTab(BaseTorrentTab, ColumnTranslationMixin):
   ```

2. **Update imports**:
   - Remove: `from d_fake_seeder.components.component.base_component import Component`
   - Add: `from d_fake_seeder.components.component.torrent_details.base_tab import BaseTorrentTab`

3. **Update `__init__`** to match BaseTorrentTab signature:
   ```python
   # BEFORE
   def __init__(self, builder: Gtk.Builder, model: Any) -> None:
       Component.__init__(self)
       ...

   # AFTER
   def __init__(self, builder: Gtk.Builder, model: Any) -> None:
       super().__init__(builder, model)
       ...
   ```

4. **Add required abstract properties/methods**:
   ```python
   @property
   def tab_name(self) -> str:
       return "Incoming Connections"  # or "Outgoing Connections"

   @property
   def tab_widget_id(self) -> str:
       return "incoming_connections_tab"  # or appropriate ID

   def _init_widgets(self) -> None:
       # Move existing widget initialization here
       pass

   def update_content(self, torrent: Any) -> None:
       # Move existing update logic here
       pass
   ```

5. **Remove/adapt Component-specific methods** that are now handled by BaseTorrentTab

---

## Phase 3: Cleanup and Consolidation

### Optional Improvements:

1. **Remove duplicate logger assignment** in BaseTorrentTab:
   - Component doesn't set `self.logger`, but BaseSettingsTab does
   - Keep `self.logger = logger` for consistency with BaseSettingsTab pattern

2. **Consider using Component's `set_model()`**:
   - Currently both base tabs set `self.model` directly in `__init__`
   - Could use `set_model()` for automatic signal tracking
   - Low priority - current approach works fine

3. **Update CLAUDE.md**:
   - Remove the TODO section about CleanupMixin & Component Hierarchy
   - Document the new consistent hierarchy

---

## Phase 4: Testing

### Manual Testing:
1. Launch application
2. Test each torrent detail tab:
   - Details, Files, Status, Trackers, Options, Log, Monitoring
   - Incoming Connections, Outgoing Connections
3. Verify tabs update correctly when selecting torrents
4. Verify cleanup works (no memory leaks, no warnings in logs)

### Automated Testing:
1. Run existing unit tests: `pytest tests/unit/`
2. Check for any test failures related to component inheritance

---

## Files to Modify

| File | Change |
|------|--------|
| `d_fake_seeder/components/component/torrent_details/base_tab.py` | Extend Component instead of CleanupMixin |
| `d_fake_seeder/components/component/torrent_details/incoming_connections_tab.py` | Extend BaseTorrentTab instead of Component |
| `d_fake_seeder/components/component/torrent_details/outgoing_connections_tab.py` | Extend BaseTorrentTab instead of Component |
| `CLAUDE.md` | Update/remove TODO section |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Breaking existing functionality | Incremental changes, test after each phase |
| Signal handling differences | Keep existing signal patterns, just change inheritance |
| Abstract method conflicts | Implement Component's methods with pass-through defaults |

---

## Estimated Effort

- Phase 1 (BaseTorrentTab): ~30 minutes
- Phase 2 (Connection Tabs): ~30 minutes each = 1 hour
- Phase 3 (Cleanup): ~15 minutes
- Phase 4 (Testing): ~30 minutes

**Total: ~2.5 hours**

---

## Success Criteria

1. ✓ All torrent detail tabs extend `BaseTorrentTab`
2. ✓ `BaseTorrentTab` extends `Component`
3. ✓ No runtime errors or warnings
4. ✓ All tabs function correctly (selection, updates, cleanup)
5. ✓ Unit tests pass
6. ✓ CLAUDE.md updated to reflect new hierarchy

