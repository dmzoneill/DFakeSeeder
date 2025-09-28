import functools
import logging
import sys
import time
from typing import Dict, Optional

# Try to import systemd journal support
try:
    from systemd.journal import JournalHandler

    SYSTEMD_AVAILABLE = True
except ImportError:
    SYSTEMD_AVAILABLE = False


class ClassNameFilter(logging.Filter):
    def filter(self, record):
        record.class_name = record.name if not hasattr(record, "class_name") else record.class_name
        return True


class TimingFilter(logging.Filter):
    """Filter that adds precise timing information to log records."""

    def filter(self, record):
        record.precise_time = time.time()
        record.timestamp_ms = f"{record.precise_time:.3f}"
        return True


class PerformanceLogger:
    """Enhanced logger with performance tracking and timing capabilities."""

    def __init__(self, logger_instance):
        self._logger = logger_instance
        self._timers: Dict[str, float] = {}
        self._operation_stack: list = []

    def timing_info(self, message: str, class_name: Optional[str] = None, operation_time_ms: Optional[float] = None):
        """Log with timing information similar to the old print statements."""
        extra = {}
        if class_name:
            extra["class_name"] = class_name

        if operation_time_ms is not None:
            message = f"{message} (took {operation_time_ms:.1f}ms)"

        self._logger.info(message, extra=extra)

    def timing_debug(self, message: str, class_name: Optional[str] = None, operation_time_ms: Optional[float] = None):
        """Debug level timing information."""
        extra = {}
        if class_name:
            extra["class_name"] = class_name

        if operation_time_ms is not None:
            message = f"{message} (took {operation_time_ms:.1f}ms)"

        self._logger.debug(message, extra=extra)

    def start_timer(self, operation_name: str) -> float:
        """Start a named timer and return the start time."""
        start_time = time.time()
        self._timers[operation_name] = start_time
        return start_time

    def end_timer(
        self, operation_name: str, message: Optional[str] = None, class_name: Optional[str] = None, level: str = "info"
    ) -> float:
        """End a named timer and log the duration."""
        if operation_name not in self._timers:
            self._logger.warning(f"Timer '{operation_name}' was not started")
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

    def operation_context(self, operation_name: str, class_name: Optional[str] = None):
        """Context manager for timing operations."""
        return OperationTimer(self, operation_name, class_name)

    def performance_info(self, message: str, class_name: Optional[str] = None, **metrics):
        """Log performance information with custom metrics."""
        extra = {"class_name": class_name} if class_name else {}
        extra.update(metrics)

        metric_str = " ".join([f"{k}={v}" for k, v in metrics.items()])
        full_message = f"{message} [{metric_str}]" if metric_str else message

        self._logger.info(full_message, extra=extra)


class OperationTimer:
    """Context manager for timing operations."""

    def __init__(self, perf_logger: PerformanceLogger, operation_name: str, class_name: Optional[str] = None):
        self.perf_logger = perf_logger
        self.operation_name = operation_name
        self.class_name = class_name
        self.start_time = None

    def __enter__(self):
        self.start_time = self.perf_logger.start_timer(self.operation_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.perf_logger.end_timer(self.operation_name, class_name=self.class_name)


def timing_decorator(operation_name: Optional[str] = None, level: str = "debug"):
    """Decorator to automatically time function execution."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            op_name = operation_name or func.__name__
            class_name = self.__class__.__name__ if hasattr(self, "__class__") else None

            with logger.performance.operation_context(op_name, class_name):
                return func(self, *args, **kwargs)

        return wrapper

    return decorator


def get_logger_settings():
    """Get logger settings from AppSettings if available, otherwise use defaults"""
    try:
        from domain.app_settings import AppSettings

        app_settings = AppSettings.get_instance()
        return {
            "level": app_settings.get("log_level", "INFO"),
            "filename": app_settings.get("log_filename", "log.log"),
            "format": app_settings.get(
                "log_format",
                "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s",
            ),
            "to_file": app_settings.get("log_to_file", False),
            "to_systemd": app_settings.get("log_to_systemd", True),
            "to_console": app_settings.get("log_to_console", False),
        }
    except (ImportError, Exception):
        # Fallback to hardcoded defaults if AppSettings not available
        # This should only happen during early startup or testing
        default_format = "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s"
        return {
            "level": "INFO",
            "filename": "log.log",
            "format": default_format,
            "to_file": False,
            "to_systemd": True,
            "to_console": False,
        }


def setup_logger():
    """Setup logger with current settings"""
    settings = get_logger_settings()

    # Set the logger level
    log_level = settings["level"]
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        numeric_level = logging.DEBUG

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
    if settings["to_systemd"] and SYSTEMD_AVAILABLE:
        journal_handler = JournalHandler(SYSLOG_IDENTIFIER="dfakeseeder")
        journal_handler.setLevel(numeric_level)
        # For systemd, we use a simpler format since it adds its own metadata
        journal_formatter = logging.Formatter("%(class_name)s[%(lineno)d]: %(message)s")
        journal_handler.setFormatter(journal_formatter)
        logger_instance.addHandler(journal_handler)
    elif settings["to_systemd"] and not SYSTEMD_AVAILABLE:
        # Fallback to stderr if systemd not available but requested
        sys.stderr.write(
            "Warning: systemd journal logging requested but python-systemd not available, falling back to stderr\n"
        )
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(numeric_level)
        stderr_handler.setFormatter(formatter)
        logger_instance.addHandler(stderr_handler)

    # Add console handler if enabled
    if settings["to_console"]:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        logger_instance.addHandler(console_handler)

    # Add filters for enhanced functionality
    logger_instance.addFilter(ClassNameFilter())
    logger_instance.addFilter(TimingFilter())

    # Create enhanced logger wrapper with performance tracking
    class EnhancedLogger:
        def __init__(self, logger_instance):
            self._logger = logger_instance
            self.performance = PerformanceLogger(logger_instance)

        def __getattr__(self, name):
            # Delegate all other attributes to the underlying logger
            return getattr(self._logger, name)

        def debug(self, message: str, class_name: Optional[str] = None, **kwargs):
            """Enhanced debug with automatic class name."""
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.debug(message, **kwargs)

        def info(self, message: str, class_name: Optional[str] = None, **kwargs):
            """Enhanced info with automatic class name."""
            extra = kwargs.get("extra", {})
            if class_name:
                extra["class_name"] = class_name
            kwargs["extra"] = extra
            return self._logger.info(message, **kwargs)

    enhanced_logger = EnhancedLogger(logger_instance)
    return enhanced_logger


def reconfigure_logger():
    """Reconfigure logger with current settings - call when settings change"""
    global logger
    logger = setup_logger()
    return logger


def get_performance_logger():
    """Get a performance logger instance for timing operations."""
    return logger.performance if hasattr(logger, "performance") else None


def debug(message: str, class_name: Optional[str] = None, **kwargs):
    """Global convenience function for debug logs with class name."""
    logger.debug(message, class_name, **kwargs)


def info(message: str, class_name: Optional[str] = None, **kwargs):
    """Global convenience function for info logs with class name."""
    logger.info(message, class_name, **kwargs)


# Initialize enhanced logger with defaults
logger = setup_logger()
