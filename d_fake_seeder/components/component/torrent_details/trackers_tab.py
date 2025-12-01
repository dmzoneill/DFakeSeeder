"""
Trackers tab for torrent details.

Displays torrent tracker information including primary and backup trackers.
"""

# fmt: off
from typing import Any, Dict, List

import gi

from .base_tab import BaseTorrentTab
from .tab_mixins import DataUpdateMixin, UIUtilityMixin

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa

# fmt: on


class TrackersTab(BaseTorrentTab, DataUpdateMixin, UIUtilityMixin):
    """
    Trackers tab component for displaying torrent tracker information.

    Shows primary and backup trackers with their URLs and status.
    """

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Trackers"

    @property
    def tab_widget_id(self) -> str:
        """Return the GTK widget ID for this tab."""
        return "trackers_tab"

    def _init_widgets(self) -> None:
        """Initialize Trackers tab widgets."""
        # Cache the main tab widget
        self._trackers_tab = self.get_widget("trackers_tab")
        self._trackers_grid_child = None

    def clear_content(self) -> None:
        """Clear the trackers tab content."""
        try:
            # Clear ALL children from the trackers tab, not just the grid
            if self._trackers_tab:
                self.remove_all_children(self._trackers_tab)
            self._trackers_grid_child = None

        except Exception as e:
            self.logger.error(f"Error clearing trackers tab content: {e}")

    def _remove_current_grid(self) -> None:
        """Remove the current grid child from the trackers tab."""
        try:
            # Clear ALL children to prevent accumulation
            if self._trackers_tab:
                self.remove_all_children(self._trackers_tab)
            self._trackers_grid_child = None

        except Exception as e:
            self.logger.error(f"Error removing trackers grid child: {e}")

    def update_content(self, attributes) -> None:
        """
        Update trackers tab content with torrent tracker data.

        Args:
            attributes: Attributes object from the torrent list
        """
        try:
            self.logger.debug(
                f"🔄 TRACKERS TAB: Starting update_content for attributes: {attributes}",
                extra={"class_name": self.__class__.__name__},
            )

            if attributes is None:
                self.logger.warning(
                    "🚨 TRACKERS TAB: Received None attributes in update_content",
                    extra={"class_name": self.__class__.__name__},
                )
                self._show_no_trackers_message()
                return

            # Remove existing content
            self.logger.debug(
                "🗑️ TRACKERS TAB: Removing existing grid content",
                extra={"class_name": self.__class__.__name__},
            )
            self._remove_current_grid()

            # Create new grid with proper styling
            self.logger.debug(
                "🏗️ TRACKERS TAB: Creating new grid",
                extra={"class_name": self.__class__.__name__},
            )
            self._trackers_grid_child = self._create_trackers_grid()

            # Get tracker information
            self.logger.debug(
                "🔍 TRACKERS TAB: Calling _get_tracker_data()",
                extra={"class_name": self.__class__.__name__},
            )
            trackers = self._get_tracker_data(attributes)
            self.logger.debug(
                f"📊 TRACKERS TAB: Retrieved {len(trackers) if trackers else 0} trackers from torrent",
                extra={"class_name": self.__class__.__name__},
            )

            if not trackers:
                self._show_no_trackers_message()
                return

            # Create grid rows for each tracker
            self._create_tracker_rows(trackers)

            # Add the grid to the tab
            if self._trackers_tab:
                self._trackers_tab.append(self._trackers_grid_child)

        except Exception as e:
            self.logger.error(f"Error updating trackers tab content: {e}")

    def _create_trackers_grid(self) -> Gtk.Grid:
        """
        Create a new grid for trackers with proper styling.

        Returns:
            Configured Grid widget
        """
        try:
            grid = Gtk.Grid()
            grid.set_visible(True)
            grid.set_column_spacing(self.ui_column_spacing_large)
            grid.set_row_spacing(self.ui_row_spacing)
            # Margins are now set in XML for consistency across all tabs
            # Removed: set_margin_start/end/top/bottom calls
            return grid

        except Exception as e:
            self.logger.error(f"Error creating trackers grid: {e}")
            return self.create_grid()  # Fallback to base grid

    def _get_tracker_data(self, attributes) -> list:
        """
        Get tracker data with live status from the torrent.

        Args:
            attributes: Attributes object from the torrent list

        Returns:
            List of tracker dictionaries with live status
        """
        try:
            self.logger.debug(
                "🚀 TRACKERS TAB: _get_tracker_data() started",
                extra={"class_name": self.__class__.__name__},
            )
            trackers: List[Dict[str, Any]] = []

            if not attributes:
                self.logger.warning(
                    "🚨 TRACKERS TAB: No attributes provided to _get_tracker_data",
                    extra={"class_name": self.__class__.__name__},
                )
                return trackers

            # Get the actual Torrent object from the model using the attributes
            torrent = self.model.get_torrent_by_attributes(attributes)
            if not torrent:
                self.logger.warning(
                    f"🚨 TRACKERS TAB: No torrent found for attributes {getattr(attributes, 'id', 'unknown')}",
                    extra={"class_name": self.__class__.__name__},
                )
                return trackers

            self.logger.debug(
                f"✅ TRACKERS TAB: Found torrent object with live tracker methods: "
                f"get_active_tracker_model={hasattr(torrent, 'get_active_tracker_model')}, "
                f"get_all_tracker_models={hasattr(torrent, 'get_all_tracker_models')}",
                extra={"class_name": self.__class__.__name__},
            )

            # Get live tracker models from torrent
            if hasattr(torrent, "get_all_tracker_models"):
                self.logger.debug(
                    "📡 TRACKERS TAB: Using live tracker models",
                    extra={"class_name": self.__class__.__name__},
                )
                tracker_models = torrent.get_all_tracker_models()

                for tracker_model in tracker_models:
                    try:
                        tracker_data = {
                            "url": tracker_model.get_property("url"),
                            "tier": tracker_model.get_property("tier"),
                            "type": ("Primary" if tracker_model.get_property("tier") == 0 else "Backup"),
                            "status": tracker_model.get_property("status"),
                            "seeders": tracker_model.get_property("seeders"),
                            "leechers": tracker_model.get_property("leechers"),
                            "last_announce": tracker_model.get_property("last_announce"),
                            "next_announce": tracker_model.get_property("next_announce"),
                            "response_time": tracker_model.get_property("average_response_time"),
                            "error_message": tracker_model.get_property("error_message"),
                            "success_rate": tracker_model.success_rate,
                            "health_status": ("Healthy" if tracker_model.is_healthy else "Unhealthy"),
                            "status_summary": tracker_model.get_status_summary(),
                            "timing_summary": tracker_model.get_timing_summary(),
                        }
                        trackers.append(tracker_data)
                    except Exception as e:
                        self.logger.debug(
                            f"Error processing tracker model: {e}",
                            extra={"class_name": self.__class__.__name__},
                        )

                self.logger.debug(
                    f"🎯 TRACKERS TAB: Retrieved {len(trackers)} live tracker models",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                # Fallback to static tracker information
                self.logger.debug(
                    "📁 TRACKERS TAB: Fallback to static tracker data",
                    extra={"class_name": self.__class__.__name__},
                )
                torrent_file = torrent.get_torrent_file()
                if torrent_file:
                    # Add primary announce URL
                    if hasattr(torrent_file, "announce") and torrent_file.announce:
                        trackers.append(
                            {
                                "url": torrent_file.announce,
                                "tier": 0,
                                "type": "Primary",
                                "status": "Unknown",
                                "seeders": 0,
                                "leechers": 0,
                                "status_summary": "No live data available",
                            }
                        )

                    # Add backup trackers from announce-list
                    if hasattr(torrent_file, "announce_list") and torrent_file.announce_list:
                        primary_url = getattr(torrent_file, "announce", None)
                        for tier_index, tracker_url in enumerate(torrent_file.announce_list):
                            if tracker_url != primary_url:
                                trackers.append(
                                    {
                                        "url": tracker_url,
                                        "tier": tier_index + 1,
                                        "type": "Backup",
                                        "status": "Unknown",
                                        "seeders": 0,
                                        "leechers": 0,
                                        "status_summary": "No live data available",
                                    }
                                )

            return trackers

        except Exception as e:
            self.logger.error(f"Error getting tracker data: {e}")
            return []

    def _create_tracker_rows(self, trackers: list) -> None:
        """
        Create grid rows for tracker data.

        Args:
            trackers: List of tracker dictionaries
        """
        try:
            # Create header row
            self._create_header_row()

            # Create data rows
            for row_index, tracker in enumerate(trackers):
                self._create_tracker_row(tracker, row_index + 1)  # +1 for header

        except Exception as e:
            self.logger.error(f"Error creating tracker rows: {e}")

    def _create_header_row(self) -> None:
        """Create header row for the trackers grid."""
        try:
            # Get translation function from model
            translate_func = (
                self.model.get_translate_func() if hasattr(self.model, "get_translate_func") else lambda x: x
            )

            headers = [
                translate_func("Type"),
                translate_func("Tier"),
                translate_func("URL"),
                translate_func("Status"),
                translate_func("Seeders"),
                translate_func("Leechers"),
                translate_func("Last Announce"),
            ]

            for col, header_text in enumerate(headers):
                header_label = Gtk.Label(label=header_text)
                header_label.set_visible(True)
                header_label.set_halign(Gtk.Align.START)
                header_label.add_css_class("heading")  # For styling
                if self._trackers_grid_child is not None:
                    self._trackers_grid_child.attach(header_label, col, 0, 1, 1)

        except Exception as e:
            self.logger.error(f"Error creating header row: {e}")

    def _create_tracker_row(self, tracker: dict, row: int) -> None:
        """
        Create a row for a tracker with live status information.

        Args:
            tracker: Tracker data dictionary with live status
            row: Row position in grid
        """
        try:
            # Type column
            type_label = Gtk.Label(label=tracker.get("type", "Unknown"))
            type_label.set_visible(True)
            type_label.set_halign(Gtk.Align.START)
            if self._trackers_grid_child is not None:
                self._trackers_grid_child.attach(type_label, 0, row, 1, 1)

            # Tier column
            tier_label = Gtk.Label(label=str(tracker.get("tier", 0)))
            tier_label.set_visible(True)
            tier_label.set_halign(Gtk.Align.START)
            if self._trackers_grid_child is not None:
                self._trackers_grid_child.attach(tier_label, 1, row, 1, 1)

            # URL column (selectable)
            url_label = Gtk.Label(label=tracker.get("url", "Unknown"))
            url_label.set_visible(True)
            url_label.set_halign(Gtk.Align.START)
            url_label.set_selectable(True)
            url_label.set_ellipsize(True)  # Ellipsize long URLs
            if self._trackers_grid_child is not None:
                self._trackers_grid_child.attach(url_label, 2, row, 1, 1)

            # Status column with live data
            status_text = tracker.get("status_summary", tracker.get("status", "Unknown"))
            status_label = Gtk.Label(label=status_text)
            status_label.set_visible(True)
            status_label.set_halign(Gtk.Align.START)

            # Add CSS class based on status for styling
            status = tracker.get("status", "unknown")
            if status == "working":
                status_label.add_css_class("success")
            elif status == "failed":
                status_label.add_css_class("error")
            elif status == "announcing":
                status_label.add_css_class("warning")

            if self._trackers_grid_child is not None:
                self._trackers_grid_child.attach(status_label, 3, row, 1, 1)

            # Seeders column
            seeders_text = str(tracker.get("seeders", 0)) if tracker.get("seeders", 0) > 0 else "-"
            seeders_label = Gtk.Label(label=seeders_text)
            seeders_label.set_visible(True)
            seeders_label.set_halign(Gtk.Align.START)
            if self._trackers_grid_child is not None:
                self._trackers_grid_child.attach(seeders_label, 4, row, 1, 1)

            # Leechers column
            leechers_text = str(tracker.get("leechers", 0)) if tracker.get("leechers", 0) > 0 else "-"
            leechers_label = Gtk.Label(label=leechers_text)
            leechers_label.set_visible(True)
            leechers_label.set_halign(Gtk.Align.START)
            if self._trackers_grid_child is not None:
                self._trackers_grid_child.attach(leechers_label, 5, row, 1, 1)

            # Last Announce column
            timing_text = tracker.get("timing_summary", "Never")
            timing_label = Gtk.Label(label=timing_text)
            timing_label.set_visible(True)
            timing_label.set_halign(Gtk.Align.START)
            if self._trackers_grid_child is not None:
                self._trackers_grid_child.attach(timing_label, 6, row, 1, 1)

        except Exception as e:
            self.logger.error(f"Error creating tracker row: {e}")

    def _show_no_trackers_message(self) -> None:
        """Show a message when no trackers are available."""
        try:
            # Create a grid if it doesn't exist
            if not self._trackers_grid_child:
                self._trackers_grid_child = self._create_trackers_grid()

            message_label = self.create_info_label("No trackers available for this torrent.")
            self.set_widget_margins(message_label, self.ui_margin_large)

            # Add message to the grid instead of directly to the tab
            if self._trackers_grid_child:
                self._trackers_grid_child.attach(message_label, 0, 0, 7, 1)  # Span all columns

            # Add the grid to the tab
            if self._trackers_tab and self._trackers_grid_child:
                self._trackers_tab.append(self._trackers_grid_child)

        except Exception as e:
            self.logger.error(f"Error showing no trackers message: {e}")

    def get_tracker_count(self) -> int:
        """
        Get the number of trackers for the current torrent.

        Returns:
            Number of trackers
        """
        try:
            if self._current_torrent:
                trackers = self._get_tracker_data(self._current_torrent)
                return len(trackers)
            return 0
        except Exception:
            return 0

    def get_primary_tracker(self) -> str:
        """
        Get the primary tracker URL.

        Returns:
            Primary tracker URL or empty string
        """
        try:
            if not self._current_torrent:
                return ""

            trackers = self._get_tracker_data(self._current_torrent)
            primary_trackers = [t for t in trackers if t.get("type") == "Primary"]

            if primary_trackers:
                return primary_trackers[0].get("url", "")

            return ""

        except Exception as e:
            self.logger.error(f"Error getting primary tracker: {e}")
            return ""
