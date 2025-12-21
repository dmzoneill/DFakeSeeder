# Magic Numbers & Strings Audit

Scan the codebase for hardcoded magic numbers and strings that should be configurable settings, then update `default.json` and create settings UI as needed.

## What This Command Does

1. **Scans** for hardcoded values that should be configurable
2. **Reports** findings with suggested configuration keys
3. **Updates** `default.json` with new settings
4. **Creates/Updates** settings UI in the appropriate tab

## Step 1: Run the Audit

First, search for common magic number patterns:

```bash
# Timeouts and delays (seconds/milliseconds)
grep -rn --include="*.py" -E "(timeout|delay|interval|duration)\s*[=:]\s*[0-9]+" d_fake_seeder/ | grep -v "settings\." | grep -v "_get_" | head -40

# Size limits and thresholds
grep -rn --include="*.py" -E "(max_|min_|limit|size|count|threshold)\s*[=:]\s*[0-9]+" d_fake_seeder/ | grep -v "settings\." | head -40

# Port numbers
grep -rn --include="*.py" -E "port\s*[=:]\s*[0-9]+" d_fake_seeder/ | grep -v "settings\." | head -20

# Retry counts
grep -rn --include="*.py" -E "(retry|retries|attempts)\s*[=:]\s*[0-9]+" d_fake_seeder/ | grep -v "settings\." | head -20

# Buffer sizes
grep -rn --include="*.py" -E "(buffer|chunk|batch)\s*[=:]\s*[0-9]+" d_fake_seeder/ | grep -v "settings\." | head -20

# Hardcoded URLs
grep -rn --include="*.py" -E 'https?://[^"'\'']+' d_fake_seeder/ | grep -v "#" | head -20

# Sleep values
grep -rn --include="*.py" -E "sleep\([0-9.]+" d_fake_seeder/ | head -20

# GLib timeouts
grep -rn --include="*.py" -E "timeout_add(_seconds)?\([0-9]+" d_fake_seeder/ | grep -v "settings\." | head -20
```

## Step 2: Categorize Findings

Group findings by category for settings organization:

| Category | Examples | Settings Section |
|----------|----------|------------------|
| **Network** | timeouts, ports, retry counts | `connection_settings` or `network_settings` |
| **UI** | animation durations, delays | `ui_settings` |
| **Performance** | buffer sizes, batch counts | `performance_settings` |
| **Limits** | max connections, queue sizes | `limits_settings` |
| **Behavior** | intervals, thresholds | Varies by feature |

## Step 3: Update default.json

For each magic value that should be configurable, add to `d_fake_seeder/config/default.json`:

```json
{
  "section_name": {
    "setting_key": default_value,
    "another_setting": another_value
  }
}
```

### Naming Conventions

- Use `snake_case` for keys
- Be descriptive: `peer_handshake_timeout_seconds` not `timeout1`
- Include units in name: `_seconds`, `_ms`, `_bytes`, `_count`
- Group related settings under a common prefix

## Step 4: Update AppSettings (if needed)

If adding a new settings section, update `d_fake_seeder/domain/app_settings.py`:

```python
# Add property accessor for the new section
@property
def my_new_section(self) -> Dict[str, Any]:
    return self._settings.get("my_new_section", {})
```

## Step 5: Update Code to Use Settings

Replace hardcoded values with settings lookups:

```python
# Before (magic number):
timeout = 30

# After (configurable):
timeout = self.settings.get("connection_settings.peer_timeout_seconds", 30)
```

## Step 6: Add Settings UI (Optional)

For user-facing settings, add UI controls. Choose the appropriate tab:

| Setting Type | Tab |
|-------------|-----|
| Network/Connection | Connection Tab |
| BitTorrent protocol | BitTorrent Tab |
| UI behavior | General Tab |
| Performance | Advanced Tab |
| Notifications | Notifications Tab |

### Adding a Setting to XML

1. Edit the appropriate tab XML in `d_fake_seeder/components/ui/settings/`
2. Add a control (SpinButton for numbers, Switch for booleans, Entry for strings):

```xml
<!-- Number setting with SpinButton -->
<object class="GtkBox">
  <property name="orientation">horizontal</property>
  <property name="spacing">8</property>
  <child>
    <object class="GtkLabel">
      <property name="label" translatable="yes">My Setting:</property>
      <property name="halign">start</property>
    </object>
  </child>
  <child>
    <object class="GtkSpinButton" id="settings_my_setting">
      <property name="halign">end</property>
      <property name="adjustment">
        <object class="GtkAdjustment">
          <property name="lower">1</property>
          <property name="upper">100</property>
          <property name="step-increment">1</property>
          <property name="value">30</property>
        </object>
      </property>
      <property name="tooltip-text" translatable="yes">Description of the setting</property>
    </object>
  </child>
</object>
```

### Wiring Up in Python Tab

In the corresponding tab Python file:

```python
def _setup_my_setting(self) -> None:
    spin = self.builder.get_object("settings_my_setting")
    if spin:
        spin.set_value(self.settings.get("section.my_setting", 30))
        spin.connect("value-changed", self._on_my_setting_changed)

def _on_my_setting_changed(self, spin: Gtk.SpinButton) -> None:
    self.settings.set("section.my_setting", int(spin.get_value()))
```

## Common Patterns to Look For

### High Priority (Should Always Be Configurable)

```python
# Timeouts that affect user experience
socket.settimeout(30)  # → connection_settings.socket_timeout_seconds
time.sleep(5)  # → Check if this is a polling interval

# Limits that users might want to adjust
max_connections = 50  # → limits_settings.max_connections
max_retries = 3  # → connection_settings.max_retries

# Network ports
port = 6881  # → Already in settings usually
```

### Medium Priority (Consider Making Configurable)

```python
# Buffer sizes (power users might want to tune)
buffer_size = 16384  # → performance_settings.buffer_size_bytes

# Intervals and frequencies
poll_interval = 1.0  # → behavior_settings.poll_interval_seconds

# Thresholds
min_peers = 5  # → bittorrent_settings.min_peers
```

### Low Priority (Usually OK as Constants)

```python
# Protocol-defined values
PROTOCOL_VERSION = 1
HEADER_SIZE = 68

# Internal implementation details
_INTERNAL_BUFFER = 1024
```

## Example Workflow

1. **Find**: `grep -rn "timeout.*=" d_fake_seeder/domain/`
2. **Evaluate**: Is this user-facing? Would users benefit from changing it?
3. **Add to default.json**: `"peer_connection_timeout_seconds": 30`
4. **Update code**: `timeout = settings.get("...", 30)`
5. **Add UI** (if needed): SpinButton in Connection tab
6. **Test**: Verify default works, verify changing setting works

## Files Reference

| Purpose | Location |
|---------|----------|
| Default settings | `d_fake_seeder/config/default.json` |
| Settings class | `d_fake_seeder/domain/app_settings.py` |
| Settings tabs | `d_fake_seeder/components/component/settings/*.py` |
| Settings XML | `d_fake_seeder/components/ui/settings/*.xml` |
| Tab registry | `d_fake_seeder/domain/config/tabs.json` |

## Validation Checklist

After making changes:

- [ ] `make lint` passes
- [ ] App starts without errors
- [ ] Default value works correctly
- [ ] Setting can be changed in UI (if applicable)
- [ ] Setting persists after restart
- [ ] Setting actually affects the behavior

