"""
Main settings dialog component.
Coordinates all settings tabs and provides the main settings interface.
"""

# isort: skip_file

# fmt: off
import os
from typing import Any, Dict, List

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa

from d_fake_seeder.domain.app_settings import AppSettings  # noqa
from d_fake_seeder.lib.logger import logger  # noqa

# Import tab configuration system
from d_fake_seeder.lib.util.tab_config import get_config_metadata  # noqa
from d_fake_seeder.lib.util.tab_config import get_settings_tab_classes  # noqa: E402

# Component inheritance removed - settings dialog should not be a general model observer
from .advanced_tab import AdvancedTab  # noqa
from .bittorrent_tab import BitTorrentTab  # noqa
from .connection_tab import ConnectionTab  # noqa
from .dht_tab import DHTTab  # noqa

# Import all tab classes  # noqa
from .general_tab import GeneralTab  # noqa
from .peer_protocol_tab import PeerProtocolTab  # noqa
from .protocol_extensions_tab import ProtocolExtensionsTab  # noqa
from .simulation_tab import SimulationTab  # noqa
from .speed_tab import SpeedTab  # noqa
from .webui_tab import WebUITab  # noqa

# fmt: on


class SettingsDialog:
    """
    Main settings dialog with tabbed interface.
    Coordinates multiple settings tabs and manages the overall settings experience.
    Uses composition pattern with specialized tab classes for maintainability.
    """

    def __init__(self, parent_window, app=None, model=None):
        """Initialize the settings dialog."""
        logger.debug("===== SettingsDialog.__init__ START =====", "SettingsDialog")
        logger.debug("parent_window:", "SettingsDialog")
        logger.debug("app:", "SettingsDialog")
        logger.debug("model:", "SettingsDialog")
        # Initialize dialog (no Component inheritance - settings don't need general model observation)
        logger.debug("super().__init__() completed", "SettingsDialog")
        logger.debug("startup", extra={"class_name": self.__class__.__name__})
        logger.debug("Setting instance variables", "SettingsDialog")
        self.parent_window = parent_window
        self.app = app
        self.model = model
        logger.debug("About to get AppSettings instance", "SettingsDialog")
        self.app_settings = AppSettings.get_instance()
        logger.debug("AppSettings instance:", "SettingsDialog")

        # Connect to AppSettings changes for theme updates
        self.app_settings.connect("attribute-changed", self._on_app_settings_changed)
        logger.debug("Connected to AppSettings attribute-changed signal", "SettingsDialog")

        # Load the settings UI
        logger.debug("Creating Gtk.Builder", "SettingsDialog")
        self.builder = Gtk.Builder()
        logger.debug("About to load UI file", "SettingsDialog")
        ui_file_path = os.environ.get("DFS_PATH") + "/components/ui/generated/settings_generated.xml"
        logger.debug("UI file path:", "SettingsDialog")
        logger.debug("UI file exists:", "SettingsDialog")
        self.builder.add_from_file(ui_file_path)
        logger.debug("UI file loaded successfully", "SettingsDialog")
        # Get main window
        logger.debug("Getting settings_window from builder", "SettingsDialog")
        self.window = self.builder.get_object("settings_window")
        logger.debug("Settings window:", "SettingsDialog")

        # Apply dark mode class if currently in dark mode
        ui_settings = self.app_settings.get("ui_settings", {})
        color_scheme = ui_settings.get("color_scheme", "auto")
        if color_scheme == "dark":
            self.window.add_css_class("dark")
            logger.debug("Added 'dark' CSS class to settings dialog", "SettingsDialog")

        logger.debug("Setting transient parent", "SettingsDialog")
        self.window.set_transient_for(parent_window)
        logger.debug("Setting modal to False", "SettingsDialog")
        self.window.set_modal(False)
        logger.debug("Window setup completed", "SettingsDialog")
        # Get notebook for tab management
        self.notebook = self.builder.get_object("settings_notebook")
        # Initialize all tab components
        self.tabs: List[Any] = []
        self._initialize_tabs()
        # Connect window signals
        logger.debug("About to connect window signals", "SettingsDialog")
        self._connect_window_signals()
        logger.debug("Window signals connected", "SettingsDialog")
        # Setup global keyboard shortcuts
        logger.debug("About to setup global shortcuts", "SettingsDialog")
        self._setup_global_shortcuts()
        logger.debug("Global shortcuts setup completed", "SettingsDialog")
        # Pass model to tabs if available
        if self.model:
            logger.debug(
                "Storing model reference for tabs and enabling dropdown translation",
                "SettingsDialog",
            )
            # Store model reference and enable dropdown translation for all tabs
            for tab in self.tabs:
                tab.model = self.model
                # Special handling for GeneralTab language dropdown
                if (
                    hasattr(tab, "tab_name")
                    and tab.tab_name == "General"
                    and hasattr(tab, "_populate_language_dropdown")
                ):
                    logger.debug(
                        "Populating language dropdown for GeneralTab with signal safety",
                        "SettingsDialog",
                    )
                    try:
                        # Set initialization flag to prevent signal handling during setup
                        tab._initializing = True
                        tab._populate_language_dropdown()
                    except Exception:
                        logger.debug("Error populating language dropdown:", "SettingsDialog")
                # Enable dropdown translation for all tabs that support it
                if hasattr(tab, "update_view"):
                    logger.debug(
                        "Calling update_view for  tab to enable dropdown translation",
                        "SettingsDialog",
                    )
                    try:
                        tab.update_view(self.model, None, None)
                    except Exception:
                        logger.debug("Error calling update_view for :", "SettingsDialog")
            logger.debug(
                "Model references stored and dropdown translation enabled",
                "SettingsDialog",
            )
            # Register settings dialog widgets for translation
            logger.debug("About to register for translation", "SettingsDialog")
            self._register_for_translation()
            logger.debug("Translation registration completed", "SettingsDialog")
        logger.debug(
            "===== SettingsDialog.__init__ COMPLETED SUCCESSFULLY =====",
            "SettingsDialog",
        )

    def _initialize_tabs(self) -> None:
        """Initialize all settings tab components."""
        logger.debug("Starting tab initialization", "SettingsDialog")
        try:
            # Create module mapping for tab configuration
            module_mapping = {
                "GeneralTab": GeneralTab,
                "ConnectionTab": ConnectionTab,
                "PeerProtocolTab": PeerProtocolTab,
                "SpeedTab": SpeedTab,
                "BitTorrentTab": BitTorrentTab,
                "DHTTab": DHTTab,
                "ProtocolExtensionsTab": ProtocolExtensionsTab,
                "SimulationTab": SimulationTab,
                "WebUITab": WebUITab,
                "AdvancedTab": AdvancedTab,
            }
            # Load tab configuration
            try:
                tab_classes = get_settings_tab_classes(module_mapping)
                logger.debug("Loaded  tabs from configuration", "SettingsDialog")
                logger.debug("Configuration metadata:", "SettingsDialog")
            except Exception:
                logger.debug(
                    "Warning: Could not load tab config (), using fallback",
                    "SettingsDialog",
                )
                # Fallback to essential tabs only
                tab_classes = [GeneralTab, ConnectionTab, AdvancedTab]
            for tab_class in tab_classes:
                logger.debug("About to initialize", "SettingsDialog")
                try:
                    # Pass app reference to GeneralTab for UI restart functionality
                    if tab_class.__name__ == "GeneralTab":
                        tab = tab_class(self.builder, self.app_settings, self.app)
                    else:
                        tab = tab_class(self.builder, self.app_settings)

                    # Set back-reference to settings dialog for cross-tab communication
                    tab.settings_dialog = self

                    self.tabs.append(tab)
                    logger.debug("Successfully initialized", "SettingsDialog")
                    # logger.debug(f"Initialized {tab.tab_name} tab")  # Temporarily commented out - causes hang
                except Exception as e:
                    logger.debug("ERROR initializing :", "SettingsDialog")
                    logger.error(f"Error initializing {tab_class.__name__}: {e}")
            logger.debug("Tab initialization completed. Total tabs:", "SettingsDialog")
            logger.debug(f"Initialized {len(self.tabs)} settings tabs")
        except Exception as e:
            logger.error(f"Error initializing settings tabs: {e}")

    def _update_tabs_with_model(self) -> None:
        """Update all tabs with the model reference."""
        try:
            logger.debug("Starting _update_tabs_with_model for  tabs", "SettingsDialog")
            # Special handling for GeneralTab to populate language dropdown
            for i, tab in enumerate(self.tabs):
                logger.debug("Checking tab :", "SettingsDialog")
                if tab.tab_name == "General" and hasattr(tab, "update_view"):
                    logger.debug(
                        "Special handling for GeneralTab to populate language dropdown",
                        "SettingsDialog",
                    )
                    logger.debug(f"Calling update_view on {tab.tab_name} tab for language dropdown")
                    # Just store the model reference and populate language dropdown
                    tab.model = self.model
                    if hasattr(tab, "_populate_language_dropdown"):
                        tab._populate_language_dropdown()
                    logger.debug("Completed language dropdown population for", "SettingsDialog")
                elif hasattr(tab, "update_view"):
                    logger.debug("Storing model reference for  tab", "SettingsDialog")
                    # For other tabs, just store the model reference without calling full update_view
                    tab.model = self.model
                    logger.debug("Model stored for  tab", "SettingsDialog")
            logger.debug("All tabs updated with model", "SettingsDialog")
            logger.debug(f"Updated {len(self.tabs)} tabs with model")
        except Exception as e:
            logger.debug("ERROR in _update_tabs_with_model:", "SettingsDialog")
            logger.error(f"Error updating tabs with model: {e}")

    def _connect_window_signals(self) -> None:
        """Connect window-level signals."""
        try:
            # Window close
            self.window.connect("close-request", self.on_window_close)
            # Notebook page switching
            if self.notebook:
                self.notebook.connect("switch-page", self.on_page_switched)
        except Exception as e:
            logger.error(f"Error connecting window signals: {e}")

    def _on_app_settings_changed(self, app_settings, key: str, value: Any) -> None:
        """Handle AppSettings changes to update dialog theme."""
        try:
            # Only handle color scheme changes
            if key == "ui_settings.color_scheme":
                logger.debug(f"Settings dialog received color scheme change: {value}", "SettingsDialog")
                # Update the dialog window's CSS class to match the new color scheme
                if value == "dark":
                    if not self.window.has_css_class("dark"):
                        self.window.add_css_class("dark")
                        logger.debug("Added 'dark' CSS class to settings dialog", "SettingsDialog")
                else:
                    # Remove dark class for "light" or "auto" modes
                    if self.window.has_css_class("dark"):
                        self.window.remove_css_class("dark")
                        logger.debug("Removed 'dark' CSS class from settings dialog", "SettingsDialog")
        except Exception as e:
            logger.error(f"Error handling app settings change in dialog: {e}", "SettingsDialog")

    def _setup_global_shortcuts(self) -> None:
        """Set up global keyboard shortcuts for the settings dialog."""
        try:
            # Common shortcuts
            shortcuts = {
                "<Ctrl>w": self.close_dialog,
                "<Ctrl>q": self.close_dialog,
                "Escape": self.close_dialog,
                "<Ctrl>r": self.reset_current_tab,
                "<Ctrl>s": self.save_all_settings,
                "<Ctrl>Tab": self.next_tab,
                "<Ctrl><Shift>Tab": self.previous_tab,
            }
            # Set up shortcuts for advanced tab if it has the mixin
            for tab in self.tabs:
                if hasattr(tab, "setup_tab_shortcuts"):
                    tab.setup_tab_shortcuts(shortcuts)
                    break
        except Exception as e:
            logger.error(f"Error setting up global shortcuts: {e}")

    def _register_for_translation(self) -> None:
        """Register settings dialog widgets for translation."""
        try:
            if self.model and hasattr(self.model, "translation_manager"):
                # Get initial widget count
                initial_count = len(self.model.translation_manager.translatable_widgets)
                # Register settings dialog builder widgets
                self.model.translation_manager.scan_builder_widgets(self.builder)
                final_count = len(self.model.translation_manager.translatable_widgets)
                new_widgets = final_count - initial_count
                logger.debug(
                    f"Registered {new_widgets} settings dialog widgets for translation. "
                    f"Total registered widgets: {final_count}",
                    extra={"class_name": self.__class__.__name__},
                )
                # CRITICAL FIX: Refresh translations for newly registered settings widgets
                # This ensures that settings widgets get translated with the correct language
                if new_widgets > 0:
                    logger.debug(
                        "Newly registered settings widgets will be refreshed by debounced system",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Use debounced refresh to avoid cascading refresh operations
                    self.model.translation_manager.refresh_all_translations()
        except Exception as e:
            logger.error(f"Error registering settings dialog for translation: {e}")

    def show(self) -> None:
        """Show the settings dialog."""
        logger.debug("===== show() method called =====", "SettingsDialog")
        logger.debug("self.window:", "SettingsDialog")
        try:
            # Reload settings from app_settings before showing the dialog
            logger.debug("Reloading settings for all tabs", "SettingsDialog")
            self.reload_all_tab_settings()

            logger.debug("About to call self.window.present()", "SettingsDialog")
            self.window.present()
            logger.debug("self.window.present() completed successfully", "SettingsDialog")
            logger.debug("Settings dialog shown")
            # Force translation refresh for settings dialog widgets
            logger.debug("Checking for translation manager", "SettingsDialog")
            if self.model and hasattr(self.model, "translation_manager"):
                logger.debug("Translation manager found", "SettingsDialog")
                # Widget scanning already handles translation registration and refresh
                # No need to force additional refresh to avoid infinite loops
                logger.debug(
                    "Settings dialog shown with translation support",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.debug("No translation manager found", "SettingsDialog")
            logger.debug("show() method completed successfully", "SettingsDialog")
        except Exception as e:
            logger.error(f"Error showing settings dialog: {e}")

    def hide(self) -> None:
        """Hide the settings dialog."""
        try:
            self.window.hide()
            logger.debug("Settings dialog hidden")
        except Exception as e:
            logger.error(f"Error hiding settings dialog: {e}")

    def close_dialog(self) -> None:
        """Close the settings dialog with validation."""
        try:
            # Validate all tabs before closing
            validation_errors = self.validate_all_settings()
            if validation_errors:
                # Show validation errors
                error_message = "Please fix the following errors before closing:\n\n"
                for tab_name, errors in validation_errors.items():
                    error_message += f"{tab_name}:\n"
                    for field, error in errors.items():
                        error_message += f"  - {error}\n"
                    error_message += "\n"
                # TODO: Show error dialog
                logger.warning(f"Settings validation failed: {validation_errors}")
                return
            # Save all settings before closing
            self.save_all_settings()
            self.hide()
        except Exception as e:
            logger.error(f"Error closing settings dialog: {e}")

    def save_all_settings(self) -> Dict[str, Any]:
        """Save settings from all tabs."""
        try:
            all_saved_settings = {}
            for tab in self.tabs:
                try:
                    saved_settings = tab.save_settings()
                    all_saved_settings.update(saved_settings)
                    logger.debug(f"Saved settings for {tab.tab_name} tab")
                except Exception as e:
                    logger.error(f"Error saving {tab.tab_name} tab settings: {e}")
            logger.debug(f"Saved settings from {len(self.tabs)} tabs")
            return all_saved_settings
        except Exception as e:
            logger.error(f"Error saving all settings: {e}")
            return {}

    def validate_all_settings(self) -> Dict[str, Dict[str, str]]:
        """Validate settings from all tabs."""
        try:
            all_validation_errors = {}
            for tab in self.tabs:
                try:
                    validation_errors = tab.validate_settings()
                    if validation_errors:
                        all_validation_errors[tab.tab_name] = validation_errors
                except Exception as e:
                    logger.error(f"Error validating {tab.tab_name} tab settings: {e}")
                    all_validation_errors[tab.tab_name] = {"general": str(e)}
            return all_validation_errors
        except Exception as e:
            logger.error(f"Error validating all settings: {e}")
            return {"general": {"error": str(e)}}

    def reset_current_tab(self) -> None:
        """Reset the currently active tab to defaults."""
        try:
            if not self.notebook:
                return
            current_page = self.notebook.get_current_page()
            if 0 <= current_page < len(self.tabs):
                tab = self.tabs[current_page]
                tab.reset_to_defaults()
                logger.debug(f"Reset {tab.tab_name} tab to defaults")
        except Exception as e:
            logger.error(f"Error resetting current tab: {e}")

    def reset_all_tabs(self) -> None:
        """Reset all tabs to default values."""
        try:
            for tab in self.tabs:
                try:
                    tab.reset_to_defaults()
                    logger.debug(f"Reset {tab.tab_name} tab to defaults")
                except Exception as e:
                    logger.error(f"Error resetting {tab.tab_name} tab: {e}")
            logger.debug("Reset all settings tabs to defaults")
        except Exception as e:
            logger.error(f"Error resetting all tabs: {e}")

    def next_tab(self) -> None:
        """Switch to the next tab."""
        try:
            if not self.notebook:
                return
            current_page = self.notebook.get_current_page()
            total_pages = self.notebook.get_n_pages()
            next_page = (current_page + 1) % total_pages
            self.notebook.set_current_page(next_page)
        except Exception as e:
            logger.error(f"Error switching to next tab: {e}")

    def previous_tab(self) -> None:
        """Switch to the previous tab."""
        try:
            if not self.notebook:
                return
            current_page = self.notebook.get_current_page()
            total_pages = self.notebook.get_n_pages()
            previous_page = (current_page - 1) % total_pages
            self.notebook.set_current_page(previous_page)
        except Exception as e:
            logger.error(f"Error switching to previous tab: {e}")

    def get_tab_by_name(self, tab_name: str) -> Any:
        """Get a specific tab by name."""
        try:
            for tab in self.tabs:
                if tab.tab_name == tab_name:
                    return tab
            return None
        except Exception as e:
            logger.error(f"Error getting tab by name {tab_name}: {e}")
            return None

    def switch_to_tab(self, tab_name: str) -> bool:
        """Switch to a specific tab by name."""
        try:
            for i, tab in enumerate(self.tabs):
                if tab.tab_name == tab_name:
                    if self.notebook:
                        self.notebook.set_current_page(i)
                        return True
            return False
        except Exception as e:
            logger.error(f"Error switching to tab {tab_name}: {e}")
            return False

    # Signal handlers
    def on_window_close(self, window) -> bool:
        """Handle window close request."""
        try:
            # Skip validation on close - just save and close
            logger.debug("Settings window close requested")
            self.save_all_settings()

            # Clean up all tabs to prevent memory leaks
            logger.debug(f"Cleaning up {len(self.tabs)} settings tabs")
            for tab in self.tabs:
                if hasattr(tab, "cleanup"):
                    try:
                        tab.cleanup()
                    except Exception as e:
                        logger.warning(f"Error cleaning up tab: {e}")

            self.hide()
            return False  # Allow default close behavior
        except Exception as e:
            logger.error(f"Error handling window close: {e}")
            return False  # Allow close even if there was an error

    def on_page_switched(self, notebook: Gtk.Notebook, page: Gtk.Widget, page_num: int) -> None:
        """Handle notebook page switch."""
        try:
            if 0 <= page_num < len(self.tabs):
                tab = self.tabs[page_num]
                logger.debug(f"Switched to {tab.tab_name} tab")
                # Update tab dependencies when switching
                tab.update_dependencies()
        except Exception as e:
            logger.error(f"Error handling page switch: {e}")

    # Utility methods for external access
    def get_current_tab(self) -> Any:
        """Get the currently active tab."""
        try:
            if not self.notebook:
                return None
            current_page = self.notebook.get_current_page()
            if 0 <= current_page < len(self.tabs):
                return self.tabs[current_page]
            return None
        except Exception as e:
            logger.error(f"Error getting current tab: {e}")
            return None

    def get_all_tab_names(self) -> List[str]:
        """Get names of all tabs."""
        try:
            return [tab.tab_name for tab in self.tabs]
        except Exception as e:
            logger.error(f"Error getting tab names: {e}")
            return []

    def export_settings(self) -> Dict[str, Any]:
        """Export all settings from all tabs."""
        try:
            exported_settings = {}
            for tab in self.tabs:
                try:
                    tab_settings = tab._collect_settings()
                    exported_settings.update(tab_settings)
                except Exception as e:
                    logger.error(f"Error exporting {tab.tab_name} tab settings: {e}")
            return exported_settings
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return {}

    def reload_all_tab_settings(self) -> bool:
        """Reload settings from app_settings for all tabs."""
        try:
            success = True
            for tab in self.tabs:
                try:
                    # Reload settings for each tab
                    tab._load_settings()
                except Exception as e:
                    logger.error(
                        f"Error reloading settings for {tab.tab_name} tab: {e}",
                        exc_info=True,
                    )
                    success = False
            return success
        except Exception as e:
            logger.error(f"Error reloading tab settings: {e}", exc_info=True)
            return False

    def import_settings(self, settings: Dict[str, Any]) -> bool:
        """Import settings to all relevant tabs."""
        try:
            success = True
            for tab in self.tabs:
                try:
                    # Reload settings for each tab
                    tab._load_settings()
                    tab.update_dependencies()
                except Exception as e:
                    logger.error(f"Error importing settings to {tab.tab_name} tab: {e}")
                    success = False
            return success
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False
