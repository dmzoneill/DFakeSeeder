# fmt: off
# isort: skip_file
import json
import os
import shutil
import tempfile
from pathlib import Path
from threading import Lock

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import GObject  # noqa: E402

from d_fake_seeder.lib.handlers.file_modified_event_handler import (  # noqa: E402
    WATCHDOG_AVAILABLE,
    FileModifiedEventHandler,
)
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.constants import NetworkConstants  # noqa: E402

if WATCHDOG_AVAILABLE:
    from watchdog.observers import Observer  # noqa: E402
else:
    # Fallback if watchdog is not available
    class Observer:
        def __init__(self):
            pass

        def schedule(self, *args, **kwargs):
            pass

        def start(self):
            pass

        def stop(self):
            pass

# fmt: on


class AppSettings(GObject.GObject):
    """
    Unified application settings manager (replaces both Settings and old AppSettings)
    Thread-safe singleton with nested attribute access, file watching, and GObject signals
    Manages all application configuration in ~/.config/dfakeseeder/settings.json
    """

    __gsignals__ = {
        "settings-attribute-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str, object),  # key, value
        ),
        "settings-value-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str, object),  # key, value
        ),
        # Legacy compatibility signals (deprecated)
        "attribute-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str, object),  # key, value
        ),
        "setting-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str, object),  # key, value
        ),
    }

    _instance = None
    _lock = Lock()  # Thread safety
    _logger = None  # Lazy logger instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize GObject early to avoid "not initialized" errors
            GObject.GObject.__init__(cls._instance)
        return cls._instance

    def __init__(self, file_path=None):
        # Check if already initialized AND file_path matches
        # This allows re-initialization when file_path changes (e.g., in tests)
        if hasattr(self, "_initialized") and hasattr(self, "_file_path"):
            # If file_path is changing, we need to reinitialize
            if file_path is not None and str(file_path) != str(self._file_path):
                # Stop existing observer before reinitializing
                if hasattr(self, "_observer") and self._observer:
                    try:
                        self._observer.stop()
                        self._observer.join(timeout=1.0)
                    except Exception:
                        pass
                # Clear initialization flag to allow reinitialization
                delattr(self, "_initialized")
            elif file_path is None or str(file_path) == str(self._file_path):
                # Same file path or no file path specified, skip reinitialization
                return

        # GObject.__init__ already called in __new__
        self._initialized = True

        self.logger.debug("AppSettings instantiate", extra={"class_name": self.__class__.__name__})

        # Initialize file paths (compatible with Settings API)
        if file_path is None:
            env_file = os.getenv(
                "DFS_SETTINGS",
                os.path.expanduser("~/.config/dfakeseeder") + "/settings.json",
            )
            file_path = env_file

        self._file_path = file_path
        self.config_dir = Path(file_path).parent
        self.config_file = Path(file_path)
        self.default_config_file = Path(__file__).parent / "config" / "default.json"

        # Initialize settings storage (compatible with both APIs)
        self.settings = {}  # New API
        self._settings = {}  # Legacy API compatibility
        self._defaults = {}
        self._last_modified = 0

        # Create config directory if needed (like Settings does)
        home_config_path = os.path.expanduser("~/.config/dfakeseeder")
        if not os.path.exists(home_config_path):
            os.makedirs(home_config_path, exist_ok=True)
            os.makedirs(home_config_path + "/torrents", exist_ok=True)

            # Determine source config file (priority order):
            # 1. System-wide RPM config: /etc/dfakeseeder/default.json
            # 2. Package default: d_fake_seeder/config/default.json
            system_config = Path("/etc/dfakeseeder/default.json")
            if system_config.exists():
                source_path = str(system_config)
                self.logger.debug(
                    f"Using system-wide config from {source_path}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                source_path = str(self.default_config_file)
                self.logger.debug(
                    f"Using package default config from {source_path}",
                    extra={"class_name": self.__class__.__name__},
                )

            # Copy the source file to the destination directory
            if os.path.exists(source_path):
                shutil.copy(source_path, home_config_path + "/settings.json")
                self.logger.debug(
                    f"Created user config at {home_config_path}/settings.json",
                    extra={"class_name": self.__class__.__name__},
                )

        # Load defaults and settings
        self._load_defaults()
        self.load_settings()

        # Set up file watching
        self._event_handler = FileModifiedEventHandler(self)
        self._observer = Observer()
        self._observer.schedule(self._event_handler, path=str(self.config_dir), recursive=False)
        self._observer.start()

    @property
    def logger(self):
        """Get logger instance with lazy import to avoid circular dependency"""
        if AppSettings._logger is None:
            try:
                from d_fake_seeder.lib.logger import logger

                AppSettings._logger = logger
            except ImportError:
                # Fallback to print if logger not available
                import logging

                AppSettings._logger = logging.getLogger(__name__)
        return AppSettings._logger

    def _load_defaults(self):
        """Load default settings from config/default.json"""
        try:
            with open(self.default_config_file, "r") as f:
                self._defaults = json.load(f)
            self.logger.debug(f"Loaded {len(self._defaults)} default settings from {self.default_config_file}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Could not load default settings file ({e}), using hardcoded defaults")
            self._defaults = {
                "upload_speed": 50,
                "download_speed": 500,
                "announce_interval": 1800,
                "concurrent_http_connections": 2,
                "torrents": {},
                "language": "auto",
            }

    def _merge_with_defaults(self, user_settings):
        """Recursively merge user settings with defaults"""

        def deep_merge(default_dict, user_dict):
            result = default_dict.copy()
            for key, value in user_dict.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(self._defaults, user_settings)

    def _get_nested_value(self, data, key):
        """Get value from nested dictionary using dot notation"""
        keys = key.split(".")
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return None
        return data

    def _set_nested_value(self, data, key, value):
        """Set value in nested dictionary using dot notation"""
        keys = key.split(".")
        for k in keys[:-1]:
            data = data.setdefault(k, {})
        data[keys[-1]] = value

    def load_settings(self):
        """Load settings from files (compatible with Settings API)"""
        self.logger.debug("Settings load", extra={"class_name": self.__class__.__name__})
        try:
            # Check if the file has been modified since last load
            modified = os.path.getmtime(self._file_path)
            if modified > self._last_modified:
                with open(self._file_path, "r") as f:
                    user_settings = json.load(f)
                # Merge user settings with defaults
                merged_settings = self._merge_with_defaults(user_settings)

                # Update both storage systems
                self._settings = merged_settings
                self.settings = merged_settings.copy()
                self._last_modified = modified
                self.logger.debug(
                    f"Loaded settings - language from file: {user_settings.get('language', 'NOT SET')},"
                    f" merged language: {merged_settings.get('language', 'NOT SET')}",
                    extra={"class_name": self.__class__.__name__},
                )
                self.logger.debug(f"Loaded and merged settings, total: {len(self.settings)}")
        except FileNotFoundError:
            # If the file doesn't exist, start with defaults and create the file
            self._settings = self._defaults.copy()
            self.settings = self._defaults.copy()

            if not os.path.exists(self._file_path):
                # Create the JSON file with default contents
                with open(self._file_path, "w") as f:
                    json.dump(self._settings, f, indent=4)
                self.logger.debug("Created new settings file with defaults")
        except json.JSONDecodeError as e:
            # Handle corrupt/truncated JSON files
            self.logger.warning(f"Settings file contains invalid JSON, using defaults: {e}")
            self._settings = self._defaults.copy()
            self.settings = self._defaults.copy()
        except Exception as e:
            self.logger.error(f"Error loading settings: {e}")

    def save_settings(self):
        """Save current settings to user config file (thread-safe with atomic writes)"""
        self.logger.debug("Settings save", extra={"class_name": self.__class__.__name__})
        try:
            # Use lock to prevent concurrent save operations
            self.logger.debug(
                "About to acquire settings lock",
                extra={"class_name": self.__class__.__name__},
            )
            with AppSettings._lock:
                self.logger.debug(
                    "Settings lock acquired",
                    extra={"class_name": self.__class__.__name__},
                )
                self._save_settings_unlocked()
                self.logger.debug(
                    "Settings saved to disk",
                    extra={"class_name": self.__class__.__name__},
                )
            self.logger.debug("Settings lock released", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}", exc_info=True)

    def _save_settings_unlocked(self):
        """Save current settings without acquiring lock (for internal use when lock already held)"""
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Use atomic write: write to temporary file first, then rename
        # This prevents corruption from incomplete writes during race conditions
        temp_fd = None
        temp_path = None
        try:
            # Create temporary file in same directory as target file
            temp_fd, temp_path = tempfile.mkstemp(dir=str(self.config_dir), prefix=".settings_tmp_", suffix=".json")

            # Write settings to temporary file
            with os.fdopen(temp_fd, "w") as temp_file:
                json.dump(self._settings, temp_file, indent=4)
                temp_file.flush()  # Ensure data is written to disk
                os.fsync(temp_file.fileno())  # Force OS to write to disk

            temp_fd = None  # File is now closed

            # Atomically replace the original file with the temporary file
            # This operation is atomic on POSIX systems, preventing corruption
            os.replace(temp_path, self._file_path)
            temp_path = None  # Successfully moved, don't clean up

            self.logger.debug("Settings saved successfully with atomic write")

        except Exception as write_error:
            # Clean up on error
            if temp_fd is not None:
                try:
                    os.close(temp_fd)
                except OSError:
                    pass
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass
            raise write_error

    def save_quit(self):
        """Save settings and stop file watching (Settings API compatibility)"""
        self.logger.debug("Settings quit", extra={"class_name": self.__class__.__name__})
        if hasattr(self, "_observer"):
            self._observer.stop()
        self.save_settings()

    def get(self, key, default=None):
        """Get a setting value (supports dot notation for nested values)"""
        # Try nested access first for dot notation keys (e.g., "watch_folder.enabled")
        value = self._get_nested_value(self._settings, key)
        if value is not None:
            return value
        # Fallback to direct key access for backward compatibility
        return self._settings.get(key, default)

    def set(self, key, value):
        """Set a setting value and save immediately"""
        logger.debug("Setting method called", "AppSettings")
        logger.debug(f"Setting: {key} = {value}", "AppSettings")

        # Determine if we need to emit signals (done outside the lock to avoid deadlock)
        should_emit = False
        with AppSettings._lock:
            # Get old value using nested access for dot notation keys
            old_value = self._get_nested_value(self._settings, key)
            logger.debug(f"Old value: {old_value}", "AppSettings")
            if old_value != value:
                logger.debug("Value changed, updating and saving", "AppSettings")
                # Use nested setter to properly handle dot notation (e.g., "watch_folder.enabled")
                self._set_nested_value(self._settings, key, value)
                # Update both storage systems directly to avoid recursion
                super().__setattr__("settings", self._settings.copy())
                logger.debug("About to save settings", "AppSettings")
                self._save_settings_unlocked()
                logger.debug("Settings saved", "AppSettings")
                should_emit = True
            else:
                logger.debug("Value unchanged, skipping update", "AppSettings")

        # Emit signals AFTER releasing the lock to avoid re-entrancy deadlocks
        if should_emit:
            logger.debug("Lock released, emitting signals", "AppSettings")
            # Emit new signals
            logger.debug("Emitting 'settings-value-changed' signal", "AppSettings")
            self.emit("settings-value-changed", key, value)
            logger.debug("Emitting 'settings-attribute-changed' signal", "AppSettings")
            self.emit("settings-attribute-changed", key, value)
            # Legacy compatibility signals
            logger.debug("Emitting 'setting-changed' signal", "AppSettings")
            self.emit("setting-changed", key, value)
            logger.debug("Emitting 'attribute-changed' signal", "AppSettings")
            self.emit("attribute-changed", key, value)
            logger.debug("All signals emitted successfully", "AppSettings")
            self.logger.debug(f"Setting changed: {key} = {value}")

        logger.debug("Setting method completed", "AppSettings")

    def __getattr__(self, name):
        """Dynamic attribute access (Settings API compatibility)"""
        if name == "settings":
            try:
                return super().__getattribute__("_settings")
            except AttributeError:
                return {}

        try:
            settings = super().__getattribute__("_settings")
            if name in settings:
                return settings[name]
        except AttributeError:
            pass

        # Check if setting exists in defaults (supports nested paths)
        try:
            defaults = super().__getattribute__("_defaults")
        except AttributeError:
            defaults = {}

        default_value = self._get_nested_value(defaults, name)
        if default_value is not None:
            # Setting exists in defaults but not in user settings, use default and save it
            try:
                # Use lock to prevent race conditions when setting defaults
                with AppSettings._lock:
                    settings = super().__getattribute__("_settings")
                    self._set_nested_value(settings, name, default_value)
                    # Update both storage systems directly to avoid recursion
                    super().__setattr__("settings", settings.copy())
                    # Skip logger call during initialization to avoid recursion
                    # self.logger.info(f"Using default value for missing setting '{name}': {default_value}")
                    self.save_settings()
                    return default_value
            except AttributeError:
                return default_value
        else:
            raise AttributeError(f"Setting '{name}' not found in user settings or defaults.")

    def __setattr__(self, name, value):
        """Dynamic attribute setting (Settings API compatibility)"""
        # Handle private attributes and initialization normally
        if (
            name.startswith("_")
            or name in ["settings", "config_dir", "config_file", "default_config_file"]
            or not hasattr(self, "_initialized")
        ):
            super().__setattr__(name, value)
            return

        self.logger.debug("Settings __setattr__", extra={"class_name": self.__class__.__name__})

        # Determine what to emit BEFORE acquiring lock
        should_emit = False
        should_save = False

        # Acquire the lock before modifying the settings
        with AppSettings._lock:
            if name == "_settings":
                # Directly set the '_settings' attribute
                super().__setattr__(name, value)
            elif name.startswith("_"):
                # Set private attributes without modifying settings or emitting signals
                super().__setattr__(name, value)
            else:
                nested_attribute = name.split(".")
                if len(nested_attribute) > 1:
                    # Update the nested attribute
                    current = self._settings
                    for attr in nested_attribute[:-1]:
                        current = current.setdefault(attr, {})
                    current[nested_attribute[-1]] = value
                    # Also update the flat settings dict directly to avoid recursion
                    super().__setattr__("settings", self._settings.copy())
                    should_emit = True
                    should_save = True
                else:
                    # Set the setting value
                    self._settings[name] = value
                    # Update settings dict directly to avoid recursion
                    super().__setattr__("settings", self._settings.copy())
                    should_emit = True
                    should_save = True

            # Save settings WHILE HOLDING LOCK (prevents re-entry)
            if should_save:
                self._save_settings_unlocked()

        # Emit signals AFTER releasing the lock to avoid deadlock
        if should_emit:
            self.emit("settings-attribute-changed", name, value)
            self.emit("settings-value-changed", name, value)
            # Legacy compatibility signals
            self.emit("attribute-changed", name, value)
            self.emit("setting-changed", name, value)

    def get_all(self):
        """Get all settings as a dict"""
        return self._settings.copy()

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        try:
            with open(self.default_config_file, "r") as f:
                defaults = json.load(f)
                self._settings = defaults.copy()
                self.save_settings()
                self.logger.debug("Settings reset to defaults")
                # Emit signals for each changed setting
                for key, value in defaults.items():
                    # Emit new signals
                    self.emit("settings-value-changed", key, value)
                    self.emit("settings-attribute-changed", key, value)
                    # Legacy compatibility signal
                    self.emit("setting-changed", key, value)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"Could not load default config file, using current defaults ({e})")
            # Use already loaded defaults
            self._settings = self._defaults.copy()
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")

    @classmethod
    def get_instance(cls, file_path=None):
        """Get singleton instance (Settings API compatibility)"""
        # Note: Can't use self.logger here since this is a class method
        try:
            from d_fake_seeder.lib.logger import logger

            logger.debug("AppSettings get instance", extra={"class_name": "AppSettings"})
        except ImportError:
            pass
        if cls._instance is None:
            cls._instance = cls(file_path)
        return cls._instance

    # Application-specific setting accessors
    @property
    def window_width(self):
        return self.get("window_width", 1024)

    @window_width.setter
    def window_width(self, value):
        self.set("window_width", value)

    @property
    def window_height(self):
        return self.get("window_height", 600)

    @window_height.setter
    def window_height(self, value):
        self.set("window_height", value)

    @property
    def start_minimized(self):
        return self.get("start_minimized", False)

    @start_minimized.setter
    def start_minimized(self, value):
        self.set("start_minimized", value)

    @property
    def minimize_to_tray(self):
        return self.get("minimize_to_tray", False)

    @minimize_to_tray.setter
    def minimize_to_tray(self, value):
        self.set("minimize_to_tray", value)

    @property
    def auto_start(self):
        return self.get("auto_start", False)

    @auto_start.setter
    def auto_start(self, value):
        self.set("auto_start", value)

    @property
    def theme(self):
        return self.get("theme", "system")

    @theme.setter
    def theme(self, value):
        self.set("theme", value)

    @property
    def language(self):
        return self.get("language", "auto")

    @language.setter
    def language(self, value):
        self.set("language", value)

    def get_language(self):
        """
        Centralized language getter with proper fallback logic.

        Returns the actual language code to use, handling:
        1. User configured language from settings
        2. "auto" setting -> system locale detection
        3. Ultimate fallback to English if all else fails

        This is the ONLY method that should contain language fallback logic.
        All other parts of the application should use this method.
        """
        import locale

        # Get the configured language from settings
        configured_lang = self.get("language", "auto")
        self.logger.debug(
            f"get_language() - configured_lang from settings: {configured_lang}",
            extra={"class_name": self.__class__.__name__},
        )

        # If it's a specific language (not "auto"), use it directly
        if configured_lang != "auto":
            self.logger.debug(
                f"get_language() - returning configured language: {configured_lang}",
                extra={"class_name": self.__class__.__name__},
            )
            return configured_lang

        # "auto" means detect system language
        try:
            # Get system locale using newer method
            try:
                current_locale = locale.getlocale()[0]
                if current_locale:
                    system_locale = current_locale
                else:
                    # Fallback to deprecated method if getlocale returns None
                    system_locale = locale.getdefaultlocale()[0]
            except Exception:
                system_locale = locale.getdefaultlocale()[0]

            if system_locale:
                # Extract language code (e.g., 'en_US' -> 'en')
                lang_code = system_locale.split("_")[0].lower()
                return lang_code
        except Exception as e:
            self.logger.warning(f"Could not detect system locale: {e}")

        # Ultimate fallback to English
        return "en"

    # Connection settings
    @property
    def listening_port(self):
        return self.get("listening_port", NetworkConstants.DEFAULT_PORT)

    @listening_port.setter
    def listening_port(self, value):
        self.set("listening_port", value)

    @property
    def enable_upnp(self):
        return self.get("enable_upnp", True)

    @enable_upnp.setter
    def enable_upnp(self, value):
        self.set("enable_upnp", value)

    @property
    def enable_dht(self):
        return self.get("enable_dht", True)

    @enable_dht.setter
    def enable_dht(self, value):
        self.set("enable_dht", value)

    @property
    def enable_pex(self):
        return self.get("enable_pex", True)

    @enable_pex.setter
    def enable_pex(self, value):
        self.set("enable_pex", value)

    # Speed settings
    @property
    def global_upload_limit(self):
        return self.get("global_upload_limit", 0)  # 0 = unlimited

    @global_upload_limit.setter
    def global_upload_limit(self, value):
        self.set("global_upload_limit", value)

    @property
    def global_download_limit(self):
        return self.get("global_download_limit", 0)  # 0 = unlimited

    @global_download_limit.setter
    def global_download_limit(self, value):
        self.set("global_download_limit", value)

    # Web UI settings
    @property
    def enable_webui(self):
        return self.get("enable_webui", False)

    @enable_webui.setter
    def enable_webui(self, value):
        self.set("enable_webui", value)

    @property
    def webui_port(self):
        return self.get("webui_port", 8080)

    @webui_port.setter
    def webui_port(self, value):
        self.set("webui_port", value)

    @property
    def webui_username(self):
        return self.get("webui_username", "admin")

    @webui_username.setter
    def webui_username(self, value):
        self.set("webui_username", value)

    @property
    def webui_password(self):
        return self.get("webui_password", "")

    @webui_password.setter
    def webui_password(self, value):
        self.set("webui_password", value)

    # Advanced settings
    @property
    def log_level(self):
        return self.get("log_level", "INFO")

    @log_level.setter
    def log_level(self, value):
        self.set("log_level", value)

    @property
    def disk_cache_size(self):
        return self.get("disk_cache_size", 64)  # MB

    @disk_cache_size.setter
    def disk_cache_size(self, value):
        self.set("disk_cache_size", value)

    # Client detection methods
    def add_detected_client(self, user_agent):
        """Add a newly detected client to the detected clients list"""
        if not user_agent or user_agent.strip() == "":
            return

        detected_clients = self.get("detected_clients", [])

        # Clean up the user agent string
        user_agent = user_agent.strip()

        # Don't add if it's already in detected clients
        if user_agent in detected_clients:
            return

        # Don't add if it's already in default agents
        default_agents = self.get("agents", [])
        for agent in default_agents:
            if "," in agent:
                default_user_agent = agent.split(",")[0]
            else:
                default_user_agent = agent
            if user_agent == default_user_agent:
                return

        # Add to detected clients
        detected_clients.append(user_agent)
        self.set("detected_clients", detected_clients)
        self.logger.debug(f"Added detected client: {user_agent}")

    def get_detected_clients(self):
        """Get list of detected clients"""
        return self.get("detected_clients", [])

    def clear_detected_clients(self):
        """Clear all detected clients"""
        self.set("detected_clients", [])
        self.logger.debug("Cleared all detected clients")
