# fmt: off
# isort: skip_file
import gi

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa

# fmt: on


class States(Component, ColumnTranslationMixin):
    def __init__(self, builder, model):

        logger.debug("States.__init__() started", "States")
        super().__init__()
        ColumnTranslationMixin.__init__(self)
        logger.debug(
            "Super initialization completed (took {(super_end - super_start)*1000:.1f}ms)",
            "UnknownClass",
        )
        self.builder = builder
        self.model = model
        # Subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.track_signal(
            self.settings,
            self.settings.connect("attribute-changed", self.handle_settings_changed),
        )
        self.states_columnview = self.builder.get_object("states_columnview")
        logger.debug("Basic setup completed (took ms)", "States")
        # PERFORMANCE OPTIMIZATION: Create essential column immediately, defer the rest
        self.create_essential_columns_only()
        logger.debug(
            "Essential column creation completed (took {(columns_end - columns_start)*1000:.1f}ms)",
            "UnknownClass",
        )
        logger.debug("States.__init__() TOTAL TIME: ms", "States")

    def create_columns(self):

        # Create the column for the tracker name
        tracker_col = Gtk.ColumnViewColumn()
        tracker_col.set_visible(True)  # Set column visibility
        tracker_col.set_expand(True)
        # Register tracker column for translation
        self.register_translatable_column(self.states_columnview, tracker_col, "tracker", "states")
        # Create a custom factory for the tracker column
        tracker_factory = Gtk.SignalListItemFactory()
        self.track_signal(
            tracker_factory,
            tracker_factory.connect("setup", self.setup_tracker_factory),
        )
        self.track_signal(tracker_factory, tracker_factory.connect("bind", self.bind_tracker_factory))
        tracker_col.set_factory(tracker_factory)
        self.states_columnview.append_column(tracker_col)
        logger.debug(
            "Tracker column created successfully",
            "UnknownClass",
        )
        # Create the column for the count
        count_col = Gtk.ColumnViewColumn()
        count_col.set_visible(True)  # Set column visibility
        # Register count column for translation
        self.register_translatable_column(self.states_columnview, count_col, "count", "states")
        # Create a custom factory for the count column
        count_factory = Gtk.SignalListItemFactory()
        self.track_signal(count_factory, count_factory.connect("setup", self.setup_count_factory))
        self.track_signal(count_factory, count_factory.connect("bind", self.bind_count_factory))
        count_col.set_factory(count_factory)
        self.states_columnview.append_column(count_col)
        logger.debug(
            "Count column created successfully",
            "UnknownClass",
        )

    def create_essential_columns_only(self):
        """Create only the most essential column immediately for fast startup."""
        from gi.repository import GLib

        # Only create tracker column immediately (most important for display)
        tracker_col = Gtk.ColumnViewColumn()
        tracker_col.set_visible(True)
        tracker_col.set_expand(True)
        # Minimal factory setup without expensive operations
        tracker_factory = Gtk.SignalListItemFactory()
        self.track_signal(
            tracker_factory,
            tracker_factory.connect("setup", self.setup_tracker_factory),
        )
        self.track_signal(tracker_factory, tracker_factory.connect("bind", self.bind_tracker_factory))
        tracker_col.set_factory(tracker_factory)
        self.states_columnview.append_column(tracker_col)
        # Register for translation after creation to reduce blocking
        try:
            self.register_translatable_column(self.states_columnview, tracker_col, "tracker", "states")
        except Exception:
            pass  # Translation registration can fail, column still works
        logger.debug(
            "Essential tracker column created in {(tracker_end - tracker_start)*1000:.1f}ms",
            "UnknownClass",
        )
        # Schedule count column for background creation
        GLib.idle_add(self._create_count_column_background)

    def _create_count_column_background(self):
        """Create count column in background to avoid blocking startup."""

        logger.debug("Starting background count column creation", "States")
        try:
            # Create the column for the count
            count_col = Gtk.ColumnViewColumn()
            count_col.set_visible(True)
            # Create a custom factory for the count column
            count_factory = Gtk.SignalListItemFactory()
            self.track_signal(count_factory, count_factory.connect("setup", self.setup_count_factory))
            self.track_signal(count_factory, count_factory.connect("bind", self.bind_count_factory))
            count_col.set_factory(count_factory)
            self.states_columnview.append_column(count_col)
            # Register count column for translation
            try:
                self.register_translatable_column(self.states_columnview, count_col, "count", "states")
            except Exception:
                pass
            logger.debug("Background count column created successfully", "States")
        except Exception:
            logger.debug("Background count column creation error:", "States")
        return False  # Don't repeat this idle task

    def setup_tracker_factory(self, factory, item):
        item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def bind_tracker_factory(self, factory, item):
        # Get the item from the factory
        torrent_state = item.get_item()
        # Update the label with just the tracker data
        tracker_name = torrent_state.tracker if torrent_state.tracker is not None else ""
        item.get_child().set_label(tracker_name)

    def setup_count_factory(self, factory, item):
        item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def bind_count_factory(self, factory, item):
        # Get the item from the factory
        torrent_state = item.get_item()
        # Update the label with the count data
        item.get_child().set_label(str(torrent_state.count))

    def set_model(self, model):
        """Set the model for the states component."""
        logger.debug("States set_model", extra={"class_name": self.__class__.__name__})
        self.model = model
        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.track_signal(model, model.connect("language-changed", self.on_language_changed))
                logger.debug(
                    "Connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.debug(
                    f"Could not connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    # Method to update the ColumnView with compatible attributes
    def update_view(self, model, torrent, attribute):
        selection_model = Gtk.SingleSelection.new(model.get_trackers_liststore())
        self.states_columnview.set_model(selection_model)

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.debug(
            "States settings update",
            extra={"class_name": self.__class__.__name__},
        )

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
