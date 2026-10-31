"""Main application toolbar component and its button/search wiring."""

import math
import os
import shutil
from types import SimpleNamespace
from typing import Any

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.gi_gtk4 import GLib, Gtk
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.xdg_paths import get_config_dir


class Toolbar(Component):
    """Application toolbar: action buttons, speed controls and search entry."""

    _BUTTON_SPECS = (
        ("add", "toolbar_add", "_on_toolbar_add_clicked"),
        ("remove", "toolbar_remove", "_on_toolbar_remove_clicked"),
        ("search", "toolbar_search", "_on_toolbar_search_clicked"),
        ("pause", "toolbar_pause", "_on_toolbar_pause_clicked"),
        ("resume", "toolbar_resume", "_on_toolbar_resume_clicked"),
        ("up", "toolbar_up", "_on_toolbar_up_clicked"),
        ("down", "toolbar_down", "_on_toolbar_down_clicked"),
        ("speed_double", "toolbar_speed_double", "_on_toolbar_speed_double_clicked"),
        ("speed_halve", "toolbar_speed_halve", "_on_toolbar_speed_halve_clicked"),
        ("dl_speed_double", "toolbar_download_speed_double", "_on_toolbar_download_speed_double_clicked"),
        ("dl_speed_halve", "toolbar_download_speed_halve", "_on_toolbar_download_speed_halve_clicked"),
    )

    def __init__(self, builder: Any, model: Any, app: Any) -> None:
        """Initialize the toolbar, wiring up its buttons, search entry and scale."""
        super().__init__()
        self.builder = builder
        self.model = model
        self.app = app
        self.settings: Any = None
        self._buttons = SimpleNamespace()
        self._widgets = SimpleNamespace(refresh_rate=None, search_entry=None)
        self._state = SimpleNamespace(
            settings_dialog=None,
            selection=None,
            search_visible=False,
            tickspeed_pending=False,
            tickspeed_source_id=None,
        )
        self._init_settings()
        self._build_buttons()
        self._build_search_entry()
        self._build_speed_button_styles()
        self._build_settings_button()
        self._build_refresh_rate()

    @property
    def _model(self) -> Any:
        """Return the attached model typed as Any for dynamic attribute access."""
        return self.model

    def _init_settings(self) -> None:
        """Obtain the shared AppSettings instance and subscribe to changes."""
        try:
            self.settings = AppSettings.get_instance()
            self.track_signal(
                self.settings,
                self.settings.connect("attribute-changed", self.handle_settings_changed),
            )
        except (AttributeError, TypeError, KeyError) as e:
            logger.error(f"ERROR getting AppSettings: {e}", self.__class__.__name__, exc_info=True)
            self.settings = None

    def _build_buttons(self) -> None:
        """Look up each flat toolbar button and connect its click handler."""
        for attr, object_id, handler_name in self._BUTTON_SPECS:
            button = self.builder.get_object(object_id)
            setattr(self._buttons, attr, button)
            self.track_signal(button, button.connect("clicked", getattr(self, handler_name)))
            button.add_css_class("flat")

    def _build_search_entry(self) -> None:
        """Resolve the search entry and connect its change and focus-out handlers."""
        entry = self.builder.get_object("toolbar_search_entry")
        self._widgets.search_entry = entry
        self.track_signal(entry, entry.connect("changed", self._on_search_entry_changed))
        focus_controller = Gtk.EventControllerFocus()
        self.track_signal(
            focus_controller,
            focus_controller.connect("leave", self._on_search_entry_focus_out),
        )
        entry.add_controller(focus_controller)

    def _build_speed_button_styles(self) -> None:
        """Tint the upload speed buttons green and the download speed buttons red."""
        self._apply_icon_color(self._buttons.speed_double, "#33d17a")
        self._apply_icon_color(self._buttons.speed_halve, "#33d17a")
        self._apply_icon_color(self._buttons.dl_speed_double, "#e01b24")
        self._apply_icon_color(self._buttons.dl_speed_halve, "#e01b24")

    @staticmethod
    def _apply_icon_color(button: Any, color: str) -> None:
        """Apply an icon colour to a toolbar button via a dedicated CSS provider."""
        provider = Gtk.CssProvider()
        provider.load_from_string(f"image {{ color: {color}; }}")
        button.get_first_child().get_style_context().add_provider(
            provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 100
        )

    def _build_settings_button(self) -> None:
        """Look up the settings button and connect it when present."""
        try:
            button = self.builder.get_object("toolbar_settings")
        except (AttributeError, TypeError):
            logger.error("ERROR in get_object", "Toolbar", exc_info=True)
            button = None
        self._buttons.settings = button
        if button:
            self.track_signal(button, button.connect("clicked", self._on_toolbar_settings_clicked))
            button.add_css_class("flat")
        else:
            logger.error("Settings button not found in UI", "Toolbar")

    def _build_refresh_rate(self) -> None:
        """Configure the refresh-rate scale and load its saved tickspeed value."""
        scale = self.builder.get_object("toolbar_refresh_rate")
        self._widgets.refresh_rate = scale
        adjustment = Gtk.Adjustment.new(1, 1, 60, 1, 10, 0)
        adjustment.set_step_increment(1)
        scale.set_adjustment(adjustment)
        scale.set_digits(0)
        try:
            scale.set_value(int(self.settings.get("tickspeed", 9)))
        except (AttributeError, TypeError, KeyError, ValueError) as e:
            logger.error(f"ERROR accessing tickspeed: {e}", "Toolbar", exc_info=True)
            scale.set_value(9)
        self.track_signal(
            scale,
            scale.connect("value-changed", self._on_toolbar_refresh_rate_changed),
        )
        scale.set_size_request(150, -1)

    def _(self, text: Any) -> Any:
        """Get translation function from model's TranslationManager"""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self._model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def _on_toolbar_refresh_rate_changed(self, scale: Any) -> None:
        """Handle refresh rate slider value change with debounced save."""
        # Cancel any pending save
        if self._state.tickspeed_source_id:
            GLib.source_remove(self._state.tickspeed_source_id)
            self._state.tickspeed_source_id = None

        # Schedule a debounced save (configurable delay)
        debounce_ms = self.settings.get("ui_settings.tickspeed_debounce_ms", 500)
        self._state.tickspeed_source_id = GLib.timeout_add(debounce_ms, self._save_tickspeed_debounced)

    def _save_tickspeed_debounced(self) -> bool:
        """Actually save the tickspeed setting after debounce delay."""
        self._state.tickspeed_source_id = None
        value = self._widgets.refresh_rate.get_value()
        tickspeed = math.ceil(float(value))
        current = self.settings.get("tickspeed", 9)

        if tickspeed != current:
            self.settings.set("tickspeed", tickspeed)
            logger.trace(f"Saved tickspeed to settings: {tickspeed}", "Toolbar")

        return False  # Don't repeat

    def _on_toolbar_add_clicked(self, button: Any) -> None:
        """Handle the add clicked action."""
        logger.trace(
            "Toolbar add button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        self.show_file_selection_dialog()

    def _on_toolbar_remove_clicked(self, button: Any) -> None:
        """Handle the remove clicked action."""
        logger.trace(
            "Toolbar remove button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return
        try:
            os.remove(selected.filepath)
        except OSError as e:
            logger.error(
                f"Error removing torrent file {selected.filepath}: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
        self._model.remove_torrent(selected.filepath)

    def _emit_selected_active(self, active: bool) -> None:
        """Set the selected torrent's active flag and broadcast the change."""
        selected = self.get_selected_torrent()
        if not selected:
            return
        selected.active = active
        self._model.emit("data-changed", self.model, selected)

    def _move_selected(self, delta: int) -> None:
        """Move the selected torrent up (delta -1) or down (delta +1) in the list."""
        selected = self.get_selected_torrent()
        if not selected:
            return
        target_id = selected.id + delta
        if target_id < 1 or target_id > len(self._model.torrent_list):
            return
        for torrent in self._model.torrent_list:
            if torrent.id == target_id:
                torrent.id = selected.id
                selected.id = target_id
                self._model.emit("data-changed", self.model, selected)
                self._model.emit("data-changed", self.model, torrent)
                break

    def _scale_speed(self, field: str, operation: Any) -> None:
        """Apply a scaling operation to every torrent's upload or download speed."""
        for torrent in self._model.torrent_list:
            setattr(torrent, field, operation(getattr(torrent, field)))
        self._model.emit("data-changed", self.model, None)

    def _on_toolbar_pause_clicked(self, button: Any) -> None:
        """Handle the pause clicked action."""
        self._emit_selected_active(False)

    def _on_toolbar_resume_clicked(self, button: Any) -> None:
        """Handle the resume clicked action."""
        self._emit_selected_active(True)

    def _on_toolbar_up_clicked(self, button: Any) -> None:
        """Handle the up clicked action."""
        self._move_selected(-1)

    def _on_toolbar_down_clicked(self, button: Any) -> None:
        """Handle the down clicked action."""
        self._move_selected(1)

    def _on_toolbar_speed_double_clicked(self, button: Any) -> None:
        """Handle the speed double clicked action."""
        self._scale_speed("upload_speed", lambda v: v * 2)

    def _on_toolbar_speed_halve_clicked(self, button: Any) -> None:
        """Handle the speed halve clicked action."""
        self._scale_speed("upload_speed", lambda v: max(1, v // 2))

    def _on_toolbar_download_speed_double_clicked(self, button: Any) -> None:
        """Handle the download speed double clicked action."""
        self._scale_speed("download_speed", lambda v: v * 2)

    def _on_toolbar_download_speed_halve_clicked(self, button: Any) -> None:
        """Handle the download speed halve clicked action."""
        self._scale_speed("download_speed", lambda v: max(1, v // 2))

    def _on_toolbar_search_clicked(self, button: Any) -> None:
        """Handle the search clicked action."""
        logger.trace(
            "Toolbar search button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        self.toggle_search_entry()

    def _on_toolbar_settings_clicked(self, button: Any) -> None:
        """Handle the settings clicked action."""
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
        except (AttributeError, TypeError, ImportError) as e:
            logger.error(
                f"ERROR in on_toolbar_settings_clicked: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def show_settings_dialog(self) -> None:
        """Open the settings dialog, reusing an existing one when still valid."""
        try:
            if self._present_existing_dialog():
                return
            from components.component.settings.settings_dialog import SettingsDialog

            main_window = self._resolve_main_window()
            dialog: Any = SettingsDialog(main_window, self.app, self.model)
            self._state.settings_dialog = dialog
            if hasattr(dialog, "window"):
                self.track_signal(
                    dialog.window,
                    dialog.window.connect("close-request", self._on_settings_dialog_closed),
                )
            else:
                logger.warning("Settings dialog has no window attribute", "Toolbar")
            dialog.show()
        except (AttributeError, TypeError, ImportError) as e:
            logger.error(
                f"FAILED to open settings dialog: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def _present_existing_dialog(self) -> bool:
        """Present an existing, still-valid settings dialog; return True if handled."""
        dialog: Any = self._state.settings_dialog
        if dialog and hasattr(dialog, "window"):
            try:
                dialog.window.present()
                return True
            except (AttributeError, TypeError) as e:
                logger.error(f"Existing settings dialog invalid, recreating: {e}", exc_info=True)
                self._state.settings_dialog = None
        return False

    def _resolve_main_window(self) -> Any:
        """Return the application's active window, or None when unavailable."""
        if hasattr(self, "app") and self.app:
            return self.app.get_active_window()
        logger.warning("No app or active window found", "Toolbar")
        return None

    def _on_settings_dialog_closed(self, window: Any) -> Any:
        """Clean up settings dialog reference when closed"""
        logger.trace(
            "Settings dialog closed, cleaning up reference",
            extra={"class_name": self.__class__.__name__},
        )
        self._state.settings_dialog = None
        return False  # Allow the window to close

    def _on_dialog_response(self, dialog: Any, response_id: Any) -> None:
        """Handle the dialog response action."""
        if response_id == Gtk.ResponseType.OK:
            logger.trace(
                "Toolbar file added",
                extra={"class_name": self.__class__.__name__},
            )
            # Get the selected file
            selected_file = dialog.get_file()
            torrents_path = os.path.join(get_config_dir(), "torrents")
            shutil.copy(os.path.abspath(selected_file.get_path()), torrents_path)
            file_path = selected_file.get_path()
            copied_torrent_path = os.path.join(torrents_path, os.path.basename(file_path))
            self._model.add_torrent(copied_torrent_path)
            dialog.destroy()
        else:
            dialog.destroy()

    def show_file_selection_dialog(self) -> None:
        """Handle show file selectidialog."""
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
        self.track_signal(dialog, dialog.connect("response", self._on_dialog_response))
        # Run the dialog
        dialog.show()

    def get_selected_torrent(self) -> Any:
        """Handle get selected torrent."""
        return self._state.selection

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """No-op: the toolbar has no per-update view refresh."""

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        """React to the settings changed signal."""
        logger.trace(
            f"Toolbar settings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Update refresh rate slider when tickspeed changes (from external source)
        if key == "tickspeed" and self._widgets.refresh_rate is not None:
            try:
                current_value = int(self._widgets.refresh_rate.get_value())
                new_value = int(value)
                if current_value != new_value:
                    # Block the value-changed handler temporarily to avoid feedback loop
                    self._widgets.refresh_rate.handler_block_by_func(self._on_toolbar_refresh_rate_changed)
                    self._widgets.refresh_rate.set_value(new_value)
                    self._widgets.refresh_rate.handler_unblock_by_func(self._on_toolbar_refresh_rate_changed)
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
        """No-op override: the toolbar does not react to model-changed signals."""

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        """No-op override: the toolbar does not react to attribute-changed signals."""

    def model_selection_changed(self, source: Any, model: Any, torrent: Any) -> Any:
        """Remember the currently selected torrent."""
        self._state.selection = torrent

    def toggle_search_entry(self) -> Any:
        """Toggle the visibility of the search entry and handle focus"""
        self._state.search_visible = not self._state.search_visible
        self._widgets.search_entry.set_visible(self._state.search_visible)
        if self._state.search_visible:
            # Grab focus when showing the search entry
            self._widgets.search_entry.grab_focus()
        else:
            # Clear search when hiding
            self._widgets.search_entry.set_text("")
            # Trigger search clear to show all torrents
            self._on_search_entry_changed(self._widgets.search_entry)

    def _on_search_entry_changed(self, entry: Any) -> None:
        """Handle real-time search as user types"""
        search_text = entry.get_text().strip()
        logger.trace(
            f"Search text changed: '{search_text}'",
            extra={"class_name": self.__class__.__name__},
        )
        # Emit search signal to update torrent filtering
        if hasattr(self.model, "set_search_filter"):
            self._model.set_search_filter(search_text)

    def _on_search_entry_focus_out(self, controller: Any) -> Any:
        """Hide search entry when it loses focus"""
        logger.trace(
            "Search entry lost focus",
            extra={"class_name": self.__class__.__name__},
        )
        self._state.search_visible = False
        self._widgets.search_entry.set_visible(False)
        # Clear search when hiding
        self._widgets.search_entry.set_text("")
        # Trigger search clear to show all torrents
        self._on_search_entry_changed(self._widgets.search_entry)
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
