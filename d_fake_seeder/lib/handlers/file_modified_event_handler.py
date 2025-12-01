try:
    # fmt: off
    from watchdog.events import FileSystemEventHandler

    WATCHDOG_AVAILABLE = True
except ImportError:
    # fmt: on
    # Fallback if watchdog is not available
    class FileSystemEventHandler:
        pass

    WATCHDOG_AVAILABLE = False


class FileModifiedEventHandler(FileSystemEventHandler):
    def __init__(self, settings_instance):
        self.settings = settings_instance

    def on_modified(self, event):
        if event.src_path == self.settings._file_path:
            self.settings.load_settings()
