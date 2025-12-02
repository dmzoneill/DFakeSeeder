# DFakeSeeder Localization System Documentation

This document provides comprehensive documentation for the localization (i18n) system in DFakeSeeder, covering all aspects from translation tools to file formats and implementation details.

## Overview

DFakeSeeder uses a sophisticated localization system built on GNU gettext with custom tooling for managing translations across 15 languages. The system supports both Python source code translations and GTK XML UI translations with automatic string extraction, validation, and compilation.

## Architecture

### Core Components

1. **Translation Infrastructure** (`d_fake_seeder/lib/i18n.py`)
2. **Language Helper Classes** (`d_fake_seeder/lib/helpers/language_helpers.py`) - **NEW**
3. **Menu Helper Classes** (`d_fake_seeder/lib/helpers/menu_helpers.py`) - **NEW**
4. **Localization Utilities** (`d_fake_seeder/lib/util/localization.py`)
5. **Translation Tools** (`tools/`)
6. **Locale Data** (`d_fake_seeder/locale/`)
7. **Build System Integration** (`Makefile`)

## Supported Languages

The application supports 15 languages with full translation infrastructure:

| Code | Language | Native Name |
| ---- | -------- | ----------- |
| `en` | English | English |
| `es` | Spanish | Español |
| `fr` | French | Français |
| `de` | German | Deutsch |
| `it` | Italian | Italiano |
| `pt` | Portuguese | Português |
| `ru` | Russian | Русский |
| `zh` | Chinese | 中文 |
| `ja` | Japanese | 日本語 |
| `ko` | Korean | 한국어 |
| `ar` | Arabic | العربية |
| `hi` | Hindi | हिन्दी |
| `nl` | Dutch | Nederlands |
| `sv` | Swedish | Svenska |
| `pl` | Polish | Polski |

## Directory Structure

```text
d_fake_seeder/
├── lib/
│   ├── i18n.py                     # Main localization manager
│   ├── helpers/                    # NEW: Reusable language helper classes
│   │   ├── __init__.py            # Helper package exports
│   │   ├── language_helpers.py    # GTK translation, locale, UI refresh helpers
│   │   └── menu_helpers.py        # Translatable menu utilities
│   └── util/
│       └── localization.py         # Utility functions for formatting
├── locale/                         # Translation files directory
│   ├── dfakeseeder.pot            # Template file (generated)
│   ├── en/LC_MESSAGES/            # English translations
│   │   ├── dfakeseeder.po         # Translation source
│   │   └── dfakeseeder.mo         # Compiled binary (generated)
│   ├── zh/LC_MESSAGES/            # Chinese translations
│   │   ├── dfakeseeder.po         # Translation source
│   │   └── dfakeseeder.mo         # Compiled binary (generated)
│   └── [other languages...]
└── ui/                            # UI definition files
    ├── *.xml                      # XML files with translatable="yes" attributes
    └── generated/
        └── settings_generated.xml  # Compiled UI files

tools/                             # Translation management tools
├── extract_strings.py            # String extraction from Python/XML
└── compile_translations.py       # PO to MO compilation
```text
## Language Helper Classes

### Helper Classes Overview

The language helper classes provide reusable utilities to centralize language-related functionality that was previously scattered throughout the codebase. These classes eliminate code duplication and provide a consistent API for language operations.

### GTKTranslationHelper Class

Centralized helper for GTK translation domain setup and management.

```python
from lib.helpers.language_helpers import GTKTranslationHelper

# Set up translation domain for GTK Builder
GTKTranslationHelper.setup_builder_translation(builder)

# Set up environment variables for GTK localization
GTKTranslationHelper.setup_environment_for_language("zh")

# Apply text direction (RTL/LTR) to widgets
GTKTranslationHelper.apply_text_direction(window)
```text
#### GTKTranslationHelper Methods

- `setup_builder_translation(builder)` - Configure GTK Builder for translations
- `setup_environment_for_language(language_code)` - Set GTK environment variables
- `apply_text_direction(widget)` - Apply RTL/LTR text direction

### LocaleHelper Class

Centralized locale management with consistent mappings and fallback handling.

```python
from lib.helpers.language_helpers import LocaleHelper

# Set locale for a specific language and category
LocaleHelper.set_locale_for_language("zh", locale.LC_TIME)

# Set LC_MESSAGES locale
LocaleHelper.set_messages_locale("zh")

# Get locale string for a language
locale_str = LocaleHelper.get_locale_for_language("zh")  # "zh_CN.UTF-8"
```text
#### LocaleHelper Features

- **Consistent Mappings**: Centralized language-to-locale mapping
- **Fallback Handling**: Automatic fallback to C/POSIX locales
- **Error Resilience**: Graceful handling of missing locales
- **Multiple Categories**: Support for LC_TIME, LC_MESSAGES, etc.

### LanguageChangeManager Class

Centralized coordinator for language changes and UI refresh operations.

```python
from lib.helpers.language_helpers import get_language_change_manager

# Get global manager instance
manager = get_language_change_manager()

# Register components for refresh
manager.register_refreshable_component(my_component)
manager.register_gtk_widget(my_window)

# Change language and refresh all registered components
manager.change_language("zh")

# Manual refresh of all components
manager.refresh_all_ui_text()
```text
#### Key Features

- **Component Registration**: Manage components that need refresh
- **Coordinated Updates**: Single point for language change coordination
- **Error Handling**: Graceful handling of component refresh failures
- **Cleanup Support**: Proper unregistration of components

### UIRefreshable Interface

Abstract interface for components that support UI text refresh.

```python
from lib.helpers.language_helpers import UIRefreshable

class MyComponent(UIRefreshable):
    def refresh_ui_text(self) -> None:
        """Refresh UI text content after language change."""
        # Update component-specific UI text
        self.label.set_text(_("Updated Text"))
```text
### Menu Helper Classes

Specialized utilities for creating and managing translatable menus.

```python
from lib.helpers.menu_helpers import RefreshableMenu, TranslatableMenuHelper

# Create a refreshable menu
menu = RefreshableMenu([
    ("About", "win.about"),
    ("Quit", "win.quit")
])

# Refresh menu after language change
menu.refresh()

# Create standard app menu
standard_menu = TranslatableMenuHelper.create_standard_app_menu()
```text
#### RefreshableMenu Class

- **Automatic Translation**: Menu items automatically translated
- **Dynamic Refresh**: Refresh menu content on language change
- **Item Management**: Add/remove items dynamically

#### TranslatableMenuHelper Class

- **Menu Creation**: Create menus with translatable items
- **Menu Updates**: Update existing menus with new translations
- **Standard Patterns**: Pre-defined standard menu patterns

### Convenience Functions

```python
from lib.helpers.language_helpers import (
    setup_component_for_i18n,
    cleanup_component_i18n
)

# Set up component for internationalization
setup_component_for_i18n(my_component, builder)

# Clean up component i18n registration
cleanup_component_i18n(my_component)
```text
## Translation Infrastructure

### LocalizationManager Class

The core of the localization system is the `LocalizationManager` class in `d_fake_seeder/lib/i18n.py`:

```python
class LocalizationManager:
    """Manages application localization and translations"""

    def __init__(self):
        self._current_language = None
        self._translation = None
        self._fallback_translation = None
        self._supported_languages = { ... }
        self._locale_dir = self._app_root / "locale"
```text
#### LocalizationManager Methods

- `detect_system_language()` - Auto-detects system language
- `load_language(language_code)` - Loads specific language translations
- `set_language_from_settings(app_settings)` - Sets language from application settings
- `_(message)` - Translates a message
- `ngettext(singular, plural, n)` - Plural-aware translation

#### GTK Integration

The system integrates with GTK's translation domain system:

```python
# Bind textdomain for GTK integration
gettext.bindtextdomain("dfakeseeder", str(self._locale_dir))
gettext.textdomain("dfakeseeder")

# Set environment variables for GTK localization
os.environ["TEXTDOMAINDIR"] = str(self._locale_dir)
os.environ["TEXTDOMAIN"] = "dfakeseeder"
os.environ["LANGUAGE"] = language_code
```text
### Global Functions

The module provides convenient global functions:

```python
from lib.i18n import _, ngettext, get_supported_languages, set_language

# Basic translation
translated_text = _("Hello, World!")

# Plural handling
message = ngettext("1 file", "%d files", count) % count

# Language management
supported = get_supported_languages()  # Returns dict of lang codes -> names
success = set_language("zh")           # Switch to Chinese
```text
## Localization Utilities

### Culture-Specific Formatting

The `d_fake_seeder/lib/util/localization.py` module provides utilities for culture-specific formatting:

#### Timestamp Formatting

```python
from lib.util.localization import format_timestamp

# Different format types
full_format = format_timestamp(timestamp, "full")    # Full date and time
date_only = format_timestamp(timestamp, "date")     # Date only
time_only = format_timestamp(timestamp, "time")     # Time only
short_format = format_timestamp(timestamp, "short") # Short format
```text
#### File Size Formatting

```python
from lib.util.localization import format_size

# Locale-aware size formatting
size_text = format_size(1024*1024, decimal_places=1)  # "1.0 MB" or "1,0 MB"
```text
#### Number Formatting

```python
from lib.util.localization import format_number

# European locales use comma as decimal separator
number_text = format_number(1234.56)  # "1,234.56" or "1 234,56"
```text
#### Text Direction

```python
from lib.util.localization import is_rtl_language, get_text_direction

# RTL language detection (Arabic, Hebrew, etc.)
is_rtl = is_rtl_language()       # True for ar, he, fa, ur
direction = get_text_direction() # "rtl" or "ltr"
```text
## Translation Tools

### String Extraction Tool (`tools/extract_strings.py`)

Comprehensive tool for extracting translatable strings from both Python and XML sources:

#### Extraction Tool Features

- **Python String Extraction**: Uses `xgettext` to extract `_()` and `ngettext()` calls
- **XML String Extraction**: Custom parser for `translatable="yes"` attributes
- **POT File Generation**: Creates/updates template files
- **PO File Management**: Creates/updates translation files for all supported languages
- **MO Compilation**: Compiles binary translation files

#### Extraction Tool Usage

```bash
# Extract all strings and update translations
python tools/extract_strings.py

# The tool automatically
# 1. Finds all Python files in d_fake_seeder/
# 2. Finds all XML files in d_fake_seeder/ui/
# 3. Extracts translatable strings
# 4. Creates/updates dfakeseeder.pot template
# 5. Updates all language PO files
# 6. Compiles MO files
```text
#### XML String Extraction

The tool uses regex patterns to find translatable XML strings:

```python
# Pattern to match translatable properties
pattern = r'<property\s+name="(?:label|tooltip-text)"\s+translatable="yes">' \
          r"([^<]+)</property>"
```text
#### String Processing

- HTML entity decoding (`&lt;` → `<`, `&gt;` → `>`, `&amp;` → `&`)
- Duplicate removal
- Sorted output for consistency

### Compilation Tool (`tools/compile_translations.py`)

Dedicated tool for compiling PO files to MO format:

#### Compilation Tool Features

- **Batch Compilation**: Compiles all PO files in the locale directory
- **Error Reporting**: Detailed error messages for compilation failures
- **Template Updates**: Can update POT templates from source files

#### Compilation Tool Usage

```bash
# Compile all translation files
python tools/compile_translations.py

# Update POT template from source files
python tools/compile_translations.py --update-pot
```text
## File Formats

### POT Template Files (`.pot`)

Template files contain all extractable strings in a standardized format:

```po
# SOME DESCRIPTIVE TITLE.
# Copyright (C) 2024 DFakeSeeder Contributors
# This file is distributed under the same license as the DFakeSeeder package.

#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: DFakeSeeder 1.0.0\n"
"Report-Msgid-Bugs-To: <<https://github.com/username/dfakeseeder/issues\n">>
"POT-Creation-Date: 2025-09-18 09:30+0100\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"Language: \n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=CHARSET\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=INTEGER; plural=EXPRESSION;\n"

msgid "Hello, World!"
msgstr ""

msgid "Settings"
msgstr ""
```text
### PO Translation Files (`.po`)

Language-specific translation files with actual translations:

```po
# Chinese translation for DFakeSeeder
# Copyright (C) 2024 DFakeSeeder Contributors

msgid ""
msgstr ""
"Project-Id-Version: DFakeSeeder 1.0.0\n"
"Report-Msgid-Bugs-To: <<https://github.com/username/dfakeseeder/issues\n">>
"POT-Creation-Date: 2025-09-18 17:51+0100\n"
"PO-Revision-Date: 2024-09-18 18:30+0100\n"
"Last-Translator: Claude <noreply@anthropic.com>\n"
"Language-Team: Chinese <zh@li.org>\n"
"Language: zh\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=1; plural=0;\n"

msgid "Settings"
msgstr "设置"

msgid "Connection"
msgstr "连接"
```text
### MO Binary Files (`.mo`)

Compiled binary files generated from PO files for runtime use. These are created automatically by the compilation tools.

## XML Internationalization

### Translatable Attributes

GTK XML files use the `translatable="yes"` attribute to mark strings for translation:

```xml
<object class="GtkLabel">
    <property name="label" translatable="yes">Preferences</property>
</object>

<object class="GtkSwitch" id="settings_auto_start">
    <property name="tooltip-text" translatable="yes">Start DFakeSeeder automatically when the system boots</property>
</object>
```text
### Supported Properties

The extraction tool looks for these translatable properties:

- `label` - Text labels for widgets
- `tooltip-text` - Tooltip descriptions
- `title` - Window/dialog titles

### XML Processing

The system processes XML files through:

1. **String Extraction**: Custom regex-based parser finds translatable strings
2. **Template Generation**: Extracted strings added to POT files
3. **GTK Integration**: Translation domain binding allows GTK to find translations
4. **Runtime Translation**: GTK automatically translates marked strings

## Python Code Internationalization

### Basic Translation

```python
from lib.i18n import _

# Simple string translation
message = _("Hello, World!")
```text
### Plural Forms

```python
from lib.i18n import ngettext

# Plural-aware translation
count = 5
message = ngettext("1 file selected", "%d files selected", count) % count
```text
### Format String Translation

```python
from lib.i18n import _

# Translating format strings
user_name = "Alice"
message = _("Welcome, {}!").format(user_name)

# Or with % formatting
message = _("Welcome, %s!") % user_name
```text
### Context-Sensitive Translation

```python
from lib.i18n import _

# Comments for translators
def show_error():
    # TRANSLATORS: This error message appears when file loading fails
    error_msg = _("Failed to load file")
```text
## Build System Integration

### Makefile Targets

The `Makefile` provides comprehensive translation management:

#### Primary Build Targets

```bash
# Complete translation system build (all languages)
make build-translations

# Build specific language
make build-translations-lang LANG=zh

# Verify translation completeness
make verify-translations

# Quality assurance (89% completion threshold)
make translations-quality-gate

# Custom quality threshold
make translations-quality-threshold THRESHOLD=95.0
```text
#### Validation Targets

```bash
# Validate translation keys consistency
make validate-translation-keys

# Check for duplicate strings
make check-duplicate-strings

# Comprehensive validation (all checks)
make validate-translations-comprehensive
```text
#### Legacy Workflow

```bash
# Traditional gettext workflow
make extract-strings        # Extract strings to POT
make validate-translations  # Validate PO files
make compile-translations   # Compile to MO files
make translations          # Complete legacy workflow
```text
#### System-Level Targets

```bash
# Run without pipenv (system Python)
make build-translations-system
make verify-translations-system
make validate-translations-system
make compile-translations-system
```text
### Integration with UI Build

```bash
# UI build includes translation compilation
make ui-build  # Builds UI and translations together
```text
### Help and Documentation

```bash
# Detailed translation help
make translations-help

# Quick help with common commands
make help
```text
## Settings Integration

### Language Settings

The application integrates with the settings system for language management:

```python
# In AppSettings
self.language = "auto"  # Auto-detect or specific language code

# In LocalizationManager
def set_language_from_settings(self, app_settings) -> bool:
    configured_language = getattr(app_settings, "language", None)

    if configured_language and configured_language != "auto":
        target_language = configured_language
    else:
        target_language = self.detect_system_language()

    return self.load_language(target_language)
```text
### Language Dropdown

The settings dialog provides a language dropdown populated from supported languages:

```python
def update_language_dropdown(self):
    supported_languages = get_supported_languages()
    language_codes = list(supported_languages.keys())

    string_list = Gtk.StringList()
    for code in language_codes:
        display_name = f"{supported_languages[code]} ({code})"
        string_list.append(display_name)

    language_dropdown.set_model(string_list)
```text
### Dynamic Language Switching

The application supports runtime language switching:

```python
def on_language_changed(self, dropdown, param):
    # Get selected language
    language_codes = list(get_supported_languages().keys())
    selected = dropdown.get_selected()
    language_code = language_codes[selected]

    # Apply language change
    if set_language(language_code):
        # Update UI
        self.refresh_translations_lightweight()

        # Refresh main application UI
        if View.instance:
            View.instance.refresh_ui_for_language_change()
```text
## Translation Workflow

### Developer Workflow

1. **Write translatable code**:
   ```python
   from lib.i18n import _
   message = _("User-visible message")
   ```

2. **Mark XML strings**:
   ```xml
   <property name="label" translatable="yes">Button Text</property>
   ```

3. **Extract strings**:
   ```bash
   make build-translations
   ```

4. **Test translations**:
   ```bash
   # Test in specific language
   DFS_LANGUAGE=zh make run-debug
   ```

### Translator Workflow

1. **Edit PO files**: Modify `d_fake_seeder/locale/LANG/LC_MESSAGES/dfakeseeder.po`

2. **Add translations**:
   ```po
   msgid "Settings"
   msgstr "设置"  # Chinese translation
   ```

3. **Compile translations**:
   ```bash
   make compile-translations
   ```

4. **Test results**:
   ```bash
   # Test the translated application
   DFS_LANGUAGE=zh make run-debug
   ```

### Quality Assurance

1. **Check completeness**:
   ```bash
   make verify-translations
   ```

2. **Validate syntax**:
   ```bash
   make validate-translations
   ```

3. **Quality gates**:
   ```bash
   make translations-quality-gate  # 89% threshold
   ```

## Advanced Features

### Locale Environment Setup

The system properly configures locale environment for GTK:

```python
# Environment variables for GTK localization
os.environ["TEXTDOMAINDIR"] = str(self._locale_dir)
os.environ["TEXTDOMAIN"] = "dfakeseeder"
os.environ["LANGUAGE"] = language_code

# Locale setting for culture-specific formatting
locale.setlocale(locale.LC_MESSAGES, f"{language_code}.UTF-8")
```text
### Fallback Handling

Robust fallback mechanisms ensure the application works even with missing translations:

```python
def load_language(self, language_code: str) -> bool:
    try:
        translation = gettext.translation(
            "dfakeseeder",
            localedir=str(self._locale_dir),
            languages=[language_code],
            fallback=False,
        )
        self._translation = translation
        return True
    except FileNotFoundError:
        logger.warning(f"Translation files not found for language: {language_code}")
        # Fallback to English
        self._translation = self._fallback_translation
        return False
```text
### Translation Statistics

The system provides translation statistics for monitoring:

```python
def get_translation_stats(self) -> dict:
    stats = {
        "supported_languages": len(self._supported_languages),
        "current_language": self.get_current_language(),
        "locale_dir_exists": self._locale_dir.exists(),
        "available_translations": [],
    }

    for lang_code in self._supported_languages:
        mo_file = self._locale_dir / lang_code / "LC_MESSAGES" / "dfakeseeder.mo"
        if mo_file.exists():
            stats["available_translations"].append(lang_code)

    return stats
```text
## Troubleshooting

### Common Issues

1. **Missing gettext tools**:
   ```bash
   # Ubuntu/Debian
   sudo apt install gettext

   # Fedora/RHEL
   sudo dnf install gettext

   # macOS
   brew install gettext
   ```

2. **Missing translations not appearing**:
   - Check MO files exist: `ls d_fake_seeder/locale/*/LC_MESSAGES/*.mo`
   - Verify translation domain binding
   - Check environment variables

3. **XML strings not translating**:
   - Verify `translatable="yes"` attributes
   - Check string extraction: `python tools/extract_strings.py`
   - Ensure GTK translation domain is set

4. **Locale errors**:
   - Install language packs: `sudo apt install language-pack-zh`
   - Check available locales: `locale -a`
   - Use fallback locale handling

### Debug Information

Enable translation debugging:

```python
import logging
logging.getLogger('lib.i18n').setLevel(logging.DEBUG)
```text
Check translation statistics:

```python
from lib.i18n import get_localization_manager
stats = get_localization_manager().get_translation_stats()
print(stats)
```text
## Migration to Helper Classes

### Before and After Comparison

#### GTK Translation Domain Setup

**Before (scattered across multiple files):**
```python
# In multiple files (view.py, settings_dialog.py, etc.)
self.builder.set_translation_domain("dfakeseeder")
```text
**After (centralized helper):**
```python
from lib.helpers.language_helpers import GTKTranslationHelper

GTKTranslationHelper.setup_builder_translation(self.builder)
```text
#### Text Direction Handling

**Before (repeated logic):**
```python
# Repeated in multiple files
from lib.util.localization import get_text_direction

text_direction = get_text_direction()
if text_direction == "rtl":
    widget.set_default_direction(Gtk.TextDirection.RTL)
else:
    widget.set_default_direction(Gtk.TextDirection.LTR)
```text
**After (single helper call):**
```python
from lib.helpers.language_helpers import GTKTranslationHelper

GTKTranslationHelper.apply_text_direction(widget)
```text
#### Locale Setting

**Before (massive if/else chains):**
```python
# 20+ line if/else chain in util/localization.py
if current_lang == "es":
    locale.setlocale(locale.LC_TIME, "es_ES.UTF-8")
elif current_lang == "fr":
    locale.setlocale(locale.LC_TIME, "fr_FR.UTF-8")
# ... 15 more conditions
```text
**After (centralized mapping):**
```python
from lib.helpers.language_helpers import LocaleHelper

LocaleHelper.set_locale_for_language(current_lang, locale.LC_TIME)
```text
#### Menu Creation and Refresh

**Before (manual menu management):**
```python
# Manual menu creation and refresh
menu = Gio.Menu.new()
menu.append(_("Quit"), "win.quit")
menu.append(_("About"), "win.about")

# Language change refresh (scattered logic)
menu.remove_all()
menu.append(_("About"), "win.about")
menu.append(_("Quit"), "win.quit")
```text
**After (refreshable menu wrapper):**
```python
from lib.helpers.menu_helpers import RefreshableMenu

# Create once
self.main_menu = RefreshableMenu([
    ("Quit", "win.quit"),
    ("About", "win.about")
])

# Simple refresh
self.main_menu.refresh()
```text
### Benefits of the Helper Classes

1. **Code Deduplication**: Eliminated repeated translation setup code across multiple files
2. **Centralized Logic**: All language-related operations in dedicated helper classes
3. **Consistent API**: Uniform interface for language operations throughout the application
4. **Error Handling**: Centralized error handling and fallback mechanisms
5. **Maintainability**: Easier to modify language behavior in one place
6. **Testability**: Helper classes can be easily unit tested
7. **Extensibility**: Easy to add new language-related functionality

### Implementation Notes

- **Backward Compatibility**: Existing code continues to work during migration
- **Gradual Migration**: Components can be migrated to helpers incrementally
- **Memory Management**: Proper registration/unregistration prevents memory leaks
- **Performance**: Reduced overhead from repeated setup operations

## Best Practices

### Development Best Practices

1. **Use helper classes for new code**:
   ```python
   # Good - use helpers
   from lib.helpers.language_helpers import GTKTranslationHelper
   GTKTranslationHelper.setup_builder_translation(builder)

   # Avoid - direct setup
   builder.set_translation_domain("dfakeseeder")
   ```

2. **Always use translation functions**:
   ```python
   # Good
   message = _("Error occurred")

   # Bad
   message = "Error occurred"
   ```

2. **Provide context for translators**:
   ```python
   # TRANSLATORS: This appears in the status bar
   status = _("Ready")
   ```

3. **Handle plurals correctly**:
   ```python
   # Good
   message = ngettext("1 item", "%d items", count) % count

   # Bad
   message = f"{count} item{'s' if count != 1 else ''}"
   ```

4. **Keep UI and logic separate**:
   ```python
   # Good - translatable UI text
   button.set_label(_("Save"))

   # Good - non-translatable internal identifiers
   action_type = "save_action"
   ```

### Translation Best Practices

1. **Maintain consistent terminology**
2. **Consider UI space constraints**
3. **Test translations in context**
4. **Follow language-specific conventions**
5. **Use appropriate formality levels**

### For Build System

1. **Always compile after translation changes**
2. **Use quality gates in CI/CD**
3. **Automate string extraction**
4. **Monitor translation completeness**

This documentation provides complete coverage of DFakeSeeder's localization system, enabling effective translation management and international deployment.