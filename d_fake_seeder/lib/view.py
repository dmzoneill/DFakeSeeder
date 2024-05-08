import os
import signal
import time
import webbrowser
from datetime import datetime

import gi

# Importing necessary libraries
from lib.component.notebook import Notebook
from lib.component.states import States
from lib.component.statusbar import Statusbar
from lib.component.toolbar import Toolbar
from lib.component.torrents import Torrents
from lib.logger import logger
from lib.settings import Settings

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gdk, Gio, GLib, Gtk  # noqa


# View class for Torrent Application
class View:
    instance = None
    toolbar = None
    notebook = None
    torrents_columnview = None
    torrents_states = None

    def __init__(self, app):
        logger.info("View instantiate", extra={"class_name": self.__class__.__name__})
        self.app = app
        View.instance = self

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        # Loading GUI from XML
        self.builder = Gtk.Builder()
        self.builder.add_from_file(os.environ.get("DFS_PATH") + "/ui/generated.xml")

        # Load CSS stylesheet
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path(os.environ.get("DFS_PATH") + "/ui/styles.css")

        # Get window object
        self.window = self.builder.get_object("main_window")

        # views
        self.torrents = Torrents(self.builder, None)
        self.toolbar = Toolbar(self.builder, None, self.window)
        self.notebook = Notebook(self.builder, None)
        self.states = States(self.builder, None)
        self.statusbar = Statusbar(self.builder, None)

        # Getting relevant objects
        self.quit_menu_item = self.builder.get_object("quit_menu_item")
        self.help_menu_item = self.builder.get_object("help_menu_item")
        self.overlay = self.builder.get_object("overlay")
        self.status = self.builder.get_object("status_label")
        self.main_paned = self.builder.get_object("main_paned")
        self.paned = self.builder.get_object("paned")
        self.current_time = time.time()

        # notification overlay
        self.notify_label = Gtk.Label(label="Overlayed Button")
        # self.notify_label.set_no_show_all(True)
        self.notify_label.set_visible(False)
        self.notify_label.hide()
        self.notify_label.set_valign(Gtk.Align.CENTER)
        self.notify_label.set_halign(Gtk.Align.CENTER)
        self.overlay.add_overlay(self.notify_label)

        self.setup_window()
        self.show_splash_image()
        GLib.timeout_add_seconds(1.0, self.resize_panes)

    def setup_window(self):
        self.window.set_title("D' Fake Seeder")
        self.window.set_application(self.app)

        # Load CSS stylesheet
        css_provider = Gtk.CssProvider()
        css_provider.load_from_path("ui/styles.css")  # Load CSS from file

        # Apply CSS to the window
        style_context = self.window.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # Create an action group
        self.action_group = Gio.SimpleActionGroup()

        # add hamburger menu
        self.header = Gtk.HeaderBar()
        self.window.set_titlebar(self.header)

        # Create a new "Action"
        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.quit)
        self.action_group.add_action(action)

        menu = Gio.Menu.new()
        menu.append("Quit", "win.quit")

        # Create a popover
        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(menu)

        # Create a menu button
        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")

        # Add menu button to the header bar
        self.header.pack_start(self.hamburger)

        # Add an about dialog
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.show_about)
        self.action_group.add_action(action)
        menu.append("About", "win.about")

        # Insert the action group into the window
        self.window.insert_action_group("win", self.action_group)

        self.window.present()

    def show_splash_image(self):
        # splash image
        self.splash_image = Gtk.Image()
        self.splash_image.set_from_file(
            os.environ.get("DFS_PATH") + "/images/dfakeseeder.png"
        )
        # self.splash_image.set_no_show_all(False)
        self.splash_image.set_visible(True)
        self.splash_image.show()
        self.splash_image.set_valign(Gtk.Align.CENTER)
        self.splash_image.set_halign(Gtk.Align.CENTER)
        self.splash_image.set_size_request(100, 100)
        self.overlay.add_overlay(self.splash_image)
        GLib.timeout_add_seconds(2, self.fade_out_image)

    def show_about(self, action, param):
        self.window.about = Gtk.AboutDialog()
        self.window.about.set_transient_for(self.window)
        self.window.about.set_modal(self)
        self.window.about.set_program_name("D' Fake Seeder")
        self.window.about.set_authors([self.settings.author])
        self.window.about.set_copyright(
            self.settings.copyright.replace("{year}", str(datetime.now().year))
        )
        self.window.about.set_license_type(Gtk.License.APACHE_2_0)
        self.window.about.set_website(self.settings.website)
        self.window.about.set_website_label("Github - D' Fake Seeder")
        self.window.about.set_version(self.settings.version)
        file = Gio.File.new_for_path(
            os.environ.get("DFS_PATH") + "/" + self.settings.logo
        )
        texture = Gdk.Texture.new_from_file(file)
        self.window.about.set_logo(texture)
        self.window.about.show()

    def fade_out_image(self):
        self.splash_image.fade_out = 1.0
        GLib.timeout_add(75, self.fade_image)

    def fade_image(self):
        self.splash_image.fade_out -= 0.025
        if self.splash_image.fade_out > 0:
            self.splash_image.set_opacity(self.splash_image.fade_out)
            return True
        else:
            self.splash_image.hide()
            self.splash_image.unparent()
            self.splash_image = None
            return False

    def resize_panes(self):
        logger.info("View resize_panes", extra={"class_name": self.__class__.__name__})
        allocation = self.main_paned.get_allocation()
        available_height = allocation.height
        position = available_height // 2
        self.main_paned.set_position(position)

        allocation = self.paned.get_allocation()
        available_width = allocation.width
        position = available_width // 4
        self.paned.set_position(position)

    # Setting model for the view
    def notify(self, text):
        logger.info("View notify", extra={"class_name": self.__class__.__name__})
        # Cancel the previous timeout, if it exists
        if hasattr(self, "timeout_id") and self.timeout_id > 0:
            GLib.source_remove(self.timeout_id)

        # self.notify_label.set_no_show_all(False)
        self.notify_label.set_visible(True)
        self.notify_label.show()
        self.notify_label.set_text(text)
        self.status.set_text(text)
        self.timeout_id = GLib.timeout_add(
            3000,
            lambda: self.notify_label.set_visible(False) or self.notify_label.hide(),
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
            "View connect signals",
            extra={"class_name": self.__class__.__name__},
        )
        self.window.connect("destroy", self.quit)
        self.window.connect("close-request", self.quit)
        self.model.connect("data-changed", self.torrents.update_view)
        self.model.connect("data-changed", self.notebook.update_view)
        self.model.connect("data-changed", self.states.update_view)
        self.model.connect("data-changed", self.statusbar.update_view)
        self.model.connect("data-changed", self.toolbar.update_view)
        self.model.connect("selection-changed", self.torrents.model_selection_changed)
        self.model.connect("selection-changed", self.notebook.model_selection_changed)
        self.model.connect("selection-changed", self.states.model_selection_changed)
        self.model.connect("selection-changed", self.statusbar.model_selection_changed)
        self.model.connect("selection-changed", self.toolbar.model_selection_changed)
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

    # open github webpage
    def on_help_clicked(self, menu_item):
        logger.info(
            "Opening GitHub webpage",
            extra={"class_name": self.__class__.__name__},
        )
        webbrowser.open(self.settings.issues_page)

    # Function to quit the application
    def quit(self, widget=None, event=None):
        logger.info("View quit", extra={"class_name": self.__class__.__name__})

        # Stopping all torrents before quitting
        for torrent in self.model.torrent_list:
            torrent.stop()
        self.settings.save_quit()
        self.window.destroy()

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)
