import math
import os
import shutil

import gi
from lib.component.component import Component
from lib.logger import logger
from lib.settings import Settings

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa


class Toolbar(Component):
    def __init__(self, builder, model, app):
        logger.info("Toolbar startup", extra={"class_name": self.__class__.__name__})
        self.builder = builder
        self.model = model
        self.app = app

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.toolbar_add_button = self.builder.get_object("toolbar_add")
        self.toolbar_add_button.connect("clicked", self.on_toolbar_add_clicked)
        self.toolbar_add_button.add_css_class("flat")

        self.toolbar_remove_button = self.builder.get_object("toolbar_remove")
        self.toolbar_remove_button.connect("clicked", self.on_toolbar_remove_clicked)
        self.toolbar_remove_button.add_css_class("flat")

        self.toolbar_search_button = self.builder.get_object("toolbar_search")
        self.toolbar_search_button.connect("clicked", self.on_toolbar_remove_clicked)
        self.toolbar_search_button.add_css_class("flat")

        self.toolbar_pause_button = self.builder.get_object("toolbar_pause")
        self.toolbar_pause_button.connect("clicked", self.on_toolbar_pause_clicked)
        self.toolbar_pause_button.add_css_class("flat")

        self.toolbar_resume_button = self.builder.get_object("toolbar_resume")
        self.toolbar_resume_button.connect("clicked", self.on_toolbar_resume_clicked)
        self.toolbar_resume_button.add_css_class("flat")

        self.toolbar_up_button = self.builder.get_object("toolbar_up")
        self.toolbar_up_button.connect("clicked", self.on_toolbar_up_clicked)
        self.toolbar_up_button.add_css_class("flat")

        self.toolbar_down_button = self.builder.get_object("toolbar_down")
        self.toolbar_down_button.connect("clicked", self.on_toolbar_down_clicked)
        self.toolbar_down_button.add_css_class("flat")

        self.toolbar_settings_button = self.builder.get_object("toolbar_settings")
        self.toolbar_settings_button.connect("clicked", self.on_toolbar_settings_clicked)
        self.toolbar_settings_button.add_css_class("flat")

        self.toolbar_refresh_rate = self.builder.get_object("toolbar_refresh_rate")
        adjustment = Gtk.Adjustment.new(0, 1, 60, 1, 1, 1)
        adjustment.set_step_increment(1)
        self.toolbar_refresh_rate.set_adjustment(adjustment)
        self.toolbar_refresh_rate.set_digits(0)
        self.toolbar_refresh_rate.connect(
            "value-changed", self.on_toolbar_refresh_rate_changed
        )
        self.toolbar_refresh_rate.set_value(int(self.settings.tickspeed))
        self.toolbar_refresh_rate.set_size_request(150, -1)

    def on_toolbar_refresh_rate_changed(self, value):
        self.settings.tickspeed = math.ceil(float(self.toolbar_refresh_rate.get_value()))

    def on_toolbar_add_clicked(self, button):
        logger.info(
            "Toolbar add button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        self.show_file_selection_dialog()

    def on_toolbar_remove_clicked(self, button):
        logger.info(
            "Toolbar remove button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return

        logger.info(
            "Toolbar remove " + selected.filepath,
            extra={"class_name": self.__class__.__name__},
        )
        logger.info(
            "Toolbar remove " + str(selected.id),
            extra={"class_name": self.__class__.__name__},
        )
        os.remove(selected.filepath)
        self.model.torrent_list.remove(selected)

    def on_toolbar_pause_clicked(self, button):
        logger.info(
            "Toolbar pause button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return

        selected.active = False
        self.model.emit("data-changed", self.model, selected, {"active": selected.active})

    def on_toolbar_resume_clicked(self, button):
        logger.info(
            "Toolbar resume button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return

        selected.active = True
        self.model.emit("data-changed", self.model, selected, {"active": selected.active})

    def on_toolbar_up_clicked(self, button):
        logger.info(
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
                self.model.emit("data-changed", self.model, selected, {"id": selected.id})
                self.model.emit("data-changed", self.model, torrent, {"id": torrent.id})
                break

    def on_toolbar_down_clicked(self, button):
        logger.info(
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
                self.model.emit("data-changed", self.model, selected, {"id": selected.id})
                self.model.emit("data-changed", self.model, torrent, {"id": torrent.id})
                break

    def on_toolbar_settings_clicked(self, button):
        logger.info(
            "Toolbar settings button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return

    def on_dialog_response(self, dialog, response_id):
        if response_id == Gtk.ResponseType.OK:
            logger.info(
                "Toolbar file added", extra={"class_name": self.__class__.__name__}
            )
            # Get the selected file
            selected_file = dialog.get_file()
            print("Selected File:", selected_file)
            current_path = os.path.dirname(os.path.abspath(__file__))
            torrents_path = os.path.join(current_path, "torrents")
            shutil.copy(os.path.abspath(selected_file.get_path()), torrents_path)

            # Assuming selected_file is a GLocalFile object
            file_path = selected_file.get_path()

            copied_torrent_path = os.path.join(torrents_path, os.path.basename(file_path))
            self.model.add_torrent(os.path.relpath(copied_torrent_path))
            dialog.destroy()
        else:
            dialog.destroy()

    def show_file_selection_dialog(self):
        logger.info("Toolbar file dialog", extra={"class_name": self.__class__.__name__})
        # Create a new file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Select torrent",
            transient_for=self.app,
            modal=True,
            action=Gtk.FileChooserAction.OPEN,
        )

        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Add", Gtk.ResponseType.OK)

        filter_torrent = Gtk.FileFilter()
        filter_torrent.set_name("Torrent Files")
        filter_torrent.add_pattern("*.torrent")
        dialog.add_filter(filter_torrent)

        # Connect the "response" signal to the callback function
        dialog.connect("response", self.on_dialog_response)

        # Run the dialog
        dialog.show()

    def get_selected_torrent(self):
        logger.info(
            "Toolbar get selected torrent",
            extra={"class_name": self.__class__.__name__},
        )
        # Get the TreeView object using self.builder.get_object
        columnview1 = self.builder.get_object("columnview1")

        # Get the currently selected item
        selection = columnview1.get_selection()
        lmodel, tree_iter = selection.get_selected()

        if tree_iter is None:
            return

        # Get the index of the selected item
        index = int(lmodel.get_path(tree_iter).get_indices()[0]) + 1

        # Remove the torrent from self.model.torrent_list
        for torrent in self.model.torrent_list:
            if torrent.id == index:
                return torrent

        return False

    def update_view(self, model, torrent, attribute):
        pass

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.info(
            "Toolbar settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)

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
