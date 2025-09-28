from watchdog.events import FileSystemEventHandler


class FileModifiedEventHandler(FileSystemEventHandler):
    def __init__(self, settings_instance):
        self.settings = settings_instance

    def on_modified(self, event):
        if event.src_path == self.settings._file_path:
            self.settings.load_settings()
