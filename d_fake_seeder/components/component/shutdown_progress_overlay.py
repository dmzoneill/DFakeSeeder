"""
Shutdown Progress Overlay Component

A GTK4 overlay widget that displays real-time shutdown progress information,
following the MVC architecture pattern as a View component.
"""

from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from components.component.component import Component  # noqa: E402
from domain.app_settings import AppSettings  # noqa: E402
from gi.repository import GLib, Gtk  # noqa: E402
from lib.logger import logger  # noqa: E402
from lib.util.shutdown_progress import ShutdownProgressTracker  # noqa: E402


class ShutdownProgressOverlay(Component):
    """
    GTK4 overlay widget for displaying shutdown progress.
    Follows MVC pattern as a View component that observes shutdown progress.
    """

    def __init__(self, builder, parent, overlay_container: Gtk.Overlay):
        super().__init__(builder, parent)
        self.overlay_container = overlay_container
        self.tracker: Optional[ShutdownProgressTracker] = None
        self.update_source = None
        self.is_visible = False

        # Get UI settings for configuration
        app_settings = AppSettings.get_instance()
        ui_settings = app_settings.get("ui_settings", {})

        self.update_interval_ms = ui_settings.get("shutdown_overlay_update_interval_ms", 100)
        self.show_details = ui_settings.get("shutdown_overlay_show_details", True)
        self.show_timer = ui_settings.get("shutdown_overlay_show_timer", True)
        self.overlay_opacity = ui_settings.get("shutdown_overlay_opacity", 0.95)

        self._create_widgets()
        self._setup_styling()

    def _create_widgets(self):
        """Create the overlay widget structure"""
        # Main container with semi-transparent background
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_spacing(20)
        self.main_box.set_halign(Gtk.Align.CENTER)
        self.main_box.set_valign(Gtk.Align.CENTER)
        self.main_box.set_size_request(400, 300)
        self.main_box.add_css_class("shutdown-overlay")

        # Title
        self.title_label = Gtk.Label()
        self.title_label.set_markup("<b>Shutting Down Application</b>")
        self.title_label.add_css_class("shutdown-title")
        self.main_box.append(self.title_label)

        # Overall progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_show_text(True)
        self.progress_bar.add_css_class("shutdown-progress")
        self.main_box.append(self.progress_bar)

        # Components status container
        self.components_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.components_box.set_spacing(8)
        self.main_box.append(self.components_box)

        # Component status labels (created dynamically)
        self.component_labels = {}

        # Timer and elapsed time
        self.timer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.timer_box.set_spacing(20)
        self.timer_box.set_halign(Gtk.Align.CENTER)

        self.elapsed_label = Gtk.Label()
        self.elapsed_label.add_css_class("shutdown-timer")
        self.timer_box.append(self.elapsed_label)

        self.remaining_label = Gtk.Label()
        self.remaining_label.add_css_class("shutdown-timer")
        self.timer_box.append(self.remaining_label)

        self.main_box.append(self.timer_box)

        # Force shutdown warning (initially hidden)
        self.warning_label = Gtk.Label()
        self.warning_label.set_markup("<b>⚠️ Force shutdown will occur soon</b>")
        self.warning_label.add_css_class("shutdown-warning")
        self.warning_label.set_visible(False)
        self.main_box.append(self.warning_label)

        # Initially hidden
        self.main_box.set_visible(False)

    def _setup_styling(self):
        """Apply CSS styling to the overlay"""
        self.main_box.set_opacity(self.overlay_opacity)

    def set_tracker(self, tracker: ShutdownProgressTracker):
        """Set the shutdown progress tracker and register for updates"""
        if self.tracker:
            self.tracker.remove_callback(self._on_progress_update)

        self.tracker = tracker
        self.tracker.add_callback(self._on_progress_update)

        # Create component status labels
        self._create_component_labels()

        logger.info("ShutdownProgressOverlay attached to tracker", extra={"class_name": self.__class__.__name__})

    def _create_component_labels(self):
        """Create status labels for each component type"""
        if not self.tracker:
            return

        # Clear existing labels
        for label in self.component_labels.values():
            self.components_box.remove(label)
        self.component_labels.clear()

        # Create labels for each component type
        for component_type in self.tracker.components.keys():
            if self.show_details:
                label = Gtk.Label()
                label.set_halign(Gtk.Align.START)
                label.add_css_class("shutdown-component")
                self.component_labels[component_type] = label
                self.components_box.append(label)

    def show_overlay(self):
        """Show the shutdown progress overlay"""
        if self.is_visible or not self.tracker:
            return

        try:
            self.is_visible = True
            self.main_box.set_visible(True)
            self.overlay_container.add_overlay(self.main_box)

            # Start periodic updates
            if not self.update_source:
                self.update_source = GLib.timeout_add(self.update_interval_ms, self._update_display)

            logger.info("Shutdown progress overlay shown", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(f"Error showing shutdown overlay: {e}", extra={"class_name": self.__class__.__name__})
            self.is_visible = False

    def hide_overlay(self):
        """Hide the shutdown progress overlay"""
        if not self.is_visible:
            return

        self.is_visible = False
        self.main_box.set_visible(False)

        # Remove from overlay container
        try:
            self.overlay_container.remove_overlay(self.main_box)
        except Exception as e:
            logger.debug(f"Error removing overlay: {e}", extra={"class_name": self.__class__.__name__})

        # Stop updates
        if self.update_source:
            GLib.source_remove(self.update_source)
            self.update_source = None

        logger.info("Shutdown progress overlay hidden", extra={"class_name": self.__class__.__name__})

    def _on_progress_update(self):
        """Callback when tracker progress changes"""
        if not self.is_visible or not self.tracker:
            return

        # Update display on next main loop iteration
        GLib.idle_add(self._update_display)

    def _update_display(self) -> bool:
        """Update the display with current progress"""
        if not self.tracker or not self.is_visible:
            return False

        try:
            # Update overall progress
            progress = self.tracker.get_progress_percentage()
            self.progress_bar.set_fraction(progress / 100.0)
            self.progress_bar.set_text(f"{progress:.1f}% Complete")

            # Update component status
            if self.show_details:
                self._update_component_status()

            # Update timing information
            if self.show_timer:
                self._update_timing_display()

            # Check if shutdown is complete
            if self.tracker.is_complete():
                self.hide_overlay()
                return False

            return True

        except Exception as e:
            logger.error(f"Error updating shutdown display: {e}", extra={"class_name": self.__class__.__name__})
            return False

    def _update_component_status(self):
        """Update individual component status displays"""
        if not self.tracker:
            return

        status_summary = self.tracker.get_status_summary()

        for component_type, component_data in status_summary.items():
            if component_type not in self.component_labels:
                continue

            label = self.component_labels[component_type]
            display_name = self.tracker.get_component_display_name(component_type)
            status_icon = self.tracker.get_status_icon(component_type)

            completed = component_data["completed"]
            total = component_data["total"]

            if total == 0:
                status_text = f"{status_icon} {display_name}: No items"
            else:
                status_text = f"{status_icon} {display_name}: {completed}/{total}"

            label.set_text(status_text)

    def _update_timing_display(self):
        """Update elapsed time and countdown display"""
        if not self.tracker:
            return

        elapsed = self.tracker.get_time_elapsed()
        remaining = self.tracker.get_time_remaining()

        self.elapsed_label.set_text(f"Elapsed: {elapsed:.1f}s")
        self.remaining_label.set_text(f"Force shutdown in: {remaining:.1f}s")

        # Show warning when close to force shutdown
        if remaining <= 3.0 and not self.tracker.is_complete():
            self.warning_label.set_visible(True)
        else:
            self.warning_label.set_visible(False)

    def cleanup(self):
        """Clean up resources when overlay is destroyed"""
        if self.tracker:
            self.tracker.remove_callback(self._on_progress_update)
            self.tracker = None

        if self.update_source:
            GLib.source_remove(self.update_source)
            self.update_source = None

        self.hide_overlay()

        logger.debug("ShutdownProgressOverlay cleaned up", extra={"class_name": self.__class__.__name__})

    # MVC Interface methods (Component base class compliance)
    def set_model(self, model):
        """Set model reference (MVC compliance - not used for this component)"""
        self.model = model

    def update_view(self, *args):
        """Update view when model changes (MVC compliance - not used for this component)"""
        pass

    def model_selection_changed(self, selection, position, n_items):
        """Handle model selection changes (MVC compliance - not used for this component)"""
        pass
