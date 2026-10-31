"""
Sidebar Filter Component - Deluge-style torrent filtering.

Provides collapsible sections for:
- States (All, Seeding, Downloading, Active, Paused, etc.)
- Trackers (All, individual trackers with counts)
"""

from collections import namedtuple
from typing import Any
from urllib.parse import urlparse

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.lib.gi_gtk4 import Gtk
from d_fake_seeder.lib.logger import logger

# Groups an expander with its listbox so the sidebar keeps one attribute per section.
_Section = namedtuple("_Section", ["expander", "listbox"])


class FilterItem(Gtk.Box):
    """Single filter item with optional icon, label, and count badge."""

    def __init__(self, filter_id: Any, label: Any, icon_name: Any = "", count: Any = 0) -> None:
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

    def update_count(self, count: Any) -> None:
        """Update the count badge."""
        self.count_label.set_label(str(count))

    def get_filter_id(self) -> Any:
        """Return the filter identifier this item represents."""
        return self.filter_id


class Sidebar(Component):
    """
    Sidebar filter panel for torrents.

    Provides collapsible sections for filtering by:
    - State (All, Seeding, Downloading, etc.)
    - Tracker (All, individual trackers)
    """

    def __init__(self, builder: Any, model: Any) -> None:
        super().__init__()
        logger.info("Sidebar.__init__() started", extra={"class_name": self.__class__.__name__})

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

        # Track current selection (by filter dimension)
        self.selection: dict[str, Any] = {"state": None, "tracker": None}

        # Create collapsible sections
        self.states_section = self._create_states_section()
        self.trackers_section = self._create_trackers_section()

        logger.trace(
            "Sidebar.__init__() completed",
            extra={"class_name": self.__class__.__name__},
        )

    def _(self, text: Any) -> Any:
        """Get translation function from model's TranslationManager"""
        if self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def get_state_filters(self) -> Any:
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

    def _create_states_section(self) -> _Section:
        """Create the collapsible States section and return its expander/listbox."""
        # Expander for states
        expander = Gtk.Expander()
        expander.set_label(self._("States"))
        expander.set_expanded(True)
        expander.add_css_class("sidebar-expander")

        # ListBox for state items
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.add_css_class("sidebar-listbox")

        # Connect selection signal
        self.track_signal(
            listbox,
            listbox.connect("row-selected", self._on_state_selected),
        )

        # Add to expander
        expander.set_child(listbox)
        self.sidebar_box.append(expander)

        section = _Section(expander, listbox)
        self.states_section = section
        # Populate state items
        self._populate_states()
        return section

    def _create_trackers_section(self) -> _Section:
        """Create the collapsible Trackers section and return its expander/listbox."""
        # Expander for trackers
        expander = Gtk.Expander()
        expander.set_label(self._("Trackers"))
        expander.set_expanded(True)
        expander.add_css_class("sidebar-expander")

        # ListBox for tracker items
        listbox = Gtk.ListBox()
        listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        listbox.add_css_class("sidebar-listbox")

        # Connect selection signal
        self.track_signal(
            listbox,
            listbox.connect("row-selected", self._on_tracker_selected),
        )

        # Add to expander
        expander.set_child(listbox)
        self.sidebar_box.append(expander)

        return _Section(expander, listbox)

    def _populate_states(self) -> Any:
        """Populate the states list with filter items."""
        # Clear existing
        self.states_section.listbox.remove_all()

        # Add state filter items
        state_filters = self.get_state_filters()
        for state_id, label, icon in state_filters:
            count = self._get_state_count(state_id)
            filter_item = FilterItem(state_id, label, icon, count)
            self.states_section.listbox.append(filter_item)

        logger.trace(
            f"Populated {len(state_filters)} state filters",
            extra={"class_name": self.__class__.__name__},
        )

    def _populate_trackers(self) -> Any:
        """Populate the trackers list with filter items."""
        if not self.model:
            return

        # Clear existing
        self.trackers_section.listbox.remove_all()

        # Add "All" tracker item
        all_count = len(self.model.torrent_list) if hasattr(self.model, "torrent_list") else 0
        all_item = FilterItem("all", self._("All"), "", all_count)
        self.trackers_section.listbox.append(all_item)

        # Get tracker statistics from model
        tracker_stats = self._get_tracker_stats()

        # Add individual tracker items
        for domain, count, has_error in tracker_stats:
            icon = "dialog-warning-symbolic" if has_error else ""
            filter_item = FilterItem(domain, domain, icon, count)
            self.trackers_section.listbox.append(filter_item)

        logger.trace(
            f"Populated {len(tracker_stats) + 1} tracker filters",
            extra={"class_name": self.__class__.__name__},
        )

    @staticmethod
    def _state_matches(state_id: Any, active: Any, uploading: Any, progress: Any) -> bool:
        """Return whether a torrent's derived state matches ``state_id``.

        Unimplemented states (checking/error/queued) never match, preserving the
        previous behaviour where they always counted as zero.
        """
        if state_id == "seeding":
            return progress >= 100.0 and uploading
        if state_id == "downloading":
            return progress < 100.0 and active
        if state_id == "active":
            return bool(active)
        if state_id == "paused":
            return not active
        return False

    def _get_state_count(self, state_id: Any) -> Any:
        """Get count of torrents matching a state."""
        if not self.model or not hasattr(self.model, "torrent_list"):
            return 0

        if state_id == "all":
            return len(self.model.torrent_list)

        # Count torrents whose derived state matches
        count = 0
        for torrent in self.model.torrent_list:
            active = getattr(torrent, "active", True)
            uploading = getattr(torrent, "uploading", False)
            progress = getattr(torrent, "progress", 0.0)
            if self._state_matches(state_id, active, uploading, progress):
                count += 1

        return count

    def _get_tracker_stats(self) -> Any:
        """
        Get tracker statistics from model.

        Returns:
            List of (domain, count, has_error) tuples
        """
        if not self.model or not hasattr(self.model, "torrent_list"):
            return []

        tracker_stats: dict[str, dict[str, Any]] = {}

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
                except (AttributeError, TypeError, KeyError) as e:
                    logger.trace(
                        f"Error getting trackers for torrent: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

        # Sort by count (descending) then by name
        sorted_stats = sorted(
            [(domain, stats["count"], stats["has_error"]) for domain, stats in tracker_stats.items()],
            key=lambda x: (-x[1], x[0]),
        )

        return sorted_stats

    def _extract_domain(self, url: Any) -> Any:
        """Extract domain from tracker URL."""
        try:
            parsed = urlparse(url)
            return parsed.hostname or url
        except (ValueError, AttributeError):
            return url

    def _on_state_selected(self, listbox: Any, row: Any) -> None:
        """Handle state filter selection."""
        if row is None:
            return

        filter_item = row.get_child()
        state_id = filter_item.get_filter_id()

        logger.trace(
            f"State selected: {state_id}",
            extra={"class_name": self.__class__.__name__},
        )

        # Clear tracker selection
        self.trackers_section.listbox.unselect_all()

        # Apply filter
        if state_id == "all":
            self.model.clear_filter("state")  # type: ignore[attr-defined]
        else:
            self.model.set_filter_criteria("state", state_id)  # type: ignore[attr-defined]

        self.selection["state"] = state_id
        self.selection["tracker"] = None

    def _on_tracker_selected(self, listbox: Any, row: Any) -> None:
        """Handle tracker filter selection."""
        if row is None:
            return

        filter_item = row.get_child()
        tracker_id = filter_item.get_filter_id()

        logger.trace(
            f"Tracker selected: {tracker_id}",
            extra={"class_name": self.__class__.__name__},
        )

        # Clear state selection
        self.states_section.listbox.unselect_all()

        # Apply filter
        if tracker_id == "all":
            self.model.clear_filter("tracker")  # type: ignore[attr-defined]
        else:
            self.model.set_filter_criteria("tracker", tracker_id)  # type: ignore[attr-defined]

        self.selection["tracker"] = tracker_id
        self.selection["state"] = None

    def _update_state_counts(self) -> None:
        """Update the state rows' counts in-place."""
        state_filters = self.get_state_filters()
        for i in range(len(state_filters)):
            row = self.states_section.listbox.get_row_at_index(i)
            if row:
                filter_item = row.get_child()
                count = self._get_state_count(filter_item.filter_id)
                filter_item.update_count(count)

    def _existing_tracker_domains(self) -> set:
        """Return the tracker domains currently shown (excluding the "All" row)."""
        existing_domains = set()
        i = 1
        while True:
            row = self.trackers_section.listbox.get_row_at_index(i)
            if not row:
                break
            filter_item = row.get_child()
            if filter_item and hasattr(filter_item, "filter_id") and filter_item.filter_id != "all":
                existing_domains.add(filter_item.filter_id)
            i += 1
        return existing_domains

    def _update_tracker_counts_in_place(self, current_stats: Any) -> None:
        """Update the "All" row and each tracker row's count without rebuilding."""
        all_count = len(self.model.torrent_list) if self.model and hasattr(self.model, "torrent_list") else 0
        row = self.trackers_section.listbox.get_row_at_index(0)
        if row:
            filter_item = row.get_child()
            if filter_item:
                filter_item.update_count(all_count)

        stats_by_domain = {domain: count for domain, count, _ in current_stats}
        j = 1
        while True:
            row = self.trackers_section.listbox.get_row_at_index(j)
            if not row:
                break
            filter_item = row.get_child()
            if filter_item and hasattr(filter_item, "filter_id"):
                count = stats_by_domain.get(filter_item.filter_id, 0)
                filter_item.update_count(count)
            j += 1

    def _update_tracker_counts(self) -> None:
        """Update tracker counts in-place, rebuilding only when the tracker set changed."""
        current_stats = self._get_tracker_stats()
        current_domains = {domain for domain, _, _ in current_stats}

        if current_domains != self._existing_tracker_domains():
            # Tracker list changed (torrent added/removed) — full rebuild needed
            self._populate_trackers()
        else:
            # Only update counts in-place — no widget destruction
            self._update_tracker_counts_in_place(current_stats)

    def update_counts(self) -> None:
        """Update all filter item counts in-place, only rebuilding trackers when the set changes."""
        if not self.model:
            return

        self._update_state_counts()
        self._update_tracker_counts()

    def refresh_trackers(self) -> None:
        """Rebuild tracker list (when trackers change)."""
        self._populate_trackers()

    def set_model(self, model: Any) -> None:
        """Set the model and populate trackers."""
        logger.trace("Sidebar set_model", extra={"class_name": self.__class__.__name__})
        self.model = model

        # Update section headers with proper translations now that model is available
        self.states_section.expander.set_label(self._("States"))
        self.trackers_section.expander.set_label(self._("Trackers"))

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
            except (AttributeError, TypeError) as e:
                logger.trace(
                    f"Could not connect to language-changed signal: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update sidebar when torrents change."""
        self.update_counts()

    def get_widget(self) -> Any:
        """Get the main sidebar widget."""
        return self.sidebar_box

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        """Handle settings changes."""
        logger.trace(
            f"Sidebar settings changed: {key}",
            extra={"class_name": self.__class__.__name__},
        )

    def on_language_changed(self, model: Any, lang_code: Any) -> None:
        """Handle language changes."""
        logger.trace(
            f"Sidebar language changed: {lang_code}",
            extra={"class_name": self.__class__.__name__},
        )
        # Update section headers
        self.states_section.expander.set_label(self._("States"))
        self.trackers_section.expander.set_label(self._("Trackers"))

        # Rebuild states list with translated labels
        self._populate_states()

        # Rebuild trackers list with translated "All" label
        self._populate_trackers()

    def model_selection_changed(self, source: Any, model: Any, torrent: Any) -> Any:
        """Handle torrent selection changes (compatibility with States interface)."""
        # Sidebar doesn't need to respond to torrent selection
