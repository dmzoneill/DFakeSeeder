# Importing necessary libraries
import signal
import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, GdkPixbuf
from lib.settings import Settings
from sys import exit
import time
from lib.views.toolbar import Toolbar
from lib.views.statusbar import Statusbar
from lib.views.notebook import Notebook
from lib.views.torrents import Torrents
from lib.views.states import States
from lib.logger import logger


# View class for Torrent Application
class View:
    instance = None
    toolbar = None
    notebook = None
    torrents_treeview = None
    torrents_states = None

    def __init__(self):
        logger.info("View instantiate", extra={"class_name": self.__class__.__name__})
        View.instance = self

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        # Loading GUI from XML
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui/generated.xml")

        # views
        self.toolbar = Toolbar(self.builder, None)
        self.notebook = Notebook(self.builder, None)
        self.torrents = Torrents(self.builder, None)
        self.states = States(self.builder, None)
        self.statusbar = Statusbar(self.builder, None)

        # Getting relevant objects
        self.window = self.builder.get_object("main_window")
        self.quit_menu_item = self.builder.get_object("quit_menu_item")
        self.overlay = self.builder.get_object("overlay")

        # notification overlay
        self.notify_label = Gtk.Label(label="Overlayed Button")
        self.notify_label.set_no_show_all(True)
        self.notify_label.set_visible(False)
        self.notify_label.hide()
        self.notify_label.set_valign(Gtk.Align.CENTER)
        self.notify_label.set_halign(Gtk.Align.CENTER)
        self.overlay.add_overlay(self.notify_label)

        self.status = self.builder.get_object("status_label")

        screen = self.window.get_screen()
        screen_width = screen.get_width()
        screen_height = screen.get_height()

        window_width = self.window.get_size()[0]
        window_height = self.window.get_size()[1]

        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2

        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.move(x, y)

        # Make sure GTK can't know the filename the bytes came from
        with open("./images/dfakeseeder.png", "rb") as fobj:
            data = fobj.read()

        loader = GdkPixbuf.PixbufLoader.new_with_type("png")
        loader.write(data)
        loader.close()

        self.window.set_icon(loader.get_pixbuf())
        self.window.set_title("D' Fake Seeder")
        self.window.set_tooltip_text("D' Fake Seeder")

        self.main_paned = self.builder.get_object("main_paned")
        self.current_time = time.time()

        GLib.timeout_add_seconds(0.5, self.resize_panes)

    def resize_panes(self):
        logger.info("View resize_panes", extra={"class_name": self.__class__.__name__})
        allocation = self.main_paned.get_allocation()
        available_height = allocation.height
        position = available_height // 2
        self.main_paned.set_position(position)
        self.status_position = position

    # Setting model for the view
    def notify(self, text):
        logger.info("View notify", extra={"class_name": self.__class__.__name__})
        # Cancel the previous timeout, if it exists
        if hasattr(self, "timeout_id") and self.timeout_id > 0:
            GLib.source_remove(self.timeout_id)

        self.notify_label.set_no_show_all(False)
        self.notify_label.set_visible(True)
        self.notify_label.show()
        self.notify_label.set_text(text)
        self.status.set_text(text)
        self.timeout_id = GLib.timeout_add(
            3000,
            lambda: self.notify_label.set_no_show_all(True)
            or self.notify_label.set_visible(False)
            or self.notify_label.hide(),
        )

    # Setting model for the view
    def set_model(self, model):
        logger.info("View set model", extra={"class_name": self.__class__.__name__})
        self.model = model
        self.notebook.set_model(model)
        self.toolbar.set_model(model)
        self.torrents.set_model(model)
        self.states.set_model(model)
        self.statusbar.set_model(model)

    # Connecting signals for different events
    def connect_signals(self):
        logger.info(
            "View connect signals", extra={"class_name": self.__class__.__name__}
        )
        self.window.connect("destroy", self.quit)
        self.window.connect("delete-event", self.quit)
        self.quit_menu_item.connect("activate", self.on_quit_clicked)
        self.model.connect("data-changed", self.torrents.update_view)
        self.model.connect("data-changed", self.notebook.update_view)
        self.model.connect("data-changed", self.states.update_view)
        self.model.connect("data-changed", self.statusbar.update_view)
        signal.signal(signal.SIGINT, self.quit)

    # Connecting signals for different events
    def remove_signals(self):
        logger.info("Remove signals", extra={"class_name": self.__class__.__name__})
        self.model.disconnect_by_func(self.torrents.update_view)
        self.model.disconnect_by_func(self.notebook.update_view)
        self.model.disconnect_by_func(self.states.update_view)
        self.model.disconnect_by_func(self.statusbar.update_view)

    # Event handler for clicking on quit
    def on_quit_clicked(self, menu_item):
        logger.info("View quit", extra={"class_name": self.__class__.__name__})
        self.remove_signals()
        self.quit()

    # Function to quit the application
    def quit(self, widget=None, event=None):
        logger.info("View quit", extra={"class_name": self.__class__.__name__})

        # Stopping all torrents before quitting
        for torrent in self.model.torrent_list:
            torrent.stop()
        self.settings.save_quit()
        self.window.destroy()
        Gtk.main_quit()
        exit(0)

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "View settings changed", extra={"class_name": self.__class__.__name__}
        )
        # print(key + " = " + value)
