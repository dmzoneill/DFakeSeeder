# Translation Audit & Update

Perform an exhaustive scan for untranslated strings, fix issues, and update the translation system.

## Full Workflow

Run these steps in order:

### Step 1: Run the Audit
```bash
make translate-audit
```

Or for JSON output:
```bash
python tools/translation_build_manager.py audit --json
```

### Step 2: Fix High-Severity Issues

For each **🔴 HIGH** severity issue found:

1. **Hardcoded Labels** - Change from:
   ```python
   label = Gtk.Label(label="Some Text")
   ```
   To:
   ```python
   label = Gtk.Label(label=self._("Some Text"))
   ```

2. **Hardcoded Buttons** - Change from:
   ```python
   button = Gtk.Button(label="Click Me")
   ```
   To:
   ```python
   button = Gtk.Button(label=self._("Click Me"))
   ```

3. **XML Missing translatable** - Change from:
   ```xml
   <property name="label">Settings</property>
   ```
   To:
   ```xml
   <property name="label" translatable="yes">Settings</property>
   ```

### Step 3: Re-extract Strings
After fixing issues, extract new translatable strings:
```bash
make translate-extract
```

### Step 4: Run Full Translation Workflow
Update all translation files with new strings:
```bash
make translate-workflow
```

### Step 5: Verify
Run the audit again to confirm issues are resolved:
```bash
make translate-audit
```

## One-Command Full Cycle (After Fixes)

After you've fixed the high-severity issues in the code, run:
```bash
make translate-full
```

This runs: `translate-extract` → `translate-workflow` → `translate-audit`

## Categories Checked

| Category | Severity | What It Finds |
|----------|----------|---------------|
| `hardcoded_label` | 🔴 High | `Gtk.Label(label="...")` without `self._()` |
| `button_label` | 🔴 High | `Gtk.Button(label="...")` without `self._()` |
| `xml_missing_translatable` | 🔴 High | XML properties missing `translatable="yes"` |
| `notification_message` | 🟡 Medium | `notify(...)` with hardcoded strings |
| `dialog_title` | 🟡 Medium | `set_title("...")` with hardcoded strings |
| `tooltip_text` | 🟡 Medium | `set_tooltip_text("...")` with hardcoded strings |
| `placeholder_text` | 🟡 Medium | `set_placeholder_text("...")` with hardcoded strings |
| `column_header` | 🟡 Medium | Column headers not in ColumnTranslations |
| `status_text` | 🟢 Low | Status dictionaries (with `--verbose`) |

## Translation System Architecture

### How Strings Get Extracted

1. **Python code**: The `translate-extract` command scans for:
   - `_("string")` patterns
   - `self._("string")` patterns  
   - `translate_func("string")` patterns

2. **XML files**: Scans for properties with `translatable="yes"`:
   - `<property name="label" translatable="yes">Text</property>`
   - `<property name="tooltip-text" translatable="yes">Text</property>`

3. **Column headers**: Defined in `d_fake_seeder/lib/util/column_translations.py`

### Translation File Locations

| File Type | Location |
|-----------|----------|
| POT template | `d_fake_seeder/components/locale/dfakeseeder.pot` |
| PO files | `d_fake_seeder/components/locale/{lang}/LC_MESSAGES/dfakeseeder.po` |
| JSON translations | `tools/translations/{lang}.json` |
| Column translations | `d_fake_seeder/lib/util/column_translations.py` |

## Fixing Common Issues

### For Notification Messages (Medium Severity)

Notifications require a helper pattern since they're often in non-component code:

```python
# In classes that have access to model:
def notify_translated(self, key: str, **kwargs) -> None:
    msg = self.model.get_translate_func()(key)
    if kwargs:
        msg = msg.format(**kwargs)
    View.instance.notify(msg)

# Usage:
self.notify_translated("Tracker updated for {name}", name=torrent.name)
```

### For Dialog Titles

```python
# Before:
dialog.set_title("Export Settings")

# After:
dialog.set_title(self._("Export Settings"))
```

### For Status Text in Dictionaries

Add status strings to `column_translations.py` or translate inline:

```python
# Before:
status_text = "Connected"

# After:
status_text = self._("Connected")
```

## Search Patterns (Manual Grep)

```bash
# Find all potential untranslated strings
grep -rn 'Gtk\.Label(label="[^"]*"' d_fake_seeder/
grep -rn 'Gtk\.Button(label="[^"]*"' d_fake_seeder/
grep -rn 'View\.instance\.notify(' d_fake_seeder/
grep -rn 'set_title("[^"]*"' d_fake_seeder/
grep -rn 'set_tooltip_text("[^"]*"' d_fake_seeder/

# Find XML without translatable
grep -rn '<property name="label">' d_fake_seeder/components/ui/ | grep -v 'translatable="yes"'
```

## CI Integration

The audit tool returns exit code 1 if high-severity issues exist:

```yaml
# In GitHub Actions
- name: Translation Audit
  run: |
    python tools/translation_build_manager.py audit
    if [ $? -ne 0 ]; then
      echo "::error::Untranslated strings found!"
      exit 1
    fi
```

## Files to Focus On

- `d_fake_seeder/components/component/` - UI components
- `d_fake_seeder/components/ui/` - XML UI definitions  
- `d_fake_seeder/view.py` - Main view
- `d_fake_seeder/domain/torrent/` - Torrent domain logic
- `d_fake_seeder/dfakeseeder_tray.py` - System tray
- `d_fake_seeder/lib/util/column_translations.py` - Column headers
