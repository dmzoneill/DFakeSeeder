# fmt: off
# isort: skip_file
from typing import Any
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
    def __init__(self, builder: Any, model: Any, app: Any) -> None:
        super().__init__()
        with logger.performance.operation_context("toolbar_init", self.__class__.__name__):
            logger.trace("Toolbar.__init__ START", self.__class__.__name__)
            logger.trace("Toolbar startup", self.__class__.__name__)
            logger.trace("Logger call completed", self.__class__.__name__)
            logger.trace("About to set builder, model, app attributes", self.__class__.__name__)
            self.builder = builder
            self.model = model
            self.app = app
            self.settings_dialog = None  # Track existing settings dialog
            logger.info("Basic attributes set successfully", self.__class__.__name__)
            # subscribe to settings changed
            with logger.performance.operation_context("settings_setup", self.__class__.__name__):
                logger.trace("About to get AppSettings instance", self.__class__.__name__)
                try:
                    self.settings = AppSettings.get_instance()
                    logger.trace(
                        "AppSettings instance obtained successfully",
                        self.__class__.__name__,
                    )
                    logger.trace(
                        "About to connect settings changed signal",
                        self.__class__.__name__,
                    )
                    self.track_signal(
                        self.settings,
                        self.settings.connect("attribute-changed", self.handle_settings_changed),
                    )
                    logger.trace(
                        "Settings signal connected successfully",
                        self.__class__.__name__,
                    )
                except Exception as e:
                    logger.error(f"ERROR getting AppSettings: {e}", self.__class__.__name__)
                    self.settings = None
                    logger.trace(
                        "Continuing without AppSettings connection",
                        self.__class__.__name__,
                    )
            with logger.performance.operation_context("toolbar_buttons_setup", self.__class__.__name__):
                logger.trace("About to get toolbar_add button", self.__class__.__name__)
                self.toolbar_add_button = self.builder.get_object("toolbar_add")
                logger.info("Got toolbar_add button successfully", self.__class__.__name__)
                self.track_signal(
                    self.toolbar_add_button,
                    self.toolbar_add_button.connect("clicked", self.on_toolbar_add_clicked),
                )
                self.toolbar_add_button.add_css_class("flat")
                logger.trace("toolbar_add button setup completed", self.__class__.__name__)
        logger.trace("About to get toolbar_remove button", "Toolbar")
        self.toolbar_remove_button = self.builder.get_object("toolbar_remove")
        logger.info("Got toolbar_remove button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_remove_button,
            self.toolbar_remove_button.connect("clicked", self.on_toolbar_remove_clicked),
        )
        self.toolbar_remove_button.add_css_class("flat")
        logger.trace("toolbar_remove button setup completed", "Toolbar")
        logger.trace("About to get toolbar_search button", "Toolbar")
        self.toolbar_search_button = self.builder.get_object("toolbar_search")
        logger.info("Got toolbar_search button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_search_button,
            self.toolbar_search_button.connect("clicked", self.on_toolbar_search_clicked),
        )
        self.toolbar_search_button.add_css_class("flat")
        logger.trace("toolbar_search button setup completed", "Toolbar")
        logger.trace("About to get toolbar_search_entry", "Toolbar")
        self.toolbar_search_entry = self.builder.get_object("toolbar_search_entry")
        logger.info("Got toolbar_search_entry successfully", "Toolbar")
        self.track_signal(
            self.toolbar_search_entry,
            self.toolbar_search_entry.connect("changed", self.on_search_entry_changed),
        )
        logger.trace("toolbar_search_entry connect completed", "Toolbar")
        # Create focus event controller for handling focus loss
        logger.trace("About to create focus controller", "Toolbar")
        from gi.repository import Gtk

        focus_controller = Gtk.EventControllerFocus()
        self.track_signal(
            focus_controller,
            focus_controller.connect("leave", self.on_search_entry_focus_out),
        )
        self.toolbar_search_entry.add_controller(focus_controller)
        self.search_visible = False
        logger.trace("Focus controller setup completed", "Toolbar")
        logger.trace("About to get toolbar_pause button", "Toolbar")
        self.toolbar_pause_button = self.builder.get_object("toolbar_pause")
        logger.info("Got toolbar_pause button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_pause_button,
            self.toolbar_pause_button.connect("clicked", self.on_toolbar_pause_clicked),
        )
        self.toolbar_pause_button.add_css_class("flat")
        logger.trace("toolbar_pause button setup completed", "Toolbar")
        logger.trace("About to get toolbar_resume button", "Toolbar")
        self.toolbar_resume_button = self.builder.get_object("toolbar_resume")
        logger.info("Got toolbar_resume button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_resume_button,
            self.toolbar_resume_button.connect("clicked", self.on_toolbar_resume_clicked),
        )
        self.toolbar_resume_button.add_css_class("flat")
        logger.trace("toolbar_resume button setup completed", "Toolbar")
        logger.trace("About to get toolbar_up button", "Toolbar")
        self.toolbar_up_button = self.builder.get_object("toolbar_up")
        logger.info("Got toolbar_up button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_up_button,
            self.toolbar_up_button.connect("clicked", self.on_toolbar_up_clicked),
        )
        self.toolbar_up_button.add_css_class("flat")
        logger.trace("toolbar_up button setup completed", "Toolbar")
        logger.trace("About to get toolbar_down button", "Toolbar")
        self.toolbar_down_button = self.builder.get_object("toolbar_down")
        logger.info("Got toolbar_down button successfully", "Toolbar")
        self.track_signal(
            self.toolbar_down_button,
            self.toolbar_down_button.connect("clicked", self.on_toolbar_down_clicked),
        )
        self.toolbar_down_button.add_css_class("flat")
        logger.trace("toolbar_down button setup completed", "Toolbar")
        logger.trace("About to get toolbar_settings button", "Toolbar")
        try:
            logger.trace("Calling self.builder.get_object('toolbar_settings')", "Toolbar")
            self.toolbar_settings_button = self.builder.get_object("toolbar_settings")
            logger.info("get_object call completed successfully", "Toolbar")
        except Exception:
            logger.error("ERROR in get_object:", "Toolbar")
            logger.error("Exception type:", "Toolbar")
            logger.error("Full traceback:", "Toolbar")
            self.toolbar_settings_button = None
        logger.info("Got toolbar_settings button successfully", "Toolbar")
        logger.trace(
            "=== SETTINGS BUTTON SETUP ===",
            extra={"class_name": self.__class__.__name__},
        )
        logger.trace(
            f"toolbar_settings_button object: {self.toolbar_settings_button}",
            extra={"class_name": self.__class__.__name__},
        )
        if self.toolbar_settings_button:
            logger.debug("Settings button found, connecting signal", "Toolbar")
            logger.trace(
                "Settings button found and connecting signal",
                extra={"class_name": self.__class__.__name__},
            )
            logger.trace(
                "About to connect clicked signal to on_toolbar_settings_clicked",
                "Toolbar",
            )
            signal_id = self.toolbar_settings_button.connect("clicked", self.on_toolbar_settings_clicked)
            self.track_signal(
                self.toolbar_settings_button,
                signal_id,
            )
            logger.info("Signal connected successfully with ID:", "Toolbar")
            logger.trace(
                f"Signal connected with ID: {signal_id}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.trace("About to add CSS class 'flat'", "Toolbar")
            self.toolbar_settings_button.add_css_class("flat")
            logger.info("CSS class 'flat' added successfully", "Toolbar")
            logger.trace(
                "CSS class 'flat' added to settings button",
                extra={"class_name": self.__class__.__name__},
            )
            logger.info("Settings button setup completed successfully", "Toolbar")
        else:
            logger.error("ERROR: Settings button not found in UI", "Toolbar")
            logger.error(
                "Settings button not found in UI",
                extra={"class_name": self.__class__.__name__},
            )
        logger.trace("About to get toolbar_refresh_rate", "Toolbar")
        self.toolbar_refresh_rate = self.builder.get_object("toolbar_refresh_rate")
        logger.info("Got toolbar_refresh_rate successfully", "Toolbar")
        logger.trace("About to create Gtk.Adjustment", "Toolbar")
        adjustment = Gtk.Adjustment.new(1, 1, 60, 1, 10, 0)  # Fixed: value=1 (was 0), page_size=0
        logger.info("Gtk.Adjustment created successfully", "Toolbar")
        logger.trace("About to set step increment", "Toolbar")
        adjustment.set_step_increment(1)
        logger.info("Step increment set successfully", "Toolbar")
        logger.trace("About to set adjustment", "Toolbar")
        self.toolbar_refresh_rate.set_adjustment(adjustment)
        logger.info("Adjustment set successfully", "Toolbar")
        logger.trace("About to set digits", "Toolbar")
        self.toolbar_refresh_rate.set_digits(0)
        logger.info("Digits set successfully", "Toolbar")
        logger.trace("About to connect value-changed signal", "Toolbar")
        logger.info("Signal connected successfully", "Toolbar")
        logger.trace("About to access self.settings.tickspeed:", "Toolbar")

        # Track pending save for debounced saving
        self._tickspeed_save_pending = False
        self._tickspeed_save_source_id = None

        try:
            logger.trace("Trying to access self.settings.tickspeed", "Toolbar")
            tickspeed_value = self.settings.get("tickspeed", 9)
            logger.trace(f"self.settings.tickspeed = {tickspeed_value}", "Toolbar")
            logger.trace("About to call set_value", "Toolbar")
            self.toolbar_refresh_rate.set_value(int(tickspeed_value))
            logger.trace("set_value completed, now connecting signal", "Toolbar")
        except Exception as e:
            logger.error(f"ERROR accessing tickspeed: {e}", "Toolbar")
            logger.trace("Using default value of 9", "Toolbar")
            self.toolbar_refresh_rate.set_value(9)

        # Connect value-changed signal - use debounced save to avoid excessive writes
        self.track_signal(
            self.toolbar_refresh_rate,
            self.toolbar_refresh_rate.connect("value-changed", self.on_toolbar_refresh_rate_changed),
        )
        logger.info("set_value completed successfully", "Toolbar")
        logger.trace("About to set size request", "Toolbar")
        self.toolbar_refresh_rate.set_size_request(150, -1)
        logger.trace("toolbar_refresh_rate setup completed", "Toolbar")
        logger.trace("===== Toolbar.__init__ COMPLETE =====", "Toolbar")

    def _(self, text: Any) -> Any:
        """Get translation function from model's TranslationManager"""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def on_toolbar_refresh_rate_changed(self, scale: Any) -> None:
        """Handle refresh rate slider value change with debounced save."""
        from gi.repository import GLib

        # Cancel any pending save
        if self._tickspeed_save_source_id:
            GLib.source_remove(self._tickspeed_save_source_id)
            self._tickspeed_save_source_id = None

        # Schedule a debounced save after 500ms of no changes
        self._tickspeed_save_source_id = GLib.timeout_add(500, self._save_tickspeed_debounced)

    def _save_tickspeed_debounced(self) -> bool:
        """Actually save the tickspeed setting after debounce delay."""
        self._tickspeed_save_source_id = None
        value = self.toolbar_refresh_rate.get_value()
        tickspeed = math.ceil(float(value))
        current = self.settings.get("tickspeed", 9)

        if tickspeed != current:
            self.settings.set("tickspeed", tickspeed)
            logger.trace(f"Saved tickspeed to settings: {tickspeed}", "Toolbar")

        return False  # Don't repeat

    def on_toolbar_add_clicked(self, button: Any) -> None:
        logger.trace(
            "Toolbar add button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        self.show_file_selection_dialog()

    def on_toolbar_remove_clicked(self, button: Any) -> None:
        logger.trace(
            "Toolbar remove button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        logger.trace(
            "Toolbar remove " + selected.filepath,
            extra={"class_name": self.__class__.__name__},
        )
        logger.trace(
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
        self.model.remove_torrent(selected.filepath)  # type: ignore[attr-defined]

    def on_toolbar_pause_clicked(self, button: Any) -> None:
        logger.trace(
            "Toolbar pause button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        selected.active = False
        self.model.emit("data-changed", self.model, selected)  # type: ignore[attr-defined]

    def on_toolbar_resume_clicked(self, button: Any) -> None:
        logger.trace(
            "Toolbar resume button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        selected.active = True
        self.model.emit("data-changed", self.model, selected)  # type: ignore[attr-defined]

    def on_toolbar_up_clicked(self, button: Any) -> None:
        logger.trace(
            "Toolbar up button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        if not selected or selected.id == 1:
            return
        for torrent in self.model.torrent_list:  # type: ignore[attr-defined]
            if torrent.id == selected.id - 1:
                torrent.id = selected.id
                selected.id -= 1
                self.model.emit("data-changed", self.model, selected)  # type: ignore[attr-defined]
                self.model.emit("data-changed", self.model, torrent)  # type: ignore[attr-defined]
                break

    def on_toolbar_down_clicked(self, button: Any) -> None:
        logger.trace(
            "Toolbar down button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        if not selected or selected.id == len(self.model.torrent_list):  # type: ignore[attr-defined]
            return
        for torrent in self.model.torrent_list:  # type: ignore[attr-defined]
            if torrent.id == selected.id + 1:
                torrent.id = selected.id
                selected.id += 1
                self.model.emit("data-changed", self.model, selected)  # type: ignore[attr-defined]
                self.model.emit("data-changed", self.model, torrent)  # type: ignore[attr-defined]
                break

    def on_toolbar_search_clicked(self, button: Any) -> None:
        logger.trace(
            "Toolbar search button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        self.toggle_search_entry()

    def on_toolbar_settings_clicked(self, button: Any) -> None:
        logger.debug("===== SETTINGS BUTTON CLICKED =====", "Toolbar")
        logger.trace("Button clicked:", "Toolbar")
        logger.trace("Button type:", "Toolbar")
        logger.trace(
            "=== SETTINGS BUTTON CLICKED ===",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            logger.trace("Button object:", "Toolbar")
            logger.trace("Self app:", "Toolbar")
            logger.trace("Self model:", "Toolbar")
            logger.trace("About to call show_settings_dialog()", "Toolbar")
            logger.trace(
                f"Button object: {button}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.trace(f"Self app: {self.app}", extra={"class_name": self.__class__.__name__})
            logger.trace(
                f"Self model: {self.model}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.trace(
                "About to call show_settings_dialog()",
                extra={"class_name": self.__class__.__name__},
            )
            self.show_settings_dialog()
            logger.trace("show_settings_dialog() call completed", "Toolbar")
            logger.trace(
                "show_settings_dialog() completed successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error("EXCEPTION in on_toolbar_settings_clicked:", "Toolbar")
            logger.error("Exception type:", "Toolbar")
            logger.error(
                f"ERROR in on_toolbar_settings_clicked: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.error("Full traceback:", "Toolbar")
            logger.error(
                f"TRACEBACK: {traceback.format_exc()}",
                extra={"class_name": self.__class__.__name__},
            )

    def show_settings_dialog(self) -> None:
        """Show the application settings dialog"""
        logger.trace("===== ENTERING show_settings_dialog =====", "Toolbar")
        logger.trace(
            "=== ENTERING show_settings_dialog ===",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            logger.trace("Current settings_dialog:", "Toolbar")
            logger.trace(
                f"Current settings_dialog: {self.settings_dialog}",
                extra={"class_name": self.__class__.__name__},
            )
            # Check if settings dialog already exists and is visible
            if self.settings_dialog and hasattr(self.settings_dialog, "window"):
                try:
                    logger.debug("Existing settings dialog found, trying to present", "Toolbar")
                    logger.trace(
                        "Existing settings dialog found, trying to present",
                        extra={"class_name": self.__class__.__name__},
                    )
                    # Try to present the existing window
                    self.settings_dialog.window.present()
                    logger.info("Existing settings dialog presented successfully", "Toolbar")
                    logger.trace(
                        "Presenting existing settings dialog",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return
                except Exception as e:
                    logger.trace(
                        "Existing settings dialog invalid: , creating new one",
                        "Toolbar",
                    )
                    logger.error(f"Existing settings dialog invalid, creating new one: {e}")
                    self.settings_dialog = None
            logger.trace("About to import SettingsDialog", "Toolbar")
            logger.trace(
                "About to import SettingsDialog",
                extra={"class_name": self.__class__.__name__},
            )
            from components.component.settings.settings_dialog import SettingsDialog

            logger.info("SettingsDialog imported successfully", "Toolbar")
            logger.trace(
                "SettingsDialog imported successfully",
                extra={"class_name": self.__class__.__name__},
            )
            # Get main window from app
            main_window = None
            logger.trace("Checking app: hasattr(self, 'app'):", "Toolbar")
            logger.trace("self.app:", "Toolbar")
            logger.trace(
                f"Checking app: hasattr(self, 'app'): {hasattr(self, 'app')}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.trace(f"self.app: {self.app}", extra={"class_name": self.__class__.__name__})
            if hasattr(self, "app") and self.app:
                logger.trace("Getting active window from app", "Toolbar")
                logger.trace(
                    "Getting active window from app",
                    extra={"class_name": self.__class__.__name__},
                )
                main_window = self.app.get_active_window()
                logger.trace("Main window found:", "Toolbar")
                logger.trace(
                    f"Main window found: {main_window}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning("WARNING: No app or active window found", "Toolbar")
                logger.warning(
                    "No app or active window found",
                    extra={"class_name": self.__class__.__name__},
                )
            # Create and show settings dialog
            logger.trace("Creating new settings dialog with params:", "Toolbar")
            logger.trace("main_window=", "Toolbar")
            logger.trace("app=", "Toolbar")
            logger.trace("model=", "Toolbar")
            logger.trace(
                f"Creating new settings dialog with params: main_window={main_window}, "
                f"app={self.app}, model={self.model}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.trace("About to call SettingsDialog constructor", "Toolbar")
            self.settings_dialog = SettingsDialog(main_window, self.app, self.model)
            logger.info("Settings dialog created:", "Toolbar")
            logger.trace(
                f"Settings dialog created: {self.settings_dialog}",
                extra={"class_name": self.__class__.__name__},
            )
            # Connect close signal to clean up reference
            logger.trace("Checking if settings dialog has window attribute", "Toolbar")
            logger.trace(
                "Checking if settings dialog has window attribute",
                extra={"class_name": self.__class__.__name__},
            )
            if hasattr(self.settings_dialog, "window"):
                logger.trace(
                    "Settings dialog has window attribute, connecting close-request signal",
                    "Toolbar",
                )
                logger.trace(
                    "Connecting close-request signal",
                    extra={"class_name": self.__class__.__name__},
                )
                self.track_signal(
                    self.settings_dialog.window,  # type: ignore[attr-defined]
                    self.settings_dialog.window.connect("close-request", self._on_settings_dialog_closed),  # type: ignore[attr-defined]  # noqa: E501
                )
                logger.info("Close-request signal connected successfully", "Toolbar")
            else:
                logger.warning("WARNING: Settings dialog has no window attribute", "Toolbar")
                logger.warning(
                    "Settings dialog has no window attribute",
                    extra={"class_name": self.__class__.__name__},
                )
            logger.trace("About to call settings_dialog.show()", "Toolbar")
            logger.trace(
                "About to call settings_dialog.show()",
                extra={"class_name": self.__class__.__name__},
            )
            self.settings_dialog.show()  # type: ignore[attr-defined]
            logger.info("Settings dialog show() called successfully", "Toolbar")
            logger.trace(
                "Settings dialog show() called successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error("EXCEPTION in show_settings_dialog:", "Toolbar")
            logger.error("Exception type:", "Toolbar")
            logger.error(
                f"FAILED to open settings dialog: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            logger.error("Full exception traceback:", "Toolbar")
            logger.error(
                f"FULL TRACEBACK: {traceback.format_exc()}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_settings_dialog_closed(self, window: Any) -> Any:
        """Clean up settings dialog reference when closed"""
        logger.trace(
            "Settings dialog closed, cleaning up reference",
            extra={"class_name": self.__class__.__name__},
        )
        self.settings_dialog = None
        return False  # Allow the window to close  # type: ignore

    def on_dialog_response(self, dialog: Any, response_id: Any) -> None:
        if response_id == Gtk.ResponseType.OK:
            logger.trace(
                "Toolbar file added",
                extra={"class_name": self.__class__.__name__},
            )
            # Get the selected file
            selected_file = dialog.get_file()
            torrents_path = os.path.expanduser("~/.config/dfakeseeder/torrents")
            shutil.copy(os.path.abspath(selected_file.get_path()), torrents_path)
            file_path = selected_file.get_path()
            copied_torrent_path = os.path.join(torrents_path, os.path.basename(file_path))
            self.model.add_torrent(copied_torrent_path)  # type: ignore[attr-defined]
            dialog.destroy()
        else:
            dialog.destroy()

    def show_file_selection_dialog(self) -> None:
        logger.trace("Toolbar file dialog", extra={"class_name": self.__class__.__name__})
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

    def get_selected_torrent(self) -> Any:
        return self.selection

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        pass

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace(
            f"Toolbar settings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Update refresh rate slider when tickspeed changes (from external source)
        if key == "tickspeed" and hasattr(self, "toolbar_refresh_rate"):
            try:
                current_value = int(self.toolbar_refresh_rate.get_value())
                new_value = int(value)
                if current_value != new_value:
                    # Block the value-changed handler temporarily to avoid feedback loop
                    self.toolbar_refresh_rate.handler_block_by_func(self.on_toolbar_refresh_rate_changed)
                    self.toolbar_refresh_rate.set_value(new_value)
                    self.toolbar_refresh_rate.handler_unblock_by_func(self.on_toolbar_refresh_rate_changed)
                    logger.trace(
                        f"Updated refresh rate slider to {new_value}",
                        extra={"class_name": self.__class__.__name__},
                    )
            except (ValueError, TypeError) as e:
                logger.error(
                    f"Failed to update refresh rate slider: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    def handle_model_changed(self, source: Any, data_obj: Any, data_changed: Any) -> None:
        logger.trace(
            "Toolbar settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace(
            "Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def model_selection_changed(self, source: Any, model: Any, torrent: Any) -> Any:
        logger.trace(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
        self.selection = torrent

    def toggle_search_entry(self) -> Any:
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

    def on_search_entry_changed(self, entry: Any) -> None:
        """Handle real-time search as user types"""
        search_text = entry.get_text().strip()
        logger.trace(
            f"Search text changed: '{search_text}'",
            extra={"class_name": self.__class__.__name__},
        )
        # Emit search signal to update torrent filtering
        if hasattr(self.model, "set_search_filter"):
            self.model.set_search_filter(search_text)  # type: ignore[attr-defined]

    def on_search_entry_focus_out(self, controller: Any) -> Any:
        """Hide search entry when it loses focus"""
        logger.trace(
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
    def levenshtein_distance(s1: Any, s2: Any) -> Any:
        """Calculate Levenshtein distance between two strings"""
        from lib.util.helpers import levenshtein_distance as util_levenshtein_distance

        return util_levenshtein_distance(s1, s2)

    @staticmethod
    def fuzzy_match(search_term: Any, target_text: Any, threshold: Any = None) -> Any:
        """
        Fuzzy match using Levenshtein distance
        Returns True if match is above threshold (0.0 to 1.0)
        """
        from lib.util.helpers import fuzzy_match as util_fuzzy_match

        return util_fuzzy_match(search_term, target_text, threshold)
