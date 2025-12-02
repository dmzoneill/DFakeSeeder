# fmt: off
# isort: skip_file
import math
import os
import shutil
import traceback

import gi

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings

# Translation function will be provided by model's TranslationManager
from d_fake_seeder.lib.logger import logger

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa

# fmt: on


class Toolbar(Component):
    def __init__(self, builder, model, app):
        super().__init__()
        with logger.performance.operation_context("toolbar_init", self.__class__.__name__):
            logger.debug("Toolbar.__init__ START", self.__class__.__name__)
            logger.debug("Toolbar startup", self.__class__.__name__)
            logger.debug("Logger call completed", self.__class__.__name__)
            logger.debug("About to set builder, model, app attributes", self.__class__.__name__)
            self.builder = builder
            self.model = model
            self.app = app
            self.settings_dialog = None  # Track existing settings dialog
            logger.debug("Basic attributes set successfully", self.__class__.__name__)
            # subscribe to settings changed
            with logger.performance.operation_context("settings_setup", self.__class__.__name__):
                logger.debug("About to get AppSettings instance", self.__class__.__name__)
                try:
                    self.settings = AppSettings.get_instance()
                    logger.debug(
                        "AppSettings instance obtained successfully",
                        self.__class__.__name__,
                    )
                    logger.debug(
                        "About to connect settings changed signal",
                        self.__class__.__name__,
                    )
                    self.track_signal(
                        self.settings,
                        self.settings.connect("attribute-changed", self.handle_settings_changed),
                    )
                    logger.debug(
                        "Settings signal connected successfully",
                        self.__class__.__name__,
                    )
                except Exception as e:
                    logger.debug(f"ERROR getting AppSettings: {e}", self.__class__.__name__)
                    self.settings = None
                    logger.debug(
                        "Continuing without AppSettings connection",
                        self.__class__.__name__,
                    )
            with logger.performance.operation_context("toolbar_buttons_setup", self.__class__.__name__):
                logger.debug("About to get toolbar_add button", self.__class__.__name__)
                self.toolbar_add_button = self.builder.get_object("toolbar_add")
                logger.debug("Got toolbar_add button successfully", self.__class__.__name__)
                self.track_signal(
                    self.toolbar_add_button,
                    self.toolbar_add_button.connect("clicked", self.on_toolbar_add_clicked),
                )
                self.toolbar_add_button.add_css_class("flat")
                logger.debug("toolbar_add button setup completed", self.__class__.__name__)
        logger.debug("About to get toolbar_remove button", "Toolbar")
        self.toolbar_remove_button = self.builder.get_object("toolbar_remove")
        logger.debug("Got toolbar_remove button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_remove_button,
            self.toolbar_remove_button.connect("clicked", self.on_toolbar_remove_clicked),
        )
        self.toolbar_remove_button.add_css_class("flat")
        logger.debug("toolbar_remove button setup completed", "Toolbar")
        logger.debug("About to get toolbar_search button", "Toolbar")
        self.toolbar_search_button = self.builder.get_object("toolbar_search")
        logger.debug("Got toolbar_search button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_search_button,
            self.toolbar_search_button.connect("clicked", self.on_toolbar_search_clicked),
        )
        self.toolbar_search_button.add_css_class("flat")
        logger.debug("toolbar_search button setup completed", "Toolbar")
        logger.debug("About to get toolbar_search_entry", "Toolbar")
        self.toolbar_search_entry = self.builder.get_object("toolbar_search_entry")
        logger.debug("Got toolbar_search_entry successfully", "Toolbar")
        self.track_signal(
            self.toolbar_search_entry,
            self.toolbar_search_entry.connect("changed", self.on_search_entry_changed),
        )
        logger.debug("toolbar_search_entry connect completed", "Toolbar")
        # Create focus event controller for handling focus loss
        logger.debug("About to create focus controller", "Toolbar")
        from gi.repository import Gtk

        focus_controller = Gtk.EventControllerFocus()
        self.track_signal(
            focus_controller,
            focus_controller.connect("leave", self.on_search_entry_focus_out),
        )
        self.toolbar_search_entry.add_controller(focus_controller)
        self.search_visible = False
        logger.debug("Focus controller setup completed", "Toolbar")
        logger.debug("About to get toolbar_pause button", "Toolbar")
        self.toolbar_pause_button = self.builder.get_object("toolbar_pause")
        logger.debug("Got toolbar_pause button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_pause_button,
            self.toolbar_pause_button.connect("clicked", self.on_toolbar_pause_clicked),
        )
        self.toolbar_pause_button.add_css_class("flat")
        logger.debug("toolbar_pause button setup completed", "Toolbar")
        logger.debug("About to get toolbar_resume button", "Toolbar")
        self.toolbar_resume_button = self.builder.get_object("toolbar_resume")
        logger.debug("Got toolbar_resume button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_resume_button,
            self.toolbar_resume_button.connect("clicked", self.on_toolbar_resume_clicked),
        )
        self.toolbar_resume_button.add_css_class("flat")
        logger.debug("toolbar_resume button setup completed", "Toolbar")
        logger.debug("About to get toolbar_up button", "Toolbar")
        self.toolbar_up_button = self.builder.get_object("toolbar_up")
        logger.debug("Got toolbar_up button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_up_button,
            self.toolbar_up_button.connect("clicked", self.on_toolbar_up_clicked),
        )
        self.toolbar_up_button.add_css_class("flat")
        logger.debug("toolbar_up button setup completed", "Toolbar")
        logger.debug("About to get toolbar_down button", "Toolbar")
        self.toolbar_down_button = self.builder.get_object("toolbar_down")
        logger.debug("Got toolbar_down button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_down_button,
            self.toolbar_down_button.connect("clicked", self.on_toolbar_down_clicked),
        )
        self.toolbar_down_button.add_css_class("flat")
        logger.debug("toolbar_down button setup completed", "Toolbar")
        logger.debug("About to get toolbar_settings button", "Toolbar")
        try:
            logger.debug("Calling self.builder.get_object('toolbar_settings')", "Toolbar")
            self.toolbar_settings_button = self.builder.get_object("toolbar_settings")
            logger.debug("get_object call completed successfully", "Toolbar")
        except Exception:
            logger.debug("ERROR in get_object:", "Toolbar")
            logger.debug("Exception type:", "Toolbar")
            logger.debug("Full traceback:", "Toolbar")
            self.toolbar_settings_button = None
        logger.debug("Got toolbar_settings button successfully", "Toolbar")
        logger.debug(
            "=== SETTINGS BUTTON SETUP ===",
            extra={"class_name": self.__class__.__name__},
        )
        logger.debug(
            f"toolbar_settings_button object: {self.toolbar_settings_button}",
            extra={"class_name": self.__class__.__name__},
        )
        if self.toolbar_settings_button:
            logger.debug("Settings button found, connecting signal", "Toolbar")
            logger.debug(
                "Settings button found and connecting signal",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug(
                "About to connect clicked signal to on_toolbar_settings_clicked",
                "Toolbar",
            )
            signal_id = self.toolbar_settings_button.connect("clicked", self.on_toolbar_settings_clicked)
            self.track_signal(
                self.toolbar_settings_button,
                signal_id,
            )
            logger.debug("Signal connected successfully with ID:", "Toolbar")
            logger.debug(
                f"Signal connected with ID: {signal_id}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug("About to add CSS class 'flat'", "Toolbar")
            self.toolbar_settings_button.add_css_class("flat")
            logger.debug("CSS class 'flat' added successfully", "Toolbar")
            logger.debug(
                "CSS class 'flat' added to settings button",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug("Settings button setup completed successfully", "Toolbar")
        else:
            logger.debug("ERROR: Settings button not found in UI", "Toolbar")
            logger.error(
                "Settings button not found in UI",
                extra={"class_name": self.__class__.__name__},
            )
        logger.debug("About to get toolbar_refresh_rate", "Toolbar")
        self.toolbar_refresh_rate = self.builder.get_object("toolbar_refresh_rate")
        logger.debug("Got toolbar_refresh_rate successfully", "Toolbar")
        logger.debug("About to create Gtk.Adjustment", "Toolbar")
        adjustment = Gtk.Adjustment.new(0, 1, 60, 1, 1, 1)
        logger.debug("Gtk.Adjustment created successfully", "Toolbar")
        logger.debug("About to set step increment", "Toolbar")
        adjustment.set_step_increment(1)
        logger.debug("Step increment set successfully", "Toolbar")
        logger.debug("About to set adjustment", "Toolbar")
        self.toolbar_refresh_rate.set_adjustment(adjustment)
        logger.debug("Adjustment set successfully", "Toolbar")
        logger.debug("About to set digits", "Toolbar")
        self.toolbar_refresh_rate.set_digits(0)
        logger.debug("Digits set successfully", "Toolbar")
        logger.debug("About to connect value-changed signal", "Toolbar")
        logger.debug("Signal connected successfully", "Toolbar")
        logger.debug("About to access self.settings.tickspeed:", "Toolbar")

        # Add event controller for button release to avoid continuous updates during drag
        from gi.repository import Gtk

        button_controller = Gtk.GestureClick()
        self.track_signal(
            button_controller,
            button_controller.connect("released", self.on_toolbar_refresh_rate_released),
        )
        self.toolbar_refresh_rate.add_controller(button_controller)

        try:
            logger.debug("Trying to access self.settings.tickspeed", "Toolbar")
            tickspeed_value = self.settings.tickspeed
            logger.debug("self.settings.tickspeed =", "Toolbar")
            logger.debug("About to call set_value (without signal)", "Toolbar")
            # Set value first without triggering signal to avoid initialization deadlock
            self.toolbar_refresh_rate.set_value(int(tickspeed_value))
            logger.debug("set_value completed, now connecting signal", "Toolbar")
            # Connect value-changed for real-time visual feedback but don't save to settings yet
            self.track_signal(
                self.toolbar_refresh_rate,
                self.toolbar_refresh_rate.connect("value-changed", self.on_toolbar_refresh_rate_preview),
            )
        except Exception:
            logger.debug("ERROR accessing tickspeed:", "Toolbar")
            logger.debug("Using default value of 9", "Toolbar")
            self.toolbar_refresh_rate.set_value(9)
            # Connect signal even on error
            self.track_signal(
                self.toolbar_refresh_rate,
                self.toolbar_refresh_rate.connect("value-changed", self.on_toolbar_refresh_rate_preview),
            )
        logger.debug("set_value completed successfully", "Toolbar")
        logger.debug("About to set size request", "Toolbar")
        self.toolbar_refresh_rate.set_size_request(150, -1)
        logger.debug("toolbar_refresh_rate setup completed", "Toolbar")
        logger.debug("===== Toolbar.__init__ COMPLETE =====", "Toolbar")

    def _(self, text):
        """Get translation function from model's TranslationManager"""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def on_toolbar_refresh_rate_preview(self, scale):
        """Preview changes without saving to settings to avoid UI hanging during drag"""
        # This method is called continuously during drag for visual feedback
        # but doesn't save to settings to prevent UI freezing
        pass

    def on_toolbar_refresh_rate_released(self, gesture, n_press, x, y):
        """Save settings only when user releases the mouse button"""
        value = self.toolbar_refresh_rate.get_value()
        logger.debug(f"Slider released with value: {value}", "Toolbar")
        self.settings.tickspeed = math.ceil(float(value))
        logger.debug(f"Saved tickspeed to settings: {self.settings.tickspeed}", "Toolbar")

    def on_toolbar_add_clicked(self, button):
        logger.debug(
            "Toolbar add button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        self.show_file_selection_dialog()

    def on_toolbar_remove_clicked(self, button):
        logger.debug(
            "Toolbar remove button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        logger.debug(
            "Toolbar remove " + selected.filepath,
            extra={"class_name": self.__class__.__name__},
        )
        logger.debug(
            "Toolbar remove " + str(selected.id),
            extra={"class_name": self.__class__.__name__},
        )
        try:
            os.remove(selected.filepath)
        except Exception as e:
            logger.error(
                f"Error removing torrent file {selected.filepath}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            pass
        self.model.remove_torrent(selected.filepath)

    def on_toolbar_pause_clicked(self, button):
        logger.debug(
            "Toolbar pause button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        selected.active = False
        self.model.emit("data-changed", self.model, selected)

    def on_toolbar_resume_clicked(self, button):
        logger.debug(
            "Toolbar resume button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        selected.active = True
        self.model.emit("data-changed", self.model, selected)

    def on_toolbar_up_clicked(self, button):
        logger.debug(
            "Toolbar up button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        if not selected or selected.id == 1:
            return
        for torrent in self.model.torrent_list:
            if torrent.id == selected.id - 1:
                torrent.id = selected.id
                selected.id -= 1
                self.model.emit("data-changed", self.model, selected)
                self.model.emit("data-changed", self.model, torrent)
                break

    def on_toolbar_down_clicked(self, button):
        logger.debug(
            "Toolbar down button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        if not selected or selected.id == len(self.model.torrent_list):
            return
        for torrent in self.model.torrent_list:
            if torrent.id == selected.id + 1:
                torrent.id = selected.id
                selected.id += 1
                self.model.emit("data-changed", self.model, selected)
                self.model.emit("data-changed", self.model, torrent)
                break

    def on_toolbar_search_clicked(self, button):
        logger.debug(
            "Toolbar search button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        self.toggle_search_entry()

    def on_toolbar_settings_clicked(self, button):
        logger.debug("===== SETTINGS BUTTON CLICKED =====", "Toolbar")
        logger.debug("Button clicked:", "Toolbar")
        logger.debug("Button type:", "Toolbar")
        logger.debug(
            "=== SETTINGS BUTTON CLICKED ===",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            logger.debug("Button object:", "Toolbar")
            logger.debug("Self app:", "Toolbar")
            logger.debug("Self model:", "Toolbar")
            logger.debug("About to call show_settings_dialog()", "Toolbar")
            logger.debug(
                f"Button object: {button}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug(f"Self app: {self.app}", extra={"class_name": self.__class__.__name__})
            logger.debug(
                f"Self model: {self.model}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug(
                "About to call show_settings_dialog()",
                extra={"class_name": self.__class__.__name__},
            )
            self.show_settings_dialog()
            logger.debug("show_settings_dialog() call completed", "Toolbar")
            logger.debug(
                "show_settings_dialog() completed successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.debug("EXCEPTION in on_toolbar_settings_clicked:", "Toolbar")
            logger.debug("Exception type:", "Toolbar")
            logger.error(
                f"ERROR in on_toolbar_settings_clicked: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug("Full traceback:", "Toolbar")
            logger.error(
                f"TRACEBACK: {traceback.format_exc()}",
                extra={"class_name": self.__class__.__name__},
            )

    def show_settings_dialog(self):
        """Show the application settings dialog"""
        logger.debug("===== ENTERING show_settings_dialog =====", "Toolbar")
        logger.debug(
            "=== ENTERING show_settings_dialog ===",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            logger.debug("Current settings_dialog:", "Toolbar")
            logger.debug(
                f"Current settings_dialog: {self.settings_dialog}",
                extra={"class_name": self.__class__.__name__},
            )
            # Check if settings dialog already exists and is visible
            if self.settings_dialog and hasattr(self.settings_dialog, "window"):
                try:
                    logger.debug("Existing settings dialog found, trying to present", "Toolbar")
                    logger.debug(
                        "Existing settings dialog found, trying to present",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Try to present the existing window
                    self.settings_dialog.window.present()
                    logger.debug("Existing settings dialog presented successfully", "Toolbar")
                    logger.debug(
                        "Presenting existing settings dialog",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return
                except Exception as e:
                    logger.debug(
                        "Existing settings dialog invalid: , creating new one",
                        "Toolbar",
                    )
                    logger.debug(f"Existing settings dialog invalid, creating new one: {e}")
                    self.settings_dialog = None
            logger.debug("About to import SettingsDialog", "Toolbar")
            logger.debug(
                "About to import SettingsDialog",
                extra={"class_name": self.__class__.__name__},
            )
            from components.component.settings.settings_dialog import SettingsDialog

            logger.debug("SettingsDialog imported successfully", "Toolbar")
            logger.debug(
                "SettingsDialog imported successfully",
                extra={"class_name": self.__class__.__name__},
            )
            # Get main window from app
            main_window = None
            logger.debug("Checking app: hasattr(self, 'app'):", "Toolbar")
            logger.debug("self.app:", "Toolbar")
            logger.debug(
                f"Checking app: hasattr(self, 'app'): {hasattr(self, 'app')}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug(f"self.app: {self.app}", extra={"class_name": self.__class__.__name__})
            if hasattr(self, "app") and self.app:
                logger.debug("Getting active window from app", "Toolbar")
                logger.debug(
                    "Getting active window from app",
                    extra={"class_name": self.__class__.__name__},
                )
                main_window = self.app.get_active_window()
                logger.debug("Main window found:", "Toolbar")
                logger.debug(
                    f"Main window found: {main_window}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.debug("WARNING: No app or active window found", "Toolbar")
                logger.warning(
                    "No app or active window found",
                    extra={"class_name": self.__class__.__name__},
                )
            # Create and show settings dialog
            logger.debug("Creating new settings dialog with params:", "Toolbar")
            logger.debug("main_window=", "Toolbar")
            logger.debug("app=", "Toolbar")
            logger.debug("model=", "Toolbar")
            logger.debug(
                f"Creating new settings dialog with params: main_window={main_window}, "
                f"app={self.app}, model={self.model}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug("About to call SettingsDialog constructor", "Toolbar")
            self.settings_dialog = SettingsDialog(main_window, self.app, self.model)
            logger.debug("Settings dialog created:", "Toolbar")
            logger.debug(
                f"Settings dialog created: {self.settings_dialog}",
                extra={"class_name": self.__class__.__name__},
            )
            # Connect close signal to clean up reference
            logger.debug("Checking if settings dialog has window attribute", "Toolbar")
            logger.debug(
                "Checking if settings dialog has window attribute",
                extra={"class_name": self.__class__.__name__},
            )
            if hasattr(self.settings_dialog, "window"):
                logger.debug(
                    "Settings dialog has window attribute, connecting close-request signal",
                    "Toolbar",
                )
                logger.debug(
                    "Connecting close-request signal",
                    extra={"class_name": self.__class__.__name__},
                )
                self.track_signal(
                    self.settings_dialog.window,
                    self.settings_dialog.window.connect("close-request", self._on_settings_dialog_closed),
                )
                logger.debug("Close-request signal connected successfully", "Toolbar")
            else:
                logger.debug("WARNING: Settings dialog has no window attribute", "Toolbar")
                logger.warning(
                    "Settings dialog has no window attribute",
                    extra={"class_name": self.__class__.__name__},
                )
            logger.debug("About to call settings_dialog.show()", "Toolbar")
            logger.debug(
                "About to call settings_dialog.show()",
                extra={"class_name": self.__class__.__name__},
            )
            self.settings_dialog.show()
            logger.debug("Settings dialog show() called successfully", "Toolbar")
            logger.debug(
                "Settings dialog show() called successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.debug("EXCEPTION in show_settings_dialog:", "Toolbar")
            logger.debug("Exception type:", "Toolbar")
            logger.error(
                f"FAILED to open settings dialog: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.debug("Full exception traceback:", "Toolbar")
            logger.error(
                f"FULL TRACEBACK: {traceback.format_exc()}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_settings_dialog_closed(self, window):
        """Clean up settings dialog reference when closed"""
        logger.debug(
            "Settings dialog closed, cleaning up reference",
            extra={"class_name": self.__class__.__name__},
        )
        self.settings_dialog = None
        return False  # Allow the window to close

    def on_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            logger.debug(
                "Toolbar file added",
                extra={"class_name": self.__class__.__name__},
            )
            # Get the selected file
            selected_file = dialog.get_file()
            torrents_path = os.path.expanduser("~/.config/dfakeseeder/torrents")
            shutil.copy(os.path.abspath(selected_file.get_path()), torrents_path)
            file_path = selected_file.get_path()
            copied_torrent_path = os.path.join(torrents_path, os.path.basename(file_path))
            self.model.add_torrent(copied_torrent_path)
            dialog.destroy()
        else:
            dialog.destroy()

    def show_file_selection_dialog(self):
        logger.debug("Toolbar file dialog", extra={"class_name": self.__class__.__name__})
        # Create a new file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title=self._("Select torrent"),
            transient_for=self.app.get_active_window(),
            modal=True,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_button(self._("Cancel"), Gtk.ResponseType.CANCEL)
        dialog.add_button(self._("Add"), Gtk.ResponseType.OK)
        filter_torrent = Gtk.FileFilter()
        filter_torrent.set_name(self._("Torrent Files"))
        filter_torrent.add_pattern("*.torrent")
        dialog.add_filter(filter_torrent)
        # Connect the "response" signal to the callback function
        self.track_signal(dialog, dialog.connect("response", self.on_dialog_response))
        # Run the dialog
        dialog.show()

    def get_selected_torrent(self):
        return self.selection

    def update_view(self, model, torrent, attribute):
        pass

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.debug(
            "Toolbar settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        logger.debug(
            "Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def model_selection_changed(self, source, model, torrent):
        logger.debug(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
        self.selection = torrent

    def toggle_search_entry(self):
        """Toggle the visibility of the search entry and handle focus"""
        self.search_visible = not self.search_visible
        self.toolbar_search_entry.set_visible(self.search_visible)
        if self.search_visible:
            # Grab focus when showing the search entry
            self.toolbar_search_entry.grab_focus()
        else:
            # Clear search when hiding
            self.toolbar_search_entry.set_text("")
            # Trigger search clear to show all torrents
            self.on_search_entry_changed(self.toolbar_search_entry)

    def on_search_entry_changed(self, entry):
        """Handle real-time search as user types"""
        search_text = entry.get_text().strip()
        logger.debug(
            f"Search text changed: '{search_text}'",
            extra={"class_name": self.__class__.__name__},
        )
        # Emit search signal to update torrent filtering
        if hasattr(self.model, "set_search_filter"):
            self.model.set_search_filter(search_text)

    def on_search_entry_focus_out(self, controller):
        """Hide search entry when it loses focus"""
        logger.debug(
            "Search entry lost focus",
            extra={"class_name": self.__class__.__name__},
        )
        self.search_visible = False
        self.toolbar_search_entry.set_visible(False)
        # Clear search when hiding
        self.toolbar_search_entry.set_text("")
        # Trigger search clear to show all torrents
        self.on_search_entry_changed(self.toolbar_search_entry)
        return False

    @staticmethod
    def levenshtein_distance(s1, s2):
        """Calculate Levenshtein distance between two strings"""
        from lib.util.helpers import levenshtein_distance as util_levenshtein_distance

        return util_levenshtein_distance(s1, s2)

    @staticmethod
    def fuzzy_match(search_term, target_text, threshold=None):
        """
        Fuzzy match using Levenshtein distance
        Returns True if match is above threshold (0.0 to 1.0)
        """
        from lib.util.helpers import fuzzy_match as util_fuzzy_match

        return util_fuzzy_match(search_term, target_text, threshold)
