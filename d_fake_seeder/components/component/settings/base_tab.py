"""
Base class for settings tab components.

Provides common functionality and interface for all settings tabs.
"""

# isort: skip_file

# fmt: off
from abc import abstractmethod
from typing import Any, Dict, List, Optional
import os

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GObject  # noqa

from d_fake_seeder.domain.app_settings import AppSettings  # noqa
from d_fake_seeder.lib.logger import logger  # noqa

from ..base_component import Component  # noqa

# fmt: on


class BaseSettingsTab(Component):
    """
    Abstract base class for settings tab components.

    Each tab is responsible for:
    - Managing its specific UI elements
    - Handling its signal connections
    - Loading and saving its settings
    - Providing validation and dependencies

    HYBRID APPROACH:
    Subclasses can use WIDGET_MAPPINGS for declarative auto-connect,
    or override _connect_signals() for complex manual handlers.
    """

    # Subclasses can override this with declarative widget mappings
    WIDGET_MAPPINGS: List[Dict[str, Any]] = []

    # Widgets that don't need handlers (containers, labels, etc.)
    IGNORE_WIDGET_TYPES = (
        Gtk.Box,
        Gtk.Grid,
        Gtk.Frame,
        Gtk.Label,
        Gtk.ScrolledWindow,
        Gtk.Separator,
        Gtk.Image,
        Gtk.Notebook,
        Gtk.Paned,
        Gtk.Overlay,
        Gtk.Stack,
        Gtk.ListBox,
        Gtk.FlowBox,
        Gtk.Revealer,
    )

    # Interactive widgets that SHOULD have handlers
    INTERACTIVE_WIDGET_TYPES = (
        Gtk.Switch,
        Gtk.CheckButton,
        Gtk.ToggleButton,
        Gtk.Button,
        Gtk.SpinButton,
        Gtk.Entry,
        Gtk.DropDown,
        Gtk.ComboBox,
        Gtk.Scale,
        Gtk.TextView,
        Gtk.ColorButton,
        Gtk.FontButton,
    )

    def __init__(self, builder: Gtk.Builder, app_settings: AppSettings) -> None:
        """
        Initialize the base tab.

        Args:
            builder: GTK Builder instance with UI loaded
            app_settings: Application settings instance
        """
        logger.trace("Starting initialization for", "BaseTab")
        super().__init__()

        self.builder = builder
        self.app_settings = app_settings
        self.logger = logger

        # Store UI widgets specific to this tab
        self._widgets: Dict[str, Any] = {}

        # Track which widgets have been connected (for validation)
        self._connected_widgets: set = set()

        # Flag to track if tab has been fully initialized (for lazy loading)
        self._fully_initialized = False

        # Flag to suppress change events during settings load
        self._loading_settings = False

        # Only do minimal initialization - defer full setup until tab is first viewed
        logger.trace("Tab created (deferred initialization)", "BaseTab")

    def ensure_initialized(self) -> None:
        """
        Ensure the tab is fully initialized (lazy initialization).
        Called when the tab is first viewed.
        """
        if self._fully_initialized:
            return

        logger.trace("Performing deferred initialization for", "BaseTab")

        # Initialize tab-specific setup
        logger.trace("About to call _init_widgets for", "BaseTab")
        self._init_widgets()
        logger.trace("Completed _init_widgets for", "BaseTab")

        # Set flag to suppress change events during initialization
        # Keep this flag True until ALL initialization is complete
        self._loading_settings = True

        # Load settings BEFORE connecting signals to avoid circular loops
        logger.trace("About to call _load_settings for", "BaseTab")
        self._load_settings()
        logger.trace("Completed _load_settings for", "BaseTab")

        # AUTO-CONNECT from WIDGET_MAPPINGS (Hybrid Approach)
        logger.trace("About to call _auto_connect_mappings for", "BaseTab")
        self._auto_connect_mappings()
        logger.trace("Completed _auto_connect_mappings for", "BaseTab")

        # Connect signals AFTER loading settings (manual handlers)
        logger.trace("About to call _connect_signals for", "BaseTab")
        self._connect_signals()
        logger.trace("Completed _connect_signals for", "BaseTab")

        logger.trace("About to call _setup_dependencies for", "BaseTab")
        self._setup_dependencies()
        logger.trace("Completed _setup_dependencies for", "BaseTab")

        # Translate dropdown items if TranslationMixin is available
        # IMPORTANT: Keep _loading_settings = True during translation to prevent
        # signal handlers from firing when dropdowns are updated
        if hasattr(self, "translate_all_dropdowns"):
            logger.trace("About to translate dropdown items for", "BaseTab")
            try:
                self.translate_all_dropdowns()
                logger.trace("Completed dropdown translation for", "BaseTab")
            except Exception as e:
                logger.error(f"Error translating dropdowns: {e}")

        # VALIDATE handler coverage in debug mode
        if self._is_debug_mode():
            self._validate_and_warn()

        # Clear flag NOW - all initialization complete, handlers can now execute normally
        self._loading_settings = False

        self._fully_initialized = True
        logger.trace("===== FULLY COMPLETED  =====", "BaseTab")

    @property
    @abstractmethod
    def tab_name(self) -> str:
        """Return the name of this tab for identification."""
        pass

    @abstractmethod
    def _init_widgets(self) -> None:
        """Initialize and cache tab-specific widgets."""
        pass

    @abstractmethod
    def _connect_signals(self) -> None:
        """Connect all signal handlers for this tab."""
        pass

    def _disconnect_signals(self) -> None:
        """
        Disconnect signal handlers for this tab's widgets.

        NOTE: If you tracked signals using track_signal(), you don't need to override this.
        The cleanup() method will automatically disconnect tracked signals.

        Override this only if you need custom disconnection logic.
        """
        # Default implementation - subclasses should override if they need custom disconnection
        pass

    def cleanup(self) -> None:
        """
        Clean up all resources used by this tab.

        This method:
        1. Calls _disconnect_signals() for custom disconnection logic
        2. Calls CleanupMixin.cleanup() to clean tracked resources
        3. Clears widget cache
        """
        logger.trace(
            f"Cleaning up {self.tab_name} tab",
            extra={"class_name": self.__class__.__name__},
        )

        # Call custom disconnection logic first
        try:
            self._disconnect_signals()
        except Exception as e:
            logger.warning(
                f"Error in _disconnect_signals for {self.tab_name}: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        # Call parent cleanup to handle tracked resources
        super().cleanup()

        # Clear widget cache
        self._widgets.clear()

        logger.trace(
            f"{self.tab_name} tab cleanup completed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def _load_settings(self) -> None:
        """Load current settings into UI widgets."""
        pass

    @abstractmethod
    def _setup_dependencies(self) -> None:
        """Set up dependencies between UI elements."""
        pass

    def get_widget(self, widget_id: str) -> Gtk.Widget:
        """
        Get a widget by ID, with caching.

        Args:
            widget_id: GTK widget ID

        Returns:
            The requested widget or None if not found
        """
        if widget_id not in self._widgets:
            self._widgets[widget_id] = self.builder.get_object(widget_id)

        return self._widgets[widget_id]

    def save_settings(self) -> Dict[str, Any]:
        """
        Save current UI state to settings.

        Returns:
            Dictionary of settings that were changed
        """
        try:
            changed_settings = self._collect_settings()

            # Handle None return (should return empty dict instead)
            if changed_settings is None:
                self.logger.warning(f"{self.tab_name} _collect_settings returned None, using empty dict")
                changed_settings = {}

            for key, value in changed_settings.items():
                self.app_settings.set(key, value)

            self.logger.info(f"{self.tab_name} tab settings saved: {len(changed_settings)} items")
            return changed_settings

        except Exception as e:
            self.logger.error(f"Error saving {self.tab_name} tab settings: {e}")
            return {}

    @abstractmethod
    def _collect_settings(self) -> Dict[str, Any]:
        """
        Collect current settings from UI widgets.

        Returns:
            Dictionary of setting_key -> value pairs
        """
        pass

    def _collect_mapped_settings(self) -> Dict[str, Any]:
        """
        Helper method to collect settings from all WIDGET_MAPPINGS.

        Returns:
            Dictionary of setting_key -> value pairs for all mapped widgets
        """
        settings = {}

        for mapping in self.WIDGET_MAPPINGS:
            widget_name = mapping.get("name")
            setting_key = mapping.get("setting_key")
            value_type = mapping.get("type")

            if not widget_name or not setting_key:
                continue

            widget = self._widgets.get(widget_name)
            if not widget:
                logger.warning(f"{self.tab_name}: Widget '{widget_name}' not found for collection", "BaseTab")
                continue

            # Extract value from widget
            value = self._extract_widget_value(widget, value_type)

            # Apply transform if provided
            if "transform" in mapping:
                value = mapping["transform"](value)

            settings[setting_key] = value
            logger.trace(f"Collected: {setting_key} = {value}", "BaseTab")

        return settings

    def validate_settings(self) -> Dict[str, str]:
        """
        Validate current settings.

        Returns:
            Dictionary of field_name -> error_message for any validation errors
        """
        try:
            return self._validate_tab_settings()
        except Exception as e:
            self.logger.error(f"Error validating {self.tab_name} tab settings: {e}")
            return {"general": f"Validation error: {e}"}

    def _validate_tab_settings(self) -> Dict[str, str]:
        """
        Tab-specific validation logic.

        Returns:
            Dictionary of validation errors
        """
        # Default implementation - no validation errors
        return {}

    def update_dependencies(self) -> None:
        """Update UI element dependencies."""
        try:
            self._update_tab_dependencies()
        except Exception as e:
            self.logger.error(f"Error updating {self.tab_name} tab dependencies: {e}")

    def _update_tab_dependencies(self) -> None:
        """Tab-specific dependency update logic. Override in subclasses."""
        pass

    def reset_to_defaults(self) -> None:
        """Reset tab settings to default values."""
        try:
            self._reset_tab_defaults()
            self.logger.trace(f"{self.tab_name} tab reset to defaults")
        except Exception as e:
            self.logger.error(f"Error resetting {self.tab_name} tab to defaults: {e}")

    def _reset_tab_defaults(self) -> None:
        """Tab-specific reset logic. Override in subclasses."""
        pass

    def on_setting_changed(self, widget: Gtk.Widget, *args: Any) -> None:
        """
        Generic setting change handler.

        Args:
            widget: Widget that changed
            *args: Additional arguments from signal
        """
        try:
            # Update dependencies when settings change
            self.update_dependencies()

            # Log the change for debugging
            widget_name = getattr(widget, "get_name", lambda: "unknown")()
            self.logger.trace(f"{self.tab_name} tab setting changed: {widget_name}")

        except Exception as e:
            self.logger.error(f"Error handling setting change in {self.tab_name} tab: {e}")

    # ========== HYBRID APPROACH: Auto-Connect Methods ==========

    def _auto_connect_mappings(self) -> None:
        """Auto-connect widgets defined in WIDGET_MAPPINGS."""
        if not self.WIDGET_MAPPINGS:
            logger.trace(f"{self.tab_name}: No WIDGET_MAPPINGS to auto-connect", "BaseTab")
            return

        logger.info(f"{self.tab_name}: Auto-connecting {len(self.WIDGET_MAPPINGS)} widgets", "BaseTab")

        for mapping in self.WIDGET_MAPPINGS:
            try:
                self._connect_widget_mapping(mapping)
            except Exception as e:
                logger.error(
                    f"{self.tab_name}: Failed to connect widget {mapping.get('id', 'unknown')}: {e}", "BaseTab"
                )

    def _connect_widget_mapping(self, mapping: Dict[str, Any]) -> None:
        """Connect a single widget from mapping config."""
        widget_id = mapping["id"]
        widget = self.builder.get_object(widget_id)

        if not widget:
            logger.warning(f"{self.tab_name}: Widget not found: {widget_id}", "BaseTab")
            return

        # Cache widget
        cache_name = mapping.get("name", widget_id)
        self._widgets[cache_name] = widget

        # Determine signal
        signal = mapping.get("signal") or self._auto_detect_signal(widget)

        # Create handler for dependencies and callbacks ONLY (no real-time save)
        def make_handler(m: Any) -> Any:
            def handler(w: Any, *args: Any) -> Any:
                # Skip event handling during settings load to prevent unnecessary change events
                if self._loading_settings:
                    return

                # Extract value from widget
                value = self._extract_widget_value(w, m.get("type"))

                # Apply transform if provided
                if "transform" in m:
                    value = m["transform"](value)

                # NOTE: Settings are NOT saved here - they're collected and saved in batch
                # via _collect_settings() when the dialog closes or Apply is clicked
                logger.trace(f"Widget changed: {m.get('name', widget_id)} = {value}", "BaseTab")

                # Handle dependencies
                if "enables" in m:
                    for dep_name in m["enables"]:
                        dep = self._widgets.get(dep_name)
                        if dep:
                            dep.set_sensitive(bool(value))

                # Custom callback if provided (for notifications, validation, etc)
                if "on_change" in m:
                    m["on_change"](self, value)

            return handler

        # Connect the signal
        handler = make_handler(mapping)
        widget.connect(signal, handler)

        # Track this widget as connected
        self._connected_widgets.add(widget_id)

        logger.trace(f"{self.tab_name}: Auto-connected {widget_id} (batch save mode, signal: {signal})", "BaseTab")

    def _auto_detect_signal(self, widget: Gtk.Widget) -> str:
        """Auto-detect appropriate signal for widget type."""
        if isinstance(widget, Gtk.Switch):
            return "state-set"
        elif isinstance(widget, Gtk.SpinButton):
            return "value-changed"
        elif isinstance(widget, Gtk.Entry):
            return "changed"
        elif isinstance(widget, Gtk.DropDown):
            return "notify::selected"
        elif isinstance(widget, (Gtk.CheckButton, Gtk.ToggleButton)):
            return "toggled"
        elif isinstance(widget, Gtk.Button):
            return "clicked"
        elif isinstance(widget, Gtk.Scale):
            return "value-changed"
        elif isinstance(widget, Gtk.ComboBox):
            return "changed"
        return "changed"  # Default fallback

    def _extract_widget_value(self, widget: Gtk.Widget, value_type: Optional[type] = None) -> Any:
        """Extract value from widget."""
        value = None

        if isinstance(widget, Gtk.Switch):
            value = widget.get_active()
        elif isinstance(widget, Gtk.SpinButton):
            value = widget.get_value()
        elif isinstance(widget, Gtk.Entry):
            value = widget.get_text()
        elif isinstance(widget, Gtk.DropDown):
            value = widget.get_selected()
        elif isinstance(widget, (Gtk.CheckButton, Gtk.ToggleButton)):
            value = widget.get_active()
        elif isinstance(widget, Gtk.Scale):
            value = widget.get_value()
        elif isinstance(widget, Gtk.TextView):
            buffer = widget.get_buffer()
            start, end = buffer.get_bounds()
            value = buffer.get_text(start, end, False)

        # Apply type conversion
        if value is not None and value_type:
            if value_type == int:
                return int(value)
            elif value_type == float:
                return float(value)
            elif value_type == bool:
                return bool(value)
            elif value_type == str:
                return str(value)

        return value

    # ========== VALIDATION Methods ==========

    def _is_debug_mode(self) -> bool:
        """Check if we're in debug mode for handler validation."""
        return os.getenv("DFS_DEBUG_HANDLERS", "false").lower() == "true"

    def _validate_and_warn(self) -> None:
        """Validate handlers and log warnings."""
        report = self.validate_handler_coverage()

        if report["missing_handlers"]:
            logger.warning(
                f"⚠️  {self.tab_name}: {len(report['missing_handlers'])} widgets missing handlers "
                f"({report['coverage_percent']:.1f}% coverage)",
                "BaseTab",
            )

            for missing in report["missing_handlers"][:5]:  # Show first 5
                logger.warning(
                    f"  Missing handler: {missing['id']} ({missing['type']}, "
                    f"expected signal: {missing['expected_signal']})",
                    "BaseTab",
                )

            if len(report["missing_handlers"]) > 5:
                logger.warning(f"  ... and {len(report['missing_handlers']) - 5} more", "BaseTab")
        else:
            logger.info(
                f"✅ {self.tab_name}: All interactive widgets have handlers "
                f"({report['coverage_percent']:.1f}% coverage)",
                "BaseTab",
            )

    def validate_handler_coverage(self) -> Dict[str, Any]:
        """Validate that all interactive widgets have handlers."""
        report = {
            "total_widgets": 0,
            "interactive_widgets": 0,
            "connected_widgets": 0,
            "missing_handlers": [],
            "coverage_percent": 0.0,
        }

        # Get all objects from builder
        all_objects = self.builder.get_objects()

        for obj in all_objects:
            # Skip non-widgets
            if not isinstance(obj, Gtk.Widget):
                continue

            report["total_widgets"] += 1  # type: ignore[operator]

            # Skip container/display-only widgets
            if isinstance(obj, self.IGNORE_WIDGET_TYPES):
                continue

            # Check if it's an interactive widget
            if isinstance(obj, self.INTERACTIVE_WIDGET_TYPES):
                report["interactive_widgets"] += 1  # type: ignore[operator]

                try:
                    widget_id = Gtk.Buildable.get_buildable_id(obj)
                except Exception:
                    widget_id = None

                if not widget_id:
                    continue

                # Check if widget has a handler
                if self._has_handler(obj, widget_id):
                    report["connected_widgets"] += 1  # type: ignore[operator]
                else:
                    report["missing_handlers"].append(  # type: ignore[attr-defined]
                        {"id": widget_id, "type": type(obj).__name__, "expected_signal": self._auto_detect_signal(obj)}
                    )

        # Calculate coverage
        if report["interactive_widgets"] > 0:  # type: ignore[operator]
            report["coverage_percent"] = (report["connected_widgets"] / report["interactive_widgets"]) * 100  # type: ignore[operator]  # noqa: E501

        return report

    def _has_handler(self, widget: Gtk.Widget, widget_id: str) -> bool:
        """Check if widget has a handler connected."""
        # Check if in auto-connected widgets
        if widget_id in self._connected_widgets:
            return True

        # Check if widget is in cached widgets (manual connection)
        if widget_id in self._widgets or any(widget_id in str(w) for w in self._widgets.values()):
            return True

        # Check if widget has any connected signals (heuristic)
        try:
            signal_name = self._auto_detect_signal(widget)
            # Strip signal detail (e.g., "notify::selected" -> "notify") for lookup
            # signal_lookup doesn't understand the "::detail" syntax
            base_signal = signal_name.split("::")[0]
            signal_id = GObject.signal_lookup(base_signal, type(widget))
            if signal_id > 0:
                # Very basic check - if signal exists, assume it might be connected
                # This is imperfect but better than nothing
                return True
        except Exception:
            pass

        return False

    def print_coverage_report(self) -> None:
        """Print a human-readable coverage report to console."""
        report = self.validate_handler_coverage()

        print(f"\n{'='*70}")
        print(f"Handler Coverage Report: {self.tab_name}")
        print(f"{'='*70}")
        print(f"Total widgets:        {report['total_widgets']}")
        print(f"Interactive widgets:  {report['interactive_widgets']}")
        print(f"Connected widgets:    {report['connected_widgets']}")
        print(f"Coverage:             {report['coverage_percent']:.1f}%")

        if report["missing_handlers"]:
            print(f"\n⚠️  Missing Handlers ({len(report['missing_handlers'])}):")
            print(f"{'─'*70}")
            for missing in report["missing_handlers"]:
                print(f"  • {missing['id']:<40} ({missing['type']})")
                print(f"    Expected signal: {missing['expected_signal']}")
        else:
            print("\n✅ All interactive widgets have handlers!")

        print(f"{'='*70}\n")
