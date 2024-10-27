import json
import os
import shutil
from threading import Lock

from gi.repository import GObject
from lib.handlers.FileModifiedEventHandler import FileModifiedEventHandler
from lib.logger import logger
from watchdog.observers import Observer


class Settings(GObject.Object):
    _settings = {}
    _instance = None  # Singleton instance
    _lock = Lock()  # Lock for thread safety

    __gsignals__ = {
        "attribute-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str, object),
        )
    }

    @staticmethod
    def get_instance(file_path=None):
        logger.info("Settings get instance", extra={"class_name": "Settings"})
        env_file = os.getenv(
            "DFS_SETTINGS",
            os.path.expanduser("~/.config/dfakeseeder") + "/settings.json",
        )
        file_path = env_file if file_path is None else file_path

        home_config_path = os.path.expanduser("~/.config/dfakeseeder")

        # Check if the destination directory exists, if not create it
        if not os.path.exists(home_config_path):
            source_path = "config/default.json"
            os.makedirs(home_config_path)
            os.makedirs(home_config_path + "/torrents")
            # Copy the source file to the destination directory
            shutil.copy(source_path, home_config_path + "/settings.json")

        if Settings._instance is None:
            Settings._instance = Settings(file_path)
        return Settings._instance

    def __init__(self, file_path):
        logger.info(
            "Settings instantiate",
            extra={"class_name": self.__class__.__name__},
        )
        if Settings._instance is not None:
            raise Exception("Only one instance of Settings class is allowed.")
        super().__init__()
        self._file_path = file_path
        self._last_modified = 0
        self.load_settings()
        Settings._instance = self

        # Create a file event handler
        self._event_handler = FileModifiedEventHandler(self)

        # Create a file system observer
        self._observer = Observer()
        self._observer.schedule(self._event_handler, path=os.getcwd(), recursive=False)
        self._observer.start()

    def load_settings(self):
        logger.info("Settings load", extra={"class_name": self.__class__.__name__})
        try:
            # Check if the file has been modified since last load
            modified = os.path.getmtime(self._file_path)
            if modified > self._last_modified:
                with open(self._file_path, "r") as f:
                    self._settings = json.load(f)
                self._last_modified = modified
        except FileNotFoundError:
            # If the file doesn't exist, create an empty settings dictionary
            self._settings = {
                "upload_speed": 50,
                "download_speed": 500,
                "seed_per_second": 75,
                "announce_interval": 1800,
                "torrents": [],
            }

            if not os.path.exists(self._file_path):
                # Create the JSON file with default contents
                with open(self._file_path, "w") as f:
                    json.dump(self._settings, f, indent=4)

    def save_settings(self):
        logger.info("Settings save", extra={"class_name": self.__class__.__name__})
        with open(self._file_path, "w") as f:
            json.dump(self._settings, f, indent=4)

    def save_quit(self):
        logger.info("Settings quit", extra={"class_name": self.__class__.__name__})
        self._observer.stop()
        self.save_settings()

    def __getattr__(self, name):
        if name == "settings":
            return self._settings
        elif name in self._settings:
            return self._settings[name]
        else:
            raise AttributeError(f"Setting '{name}' not found.")

    def __setattr__(self, name, value):
        logger.debug(
            "Settings __setattr__",
            extra={"class_name": self.__class__.__name__},
        )
        # Acquire the lock before modifying the settings
        with Settings._lock:
            if name == "_settings":
                # Directly set the 'settings' attribute
                super().__setattr__(name, value)
            elif name.startswith("_"):
                # Set the attribute without modifying 'settings' or emitting
                # signals
                super().__setattr__(name, value)
            else:
                nested_attribute = name.split(".")
                if len(nested_attribute) > 1:
                    # Update the nested attribute
                    current = self._settings
                    for attr in nested_attribute[:-1]:
                        current = current.setdefault(attr, {})
                    current[nested_attribute[-1]] = value
                else:
                    # Set the setting value and emit the 'attribute-changed'
                    # signal
                    self._settings[name] = value
                    self.emit("attribute-changed", name, value)
                    self.save_settings()
