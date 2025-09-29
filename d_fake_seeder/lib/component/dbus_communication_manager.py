"""
D-Bus Communication Manager

Pure D-Bus communication class with singleton and publish/subscribe patterns.
Provides a central hub for D-Bus IPC with observer pattern support.
Any application component can subscribe to events and publish messages.
"""

import threading
from enum import Enum
from typing import Callable, Dict, List, Optional

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from lib.logger import logger


class DBusEvent(Enum):
    """Enumeration of available D-Bus events for type safety."""

    SHOW_WINDOW = "show_window"
    QUIT_APPLICATION = "quit_application"
    STATUS_CHANGED = "status_changed"
    TORRENT_COUNT_CHANGED = "torrent_count_changed"
    APPLICATION_CLOSING = "application_closing"
    PING = "ping"


class DBusCommunicationManager:
    """
    Pure D-Bus communication manager with singleton pattern.

    Provides clean D-Bus IPC functionality with observer pattern support
    through callback registration. No UI or framework dependencies.
    """

    _instance: Optional["DBusCommunicationManager"] = None
    _lock = threading.Lock()

    # D-Bus configuration
    SERVICE_NAME = "ie.fio.dfakeseeder"
    OBJECT_PATH = "/ie/fio/dfakeseeder/tray"
    INTERFACE_NAME = "ie.fio.dfakeseeder.Tray"

    def __init__(self):
        """Initialize D-Bus communication manager (private - use get_instance())."""
        self.dbus_server: Optional["DBusServer"] = None
        self.is_active = False

        # Publish/Subscribe system
        self._subscribers: Dict[DBusEvent, List[Callable]] = {event: [] for event in DBusEvent}
        self._publisher_lock = threading.Lock()

        # Initialize D-Bus main loop if not already done
        self._ensure_dbus_mainloop()

        logger.info(
            "D-Bus communication manager initialized with pub/sub pattern",
            extra={"class_name": self.__class__.__name__},
        )

        # Auto-start server
        self._auto_start_server()

    @classmethod
    def get_instance(cls) -> "DBusCommunicationManager":
        """
        Get singleton instance of D-Bus communication manager.

        Returns:
            DBusCommunicationManager: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.debug("D-Bus communication manager singleton created", extra={"class_name": cls.__name__})
        return cls._instance

    def _ensure_dbus_mainloop(self):
        """Ensure D-Bus main loop is initialized."""
        try:
            DBusGMainLoop(set_as_default=True)
            logger.debug("D-Bus main loop initialized", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.warning(f"D-Bus main loop initialization failed: {e}", extra={"class_name": self.__class__.__name__})

    def start_server(self) -> bool:
        """
        Start D-Bus server for incoming connections.

        Returns:
            bool: True if server started successfully, False otherwise
        """
        logger.info("Starting D-Bus server", extra={"class_name": self.__class__.__name__})

        try:
            # Create D-Bus server
            self.dbus_server = DBusServer(self.SERVICE_NAME, self.OBJECT_PATH, self.INTERFACE_NAME, self)

            self.is_active = True
            logger.info("D-Bus server started successfully", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to start D-Bus server: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            return False

    def stop_server(self):
        """Stop D-Bus server."""
        logger.info("Stopping D-Bus server", extra={"class_name": self.__class__.__name__})

        try:
            if self.dbus_server:
                self.dbus_server.notify_application_closing()
                self.dbus_server.cleanup()
                self.dbus_server = None

            self.is_active = False
            logger.info("D-Bus server stopped", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error stopping D-Bus server: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def is_server_active(self) -> bool:
        """
        Check if D-Bus server is active.

        Returns:
            bool: True if server is active, False otherwise
        """
        return self.is_active and self.dbus_server is not None

    def _auto_start_server(self):
        """Auto-start D-Bus server."""
        try:
            # Start D-Bus server
            if self.start_server():
                logger.info("D-Bus server auto-started successfully", extra={"class_name": self.__class__.__name__})
            else:
                logger.warning("D-Bus server auto-start failed", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error in auto-start server: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def subscribe(self, event: DBusEvent, subscriber: Callable, subscriber_name: str = None):
        """
        Subscribe to a D-Bus event (Publisher/Subscriber pattern).

        Args:
            event: D-Bus event to subscribe to
            subscriber: Function to call when event occurs
            subscriber_name: Optional name for logging (defaults to function name)
        """
        with self._publisher_lock:
            if event not in self._subscribers:
                self._subscribers[event] = []

            self._subscribers[event].append(subscriber)

            name = subscriber_name or getattr(subscriber, "__name__", "unknown")
            logger.debug(
                f"Subscriber '{name}' subscribed to event: {event.value}", extra={"class_name": self.__class__.__name__}
            )

    def unsubscribe(self, event: DBusEvent, subscriber: Callable):
        """
        Unsubscribe from a D-Bus event.

        Args:
            event: D-Bus event to unsubscribe from
            subscriber: Function to remove from subscribers
        """
        with self._publisher_lock:
            if event in self._subscribers and subscriber in self._subscribers[event]:
                self._subscribers[event].remove(subscriber)
                name = getattr(subscriber, "__name__", "unknown")
                logger.debug(
                    f"Subscriber '{name}' unsubscribed from event: {event.value}",
                    extra={"class_name": self.__class__.__name__},
                )

    def publish(self, event: DBusEvent, *args, **kwargs):
        """
        Publish a D-Bus event to all subscribers.

        Args:
            event: D-Bus event to publish
            *args: Arguments to pass to subscribers
            **kwargs: Keyword arguments to pass to subscribers
        """
        with self._publisher_lock:
            if event in self._subscribers:
                subscriber_count = len(self._subscribers[event])
                logger.debug(
                    f"Publishing event {event.value} to {subscriber_count} subscribers",
                    extra={"class_name": self.__class__.__name__},
                )

                for subscriber in self._subscribers[event]:
                    try:
                        subscriber(*args, **kwargs)
                    except Exception as e:
                        name = getattr(subscriber, "__name__", "unknown")
                        logger.error(
                            f"Error in subscriber '{name}' for {event.value}: {e}",
                            extra={"class_name": self.__class__.__name__},
                            exc_info=True,
                        )
            else:
                logger.debug(f"No subscribers for event: {event.value}", extra={"class_name": self.__class__.__name__})

    def broadcast_signal(self, signal_name: str, *args):
        """
        Broadcast a D-Bus signal to all connected clients.

        Args:
            signal_name: Name of the signal to broadcast
            *args: Arguments to include in the signal
        """
        if self.is_server_active():
            try:
                getattr(self.dbus_server, signal_name)(*args)
                logger.debug(
                    f"Signal broadcasted: {signal_name} with args: {args}",
                    extra={"class_name": self.__class__.__name__},
                )
            except AttributeError:
                logger.warning(f"Signal method not found: {signal_name}", extra={"class_name": self.__class__.__name__})
            except Exception as e:
                logger.error(
                    f"Error broadcasting signal {signal_name}: {e}",
                    extra={"class_name": self.__class__.__name__},
                    exc_info=True,
                )

    def get_current_status(self) -> str:
        """
        Get current application status for D-Bus clients.

        Returns:
            str: Current status text
        """
        return "Running" if self.is_active else "Inactive"

    # Publisher methods for application components to send messages via D-Bus

    def publish_status_update(self, status_text: str):
        """
        Publish a status update message.

        Args:
            status_text: New status text to broadcast
        """
        self.publish(DBusEvent.STATUS_CHANGED, status_text)
        self.broadcast_signal("status_changed", status_text)
        logger.debug(f"Published status update: {status_text}", extra={"class_name": self.__class__.__name__})

    def publish_torrent_count_update(self, active_count: int, total_count: int):
        """
        Publish a torrent count update message.

        Args:
            active_count: Number of active torrents
            total_count: Total number of torrents
        """
        self.publish(DBusEvent.TORRENT_COUNT_CHANGED, active_count, total_count)
        self.broadcast_signal("torrent_count_changed", active_count, total_count)
        logger.debug(
            f"Published torrent count update: {active_count}/{total_count}",
            extra={"class_name": self.__class__.__name__},
        )

    def publish_application_closing(self):
        """Publish application closing notification."""
        self.publish(DBusEvent.APPLICATION_CLOSING)
        self.broadcast_signal("application_closing")
        logger.debug("Published application closing notification", extra={"class_name": self.__class__.__name__})

    def get_subscriber_count(self, event: DBusEvent) -> int:
        """
        Get the number of subscribers for a specific event.

        Args:
            event: D-Bus event to check

        Returns:
            int: Number of subscribers
        """
        return len(self._subscribers.get(event, []))


class DBusServer(dbus.service.Object):
    """
    D-Bus server implementation for handling incoming connections.

    Pure D-Bus server without GLib main loop integration.
    """

    def __init__(self, service_name: str, object_path: str, interface_name: str, manager: DBusCommunicationManager):
        """
        Initialize D-Bus server.

        Args:
            service_name: D-Bus service name
            object_path: D-Bus object path
            interface_name: D-Bus interface name
            manager: Reference to communication manager
        """
        self.service_name = service_name
        self.object_path = object_path
        self.interface_name = interface_name
        self.manager = manager

        try:
            # Create service on session bus
            self.bus = dbus.SessionBus()
            self.bus_name = dbus.service.BusName(service_name, self.bus)

            # Initialize the service object
            super().__init__(self.bus_name, object_path)

            logger.info(
                f"D-Bus server initialized: {service_name} at {object_path}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize D-Bus server: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            raise

    @dbus.service.method("ie.fio.dfakeseeder.Tray", in_signature="", out_signature="")
    def show_window(self):
        """D-Bus method to show the main window."""
        logger.debug("D-Bus show_window method called", extra={"class_name": self.__class__.__name__})
        self.manager.publish(DBusEvent.SHOW_WINDOW)

    @dbus.service.method("ie.fio.dfakeseeder.Tray", in_signature="", out_signature="")
    def quit_application(self):
        """D-Bus method to quit the application."""
        logger.debug("D-Bus quit_application method called", extra={"class_name": self.__class__.__name__})
        self.manager.publish(DBusEvent.QUIT_APPLICATION)

    @dbus.service.method("ie.fio.dfakeseeder.Tray", in_signature="", out_signature="s")
    def get_status(self):
        """D-Bus method to get current status."""
        logger.debug("D-Bus get_status method called", extra={"class_name": self.__class__.__name__})
        return self.manager.get_current_status()

    @dbus.service.method("ie.fio.dfakeseeder.Tray", in_signature="", out_signature="")
    def ping(self):
        """D-Bus method for testing connectivity."""
        logger.debug("D-Bus ping method called", extra={"class_name": self.__class__.__name__})
        self.manager.publish(DBusEvent.PING)

    @dbus.service.signal("ie.fio.dfakeseeder.Tray", signature="s")
    def status_changed(self, status):
        """D-Bus signal emitted when status changes."""
        logger.debug(f"D-Bus status_changed signal emitted: {status}", extra={"class_name": self.__class__.__name__})

    @dbus.service.signal("ie.fio.dfakeseeder.Tray", signature="ii")
    def torrent_count_changed(self, active_count, total_count):
        """D-Bus signal emitted when torrent count changes."""
        logger.debug(
            f"D-Bus torrent_count_changed signal emitted: {active_count}/{total_count}",
            extra={"class_name": self.__class__.__name__},
        )

    @dbus.service.signal("ie.fio.dfakeseeder.Tray", signature="")
    def application_closing(self):
        """D-Bus signal emitted when application is closing."""
        logger.debug("D-Bus application_closing signal emitted", extra={"class_name": self.__class__.__name__})

    def notify_application_closing(self):
        """Notify clients that application is closing."""
        try:
            self.application_closing()
            logger.debug(
                "Application closing notification sent via D-Bus", extra={"class_name": self.__class__.__name__}
            )
        except Exception as e:
            logger.error(
                f"Error notifying application closing: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def cleanup(self):
        """Clean up D-Bus server resources."""
        try:
            if hasattr(self, "bus_name"):
                del self.bus_name
            logger.info("D-Bus server cleaned up", extra={"class_name": self.__class__.__name__})
        except Exception as e:
            logger.error(
                f"Error during D-Bus server cleanup: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
