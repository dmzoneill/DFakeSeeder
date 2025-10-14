import os
from urllib.parse import urlparse

import gi  # noqa

gi.require_version("Gdk", "4.0")
gi.require_version("GioUnix", "2.0")
from gi.repository import Gio  # noqa: E402
from gi.repository import GObject, Gtk  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.domain.torrent.model.attributes import Attributes  # noqa: E402
from d_fake_seeder.domain.torrent.model.torrentstate import TorrentState  # noqa: E402
from d_fake_seeder.domain.torrent.torrent import Torrent  # noqa: E402
from d_fake_seeder.domain.translation_manager import create_translation_manager  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.column_translations import ColumnTranslations  # noqa: E402


# Class for handling Torrent data
class Model(GObject.GObject):
    # Define custom signal 'data-changed' which is emitted when torrent data
    # is modified
    __gsignals__ = {
        "data-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (object, object),
        ),
        "selection-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (object, object),
        ),
        "language-changed": (
            GObject.SignalFlags.RUN_FIRST,
            None,
            (str,),
        ),
    }

    def __init__(self):
        GObject.GObject.__init__(self)
        logger.debug("===== Model.__init__ START =====", "Model")
        logger.info("Model instantiate", extra={"class_name": self.__class__.__name__})
        logger.debug("Logger call completed", "Model")
        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        logger.debug("DEBUG: Connecting to AppSettings signals...", "Model")
        logger.debug("DEBUG: AppSettings instance:", "Model")
        # Connect to both new and legacy signals to ensure we catch the change
        try:
            self.settings.connect("settings-attribute-changed", self.handle_settings_changed)
            logger.debug("DEBUG: Connected to 'settings-attribute-changed' signal", "Model")
        except Exception:
            logger.debug("DEBUG: Failed to connect to 'settings-attribute-changed':", "Model")
        try:
            self.settings.connect("attribute-changed", self.handle_settings_changed)
            logger.debug("DEBUG: Connected to 'attribute-changed' signal", "Model")
        except Exception:
            logger.debug("DEBUG: Failed to connect to 'attribute-changed':", "Model")
        logger.debug("DEBUG: AppSettings signal connections completed", "Model")
        # Initialize translation manager
        logger.debug("About to create TranslationManager", "Model")
        self.translation_manager = create_translation_manager(
            domain="dfakeseeder",
            localedir=os.path.join(os.environ.get("DFS_PATH", "."), "components", "locale"),
            fallback_language="en",
        )
        logger.debug("TranslationManager created successfully", "Model")
        # Setup automatic translation
        logger.debug("About to call setup_translations()", "Model")
        try:
            result = self.translation_manager.setup_translations(auto_detect=True)
            logger.debug(f"setup_translations() returned: {result}", "Model")
        except Exception:
            logger.error("Exception in setup_translations()", "Model", exc_info=True)
        # Register translation function with ColumnTranslations to avoid expensive gc.get_objects() calls
        if hasattr(self.translation_manager, "translate_func"):
            ColumnTranslations.register_translation_function(self.translation_manager.translate_func)
            logger.debug("Registered translation function with ColumnTranslations", "Model")
        self.torrent_list = []  # List to hold all torrent instances
        self.torrent_list_attributes = Gio.ListStore.new(Attributes)  # List to hold all Attributes instances
        # Search filtering
        logger.debug("About to initialize search filtering", "Model")
        self.search_filter = ""
        self.filtered_torrent_list_attributes = None
        logger.debug("About to call _setup_filtering()", "Model")
        self._setup_filtering()
        logger.debug("_setup_filtering() completed", "Model")
        logger.debug("===== Model.__init__ COMPLETE =====", "Model")
        logger.info(
            "Model initialization completed successfully",
            extra={"class_name": self.__class__.__name__},
        )

    # Method to add a new torrent
    def add_torrent(self, filepath):
        logger.info("Model add torrent", extra={"class_name": self.__class__.__name__})
        # Create new Torrent instance
        torrent = Torrent(filepath)
        torrent.connect("attribute-changed", self.handle_model_changed)
        self.torrent_list.append(torrent)
        self.torrent_list_attributes.append(torrent.get_attributes())
        current_id = 1
        for torrent in self.torrent_list:
            if torrent.id != current_id:
                torrent.id = current_id
            current_id += 1
        # Update filtered list if search is active
        if self.search_filter:
            self._update_filtered_list()
        # Emit 'data-changed' signal with torrent instance and message
        self.emit("data-changed", torrent, "add")

    # Method to add a new torrent
    def remove_torrent(self, filepath):
        logger.info("Model add torrent", extra={"class_name": self.__class__.__name__})
        # Find the Torrent instance
        torrent = next((t for t in self.torrent_list if t.filepath == filepath), None)
        if torrent is not None:
            self.torrent_list.remove(torrent)
            for index, item in enumerate(self.torrent_list_attributes):
                if item.filepath == torrent.filepath:
                    del self.torrent_list_attributes[index]
                    break
            sorted_list = sorted(self.torrent_list_attributes, key=lambda x: x.id)
            # Sort the list by member attribute 'id'
            for item in sorted_list:
                if item.id <= torrent.id:
                    continue
                item.id -= 1
        # Update filtered list if search is active
        if self.search_filter:
            self._update_filtered_list()
        # Emit 'data-changed' signal with torrent instance and message
        self.emit("data-changed", torrent, "remove")

    # Method to get ListStore of torrents for Gtk.TreeView
    def get_liststore(self):
        logger.debug("Model get_liststore", extra={"class_name": self.__class__.__name__})
        return self.torrent_list_attributes

    def get_torrents(self):
        logger.debug("Model get_torrents", extra={"class_name": self.__class__.__name__})
        return self.torrent_list

    def get_trackers_liststore(self):
        logger.debug(
            "Model get trackers liststore",
            extra={"class_name": self.__class__.__name__},
        )
        tracker_count = {}
        for torrent in self.torrent_list:
            if torrent.is_ready():
                # Get ALL trackers from the torrent file
                all_trackers = torrent.get_torrent_file().get_trackers()
                for tracker_url in all_trackers:
                    try:
                        parsed_url = urlparse(tracker_url)
                        fqdn = parsed_url.hostname
                        if fqdn and fqdn.strip():  # Only count valid hostnames
                            if fqdn in tracker_count:
                                tracker_count[fqdn] += 1
                            else:
                                tracker_count[fqdn] = 1
                    except Exception as e:
                        logger.warning(f"Failed to parse tracker URL {tracker_url}: {e}")
        # Create a list store with the custom GObject type TorrentState
        list_store = Gio.ListStore.new(TorrentState)
        # Sort trackers by count (descending) then by name (ascending)
        sorted_trackers = sorted(tracker_count.items(), key=lambda x: (-x[1], x[0]))
        for fqdn, count in sorted_trackers:
            # Create a new instance of TorrentState and append it to the list store
            list_store.append(TorrentState(fqdn, count))
        logger.info(f"Found {len(sorted_trackers)} unique trackers across all torrents")
        return list_store

    def stop(self, shutdown_tracker=None):
        # Stopping all torrents before quitting
        logger.info(
            f"Stopping {len(self.torrent_list)} torrents",
            extra={"class_name": self.__class__.__name__},
        )
        for torrent in self.torrent_list:
            torrent.stop()
            # Update progress tracker if provided
            if shutdown_tracker:
                shutdown_tracker.mark_completed("model_torrents", 1)
        logger.info("All model torrents stopped", extra={"class_name": self.__class__.__name__})

    # Method to get ListStore of torrents for Gtk.TreeView
    def get_liststore_item(self, index):
        logger.info(
            "Model get list store item",
            extra={"class_name": self.__class__.__name__},
        )
        return self.torrent_list[index]

    def get_torrent_by_attributes(self, attributes):
        """
        Get the Torrent object corresponding to the given Attributes object.
        Args:
            attributes: Attributes object to find corresponding Torrent for
        Returns:
            Torrent object if found, None otherwise
        """
        try:
            if not attributes:
                logger.warning(
                    "No attributes provided to get_torrent_by_attributes",
                    extra={"class_name": self.__class__.__name__},
                )
                return None
            # Get the ID from the attributes object
            torrent_id = getattr(attributes, "id", None)
            if torrent_id is None:
                logger.warning(
                    "Attributes object has no ID",
                    extra={"class_name": self.__class__.__name__},
                )
                return None
            # Find the torrent with matching ID
            for torrent in self.torrent_list:
                if hasattr(torrent, "id") and torrent.id == torrent_id:
                    logger.debug(
                        f"Found torrent {torrent_id} for attributes",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return torrent
            logger.warning(
                f"No torrent found with ID {torrent_id}",
                extra={"class_name": self.__class__.__name__},
            )
            return None
        except Exception as e:
            logger.error(
                f"Error getting torrent by attributes: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    def handle_settings_changed(self, source, key, value):
        logger.debug("===== handle_settings_changed() CALLED =====", "Model")
        logger.debug("DEBUG: Signal received - key='', value=''", "Model")
        logger.debug("DEBUG: Source object:", "Model")
        logger.debug("DEBUG: Source type:", "Model")
        logger.info(
            f"Model settings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )
        # Handle language changes from AppSettings
        if key == "language":
            logger.debug("===== LANGUAGE CHANGE DETECTED =====", "Model")
            logger.debug("New language value: ''", "Model")
            try:
                logger.info(f"Language change detected from AppSettings: {value}")
                logger.debug("About to check translation_manager availability...", "Model")
                # Use the translation manager to switch language
                if hasattr(self, "translation_manager") and self.translation_manager:
                    logger.debug(
                        "Translation manager available, calling switch_language('')",
                        "Model",
                    )
                    actual_lang = self.translation_manager.switch_language(value)
                    logger.debug("switch_language() returned: ''", "Model")
                    logger.info(f"Language switched via translation manager: {actual_lang}")
                    # Update translate function reference
                    logger.debug("Updating translate function reference...", "Model")
                    self.translate_func = self.translation_manager.translate_func
                    logger.debug("Translate function updated", "Model")
                    # CRITICAL: Re-register the NEW translation function with ColumnTranslations
                    # This must happen BEFORE emitting the signal so column components get the new function
                    logger.debug(
                        "About to re-register translation function with ColumnTranslations...",
                        "Model",
                    )
                    if hasattr(self.translation_manager, "translate_func"):
                        ColumnTranslations.register_translation_function(self.translation_manager.translate_func)
                        logger.debug(
                            "Re-registered NEW translation function with ColumnTranslations for language:",
                            "Model",
                        )
                    # Emit our own language-changed signal for UI components
                    logger.debug("About to emit 'language-changed' signal with: ''", "Model")
                    self.emit("language-changed", actual_lang)
                    logger.debug("Successfully emitted language-changed signal:", "Model")
                else:
                    logger.debug("ERROR: Translation manager not available!", "Model")
                    logger.debug("hasattr(self, 'translation_manager'):", "Model")
                    if hasattr(self, "translation_manager"):
                        logger.debug("self.translation_manager:", "Model")
                    logger.error("Translation manager not available for language change")
            except Exception as e:
                logger.error(
                    f"Error handling language change from AppSettings: {e}",
                    "Model",
                    exc_info=True,
                )
        else:
            logger.debug("Non-language setting change:  =", "Model")
        logger.debug("===== handle_settings_changed() COMPLETED =====", "Model")
        # Handle other setting changes as needed
        # Add other key-specific handling here in the future

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.info(
            "Notebook settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        self.emit("data-changed", data_obj, "attribute")

    def _setup_filtering(self):
        """Setup the filtering system for search functionality"""

        # Create a custom filter function
        def search_filter_func(item):
            if not self.search_filter:
                return True
            # Get torrent attributes
            name = getattr(item, "name", "") or ""
            filepath = getattr(item, "filepath", "") or ""
            # Use simple case-insensitive substring matching
            search_lower = self.search_filter.lower()
            return search_lower in name.lower() or search_lower in filepath.lower()

        # Create filter and filter model
        self.filter = Gtk.Filter()
        self.filter.changed = lambda *args: None  # Will be properly implemented
        # We'll create the actual filter model when needed
        self.filter_func = search_filter_func

    def set_search_filter(self, search_text):
        """Set the search filter and update the filtered list"""
        logger.debug(
            f"Setting search filter: '{search_text}'",
            extra={"class_name": self.__class__.__name__},
        )
        self.search_filter = search_text.strip()
        # Update the filtered list
        self._update_filtered_list()
        # Emit signal to notify views
        self.emit("data-changed", None, "filter")

    def _update_filtered_list(self):
        """Update the filtered torrent list based on current search filter"""
        if not self.search_filter:
            # No filter - show all torrents
            self.filtered_torrent_list_attributes = self.torrent_list_attributes
            return
        # Create a new ListStore for filtered results
        self.filtered_torrent_list_attributes = Gio.ListStore.new(Attributes)
        # Use simple case-insensitive substring matching
        search_lower = self.search_filter.lower()

        # Filter torrents based on search criteria
        for i in range(self.torrent_list_attributes.get_n_items()):
            item = self.torrent_list_attributes.get_item(i)
            name = getattr(item, "name", "") or ""
            filepath = getattr(item, "filepath", "") or ""
            # Check if torrent matches search filter using case-insensitive substring matching
            if search_lower in name.lower() or search_lower in filepath.lower():
                self.filtered_torrent_list_attributes.append(item)
        logger.debug(
            f"Filtered {self.torrent_list_attributes.get_n_items()} torrents to "
            f"{self.filtered_torrent_list_attributes.get_n_items()} results",
            extra={"class_name": self.__class__.__name__},
        )

    def get_filtered_liststore(self):
        """Get the filtered ListStore for display"""
        if self.filtered_torrent_list_attributes is None:
            return self.torrent_list_attributes
        return self.filtered_torrent_list_attributes

    def switch_language(self, lang_code: str):
        """Switch language and notify views"""
        with logger.performance.operation_context("model_switch_language", "Model"):
            logger.debug(f"switch_language() called with: {lang_code}", "Model")
            logger.info(
                f"Switching language to: {lang_code}",
                extra={"class_name": self.__class__.__name__},
            )
            # Check widget registration before switching
            widget_count = len(self.translation_manager.translatable_widgets) if self.translation_manager else 0
            logger.debug(
                f"TranslationManager has {widget_count} registered widgets before switch",
                "Model",
            )
            logger.info(
                f"TranslationManager has {widget_count} registered widgets before switch",
                extra={"class_name": self.__class__.__name__},
            )
            # Call the TranslationManager's switch_language method
            with logger.performance.operation_context("translation_switch", "Model"):
                logger.debug("Calling TranslationManager.switch_language()", "Model")
                actual_lang = self.translation_manager.switch_language(lang_code)
                logger.info(
                    f"TranslationManager.switch_language returned: {actual_lang}",
                    extra={"class_name": self.__class__.__name__},
                )
            # Check widget registration after switching
            widget_count = len(self.translation_manager.translatable_widgets) if self.translation_manager else 0
            logger.debug(
                f"TranslationManager has {widget_count} registered widgets after switch",
                "Model",
            )
            logger.info(
                f"TranslationManager has {widget_count} registered widgets after switch",
                extra={"class_name": self.__class__.__name__},
            )
            # TranslationManager.switch_language() already calls refresh_all_translations() internally
            # No need to call it manually here to avoid infinite loops
            # Re-register the NEW translation function with ColumnTranslations
            # This is critical - the translation function changes when language changes!
            with logger.performance.operation_context("translation_reregister", "Model"):
                if hasattr(self.translation_manager, "translate_func"):
                    ColumnTranslations.register_translation_function(self.translation_manager.translate_func)
                    logger.debug(
                        f"Re-registered NEW translation function with ColumnTranslations for language: {lang_code}",
                        "Model",
                    )
            # Emit signal for any manual handling needed
            with logger.performance.operation_context("language_signal_emit", "Model"):
                logger.debug("Emitting language-changed signal", "Model")
                self.emit("language-changed", actual_lang)
            logger.debug("Language switch completed", "Model")
            logger.info(
                f"Language switched to: {actual_lang}, signal emitted",
                extra={"class_name": self.__class__.__name__},
            )
            return actual_lang

    def get_translate_func(self):
        """Get current translation function for manual translations"""
        return self.translation_manager.translate_func

    def get_supported_languages(self):
        """Get set of supported language codes"""
        return self.translation_manager.get_supported_languages()

    def get_current_language(self):
        """Get current language code"""
        return self.translation_manager.get_current_language()
