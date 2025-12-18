from typing import Any

try:
    # fmt: off
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    # fmt: on
    # Fallback if watchdog is not available
    class FileSystemEventHandler:  # type: ignore[no-redef]
        pass

    WATCHDOG_AVAILABLE = False


class FileModifiedEventHandler(FileSystemEventHandler):
    def __init__(self, settings_instance: Any) -> None:
        self.settings = settings_instance

    def on_modified(self, event: Any) -> None:
        if event.src_path == self.settings._file_path:
            self.settings.load_settings()
