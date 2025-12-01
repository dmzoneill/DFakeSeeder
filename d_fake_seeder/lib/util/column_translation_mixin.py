"""
Column Translation Mixin

Provides reusable column translation functionality for ColumnView components.
This mixin integrates with the existing TranslationManager to support runtime
language switching for column headers.
"""

# fmt: off
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.column_translations import ColumnTranslations

# fmt: on


class ColumnTranslationMixin:
    """
    Mixin class providing column translation functionality for ColumnView components

    This mixin should be inherited by any component that manages ColumnView widgets
    and needs runtime column header translation support.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Track columns for translation updates
        self._translatable_columns = {}  # column_view -> [(column, property_name, column_type)]

        # Get settings instance for language access
        self.settings = AppSettings.get_instance()

    def register_translatable_column(self, column_view, column, property_name, column_type):
        """
        Register a column for runtime translation

        Args:
            column_view: The Gtk.ColumnView widget
            column: The Gtk.ColumnViewColumn instance
            property_name: Model property name for this column
            column_type: Type identifier for translation mapping ('torrent', 'peer', etc.)
        """
        if column_view not in self._translatable_columns:
            self._translatable_columns[column_view] = []

        self._translatable_columns[column_view].append((column, property_name, column_type))

        # Set initial translated title
        self._update_column_title(column, property_name, column_type)

        logger.debug(
            f"Registered translatable column: {property_name} ({column_type})",
            extra={"class_name": self.__class__.__name__},
        )

    def _update_column_title(self, column, property_name, column_type):
        """
        Update a single column's title with current translation

        Args:
            column: The Gtk.ColumnViewColumn instance
            property_name: Model property name
            column_type: Type identifier for translation mapping
        """
        try:
            translated_title = ColumnTranslations.get_column_title(column_type, property_name)
            column.set_title(translated_title)

            logger.debug(
                f"Updated column title: {property_name} -> '{translated_title}'",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Failed to update column title for {property_name}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def refresh_column_translations(self):
        """
        Refresh all registered column translations

        This method should be called when the language changes to update
        all column headers with new translations.
        """
        logger.debug("Refreshing column translations", self.__class__.__name__)
        logger.debug(
            f"Number of column views: {len(self._translatable_columns)}",
            self.__class__.__name__,
        )

        logger.debug(
            f"Refreshing column translations for {len(self._translatable_columns)} column views",
            extra={"class_name": self.__class__.__name__},
        )

        for column_view, columns in self._translatable_columns.items():
            logger.debug(f"Processing column view: {column_view}", self.__class__.__name__)
            logger.debug(f"Number of columns: {len(columns)}", self.__class__.__name__)
            for column, property_name, column_type in columns:
                logger.debug(
                    f"Updating column: {property_name} ({column_type})",
                    self.__class__.__name__,
                )
                self._update_column_title(column, property_name, column_type)

        logger.debug("Column translations refresh completed", self.__class__.__name__)

    def on_language_changed(self, model, lang_code):
        """
        Handle language change notification

        This method can be connected to the model's "language-changed" signal
        or called directly when language changes are detected.

        Args:
            model: The model that emitted the signal
            lang_code: The new language code
        """
        logger.debug("Language change received", self.__class__.__name__)
        logger.debug(f"Model: {model}", self.__class__.__name__)
        logger.debug(f"Language code: {lang_code}", self.__class__.__name__)
        logger.debug(
            f"Number of column views: {len(self._translatable_columns)}",
            self.__class__.__name__,
        )

        logger.debug(
            f"Column translation mixin received language change: {lang_code}",
            extra={"class_name": self.__class__.__name__},
        )

        # Refresh all column translations
        logger.debug("About to refresh column translations", self.__class__.__name__)
        self.refresh_column_translations()
        logger.debug("Column translations refresh completed", self.__class__.__name__)

    def create_translated_column(self, column_view, property_name, column_type, factory=None):
        """
        Helper method to create a column with translation support

        Args:
            column_view: The Gtk.ColumnView widget
            property_name: Model property name for this column
            column_type: Type identifier for translation mapping
            factory: Optional Gtk.ListItemFactory for the column

        Returns:
            The created Gtk.ColumnViewColumn instance
        """
        try:
            import gi

            gi.require_version("Gtk", "4.0")
            from gi.repository import Gtk

            # Create column
            if factory:
                column = Gtk.ColumnViewColumn.new(None, factory)
            else:
                # Create default factory if none provided
                factory = Gtk.SignalListItemFactory()
                column = Gtk.ColumnViewColumn.new(None, factory)

            # Register for translation
            self.register_translatable_column(column_view, column, property_name, column_type)

            # Add to column view
            column_view.append_column(column)

            logger.debug(
                f"Created translated column: {property_name} ({column_type})",
                extra={"class_name": self.__class__.__name__},
            )

            return column

        except Exception as e:
            logger.error(
                f"Failed to create translated column {property_name}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return None

    def get_column_count(self, column_view):
        """
        Get the number of registered translatable columns for a column view

        Args:
            column_view: The Gtk.ColumnView widget

        Returns:
            Number of registered columns
        """
        return len(self._translatable_columns.get(column_view, []))

    def clear_translatable_columns(self, column_view=None):
        """
        Clear translatable column registrations

        Args:
            column_view: Specific column view to clear, or None to clear all
        """
        if column_view:
            if column_view in self._translatable_columns:
                del self._translatable_columns[column_view]
                logger.debug(
                    "Cleared translatable columns for specific column view",
                    extra={"class_name": self.__class__.__name__},
                )
        else:
            self._translatable_columns.clear()
            logger.debug(
                "Cleared all translatable columns",
                extra={"class_name": self.__class__.__name__},
            )

    def cleanup_column_translations(self):
        """
        Clean up column translation resources

        Should be called when the component is being destroyed.
        """
        self.clear_translatable_columns()
        logger.debug(
            "Cleaned up column translation resources",
            extra={"class_name": self.__class__.__name__},
        )
