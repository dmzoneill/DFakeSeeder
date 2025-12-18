# fmt: off
import asyncio
import os
from typing import Any, Optional

from gi.repository import GLib

from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.dht_manager import DHTManager
from d_fake_seeder.domain.torrent.global_peer_manager import GlobalPeerManager
from d_fake_seeder.lib.handlers.torrent_folder_watcher import TorrentFolderWatcher

# from domain.torrent.listener import Listener
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.autostart_manager import sync_autostart
from d_fake_seeder.lib.util.client_behavior_simulator import ClientBehaviorSimulator
from d_fake_seeder.lib.util.dbus_unifier import DBusUnifier
from d_fake_seeder.lib.util.speed_distribution_manager import SpeedDistributionManager
from d_fake_seeder.lib.util.speed_scheduler import SpeedScheduler
from d_fake_seeder.lib.util.upnp_manager import UPnPManager
from d_fake_seeder.lib.util.window_manager import WindowManager

# Optional imports for features that may not be available
try:
    from d_fake_seeder.webui import WebUIServer
    WEBUI_AVAILABLE = True
except ImportError:
    WEBUI_AVAILABLE = False
    WebUIServer = None  # type: ignore[assignment, misc]

try:
    from d_fake_seeder.domain.torrent.protocols.lpd import LocalPeerDiscovery
    LPD_AVAILABLE = True
except ImportError:
    LPD_AVAILABLE = False
    LocalPeerDiscovery = None  # type: ignore[assignment, misc]

# fmt: on


# Cont roller
class Controller:
    def __init__(self, view: Any, model: Any) -> None:
        logger.trace("Startup", extra={"class_name": self.__class__.__name__})
        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.view = view
        self.model = model

        # Initialize global peer manager
        self.global_peer_manager = GlobalPeerManager()

        # Initialize DHT manager
        dht_enabled = self.settings.get("protocols.dht.enabled", False)
        self.dht_manager = None
        if dht_enabled:
            dht_port = self.settings.get("connection.listening_port", 6881)
            self.dht_manager = DHTManager(port=dht_port)

        # Initialize speed distribution manager
        self.speed_distribution_manager = SpeedDistributionManager(model)

        # Initialize client behavior simulator
        behavior_profile = self.settings.get("simulation.client_behavior_engine.primary_client", "balanced")
        self.client_behavior_simulator = ClientBehaviorSimulator(behavior_profile)

        # Tick timer for speed distribution and behavior simulation
        self.tick_timer_id = None

        # Initialize speed scheduler for automatic alternative speed switching
        self.speed_scheduler = SpeedScheduler()

        # Initialize UPnP manager for port forwarding
        self.upnp_manager = UPnPManager()

        # Initialize Web UI server (if available)
        self.webui_server: Optional[Any] = None
        if WEBUI_AVAILABLE and WebUIServer is not None:
            self.webui_server = WebUIServer(model)

        # Initialize Local Peer Discovery (if available)
        self.lpd_manager: Optional[Any] = None
        if LPD_AVAILABLE and LocalPeerDiscovery is not None:
            port = self.settings.get("connection.listening_port", 6881)
            self.lpd_manager = LocalPeerDiscovery(port, self._on_lpd_peer_discovered)

        # Initialize window manager with main window
        self.window_manager = None  # Will be set after view initialization

        # Initialize torrent folder watcher (pass global_peer_manager for P2P integration)
        self.torrent_watcher = TorrentFolderWatcher(model, self.settings, self.global_peer_manager)

        # Initialize D-Bus service for tray communication
        self.dbus = None
        try:
            self.dbus = DBusUnifier()
            logger.trace(
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
            logger.trace(
                "Window manager initialized",
                extra={"class_name": self.__class__.__name__},
            )

        # Make managers accessible to view components and model
        self.view.global_peer_manager = self.global_peer_manager
        self.view.statusbar.global_peer_manager = self.global_peer_manager
        self.view.notebook.global_peer_manager = self.global_peer_manager
        self.model.speed_distribution_manager = self.speed_distribution_manager
        if self.window_manager:
            self.view.window_manager = self.window_manager

        # Set up connection callback for UI updates
        self.global_peer_manager.set_connection_callback(self.view.handle_peer_connection_event)

        # Start global peer manager after setting up callbacks
        self.global_peer_manager.start()

        # Start DHT manager if enabled
        if self.dht_manager:
            self.dht_manager.start()
            logger.info("DHT Manager started", "Controller")

        # Start speed distribution manager
        self.speed_distribution_manager.start()

        # Start tick timer for speed redistribution
        tick_speed = getattr(self.settings, "tickspeed", 9)
        self.tick_timer_id = GLib.timeout_add_seconds(tick_speed, self._on_tick)
        logger.debug(f"Tick timer started ({tick_speed} seconds)", "Controller")

        # Setup D-Bus signal forwarding after all components are initialized
        if self.dbus:
            self.dbus.setup_settings_signal_forwarding()
            logger.trace(
                "D-Bus settings signal forwarding enabled",
                extra={"class_name": self.__class__.__name__},
            )

        self.view.connect_signals()

    def run(self) -> Any:
        logger.trace("Controller Run", extra={"class_name": self.__class__.__name__})
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

            # Register torrent with DHT if enabled
            if self.dht_manager and hasattr(torrent, "torrent_file") and hasattr(torrent.torrent_file, "info_hash"):
                self.dht_manager.register_torrent(torrent.torrent_file.info_hash, torrent)

        # Start watching folder for new torrents
        self.torrent_watcher.start()

        # Sync autostart state with current setting
        auto_start_enabled = getattr(self.settings, "auto_start", False)
        sync_autostart(auto_start_enabled)

        # Start speed scheduler for automatic alternative speed switching
        if hasattr(self, "speed_scheduler") and self.speed_scheduler:
            self.speed_scheduler.start()
            logger.info("Speed scheduler started", "Controller")

        # Start UPnP port forwarding
        if hasattr(self, "upnp_manager") and self.upnp_manager:
            if self.upnp_manager.start():
                logger.info("UPnP port forwarding enabled", "Controller")
            else:
                logger.debug("UPnP port forwarding not available", "Controller")

        # Start Web UI server (async)
        if hasattr(self, "webui_server") and self.webui_server:
            self._start_webui_async()

        # Start Local Peer Discovery (async)
        if hasattr(self, "lpd_manager") and self.lpd_manager:
            self._start_lpd_async()

    def stop(self, shutdown_tracker: Any = None) -> Any:
        """Stop the controller and cleanup all background processes"""
        logger.trace("Controller stopping", extra={"class_name": self.__class__.__name__})

        # Stop tick timer
        if hasattr(self, "tick_timer_id") and self.tick_timer_id:
            GLib.source_remove(self.tick_timer_id)
            self.tick_timer_id = None

        # Stop speed scheduler
        if hasattr(self, "speed_scheduler") and self.speed_scheduler:
            self.speed_scheduler.stop()
            logger.trace("Speed scheduler stopped", extra={"class_name": self.__class__.__name__})

        # Stop Web UI server (async)
        if hasattr(self, "webui_server") and self.webui_server:
            self._stop_webui_async()
            logger.trace("Web UI server stopped", extra={"class_name": self.__class__.__name__})

        # Stop Local Peer Discovery (async)
        if hasattr(self, "lpd_manager") and self.lpd_manager:
            self._stop_lpd_async()
            logger.trace("Local Peer Discovery stopped", extra={"class_name": self.__class__.__name__})

        # Stop UPnP port forwarding
        if hasattr(self, "upnp_manager") and self.upnp_manager:
            self.upnp_manager.stop()
            logger.trace("UPnP port forwarding stopped", extra={"class_name": self.__class__.__name__})

        # Stop speed distribution manager
        if hasattr(self, "speed_distribution_manager") and self.speed_distribution_manager:
            self.speed_distribution_manager.stop()

        # Stop DHT manager (before peer manager to cleanly unregister torrents)
        if hasattr(self, "dht_manager") and self.dht_manager:
            logger.trace("Stopping DHT Manager", extra={"class_name": self.__class__.__name__})
            self.dht_manager.stop()

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

        logger.trace(
            "🔧 About to cleanup window manager",
            extra={"class_name": self.__class__.__name__},
        )
        # Cleanup window manager
        if hasattr(self, "window_manager") and self.window_manager:
            self.window_manager.cleanup()
        logger.trace(
            "✅ Window manager cleanup complete",
            extra={"class_name": self.__class__.__name__},
        )

        logger.trace("🔧 About to cleanup D-Bus", extra={"class_name": self.__class__.__name__})
        # Cleanup D-Bus service
        if hasattr(self, "dbus") and self.dbus:
            self.dbus.cleanup()
        logger.trace("✅ D-Bus cleanup complete", extra={"class_name": self.__class__.__name__})

        logger.info("Controller stopped", extra={"class_name": self.__class__.__name__})

    def _on_tick(self) -> bool:
        """Tick callback for speed redistribution, behavior simulation, and torrent state persistence."""
        try:
            if self.speed_distribution_manager:
                self.speed_distribution_manager.check_redistribution("tick")

            # Run client behavior simulation
            if hasattr(self, "client_behavior_simulator") and self.client_behavior_simulator:
                if hasattr(self, "model") and self.model:
                    torrents = self.model.get_torrents()
                    self.client_behavior_simulator.simulate_tick(torrents)

            # Save all torrent states to transient storage (in-memory only)
            # This ensures torrent progress is always up-to-date when save_quit() is called
            if hasattr(self, "model") and self.model:
                for torrent in self.model.get_torrents():
                    try:
                        torrent.save_to_transient()
                    except Exception as e:
                        logger.error(
                            f"Error saving torrent {getattr(torrent, 'name', 'unknown')} to transient: {e}",
                            "Controller",
                            exc_info=True,
                        )
        except Exception as e:
            logger.error(f"Error in tick callback: {e}", "Controller", exc_info=True)
        return True  # Keep timer running

    def handle_settings_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace(
            f"Controller settings changed: {key} = {value}",
            extra={"class_name": self.__class__.__name__},
        )

        # Handle auto_start setting change
        if key == "auto_start":
            sync_autostart(value)

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

        # Handle scheduler settings changes
        if key.startswith("scheduler."):
            if hasattr(self, "speed_scheduler") and self.speed_scheduler:
                self.speed_scheduler.force_check()

        # Handle UPnP settings changes
        if key == "connection.upnp_enabled":
            if hasattr(self, "upnp_manager") and self.upnp_manager:
                if value:
                    self.upnp_manager.start()
                else:
                    self.upnp_manager.stop()

        # Handle Web UI settings changes
        if key == "webui.enabled":
            if hasattr(self, "webui_server") and self.webui_server:
                if value:
                    self._start_webui_async()
                else:
                    self._stop_webui_async()

        # Handle LPD settings changes
        if key == "bittorrent.enable_lpd":
            if hasattr(self, "lpd_manager") and self.lpd_manager:
                if value:
                    self._start_lpd_async()
                else:
                    self._stop_lpd_async()

        # Sync bittorrent.enable_dht to protocols.dht.enabled (they control the same feature)
        if key == "bittorrent.enable_dht":
            # Sync to the protocol-level setting
            current_protocol = self.settings.get("protocols.dht.enabled", True)
            if current_protocol != value:
                self.settings.set("protocols.dht.enabled", value)
            # Also restart/stop DHT manager
            if hasattr(self, "dht_manager"):
                if value and not self.dht_manager:
                    dht_port = self.settings.get("connection.listening_port", 6881)
                    from d_fake_seeder.domain.torrent.dht_manager import DHTManager

                    self.dht_manager = DHTManager(port=dht_port)
                    self.dht_manager.start()
                    logger.info("DHT Manager started", "Controller")
                elif not value and self.dht_manager:
                    self.dht_manager.stop()
                    self.dht_manager = None
                    logger.info("DHT Manager stopped", "Controller")

        # Sync protocols.dht.enabled back to bittorrent.enable_dht
        if key == "protocols.dht.enabled":
            current_bt = self.settings.get("bittorrent.enable_dht", True)
            if current_bt != value:
                self.settings.set("bittorrent.enable_dht", value)

        # Sync bittorrent.enable_pex to protocols.extensions.ut_pex
        if key == "bittorrent.enable_pex":
            current_protocol = self.settings.get("protocols.extensions.ut_pex", True)
            if current_protocol != value:
                self.settings.set("protocols.extensions.ut_pex", value)

        # Sync protocols.extensions.ut_pex back to bittorrent.enable_pex
        if key == "protocols.extensions.ut_pex":
            current_bt = self.settings.get("bittorrent.enable_pex", True)
            if current_bt != value:
                self.settings.set("bittorrent.enable_pex", value)

        # Handle debug mode - switch logging to DEBUG level
        if key == "expert.debug_mode":
            from d_fake_seeder.lib.logger import reconfigure_logger

            if value:
                # Set logging level to DEBUG when debug mode enabled
                self.settings.set("logging.level", "DEBUG")
            else:
                # Restore to INFO when debug mode disabled
                self.settings.set("logging.level", "INFO")
            reconfigure_logger()
            logger.info(f"Debug mode {'enabled' if value else 'disabled'}, logging level changed")

        # Handle logging level changes
        if key == "logging.level":
            from d_fake_seeder.lib.logger import reconfigure_logger

            reconfigure_logger()
            logger.info(f"Logging level changed to {value}")

        # Handle application quit request
        if key == "application_quit_requested" and value:
            logger.trace(
                "🚨 QUIT SEQUENCE START: Quit requested via D-Bus settings",
                extra={"class_name": self.__class__.__name__},
            )
            # Don't reset the flag here - it will be reset when settings are saved during quit
            # Resetting it here can cause signal loops

            # Trigger proper application shutdown (not immediate quit)
            if hasattr(self, "view") and self.view:
                logger.trace(
                    "✅ QUIT SEQUENCE: Found view object, triggering proper shutdown sequence",
                    extra={"class_name": self.__class__.__name__},
                )
                if hasattr(self.view, "on_quit_clicked"):
                    logger.trace(
                        "🎯 QUIT SEQUENCE: Calling self.view.on_quit_clicked() with fast_shutdown=True for D-Bus quit",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.view.on_quit_clicked(None, fast_shutdown=True)  # Use fast shutdown for D-Bus triggered quit
                    logger.trace(
                        "📞 QUIT SEQUENCE: self.view.on_quit_clicked() call completed",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    logger.trace(
                        "🎯 QUIT SEQUENCE: Calling self.view.quit() with fast_shutdown=True "
                        "for ShutdownProgressTracker shutdown",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.view.quit(fast_shutdown=True)  # Fallback to direct quit with fast shutdown
                    logger.trace(
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
                    logger.trace(
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

    # Helper methods for async feature management

    def _start_webui_async(self) -> None:
        """Start Web UI server asynchronously."""
        server = self.webui_server
        if not server:
            return

        async def _start() -> None:
            try:
                if await server.start():
                    logger.info("Web UI server started", "Controller")
            except Exception as e:
                logger.error(f"Failed to start Web UI: {e}", "Controller")

        # Run in existing event loop or create new one
        try:
            asyncio.get_running_loop()
            asyncio.create_task(_start())
        except RuntimeError:
            # No running loop - use GLib to schedule
            GLib.idle_add(lambda: asyncio.run(_start()) or False)

    def _stop_webui_async(self) -> None:
        """Stop Web UI server asynchronously."""
        server = self.webui_server
        if not server:
            return

        async def _stop() -> None:
            try:
                await server.stop()
            except Exception as e:
                logger.error(f"Error stopping Web UI: {e}", "Controller")

        try:
            asyncio.get_running_loop()
            asyncio.create_task(_stop())
        except RuntimeError:
            GLib.idle_add(lambda: asyncio.run(_stop()) or False)

    def _start_lpd_async(self) -> None:
        """Start Local Peer Discovery asynchronously."""
        lpd = self.lpd_manager
        if not lpd:
            return

        async def _start() -> None:
            try:
                if await lpd.start():
                    logger.info("Local Peer Discovery started", "Controller")
            except Exception as e:
                logger.error(f"Failed to start LPD: {e}", "Controller")

        try:
            asyncio.get_running_loop()
            asyncio.create_task(_start())
        except RuntimeError:
            GLib.idle_add(lambda: asyncio.run(_start()) or False)

    def _stop_lpd_async(self) -> None:
        """Stop Local Peer Discovery asynchronously."""
        lpd = self.lpd_manager
        if not lpd:
            return

        async def _stop() -> None:
            try:
                await lpd.stop()
            except Exception as e:
                logger.error(f"Error stopping LPD: {e}", "Controller")

        try:
            asyncio.get_running_loop()
            asyncio.create_task(_stop())
        except RuntimeError:
            GLib.idle_add(lambda: asyncio.run(_stop()) or False)

    def _on_lpd_peer_discovered(self, ip: str, port: int, info_hash: bytes) -> None:
        """Callback when a peer is discovered via LPD."""
        logger.debug(
            f"LPD peer discovered: {ip}:{port} for {info_hash.hex()[:16]}...",
            extra={"class_name": self.__class__.__name__},
        )

        # Add peer to the appropriate torrent's peer list
        if hasattr(self, "global_peer_manager") and self.global_peer_manager:
            # Find torrent with matching info_hash
            for torrent in self.model.get_torrents():
                if hasattr(torrent, "torrent_file") and hasattr(torrent.torrent_file, "info_hash"):
                    if torrent.torrent_file.info_hash == info_hash:
                        # Add peer to global peer manager for this torrent
                        try:
                            info_hash_hex = info_hash.hex()
                            if info_hash_hex in self.global_peer_manager.peer_managers:
                                manager = self.global_peer_manager.peer_managers[info_hash_hex]
                                manager.add_peers([f"{ip}:{port}"])
                                logger.trace(
                                    f"Added LPD peer {ip}:{port} to torrent {torrent.name}",
                                    extra={"class_name": self.__class__.__name__},
                                )
                        except Exception as e:
                            logger.warning(
                                f"Failed to add LPD peer: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                        break
