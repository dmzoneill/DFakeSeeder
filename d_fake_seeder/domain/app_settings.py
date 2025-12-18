# fmt: off
# isort: skip_file
from typing import Dict,  Any
import json
import os
import shutil
import tempfile
from pathlib import Path
from threading import Lock

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import GLib, GObject  # noqa: E402

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
    class Observer:  # type: ignore[no-redef]
        def __init__(self) -> None:
            pass

        def schedule(self, *args: Any, **kwargs: Any) -> Any:
            pass

        def start(self) -> Any:
            pass

        def stop(self) -> Any:
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

    def __new__(cls, *args: Any, **kwargs: Any) -> Any:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize GObject early to avoid "not initialized" errors
            GObject.GObject.__init__(cls._instance)
        return cls._instance

    def __init__(self, file_path: Any = None) -> None:
        # Check if already initialized AND file_path matches
        # This allows re-initialization when file_path changes (e.g., in tests)
        if hasattr(self, "_initialized") and hasattr(self, "_file_path"):
            # If file_path is changing, we need to reinitialize
            if file_path is not None and str(file_path) != str(self._file_path):  # type: ignore[has-type]
                # Stop existing observer before reinitializing
                if hasattr(self, "_observer") and self._observer:  # type: ignore[has-type]
                    try:
                        self._observer.stop()  # type: ignore[has-type]
                        self._observer.join(timeout=1.0)  # type: ignore[has-type]
                    except Exception:
                        pass
                # Clear initialization flag to allow reinitialization
                delattr(self, "_initialized")
            elif file_path is None or str(file_path) == str(self._file_path):  # type: ignore[has-type]
                # Same file path or no file path specified, skip reinitialization
                return

        # GObject.__init__ already called in __new__
        self._initialized = True

        self.logger.trace("AppSettings instantiate", extra={"class_name": self.__class__.__name__})

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
        self.default_config_file = Path(__file__).parent.parent / "config" / "default.json"

        # Three-layer data structure:
        # 1. _defaults: Loaded from default.json, never changes
        # 2. _user_settings: Persistent user preferences (everything except torrents)
        # 3. _transient_data: Runtime-only data (ENTIRE torrents dictionary)
        self._defaults = {}  # type: ignore[var-annotated]
        self._user_settings = {}  # type: ignore[var-annotated]
        self._transient_data: Dict[str, Any] = {}  # ENTIRE torrents dictionary stored here

        # Merged view for reading (rebuilt when any layer changes)
        self._settings: Dict[str, Any] = {}  # Legacy compatibility - will be merged view

        # File watching state
        self._last_modified = 0
        self._save_timer = None  # Debounce timer for queued saves
        self._pending_save = False  # Flag for pending save operations

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
                self.logger.trace(
                    f"Using system-wide config from {source_path}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                source_path = str(self.default_config_file)
                self.logger.trace(
                    f"Using package default config from {source_path}",
                    extra={"class_name": self.__class__.__name__},
                )

            # Copy the source file to the destination directory
            if os.path.exists(source_path):
                shutil.copy(source_path, home_config_path + "/settings.json")
                self.logger.trace(
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
    def logger(self) -> Any:
        """Get logger instance with lazy import to avoid circular dependency"""
        if AppSettings._logger is None:
            try:
                from d_fake_seeder.lib.logger import logger

                AppSettings._logger = logger
            except ImportError:
                # Fallback to print if logger not available
                import logging
                from d_fake_seeder.lib.logger import add_trace_to_logger

                AppSettings._logger = add_trace_to_logger(logging.getLogger(__name__))  # type: ignore[func-returns-value]  # noqa: E501
        return AppSettings._logger

    @property
    def settings(self) -> Any:
        """
        Backwards compatibility property.
        Returns merged view of all settings (defaults + user + transient).
        NOTE: This is read-only. Use get()/set() methods for access.
        """
        return self._settings

    @property
    def torrents(self) -> Any:
        """
        Convenience property for accessing torrents dictionary.
        Returns transient data directly.
        """
        return self._transient_data

    def _load_defaults(self) -> None:
        """Load default settings from config/default.json"""
        try:
            with open(self.default_config_file, "r") as f:
                self._defaults = json.load(f)
            self.logger.trace(f"Loaded {len(self._defaults)} default settings from {self.default_config_file}")
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

    def _merge_with_defaults(self, user_settings: Any) -> Any:
        """Recursively merge user settings with defaults"""

        def deep_merge(default_dict: Any, user_dict: Any) -> Any:
            result = default_dict.copy()
            for key, value in user_dict.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        return deep_merge(self._defaults, user_settings)

    def _build_merged_view(self) -> None:
        """
        Build merged settings view from three layers:
        1. Defaults (from default.json)
        2. User settings (persistent preferences)
        3. Transient data (torrents dictionary only)

        Returns: Complete merged dictionary
        """
        # Start with defaults
        merged = self._merge_with_defaults(self._user_settings)

        # Add transient data (entire torrents dictionary)
        if self._transient_data:
            merged["torrents"] = self._transient_data

        return merged  # type: ignore[no-any-return]

    def _get_nested_value(self, data: Any, key: Any) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key.split(".")
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return None
        return data

    def _set_nested_value(self, data: Any, key: Any, value: Any) -> Any:
        """Set value in nested dictionary using dot notation"""
        keys = key.split(".")
        for k in keys[:-1]:
            data = data.setdefault(k, {})
        data[keys[-1]] = value

    def load_settings(self) -> None:
        """
        Load settings from disk with three-layer architecture:
        1. Load file from disk
        2. Extract torrents → _transient_data (runtime-only)
        3. Remaining → _user_settings (persistent)
        4. Build merged view = defaults + user_settings + transient_data
        """
        self.logger.trace("Settings load", extra={"class_name": self.__class__.__name__})
        try:
            # Skip reload if we're currently saving (prevents file watch feedback loop)
            if hasattr(self, "_saving") and self._saving:  # type: ignore[has-type]
                self.logger.trace(
                    "Skipping load_settings - save in progress", extra={"class_name": self.__class__.__name__}
                )
                return

            # Skip reload if we have a pending save (queued changes more important)
            if self._pending_save:
                self.logger.trace(
                    "Skipping load_settings - save pending", extra={"class_name": self.__class__.__name__}
                )
                return

            # Check if the file has been modified since last load
            modified = os.path.getmtime(self._file_path)
            if modified > self._last_modified:
                with open(self._file_path, "r") as f:
                    loaded_data = json.load(f)

                # Check if this is initial load (transient data empty)
                is_initial_load = not self._transient_data

                if is_initial_load:
                    # INITIAL LOAD: Extract torrents to transient
                    self._transient_data = loaded_data.pop("torrents", {})
                    self.logger.info(
                        f"Initial load: Extracted {len(self._transient_data)} torrents to transient data",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    # RELOAD (file change event): Ignore torrents from disk, keep memory version
                    loaded_data.pop("torrents", None)  # Discard disk torrents
                    self.logger.info(
                        "Reload: Ignoring torrents from disk, keeping {len(self._transient_data)} torrents in memory",
                        extra={"class_name": self.__class__.__name__},
                    )

                # Store remaining data as user settings
                self._user_settings = loaded_data

                # Rebuild merged view
                self._settings = self._build_merged_view()  # type: ignore[func-returns-value]
                self._last_modified = modified  # type: ignore[assignment]

                self.logger.debug(
                    f"Settings loaded - {len(self._user_settings)} user settings, "
                    f"{len(self._transient_data)} transient torrents"
                )

        except FileNotFoundError:
            # If the file doesn't exist, start with defaults and create the file
            self.logger.warning("Settings file not found, creating from defaults")
            self._user_settings = {}
            self._transient_data = {}
            self._settings = self._build_merged_view()  # type: ignore[func-returns-value]

            if not os.path.exists(self._file_path):
                # Create the JSON file with default contents (no torrents yet)
                with open(self._file_path, "w") as f:
                    json.dump(self._defaults, f, indent=4)
                self.logger.info("Created new settings file with defaults")

        except json.JSONDecodeError as e:
            # Handle corrupt/truncated JSON files
            self.logger.error(f"Settings file contains invalid JSON, using defaults: {e}")
            self._user_settings = {}
            self._transient_data = {}
            self._settings = self._build_merged_view()  # type: ignore[func-returns-value]

        except Exception as e:
            self.logger.error(f"Error loading settings: {e}", exc_info=True)

    def _queue_save(self) -> Any:
        """
        Queue a debounced save operation.

        Cancels any existing timer and creates a new one that fires after 1 second.
        This prevents excessive disk writes when settings are changed rapidly.
        """
        logger.trace("Queueing save operation with 1-second debounce", "AppSettings")

        # Set pending save flag to prevent file watcher reload
        self._pending_save = True

        # Cancel any existing save timer
        if self._save_timer is not None:
            logger.trace("Cancelling existing save timer", "AppSettings")
            GLib.source_remove(self._save_timer)
            self._save_timer = None

        # Create new timer that fires after 1 second (1000ms)
        self._save_timer = GLib.timeout_add(1000, self._debounced_save_callback)
        logger.trace(f"Save timer created: {self._save_timer}", "AppSettings")

    def _debounced_save_callback(self) -> Any:
        """
        Callback for debounced save timer.
        Saves settings and clears the pending flag.

        Returns:
            False to remove the timer source (one-shot timer)
        """
        logger.debug("Executing debounced save callback", "AppSettings")

        try:
            self.save_settings()
            logger.info("Debounced save completed successfully", "AppSettings")
        except Exception as e:
            logger.error(f"Error in debounced save: {e}", "AppSettings", exc_info=True)
        finally:
            # Clear pending save flag and timer reference
            self._pending_save = False
            self._save_timer = None
            logger.trace("Pending save flag cleared", "AppSettings")

        # Return False to remove the timer source (one-shot timer)
        return False

    def save_settings(self) -> None:
        """Save current settings to user config file (thread-safe with atomic writes)"""
        self.logger.trace("Settings save", extra={"class_name": self.__class__.__name__})
        try:
            # Use lock to prevent concurrent save operations
            self.logger.trace(
                "About to acquire settings lock",
                extra={"class_name": self.__class__.__name__},
            )
            with AppSettings._lock:
                self.logger.trace(
                    "Settings lock acquired",
                    extra={"class_name": self.__class__.__name__},
                )
                self._save_settings_unlocked()
                self.logger.trace(
                    "Settings saved to disk",
                    extra={"class_name": self.__class__.__name__},
                )
            self.logger.trace("Settings lock released", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}", exc_info=True)

    def _save_settings_unlocked(self) -> None:
        """
        Save current settings without acquiring lock (for internal use when lock already held).

        Saves only _user_settings to disk (persistent preferences).
        Transient data (_transient_data) is NOT saved here - it's merged during save_quit().
        """
        self.config_dir.mkdir(parents=True, exist_ok=True)

        # Set flag to prevent file watch reload during save
        self._saving = True

        # Use atomic write: write to temporary file first, then rename
        # This prevents corruption from incomplete writes during race conditions
        temp_fd = None
        temp_path = None
        try:
            # Create temporary file in same directory as target file
            temp_fd, temp_path = tempfile.mkstemp(dir=str(self.config_dir), prefix=".settings_tmp_", suffix=".json")

            # Write settings to temporary file
            # NOTE: We save _user_settings only (persistent preferences)
            # Transient data (torrents) is NOT included in normal saves
            with os.fdopen(temp_fd, "w") as temp_file:
                json.dump(self._user_settings, temp_file, indent=4)
                temp_file.flush()  # Ensure data is written to disk
                os.fsync(temp_file.fileno())  # Force OS to write to disk

            temp_fd = None  # File is now closed

            # Atomically replace the original file with the temporary file
            # This operation is atomic on POSIX systems, preventing corruption
            os.replace(temp_path, self._file_path)
            temp_path = None  # Successfully moved, don't clean up

            # Update last modified timestamp to prevent unnecessary reloads
            self._last_modified = os.path.getmtime(self._file_path)  # type: ignore[assignment]

            self.logger.info("Settings saved successfully with atomic write")

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
        finally:
            # Clear save flag to allow file watch reload (with small delay to ensure file system settles)
            import time

            time.sleep(0.1)  # 100ms delay to ensure file system events complete
            self._saving = False
            self.logger.trace("Save flag cleared, file watch can reload", extra={"class_name": self.__class__.__name__})

    def save_quit(self) -> None:
        """
        Save settings and stop file watching (Settings API compatibility).

        Merges transient data (torrents) into user_settings before final write.
        This is the ONLY place where transient data is persisted to disk.
        """
        # Cancel any pending debounced save timer
        if self._save_timer is not None:
            GLib.source_remove(self._save_timer)
            self._save_timer = None
            self._pending_save = False

        # Merge transient data (torrents) into user_settings before final write
        with AppSettings._lock:
            if self._transient_data:
                self._user_settings["torrents"] = self._transient_data

        # Stop file watching
        if hasattr(self, "_observer"):
            self._observer.stop()

        # Save merged settings to disk (includes torrents)
        self.save_settings()

    def get(self, key: Any, default: Any = None) -> Any:
        """Get a setting value (supports dot notation for nested values)"""
        # Try nested access first for dot notation keys (e.g., "watch_folder.enabled")
        value = self._get_nested_value(self._settings, key)
        if value is not None:
            return value
        # Fallback to direct key access for backward compatibility
        return self._settings.get(key, default)

    def set(self, key: Any, value: Any) -> Any:
        """
        Set a setting value with automatic transient/persistent routing.

        Transient data (torrents.*): Stored in memory only, no disk write
        Persistent data (everything else): Stored in user_settings, queued for save

        Args:
            key: Setting key (supports dot notation, e.g., "torrents.*.upload_speed")
            value: Setting value
        """
        logger.trace(f"set() called: {key} = {value}", "AppSettings")

        # Determine if this is transient data (entire torrents dictionary)
        is_transient = key == "torrents" or key.startswith("torrents.")

        should_emit = False
        with AppSettings._lock:
            if is_transient:
                # TRANSIENT DATA: Update in-memory only, NO disk write
                logger.trace(f"Transient key detected: {key}", "AppSettings")

                if key == "torrents":
                    # Setting entire torrents dictionary
                    old_value = self._transient_data
                    if old_value != value:
                        self._transient_data = value
                        should_emit = True
                        logger.info(f"Updated entire torrents dict ({len(value)} torrents)", "AppSettings")
                elif "." in key:
                    # Setting specific torrent data (e.g., "torrents./path/to/file.torrent")
                    # Extract torrent file path (everything after "torrents.")
                    torrent_path = key[9:]  # Remove "torrents." prefix

                    # Check if we're setting the entire torrent entry or a nested field
                    if torrent_path and "." not in torrent_path:
                        # Setting entire torrent entry: torrents.<filepath>
                        old_value = self._transient_data.get(torrent_path)  # type: ignore[assignment]
                        if old_value != value:
                            self._transient_data[torrent_path] = value
                            should_emit = True
                            logger.debug(
                                f"Updated torrent entry: {torrent_path[:50]}... (NO disk write)", "AppSettings"
                            )
                    else:
                        # Setting nested field: torrents.<filepath>.<field>
                        old_value = self._get_nested_value({"torrents": self._transient_data}, key)
                        if old_value != value:
                            self._set_nested_value({"torrents": self._transient_data}, key, value)
                            should_emit = True
                            logger.debug(f"Updated transient field: {key} (NO disk write)", "AppSettings")

                # Rebuild merged view to include updated transient data
                self._settings = self._build_merged_view()  # type: ignore[func-returns-value]

            else:
                # PERSISTENT DATA: Update user_settings and queue save
                logger.trace(f"Persistent key detected: {key}", "AppSettings")

                old_value = self._get_nested_value(self._user_settings, key)
                if old_value != value:
                    self._set_nested_value(self._user_settings, key, value)
                    should_emit = True
                    logger.debug(f"Updated persistent: {key}", "AppSettings")

                    # Console output for UI validation
                    print(f"⚙️  SETTING CHANGED: {key} = {value}")

                    # Rebuild merged view
                    self._settings = self._build_merged_view()  # type: ignore[func-returns-value]

                    # Queue debounced save (1 second delay)
                    self._queue_save()
                else:
                    logger.trace("Value unchanged, skipping update", "AppSettings")

        # Emit signals AFTER releasing lock
        if should_emit:
            logger.trace("Emitting change signals", "AppSettings")
            self.emit("settings-value-changed", key, value)
            self.emit("settings-attribute-changed", key, value)
            # Legacy signals
            self.emit("setting-changed", key, value)
            self.emit("attribute-changed", key, value)
            logger.info(f"Setting updated: {key}", "AppSettings")

        logger.trace("set() completed", "AppSettings")

    def __getattr__(self, name: Any) -> Any:
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

    def __setattr__(self, name: Any, value: Any) -> None:
        """
        Dynamic attribute setting (Settings API compatibility).

        DEPRECATED: Use app_settings.set(key, value) instead for explicit settings updates.
        This method is kept for backwards compatibility but may be removed in future versions.
        """
        # Handle private attributes and initialization normally
        if (
            name.startswith("_")
            or name in ["settings", "config_dir", "config_file", "default_config_file"]
            or not hasattr(self, "_initialized")
        ):
            super().__setattr__(name, value)
            return

        # Check if this attribute has a property setter defined in the class
        # If so, delegate to the property setter instead of setting directly
        for cls in type(self).__mro__:
            if name in cls.__dict__:
                attr = cls.__dict__[name]
                if isinstance(attr, property) and attr.fset is not None:
                    # Use the property setter
                    attr.fset(self, value)
                    return

        # Emit deprecation warning for non-property attribute access
        logger.warning(
            f"DEPRECATED: app_settings.{name} = value syntax is deprecated. "
            f"Use app_settings.set('{name}', value) instead.",
            "AppSettings",
        )

        self.logger.trace("Settings __setattr__", extra={"class_name": self.__class__.__name__})

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

    def get_all(self) -> Any:
        """Get all settings as a dict"""
        return self._settings.copy()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        try:
            with self._lock:
                # Load defaults
                self._user_settings = self._defaults.copy()
                # Rebuild merged view
                self._settings = self._build_merged_view()  # type: ignore[func-returns-value]
                # Save to disk
                self._save_settings_unlocked()
                self.logger.debug("Settings reset to defaults")
            # Emit signals for each changed setting
            for key, value in self._defaults.items():
                # Emit new signals
                self.emit("settings-value-changed", key, value)
                self.emit("settings-attribute-changed", key, value)
                # Legacy compatibility signal
                self.emit("setting-changed", key, value)
                self.emit("attribute-changed", key, value)
        except Exception as e:
            self.logger.error(f"Failed to reset settings: {e}")

    def export_settings(self, file_path: str) -> Any:
        """Export current settings to a file"""
        try:
            with self._lock:
                # Export user settings (not including transient data)
                with open(file_path, "w") as f:
                    json.dump(self._user_settings, f, indent=4)
                self.logger.info(f"Settings exported to: {file_path}")
        except Exception as e:
            self.logger.error(f"Failed to export settings: {e}", exc_info=True)
            raise

    def import_settings(self, file_path: str) -> Any:
        """Import settings from a file"""
        try:
            with self._lock:
                # Load settings from file
                with open(file_path, "r") as f:
                    imported_settings = json.load(f)
                # Update user settings
                self._user_settings = imported_settings.copy()
                # Rebuild merged view
                self._settings = self._build_merged_view()  # type: ignore[func-returns-value]
                # Save to disk
                self._save_settings_unlocked()
                self.logger.info(f"Settings imported from: {file_path}")
            # Emit signals for each changed setting
            for key, value in imported_settings.items():
                # Emit new signals
                self.emit("settings-value-changed", key, value)
                self.emit("settings-attribute-changed", key, value)
                # Legacy compatibility signal
                self.emit("setting-changed", key, value)
                self.emit("attribute-changed", key, value)
        except Exception as e:
            self.logger.error(f"Failed to import settings: {e}", exc_info=True)
            raise

    @classmethod
    def get_instance(cls, file_path: Any = None) -> Any:
        """Get singleton instance (Settings API compatibility)"""
        # Note: Can't use self.logger here since this is a class method
        try:
            from d_fake_seeder.lib.logger import logger

            logger.trace("AppSettings get instance", extra={"class_name": "AppSettings"})
        except ImportError:
            pass
        if cls._instance is None:
            cls._instance = cls(file_path)
        return cls._instance

    # Application-specific setting accessors
    @property
    def window_width(self) -> Any:
        return self.get("window_width", 1024)

    @window_width.setter
    def window_width(self, value: Any) -> Any:
        self.set("window_width", value)

    @property
    def window_height(self) -> Any:
        return self.get("window_height", 600)

    @window_height.setter
    def window_height(self, value: Any) -> Any:
        self.set("window_height", value)

    @property
    def remember_window_size(self) -> Any:
        return self.get("remember_window_size", True)

    @remember_window_size.setter
    def remember_window_size(self, value: Any) -> None:
        self.set("remember_window_size", value)

    @property
    def start_minimized(self) -> None:
        return self.get("start_minimized", False)  # type: ignore[no-any-return]

    @start_minimized.setter
    def start_minimized(self, value: Any) -> None:
        self.set("start_minimized", value)

    @property
    def minimize_to_tray(self) -> Any:
        return self.get("minimize_to_tray", False)

    @minimize_to_tray.setter
    def minimize_to_tray(self, value: Any) -> Any:
        self.set("minimize_to_tray", value)

    @property
    def auto_start(self) -> Any:
        return self.get("auto_start", False)

    @auto_start.setter
    def auto_start(self, value: Any) -> Any:
        self.set("auto_start", value)

    @property
    def theme(self) -> Any:
        return self.get("theme", "system")

    @theme.setter
    def theme(self, value: Any) -> Any:
        self.set("theme", value)

    @property
    def language(self) -> Any:
        return self.get("language", "auto")

    @language.setter
    def language(self, value: Any) -> Any:
        self.set("language", value)

    def get_language(self) -> Any:
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
        self.logger.trace(
            f"get_language() - configured_lang from settings: {configured_lang}",
            extra={"class_name": self.__class__.__name__},
        )

        # If it's a specific language (not "auto"), use it directly
        if configured_lang != "auto":
            self.logger.trace(
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
                    system_locale = locale.getdefaultlocale()[0]  # type: ignore[assignment]
            except Exception:
                system_locale = locale.getdefaultlocale()[0]  # type: ignore[assignment]

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
    def listening_port(self) -> Any:
        return self.get("connection.listening_port", NetworkConstants.DEFAULT_PORT)

    @listening_port.setter
    def listening_port(self, value: Any) -> Any:
        self.set("connection.listening_port", value)

    @property
    def enable_upnp(self) -> None:
        return self.get("connection.upnp_enabled", True)  # type: ignore[no-any-return]

    @enable_upnp.setter
    def enable_upnp(self, value: Any) -> None:
        self.set("connection.upnp_enabled", value)

    @property
    def upnp_enabled(self) -> Any:
        return self.get("connection.upnp_enabled", True)

    @upnp_enabled.setter
    def upnp_enabled(self, value: Any) -> Any:
        self.set("connection.upnp_enabled", value)

    @property
    def max_global_connections(self) -> Any:
        return self.get("connection.max_global_connections", 200)

    @max_global_connections.setter
    def max_global_connections(self, value: Any) -> Any:
        self.set("connection.max_global_connections", value)

    @property
    def max_per_torrent(self) -> Any:
        return self.get("connection.max_per_torrent", 50)

    @max_per_torrent.setter
    def max_per_torrent(self, value: Any) -> Any:
        self.set("connection.max_per_torrent", value)

    @property
    def max_upload_slots(self) -> Any:
        return self.get("connection.max_upload_slots", 4)

    @max_upload_slots.setter
    def max_upload_slots(self, value: Any) -> Any:
        self.set("connection.max_upload_slots", value)

    # Proxy settings
    @property
    def proxy_type(self) -> Any:
        return self.get("proxy.type", "none")

    @proxy_type.setter
    def proxy_type(self, value: Any) -> Any:
        self.set("proxy.type", value)

    @property
    def proxy_server(self) -> Any:
        return self.get("proxy.server", "")

    @proxy_server.setter
    def proxy_server(self, value: Any) -> Any:
        self.set("proxy.server", value)

    @property
    def proxy_port(self) -> Any:
        return self.get("proxy.port", 8080)

    @proxy_port.setter
    def proxy_port(self, value: Any) -> Any:
        self.set("proxy.port", value)

    @property
    def proxy_auth_enabled(self) -> Any:
        return self.get("proxy.auth_enabled", False)

    @proxy_auth_enabled.setter
    def proxy_auth_enabled(self, value: Any) -> Any:
        self.set("proxy.auth_enabled", value)

    @property
    def proxy_username(self) -> Any:
        return self.get("proxy.username", "")

    @proxy_username.setter
    def proxy_username(self, value: Any) -> Any:
        self.set("proxy.username", value)

    @property
    def proxy_password(self) -> Any:
        return self.get("proxy.password", "")

    @proxy_password.setter
    def proxy_password(self, value: Any) -> Any:
        self.set("proxy.password", value)

    @property
    def proxies(self) -> dict:
        """
        Get proxy configuration in requests library format.

        Returns:
            Dictionary with http/https proxy URLs, or empty dict if no proxy configured.
        """
        proxy_type = self.get("proxy.type", "none")
        if proxy_type == "none":
            return {}

        server = self.get("proxy.server", "")
        port = self.get("proxy.port", 8080)

        if not server:
            return {}

        # Build auth string if enabled
        auth = ""
        if self.get("proxy.auth_enabled", False):
            username = self.get("proxy.username", "")
            password = self.get("proxy.password", "")
            if username:
                auth = f"{username}:{password}@"

        # Build proxy URL based on type
        if proxy_type == "http":
            proxy_url = f"http://{auth}{server}:{port}"
        elif proxy_type in ("socks4", "socks5"):
            proxy_url = f"{proxy_type}://{auth}{server}:{port}"
        else:
            return {}

        return {
            "http": proxy_url,
            "https": proxy_url,
        }

    # BitTorrent settings
    @property
    def enable_dht(self) -> Any:
        return self.get("bittorrent.enable_dht", True)

    @enable_dht.setter
    def enable_dht(self, value: Any) -> None:
        self.set("bittorrent.enable_dht", value)

    @property
    def enable_pex(self) -> Any:
        return self.get("bittorrent.enable_pex", True)

    @enable_pex.setter
    def enable_pex(self, value: Any) -> None:
        self.set("bittorrent.enable_pex", value)

    @property
    def enable_lpd(self) -> Any:
        return self.get("bittorrent.enable_lpd", True)

    @enable_lpd.setter
    def enable_lpd(self, value: Any) -> None:
        self.set("bittorrent.enable_lpd", value)

    @property
    def encryption_mode(self) -> Any:
        return self.get("bittorrent.encryption_mode", "enabled")

    @encryption_mode.setter
    def encryption_mode(self, value: Any) -> None:
        self.set("bittorrent.encryption_mode", value)

    @property
    def bittorrent_user_agent(self) -> Any:
        return self.get("bittorrent.user_agent", "Deluge/2.0.3 libtorrent/2.0.5.0")

    @bittorrent_user_agent.setter
    def bittorrent_user_agent(self, value: Any) -> None:
        self.set("bittorrent.user_agent", value)

    @property
    def peer_id_prefix(self) -> Any:
        return self.get("bittorrent.peer_id_prefix", "-DE2003-")

    @peer_id_prefix.setter
    def peer_id_prefix(self, value: Any) -> None:
        self.set("bittorrent.peer_id_prefix", value)

    @property
    def bittorrent_announce_interval(self) -> Any:
        return self.get("bittorrent.announce_interval_seconds", 1800)

    @bittorrent_announce_interval.setter
    def bittorrent_announce_interval(self, value: Any) -> None:
        self.set("bittorrent.announce_interval_seconds", value)

    @property
    def bittorrent_min_announce_interval(self) -> Any:
        return self.get("bittorrent.min_announce_interval_seconds", 300)

    @bittorrent_min_announce_interval.setter
    def bittorrent_min_announce_interval(self, value: Any) -> None:
        self.set("bittorrent.min_announce_interval_seconds", value)

    @property
    def bittorrent_scrape_interval(self) -> Any:
        return self.get("bittorrent.scrape_interval_seconds", 900)

    @bittorrent_scrape_interval.setter
    def bittorrent_scrape_interval(self, value: Any) -> None:
        self.set("bittorrent.scrape_interval_seconds", value)

    # Speed settings
    @property
    def upload_limit_kbps(self) -> Any:
        return self.get("speed.upload_limit_kbps", 0)  # 0 = unlimited

    @upload_limit_kbps.setter
    def upload_limit_kbps(self, value: Any) -> None:
        self.set("speed.upload_limit_kbps", value)

    @property
    def download_limit_kbps(self) -> Any:
        return self.get("speed.download_limit_kbps", 0)  # 0 = unlimited

    @download_limit_kbps.setter
    def download_limit_kbps(self, value: Any) -> None:
        self.set("speed.download_limit_kbps", value)

    @property
    def enable_alternative_speeds(self) -> Any:
        return self.get("speed.enable_alternative_speeds", False)

    @enable_alternative_speeds.setter
    def enable_alternative_speeds(self, value: Any) -> None:
        self.set("speed.enable_alternative_speeds", value)

    @property
    def alt_upload_limit_kbps(self) -> Any:
        return self.get("speed.alt_upload_limit_kbps", 50)

    @alt_upload_limit_kbps.setter
    def alt_upload_limit_kbps(self, value: Any) -> None:
        self.set("speed.alt_upload_limit_kbps", value)

    @property
    def alt_download_limit_kbps(self) -> Any:
        return self.get("speed.alt_download_limit_kbps", 100)

    @alt_download_limit_kbps.setter
    def alt_download_limit_kbps(self, value: Any) -> None:
        self.set("speed.alt_download_limit_kbps", value)

    # Scheduler settings
    @property
    def scheduler_enabled(self) -> Any:
        return self.get("scheduler.enabled", False)

    @scheduler_enabled.setter
    def scheduler_enabled(self, value: Any) -> None:
        self.set("scheduler.enabled", value)

    @property
    def scheduler_start_hour(self) -> Any:
        return self.get("scheduler.start_hour", 22)

    @scheduler_start_hour.setter
    def scheduler_start_hour(self, value: Any) -> None:
        self.set("scheduler.start_hour", value)

    @property
    def scheduler_start_minute(self) -> Any:
        return self.get("scheduler.start_minute", 0)

    @scheduler_start_minute.setter
    def scheduler_start_minute(self, value: Any) -> None:
        self.set("scheduler.start_minute", value)

    @property
    def scheduler_end_hour(self) -> Any:
        return self.get("scheduler.end_hour", 6)

    @scheduler_end_hour.setter
    def scheduler_end_hour(self, value: Any) -> None:
        self.set("scheduler.end_hour", value)

    @property
    def scheduler_end_minute(self) -> Any:
        return self.get("scheduler.end_minute", 0)

    @scheduler_end_minute.setter
    def scheduler_end_minute(self, value: Any) -> None:
        self.set("scheduler.end_minute", value)

    @property
    def scheduler_days(self) -> Any:
        return self.get(
            "scheduler.days",
            {
                "monday": True,
                "tuesday": True,
                "wednesday": True,
                "thursday": True,
                "friday": True,
                "saturday": True,
                "sunday": True,
            },
        )

    @scheduler_days.setter
    def scheduler_days(self, value: Any) -> None:
        self.set("scheduler.days", value)

    # Web UI settings
    @property
    def webui_enabled(self) -> Any:
        return self.get("webui.enabled", False)

    @webui_enabled.setter
    def webui_enabled(self, value: Any) -> None:
        self.set("webui.enabled", value)

    @property
    def webui_port(self) -> Any:
        return self.get("webui.port", 8080)

    @webui_port.setter
    def webui_port(self, value: Any) -> None:
        self.set("webui.port", value)

    @property
    def webui_interface(self) -> Any:
        return self.get("webui.interface", "127.0.0.1")

    @webui_interface.setter
    def webui_interface(self, value: Any) -> None:
        self.set("webui.interface", value)

    @property
    def webui_localhost_only(self) -> Any:
        return self.get("webui.localhost_only", True)

    @webui_localhost_only.setter
    def webui_localhost_only(self, value: Any) -> None:
        self.set("webui.localhost_only", value)

    @property
    def webui_https_enabled(self) -> Any:
        return self.get("webui.https_enabled", False)

    @webui_https_enabled.setter
    def webui_https_enabled(self, value: Any) -> None:
        self.set("webui.https_enabled", value)

    @property
    def webui_auth_enabled(self) -> Any:
        return self.get("webui.auth_enabled", True)

    @webui_auth_enabled.setter
    def webui_auth_enabled(self, value: Any) -> None:
        self.set("webui.auth_enabled", value)

    @property
    def webui_username(self) -> Any:
        return self.get("webui.username", "admin")

    @webui_username.setter
    def webui_username(self, value: Any) -> None:
        self.set("webui.username", value)

    @property
    def webui_password(self) -> Any:
        return self.get("webui.password", "")

    @webui_password.setter
    def webui_password(self, value: Any) -> None:
        self.set("webui.password", value)

    @property
    def webui_session_timeout(self) -> Any:
        return self.get("webui.session_timeout_minutes", 60)

    @webui_session_timeout.setter
    def webui_session_timeout(self, value: Any) -> None:
        self.set("webui.session_timeout_minutes", value)

    @property
    def webui_csrf_protection(self) -> Any:
        return self.get("webui.csrf_protection", True)

    @webui_csrf_protection.setter
    def webui_csrf_protection(self, value: Any) -> None:
        self.set("webui.csrf_protection", value)

    @property
    def webui_clickjacking_protection(self) -> Any:
        return self.get("webui.clickjacking_protection", True)

    @webui_clickjacking_protection.setter
    def webui_clickjacking_protection(self, value: Any) -> None:
        self.set("webui.clickjacking_protection", value)

    @property
    def webui_secure_headers(self) -> Any:
        return self.get("webui.secure_headers", True)

    @webui_secure_headers.setter
    def webui_secure_headers(self, value: Any) -> None:
        self.set("webui.secure_headers", value)

    @property
    def webui_host_header_validation(self) -> Any:
        return self.get("webui.host_header_validation", True)

    @webui_host_header_validation.setter
    def webui_host_header_validation(self, value: Any) -> None:
        self.set("webui.host_header_validation", value)

    @property
    def webui_ban_after_failures(self) -> Any:
        return self.get("webui.ban_after_failures", 5)

    @webui_ban_after_failures.setter
    def webui_ban_after_failures(self, value: Any) -> None:
        self.set("webui.ban_after_failures", value)

    # Advanced settings
    @property
    def log_level(self) -> None:
        return self.get("log_level", "INFO")  # type: ignore[no-any-return]

    @log_level.setter
    def log_level(self, value: Any) -> None:
        self.set("log_level", value)

    @property
    def disk_cache_size(self) -> Any:
        return self.get("disk_cache_size", 64)  # MB

    @disk_cache_size.setter
    def disk_cache_size(self, value: Any) -> Any:
        self.set("disk_cache_size", value)

    # Speed distribution settings - Upload
    @property
    def upload_distribution_algorithm(self) -> Any:
        speed_dist = self.get("speed_distribution", {})
        if speed_dist is None or not isinstance(speed_dist, dict):
            return "off"
        upload = speed_dist.get("upload", {})
        if upload is None or not isinstance(upload, dict):
            return "off"
        algorithm = upload.get("algorithm", "off")
        return algorithm

    @upload_distribution_algorithm.setter
    def upload_distribution_algorithm(self, value: Any) -> Any:
        import copy

        self.logger.info(f"🔧 SETTER CALLED: upload_distribution_algorithm = {value}")

        # IMPORTANT: Create a deep copy to avoid in-place modification bug
        # If we modify the original dict, old_value == new_value in set(), preventing save
        old_speed_dist = self.get("speed_distribution", {})
        self.logger.info(f"   Old speed_distribution: {old_speed_dist}")

        speed_dist = copy.deepcopy(old_speed_dist)
        self.logger.info(f"   Deep copied (id changed: {id(old_speed_dist)} -> {id(speed_dist)})")

        # Handle None case (when settings file has null)
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "upload" not in speed_dist:
            speed_dist["upload"] = {}
        speed_dist["upload"]["algorithm"] = value

        self.logger.info(f"   New speed_distribution: {speed_dist}")
        self.logger.info("   Calling self.set('speed_distribution', ...)")
        self.set("speed_distribution", speed_dist)
        self.logger.info("   ✅ self.set() completed")

    @property
    def upload_distribution_spread_percentage(self) -> Any:
        return self.get("speed_distribution", {}).get("upload", {}).get("spread_percentage", 50)

    @upload_distribution_spread_percentage.setter
    def upload_distribution_spread_percentage(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "upload" not in speed_dist:
            speed_dist["upload"] = {}
        speed_dist["upload"]["spread_percentage"] = value
        self.set("speed_distribution", speed_dist)

    @property
    def upload_distribution_redistribution_mode(self) -> Any:
        return self.get("speed_distribution", {}).get("upload", {}).get("redistribution_mode", "tick")

    @upload_distribution_redistribution_mode.setter
    def upload_distribution_redistribution_mode(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "upload" not in speed_dist:
            speed_dist["upload"] = {}
        speed_dist["upload"]["redistribution_mode"] = value
        self.set("speed_distribution", speed_dist)

    @property
    def upload_distribution_custom_interval_minutes(self) -> Any:
        return self.get("speed_distribution", {}).get("upload", {}).get("custom_interval_minutes", 5)

    @upload_distribution_custom_interval_minutes.setter
    def upload_distribution_custom_interval_minutes(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "upload" not in speed_dist:
            speed_dist["upload"] = {}
        speed_dist["upload"]["custom_interval_minutes"] = value
        self.set("speed_distribution", speed_dist)

    # Speed distribution settings - Download
    @property
    def download_distribution_algorithm(self) -> Any:
        return self.get("speed_distribution", {}).get("download", {}).get("algorithm", "off")

    @download_distribution_algorithm.setter
    def download_distribution_algorithm(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "download" not in speed_dist:
            speed_dist["download"] = {}
        speed_dist["download"]["algorithm"] = value
        self.set("speed_distribution", speed_dist)

    @property
    def download_distribution_spread_percentage(self) -> Any:
        return self.get("speed_distribution", {}).get("download", {}).get("spread_percentage", 50)

    @download_distribution_spread_percentage.setter
    def download_distribution_spread_percentage(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "download" not in speed_dist:
            speed_dist["download"] = {}
        speed_dist["download"]["spread_percentage"] = value
        self.set("speed_distribution", speed_dist)

    @property
    def download_distribution_redistribution_mode(self) -> Any:
        return self.get("speed_distribution", {}).get("download", {}).get("redistribution_mode", "tick")

    @download_distribution_redistribution_mode.setter
    def download_distribution_redistribution_mode(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "download" not in speed_dist:
            speed_dist["download"] = {}
        speed_dist["download"]["redistribution_mode"] = value
        self.set("speed_distribution", speed_dist)

    @property
    def download_distribution_custom_interval_minutes(self) -> Any:
        return self.get("speed_distribution", {}).get("download", {}).get("custom_interval_minutes", 5)

    @download_distribution_custom_interval_minutes.setter
    def download_distribution_custom_interval_minutes(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "download" not in speed_dist:
            speed_dist["download"] = {}
        speed_dist["download"]["custom_interval_minutes"] = value
        self.set("speed_distribution", speed_dist)

    # Upload stopped torrents percentage range
    @property
    def upload_distribution_stopped_min_percentage(self) -> Any:
        return self.get("speed_distribution", {}).get("upload", {}).get("stopped_min_percentage", 20)

    @upload_distribution_stopped_min_percentage.setter
    def upload_distribution_stopped_min_percentage(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "upload" not in speed_dist:
            speed_dist["upload"] = {}
        speed_dist["upload"]["stopped_min_percentage"] = value
        self.set("speed_distribution", speed_dist)

    @property
    def upload_distribution_stopped_max_percentage(self) -> Any:
        return self.get("speed_distribution", {}).get("upload", {}).get("stopped_max_percentage", 40)

    @upload_distribution_stopped_max_percentage.setter
    def upload_distribution_stopped_max_percentage(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "upload" not in speed_dist:
            speed_dist["upload"] = {}
        speed_dist["upload"]["stopped_max_percentage"] = value
        self.set("speed_distribution", speed_dist)

    # Download stopped torrents percentage range
    @property
    def download_distribution_stopped_min_percentage(self) -> Any:
        return self.get("speed_distribution", {}).get("download", {}).get("stopped_min_percentage", 20)

    @download_distribution_stopped_min_percentage.setter
    def download_distribution_stopped_min_percentage(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "download" not in speed_dist:
            speed_dist["download"] = {}
        speed_dist["download"]["stopped_min_percentage"] = value
        self.set("speed_distribution", speed_dist)

    @property
    def download_distribution_stopped_max_percentage(self) -> Any:
        return self.get("speed_distribution", {}).get("download", {}).get("stopped_max_percentage", 40)

    @download_distribution_stopped_max_percentage.setter
    def download_distribution_stopped_max_percentage(self, value: Any) -> Any:
        import copy

        speed_dist = copy.deepcopy(self.get("speed_distribution", {}))
        if speed_dist is None or not isinstance(speed_dist, dict):
            speed_dist = {}
        if "download" not in speed_dist:
            speed_dist["download"] = {}
        speed_dist["download"]["stopped_max_percentage"] = value
        self.set("speed_distribution", speed_dist)

    # Client detection methods
    def add_detected_client(self, user_agent: Any) -> None:
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
        self.logger.trace(f"Added detected client: {user_agent}")

    def get_detected_clients(self) -> Any:
        """Get list of detected clients"""
        return self.get("detected_clients", [])

    def clear_detected_clients(self) -> None:
        """Clear all detected clients"""
        self.set("detected_clients", [])
        self.logger.trace("Cleared all detected clients")
