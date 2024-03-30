import gi

gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa


class PreferencesDialog(Gtk.Dialog):
    def __init__(self, parent):
        Gtk.Dialog.__init__(
            self,
            "Preferences",
            parent,
            0,
            (
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )

        self.set_default_size(250, 200)

        # Load the preferences UI from a XML file
        builder = Gtk.Builder()
        builder.add_from_file("ui/preferences.xml")

        # Retrieve the main preferences box from the builder
        preferences_box = builder.get_object("preferences_box")

        # Get the content area of the dialog
        content_area = self.get_content_area()

        # Add the preferences box to the content area
        content_area.add(preferences_box)
        content_area.show_all()


# Create a main window to demonstrate the preferences dialog
class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Main Window")
        self.set_default_size(200, 200)

        button = Gtk.Button(label="Open Preferences")
        button.connect("clicked", self.on_preferences_clicked)
        self.add(button)

    def on_preferences_clicked(self, widget):
        dialog = PreferencesDialog(self)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            print("OK button clicked")
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel button clicked")

        dialog.destroy()


win = MainWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
