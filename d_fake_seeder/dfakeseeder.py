# import gettext
import importlib.util
import os

import gi
import typer
from lib.controller import Controller
from lib.logger import logger
from lib.model import Model
from lib.settings import Settings
from lib.view import View

gi.require_version("Gtk", "4.0")

from gi.repository import Gio, Gtk  # noqa

# Import the Model, View, and Controller classes from their respective modules


class DFakeSeeder(Gtk.Application):
    def __init__(self):
        super().__init__(
            application_id="ie.fio.dfakeseeder",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
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


app = typer.Typer()


@app.command()
def run():
    try:
        os.environ["DFS_PATH"] = os.getcwd()
        d = DFakeSeeder()
        d.run()
        return
    except Exception as e:
        print(f"Tried to run from current directory failed, trying module find_spec {e}")
        try:
            spec = importlib.util.find_spec("d_fake_seeder")
            if os.getenv("DFS_PATH") is None:
                os.environ["DFS_PATH"] = spec.submodule_search_locations[0]
            d = DFakeSeeder()
            d.run()
        except Exception as e:
            raise ImportError(f"Module d_fake_seeder not found. {e}")


# If the script is run directly (rather than imported as a module), create
# an instance of the UI class
if __name__ == "__main__":
    app()
