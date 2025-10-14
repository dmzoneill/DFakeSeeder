import os

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")

import typer  # noqa: E402
from controller import Controller  # noqa: E402
from gi.repository import Gio  # noqa
from gi.repository import Gtk  # noqa: E402
from model import Model  # noqa: E402
from view import View  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.app_initialization import AppInitializationHelper  # noqa: E402

# Import the Model, View, and Controller classes from their respective modules


class DFakeSeeder(Gtk.Application):
    def __init__(self):
        # Use default application ID to avoid AppSettings recursion during initialization
        application_id = "ie.fio.dfakeseeder"

        super().__init__(
            application_id=application_id,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        logger.info("Startup", extra={"class_name": self.__class__.__name__})
        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

    def do_activate(self):
        with logger.performance.operation_context("do_activate", self.__class__.__name__):
            logger.debug("do_activate() started", self.__class__.__name__)
            logger.info("Run Controller", self.__class__.__name__)

            # Ensure resource paths are set up before creating Model
            with logger.performance.operation_context("setup_resource_paths", self.__class__.__name__):
                logger.debug(f"DFS_PATH before setup: {os.environ.get('DFS_PATH')}", self.__class__.__name__)
                AppInitializationHelper.setup_resource_paths()
                logger.debug(f"DFS_PATH after setup: {os.environ.get('DFS_PATH')}", self.__class__.__name__)

            # The Model manages the data and logic
            with logger.performance.operation_context("model_creation", self.__class__.__name__):
                logger.debug("About to create Model instance", self.__class__.__name__)
                self.model = Model()
                logger.debug("Model creation completed successfully", self.__class__.__name__)

            # The View manages the user interface
            with logger.performance.operation_context("view_creation", self.__class__.__name__):
                logger.debug("About to create View instance", self.__class__.__name__)
                self.view = View(self)
                logger.debug("View creation completed successfully", self.__class__.__name__)

            # The Controller manages the interactions between the Model and View
            with logger.performance.operation_context("controller_creation", self.__class__.__name__):
                logger.debug("About to create Controller instance", self.__class__.__name__)
                self.controller = Controller(self.view, self.model)
                logger.debug("Controller creation completed", self.__class__.__name__)

            # Start the controller
            with logger.performance.operation_context("controller_start", self.__class__.__name__):
                logger.debug("About to start controller", self.__class__.__name__)
                self.controller.run()
                logger.debug("Controller started", self.__class__.__name__)

            # Show the window
            with logger.performance.operation_context("window_show", self.__class__.__name__):
                logger.debug("About to show window", self.__class__.__name__)
                self.view.window.show()
                logger.debug("Window shown", self.__class__.__name__)

    def handle_settings_changed(self, source, key, value):
        logger.info("Settings changed", extra={"class_name": self.__class__.__name__})


app = typer.Typer()


@app.command()
def run():
    """Run the DFakeSeeder application with proper initialization."""
    try:
        # Perform full application initialization (locale, paths, settings)
        AppInitializationHelper.perform_full_initialization()

        # Create and run the application
        d = DFakeSeeder()
        d.run()

    except Exception as e:
        logger.error(f"Failed to run DFakeSeeder application: {e}")
        logger.debug("Failed to start application: ...", "DFakeSeeder")


# If the script is run directly (rather than imported as a module), create
# an instance of the UI class
if __name__ == "__main__":
    app()
