# Logger Recategorization - 2025-12-08

## Overview

Complete overhaul of logging levels across the DFakeSeeder codebase to provide better granularity and proper log level assignment based on message content and purpose.

## Changes Made

### 1. Added TRACE Log Level

**New Custom Log Level:**
- **TRACE (level 5)**: Ultra-verbose logging below DEBUG
- Used for: function entry/exit, loop iterations, internal state tracking
- Positioned below Python's standard DEBUG (level 10)

**Implementation:**
- Added `TRACE_LEVEL = 5` constant in `d_fake_seeder/lib/logger.py`
- Registered with Python logging: `logging.addLevelName(TRACE_LEVEL, "TRACE")`
- Added `trace()` method to EnhancedLogger class
- Integrated into Settings UI dropdown (`advanced.xml`)
- Updated all level mappings in `advanced_tab.py`

### 2. Log Level Hierarchy

```text
CRITICAL (50) - Fatal errors that prevent operation
ERROR    (40) - Errors that need attention but don't crash
WARNING  (30) - Unexpected but recoverable situations
INFO     (20) - Important state changes and milestones
DEBUG    (10) - Verbose diagnostic information
TRACE     (5) - Ultra-verbose detailed diagnostics
```

### 3. Recategorization Results

**Total statements analyzed: 2,695**

| Suggested Level | Count | Description |
|-----------------|-------|-------------|
| TRACE | 1,660 | Function entry/exit, setup completion, signal connections |
| DEBUG | 27 | Important state changes, control flow |
| INFO | 165 | Lifecycle events, successful operations |
| WARNING | 158 | Recoverable issues, missing optional features |
| ERROR | 683 | Failed operations, caught exceptions |
| CRITICAL | 1 | Unrecoverable fatal errors |

**Changes applied: 1,832 logger calls updated across 124 Python files**

### 4. Categorization Guidelines

#### TRACE (Ultra-verbose)
- Function entry/exit markers
- Loop iteration tracking
- Signal connection/disconnection
- Widget creation and initialization
- Setup/teardown operations
- Internal state changes
- Checkpoint debugging

**Examples:**
```python
logger.trace("===== SettingsDialog.__init__ START =====")
logger.trace("About to call _init_widgets")
logger.trace("Signal connected successfully")
logger.trace("Widget lookup completed")
```

#### DEBUG (Diagnostic)
- Important state transitions
- Control flow decisions
- Variable value tracking
- Filter/selection changes
- Configuration updates

**Examples:**
```python
logger.debug("State changed from idle to active")
logger.debug("Filter changed, updating results")
logger.debug("Setting upload_limit value to 1000")
```

#### INFO (Milestones)
- Application lifecycle events
- Successful operations
- User-initiated actions
- Configuration save/load
- Major state transitions

**Examples:**
```python
logger.info("Application started successfully")
logger.info("Settings saved")
logger.info("Language switched to Spanish")
logger.info("Torrent added: example.torrent")
```

#### WARNING (Recoverable Issues)
- Missing optional features
- Deprecated usage
- Performance concerns
- Unexpected but handled situations
- Configuration issues

**Examples:**
```python
logger.warning("Warning: Optional dependency not available")
logger.warning("Performance: Operation took longer than expected")
logger.warning("Unexpected value, using default")
```


#### ERROR (Failures)

- Failed operations
- Caught exceptions
- Invalid input/data
- Resource not found
- Connection failures

**Examples:**
```python
logger.error("Failed to load configuration file")
logger.error("Exception during peer connection", exc_info=True)
logger.error("Invalid torrent file format")
```

#### CRITICAL (Fatal)
- Unrecoverable errors
- Cannot start application
- Critical resource missing
- System failure

**Examples:**
```python
logger.critical("Cannot start: Required dependency missing")
logger.critical("Fatal error: Database corrupted")
```

## Benefits

1. **Better Debugging**: TRACE level provides ultra-detailed diagnostics without cluttering DEBUG logs
2. **Clearer Logs**: Each level has a clear purpose and consistent usage
3. **Flexible Filtering**: Users can choose exact verbosity level needed
4. **Performance**: TRACE can be disabled in production for better performance
5. **Consistency**: Automated recategorization ensures uniform log level usage

## Usage in Settings UI

The Advanced tab now includes 6 log levels in the dropdown:
- TRACE (most verbose)
- DEBUG
- INFO (default)
- WARNING
- ERROR
- CRITICAL (least verbose)

Users can select the minimum log level to record, providing fine-grained control over logging output.

## Technical Details

### Files Modified

**Core Infrastructure:**
- `d_fake_seeder/lib/logger.py` - Added TRACE level and EnhancedLogger methods
- `d_fake_seeder/components/ui/settings/advanced.xml` - Added TRACE to dropdown
- `d_fake_seeder/components/component/settings/advanced_tab.py` - Updated level mappings

**Recategorization:**
- 124 Python files updated
- 1,832 logger calls changed
- 863 logger calls already correctly categorized

### Automation Tools

Created analysis and application scripts:
- `/tmp/recategorize_logger_statements.py` - Analysis script for categorization
- `/tmp/apply_logger_recategorization.py` - Application script for changes

### Pattern-Based Categorization

The recategorization used pattern matching on message content:

**TRACE patterns:**
- `START.*=====`, `COMPLETE.*=====`
- `About to`, `completed`, `finished`
- `signal.*connected`, `widget.*created`
- `initialization`, `setup completed`

**DEBUG patterns:**
- `State changed`, `Filter.*changed`
- `Adding.*callback`, `Updating`
- `Setting.*to`, `Changed.*from.*to`

**INFO patterns:**
- `successfully`, `Language switched`
- `Settings.*saved`, `Torrent.*added`
- `Started`, `Stopped`, `Initialized`

**WARNING patterns:**
- `Warning:`, `Deprecated`
- `unexpected`, `Missing.*optional`
- `Performance`, `not recommended`

**ERROR patterns:**

- `Error`, `Exception`, `Failed`
- `Cannot`, `Unable to`, `Invalid`
- `not found`, `traceback`

**CRITICAL patterns:**
- `FATAL`, `Cannot start`
- `Critical`, `Unrecoverable`

## Terminal Detection Fix

Also fixed console output issue where systemd journal logging was outputting to terminal:

```python
# Detect if running in a terminal session
running_in_terminal = sys.stdout.isatty() or sys.stderr.isatty()

# Skip systemd logging when running in terminal
if settings["to_systemd"] and SYSTEMD_AVAILABLE and not running_in_terminal:
    journal_handler = JournalHandler(SYSLOG_IDENTIFIER="dfakeseeder")
    # ... setup handler ...
```

This ensures that when "Log to console" is OFF, no console output appears even when running interactively.

## Migration Notes

Existing code using `logger.debug()` extensively will now primarily use:
- `logger.trace()` for verbose diagnostic output (function entry/exit, iterations)
- `logger.debug()` for important state changes and control flow
- `logger.info()` for successful operations and lifecycle events

The old DEBUG calls have been automatically recategorized based on message content analysis.

## Future Improvements

1. Consider adding structured logging with additional context fields
2. Add log filtering by component/module
3. Implement log rotation and archiving for file logging
4. Add performance metrics logging at TRACE level
5. Consider adding log highlighting/coloring for console output
