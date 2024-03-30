# import gettext
import gi

# Ensure the correct version of Gtk is used
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

# Import the Model, View, and Controller classes from their respective modules
from lib.model import Model
from lib.view import View
from lib.controller import Controller
from lib.settings import Settings
from lib.logger import logger


class DFakeSeeder(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="ie.fio.dfakeseeder", flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        logger.info("Startup", extra={"class_name": self.__class__.__name__})
        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

    def do_activate(self):
        logger.info("Run Controller", extra={"class_name": self.__class__.__name__})

        # The Model manages the data and logic
        self.model = Model()
        # The View manages the user interface
        self.view = View(self)
        # The Controller manages the interactions between the Model and View
        self.controller = Controller(self.view, self.model)

        # Start the controller
        self.controller.run()

        self.view.window.show()

    def handle_settings_changed(self, source, key, value):
        logger.info("Settings changed", extra={"class_name": self.__class__.__name__})
        # print(key + " = " + value)


# If the script is run directly (rather than imported as a module), create an instance of the UI class
if __name__ == "__main__":
    d = DFakeSeeder()
    d.run()
