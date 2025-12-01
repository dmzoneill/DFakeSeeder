# fmt: off
import os

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.global_peer_manager import GlobalPeerManager
from d_fake_seeder.lib.handlers.torrent_folder_watcher import TorrentFolderWatcher

# from domain.torrent.listener import Listener
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.dbus_unifier import DBusUnifier
from d_fake_seeder.lib.util.window_manager import WindowManager

# fmt: on


# Cont roller
class Controller:
    def __init__(self, view, model):
        logger.debug("Startup", extra={"class_name": self.__class__.__name__})
        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.view = view
        self.model = model

        # Initialize global peer manager
        self.global_peer_manager = GlobalPeerManager()

        # Initialize window manager with main window
        self.window_manager = None  # Will be set after view initialization

        # Initialize torrent folder watcher (pass global_peer_manager for P2P integration)
        self.torrent_watcher = TorrentFolderWatcher(model, self.settings, self.global_peer_manager)

        # Initialize D-Bus service for tray communication
        self.dbus = None
        try:
            self.dbus = DBusUnifier()
            logger.debug(
                "D-Bus service initialized",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Failed to initialize D-Bus service: {e}",
                extra={"class_name": self.__class__.__name__},
            )

        # self.listener = Listener(self.model)
        # self.listener.start()
        self.view.set_model(self.model)

        # Initialize window manager after view is set up
        if hasattr(self.view, "window") and self.view.window:
            self.window_manager = WindowManager(self.view.window)
            logger.debug(
                "Window manager initialized",
                extra={"class_name": self.__class__.__name__},
            )

        # Make managers accessible to view components
        self.view.global_peer_manager = self.global_peer_manager
        self.view.statusbar.global_peer_manager = self.global_peer_manager
        self.view.notebook.global_peer_manager = self.global_peer_manager
        if self.window_manager:
            self.view.window_manager = self.window_manager

        # Set up connection callback for UI updates
        self.global_peer_manager.set_connection_callback(self.view.handle_peer_connection_event)

        # Start global peer manager after setting up callbacks
        self.global_peer_manager.start()

        # Setup D-Bus signal forwarding after all components are initialized
        if self.dbus:
            self.dbus.setup_settings_signal_forwarding()
            logger.debug(
                "D-Bus settings signal forwarding enabled",
                extra={"class_name": self.__class__.__name__},
            )

        self.view.connect_signals()

    def run(self):
        logger.debug("Controller Run", extra={"class_name": self.__class__.__name__})
        for filename in os.listdir(os.path.expanduser("~/.config/dfakeseeder/torrents")):
            if filename.endswith(".torrent"):
                torrent_file = os.path.join(
                    os.path.expanduser("~/.config/dfakeseeder/torrents"),
                    filename,
                )
                self.model.add_torrent(torrent_file)

        # Add all torrents to global peer manager after model is populated
        for torrent in self.model.get_torrents():
            self.global_peer_manager.add_torrent(torrent)

        # Start watching folder for new torrents
        self.torrent_watcher.start()

    def stop(self, shutdown_tracker=None):
        """Stop the controller and cleanup all background processes"""
        logger.debug("Controller stopping", extra={"class_name": self.__class__.__name__})

        # Stop global peer manager
        if hasattr(self, "global_peer_manager") and self.global_peer_manager:
            self.global_peer_manager.stop(shutdown_tracker=shutdown_tracker)
        else:
            # Mark components as completed if no global peer manager
            if shutdown_tracker:
                shutdown_tracker.mark_completed("peer_managers", 0)
                shutdown_tracker.mark_completed("background_workers", 0)
                shutdown_tracker.mark_completed("network_connections", 0)

        # Stop torrent folder watcher
        if hasattr(self, "torrent_watcher") and self.torrent_watcher:
            self.torrent_watcher.stop()

        logger.debug(
            "🔧 About to cleanup window manager",
            extra={"class_name": self.__class__.__name__},
        )
        # Cleanup window manager
        if hasattr(self, "window_manager") and self.window_manager:
            self.window_manager.cleanup()
        logger.debug(
            "✅ Window manager cleanup complete",
            extra={"class_name": self.__class__.__name__},
        )

        logger.debug("🔧 About to cleanup D-Bus", extra={"class_name": self.__class__.__name__})
        # Cleanup D-Bus service
        if hasattr(self, "dbus") and self.dbus:
            self.dbus.cleanup()
        logger.debug("✅ D-Bus cleanup complete", extra={"class_name": self.__class__.__name__})

        logger.debug("Controller stopped", extra={"class_name": self.__class__.__name__})

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            f"Controller settings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Handle watch folder settings changes
        if key.startswith("watch_folder"):
            if hasattr(self, "torrent_watcher"):
                # Restart watcher when settings change
                self.torrent_watcher.stop()
                self.torrent_watcher.start()

        # Handle window management settings changes
        if self.window_manager and key in [
            "window_visible",
            "close_to_tray",
            "minimize_to_tray",
        ]:
            if key == "window_visible":
                if value:
                    self.window_manager.show()
                else:
                    self.window_manager.hide()

        # Handle application quit request
        if key == "application_quit_requested" and value:
            logger.debug(
                "🚨 QUIT SEQUENCE START: Quit requested via D-Bus settings",
                extra={"class_name": self.__class__.__name__},
            )
            # Don't reset the flag here - it will be reset when settings are saved during quit
            # Resetting it here can cause signal loops

            # Trigger proper application shutdown (not immediate quit)
            if hasattr(self, "view") and self.view:
                logger.debug(
                    "✅ QUIT SEQUENCE: Found view object, triggering proper shutdown sequence",
                    extra={"class_name": self.__class__.__name__},
                )
                if hasattr(self.view, "on_quit_clicked"):
                    logger.debug(
                        "🎯 QUIT SEQUENCE: Calling self.view.on_quit_clicked() with fast_shutdown=True for D-Bus quit",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.view.on_quit_clicked(None, fast_shutdown=True)  # Use fast shutdown for D-Bus triggered quit
                    logger.debug(
                        "📞 QUIT SEQUENCE: self.view.on_quit_clicked() call completed",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    logger.debug(
                        "🎯 QUIT SEQUENCE: Calling self.view.quit() with fast_shutdown=True "
                        "for ShutdownProgressTracker shutdown",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.view.quit(fast_shutdown=True)  # Fallback to direct quit with fast shutdown
                    logger.debug(
                        "📞 QUIT SEQUENCE: self.view.quit() call completed",
                        extra={"class_name": self.__class__.__name__},
                    )
            elif hasattr(self, "view") and self.view and hasattr(self.view, "app") and self.view.app:
                logger.warning(
                    "⚠️ QUIT SEQUENCE: Using app.quit() fallback - this should not happen",
                    extra={"class_name": self.__class__.__name__},
                )
                # Even in fallback, try to use the proper shutdown if available
                if hasattr(self.view, "quit"):
                    logger.debug(
                        "🔄 QUIT SEQUENCE: Found view.quit() method, using proper shutdown in fallback",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.view.quit(fast_shutdown=True)
                else:
                    logger.error(
                        "❌ QUIT SEQUENCE: No proper shutdown available, using immediate quit as last resort",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.view.app.quit()  # Last resort only
            else:
                logger.error(
                    "❌ QUIT SEQUENCE: No view or app found - cannot quit!",
                    extra={"class_name": self.__class__.__name__},
                )
