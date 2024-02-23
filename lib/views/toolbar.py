import gi
import os
import shutil

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
from lib.settings import Settings
from lib.logger import logger


class Toolbar:
    def __init__(self, builder, model):
        logger.info("Toolbar startup", extra={"class_name": self.__class__.__name__})
        self.builder = builder
        self.model = model

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        toolbar_add_button = self.builder.get_object("toolbar_add")
        toolbar_add_button.connect("clicked", self.on_toolbar_add_clicked)

        toolbar_remove_button = self.builder.get_object("toolbar_remove")
        toolbar_remove_button.connect("clicked", self.on_toolbar_remove_clicked)

        toolbar_pause_button = self.builder.get_object("toolbar_pause")
        toolbar_pause_button.connect("clicked", self.on_toolbar_pause_clicked)

        toolbar_resume_button = self.builder.get_object("toolbar_resume")
        toolbar_resume_button.connect("clicked", self.on_toolbar_resume_clicked)

        toolbar_up_button = self.builder.get_object("toolbar_up")
        toolbar_up_button.connect("clicked", self.on_toolbar_up_clicked)

        toolbar_down_button = self.builder.get_object("toolbar_down")
        toolbar_down_button.connect("clicked", self.on_toolbar_down_clicked)

        toolbar_settings_button = self.builder.get_object("toolbar_settings")
        toolbar_settings_button.connect("clicked", self.on_toolbar_settings_clicked)

    def set_model(self, model):
        self.model = model

    def on_toolbar_add_clicked(self, button):
        logger.info(
            "Toolbar add button clicked", extra={"class_name": self.__class__.__name__}
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

    def on_toolbar_resume_clicked(self, button):
        logger.info(
            "Toolbar resume button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return

        selected.active = True

    def on_toolbar_up_clicked(self, button):
        logger.info(
            "Toolbar up button clicked", extra={"class_name": self.__class__.__name__}
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
                break

    def on_toolbar_down_clicked(self, button):
        logger.info(
            "Toolbar down button clicked", extra={"class_name": self.__class__.__name__}
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
                break

    def on_toolbar_settings_clicked(self, button):
        logger.info(
            "Toolbar settings button clicked",
            extra={"class_name": self.__class__.__name__},
        )
        selected = self.get_selected_torrent()
        if not selected:
            return

    def on_file_selected(self, dialog, args):
        logger.info("Toolbar file added", extra={"class_name": self.__class__.__name__})
        # Get the selected file
        selected_file = dialog.get_filename()
        print("Selected File:", selected_file)
        current_path = os.path.dirname(os.path.abspath(__file__))
        torrents_path = os.path.join(current_path, "torrents")
        shutil.copy(os.path.abspath(selected_file), torrents_path)
        copied_torrent_path = os.path.join(torrents_path, os.path.basename(selected_file))
        self.model.add_torrent(os.path.relpath(copied_torrent_path))

    def show_file_selection_dialog(self):
        logger.info(
            "Toolbar file dialog", extra={"class_name": self.__class__.__name__}
        )
        # Create a new file chooser dialog
        dialog = Gtk.FileChooserDialog(
            "Select File",
            None,
            Gtk.FileChooserAction.OPEN,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )

        filter_torrent = Gtk.FileFilter()
        filter_torrent.set_name("Torrent Files")
        filter_torrent.add_pattern("*.torrent")
        dialog.add_filter(filter_torrent)

        # Connect the "response" signal to the callback function
        dialog.connect("response", self.on_file_selected)

        # Run the dialog
        response = dialog.run()

        # Close the dialog
        dialog.destroy()

        # Handle the user's response
        if response == Gtk.ResponseType.OK:
            print("User clicked Open button")
        elif response == Gtk.ResponseType.CANCEL:
            print("User clicked Cancel button")

    def get_selected_torrent(self):
        logger.info(
            "Toolbar get selected torrent",
            extra={"class_name": self.__class__.__name__},
        )
        # Get the TreeView object using self.builder.get_object
        treeview1 = self.builder.get_object("treeview1")

        # Get the currently selected item
        selection = treeview1.get_selection()
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

    def update_view(self, model, _, torrent, attribute):
        pass

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Toolbar settings changed", extra={"class_name": self.__class__.__name__}
        )
        # print(key + " = " + value)
