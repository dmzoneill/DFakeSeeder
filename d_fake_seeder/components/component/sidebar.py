"""
Sidebar Filter Component - Deluge-style torrent filtering.

Provides collapsible sections for:
- States (All, Seeding, Downloading, Active, Paused, etc.)
- Trackers (All, individual trackers with counts)
"""

# isort: skip_file

# fmt: off
import gi

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.logger import logger

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

# fmt: on


class FilterItem(Gtk.Box):
    """Single filter item with optional icon, label, and count badge."""

    def __init__(self, filter_id, label, icon_name="", count=0):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        self.filter_id = filter_id
        self.add_css_class("filter-item")

        # Icon (if provided)
        if icon_name:
            self.icon = Gtk.Image.new_from_icon_name(icon_name)
            self.icon.set_pixel_size(16)
            self.append(self.icon)

        # Label
        self.label = Gtk.Label(label=label)
        self.label.set_hexpand(True)
        self.label.set_xalign(0)
        self.append(self.label)

        # Count badge
        self.count_label = Gtk.Label(label=str(count))
        self.count_label.add_css_class("count-badge")
        self.append(self.count_label)

        # Make it selectable
        self.set_margin_start(4)
        self.set_margin_end(4)
        self.set_margin_top(2)
        self.set_margin_bottom(2)

    def update_count(self, count):
        """Update the count badge."""
        self.count_label.set_label(str(count))


class Sidebar(Component):
    """
    Sidebar filter panel for torrents.

    Provides collapsible sections for filtering by:
    - State (All, Seeding, Downloading, etc.)
    - Tracker (All, individual trackers)
    """

    def __init__(self, builder, model):
        super().__init__()
        logger.debug("Sidebar.__init__() started", extra={"class_name": self.__class__.__name__})

        self.builder = builder
        self.model = model

        # Subscribe to settings
        self.settings = AppSettings.get_instance()
        self.track_signal(
            self.settings,
            self.settings.connect("attribute-changed", self.handle_settings_changed),
        )

        # Create main container
        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sidebar_box.set_size_request(200, -1)
        self.sidebar_box.add_css_class("sidebar")

        # Create states section
        self._create_states_section()

        # Create trackers section
        self._create_trackers_section()

        # Track current selection
        self.selected_state = None
        self.selected_tracker = None

        logger.debug("Sidebar.__init__() completed", extra={"class_name": self.__class__.__name__})

    def _(self, text):
        """Get translation function from model's TranslationManager"""
        if self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def get_state_filters(self):
        """Get state filter definitions with translated labels (id, label, icon)"""
        _ = self._
        return [
            ("all", _("All"), ""),
            ("downloading", _("Downloading"), "folder-download-symbolic"),
            ("seeding", _("Seeding"), "folder-upload-symbolic"),
            ("active", _("Active"), "media-playback-start-symbolic"),
            ("paused", _("Paused"), "media-playback-pause-symbolic"),
            ("checking", _("Checking"), "system-search-symbolic"),
            ("error", _("Error"), "dialog-error-symbolic"),
            ("queued", _("Queued"), "view-list-symbolic"),
        ]

    def _create_states_section(self):
        """Create the collapsible States section."""
        # Expander for states
        self.states_expander = Gtk.Expander()
        self.states_expander.set_label(self._("States"))
        self.states_expander.set_expanded(True)
        self.states_expander.add_css_class("sidebar-expander")

        # ListBox for state items
        self.states_listbox = Gtk.ListBox()
        self.states_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.states_listbox.add_css_class("sidebar-listbox")

        # Connect selection signal
        self.track_signal(
            self.states_listbox,
            self.states_listbox.connect("row-selected", self._on_state_selected),
        )

        # Add to expander
        self.states_expander.set_child(self.states_listbox)
        self.sidebar_box.append(self.states_expander)

        # Populate state items
        self._populate_states()

    def _create_trackers_section(self):
        """Create the collapsible Trackers section."""
        # Expander for trackers
        self.trackers_expander = Gtk.Expander()
        self.trackers_expander.set_label(self._("Trackers"))
        self.trackers_expander.set_expanded(True)
        self.trackers_expander.add_css_class("sidebar-expander")

        # ListBox for tracker items
        self.trackers_listbox = Gtk.ListBox()
        self.trackers_listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.trackers_listbox.add_css_class("sidebar-listbox")

        # Connect selection signal
        self.track_signal(
            self.trackers_listbox,
            self.trackers_listbox.connect("row-selected", self._on_tracker_selected),
        )

        # Add to expander
        self.trackers_expander.set_child(self.trackers_listbox)
        self.sidebar_box.append(self.trackers_expander)

    def _populate_states(self):
        """Populate the states list with filter items."""
        # Clear existing
        while True:
            row = self.states_listbox.get_row_at_index(0)
            if row is None:
                break
            self.states_listbox.remove(row)

        # Add state filter items
        state_filters = self.get_state_filters()
        for state_id, label, icon in state_filters:
            count = self._get_state_count(state_id)
            filter_item = FilterItem(state_id, label, icon, count)
            self.states_listbox.append(filter_item)

        logger.debug(
            f"Populated {len(state_filters)} state filters",
            extra={"class_name": self.__class__.__name__},
        )

    def _populate_trackers(self):
        """Populate the trackers list with filter items."""
        if not self.model:
            return

        # Clear existing
        while True:
            row = self.trackers_listbox.get_row_at_index(0)
            if row is None:
                break
            self.trackers_listbox.remove(row)

        # Add "All" tracker item
        all_count = len(self.model.torrent_list) if hasattr(self.model, "torrent_list") else 0
        all_item = FilterItem("all", self._("All"), "", all_count)
        self.trackers_listbox.append(all_item)

        # Get tracker statistics from model
        tracker_stats = self._get_tracker_stats()

        # Add individual tracker items
        for domain, count, has_error in tracker_stats:
            icon = "dialog-warning-symbolic" if has_error else ""
            filter_item = FilterItem(domain, domain, icon, count)
            self.trackers_listbox.append(filter_item)

        logger.debug(
            f"Populated {len(tracker_stats) + 1} tracker filters",
            extra={"class_name": self.__class__.__name__},
        )

    def _get_state_count(self, state_id):
        """Get count of torrents matching a state."""
        if not self.model or not hasattr(self.model, "torrent_list"):
            return 0

        if state_id == "all":
            return len(self.model.torrent_list)

        # Count torrents by derived state (based on available torrent properties)
        count = 0
        for torrent in self.model.torrent_list:
            # Get torrent attributes
            active = getattr(torrent, "active", True)
            uploading = getattr(torrent, "uploading", False)
            progress = getattr(torrent, "progress", 0.0)

            # Derive state from properties
            if state_id == "seeding":
                # Seeding: progress is 100% and uploading
                if progress >= 100.0 and uploading:
                    count += 1
            elif state_id == "downloading":
                # Downloading: progress < 100%
                if progress < 100.0 and active:
                    count += 1
            elif state_id == "active":
                # Active: active flag is true
                if active:
                    count += 1
            elif state_id == "paused":
                # Paused: active flag is false
                if not active:
                    count += 1
            elif state_id == "checking":
                # Checking: Not implemented yet, always 0
                pass
            elif state_id == "error":
                # Error: Not implemented yet, always 0
                pass
            elif state_id == "queued":
                # Queued: Not implemented yet, always 0
                pass

        return count

    def _get_tracker_stats(self):
        """
        Get tracker statistics from model.

        Returns:
            List of (domain, count, has_error) tuples
        """
        if not self.model or not hasattr(self.model, "torrent_list"):
            return []

        tracker_stats = {}

        for torrent in self.model.torrent_list:
            # Get trackers from torrent file
            if torrent.is_ready():
                try:
                    trackers = torrent.get_torrent_file().get_trackers()
                    for tracker_url in trackers:
                        domain = self._extract_domain(tracker_url)

                        if domain not in tracker_stats:
                            tracker_stats[domain] = {"count": 0, "has_error": False}

                        tracker_stats[domain]["count"] += 1

                        # Note: Error status would need to come from seeder, not implemented yet
                except Exception as e:
                    logger.debug(
                        f"Error getting trackers for torrent: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

        # Sort by count (descending) then by name
        sorted_stats = sorted(
            [(domain, stats["count"], stats["has_error"]) for domain, stats in tracker_stats.items()],
            key=lambda x: (-x[1], x[0]),
        )

        return sorted_stats

    def _extract_domain(self, url):
        """Extract domain from tracker URL."""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            return parsed.hostname or url
        except Exception:
            return url

    def _on_state_selected(self, listbox, row):
        """Handle state filter selection."""
        if row is None:
            return

        filter_item = row.get_child()
        state_id = filter_item.filter_id

        logger.debug(
            f"State selected: {state_id}",
            extra={"class_name": self.__class__.__name__},
        )

        # Clear tracker selection
        self.trackers_listbox.unselect_all()

        # Apply filter
        if state_id == "all":
            self.model.clear_filter("state")
        else:
            self.model.set_filter_criteria("state", state_id)

        self.selected_state = state_id
        self.selected_tracker = None

    def _on_tracker_selected(self, listbox, row):
        """Handle tracker filter selection."""
        if row is None:
            return

        filter_item = row.get_child()
        tracker_id = filter_item.filter_id

        logger.debug(
            f"Tracker selected: {tracker_id}",
            extra={"class_name": self.__class__.__name__},
        )

        # Clear state selection
        self.states_listbox.unselect_all()

        # Apply filter
        if tracker_id == "all":
            self.model.clear_filter("tracker")
        else:
            self.model.set_filter_criteria("tracker", tracker_id)

        self.selected_tracker = tracker_id
        self.selected_state = None

    def update_counts(self):
        """Update all filter item counts."""
        if not self.model:
            return

        # Update state counts
        state_filters = self.get_state_filters()
        for i in range(len(state_filters)):
            row = self.states_listbox.get_row_at_index(i)
            if row:
                filter_item = row.get_child()
                count = self._get_state_count(filter_item.filter_id)
                filter_item.update_count(count)

        # Update tracker counts - full rebuild since trackers can be added/removed
        self._populate_trackers()

    def refresh_trackers(self):
        """Rebuild tracker list (when trackers change)."""
        self._populate_trackers()

    def set_model(self, model):
        """Set the model and populate trackers."""
        logger.debug("Sidebar set_model", extra={"class_name": self.__class__.__name__})
        self.model = model

        # Update section headers with proper translations now that model is available
        self.states_expander.set_label(self._("States"))
        self.trackers_expander.set_label(self._("Trackers"))

        # Rebuild state labels with proper translations now that model is available
        self._populate_states()

        # Populate trackers now that we have a model
        self._populate_trackers()

        # Connect to language change if available
        if self.model and hasattr(self.model, "connect"):
            try:
                self.track_signal(
                    model,
                    model.connect("language-changed", self.on_language_changed),
                )
            except Exception as e:
                logger.debug(
                    f"Could not connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    def update_view(self, model, torrent, attribute):
        """Update sidebar when torrents change."""
        self.update_counts()

    def get_widget(self):
        """Get the main sidebar widget."""
        return self.sidebar_box

    def handle_settings_changed(self, source, key, value):
        """Handle settings changes."""
        logger.debug(
            f"Sidebar settings changed: {key}",
            extra={"class_name": self.__class__.__name__},
        )

    def on_language_changed(self, model, lang_code):
        """Handle language changes."""
        logger.debug(
            f"Sidebar language changed: {lang_code}",
            extra={"class_name": self.__class__.__name__},
        )
        # Update section headers
        self.states_expander.set_label(self._("States"))
        self.trackers_expander.set_label(self._("Trackers"))

        # Rebuild states list with translated labels
        self._populate_states()

        # Rebuild trackers list with translated "All" label
        self._populate_trackers()

    def model_selection_changed(self, source, model, torrent):
        """Handle torrent selection changes (compatibility with States interface)."""
        # Sidebar doesn't need to respond to torrent selection
        pass
