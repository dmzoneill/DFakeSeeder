import logging
import os


class ClassNameFilter(logging.Filter):
    def filter(self, record):
        record.class_name = (
            record.name if not hasattr(record, "class_name") else record.class_name
        )
        return True


# Set the logger level from environment variable
# DEBUG, INFO, WARNING, ERROR, and CRITICAL.
log_level = os.getenv("LOG_LEVEL", "DEBUG")
numeric_level = getattr(logging, log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError(f"Invalid log level: {log_level}")

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(numeric_level)

# Create a file handler
file_handler = logging.FileHandler("log.log")
file_handler.setLevel(numeric_level)

# Add a custom formatter
formatter = logging.Formatter(
    "[%(asctime)s][%(class_name)s][%(levelname)s][%(lineno)d] - %(message)s"
)
file_handler.setFormatter(formatter)

# Add the file handler to the logger
logger.addHandler(file_handler)
logger.addFilter(ClassNameFilter())
