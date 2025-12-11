# Logger Fixes - 2025-12-08

## Issues Fixed

This document details the bugs found and fixed during the logger recategorization process.

## Bug 1: Incorrect Method Calls in EnhancedLogger

**Location:** `d_fake_seeder/lib/logger.py`

**Problem:**
When implementing the EnhancedLogger class with TRACE level support, two methods were accidentally calling the wrong underlying logger methods:

1. Line 429: `debug()` method was calling `self._logger.trace()` instead of `self._logger.debug()`
2. Line 493: Global `debug()` convenience function was calling `logger.trace()` instead of `logger.debug()`

**Error:**
```python
AttributeError: 'Logger' object has no attribute 'trace'
```

**Root Cause:**
Copy-paste error when creating the new `trace()` method - the `debug()` method was incorrectly modified to call `.trace()`.

**Fix:**
```python
# BEFORE (incorrect)
def debug(self, message: str, class_name: Optional[str] = None, **kwargs):
    ...
    return self._logger.trace(message, **kwargs)  # Wrong!

# AFTER (correct)
def debug(self, message: str, class_name: Optional[str] = None, **kwargs):
    ...
    return self._logger.debug(message, **kwargs)  # Correct
```

## Bug 2: Fallback Loggers Missing trace() Method

**Locations:**
- `d_fake_seeder/domain/app_settings.py` (line 182)
- `d_fake_seeder/lib/util/language_config.py` (line 20)
- `d_fake_seeder/lib/metrics_collector.py` (line 26)

**Problem:**
Several modules use fallback code that creates raw Logger instances via `logging.getLogger(__name__)` when the EnhancedLogger cannot be imported (e.g., circular import scenarios). After the logger recategorization, these modules were calling `.trace()` on raw Logger objects that don't have that method.

**Error:**
```python
AttributeError: 'Logger' object has no attribute 'trace'
```

**Root Cause:**
The automatic recategorization converted many `logger.debug()` calls to `logger.trace()`, but the fallback loggers created with `logging.getLogger()` are standard Python Logger instances that only have the built-in log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL).

**Fix:**
Created a helper function to add the `trace()` method to any Logger instance:

```python
def add_trace_to_logger(logger_instance):
    """
    Add trace() method to a standard Logger instance.

    This is used to add TRACE level support to fallback loggers
    that are created when the EnhancedLogger is not available.
    """
    def trace(msg, *args, **kwargs):
        if logger_instance.isEnabledFor(TRACE_LEVEL):
            logger_instance._log(TRACE_LEVEL, msg, args, **kwargs)

    logger_instance.trace = trace
    return logger_instance
```

Updated all fallback logger creation code:

```python
# BEFORE (missing trace method)
import logging
logger = logging.getLogger(__name__)

# AFTER (with trace method)
import logging
from d_fake_seeder.lib.logger import add_trace_to_logger
logger = add_trace_to_logger(logging.getLogger(__name__))
```

### Files Updated:

1. **app_settings.py:**
   - Line 181: Added `add_trace_to_logger` import
   - Line 183: Wrapped logger creation with `add_trace_to_logger()`

2. **language_config.py:**
   - Line 19: Added `add_trace_to_logger` import
   - Line 21: Wrapped logger creation with `add_trace_to_logger()`

3. **metrics_collector.py:**
   - Line 24: Added `add_trace_to_logger` import
   - Line 26: Wrapped logger creation with `add_trace_to_logger()`

## Bug 3: Linter Errors - Unused Import

**Problem:**
Initial fix imported both `add_trace_to_logger` and `TRACE_LEVEL`, but only used `add_trace_to_logger`.

**Error:**
```
F401 'd_fake_seeder.lib.logger.TRACE_LEVEL' imported but unused
```

**Fix:**
Removed unused `TRACE_LEVEL` import from:
- `domain/app_settings.py`
- `lib/util/language_config.py`
- `lib/metrics_collector.py`

## Testing

All fixes were verified with:

1. **Direct import test:**
   ```bash
   python3 -c "from d_fake_seeder.lib.logger import logger; logger.trace('test')"
   ```

2. **AppSettings test:**
   ```bash
   python3 -c "from d_fake_seeder.domain.app_settings import AppSettings;
               settings = AppSettings.get_instance();
               settings.logger.trace('test')"
   ```

3. **Fallback logger tests:**
   - Verified `language_config.logger.trace()` works
   - Verified `metrics_collector.logger.trace()` works

4. **Linting:**
   ```bash
   make lint
   ```
   ✅ All checks passed

## Prevention

To prevent similar issues in the future:

1. **Type Checking:** Consider adding type hints to logger methods
2. **Unit Tests:** Add tests for custom log levels
3. **Code Review:** Pay special attention to copy-paste code
4. **Documentation:** Document the fallback logger pattern clearly

## Related Documentation

- See `docs/LOGGER_RECATEGORIZATION.md` for full details on the TRACE level implementation
- See `d_fake_seeder/lib/logger.py` for the complete logger implementation
