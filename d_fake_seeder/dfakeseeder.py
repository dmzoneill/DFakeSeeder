# fmt: off
# isort: skip_file
from typing import Any
import os
import sys

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")

import typer  # noqa: E402
from gi.repository import Gio  # noqa
from gi.repository import Gtk  # noqa: E402

from d_fake_seeder.controller import Controller  # noqa: E402
from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.app_initialization import (  # noqa: E402
    AppInitializationHelper,
)
from d_fake_seeder.lib.util.single_instance import MultiMethodSingleInstance  # noqa: E402
from d_fake_seeder.model import Model  # noqa: E402
from d_fake_seeder.view import View  # noqa: E402

# fmt: on

# Import the Model, View, and Controller classes from their respective modules


class DFakeSeeder(Gtk.Application):
    def __init__(self) -> None:
        # Use default application ID to avoid AppSettings recursion during initialization
        application_id = "ie.fio.dfakeseeder"

        # GTK4 single-instance support - this is the primary mechanism
        # If another instance exists, it will receive 'activate' signal instead
        super().__init__(
            application_id=application_id,
            flags=Gio.ApplicationFlags.FLAGS_NONE,  # Default: single instance
        )
        logger.trace("Startup", extra={"class_name": self.__class__.__name__})

        # Track if we've shown the UI (for single-instance handling)
        self.ui_initialized = False

        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

    def do_activate(self) -> None:
        """
        GTK4 single-instance handler.

        This is called when:
        1. First instance starts (ui_initialized=False)
        2. Another instance tries to start (GTK4 passes activate to existing instance)
        """
        with logger.performance.operation_context("do_activate", self.__class__.__name__):
            logger.info("do_activate() started", self.__class__.__name__)

            # If UI already initialized, this is a second instance trying to start
            if self.ui_initialized:
                logger.info(
                    "Existing instance detected - presenting existing window (GTK4 Application Registration)",
                    extra={"class_name": self.__class__.__name__},
                )
                # Just present the existing window
                if hasattr(self, "view") and self.view and hasattr(self.view, "window"):  # type: ignore[has-type]
                    self.view.window.present()  # type: ignore[has-type]
                return

            logger.trace("First instance - initializing UI", self.__class__.__name__)

            # Ensure resource paths are set up before creating Model
            with logger.performance.operation_context("setup_resource_paths", self.__class__.__name__):
                logger.trace(
                    f"DFS_PATH before setup: {os.environ.get('DFS_PATH')}",
                    self.__class__.__name__,
                )
                AppInitializationHelper.setup_resource_paths()
                logger.trace(
                    f"DFS_PATH after setup: {os.environ.get('DFS_PATH')}",
                    self.__class__.__name__,
                )

            # The Model manages the data and logic
            with logger.performance.operation_context("model_creation", self.__class__.__name__):
                logger.trace("About to create Model instance", self.__class__.__name__)
                self.model = Model()
                logger.info("Model creation completed successfully", self.__class__.__name__)

            # The View manages the user interface
            with logger.performance.operation_context("view_creation", self.__class__.__name__):
                logger.trace("About to create View instance", self.__class__.__name__)
                self.view = View(self)
                logger.info("View creation completed successfully", self.__class__.__name__)

            # The Controller manages the interactions between the Model and View
            with logger.performance.operation_context("controller_creation", self.__class__.__name__):
                logger.trace("About to create Controller instance", self.__class__.__name__)
                self.controller = Controller(self.view, self.model)
                logger.trace("Controller creation completed", self.__class__.__name__)

            # Start the controller
            with logger.performance.operation_context("controller_start", self.__class__.__name__):
                logger.trace("About to start controller", self.__class__.__name__)
                self.controller.run()
                logger.info("Controller started", self.__class__.__name__)

            # Show the window
            with logger.performance.operation_context("window_show", self.__class__.__name__):
                logger.trace("About to show window", self.__class__.__name__)
                self.view.window.show()

                # Check if we should start minimized
                if self.settings.start_minimized:
                    logger.info("Starting minimized as per settings", self.__class__.__name__)
                    self.view.window.minimize()
                    # If minimize_to_tray is also enabled, hide the window
                    if self.settings.minimize_to_tray:
                        self.view.window.hide()

                logger.trace("Window shown", self.__class__.__name__)

            # Mark UI as initialized
            self.ui_initialized = True

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace("Settings changed", extra={"class_name": self.__class__.__name__})


app = typer.Typer()


def _show_console_message(detection_method: str) -> Any:
    """Show console message when another instance is detected before GTK initialization"""
    print(f"\nDFakeSeeder is already running (detected via {detection_method})")
    print("Existing instance will be brought to front.\n")


@app.command()
def run() -> Any:
    """Run the DFakeSeeder application with proper initialization."""
    try:
        # Perform full application initialization (locale, paths, settings)
        AppInitializationHelper.perform_full_initialization()

        # ========== MULTI-METHOD SINGLE INSTANCE CHECK ==========
        # Check using D-Bus, Socket, and PID file BEFORE creating GTK app
        # This provides defense-in-depth before GTK4's single-instance mechanism
        logger.trace("Checking for existing instance using multi-method approach", "DFakeSeeder")

        instance_checker = MultiMethodSingleInstance(
            app_name="dfakeseeder-main", dbus_service="ie.fio.dfakeseeder", use_pidfile=True
        )

        is_running, detected_by = instance_checker.is_already_running()

        if is_running:
            logger.info(
                f"Existing instance detected via {detected_by} - exiting",
                extra={"class_name": "DFakeSeeder"},
            )
            _show_console_message(detected_by)  # type: ignore[arg-type]
            sys.exit(0)

        logger.trace(
            "No existing instance detected - proceeding with application startup",
            "DFakeSeeder",
        )

        # Create and run the application
        # GTK4 will provide additional single-instance protection
        d = DFakeSeeder()
        exit_code = d.run()

        # Cleanup locks
        instance_checker.cleanup()

        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"Failed to run DFakeSeeder application: {e}")
        logger.error("Failed to start application: ...", "DFakeSeeder")
        sys.exit(1)


# If the script is run directly (rather than imported as a module), create
# an instance of the UI class
if __name__ == "__main__":
    app()
