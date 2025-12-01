# Sidebar Filter Implementation Plan

## Overview
Implement a Deluge-style sidebar filter panel that allows users to filter torrents by state, tracker, and other criteria. This enhances usability by providing quick access to torrent subsets.

## Current State Analysis

### Existing Components
From the codebase analysis:
- ✅ **`states.py`** - Already displays torrent states in the UI
- ✅ **`Model.get_trackers_liststore()`** - Already aggregates tracker statistics
- ✅ **GTK4 Paned Layout** - Main window uses `Gtk.Paned` for resizable panels
- ✅ **Search Filtering** - Model already has `search_filter` and `filtered_torrent_list_attributes`

### What Deluge Provides
Looking at the screenshot:
1. **States Section** (collapsible)
   - All (with count)
   - Active (with count)
   - Seeding (with count)
   - Downloading (with count)
   - Paused (with count)
   - etc.

2. **Trackers Section** (collapsible)
   - All (with count)
   - Error (with warning icon)
   - Individual trackers grouped by domain (with counts)

3. **Owner Section** (collapsible) - for multi-user setups

## Implementation Plan

### Phase 1: UI Structure & Layout
**Goal**: Create the sidebar widget structure

#### 1.1 Create Sidebar Component
**File**: `d_fake_seeder/components/component/sidebar.py`

```python
class Sidebar(Component):
    """
    Sidebar filter panel for torrents.

    Provides filtering by:
    - State (All, Active, Seeding, Downloading, Paused, etc.)
    - Tracker (All, Error, grouped by domain)
    - Labels/Tags (future)
    """

    def __init__(self, builder, model):
        # Main scrolled window
        # Vertical box container
        # Filter sections (States, Trackers, etc.)
```

**Key Features**:
- Collapsible sections using `Gtk.Expander`
- Tree-like structure using `Gtk.ListBox`
- Badge/count display for each filter item
- Icon support (state icons, tracker favicons, warning icons)

#### 1.2 Update Main Window Layout
**File**: `d_fake_seeder/view.py`

**Current Layout**:
```
Window
└── Paned (horizontal)
    ├── Left: Torrents List
    └── Right: Details Notebook
```

**New Layout**:
```
Window
└── Paned (horizontal) - main_paned
    ├── Left: Paned (horizontal) - filter_paned
    │   ├── Left: Sidebar (200-300px)
    │   └── Right: Torrents List
    └── Right: Details Notebook
```

**Changes Needed**:
- Wrap existing torrents view in a new nested paned
- Add sidebar as left pane
- Make sidebar collapsible/hideable
- Save pane positions in settings

#### 1.3 Create UI XML Structure
**File**: `d_fake_seeder/components/ui/sidebar/sidebar.xml`

```xml
<object class="GtkBox" id="sidebar_box">
  <property name="orientation">vertical</property>
  <property name="width-request">200</property>

  <!-- States Section -->
  <child>
    <object class="GtkExpander" id="states_expander">
      <property name="label">States</property>
      <property name="expanded">true</property>
      <child>
        <object class="GtkListBox" id="states_listbox">
          <!-- Filter items will be added dynamically -->
        </object>
      </child>
    </object>
  </child>

  <!-- Trackers Section -->
  <child>
    <object class="GtkExpander" id="trackers_expander">
      <property name="label">Trackers</property>
      <property name="expanded">true</property>
      <child>
        <object class="GtkListBox" id="trackers_listbox">
          <!-- Filter items will be added dynamically -->
        </object>
      </child>
    </object>
  </child>
</object>
```

### Phase 2: Filter Logic Implementation

#### 2.1 Extend Model Filtering
**File**: `d_fake_seeder/model.py`

**Current**: Only supports text search filtering
**Needed**: Multi-criteria filtering

```python
class Model:
    def __init__(self):
        # Existing
        self.search_filter = ""

        # New filter criteria
        self.active_filters = {
            'state': None,      # None = All, or TorrentState value
            'tracker': None,    # None = All, or tracker domain
            'label': None,      # Future: custom labels
            'search': ''        # Text search
        }

    def set_filter_criteria(self, filter_type, value):
        """Set a filter criterion and update filtered list."""
        self.active_filters[filter_type] = value
        self._update_filtered_list()

    def clear_filter(self, filter_type):
        """Clear a specific filter."""
        self.active_filters[filter_type] = None
        self._update_filtered_list()

    def _matches_filters(self, torrent_attributes):
        """Check if torrent matches all active filter criteria."""
        torrent = self._find_torrent_by_hash(torrent_attributes.info_hash)

        # State filter
        if self.active_filters['state']:
            if torrent.state != self.active_filters['state']:
                return False

        # Tracker filter
        if self.active_filters['tracker']:
            tracker_match = False
            for tracker in torrent.trackers:
                if self._get_tracker_domain(tracker.url) == self.active_filters['tracker']:
                    tracker_match = True
                    break
            if not tracker_match:
                return False

        # Search filter (existing logic)
        if self.active_filters['search']:
            # Fuzzy search logic
            ...

        return True
```

#### 2.2 State Filter Items
Define the standard torrent states:

```python
STATE_FILTERS = [
    ('all', 'All', ''),
    ('downloading', 'Downloading', 'folder-download-symbolic'),
    ('seeding', 'Seeding', 'folder-upload-symbolic'),
    ('active', 'Active', 'media-playback-start-symbolic'),
    ('paused', 'Paused', 'media-playback-pause-symbolic'),
    ('checking', 'Checking', 'system-search-symbolic'),
    ('error', 'Error', 'dialog-error-symbolic'),
    ('queued', 'Queued', 'view-list-symbolic'),
]
```

#### 2.3 Tracker Grouping Logic
**File**: `d_fake_seeder/model.py` (enhance existing method)

```python
def get_tracker_filters(self):
    """
    Get tracker filter items with counts.
    Returns: List of (domain, count, has_error) tuples
    """
    tracker_stats = {}

    for torrent in self.torrent_list:
        for tracker in torrent.trackers:
            domain = self._get_tracker_domain(tracker.url)
            if domain not in tracker_stats:
                tracker_stats[domain] = {'count': 0, 'has_error': False}

            tracker_stats[domain]['count'] += 1
            if tracker.has_error():
                tracker_stats[domain]['has_error'] = True

    return sorted(tracker_stats.items(), key=lambda x: (-x[1]['count'], x[0]))
```

### Phase 3: Sidebar Component Implementation

#### 3.1 Filter Item Widget
Create a custom widget for filter items with icon + label + count badge:

```python
class FilterItem(Gtk.Box):
    """Single filter item with icon, label, and count badge."""

    def __init__(self, filter_id, label, icon_name, count):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

        # Icon (state/tracker icon)
        self.icon = Gtk.Image.new_from_icon_name(icon_name)
        self.append(self.icon)

        # Label
        self.label = Gtk.Label(label=label)
        self.label.set_hexpand(True)
        self.label.set_xalign(0)
        self.append(self.label)

        # Count badge
        self.count_label = Gtk.Label(label=str(count))
        self.count_label.add_css_class("count-badge")
        self.append(self.count_label)

        # Store filter ID for event handling
        self.filter_id = filter_id
```

#### 3.2 Sidebar Class Structure

```python
class Sidebar(Component):
    def __init__(self, builder, model):
        super().__init__()
        self.model = model
        self.builder = builder

        # Create UI structure
        self._init_widgets()

        # Populate filter items
        self._populate_states()
        self._populate_trackers()

        # Connect signals
        self._connect_signals()

    def _init_widgets(self):
        """Create sidebar widget structure."""
        self.sidebar_box = self.builder.get_object("sidebar_box")
        self.states_listbox = self.builder.get_object("states_listbox")
        self.trackers_listbox = self.builder.get_object("trackers_listbox")

        # Selection mode
        self.states_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.trackers_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

    def _populate_states(self):
        """Populate state filter items."""
        for state_id, label, icon in STATE_FILTERS:
            count = self._get_state_count(state_id)
            item = FilterItem(state_id, label, icon, count)
            self.states_listbox.append(item)

    def _populate_trackers(self):
        """Populate tracker filter items."""
        # Clear existing
        self.trackers_listbox.remove_all()

        # Add "All" item
        all_count = len(self.model.torrent_list)
        all_item = FilterItem('all', 'All', '', all_count)
        self.trackers_listbox.append(all_item)

        # Add tracker items
        for domain, stats in self.model.get_tracker_filters():
            icon = 'dialog-warning-symbolic' if stats['has_error'] else ''
            item = FilterItem(domain, domain, icon, stats['count'])
            self.trackers_listbox.append(item)

    def _on_state_selected(self, listbox, row):
        """Handle state filter selection."""
        if row:
            filter_item = row.get_child()
            state = filter_item.filter_id

            # Apply filter
            if state == 'all':
                self.model.clear_filter('state')
            else:
                self.model.set_filter_criteria('state', state)

            # Clear tracker selection
            self.trackers_listbox.unselect_all()

    def _on_tracker_selected(self, listbox, row):
        """Handle tracker filter selection."""
        if row:
            filter_item = row.get_child()
            tracker = filter_item.filter_id

            # Apply filter
            if tracker == 'all':
                self.model.clear_filter('tracker')
            else:
                self.model.set_filter_criteria('tracker', tracker)

            # Clear state selection (or combine filters?)
            # Decision: Allow combining state + tracker filters

    def update_counts(self):
        """Update counts for all filter items."""
        # Called when torrents change
        self._update_state_counts()
        self._update_tracker_counts()

    def refresh_trackers(self):
        """Rebuild tracker list (when trackers change)."""
        self._populate_trackers()
```

### Phase 4: Visual Design & Styling

#### 4.1 CSS Styling
**File**: `d_fake_seeder/components/ui/css/styles.css`

```css
/* Sidebar */
#sidebar_box {
    background: @theme_base_color;
    border-right: 1px solid @borders;
}

/* Filter expanders */
.sidebar-expander {
    padding: 8px;
    font-weight: bold;
}

/* Filter list items */
.filter-item {
    padding: 4px 8px;
}

.filter-item:hover {
    background: alpha(@theme_selected_bg_color, 0.1);
}

.filter-item:selected {
    background: @theme_selected_bg_color;
    color: @theme_selected_fg_color;
}

/* Count badges */
.count-badge {
    min-width: 24px;
    padding: 2px 6px;
    margin-left: 8px;
    border-radius: 12px;
    background: alpha(@theme_fg_color, 0.1);
    font-size: 0.85em;
}

.filter-item:selected .count-badge {
    background: alpha(@theme_selected_fg_color, 0.2);
}

/* Warning/error trackers */
.tracker-error .count-badge {
    background: @warning_color;
    color: @theme_base_color;
}
```

#### 4.2 Icons
Use standard GTK symbolic icons:
- **All**: (no icon or `folder-symbolic`)
- **Downloading**: `folder-download-symbolic`
- **Seeding**: `folder-upload-symbolic`
- **Active**: `media-playback-start-symbolic`
- **Paused**: `media-playback-pause-symbolic`
- **Checking**: `system-search-symbolic`
- **Error**: `dialog-error-symbolic`
- **Tracker Error**: `dialog-warning-symbolic`

### Phase 5: Integration & Signals

#### 5.1 Connect Model Signals
```python
# In View.__init__():
self.sidebar = Sidebar(self.builder, self.model)

# In View.connect_signals():
self.model.connect("data-changed", self.sidebar.update_counts)
```

#### 5.2 Settings Persistence
**File**: `d_fake_seeder/config/default.json`

```json
{
  "ui_settings": {
    "sidebar_visible": true,
    "sidebar_width": 200,
    "states_expanded": true,
    "trackers_expanded": true,
    "remember_last_filter": true,
    "last_filter": {
      "state": null,
      "tracker": null
    }
  }
}
```

### Phase 6: Advanced Features (Future Enhancements)

#### 6.1 Custom Labels/Tags
Allow users to create custom categories:
- "Important"
- "Linux ISOs"
- "Work"
- etc.

#### 6.2 Right-Click Context Menu
On tracker items:
- "Set as default tracker"
- "Remove all torrents from this tracker"
- "Edit tracker URL"

#### 6.3 Drag & Drop
Drag torrents to tracker/label items to:
- Add tracker
- Change label

#### 6.4 Search Within Filters
Add search box at top of sidebar to filter the filter items themselves.

#### 6.5 Tracker Favicons
Download and display actual tracker favicons instead of generic icons.

#### 6.6 Multi-Select Filters
Allow Ctrl+Click to combine multiple filters (e.g., "Seeding" + "archlinux.org").

## Implementation Checklist

### Milestone 1: Basic Structure (2-3 hours)
- [ ] Create `sidebar.py` component file
- [ ] Create `sidebar.xml` UI definition
- [ ] Update main window layout in `view.py`
- [ ] Add sidebar to View initialization
- [ ] Basic CSS styling

### Milestone 2: States Filter (2-3 hours)
- [ ] Define state filter constants
- [ ] Implement state counting logic in Model
- [ ] Create FilterItem widget
- [ ] Populate states list
- [ ] Implement state filter selection handler
- [ ] Connect to model filtering

### Milestone 3: Trackers Filter (2-3 hours)
- [ ] Enhance `get_trackers_liststore()` for sidebar use
- [ ] Implement tracker domain extraction
- [ ] Populate trackers list
- [ ] Implement tracker filter selection handler
- [ ] Add error/warning icon support

### Milestone 4: Polish & Testing (2-3 hours)
- [ ] Add count badge updates on torrent changes
- [ ] Implement collapsible sections
- [ ] Add keyboard navigation support
- [ ] Persist sidebar state in settings
- [ ] Add translation support
- [ ] Test with various torrent states/trackers

### Milestone 5: Advanced Features (optional)
- [ ] Add "Labels" section
- [ ] Implement custom label creation
- [ ] Add context menus
- [ ] Add drag & drop support

## Technical Considerations

### 1. Performance
- **Concern**: Updating counts on every torrent change
- **Solution**: Debounce updates, batch count calculations

### 2. GTK4 Best Practices
- Use `Gtk.ListBox` for filter lists (better than TreeView for this use case)
- Use `Gtk.Expander` for collapsible sections
- Use symbolic icons for consistent theming

### 3. Multi-Language Support
- All filter labels must be translatable
- Tracker domains are not translated (keep as-is)

### 4. Accessibility
- Proper ARIA labels for screen readers
- Keyboard navigation (arrows to move, Enter to select)
- High contrast theme support

## Estimated Timeline
- **Phase 1-3**: 6-9 hours (core implementation)
- **Phase 4-5**: 4-6 hours (polish & integration)
- **Phase 6**: 8-12 hours (advanced features - optional)

**Total for basic implementation**: ~10-15 hours
**Total with advanced features**: ~18-27 hours

## References
- Deluge sidebar: Visual reference provided
- Transmission: Similar state filtering
- qBittorrent: Category + tag system
- GTK4 ListBox: https://docs.gtk.org/gtk4/class.ListBox.html
- GTK4 Expander: https://docs.gtk.org/gtk4/class.Expander.html

## Success Criteria
✅ User can filter torrents by state (All, Seeding, Downloading, etc.)
✅ User can filter torrents by tracker domain
✅ Filter counts update automatically when torrents change
✅ Sidebar is collapsible and width is adjustable
✅ Settings are persisted across sessions
✅ UI is responsive and doesn't impact performance
✅ Works with existing search filter (combines filters)

## Future Considerations
- Integration with web UI (if/when implemented)
- Export/import filter presets
- Smart filters (e.g., "Torrents with ratio > 2.0")
- Saved filter combinations
