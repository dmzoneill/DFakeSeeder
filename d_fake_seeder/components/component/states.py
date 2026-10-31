"""States component: tracker/count ColumnView for the DFakeSeeder main window."""

import contextlib
from typing import Any

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.gi_gtk4 import GLib, Gtk
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translation_mixin import ColumnTranslationMixin


class States(Component, ColumnTranslationMixin):
    """ColumnView component showing per-tracker torrent state counts."""

    def __init__(self, builder: Any, model: Any) -> None:

        logger.info("States.__init__() started", "States")
        super().__init__()
        ColumnTranslationMixin.__init__(self)
        logger.trace(
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
        logger.trace("Basic setup completed (took ms)", "States")
        # PERFORMANCE OPTIMIZATION: Create essential column immediately, defer the rest
        self.create_essential_columns_only()
        logger.trace(
            "Essential column creation completed (took {(columns_end - columns_start)*1000:.1f}ms)",
            "UnknownClass",
        )
        logger.trace("States.__init__() TOTAL TIME: ms", "States")

    def create_columns(self) -> None:
        """Create the tracker and count columns with their factories."""

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
        logger.trace(
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
        logger.trace(
            "Count column created successfully",
            "UnknownClass",
        )

    def create_essential_columns_only(self) -> None:
        """Create only the most essential column immediately for fast startup."""

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
        # Translation registration can fail, column still works
        with contextlib.suppress(AttributeError, TypeError, KeyError, ValueError):
            self.register_translatable_column(self.states_columnview, tracker_col, "tracker", "states")
        logger.trace(
            "Essential tracker column created in {(tracker_end - tracker_start)*1000:.1f}ms",
            "UnknownClass",
        )
        # Schedule count column for background creation
        GLib.idle_add(self._create_count_column_background)

    def _create_count_column_background(self) -> Any:
        """Create count column in background to avoid blocking startup."""

        logger.trace("Starting background count column creation", "States")
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
            with contextlib.suppress(AttributeError, TypeError, KeyError, ValueError):
                self.register_translatable_column(self.states_columnview, count_col, "count", "states")
            logger.info("Background count column created successfully", "States")
        except (AttributeError, TypeError, ValueError, GLib.Error):
            logger.error("Background count column creation error:", "States")
        return False  # Don't repeat this idle task  # type: ignore

    def setup_tracker_factory(self, factory: Any, item: Any) -> None:
        """Set up a list item widget for the tracker column."""
        item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def bind_tracker_factory(self, factory: Any, item: Any) -> None:
        """Bind a torrent state's tracker name to its list item label."""
        # Get the item from the factory
        torrent_state = item.get_item()
        # Update the label with just the tracker data
        tracker_name = torrent_state.tracker if torrent_state.tracker is not None else ""
        item.get_child().set_label(tracker_name)

    def setup_count_factory(self, factory: Any, item: Any) -> None:
        """Set up a list item widget for the count column."""
        item.set_child(Gtk.Label(halign=Gtk.Align.START))

    def bind_count_factory(self, factory: Any, item: Any) -> None:
        """Bind a torrent state's count to its list item label."""
        # Get the item from the factory
        torrent_state = item.get_item()
        # Update the label with the count data
        item.get_child().set_label(str(torrent_state.count))

    def set_model(self, model: Any) -> None:
        """Set the model for the states component."""
        logger.trace("States set_model", extra={"class_name": self.__class__.__name__})
        self.model = model
        # Connect to language change signals for column translation
        if self.model and hasattr(self.model, "connect"):
            try:
                self.track_signal(model, model.connect("language-changed", self.on_language_changed))
                logger.trace(
                    "Connected to language-changed signal for column translation",
                    extra={"class_name": self.__class__.__name__},
                )
            except (AttributeError, TypeError, GLib.Error) as e:
                logger.trace(
                    f"Could not connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    # Method to update the ColumnView with compatible attributes
    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Refresh the ColumnView selection model from the trackers liststore."""
        selection_model = Gtk.SingleSelection.new(model.get_trackers_liststore())
        self.states_columnview.set_model(selection_model)

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle an application settings change (no-op refresh hook)."""
        logger.trace(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_model_changed(self, source: Any, data_obj: Any, data_changed: Any) -> None:
        """Handle a model change notification."""
        logger.trace(
            "States settings update",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle an attribute change notification."""
        logger.trace(
            "Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def model_selection_changed(self, source: Any, model: Any, torrent: Any) -> Any:
        """Handle a selection change in the model."""
        logger.trace(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
