"""
Enhanced Logger Module.

This module provides a comprehensive logging system with TRACE level support,
performance monitoring, colored console output, and optional systemd journal
integration. It wraps Python's standard logging with additional features
tailored for the DFakeSeeder application.
"""

# fmt: off
import functools
import logging
import os
import sys
import time
from typing import Any, Dict, Optional

# Try to import systemd journal support
try:
    from systemd.journal import JournalHandler

    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False

# Define custom log levels
# TRACE (5): Ultra-verbose - function entry/exit, every iteration, internal state
# DEBUG (10): Verbose diagnostic - important state changes, control flow
# Python's default DEBUG is 10, so we add TRACE below it
TRACE_LEVEL = 5
logging.addLevelName(TRACE_LEVEL, "TRACE")


def add_trace_to_logger(logger_instance: Any) -> None:
    """
    Add trace() method to a standard Logger instance.

    This is used to add TRACE level support to fallback loggers
    that are created when the EnhancedLogger is not available.
    """
    def trace(msg: Any, *args: Any, **kwargs: Any) -> Any:
        if logger_instance.isEnabledFor(TRACE_LEVEL):
            logger_instance._log(TRACE_LEVEL, msg, args, **kwargs)  # pylint: disable=protected-access

    logger_instance.trace = trace
    return logger_instance  # type: ignore[no-any-return]


# fmt: on


class ClassNameFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """Logging filter that extracts and adds class name to log records."""

    def filter(self, record: Any) -> Any:
        if hasattr(record, "class_name") and record.class_name:
            # Use provided class_name
            pass
        else:
            # Try to extract class name from the call stack
            class_name = self._extract_class_from_stack(record)
            if class_name:
                record.class_name = class_name
            else:
                # Fallback: extract a cleaner name from the module path
                # e.g., "d_fake_seeder.lib.logger" -> "Logger"
                name_parts = record.name.split(".")
                last_part = name_parts[-1] if name_parts else record.name
                record.class_name = last_part.replace("_", " ").title().replace(" ", "")
        return True

    def _extract_class_from_stack(self, record: Any) -> Optional[str]:
        """Try to extract the class name from the call stack."""
        import inspect

        try:
            # Walk up the stack to find the calling class
            # Skip frames that are part of the logging infrastructure
            for frame_info in inspect.stack():
                # Skip logging-related frames
                if "logging" in frame_info.filename or "logger" in frame_info.filename:
                    continue

                # Check if 'self' is in the local variables
                local_vars = frame_info.frame.f_locals
                if "self" in local_vars:
                    obj = local_vars["self"]
                    return str(obj.__class__.__name__)
                if "cls" in local_vars:
                    cls = local_vars["cls"]
                    return str(cls.__name__) if hasattr(cls, "__name__") else None

            return None
        except (AttributeError, KeyError, TypeError):
            return None


class TimingFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """Filter that adds precise timing information to log records."""

    def filter(self, record: Any) -> Any:
        record.precise_time = time.time()
        record.timestamp_ms = f"{record.precise_time:.3f}"
        return True


class DuplicateFilter(logging.Filter):  # pylint: disable=too-few-public-methods
    """
    Filter that suppresses duplicate log messages within a time window.

    Combines time-based rate limiting with count-based suppression:
    - Suppresses duplicate messages within a configurable time window
    - Counts how many times a message was suppressed
    - Logs summary when suppression window expires
    - Optionally flushes suppressed counts periodically
    """

    def __init__(self, time_window: Any = 5.0, flush_interval: Any = 30.0) -> None:
        """
        Initialize the duplicate filter.

        Args:
            time_window: Seconds within which to suppress duplicate messages
            flush_interval: Seconds between periodic flushes of suppressed counts
        """
        super().__init__()
        self.time_window = time_window
        self.flush_interval = flush_interval
        self.last_messages: Dict[str, Any] = {}  # message_key -> (count, first_time, last_time, record)
        self.last_flush = time.time()

    def _get_message_key(self, record: Any) -> Any:
        """Create a unique key for this log message."""
        # Use levelname, module, line number, and message content as key
        # This allows same message from different locations to be logged separately
        return (record.levelname, record.name, record.lineno, record.getMessage())

    def _should_flush(self) -> Any:
        """Check if it's time to flush suppressed message counts."""
        current_time = time.time()
        if current_time - self.last_flush >= self.flush_interval:
            self.last_flush = current_time
            return True
        return False

    def _flush_suppressed_counts(self) -> Any:
        """Log summary of all suppressed messages."""
        current_time = time.time()
        to_remove = []

        for message_key, (
            count,
            first_time,
            last_time,
            saved_record,
        ) in self.last_messages.items():
            if count > 1:
                # Create a summary record
                duration = current_time - first_time
                saved_record.msg = (
                    f"{saved_record.getMessage()} "
                    f"(repeated {count} times over {duration:.1f}s, last seen {current_time - last_time:.1f}s ago)"
                )
                # Log the summary (bypass this filter by creating new record)
                saved_record.levelname = "INFO"

            # Mark old entries for removal
            if current_time - last_time > self.time_window * 2:
                to_remove.append(message_key)

        # Clean up old entries
        for key in to_remove:
            del self.last_messages[key]

    def filter(self, record: Any) -> Any:
        """
        Filter duplicate messages.

        Returns:
            True if message should be logged, False if suppressed
        """
        # Periodic flush check
        if self._should_flush():
            self._flush_suppressed_counts()

        message_key = self._get_message_key(record)
        current_time = time.time()

        if message_key in self.last_messages:
            count, first_time, last_time, _ = self.last_messages[message_key]

            # Check if still within suppression window
            if current_time - last_time < self.time_window:
                # Update count and suppress this message
                self.last_messages[message_key] = (
                    count + 1,
                    first_time,
                    current_time,
                    record,
                )
                return False
            # Time window expired, log summary of suppressed messages
            if count > 1:
                duration = last_time - first_time
                record.msg = f"{record.getMessage()} " f"(previous message repeated {count} times over {duration:.1f}s)"

            # Reset counter for this message
            self.last_messages[message_key] = (
                1,
                current_time,
                current_time,
                record,
            )
            return True

        # First occurrence of this message
        self.last_messages[message_key] = (1, current_time, current_time, record)
        return True


class PerformanceLogger:
    """Enhanced logger with performance tracking and timing capabilities."""

    def __init__(self, logger_instance: Any) -> None:
        self._logger = logger_instance
        self._timers: Dict[str, float] = {}
        self._operation_stack: list = []

    def timing_info(
        self, message: str, class_name: Optional[str] = None, operation_time_ms: Optional[float] = None
    ) -> Any:  # noqa: E501
        """Log with timing information similar to the old print statements."""
        extra = {}
        if class_name:
            extra["class_name"] = class_name

        if operation_time_ms is not None:
            message = f"{message} (took {operation_time_ms:.1f}ms)"

        self._logger.info(message, extra=extra)

    def timing_debug(
        self, message: str, class_name: Optional[str] = None, operation_time_ms: Optional[float] = None
    ) -> Any:  # noqa: E501
        """Debug level timing information."""
        extra = {}
        if class_name:
            extra["class_name"] = class_name

        if operation_time_ms is not None:
            message = f"{message} (took {operation_time_ms:.1f}ms)"

        self._logger.trace(message, extra=extra)

    def start_timer(self, operation_name: str) -> float:
        """Start a named timer and return the start time."""
        start_time = time.time()
        self._timers[operation_name] = start_time
        return start_time

    def end_timer(
        self, operation_name: str, message: Optional[str] = None, class_name: Optional[str] = None, level: str = "info"
    ) -> float:  # noqa: E501
        """End a named timer and log the duration."""
        if operation_name not in self._timers:
            self._logger.info(f"Timer '{operation_name}' was not started")
            return 0.0

        start_time = self._timers.pop(operation_name)
        duration_ms = (time.time() - start_time) * 1000

        if message is None:
            message = f"{operation_name} completed"

        extra = {}
        if class_name:
            extra["class_name"] = class_name

        log_method = getattr(self._logger, level.lower(), self._logger.info)
        log_method(f"{message} (took {duration_ms:.1f}ms)", extra=extra)

        return duration_ms

    def operation_context(self, operation_name: str, class_name: Optional[str] = None) -> Any:
        """Context manager for timing operations."""
        return OperationTimer(self, operation_name, class_name)

    def performance_info(self, message: str, class_name: Optional[str] = None, **metrics: Any) -> Any:
        """Log performance information with custom metrics."""
        extra = {"class_name": class_name} if class_name else {}
        extra.update(metrics)

        metric_str = " ".join([f"{k}={v}" for k, v in metrics.items()])
        full_message = f"{message} [{metric_str}]" if metric_str else message

        self._logger.info(full_message, extra=extra)


class OperationTimer:
    """Context manager for timing operations."""

    def __init__(self, perf_logger: PerformanceLogger, operation_name: str, class_name: Optional[str] = None) -> None:
        self.perf_logger = perf_logger
        self.operation_name = operation_name
        self.class_name = class_name
        self.start_time = None

    def __enter__(self) -> Any:
        self.start_time = self.perf_logger.start_timer(self.operation_name)  # type: ignore[assignment]
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.perf_logger.end_timer(self.operation_name, class_name=self.class_name, level="debug")


def timing_decorator(operation_name: Optional[str] = None, level: str = "debug") -> Any:
    """Decorator to automatically time function execution."""

    def decorator(func: Any) -> Any:
        @functools.wraps(func)
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:  # type: ignore[no-untyped-def]
            op_name = operation_name or func.__name__
            class_name = self.__class__.__name__ if hasattr(self, "__class__") else None

            with logger.performance.operation_context(op_name, class_name):
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


def _get_default_log_path() -> str:
    """Return the config dir for log file path without importing xdg_paths (avoids circular imports)."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "dfakeseeder")


def get_logger_settings() -> Any:
    """Get logger settings from AppSettings if available, otherwise use defaults"""
    try:
        from domain.app_settings import AppSettings

        app_settings = AppSettings.get_instance()
        # Each output has its own independent level - no main level
        to_console_val = app_settings.get("logging.log_to_console", True)
        return {
            "console_level": app_settings.get("logging.console_level", "INFO"),
            "systemd_level": app_settings.get("logging.systemd_level", "ERROR"),
            "file_level": app_settings.get("logging.file_level", "DEBUG"),
            "filename": (
                app_settings.get("logging.filename", "") or os.path.join(_get_default_log_path(), "dfakeseeder.log")
            ),
            "format": app_settings.get(
                "logging.format",
                "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s",
            ),
            "to_file": app_settings.get("logging.log_to_file", False),
            "to_systemd": app_settings.get("logging.log_to_systemd", True),
            "to_console": to_console_val,
            "suppress_duplicates": app_settings.get("logging.suppress_duplicates", True),
            "duplicate_time_window": app_settings.get("logging.duplicate_time_window", 5.0),
            "duplicate_flush_interval": app_settings.get("logging.duplicate_flush_interval", 30.0),
        }
    except (ImportError, Exception):  # pylint: disable=broad-exception-caught
        # Fallback to hardcoded defaults if AppSettings not available
        # This should only happen during early startup or testing
        # IMPORTANT: Console is OFF by default - only enable when user settings confirm it
        # This prevents console output before user settings are loaded
        default_format = "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s"
        return {
            "console_level": "INFO",
            "systemd_level": "ERROR",
            "file_level": "DEBUG",
            "filename": os.path.join(_get_default_log_path(), "dfakeseeder.log"),
            "format": default_format,
            "to_file": False,
            "to_systemd": True,
            "to_console": False,  # OFF by default - wait for user settings
            "suppress_duplicates": True,
            "duplicate_time_window": 5.0,
            "duplicate_flush_interval": 30.0,
        }


def setup_logger() -> None:  # pylint: disable=too-many-locals,too-many-statements
    """Setup logger with current settings.

    Each output (console, systemd, file) has its own independent log level.
    """
    settings = get_logger_settings()

    # Get per-output log levels
    console_level_str = settings.get("console_level", "INFO")
    systemd_level_str = settings.get("systemd_level", "ERROR")
    file_level_str = settings.get("file_level", "DEBUG")

    def get_numeric_level(level_str: str, default: int) -> int:
        level = getattr(logging, level_str.upper(), None)
        return level if isinstance(level, int) else default

    console_numeric = get_numeric_level(console_level_str, logging.INFO)
    systemd_numeric = get_numeric_level(systemd_level_str, logging.ERROR)
    file_numeric = get_numeric_level(file_level_str, logging.DEBUG)

    # Create or get logger
    logger_instance = logging.getLogger(__name__)

    # Clear only logger-managed handlers (StreamHandler, FileHandler, JournalHandler)
    # Keep custom handlers like LogTabHandler intact
    managed_handler_types: list[type] = [logging.StreamHandler, logging.FileHandler]
    if SYSTEMD_AVAILABLE:
        managed_handler_types.append(JournalHandler)

    for handler in logger_instance.handlers[:]:
        # Only remove handlers that are exactly our managed types
        # Custom subclasses are preserved
        if type(handler) in managed_handler_types:
            logger_instance.removeHandler(handler)

    # Set logger to lowest enabled level to capture all messages
    min_level = logging.DEBUG  # Default to lowest
    if settings["to_console"]:
        min_level = min(min_level, console_numeric)
    if settings["to_systemd"]:
        min_level = min(min_level, systemd_numeric)
    if settings["to_file"]:
        min_level = min(min_level, file_numeric)
    logger_instance.setLevel(min_level)

    # Create formatter with enhanced timing support
    enhanced_format = settings["format"].replace("%(asctime)s", "%(asctime)s[%(timestamp_ms)s]")
    formatter = logging.Formatter(enhanced_format)

    # Add file handler if enabled
    if settings["to_file"]:
        log_path = os.path.expanduser(settings["filename"])
        # Ensure directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(file_numeric)
        file_handler.setFormatter(formatter)
        logger_instance.addHandler(file_handler)

    # Add systemd journal handler if enabled and available
    if settings["to_systemd"] and SYSTEMD_AVAILABLE:
        journal_handler = JournalHandler(SYSLOG_IDENTIFIER="dfakeseeder")
        journal_handler.setLevel(systemd_numeric)
        journal_formatter = logging.Formatter("%(class_name)s[%(lineno)d]: %(message)s")
        journal_handler.setFormatter(journal_formatter)
        logger_instance.addHandler(journal_handler)

    # Add console handler if enabled
    if settings["to_console"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_numeric)
        console_handler.setFormatter(formatter)
        logger_instance.addHandler(console_handler)

    # Add filters for enhanced functionality
    logger_instance.addFilter(ClassNameFilter())
    logger_instance.addFilter(TimingFilter())

    # Add duplicate filter if enabled
    if settings.get("suppress_duplicates", True):
        duplicate_filter = DuplicateFilter(
            time_window=settings.get("duplicate_time_window", 5.0),
            flush_interval=settings.get("duplicate_flush_interval", 30.0),
        )
        logger_instance.addFilter(duplicate_filter)

    # Create enhanced logger wrapper with performance tracking
    class EnhancedLogger:
        """Enhanced logger wrapper with TRACE level and performance tracking."""

        def __init__(self, logger_instance: Any) -> None:
            self._logger = logger_instance
            self.performance = PerformanceLogger(logger_instance)

        def __getattr__(self, name: Any) -> Any:
            # Delegate all other attributes to the underlying logger
            return getattr(self._logger, name)

        def trace(self, message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
            """
            Ultra-verbose logging for detailed diagnostics.
            Use for: function entry/exit, loop iterations, internal state.
            """
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.log(TRACE_LEVEL, message, **kwargs)

        def debug(self, message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
            """
            Verbose diagnostic logging.
            Use for: important state changes, control flow, variable values.
            """
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.debug(message, **kwargs)

        def info(self, message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
            """
            Important state changes and milestones.
            Use for: application lifecycle, major operations, user actions.
            """
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.info(message, **kwargs)

        def warning(self, message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
            """
            Unexpected but recoverable situations.
            Use for: missing optional config, deprecated usage, performance issues.
            """
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.warning(message, **kwargs)

        def error(self, message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
            """
            Errors that need attention but don't crash the app.
            Use for: failed operations, exceptions caught, data errors.
            """
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.error(message, **kwargs)

        def critical(self, message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
            """
            Fatal errors that prevent operation.
            Use for: cannot start app, critical resources missing, unrecoverable errors.
            """
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.critical(message, **kwargs)

    enhanced_logger = EnhancedLogger(logger_instance)
    return enhanced_logger  # type: ignore[return-value]


# pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals,too-many-statements
def reconfigure_logger(
    override_console: Optional[bool] = None,
    override_systemd: Optional[bool] = None,
    override_file: Optional[bool] = None,
    override_console_level: Optional[str] = None,
    override_systemd_level: Optional[str] = None,
    override_file_level: Optional[str] = None,
) -> Any:
    """Reconfigure logger with current settings - call when settings change.

    Each output (console, systemd, file) has its own independent log level.
    There is no main level.

    Args:
        override_console: If provided, use this value for console logging.
        override_systemd: If provided, use this value for systemd logging.
        override_file: If provided, use this value for file logging.
        override_console_level: If provided, use this level for console handler.
        override_systemd_level: If provided, use this level for systemd handler.
        override_file_level: If provided, use this level for file handler.
    """
    global logger  # pylint: disable=global-statement

    # Get the underlying Python logger instance
    if hasattr(logger, "_logger"):
        underlying_logger = logger._logger  # pylint: disable=protected-access
    else:
        # Fallback: create new logger if structure is unexpected
        logger = setup_logger()  # type: ignore[func-returns-value]
        return logger

    # Get new settings
    settings = get_logger_settings()
    to_console = override_console if override_console is not None else settings["to_console"]
    to_systemd = override_systemd if override_systemd is not None else settings["to_systemd"]
    to_file = override_file if override_file is not None else settings["to_file"]

    # Per-output log levels - each has its own independent level
    console_level_str = override_console_level or settings.get("console_level", "INFO")
    systemd_level_str = override_systemd_level or settings.get("systemd_level", "ERROR")
    file_level_str = override_file_level or settings.get("file_level", "DEBUG")

    # Calculate numeric levels for each output
    def get_numeric_level(level_str: str, default_level: int) -> int:
        level = getattr(logging, level_str.upper(), None)
        return level if isinstance(level, int) else default_level

    console_numeric = get_numeric_level(console_level_str, logging.INFO)
    systemd_numeric = get_numeric_level(systemd_level_str, logging.ERROR)
    file_numeric = get_numeric_level(file_level_str, logging.DEBUG)

    # Set logger to the lowest level of all outputs so all messages are captured
    min_level = min(console_numeric, systemd_numeric, file_numeric)
    if to_console:
        min_level = min(min_level, console_numeric)
    if to_systemd:
        min_level = min(min_level, systemd_numeric)
    if to_file:
        min_level = min(min_level, file_numeric)

    # Update logger level to lowest enabled level to capture all messages
    underlying_logger.setLevel(min_level)

    # Clear only logger-managed handlers (StreamHandler, FileHandler, JournalHandler)
    # Keep custom handlers like LogTabHandler intact
    managed_handler_types: list[type] = [logging.StreamHandler, logging.FileHandler]
    if SYSTEMD_AVAILABLE:
        managed_handler_types.append(JournalHandler)

    for handler in underlying_logger.handlers[:]:
        # Only remove handlers that are exactly our managed types
        # Custom subclasses (like LogTabHandler) are preserved
        if type(handler) in managed_handler_types:
            underlying_logger.removeHandler(handler)

    # Re-add handlers with new settings
    enhanced_format = settings["format"].replace("%(asctime)s", "%(asctime)s[%(timestamp_ms)s]")
    formatter = logging.Formatter(enhanced_format)

    # File handler
    if to_file:
        log_path = os.path.expanduser(settings["filename"])
        # Ensure directory exists
        log_dir = os.path.dirname(log_path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(file_numeric)
        file_handler.setFormatter(formatter)
        underlying_logger.addHandler(file_handler)

    # Console handler
    if to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(console_numeric)
        console_handler.setFormatter(formatter)
        underlying_logger.addHandler(console_handler)

    # Systemd handler (if available and enabled)
    if to_systemd and SYSTEMD_AVAILABLE:
        journal_handler = JournalHandler(SYSLOG_IDENTIFIER="dfakeseeder")
        journal_handler.setLevel(systemd_numeric)
        journal_formatter = logging.Formatter("%(class_name)s[%(lineno)d]: %(message)s")
        journal_handler.setFormatter(journal_formatter)
        underlying_logger.addHandler(journal_handler)

    return logger


def get_performance_logger() -> Any:
    """Get a performance logger instance for timing operations."""
    return logger.performance if hasattr(logger, "performance") else None


def debug(message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
    """Global convenience function for debug logs with class name."""
    logger.debug(message, class_name, **kwargs)


def info(message: str, class_name: Optional[str] = None, **kwargs: Any) -> Any:
    """Global convenience function for info logs with class name."""
    logger.info(message, class_name, **kwargs)


# Initialize enhanced logger with defaults
logger = setup_logger()  # type: ignore[func-returns-value]
