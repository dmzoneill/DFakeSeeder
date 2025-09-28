import os

from domain.app_settings import AppSettings
from domain.torrent.global_peer_manager import GlobalPeerManager

# from domain.torrent.listener import Listener
from lib.logger import logger


# Cont roller
class Controller:
    def __init__(self, view, model):
        logger.info("Controller Startup", extra={"class_name": self.__class__.__name__})
        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.view = view
        self.model = model

        # Initialize global peer manager
        self.global_peer_manager = GlobalPeerManager()

        # self.listener = Listener(self.model)
        # self.listener.start()
        self.view.set_model(self.model)
        # Make global peer manager accessible to view components
        self.view.global_peer_manager = self.global_peer_manager
        self.view.statusbar.global_peer_manager = self.global_peer_manager
        self.view.notebook.global_peer_manager = self.global_peer_manager

        # Set up connection callback for UI updates
        self.global_peer_manager.set_connection_callback(self.view.handle_peer_connection_event)

        # Start global peer manager after setting up callbacks
        self.global_peer_manager.start()

        self.view.connect_signals()

    def run(self):
        logger.info("Controller Run", extra={"class_name": self.__class__.__name__})
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

    def stop(self, shutdown_tracker=None):
        """Stop the controller and cleanup all background processes"""
        logger.info("Controller stopping", extra={"class_name": self.__class__.__name__})

        # Stop global peer manager
        if hasattr(self, "global_peer_manager") and self.global_peer_manager:
            self.global_peer_manager.stop(shutdown_tracker=shutdown_tracker)
        else:
            # Mark components as completed if no global peer manager
            if shutdown_tracker:
                shutdown_tracker.mark_completed("peer_managers", 0)
                shutdown_tracker.mark_completed("background_workers", 0)
                shutdown_tracker.mark_completed("network_connections", 0)

        logger.info("Controller stopped", extra={"class_name": self.__class__.__name__})

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Controller settings changed",
            extra={"class_name": self.__class__.__name__},
        )
