import gi

# Ensure the correct version of Gtk is used
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib, Gdk
import cairo

# Import the Model, View, and Controller classes from their respective modules
from lib.model import Model
from lib.view import View
from lib.controller import Controller
from lib.settings import Settings
from lib.logger import logger


class DFakeSeeder:
    def __init__(self):
        logger.info("Startup", extra={"class_name": self.__class__.__name__})
        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)
        self.show_splash_screen()

    def show_splash_screen(self):
        logger.info("Splash", extra={"class_name": self.__class__.__name__})
        # Create a window
        self.splash_window = Gtk.Window()
        self.splash_window.set_title("Splash Screen")
        self.splash_window.set_default_size(1024, 381)
        self.splash_window.set_decorated(False)
        self.splash_window.set_position(Gtk.WindowPosition.CENTER)
        self.splash_window.set_app_paintable(True)
        self.splash_window.connect("draw", self.on_draw)

        # Load and display the splash screen image
        image = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file("images/dfakeseeder-logo.png")
        image.set_from_pixbuf(pixbuf)
        self.splash_window.add(image)

        # Show the window and start the main loop
        self.splash_window.show_all()
        GLib.timeout_add_seconds(2, self.show_main_window)
        Gtk.main()

    def delayed_execution(self):
        logger.info("Run Controller", extra={"class_name": self.__class__.__name__})
        # Start the controller
        self.controller.run()

    def show_main_window(self):
        logger.info("Main window", extra={"class_name": self.__class__.__name__})
        # Close the splash window
        if self.splash_window:
            self.splash_window.destroy()

        # The Model manages the data and logic
        self.model = Model()
        # The View manages the user interface
        self.view = View()
        # The Controller manages the interactions between the Model and View
        self.controller = Controller(self.view, self.model)

        # allow the window to draw before executing the view/model
        GLib.timeout_add_seconds(2, self.delayed_execution)

        self.view.window.show_all()
        Gtk.main()

    def on_draw(self, window, cr):
        logger.info("Draw pixbuf", extra={"class_name": self.__class__.__name__})
        # Set the background color and clear the window
        cr.set_source_rgba(0, 0, 0, 0.8)
        cr.set_operator(cairo.Operator.SOURCE)
        cr.paint()

        # Draw the splash screen image in the center of the window
        image = window.get_child()
        allocation = window.get_allocation()
        x = (allocation.width - image.get_allocated_width()) / 2
        y = (allocation.height - image.get_allocated_height()) / 2
        Gdk.cairo_set_source_pixbuf(cr, image.get_pixbuf(), x, y)
        cr.paint()
        return False

    def handle_settings_changed(self, source, key, value):
        logger.info("Settings changed", extra={"class_name": self.__class__.__name__})
        # print(key + " = " + value)


# If the script is run directly (rather than imported as a module), create an instance of the UI class
if __name__ == "__main__":
    DFakeSeeder()
