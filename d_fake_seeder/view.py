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
from d_fake_seeder.components.component.states import States  # noqa: E402
from d_fake_seeder.components.component.statusbar import Statusbar  # noqa: E402
from d_fake_seeder.components.component.toolbar import Toolbar  # noqa: E402

# Importing necessary libraries
from d_fake_seeder.components.component.torrent_details import TorrentDetailsNotebook  # noqa: E402
from d_fake_seeder.components.component.torrents import Torrents  # noqa: E402
from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402

# Translation function will be provided by model's TranslationManager
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.shutdown_progress import ShutdownProgressTracker  # noqa: E402


# View class for Torrent Application
class View:
    instance = None
    toolbar = None
    notebook = None
    torrents_columnview = None
    torrents_states = None

    def __init__(self, app):
        with logger.performance.operation_context("view_init", self.__class__.__name__):
            logger.debug("View.__init__() started", self.__class__.__name__)
            logger.info("View instantiate", self.__class__.__name__)
            self.app = app
            View.instance = self
            # Initialize timeout_id to prevent warnings on cleanup
            with logger.performance.operation_context("basic_init", self.__class__.__name__):
                self.timeout_id = 0
                self.timeout_source = None
                # Initialize shutdown progress tracking
                self.shutdown_tracker = None
                self.shutdown_overlay = None
                logger.debug("Basic initialization completed", self.__class__.__name__)
            # subscribe to settings changed
            with logger.performance.operation_context("settings_init", self.__class__.__name__):
                self.settings = AppSettings.get_instance()
                self.settings.connect("attribute-changed", self.handle_settings_changed)
                logger.debug("Settings subscription completed", self.__class__.__name__)
            # Loading GUI from XML
            with logger.performance.operation_context("builder_creation", self.__class__.__name__):
                logger.debug("About to create Gtk.Builder", self.__class__.__name__)
                self.builder = Gtk.Builder()
                logger.debug("Gtk.Builder created", self.__class__.__name__)
            with logger.performance.operation_context("xml_loading", self.__class__.__name__):
                logger.debug("About to load XML file", self.__class__.__name__)
                self.builder.add_from_file(os.environ.get("DFS_PATH") + "/components/ui/generated/generated.xml")
                logger.debug("XML file loaded", self.__class__.__name__)
            # CSS will be loaded and applied in setup_window() method
            # Get window object
            with logger.performance.operation_context("window_setup", self.__class__.__name__):
                self.window = self.builder.get_object("main_window")
                # Set window icon using icon name
                self.window.set_icon_name("dfakeseeder")
                # Also set the application ID to match desktop file
                if hasattr(self.app, "set_application_id"):
                    self.app.set_application_id("ie.fio.dfakeseeder")
                logger.debug("Window setup completed", self.__class__.__name__)
        # views
        logger.debug("About to create Torrents component", "View")
        self.torrents = Torrents(self.builder, None)
        logger.debug(
            "Torrents component created successfully (took {(torrents_end - torrents_start)*1000:.1f}ms)", "View"
        )
        logger.debug("About to create Toolbar component", "View")
        self.toolbar = Toolbar(self.builder, None, self.app)
        logger.debug("Toolbar component created successfully (took {(toolbar_end - toolbar_start)*1000:.1f}ms)", "View")
        logger.debug("About to create TorrentDetailsNotebook component", "View")
        self.notebook = TorrentDetailsNotebook(self.builder, None)
        logger.debug(
            "TorrentDetailsNotebook component created successfully (took {(notebook_end - notebook_start)*1000:.1f}ms)",
            "View",
        )
        logger.debug("About to create States component", "View")
        self.states = States(self.builder, None)
        logger.debug("States component created successfully (took {(states_end - states_start)*1000:.1f}ms)", "View")
        logger.debug("About to create Statusbar component", "View")
        self.statusbar = Statusbar(self.builder, None)
        logger.debug(
            "Statusbar component created successfully (took {(statusbar_end - statusbar_start)*1000:.1f}ms)", "View"
        )
        # Getting relevant objects
        self.quit_menu_item = self.builder.get_object("quit_menu_item")
        self.help_menu_item = self.builder.get_object("help_menu_item")
        self.overlay = self.builder.get_object("overlay")
        self.status = self.builder.get_object("status_label")
        self.main_paned = self.builder.get_object("main_paned")
        self.paned = self.builder.get_object("paned")
        self.notebook_widget = self.builder.get_object("notebook1")
        self.current_time = time.time()
        logger.debug("Getting relevant objects completed (took {(objects_end - objects_start)*1000:.1f}ms)", "View")
        # notification overlay
        self.notify_label = Gtk.Label(label=self._("Overlay Notification"))
        # self.notify_label.set_no_show_all(True)
        self.notify_label.set_visible(False)
        self.notify_label.hide()
        self.notify_label.set_valign(Gtk.Align.CENTER)
        self.notify_label.set_halign(Gtk.Align.CENTER)
        self.overlay.add_overlay(self.notify_label)
        logger.debug("Notification overlay setup completed (took {(overlay_end - overlay_start)*1000:.1f}ms)", "View")
        # Get UI settings for configurable timeouts
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.resize_delay = ui_settings.get("resize_delay_seconds", 1.0)
        self.splash_display_duration = ui_settings.get("splash_display_duration_seconds", 2)
        self.splash_fade_interval = ui_settings.get("splash_fade_interval_ms", 75)
        self.splash_fade_step = ui_settings.get("splash_fade_step", 0.025)
        self.splash_image_size = ui_settings.get("splash_image_size_pixels", 100)
        self.notification_timeout_min = ui_settings.get("notification_timeout_min_ms", 2000)
        self.notification_timeout_multiplier = ui_settings.get("notification_timeout_multiplier", 500)
        logger.debug(
            "UI settings configuration completed (took {(ui_settings_end - ui_settings_start)*1000:.1f}ms)", "View"
        )
        logger.debug("About to call setup_window()", "View")
        self.setup_window()
        logger.debug("setup_window() completed (took ms)", "View")
        logger.debug("About to show splash image", "View")
        self.show_splash_image()
        logger.debug("Splash image shown (took ms)", "View")
        GLib.timeout_add_seconds(int(self.resize_delay), self.resize_panes)
        logger.debug("Timeout for resize panes added (took {(timeout_end - timeout_start)*1000:.1f}ms)", "View")
        # Shutdown overlay disabled - keeping only shutdown tracking behavior
        self.shutdown_overlay = None
        logger.debug("View.__init__() completed", "View")

    def _(self, text):
        """Get translation function from model's TranslationManager"""
        if hasattr(self, "model") and self.model and hasattr(self.model, "translation_manager"):
            return self.model.translation_manager.translate_func(text)
        return text  # Fallback if model not set yet

    def setup_window(self):
        # Get application settings
        app_settings = AppSettings.get_instance()
        app_title = app_settings.get("application", {}).get("title", self._("D' Fake Seeder"))
        css_file = app_settings.get("application", {}).get("css_file", "ui/styles.css")
        self.window.set_title(app_title)
        self.window.set_application(self.app)
        # Load CSS stylesheet
        css_provider = Gtk.CssProvider()
        css_file_path = os.environ.get("DFS_PATH") + "/" + css_file
        css_provider.load_from_path(css_file_path)
        # Apply CSS globally to the display for better theme consistency
        display = self.window.get_display()
        Gtk.StyleContext.add_provider_for_display(display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        logger.debug(f"CSS loaded and applied globally: {css_file_path}")
        # Store CSS provider for theme switching
        self.css_provider = css_provider
        self.display = display
        # Apply initial theme
        initial_theme = app_settings.get("theme", "system")
        self.apply_theme(initial_theme)
        # Connect to AppSettings changes for theme switching
        app_settings.connect("attribute-changed", self.handle_app_settings_changed)
        # Create an action group
        self.action_group = Gio.SimpleActionGroup()
        # add hamburger menu
        self.header = Gtk.HeaderBar()
        self.window.set_titlebar(self.header)
        # Create a new "Action"
        action = Gio.SimpleAction.new("quit", None)
        action.connect("activate", self.quit)
        self.action_group.add_action(action)
        # Create standard menu with translatable structure
        self.main_menu_items = [{"action": "win.about", "key": "About"}, {"action": "win.quit", "key": "Quit"}]
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
        # Add an about dialog
        action = Gio.SimpleAction.new("about", None)
        action.connect("activate", self.show_about)
        self.action_group.add_action(action)
        # Insert the action group into the window
        self.window.insert_action_group("win", self.action_group)
        # Register widgets for automatic translation
        if hasattr(self, "model") and self.model:
            self.model.translation_manager.scan_builder_widgets(self.builder)
            logger.debug("Registered widgets for translation", extra={"class_name": self.__class__.__name__})
        self.window.present()

    def show_splash_image(self):
        # splash image
        self.splash_image = Gtk.Image()
        self.splash_image.set_from_file(os.environ.get("DFS_PATH") + "/components/images/dfakeseeder.png")
        # self.splash_image.set_no_show_all(False)
        self.splash_image.set_visible(True)
        self.splash_image.show()
        self.splash_image.set_valign(Gtk.Align.CENTER)
        self.splash_image.set_halign(Gtk.Align.CENTER)
        self.splash_image.set_size_request(self.splash_image_size, self.splash_image_size)
        self.overlay.add_overlay(self.splash_image)
        GLib.timeout_add_seconds(self.splash_display_duration, self.fade_out_image)

    def show_about(self, action, _param):
        self.window.about = Gtk.AboutDialog()
        self.window.about.set_transient_for(self.window)
        self.window.about.set_modal(self)
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

        file = Gio.File.new_for_path(os.environ.get("DFS_PATH") + "/" + self.settings.logo)
        texture = Gdk.Texture.new_from_file(file)
        self.window.about.set_logo(texture)
        self.window.about.show()

    def fade_out_image(self):
        self.splash_image.fade_out = 1.0
        GLib.timeout_add(self.splash_fade_interval, self.fade_image)

    def fade_image(self):
        self.splash_image.fade_out -= self.splash_fade_step
        if self.splash_image.fade_out > 0:
            self.splash_image.set_opacity(self.splash_image.fade_out)
            return True
        else:
            self.splash_image.hide()
            self.splash_image.unparent()
            self.splash_image = None
            return False

    def resize_panes(self):
        logger.info("View resize_panes", extra={"class_name": self.__class__.__name__})
        allocation = self.main_paned.get_allocation()
        available_height = allocation.height
        position = available_height // 2
        self.main_paned.set_position(position)
        allocation = self.paned.get_allocation()
        available_width = allocation.width
        position = available_width // 4
        self.paned.set_position(position)

    # Setting model for the view
    def notify(self, text):
        logger.info("View notify", extra={"class_name": self.__class__.__name__})
        # Cancel the previous timeout, if it exists
        if hasattr(self, "timeout_source") and self.timeout_source and not self.timeout_source.is_destroyed():
            self.timeout_source.destroy()
            self.timeout_source = None
        self.timeout_id = 0
        # self.notify_label.set_no_show_all(False)
        self.notify_label.set_visible(True)
        self.notify_label.show()
        self.notify_label.set_text(text)
        self.status.set_text(text)
        # Use configurable notification timeout (based on tickspeed, minimum configurable)
        notification_timeout = max(
            self.notification_timeout_min,
            int(self.settings.tickspeed * self.notification_timeout_multiplier),
        )
        # Create timeout source and store reference
        self.timeout_source = GLib.timeout_source_new(notification_timeout)
        self.timeout_source.set_callback(
            lambda user_data: self.notify_label.set_visible(False) or self.notify_label.hide()
        )
        self.timeout_id = self.timeout_source.attach(GLib.MainContext.default())

    # Setting model for the view
    def set_model(self, model):
        logger.info("View set model", extra={"class_name": self.__class__.__name__})
        self.model = model
        self.notebook.set_model(model)
        self.toolbar.set_model(model)
        self.torrents.set_model(model)
        self.states.set_model(model)
        self.statusbar.set_model(model)
        # Pass view reference to statusbar so it can access connection components
        self.statusbar.view = self
        # Connect to language change signal
        self.model.connect("language-changed", self.on_language_changed)
        # Register widgets for translation after model is set
        self.model.translation_manager.scan_builder_widgets(self.builder)
        # Debug: Check how many widgets were registered
        widget_count = len(self.model.translation_manager.translatable_widgets)
        logger.info(
            f"Registered {widget_count} widgets for automatic translation",
            extra={"class_name": self.__class__.__name__},
        )
        # Debug: Print discovered translatable widgets (only in debug mode)
        if logger.isEnabledFor(logging.DEBUG):
            self.model.translation_manager.print_discovered_widgets()
        # CRITICAL FIX: Refresh translations for newly registered widgets
        # This ensures that widgets get translated with the correct language on startup
        if widget_count > 0:
            logger.info(
                "Newly registered widgets will be refreshed by debounced system",
                extra={"class_name": self.__class__.__name__},
            )
            # Use debounced refresh to avoid cascading refresh operations during startup
            self.model.translation_manager.refresh_all_translations()
        # Register notebook for translation updates
        if hasattr(self.notebook, "register_for_translation"):
            self.notebook.register_for_translation()
        # Register main menu for translation updates
        if hasattr(self, "main_menu") and hasattr(self, "main_menu_items"):
            self.model.translation_manager.register_menu(self.main_menu, self.main_menu_items, popover=self.popover)
            logger.info(
                f"Registered main menu with {len(self.main_menu_items)} items for translation",
                extra={"class_name": self.__class__.__name__},
            )

    # Connecting signals for different events
    def connect_signals(self):
        logger.info(
            "View connect signals",
            extra={"class_name": self.__class__.__name__},
        )
        self.window.connect("destroy", self.quit)
        self.window.connect("close-request", self.quit)
        self.model.connect("data-changed", self.torrents.update_view)
        self.model.connect("data-changed", self.notebook.update_view)
        self.model.connect("data-changed", self.states.update_view)
        self.model.connect("data-changed", self.statusbar.update_view)
        self.model.connect("data-changed", self.toolbar.update_view)
        # LAZY LOADING FIX: Connect to connection components only if they exist
        # They will be connected later when created in background
        incoming_connections = self.notebook.get_incoming_connections()
        if incoming_connections:
            self.model.connect("data-changed", incoming_connections.update_view)
        outgoing_connections = self.notebook.get_outgoing_connections()
        if outgoing_connections:
            self.model.connect("data-changed", outgoing_connections.update_view)
        self.model.connect("selection-changed", self.torrents.model_selection_changed)
        self.model.connect("selection-changed", self.notebook.model_selection_changed)
        self.model.connect("selection-changed", self.states.model_selection_changed)
        self.model.connect("selection-changed", self.statusbar.model_selection_changed)
        self.model.connect("selection-changed", self.toolbar.model_selection_changed)
        signal.signal(signal.SIGINT, self.quit)

    # Connecting signals for different events
    def remove_signals(self):
        logger.info("Remove signals", extra={"class_name": self.__class__.__name__})
        self.model.disconnect_by_func(self.torrents.update_view)
        self.model.disconnect_by_func(self.notebook.update_view)
        self.model.disconnect_by_func(self.states.update_view)
        self.model.disconnect_by_func(self.statusbar.update_view)
        self.model.disconnect_by_func(self.notebook.get_incoming_connections().update_view)
        self.model.disconnect_by_func(self.notebook.get_outgoing_connections().update_view)

    # Event handler for clicking on quit
    def on_quit_clicked(self, menu_item, fast_shutdown=False):
        logger.info(
            "🎯 ON_QUIT_CLICKED: Starting complete quit procedure", extra={"class_name": self.__class__.__name__}
        )
        logger.info("🔌 ON_QUIT_CLICKED: Removing signal connections", extra={"class_name": self.__class__.__name__})
        self.remove_signals()
        logger.info(
            "🎬 ON_QUIT_CLICKED: Signal removal complete, calling quit()", extra={"class_name": self.__class__.__name__}
        )
        self.quit(fast_shutdown=fast_shutdown)
        logger.info(
            "🏁 ON_QUIT_CLICKED: Complete quit procedure finished", extra={"class_name": self.__class__.__name__}
        )

    # open github webpage
    def on_help_clicked(self, menu_item):
        logger.info(
            "Opening GitHub webpage",
            extra={"class_name": self.__class__.__name__},
        )
        webbrowser.open(self.settings.issues_page)

    def handle_peer_connection_event(self, direction, action, address, port, data=None):
        """Handle peer connection events from peer server or connection manager"""
        torrent_hash = (data or {}).get("torrent_hash", "unknown") if data else "unknown"
        logger.debug(
            f"Peer connection event: {direction} {action} {address}:{port} " f"(torrent: {torrent_hash})",
            extra={"class_name": self.__class__.__name__},
        )
        try:
            if direction == "incoming":
                component = self.notebook.get_incoming_connections()
                if action == "add":
                    component.add_incoming_connection(address, port, **(data or {}))
                    total_count = component.get_total_connection_count()
                    visible_count = component.get_connection_count()
                    connection_word = "connection" if total_count == 1 else "connections"
                    message = (
                        f"Added incoming connection. Total: {total_count} {connection_word}, Visible: {visible_count}"
                    )
                    logger.info(
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
                        f"Removed incoming connection. Total: {total_count} {connection_word}, Visible: {visible_count}"
                    )
                    logger.info(
                        message,
                        extra={"class_name": self.__class__.__name__},
                    )
            elif direction == "outgoing":
                component = self.notebook.get_outgoing_connections()
                if action == "add":
                    component.add_outgoing_connection(address, port, **(data or {}))
                    total_count = component.get_total_connection_count()
                    visible_count = component.get_connection_count()
                    connection_word = "connection" if total_count == 1 else "connections"
                    message = (
                        f"Added outgoing connection. Total: {total_count} {connection_word}, Visible: {visible_count}"
                    )
                    logger.info(
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
                        f"Removed outgoing connection. Total: {total_count} {connection_word}, Visible: {visible_count}"
                    )
                    logger.info(
                        message,
                        extra={"class_name": self.__class__.__name__},
                    )
            # Update connection counts
            self.notebook.update_connection_counts()
        except Exception as e:
            logger.error(
                f"Error handling peer connection event: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    # Function to quit the application
    def quit(self, widget=None, event=None, fast_shutdown=False):
        logger.info(
            f"🎬 VIEW QUIT START: view.quit() method called "
            f"(widget={widget}, event={event}, fast_shutdown={fast_shutdown})",
            extra={"class_name": self.__class__.__name__},
        )
        logger.info("🔧 VIEW QUIT: Initializing ShutdownProgressTracker", extra={"class_name": self.__class__.__name__})
        # Initialize shutdown progress tracking
        self.shutdown_tracker = ShutdownProgressTracker()

        # Use shorter timeout for D-Bus triggered shutdowns
        if fast_shutdown:
            logger.info(
                "⚡ VIEW QUIT: Using fast shutdown mode (2 second timeout)",
                extra={"class_name": self.__class__.__name__},
            )
            self.shutdown_tracker.force_shutdown_timer = 2.0  # 2 seconds for fast quit
        else:
            logger.info(
                "🐌 VIEW QUIT: Using normal shutdown mode (5 second timeout)",
                extra={"class_name": self.__class__.__name__},
            )
            self.shutdown_tracker.force_shutdown_timer = 5.0  # 5 seconds for normal quit

        self.shutdown_tracker.start_shutdown()
        logger.info("▶️ VIEW QUIT: ShutdownProgressTracker started", extra={"class_name": self.__class__.__name__})
        # Count components that need to be shut down
        model_torrent_count = 0
        peer_manager_count = 0
        background_worker_count = 0
        network_connection_count = 0
        # Count model torrents
        if hasattr(self, "model") and self.model and hasattr(self.model, "torrent_list"):
            model_torrent_count = len(self.model.torrent_list)
        # Count peer managers and connections from controller
        if hasattr(self, "app") and self.app and hasattr(self.app, "controller"):
            controller = self.app.controller
            if hasattr(controller, "global_peer_manager") and controller.global_peer_manager:
                # Count active torrent peer managers
                peer_manager_count = len(getattr(controller.global_peer_manager, "torrent_managers", {}))
                # Count active network connections
                if hasattr(controller.global_peer_manager, "peer_server"):
                    network_connection_count += 1
                # Count background worker threads
                background_worker_count = 1  # Global peer manager main thread
        # Register components with tracker
        self.shutdown_tracker.register_component("model_torrents", model_torrent_count)
        self.shutdown_tracker.register_component("peer_managers", peer_manager_count)
        self.shutdown_tracker.register_component("background_workers", background_worker_count)
        self.shutdown_tracker.register_component("network_connections", network_connection_count)
        # Shutdown progress tracking continues in background (overlay removed)
        # Step 1: Stop model first (stops individual torrents and their seeders)
        if hasattr(self, "model") and self.model:
            logger.info("Stopping model during quit", extra={"class_name": self.__class__.__name__})
            self.shutdown_tracker.start_component_shutdown("model_torrents")
            # Pass shutdown tracker to model for progress callbacks
            try:
                self.model.stop(shutdown_tracker=self.shutdown_tracker)
            except TypeError:
                # Fallback for older stop() method without shutdown_tracker parameter
                self.model.stop()
                # Mark all model torrents as completed if no callback support
                self.shutdown_tracker.mark_completed("model_torrents", model_torrent_count)
        # Step 2: Stop the controller (stops global peer manager)
        if hasattr(self, "app") and self.app and hasattr(self.app, "controller"):
            logger.info("Stopping controller during quit", extra={"class_name": self.__class__.__name__})
            self.shutdown_tracker.start_component_shutdown("peer_managers")
            self.shutdown_tracker.start_component_shutdown("background_workers")
            self.shutdown_tracker.start_component_shutdown("network_connections")
            # Pass shutdown tracker to controller for progress callbacks
            try:
                self.app.controller.stop(shutdown_tracker=self.shutdown_tracker)
            except TypeError:
                # Fallback for older stop() method without shutdown_tracker parameter
                self.app.controller.stop()
                # Mark components as completed if no callback support
                self.shutdown_tracker.mark_completed("peer_managers", peer_manager_count)
                self.shutdown_tracker.mark_completed("background_workers", background_worker_count)
                self.shutdown_tracker.mark_completed("network_connections", network_connection_count)
        # Step 3: Save settings
        logger.info("Saving settings during quit", extra={"class_name": self.__class__.__name__})
        self.settings.save_quit()
        # Step 4: Check if force shutdown is needed
        if self.shutdown_tracker and self.shutdown_tracker.is_force_shutdown_time():
            timeout_duration = self.shutdown_tracker.force_shutdown_timer
            logger.warning(
                f"⏰ FORCE SHUTDOWN: Timeout reached after {timeout_duration} seconds",
                extra={"class_name": self.__class__.__name__},
            )

            # Log which components are still pending
            pending_components = []
            for component_type in self.shutdown_tracker.components:
                component_status = self.shutdown_tracker.components[component_type]["status"]
                if component_status not in ["complete", "timeout"]:
                    pending_components.append(f"{component_type}({component_status})")
                    self.shutdown_tracker.mark_component_timeout(component_type)

            if pending_components:
                logger.warning(
                    f"🐌 FORCE SHUTDOWN: These components were still pending: {', '.join(pending_components)}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.info(
                    "✅ FORCE SHUTDOWN: All components completed, force shutdown was just a safety check",
                    extra={"class_name": self.__class__.__name__},
                )
        # Step 5: Shutdown tracking completed (overlay cleanup removed)
        # Step 6: Destroy window and quit application
        logger.info("🏗️ VIEW QUIT: Destroying window during quit", extra={"class_name": self.__class__.__name__})
        self.window.destroy()

        # Step 7: Quit the GTK application to fully terminate
        if hasattr(self, "app") and self.app:
            logger.info(
                "🚪 VIEW QUIT: Calling app.quit() to terminate GTK application",
                extra={"class_name": self.__class__.__name__},
            )
            self.app.quit()
        else:
            logger.warning(
                "⚠️ VIEW QUIT: No app reference found, GTK loop may continue running",
                extra={"class_name": self.__class__.__name__},
            )

        logger.info(
            "🏁 VIEW QUIT COMPLETE: view.quit() method finished successfully",
            extra={"class_name": self.__class__.__name__},
        )

        # Return False to allow GTK to process the close-request signal normally
        return False

    def on_language_changed(self, model, lang_code):
        """Handle language change notification from model"""
        logger.debug("on_language_changed() called with:", "View")
        logger.info(f"View received language change: {lang_code}", extra={"class_name": self.__class__.__name__})
        # TranslationManager should automatically refresh all registered widgets and menus
        widget_count = len(model.translation_manager.translatable_widgets) if model.translation_manager else 0
        menu_count = len(model.translation_manager.translatable_menus) if model.translation_manager else 0
        logger.debug(
            f"TranslationManager has {widget_count} registered widgets and {menu_count} registered menus", "View"
        )
        logger.info(
            f"TranslationManager has {widget_count} registered widgets and {menu_count} registered menus",
            extra={"class_name": self.__class__.__name__},
        )
        # TranslationManager.switch_language() already handles widget refresh
        # No need to call refresh_all_translations() again to avoid infinite loops
        logger.debug("Language change signal processed successfully", "View")
        logger.info(
            "Language changed signal received, widget and menu translations already refreshed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, _source, key, value):  # noqa: ARG002
        logger.debug(
            f"View settings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Handle theme changes
        if key == "theme":
            logger.debug(f"Theme setting changed to: {value}", extra={"class_name": self.__class__.__name__})
            self.apply_theme(value)

        # Handle show_preferences trigger from tray
        elif key == "show_preferences" and value:
            logger.info("📋 Showing preferences from D-Bus/tray", extra={"class_name": self.__class__.__name__})
            # Reset the flag immediately
            self.settings.set("show_preferences", False)
            # Show the preferences dialog
            if hasattr(self, "toolbar") and self.toolbar:
                logger.info("Calling toolbar.show_settings_dialog()", extra={"class_name": self.__class__.__name__})
                GLib.idle_add(self.toolbar.show_settings_dialog)
            else:
                logger.error(
                    "Toolbar not available, cannot show settings dialog", extra={"class_name": self.__class__.__name__}
                )

        # Handle show_about trigger from tray
        elif key == "show_about" and value:
            logger.info("ℹ️  Showing about dialog from D-Bus/tray", extra={"class_name": self.__class__.__name__})
            # Reset the flag immediately
            self.settings.set("show_about", False)
            # Show the about dialog
            logger.info("Calling show_about()", extra={"class_name": self.__class__.__name__})
            GLib.idle_add(self.show_about, None, None)

    def handle_app_settings_changed(self, _source, key, value):  # noqa: ARG002
        """Handle AppSettings changes."""
        logger.debug(
            f"AppSettings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Handle theme changes
        if key == "theme":
            logger.debug(f"Theme setting changed to: {value}", extra={"class_name": self.__class__.__name__})
            self.apply_theme(value)

    def apply_theme(self, theme: str) -> None:
        """
        Apply the specified theme to the application using modern Adwaita StyleManager.

        Args:
            theme: Theme name ("system", "light", "dark")
        """
        try:
            logger.debug(f"Applying theme: {theme}", extra={"class_name": self.__class__.__name__})

            # Use modern AdwStyleManager instead of deprecated GTK settings
            style_manager = Adw.StyleManager.get_default()

            if theme == "system":
                # Follow system theme preference
                style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
                logger.debug("Theme set to follow system preference", extra={"class_name": self.__class__.__name__})
            elif theme == "light":
                # Force light theme
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
                logger.debug("Theme set to light", extra={"class_name": self.__class__.__name__})
            elif theme == "dark":
                # Force dark theme
                style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
                logger.debug("Theme set to dark", extra={"class_name": self.__class__.__name__})
            else:
                logger.warning(
                    f"Unknown theme: {theme}, falling back to system", extra={"class_name": self.__class__.__name__}
                )
                style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)

            # Add CSS classes for additional theme control
            if hasattr(self, "window") and self.window:
                style_context = self.window.get_style_context()
                # Remove existing theme classes
                style_context.remove_class("theme-light")
                style_context.remove_class("theme-dark")

                # Add appropriate theme class
                if theme == "light":
                    style_context.add_class("theme-light")
                elif theme == "dark":
                    style_context.add_class("theme-dark")

                logger.debug(f"CSS theme class applied: theme-{theme}", extra={"class_name": self.__class__.__name__})

            # Try Adwaita StyleManager as fallback if available
            try:
                theme_manager = Adw.StyleManager.get_default()
                if theme == "system":
                    theme_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)
                elif theme == "light":
                    theme_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
                elif theme == "dark":
                    theme_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
                logger.debug("Adwaita StyleManager also applied", extra={"class_name": self.__class__.__name__})
            except Exception as adw_error:
                logger.debug(
                    f"Adwaita StyleManager not available: {adw_error}", extra={"class_name": self.__class__.__name__}
                )

            logger.info(f"Theme successfully applied: {theme}", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(f"Error applying theme {theme}: {e}", extra={"class_name": self.__class__.__name__})
