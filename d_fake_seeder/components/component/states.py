import gi
from components.component.component import Component
from domain.app_settings import AppSettings
from lib.logger import logger
from lib.util.column_translation_mixin import ColumnTranslationMixin

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk  # noqa


class States(Component, ColumnTranslationMixin):
    def __init__(self, builder, model):
        import time

        start_time = time.time()
        logger.debug("States.__init__() started", "States")

        super_start = time.time()
        super().__init__()
        ColumnTranslationMixin.__init__(self)
        super_end = time.time()
        logger.debug("Super initialization completed (took {(super_end - super_start)*1000:.1f}ms)", "UnknownClass")

        setup_start = time.time()
        self.builder = builder
        self.model = model

        # Subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.states_columnview = self.builder.get_object("states_columnview")
        setup_end = time.time()
        logger.debug("Basic setup completed (took ms)", "States")

        # PERFORMANCE OPTIMIZATION: Create essential column immediately, defer the rest
        columns_start = time.time()
        self.create_essential_columns_only()
        columns_end = time.time()
        logger.debug("Essential column creation completed (took {(columns_end - columns_start)*1000:.1f}ms)", "UnknownClass")

        total_time = (time.time() - start_time) * 1000
        logger.debug("States.__init__() TOTAL TIME: ms", "States")

    def create_columns(self):
        import time

        # Create the column for the tracker name
        tracker_start = time.time()
        tracker_col = Gtk.ColumnViewColumn()
        tracker_col.set_visible(True)  # Set column visibility
        tracker_col.set_expand(True)
        tracker_basic = time.time()

        # Register tracker column for translation
        translation_start = time.time()
        self.register_translatable_column(self.states_columnview, tracker_col, "tracker", "states")
        translation_end = time.time()

        # Create a custom factory for the tracker column
        factory_start = time.time()
        tracker_factory = Gtk.SignalListItemFactory()
        tracker_factory.connect("setup", self.setup_tracker_factory)
        tracker_factory.connect("bind", self.bind_tracker_factory)
        tracker_col.set_factory(tracker_factory)
        factory_end = time.time()

        append_start = time.time()
        self.states_columnview.append_column(tracker_col)
        append_mid = time.time()

        tracker_total = time.time() - tracker_start
        logger.debug("Tracker column: basic={((tracker_basic - tracker_start)*1000):.1f}ms, translation={((translation_end - translation_start)*1000):.1f}ms, factory={((factory_end - factory_start)*1000):.1f}ms, append={((append_mid - append_start)*1000):.1f}ms, TOTAL={tracker_total*1000:.1f}ms", "UnknownClass")

        # Create the column for the count
        count_start = time.time()
        count_col = Gtk.ColumnViewColumn()
        count_col.set_visible(True)  # Set column visibility
        count_basic = time.time()

        # Register count column for translation
        count_trans_start = time.time()
        self.register_translatable_column(self.states_columnview, count_col, "count", "states")
        count_trans_end = time.time()

        # Create a custom factory for the count column
        count_factory_start = time.time()
        count_factory = Gtk.SignalListItemFactory()
        count_factory.connect("setup", self.setup_count_factory)
        count_factory.connect("bind", self.bind_count_factory)
        count_col.set_factory(count_factory)
        count_factory_end = time.time()

        count_append_start = time.time()
        self.states_columnview.append_column(count_col)
        count_append_end = time.time()

        count_total = time.time() - count_start
        logger.debug("Count column: basic={((count_basic - count_start)*1000):.1f}ms, translation={((count_trans_end - count_trans_start)*1000):.1f}ms, factory={((count_factory_end - count_factory_start)*1000):.1f}ms, append={((count_append_end - count_append_start)*1000):.1f}ms, TOTAL={count_total*1000:.1f}ms", "UnknownClass")

    def create_essential_columns_only(self):
        """Create only the most essential column immediately for fast startup."""
        import time
        from gi.repository import GLib

        # Only create tracker column immediately (most important for display)
        tracker_start = time.time()
        tracker_col = Gtk.ColumnViewColumn()
        tracker_col.set_visible(True)
        tracker_col.set_expand(True)

        # Minimal factory setup without expensive operations
        tracker_factory = Gtk.SignalListItemFactory()
        tracker_factory.connect("setup", self.setup_tracker_factory)
        tracker_factory.connect("bind", self.bind_tracker_factory)
        tracker_col.set_factory(tracker_factory)

        self.states_columnview.append_column(tracker_col)

        # Register for translation after creation to reduce blocking
        try:
            self.register_translatable_column(self.states_columnview, tracker_col, "tracker", "states")
        except Exception:
            pass  # Translation registration can fail, column still works

        tracker_end = time.time()
        logger.debug("Essential tracker column created in {(tracker_end - tracker_start)*1000:.1f}ms", "UnknownClass")

        # Schedule count column for background creation
        GLib.idle_add(self._create_count_column_background)

    def _create_count_column_background(self):
        """Create count column in background to avoid blocking startup."""
        import time

        bg_start = time.time()
        logger.debug("Starting background count column creation", "States")

        try:
            # Create the column for the count
            count_col = Gtk.ColumnViewColumn()
            count_col.set_visible(True)

            # Create a custom factory for the count column
            count_factory = Gtk.SignalListItemFactory()
            count_factory.connect("setup", self.setup_count_factory)
            count_factory.connect("bind", self.bind_count_factory)
            count_col.set_factory(count_factory)

            self.states_columnview.append_column(count_col)

            # Register count column for translation
            try:
                self.register_translatable_column(self.states_columnview, count_col, "count", "states")
            except Exception:
                pass

            bg_end = time.time()
            bg_time = (bg_end - bg_start) * 1000
            logger.debug("Background count column created in ms", "States")

        except Exception as e:
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
        logger.info("States set_model", extra={"class_name": self.__class__.__name__})
        self.model = model

        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.model.connect("language-changed", self.on_language_changed)
                logger.debug(
                    "Connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.debug(
                    f"Could not connect to language-changed signal: {e}", extra={"class_name": self.__class__.__name__}
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
