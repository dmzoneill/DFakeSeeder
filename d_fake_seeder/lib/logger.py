# fmt: off
import functools
import logging
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
            logger_instance._log(TRACE_LEVEL, msg, args, **kwargs)

    logger_instance.trace = trace
    return logger_instance  # type: ignore[no-any-return]


# fmt: on


class ClassNameFilter(logging.Filter):
    def filter(self, record: Any) -> Any:
        record.class_name = record.name if not hasattr(record, "class_name") else record.class_name
        return True


class TimingFilter(logging.Filter):
    """Filter that adds precise timing information to log records."""

    def filter(self, record: Any) -> Any:
        record.precise_time = time.time()
        record.timestamp_ms = f"{record.precise_time:.3f}"
        return True


class DuplicateFilter(logging.Filter):
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
            else:
                # Time window expired, log summary of suppressed messages
                if count > 1:
                    duration = last_time - first_time
                    record.msg = (
                        f"{record.getMessage()} " f"(previous message repeated {count} times over {duration:.1f}s)"
                    )

                # Reset counter for this message
                self.last_messages[message_key] = (
                    1,
                    current_time,
                    current_time,
                    record,
                )
                return True
        else:
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


def get_logger_settings() -> Any:
    """Get logger settings from AppSettings if available, otherwise use defaults"""
    try:
        from domain.app_settings import AppSettings

        app_settings = AppSettings.get_instance()
        return {
            "level": app_settings.get("log_level", "INFO"),
            "level_systemd": app_settings.get("log_level_systemd", "WARNING"),
            "filename": app_settings.get("log_filename", "log.log"),
            "format": app_settings.get(
                "log_format",
                "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s",
            ),
            "to_file": app_settings.get("log_to_file", False),
            "to_systemd": app_settings.get("log_to_systemd", True),
            "to_console": app_settings.get("log_to_console", False),
            "suppress_duplicates": app_settings.get("log_suppress_duplicates", True),
            "duplicate_time_window": app_settings.get("log_duplicate_time_window", 5.0),
            "duplicate_flush_interval": app_settings.get("log_duplicate_flush_interval", 30.0),
        }
    except (ImportError, Exception):
        # Fallback to hardcoded defaults if AppSettings not available
        # This should only happen during early startup or testing
        default_format = "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s"
        return {
            "level": "INFO",
            "level_systemd": "WARNING",
            "filename": "log.log",
            "format": default_format,
            "to_file": False,
            "to_systemd": True,
            "to_console": False,
            "suppress_duplicates": True,
            "duplicate_time_window": 5.0,
            "duplicate_flush_interval": 30.0,
        }


def setup_logger() -> None:
    """Setup logger with current settings"""
    settings = get_logger_settings()

    # Set the logger level
    log_level = settings["level"]
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.DEBUG

    # Get systemd-specific log level (defaults to WARNING to reduce journal noise)
    log_level_systemd = settings.get("level_systemd", "WARNING")
    numeric_level_systemd = getattr(logging, log_level_systemd.upper(), None)
    if not isinstance(numeric_level_systemd, int):
        numeric_level_systemd = logging.WARNING

    # Detect if running in a terminal session
    # If stdin/stdout/stderr are connected to a TTY, we're in an interactive terminal
    # In this case, systemd journal will write to the terminal instead of the journal daemon
    running_in_terminal = sys.stdout.isatty() or sys.stderr.isatty()

    # Create or get logger
    logger_instance = logging.getLogger(__name__)

    # Clear existing handlers to avoid duplicates
    for handler in logger_instance.handlers[:]:
        logger_instance.removeHandler(handler)

    logger_instance.setLevel(numeric_level)

    # Create formatter with enhanced timing support - automatically include precise timestamps
    enhanced_format = settings["format"].replace("%(asctime)s", "%(asctime)s[%(timestamp_ms)s]")
    formatter = logging.Formatter(enhanced_format)

    # Add file handler if enabled
    if settings["to_file"]:
        file_handler = logging.FileHandler(settings["filename"])
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        logger_instance.addHandler(file_handler)

    # Add systemd journal handler if enabled and available
    # Use separate WARNING level for systemd to reduce journal noise
    # Skip systemd logging when running in a terminal to avoid duplicate console output
    if settings["to_systemd"] and SYSTEMD_AVAILABLE and not running_in_terminal:
        journal_handler = JournalHandler(SYSLOG_IDENTIFIER="dfakeseeder")
        journal_handler.setLevel(numeric_level_systemd)
        # For systemd, we use a simpler format since it adds its own metadata
        journal_formatter = logging.Formatter("%(class_name)s[%(lineno)d]: %(message)s")
        journal_handler.setFormatter(journal_formatter)
        logger_instance.addHandler(journal_handler)
    elif settings["to_systemd"] and (not SYSTEMD_AVAILABLE or running_in_terminal):
        # If systemd logging is requested but not available or running in terminal, skip it
        # Don't fall back to console - respect the user's logging preferences
        pass

    # Add console handler if enabled
    if settings["to_console"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
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


def reconfigure_logger() -> Any:
    """Reconfigure logger with current settings - call when settings change"""
    global logger
    logger = setup_logger()  # type: ignore[func-returns-value]
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
