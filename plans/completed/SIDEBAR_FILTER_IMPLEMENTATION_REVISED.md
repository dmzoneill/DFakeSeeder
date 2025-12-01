# Sidebar Filter Implementation Plan (REVISED)

## What We Already Have ✅

### Current Layout
```
main_paned (vertical - top/bottom)
└── paned (horizontal - left/right)
    ├── LEFT: states_columnview (Trackers)
    │   └── Shows: Tracker name | Count
    └── RIGHT: columnview1 (Torrents list)
```

### Existing Components
- ✅ **`states.py`** - Already displays tracker list with counts!
- ✅ **`states_columnview`** - GTK4 ColumnView showing trackers
- ✅ **`Model.get_trackers_liststore()`** - Already provides tracker data
- ✅ **Paned layout** - Sidebar is already on the left!
- ✅ **Filtering infrastructure** - Model has `filtered_torrent_list_attributes`

## Current Functionality

### What `states.py` Does NOW:
```python
def update_view(self, model, torrent, attribute):
    selection_model = Gtk.SingleSelection.new(model.get_trackers_liststore())
    self.states_columnview.set_model(selection_model)
```

**Displays**: Tracker Name | Count
**Source**: `model.get_trackers_liststore()`

### What It DOESN'T Do Yet:
❌ Filter torrents when you click a tracker
❌ Show torrent states (All, Seeding, Downloading, etc.)
❌ Show "All" option
❌ Show error/warning icons for problematic trackers
❌ Collapsible sections (States vs Trackers)
❌ Update torrent list based on selection

## Revised Implementation Plan

### Phase 1: Add Click Filtering (HIGHEST PRIORITY)
**Goal**: Make clicking a tracker filter the torrent list

#### 1.1 Add Selection Handler to states.py
```python
class States(Component):
    def __init__(self, builder, model):
        # ... existing code ...

        # Add selection changed handler
        selection = self.states_columnview.get_model()  # Gets SingleSelection
        self.track_signal(
            selection,
            selection.connect("selection-changed", self.on_tracker_selected)
        )

    def on_tracker_selected(self, selection, position, n_items):
        """Handle tracker selection and filter torrents."""
        selected_item = selection.get_selected_item()
        if selected_item:
            tracker_name = selected_item.tracker
            # Tell model to filter by this tracker
            self.model.set_filter_criteria('tracker', tracker_name)
```

#### 1.2 Enhance Model Filtering
**File**: `d_fake_seeder/model.py`

**Add**:
```python
class Model:
    def __init__(self):
        # ... existing ...
        self.active_filter_tracker = None  # NEW

    def set_filter_criteria(self, filter_type, value):
        """Set filter criteria (tracker, state, etc.)"""
        if filter_type == 'tracker':
            self.active_filter_tracker = value
            self._update_filtered_list()

    def _matches_filters(self, torrent_attributes):
        """Check if torrent matches active filters."""
        torrent = self._find_torrent_by_hash(torrent_attributes.info_hash)

        # Tracker filter
        if self.active_filter_tracker and self.active_filter_tracker != 'All':
            tracker_match = False
            for tracker in torrent.trackers:
                domain = self._get_tracker_domain(tracker.url)
                if domain == self.active_filter_tracker:
                    tracker_match = True
                    break
            if not tracker_match:
                return False

        # Search filter (existing logic)
        if self.search_filter:
            # ... existing search logic ...

        return True
```

**Estimated Time**: 2-3 hours

---

### Phase 2: Add State Filters
**Goal**: Add "All", "Seeding", "Downloading" above trackers

#### 2.1 Option A: Add States Above Trackers (Simpler)
Keep current ColumnView but add state items at top:

**Modify** `model.get_trackers_liststore()`:
```python
def get_trackers_liststore(self):
    """Get tracker list with state filters at top."""
    list_store = Gio.ListStore.new(TorrentState)

    # Add state filters first
    list_store.append(TorrentState("━━━ States ━━━", 0))  # Separator
    list_store.append(TorrentState("All", len(self.torrent_list)))
    list_store.append(TorrentState("Seeding", self._count_by_state('seeding')))
    list_store.append(TorrentState("Downloading", self._count_by_state('downloading')))
    list_store.append(TorrentState("━━━ Trackers ━━━", 0))  # Separator

    # Add trackers (existing logic)
    for fqdn, count in sorted_trackers:
        list_store.append(TorrentState(fqdn, count))

    return list_store
```

#### 2.2 Option B: Convert to ListBox with Expanders (More Complex)
Replace ColumnView with ListBox to support Gtk.Expander:

**Create**: New `sidebar.xml`:
```xml
<object class="GtkBox" id="sidebar_box">
  <property name="orientation">vertical</property>

  <child>
    <object class="GtkExpander">
      <property name="label">States</property>
      <property name="expanded">true</property>
      <child>
        <object class="GtkListBox" id="states_listbox">
          <!-- State items go here -->
        </object>
      </child>
    </object>
  </child>

  <child>
    <object class="GtkExpander">
      <property name="label">Trackers</property>
      <property name="expanded">true</property>
      <child>
        <object class="GtkListBox" id="trackers_listbox">
          <!-- Tracker items go here -->
        </object>
      </child>
    </object>
  </child>
</object>
```

**Estimated Time**: Option A (2 hours), Option B (5-6 hours)

---

### Phase 3: Visual Enhancements
**Goal**: Add icons, styling, better visual feedback

#### 3.1 Add Icons
- State icons (seeding, downloading, paused)
- Warning icon for tracker errors
- Count badges

#### 3.2 CSS Styling
```css
/* Sidebar */
#sidebar_box {
    min-width: 200px;
    background: @theme_base_color;
}

/* Selected filter item */
.filter-item:selected {
    background: @theme_selected_bg_color;
    color: @theme_selected_fg_color;
}

/* Count badges */
.count-badge {
    margin-left: 8px;
    opacity: 0.7;
}
```

**Estimated Time**: 2-3 hours

---

## Recommended Approach

### SHORT TERM (Do This First)
**Phase 1 ONLY** - Add click-to-filter functionality to existing sidebar:
1. Add selection handler to `states.py`
2. Implement `model.set_filter_criteria()`
3. Test clicking tracker filters torrent list

**Result**: Working filter sidebar in 2-3 hours!

### MEDIUM TERM (Do This Next)
**Phase 2 Option A** - Add state filters to top of current list:
1. Modify `get_trackers_liststore()` to include states
2. Handle state vs tracker selection differently
3. Add visual separators

**Result**: States + Trackers in one list (like Deluge) in 2 hours!

### LONG TERM (Optional Polish)
**Phase 2 Option B + Phase 3** - Full collapsible sections with icons
**Result**: Polished, professional sidebar (6-8 hours)

---

## Comparison: Current vs Deluge

### Current DFakeSeeder:
```
[Trackers]
archlinux.org     3
fedoraproject...  1
ubuntu.com        1
```

### After Phase 1:
```
[Trackers] ← Clickable, filters work!
archlinux.org     3
fedoraproject...  1
ubuntu.com        1
```

### After Phase 2A:
```
━━━ States ━━━
All               5
Seeding           3
Downloading       2
━━━ Trackers ━━━
archlinux.org     3
fedoraproject...  1
ubuntu.com        1
```

### After Phase 2B (Full Deluge Style):
```
▼ States
  All             5
  Seeding         3
  Downloading     2
▼ Trackers
  All             5
  ⚠ Error         1
  archlinux.org   3
  fedoraproject   1
```

---

## Questions for You

1. **Do you want Phase 1 first** (just make clicking work)?
   - ✅ Quick win (2-3 hours)
   - ✅ Immediately useful
   - Limited visual changes

2. **Or jump straight to Phase 2A** (states + trackers in one list)?
   - More complete feature
   - Still relatively quick (4-5 hours)
   - Better matches Deluge

3. **Or go all-in with Phase 2B** (collapsible sections)?
   - Most polished result
   - Longer implementation (8-10 hours)
   - Closest to Deluge

---

## My Recommendation

**Start with Phase 1** ✅

Get filtering working with what we have NOW. Then we can decide if we want the prettier collapsible sections or if the simple list is good enough.

The beauty is: **We already have 80% of the UI built!** We just need to make it functional.

---

## Technical Notes

### Why Keep states.py Instead of Creating sidebar.py?

**Pros of Keeping states.py**:
- ✅ Already in UI, already wired up
- ✅ Less refactoring needed
- ✅ Model code already provides data
- ✅ Translation support already there
- ✅ Faster to implement

**Cons**:
- Name is misleading (shows trackers, not states)
- Harder to add collapsible sections without major rewrite

### Rename states.py?

**Option**: Rename `states.py` → `sidebar.py` for clarity
- Update all references
- More accurate naming
- But requires more changes

**Verdict**: Keep name for now, rename later if needed.

---

## Implementation Checklist - Phase 1

### Step 1: Add Selection Handling (30 min)
- [ ] Add `on_tracker_selected()` to `states.py`
- [ ] Connect to selection-changed signal
- [ ] Log selected tracker name

### Step 2: Model Filtering (1 hour)
- [ ] Add `active_filter_tracker` to Model
- [ ] Implement `set_filter_criteria()`
- [ ] Implement `_matches_filters()`
- [ ] Test filtering logic

### Step 3: Integration & Testing (1 hour)
- [ ] Wire up states → model → torrents update
- [ ] Test clicking different trackers
- [ ] Verify torrent list filters correctly
- [ ] Test with multiple torrents/trackers

### Step 4: Visual Feedback (30 min)
- [ ] Add selection highlight CSS
- [ ] Test selection visibility
- [ ] Add "All" tracker option

**Total**: 2.5-3 hours for working sidebar filter!

---

What would you like to do? Start with Phase 1?
