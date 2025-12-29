"""
DFakeSeeder View Module.

This module implements the GTK4 user interface for the DFakeSeeder application.
It manages all UI components, windows, dialogs, and user interaction handling.
"""

# pylint: disable=too-many-lines

# fmt: off
# isort: skip_file
from typing import Any
import json
import logging
import os
import signal
import time
import webbrowser
from datetime import datetime

import gi

gi.require_version("Gdk", "4.0")
gi.require_version("Gtk", "4.0")
gi.require_version("GioUnix", "2.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa

# Shutdown progress tracking (overlay removed, keeping behavior)
from d_fake_seeder.components.component.sidebar import Sidebar  # noqa: E402
from d_fake_seeder.components.component.statusbar import Statusbar  # noqa: E402
from d_fake_seeder.components.component.toolbar import Toolbar  # noqa: E402
from d_fake_seeder.components.component.tracker_tab import TrackerTab  # noqa: E402

# Importing necessary libraries
from d_fake_seeder.components.component.torrent_details import (  # noqa: E402
    TorrentDetailsNotebook,
)
from d_fake_seeder.components.component.torrents import Torrents  # noqa: E402
from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402

# Translation function will be provided by model's TranslationManager
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.cleanup_mixin import CleanupMixin  # noqa: E402
from d_fake_seeder.lib.util.notification_manager import NotificationManager  # noqa: E402
from d_fake_seeder.lib.util.notification_widget import NotificationType  # noqa: E402
from d_fake_seeder.lib.util.shutdown_progress import (  # noqa: E402
    ShutdownProgressTracker,
)

# fmt: on


# View class for Torrent Application
class View(CleanupMixin):  # pylint: disable=too-many-instance-attributes
    """Main GTK4 View class managing all UI components and user interactions."""

    instance = None
    toolbar = None
    notebook = None
    torrents_columnview = None
    torrents_states = None

    def __init__(self, app: Any) -> None:  # pylint: disable=too-many-statements
        with logger.performance.operation_context("view_init", self.__class__.__name__):
            logger.info("View.__init__() started", self.__class__.__name__)
            logger.trace("View instantiate", self.__class__.__name__)
            CleanupMixin.__init__(self)
            self.app = app
            View.instance = self
            # Initialize timeout_id to prevent warnings on cleanup
            with logger.performance.operation_context("basic_init", self.__class__.__name__):
                self.timeout_id = 0
                self.timeout_source = None
                # Initialize shutdown progress tracking
                self.shutdown_tracker = None
                self.shutdown_overlay = None
                logger.trace("Basic initialization completed", self.__class__.__name__)
            # subscribe to settings changed
            with logger.performance.operation_context("settings_init", self.__class__.__name__):
                self.settings = AppSettings.get_instance()
                self.settings.connect("attribute-changed", self.handle_settings_changed)
                logger.trace("Settings subscription completed", self.__class__.__name__)
            # Loading GUI from XML
            with logger.performance.operation_context("builder_creation", self.__class__.__name__):
                logger.trace("About to create Gtk.Builder", self.__class__.__name__)
                self.builder = Gtk.Builder()
                logger.info("Gtk.Builder created", self.__class__.__name__)
            with logger.performance.operation_context("xml_loading", self.__class__.__name__):
                logger.trace("About to load XML file", self.__class__.__name__)
                dfs_path = os.environ.get("DFS_PATH")
                xml_path = dfs_path + "/components/ui/generated/generated.xml"  # type: ignore[operator]
                self.builder.add_from_file(xml_path)
                logger.trace("XML file loaded", self.__class__.__name__)
            # CSS will be loaded and applied in setup_window() method
            # Get window object
            with logger.performance.operation_context("window_setup", self.__class__.__name__):
                self.window = self.builder.get_object("main_window")

                # TEMPORARILY DISABLED: Window keyboard controller for debugging
                # print("✅ Keyboard controller disabled - testing natural GTK focus")

                # Set window icon using icon name
                self.window.set_icon_name("dfakeseeder")
                # Also set the application ID to match desktop file
                if hasattr(self.app, "set_application_id"):
                    self.app.set_application_id("ie.fio.dfakeseeder")
                logger.trace("Window setup completed", self.__class__.__name__)
        # views
        logger.trace("About to create Torrents component", "View")
        self.torrents = Torrents(self.builder, None)
        logger.trace(
            "Torrents component created successfully (took {(torrents_end - torrents_start)*1000:.1f}ms)",
            "View",
        )
        logger.trace("About to create Toolbar component", "View")
        self.toolbar = Toolbar(self.builder, None, self.app)
        logger.trace(
            "Toolbar component created successfully (took {(toolbar_end - toolbar_start)*1000:.1f}ms)",
            "View",
        )
        logger.trace("About to create TorrentDetailsNotebook component", "View")
        self.notebook = TorrentDetailsNotebook(self.builder, None)
        logger.trace(
            "TorrentDetailsNotebook component created successfully (took {(notebook_end - notebook_start)*1000:.1f}ms)",
            "View",
        )
        logger.trace("About to create Sidebar component", "View")
        self.sidebar = Sidebar(self.builder, None)  # type: ignore[abstract]
        logger.trace(
            "Sidebar component created successfully",
            "View",
        )
        logger.trace("About to create Statusbar component", "View")
        self.statusbar = Statusbar(self.builder, None)
        logger.trace(
            "Statusbar component created successfully (took {(statusbar_end - statusbar_start)*1000:.1f}ms)",
            "View",
        )
        logger.trace("About to create TrackerTab component", "View")
        self.tracker_tab = TrackerTab(self.builder, None)
        logger.trace("TrackerTab component created successfully", "View")
        # Getting relevant objects
        self.quit_menu_item = self.builder.get_object("quit_menu_item")
        self.help_menu_item = self.builder.get_object("help_menu_item")
        self.overlay = self.builder.get_object("overlay")
        self.status = self.builder.get_object("status_label")
        self.main_paned = self.builder.get_object("main_paned")
        self.paned = self.builder.get_object("paned")
        self.notebook_widget = self.builder.get_object("notebook1")
        self.current_time = time.time()

        # Replace old states_columnview with new sidebar
        logger.trace("Replacing states_columnview with sidebar", "View")
        old_states_scroll = self.paned.get_start_child()
        if old_states_scroll:
            self.paned.set_start_child(None)  # Remove old widget

        # Wrap sidebar in ScrolledWindow for consistent layout
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_child(self.sidebar.get_widget())
        self.paned.set_start_child(sidebar_scroll)
        logger.trace("Sidebar integrated into UI", "View")

        logger.trace(
            "Getting relevant objects completed (took {(objects_end - objects_start)*1000:.1f}ms)",
            "View",
        )
        # notification overlay
        self.notify_label = Gtk.Label(label=self._("Overlay Notification"))
        # self.notify_label.set_no_show_all(True)
        self.notify_label.set_visible(False)
        self.notify_label.hide()
        self.notify_label.set_valign(Gtk.Align.CENTER)
        self.notify_label.set_halign(Gtk.Align.CENTER)
        # CRITICAL: Prevent overlay from blocking keyboard events
        self.notify_label.set_can_target(False)
        self.notify_label.set_can_focus(False)
        self.overlay.add_overlay(self.notify_label)

        # Initialize the toast-style NotificationManager
        def statusbar_callback(text: str) -> None:
            if hasattr(self, "status") and self.status:
                self.status.set_text(text)

        self.notification_manager = NotificationManager(
            overlay=self.overlay,
            statusbar_callback=statusbar_callback,
        )
        logger.trace(
            "Notification overlay setup completed (took {(overlay_end - overlay_start)*1000:.1f}ms)",
            "View",
        )
        # Get UI settings for configurable timeouts using proper AppSettings API
        self.resize_delay = self.settings.get("ui_settings.resize_delay_seconds", 1.0)
        self.splash_display_duration = self.settings.get("ui_settings.splash_display_duration_seconds", 2)
        self.splash_fade_interval = self.settings.get("ui_settings.splash_fade_interval_ms", 75)
        self.splash_fade_step = self.settings.get("ui_settings.splash_fade_step", 0.025)
        self.splash_image_size = self.settings.get("ui_settings.splash_image_size_pixels", 300)
        self.notification_timeout_min = self.settings.get("ui_settings.notification_timeout_min_ms", 2000)
        self.notification_timeout_multiplier = self.settings.get("ui_settings.notification_timeout_multiplier", 500)
        logger.trace(
            "UI settings configuration completed (took {(ui_settings_end - ui_settings_start)*1000:.1f}ms)",
            "View",
        )
        logger.trace("About to call setup_window()", "View")
        self.setup_window()
        logger.trace("setup_window() completed (took ms)", "View")
        logger.trace("About to show splash image", "View")
        self.show_splash_image()
        logger.trace("Splash image shown (took ms)", "View")
        self.track_timeout(GLib.timeout_add_seconds(int(self.resize_delay), self.resize_panes))
        logger.trace(
            "Timeout for resize panes added (took {(timeout_end - timeout_start)*1000:.1f}ms)",
            "View",
        )
        # Shutdown overlay disabled - keeping only shutdown tracking behavior
        self.shutdown_overlay = None
        logger.trace("View.__init__() completed", "View")

    def _(self, text: Any) -> Any:
        """Get translation function from model's TranslationManager"""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def setup_window(self) -> None:
        """Configure main window properties and theme."""
        # Get application settings
        app_settings = AppSettings.get_instance()
        app_title = app_settings.get("application", {}).get("title", self._("D' Fake Seeder"))
        self.window.set_title(app_title)
        self.window.set_application(self.app)
        # Initialize display for CSS loading
        self.display = self.window.get_display()
        self.css_provider = None
        # Get theme style and color scheme from ui_settings
        theme_style = app_settings.get("ui_settings.theme_style", "classic")
        color_scheme = app_settings.get("ui_settings.color_scheme", "auto")
        logger.trace(f"Initial theme from settings: style={theme_style}, color={color_scheme}")
        # Apply initial theme (will load appropriate CSS file and color scheme)
        self.apply_theme(theme_style, color_scheme)
        # Connect to AppSettings changes for theme switching
        app_settings.connect("attribute-changed", self.handle_app_settings_changed)
        # Create an action group
        self.action_group = Gio.SimpleActionGroup()
        # add hamburger menu
        self.header = Gtk.HeaderBar()
        self.window.set_titlebar(self.header)
        # Create a new "Action"
        action = Gio.SimpleAction.new("quit", None)
        # Use lambda to properly handle the action signal (action, parameter) -> quit()
        action.connect("activate", lambda action, param: self.quit())
        self.action_group.add_action(action)
        # Create standard menu with translatable structure
        self.main_menu_items = [
            {"action": "win.preferences", "key": "Preferences"},
            {"action": "win.about", "key": "About"},
            {"action": "win.quit", "key": "Quit"},
        ]
        self.main_menu = Gio.Menu()
        for item in self.main_menu_items:
            translated_text = self._(item["key"])
            self.main_menu.append(translated_text, item["action"])
        # Create a popover
        self.popover = Gtk.PopoverMenu()
        self.popover.set_menu_model(self.main_menu)
        # Create a menu button
        self.hamburger = Gtk.MenuButton()
        self.hamburger.set_popover(self.popover)
        self.hamburger.set_icon_name("open-menu-symbolic")
        # Add menu button to the header bar
        self.header.pack_start(self.hamburger)
        # Add preferences action
        action = Gio.SimpleAction.new("preferences", None)
        action.connect("activate", self.show_preferences)
        self.action_group.add_action(action)
        # Add an about dialog
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.show_about)
        self.action_group.add_action(action)
        # Insert the action group into the window
        self.window.insert_action_group("win", self.action_group)
        # Register widgets for automatic translation
        if hasattr(self, "model") and self.model:
            self.model.translation_manager.scan_builder_widgets(self.builder)
            logger.trace(
                "Registered widgets for translation",
                extra={"class_name": self.__class__.__name__},
            )
        self.window.present()

    def show_splash_image(self) -> None:
        """Display splash image overlay on startup."""
        # splash image
        self.splash_image = Gtk.Image()
        splash_path = os.environ.get("DFS_PATH") + "/components/images/dfakeseeder.png"  # type: ignore[operator]
        self.splash_image.set_from_file(splash_path)
        # self.splash_image.set_no_show_all(False)
        self.splash_image.set_visible(True)
        self.splash_image.show()
        self.splash_image.set_valign(Gtk.Align.CENTER)
        self.splash_image.set_halign(Gtk.Align.CENTER)
        # Use set_pixel_size() to actually scale the image, not just set widget size
        self.splash_image.set_pixel_size(self.splash_image_size)
        # CRITICAL: Prevent splash from blocking keyboard events
        self.splash_image.set_can_target(False)
        self.splash_image.set_can_focus(False)
        self.overlay.add_overlay(self.splash_image)
        self.track_timeout(GLib.timeout_add_seconds(self.splash_display_duration, self.fade_out_image))

    def show_about(self, action: Any, _param: Any) -> None:
        """Show the About dialog with application info."""
        self.window.about = Gtk.AboutDialog()
        self.window.about.set_transient_for(self.window)
        self.window.about.set_modal(True)
        app_settings = AppSettings.get_instance()
        app_title = app_settings.get("application", {}).get("title", self._("D' Fake Seeder"))
        self.window.about.set_program_name(app_title)
        self.window.about.set_authors([self.settings.author])
        self.window.about.set_copyright(self.settings.copyright.replace("{year}", str(datetime.now().year)))
        self.window.about.set_license_type(Gtk.License.APACHE_2_0)
        self.window.about.set_website(self.settings.website)
        self.window.about.set_website_label(self._("Github - D' Fake Seeder"))
        self.window.about.set_version(self.settings.version)

        # Add information about the name origin
        about_name_text = self._(
            'The name "D\' Fake Seeder" is a playful nod to the Irish English accent. '
            'In Irish pronunciation, the "th" sound in "the" is often rendered as a hard "d" sound - '
            'so "the" becomes "de" or "d\'". This linguistic quirk gives us "D\' Fake Seeder" '
            'instead of "The Fake Seeder", celebrating the project\'s Irish heritage while describing '
            "exactly what it does: simulates (fakes) torrent seeding activity."
        )
        self.window.about.set_comments(about_name_text)

        file = Gio.File.new_for_path(os.environ.get("DFS_PATH") + "/" + self.settings.logo)  # type: ignore[operator]
        texture = Gdk.Texture.new_from_file(file)
        self.window.about.set_logo(texture)
        self.window.about.show()

    def show_preferences(self, action: Any, _param: Any) -> None:  # noqa: ARG002
        """Show the preferences/settings dialog from the hamburger menu."""
        if hasattr(self, "toolbar") and self.toolbar:
            logger.trace(
                "Opening preferences from hamburger menu",
                extra={"class_name": self.__class__.__name__},
            )
            self.toolbar.show_settings_dialog()
        else:
            logger.error(
                "Toolbar not available, cannot show settings dialog",
                extra={"class_name": self.__class__.__name__},
            )

    def fade_out_image(self) -> Any:
        """Start splash image fade out animation."""
        self.splash_image.fade_out = 1.0
        self.track_timeout(GLib.timeout_add(self.splash_fade_interval, self.fade_image))

    def fade_image(self) -> Any:
        """Animate splash image opacity reduction."""
        self.splash_image.fade_out -= self.splash_fade_step
        if self.splash_image.fade_out > 0:
            self.splash_image.set_opacity(self.splash_image.fade_out)
            return True
        self.splash_image.hide()
        self.splash_image.unparent()
        self.splash_image = None
        return False

    def resize_panes(self) -> bool:
        """Set initial pane positions: upper/lower halved, left sidebar to 275px."""
        logger.trace("View resize_panes", extra={"class_name": self.__class__.__name__})
        # Set upper/lower panes to half height
        allocation = self.main_paned.get_allocation()
        available_height = allocation.height
        # If window not yet realized, use a reasonable default (300px for top pane)
        if available_height < 100:
            position = 300
        else:
            position = available_height // 2
        self.main_paned.set_position(position)
        logger.trace(f"Set main_paned position to {position} (height={available_height})")
        # Set left sidebar to 275px
        self.paned.set_position(275)
        return False  # Don't repeat the timeout

    # Setting model for the view
    def notify(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self,
        text: Any,
        notification_type: str = "info",
        translate: bool = False,
        action_label: str | None = None,
        action_callback: Any = None,
        timeout_ms: int | None = None,
        **kwargs: Any,
    ) -> Any:
        """
        Show a notification message using toast-style popups.

        This method is THREAD-SAFE - it can be called from any thread and
        will properly marshal the notification to the GTK main thread.

        Args:
            text: The notification text (can be a translation key if translate=True)
            notification_type: Type of notification ("info", "success", "warning", "error")
            translate: If True, translate the text using the translation manager
            action_label: Optional label for an action button
            action_callback: Optional callback when action button is clicked
            timeout_ms: Override auto-dismiss timeout (None = use settings)
            **kwargs: Format arguments for the translated string
        """
        logger.trace("View notify", extra={"class_name": self.__class__.__name__})

        # Optionally translate the text
        if translate:
            text = self._(text)
            if kwargs:
                text = text.format(**kwargs)

        # Map string type to NotificationType enum
        type_map = {
            "info": NotificationType.INFO,
            "success": NotificationType.SUCCESS,
            "warning": NotificationType.WARNING,
            "error": NotificationType.ERROR,
        }
        notif_type = type_map.get(notification_type, NotificationType.INFO)

        # Use the new NotificationManager if available
        if hasattr(self, "notification_manager") and self.notification_manager:
            # CRITICAL: Marshal to main GTK thread using GLib.idle_add
            # This prevents UI freezes when notify() is called from background threads
            def _show_notification() -> bool:
                if hasattr(self, "notification_manager") and self.notification_manager:
                    self.notification_manager.show(
                        message=str(text),
                        notification_type=notif_type,
                        action_label=action_label,
                        action_callback=action_callback,
                        timeout_ms=timeout_ms,
                    )
                return False  # Don't repeat

            GLib.idle_add(_show_notification)
            return None

        # Fallback to old label-based notification (for backwards compatibility)
        # Also use GLib.idle_add for thread safety
        def _show_fallback_notification() -> bool:
            # Cancel the previous timeout, if it exists
            if hasattr(self, "timeout_source") and self.timeout_source and not self.timeout_source.is_destroyed():
                self.timeout_source.destroy()
                self.timeout_source = None
            self.timeout_id = 0
            self.notify_label.set_visible(True)
            self.notify_label.show()
            self.notify_label.set_text(str(text))
            self.status.set_text(str(text))
            # Use configurable notification timeout (based on tickspeed, minimum configurable)
            notification_timeout = max(
                self.notification_timeout_min,
                int(self.settings.tickspeed * self.notification_timeout_multiplier),
            )
            # Create timeout source and store reference
            self.timeout_source = GLib.timeout_source_new(notification_timeout)
            self.timeout_source.set_callback(  # type: ignore[attr-defined]
                lambda user_data: self.notify_label.set_visible(False) or self.notify_label.hide()
            )
            self.timeout_id = self.timeout_source.attach(GLib.MainContext.default())  # type: ignore[attr-defined]
            return False  # Don't repeat

        GLib.idle_add(_show_fallback_notification)

    # Setting model for the view
    def set_model(self, model: Any) -> None:
        """Set the model and propagate it to all child components."""
        logger.trace("View set model", extra={"class_name": self.__class__.__name__})
        self.model = model
        self.notebook.set_model(model)  # type: ignore[union-attr]
        self.toolbar.set_model(model)  # type: ignore[union-attr]
        self.torrents.set_model(model)
        self.sidebar.set_model(model)
        self.statusbar.set_model(model)
        # Pass view reference to statusbar so it can access connection components
        self.statusbar.view = self  # type: ignore[attr-defined]
        # Connect to language change signal
        self.model.connect("language-changed", self.on_language_changed)
        # Register widgets for translation after model is set
        self.model.translation_manager.scan_builder_widgets(self.builder)
        # Debug: Check how many widgets were registered
        widget_count = len(self.model.translation_manager.translatable_widgets)
        logger.trace(
            f"Registered {widget_count} widgets for automatic translation",
            extra={"class_name": self.__class__.__name__},
        )
        # Debug: Print discovered translatable widgets (only in debug mode)
        if logger.isEnabledFor(logging.DEBUG):
            self.model.translation_manager.print_discovered_widgets()
        # CRITICAL FIX: Refresh translations for newly registered widgets
        # This ensures that widgets get translated with the correct language on startup
        if widget_count > 0:
            logger.trace(
                "Newly registered widgets will be refreshed by debounced system",
                extra={"class_name": self.__class__.__name__},
            )
            # Use debounced refresh to avoid cascading refresh operations during startup
            self.model.translation_manager.refresh_all_translations()
        # Register notebook for translation updates
        if hasattr(self.notebook, "register_for_translation"):
            self.notebook.register_for_translation()  # type: ignore[union-attr]
        # Register main menu for translation updates
        if hasattr(self, "main_menu") and hasattr(self, "main_menu_items"):
            self.model.translation_manager.register_menu(self.main_menu, self.main_menu_items, popover=self.popover)
            logger.trace(
                f"Registered main menu with {len(self.main_menu_items)} items for translation",
                extra={"class_name": self.__class__.__name__},
            )

    # Connecting signals for different events
    def connect_signals(self) -> None:
        """Connect GObject signals between model and view components."""
        logger.trace(
            "View connect signals",
            extra={"class_name": self.__class__.__name__},
        )
        self.window.connect("destroy", self.quit)
        self.window.connect("close-request", self.quit)
        self.model.connect("data-changed", self.torrents.update_view)
        self.model.connect("data-changed", self.notebook.update_view)  # type: ignore[union-attr]
        self.model.connect("data-changed", self.sidebar.update_view)
        self.model.connect("data-changed", self.statusbar.update_view)
        self.model.connect("data-changed", self.toolbar.update_view)  # type: ignore[union-attr]
        # LAZY LOADING FIX: Connect to connection components only if they exist
        # They will be connected later when created in background
        incoming_connections = self.notebook.get_incoming_connections()  # type: ignore[union-attr]
        if incoming_connections:
            self.model.connect("data-changed", incoming_connections.update_view)
        outgoing_connections = self.notebook.get_outgoing_connections()  # type: ignore[union-attr]
        if outgoing_connections:
            self.model.connect("data-changed", outgoing_connections.update_view)
        self.model.connect("selection-changed", self.torrents.model_selection_changed)
        self.model.connect("selection-changed", self.notebook.model_selection_changed)  # type: ignore[union-attr]
        self.model.connect("selection-changed", self.sidebar.model_selection_changed)
        self.model.connect("selection-changed", self.statusbar.model_selection_changed)
        self.model.connect("selection-changed", self.toolbar.model_selection_changed)  # type: ignore[union-attr]
        signal.signal(signal.SIGINT, self.quit)

    # Connecting signals for different events
    def remove_signals(self) -> None:
        """Disconnect GObject signals during cleanup."""
        logger.trace("Remove signals", extra={"class_name": self.__class__.__name__})
        self.model.disconnect_by_func(self.torrents.update_view)
        self.model.disconnect_by_func(self.notebook.update_view)  # type: ignore[union-attr]
        self.model.disconnect_by_func(self.sidebar.update_view)
        self.model.disconnect_by_func(self.statusbar.update_view)
        self.model.disconnect_by_func(self.notebook.get_incoming_connections().update_view)  # type: ignore[union-attr]
        self.model.disconnect_by_func(self.notebook.get_outgoing_connections().update_view)  # type: ignore[union-attr]

    # Event handler for clicking on quit - delegates to consolidated quit procedure
    def on_quit_clicked(self, menu_item: Any, fast_shutdown: Any = False) -> None:
        """Handle quit menu click - delegates to consolidated quit procedure"""
        logger.trace(
            "🎯 QUIT MENU: Quit menu clicked, delegating to quit()",
            extra={"class_name": self.__class__.__name__},
        )
        self.quit(fast_shutdown=fast_shutdown)

    # open github webpage
    def on_help_clicked(self, menu_item: Any) -> None:
        """Open GitHub project page in default browser."""
        logger.trace(
            "Opening GitHub webpage",
            extra={"class_name": self.__class__.__name__},
        )
        webbrowser.open(self.settings.issues_page)

    def handle_peer_connection_event(  # pylint: disable=too-many-arguments,too-many-positional-arguments
        self, direction: Any, action: Any, address: Any, port: Any, data: Any = None
    ) -> None:  # noqa: E501
        """Handle peer connection events from peer server or connection manager"""
        torrent_hash = (data or {}).get("torrent_hash", "unknown") if data else "unknown"
        logger.trace(
            f"Peer connection event: {direction} {action} {address}:{port} " f"(torrent: {torrent_hash})",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            if direction == "incoming":
                component = self.notebook.get_incoming_connections()  # type: ignore[union-attr]
                if action == "add":
                    component.add_incoming_connection(address, port, **(data or {}))
                    total_count = component.get_total_connection_count()
                    visible_count = component.get_connection_count()
                    connection_word = "connection" if total_count == 1 else "connections"
                    message = (
                        f"Added incoming connection. Total: {total_count} "
                        f"{connection_word}, Visible: {visible_count}"
                    )
                    logger.trace(
                        message,
                        extra={"class_name": self.__class__.__name__},
                    )
                elif action == "update":
                    component.update_incoming_connection(address, port, **(data or {}))
                elif action == "remove":
                    component.remove_incoming_connection(address, port)
                    total_count = component.get_total_connection_count()
                    visible_count = component.get_connection_count()
                    connection_word = "connection" if total_count == 1 else "connections"
                    message = (
                        f"Removed incoming connection. Total: {total_count} "
                        f"{connection_word}, Visible: {visible_count}"
                    )
                    logger.trace(
                        message,
                        extra={"class_name": self.__class__.__name__},
                    )
            elif direction == "outgoing":
                component = self.notebook.get_outgoing_connections()  # type: ignore[union-attr]
                if action == "add":
                    component.add_outgoing_connection(address, port, **(data or {}))
                    total_count = component.get_total_connection_count()
                    visible_count = component.get_connection_count()
                    connection_word = "connection" if total_count == 1 else "connections"
                    message = (
                        f"Added outgoing connection. Total: {total_count} "
                        f"{connection_word}, Visible: {visible_count}"
                    )
                    logger.trace(
                        message,
                        extra={"class_name": self.__class__.__name__},
                    )
                elif action == "update":
                    component.update_outgoing_connection(address, port, **(data or {}))
                elif action == "remove":
                    component.remove_outgoing_connection(address, port)
                    total_count = component.get_total_connection_count()
                    visible_count = component.get_connection_count()
                    connection_word = "connection" if total_count == 1 else "connections"
                    message = (
                        f"Removed outgoing connection. Total: {total_count} "
                        f"{connection_word}, Visible: {visible_count}"
                    )
                    logger.trace(
                        message,
                        extra={"class_name": self.__class__.__name__},
                    )
            # Update connection counts
            self.notebook.update_connection_counts()  # type: ignore[union-attr]
        except (GLib.Error, RuntimeError, AttributeError, KeyError) as e:
            logger.error(
                f"Error handling peer connection event: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _cleanup_timers(self) -> Any:
        """Cleanup all GLib timers and timeout sources"""
        logger.trace("🧹 Cleaning up GLib timers", extra={"class_name": self.__class__.__name__})

        # Clean up all tracked timeouts via CleanupMixin
        CleanupMixin.cleanup(self)

        # Clean up notification timeout (custom source that uses destroy() instead of remove())
        if hasattr(self, "timeout_source") and self.timeout_source:
            try:
                if not self.timeout_source.is_destroyed():
                    self.timeout_source.destroy()
                self.timeout_source = None
                self.timeout_id = 0
            except (GLib.Error, RuntimeError, AttributeError) as e:
                logger.trace(
                    f"Error cleaning up timeout_source: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        # Clean up any splash image timers by hiding splash
        if hasattr(self, "splash_image") and self.splash_image:
            try:
                self.splash_image.hide()
                self.splash_image.unparent()
                self.splash_image = None
            except (GLib.Error, RuntimeError, AttributeError) as e:
                logger.trace(
                    f"Error cleaning up splash_image: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        # Clean up connection tab timers (incoming connections tab has removal_timers)
        try:  # pylint: disable=too-many-nested-blocks
            if hasattr(self, "notebook") and self.notebook:
                incoming_tab = self.notebook.get_incoming_connections()
                if incoming_tab and hasattr(incoming_tab, "removal_timers"):
                    timer_count = len(incoming_tab.removal_timers)
                    if timer_count > 0:
                        logger.trace(
                            f"🧹 Removing {timer_count} connection removal timers",
                            extra={"class_name": self.__class__.__name__},
                        )
                        for timer_id in incoming_tab.removal_timers.values():
                            try:
                                GLib.source_remove(timer_id)
                            except (GLib.Error, ValueError):
                                pass  # Timer may have already fired
                        incoming_tab.removal_timers.clear()
        except (GLib.Error, RuntimeError, AttributeError) as e:
            logger.trace(
                f"Error cleaning up connection timers: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        logger.trace(
            "✅ GLib timer cleanup complete",
            extra={"class_name": self.__class__.__name__},
        )

    def _get_shutdown_kill_timeout(self) -> Any:
        """Get shutdown kill timeout from settings."""
        ui = getattr(self.settings, "ui_settings", {})
        return ui.get("shutdown_kill_timeout_seconds", 0.1) if isinstance(ui, dict) else 0.1

    def _get_shutdown_backup_timeout(self) -> Any:
        """Get shutdown backup timeout from settings."""
        ui = getattr(self.settings, "ui_settings", {})
        return ui.get("shutdown_backup_timeout_seconds", 0.25) if isinstance(ui, dict) else 0.25

    # Function to quit the application with consolidated shutdown procedure
    def quit(  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
        self, widget: Any = None, event: Any = None, fast_shutdown: Any = False
    ) -> Any:
        """
        Consolidated shutdown procedure for all application resources.

        Shutdown order (optimized for speed and reliability):
        1. Cleanup UI timers (instant)
        2. Remove signal connections (instant)
        3. Stop model torrents in parallel (fast)
        4. Stop controller & network resources (parallel where possible)
        5. Save settings (fast)
        6. Cleanup UI and destroy window
        7. Force exit with watchdog
        """
        # CRITICAL: Detect recursive/hanging shutdown attempts
        if hasattr(self, "_quit_in_progress"):
            logger.error(
                "⚠️⚠️⚠️ RECURSIVE QUIT DETECTED - IMMEDIATE FORCE EXIT",
                extra={"class_name": self.__class__.__name__},
            )
            os._exit(0)

        self._quit_in_progress = True
        shutdown_start_time = time.time()

        # NOTE: Settings are saved AFTER model.stop() to ensure torrent state is captured
        # (torrents call save_to_transient() during stop())

        logger.trace(
            f"🎬 SHUTDOWN START: Consolidated quit procedure "
            f"(widget={widget}, event={event}, fast_shutdown={fast_shutdown})",
            extra={"class_name": self.__class__.__name__},
        )

        # ========== START WATCHDOGS IMMEDIATELY (BEFORE ANY CLEANUP) ==========
        import threading

        def ultra_aggressive_watchdog() -> Any:
            time.sleep(self._get_shutdown_kill_timeout())  # Configurable kill timeout
            logger.error(
                "⚠️⚠️⚠️ ULTRA WATCHDOG: Shutdown blocked for 100ms - FORCE KILLING NOW",
                extra={"class_name": self.__class__.__name__},
            )
            os._exit(0)

        def backup_watchdog() -> Any:
            time.sleep(self._get_shutdown_backup_timeout())  # Configurable backup timeout
            logger.warning(
                "⚠️ BACKUP WATCHDOG: Force exit",
                extra={"class_name": self.__class__.__name__},
            )
            os._exit(0)

        # Start watchdogs BEFORE any cleanup operations
        ultra_wd = threading.Thread(target=ultra_aggressive_watchdog, daemon=True, name="UltraWatchdog")
        ultra_wd.start()

        backup_wd = threading.Thread(target=backup_watchdog, daemon=True, name="BackupWatchdog")
        backup_wd.start()

        logger.trace(
            "⏰ Watchdogs active: 100ms + 250ms force-kill",
            extra={"class_name": self.__class__.__name__},
        )

        # Initialize shutdown tracking
        self.shutdown_tracker = ShutdownProgressTracker()  # type: ignore[assignment]
        phase_times = {}

        # Configure shutdown timeout
        if fast_shutdown:
            logger.trace(
                "⚡ Using FAST shutdown mode (1s timeout)",
                extra={"class_name": self.__class__.__name__},
            )
            self.shutdown_tracker.force_shutdown_timer = 1.0  # type: ignore[attr-defined]
        else:
            logger.trace(
                "🐌 Using NORMAL shutdown mode (2s timeout)",
                extra={"class_name": self.__class__.__name__},
            )
            self.shutdown_tracker.force_shutdown_timer = 2.0  # type: ignore[attr-defined]

        self.shutdown_tracker.start_shutdown()  # type: ignore[attr-defined]

        # ========== PHASE 0: IMMEDIATE UI CLEANUP (< 10ms) ==========
        step_start = time.time()
        logger.trace(
            "🧹 PHASE 0: Cleaning up UI timers",
            extra={"class_name": self.__class__.__name__},
        )
        self._cleanup_timers()
        phase_times["ui_cleanup"] = time.time() - step_start

        # ========== PHASE 1: REMOVE SIGNAL CONNECTIONS (< 10ms) ==========
        step_start = time.time()
        logger.trace(
            "🔌 PHASE 1: Removing signal connections",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            self.remove_signals()
        except (GLib.Error, RuntimeError, AttributeError) as e:
            logger.warning(
                f"Error removing signals: {e}",
                extra={"class_name": self.__class__.__name__},
            )
        phase_times["signal_removal"] = time.time() - step_start

        # Count components for tracking
        model_torrent_count = len(self.model.torrent_list) if hasattr(self, "model") and self.model else 0

        # Register components
        self.shutdown_tracker.register_component("model_torrents", model_torrent_count)  # type: ignore[attr-defined]
        self.shutdown_tracker.register_component("peer_managers", 1)  # type: ignore[attr-defined]
        self.shutdown_tracker.register_component("background_workers", 1)  # type: ignore[attr-defined]
        self.shutdown_tracker.register_component("network_connections", 1)  # type: ignore[attr-defined]

        # ========== PHASE 2: STOP MODEL (PARALLEL TORRENT SHUTDOWN) ==========
        step_start = time.time()
        if hasattr(self, "model") and self.model:
            logger.trace(
                f"🛑 PHASE 2: Stopping {model_torrent_count} torrents (parallel)",
                extra={"class_name": self.__class__.__name__},
            )
            self.shutdown_tracker.start_component_shutdown("model_torrents")  # type: ignore[attr-defined]
            try:
                self.model.stop(shutdown_tracker=self.shutdown_tracker)
            except (RuntimeError, OSError, AttributeError) as e:
                logger.warning(
                    f"Error stopping model: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                self.shutdown_tracker.mark_completed(  # type: ignore[attr-defined]
                    "model_torrents", model_torrent_count
                )
        phase_times["model_stop"] = time.time() - step_start

        # ========== PHASE 3: STOP CONTROLLER & NETWORK ==========
        step_start = time.time()
        if hasattr(self, "app") and self.app and hasattr(self.app, "controller"):
            logger.trace(
                "🌐 PHASE 3: Stopping controller & network resources",
                extra={"class_name": self.__class__.__name__},
            )
            self.shutdown_tracker.start_component_shutdown("peer_managers")  # type: ignore[attr-defined]
            self.shutdown_tracker.start_component_shutdown("background_workers")  # type: ignore[attr-defined]
            self.shutdown_tracker.start_component_shutdown("network_connections")  # type: ignore[attr-defined]
            try:
                self.app.controller.stop(shutdown_tracker=self.shutdown_tracker)
            except (RuntimeError, OSError, AttributeError) as e:
                logger.warning(
                    f"Error stopping controller: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                self.shutdown_tracker.mark_completed("peer_managers", 1)  # type: ignore[attr-defined]
                self.shutdown_tracker.mark_completed("background_workers", 1)  # type: ignore[attr-defined]
                self.shutdown_tracker.mark_completed("network_connections", 1)  # type: ignore[attr-defined]
        phase_times["controller_stop"] = time.time() - step_start

        # ========== PHASE 4: SAVE SETTINGS (AFTER TORRENTS STOP) ==========
        step_start = time.time()
        logger.trace(
            "💾 PHASE 4: Saving settings (after torrents saved their state)",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            self.settings.save_quit()
            logger.trace(
                "✅ Settings saved successfully",
                extra={"class_name": self.__class__.__name__},
            )
        except (OSError, json.JSONDecodeError, RuntimeError) as e:
            logger.warning(
                f"Error saving settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )
        phase_times["settings_save"] = time.time() - step_start

        # ========== PHASE 5: CHECK TIMEOUT & LOG STATUS ==========
        if self.shutdown_tracker.is_force_shutdown_time():  # type: ignore[attr-defined]
            timeout_duration = self.shutdown_tracker.force_shutdown_timer  # type: ignore[attr-defined]
            logger.warning(
                f"⏰ TIMEOUT: Shutdown exceeded {timeout_duration}s limit",
                extra={"class_name": self.__class__.__name__},
            )

            pending_components = []
            components = self.shutdown_tracker.components  # type: ignore[attr-defined]
            for component_type, component_data in components.items():
                status = component_data["status"]
                if status not in ["complete", "timeout"]:
                    pending_components.append(f"{component_type}({status})")
                    self.shutdown_tracker.mark_component_timeout(component_type)  # type: ignore[attr-defined]

            if pending_components:
                logger.warning(
                    f"⚠️ Still pending: {', '.join(pending_components)}",
                    extra={"class_name": self.__class__.__name__},
                )

        # ========== PHASE 5.5: CLEANUP UI RESOURCES ==========
        step_start = time.time()
        logger.trace(
            "🧹 PHASE 5.5: Cleaning up UI resources",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            # Clean up translation manager widget registry
            if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
                tm = self.model.translation_manager
                widget_count = len(tm.translatable_widgets) if hasattr(tm, "translatable_widgets") else 0
                menu_count = len(tm.translatable_menus) if hasattr(tm, "translatable_menus") else 0

                logger.trace(
                    f"Clearing {widget_count} widget references and {menu_count} menu references",
                    extra={"class_name": self.__class__.__name__},
                )

                # Clear widget registry to release GTK widget references
                if hasattr(tm, "translatable_widgets"):
                    tm.translatable_widgets.clear()
                if hasattr(tm, "translatable_menus"):
                    tm.translatable_menus.clear()

                logger.trace(
                    f"Cleared TranslationManager registries ({widget_count} widgets, {menu_count} menus)",
                    extra={"class_name": self.__class__.__name__},
                )

            # Clean up notebook connection tabs data
            if hasattr(self, "notebook") and self.notebook:
                # Clear incoming connections data
                incoming_tab = self.notebook.get_incoming_connections()
                if incoming_tab and hasattr(incoming_tab, "connections"):
                    conn_count = len(incoming_tab.connections) if hasattr(incoming_tab.connections, "__len__") else 0
                    if conn_count > 0:
                        incoming_tab.connections.clear()
                        logger.trace(
                            f"Cleared {conn_count} incoming connection records",
                            extra={"class_name": self.__class__.__name__},
                        )

                # Clear outgoing connections data
                outgoing_tab = self.notebook.get_outgoing_connections()
                if outgoing_tab and hasattr(outgoing_tab, "connections"):
                    conn_count = len(outgoing_tab.connections) if hasattr(outgoing_tab.connections, "__len__") else 0
                    if conn_count > 0:
                        outgoing_tab.connections.clear()
                        logger.trace(
                            f"Cleared {conn_count} outgoing connection records",
                            extra={"class_name": self.__class__.__name__},
                        )

            # Force garbage collection of UI objects
            import gc

            collected = gc.collect()
            logger.trace(
                f"UI cleanup garbage collection freed {collected} objects",
                extra={"class_name": self.__class__.__name__},
            )

        except (GLib.Error, RuntimeError, AttributeError) as e:
            logger.warning(
                f"Error during UI cleanup: {e}",
                extra={"class_name": self.__class__.__name__},
            )
        phase_times["ui_resource_cleanup"] = time.time() - step_start

        # ========== PHASE 6: DESTROY WINDOW ==========
        logger.trace(
            "🏗️ PHASE 6: Destroying window",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            self.window.destroy()
        except (GLib.Error, RuntimeError, AttributeError) as e:
            logger.warning(
                f"Error destroying window: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        # ========== FINAL: LOG SUMMARY & FORCE EXIT ==========
        total_shutdown_time = time.time() - shutdown_start_time
        logger.trace(
            f"🏁 SHUTDOWN COMPLETE in {total_shutdown_time:.3f}s | "
            f"UI:{phase_times.get('ui_cleanup', 0):.3f}s "
            f"Signals:{phase_times.get('signal_removal', 0):.3f}s "
            f"Model:{phase_times.get('model_stop', 0):.3f}s "
            f"Controller:{phase_times.get('controller_stop', 0):.3f}s "
            f"Settings:{phase_times.get('settings_save', 0):.3f}s "
            f"UICleanup:{phase_times.get('ui_resource_cleanup', 0):.3f}s",
            extra={"class_name": self.__class__.__name__},
        )

        # Try graceful GTK quit (watchdogs already running from start of function)
        if hasattr(self, "app") and self.app:
            logger.trace("🚪 Calling app.quit()", extra={"class_name": self.__class__.__name__})
            try:
                self.app.quit()
            except (GLib.Error, RuntimeError, AttributeError) as e:
                logger.warning(
                    f"app.quit() failed: {e} - forcing exit",
                    extra={"class_name": self.__class__.__name__},
                )
                os._exit(0)
        else:
            logger.warning(
                "⚠️ No app ref - forcing exit",
                extra={"class_name": self.__class__.__name__},
            )
            os._exit(0)

        return False

    def on_language_changed(self, model: Any, lang_code: Any) -> None:
        """Handle language change notification from model"""
        logger.trace("on_language_changed() called with:", "View")
        logger.trace(
            f"View received language change: {lang_code}",
            extra={"class_name": self.__class__.__name__},
        )
        # TranslationManager should automatically refresh all registered widgets and menus
        widget_count = len(model.translation_manager.translatable_widgets) if model.translation_manager else 0
        menu_count = len(model.translation_manager.translatable_menus) if model.translation_manager else 0
        logger.trace(
            f"TranslationManager has {widget_count} registered widgets and {menu_count} registered menus",
            "View",
        )
        logger.trace(
            f"TranslationManager has {widget_count} registered widgets and {menu_count} registered menus",
            extra={"class_name": self.__class__.__name__},
        )
        # TranslationManager.switch_language() already handles widget refresh
        # No need to call refresh_all_translations() again to avoid infinite loops
        logger.info("Language change signal processed successfully", "View")
        logger.trace(
            "Language changed signal received, widget and menu translations already refreshed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, _source: Any, key: Any, value: Any) -> None:  # noqa: ARG002
        """Handle settings change events for theme and UI updates."""
        logger.trace(
            f"View settings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Handle theme changes
        if key == "theme":
            logger.trace(
                f"Theme setting changed to: {value}",
                extra={"class_name": self.__class__.__name__},
            )
            self.apply_theme(value)

        # Handle show_preferences trigger from tray
        elif key == "show_preferences" and value:
            logger.trace(
                "📋 Showing preferences from D-Bus/tray",
                extra={"class_name": self.__class__.__name__},
            )
            # Reset the flag immediately
            self.settings.set("show_preferences", False)
            # Show the preferences dialog
            if hasattr(self, "toolbar") and self.toolbar:
                logger.trace(
                    "Calling toolbar.show_settings_dialog()",
                    extra={"class_name": self.__class__.__name__},
                )
                GLib.idle_add(self.toolbar.show_settings_dialog)
            else:
                logger.error(
                    "Toolbar not available, cannot show settings dialog",
                    extra={"class_name": self.__class__.__name__},
                )

        # Handle show_about trigger from tray
        elif key == "show_about" and value:
            logger.trace(
                "ℹ️  Showing about dialog from D-Bus/tray",
                extra={"class_name": self.__class__.__name__},
            )
            # Reset the flag immediately
            self.settings.set("show_about", False)
            # Show the about dialog
            logger.trace("Calling show_about()", extra={"class_name": self.__class__.__name__})
            GLib.idle_add(self.show_about, None, None)

    def handle_app_settings_changed(self, _source: Any, key: Any, value: Any) -> None:  # noqa: ARG002
        """Handle AppSettings changes."""
        logger.trace(
            f"AppSettings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Handle theme style changes
        if key == "ui_settings.theme_style":
            logger.trace(
                f"Theme style changed to: {value}",
                extra={"class_name": self.__class__.__name__},
            )
            # Get current color scheme
            app_settings = AppSettings.get_instance()
            color_scheme = app_settings.get("ui_settings.color_scheme", "auto")
            self.apply_theme(value, color_scheme)

        # Handle color scheme changes
        elif key == "ui_settings.color_scheme":
            logger.trace(
                f"Color scheme changed to: {value}",
                extra={"class_name": self.__class__.__name__},
            )
            # Get current theme style
            app_settings = AppSettings.get_instance()
            theme_style = app_settings.get("ui_settings.theme_style", "classic")
            self.apply_theme(theme_style, value)

    def apply_theme(  # pylint: disable=too-many-branches,too-many-statements
        self, theme_style: str, color_scheme: str = "auto"
    ) -> None:
        """
        Apply the specified theme style and color scheme to the application.

        Args:
            theme_style: Theme style ("system", "classic", "modern")
                - "system": Use system default GTK theme (no custom CSS)
                - "classic": Deluge-style classic theme (styles-classic.css)
                - "modern": Modern chunky theme (styles-modern.css)
            color_scheme: Color scheme ("auto", "light", "dark")
                - "auto": Follow system preference
                - "light": Force light mode
                - "dark": Force dark mode
        """
        try:
            logger.trace(
                f"Applying theme: style={theme_style}, color={color_scheme}",
                extra={"class_name": self.__class__.__name__},
            )

            # Remove existing CSS provider if one exists
            if hasattr(self, "css_provider") and self.css_provider and hasattr(self, "display"):
                Gtk.StyleContext.remove_provider_for_display(self.display, self.css_provider)
                logger.trace(
                    "Removed previous CSS provider",
                    extra={"class_name": self.__class__.__name__},
                )

            # Determine which CSS file to load based on theme style
            css_file = None
            if theme_style == "classic":
                css_file = "components/ui/css/styles-classic.css"
                logger.trace("Loading Deluge-style classic theme")
            elif theme_style == "modern":
                css_file = "components/ui/css/styles-modern.css"
                logger.trace("Loading modern chunky theme")
            elif theme_style == "system":
                # No custom CSS - use system default
                logger.trace(
                    "Using system default theme (no custom CSS)",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    f"Unknown theme style: {theme_style}, falling back to classic",
                    extra={"class_name": self.__class__.__name__},
                )
                css_file = "components/ui/css/styles-classic.css"

            # Load and apply the CSS file if specified
            if css_file:
                self.css_provider = Gtk.CssProvider()
                css_file_path = os.path.join(os.environ.get("DFS_PATH", "."), css_file)

                if not os.path.exists(css_file_path):
                    logger.error(
                        f"CSS file not found: {css_file_path}",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    self.css_provider.load_from_path(css_file_path)

                    # Apply CSS globally to the display
                    if not hasattr(self, "display"):
                        self.display = self.window.get_display()

                    Gtk.StyleContext.add_provider_for_display(
                        self.display, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                    )

                    logger.trace(
                        f"CSS loaded: {css_file_path}",
                        extra={"class_name": self.__class__.__name__},
                    )

            # Apply color scheme using Adwaita StyleManager
            try:
                style_manager = Adw.StyleManager.get_default()

                # Add/remove 'dark' CSS class for programmatic dark mode styling
                if color_scheme == "auto":
                    style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
                    # Remove dark class - let system preference decide
                    self.window.remove_css_class("dark")
                    logger.trace("Color scheme set to follow system preference")
                elif color_scheme == "light":
                    style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
                    # Remove dark class for light mode
                    self.window.remove_css_class("dark")
                    logger.trace("Color scheme set to light")
                elif color_scheme == "dark":
                    style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
                    # Add dark class for CSS dark mode styling
                    self.window.add_css_class("dark")
                    logger.trace("Color scheme set to dark with CSS class")
                else:
                    logger.warning(f"Unknown color scheme: {color_scheme}, using auto")
                    style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
                    self.window.remove_css_class("dark")

            except (GLib.Error, RuntimeError, AttributeError) as adw_error:
                logger.trace(
                    f"Adwaita StyleManager not available: {adw_error}",
                    extra={"class_name": self.__class__.__name__},
                )

            logger.trace(
                f"Theme successfully applied: style={theme_style}, color={color_scheme}",
                extra={"class_name": self.__class__.__name__},
            )

        except (GLib.Error, RuntimeError, AttributeError) as e:
            logger.error(
                f"Error applying theme (style={theme_style}, color={color_scheme}): {e}",
                extra={"class_name": self.__class__.__name__},
            )
