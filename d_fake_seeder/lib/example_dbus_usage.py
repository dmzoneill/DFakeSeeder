"""
Example usage of D-Bus Communication Manager

This demonstrates how different parts of the application can subscribe to
D-Bus events and publish messages using the singleton pub/sub pattern.
"""

from lib.component.dbus_communication_manager import DBusCommunicationManager, DBusEvent
from lib.logger import logger


class ExampleTorrentManager:
    """Example class showing how torrent manager can use D-Bus communication."""

    def __init__(self):
        # Get singleton instance of D-Bus manager
        self.dbus_manager = DBusCommunicationManager.get_instance()

        # Subscribe to events this component cares about
        self.dbus_manager.subscribe(DBusEvent.STATUS_CHANGED, self.handle_status_change, "TorrentManager")
        self.dbus_manager.subscribe(DBusEvent.APPLICATION_CLOSING, self.handle_app_closing, "TorrentManager")

        logger.info("TorrentManager subscribed to D-Bus events", extra={"class_name": self.__class__.__name__})

    def handle_status_change(self, status_text: str):
        """Handle status change events from other components."""
        logger.info(
            f"TorrentManager received status change: {status_text}", extra={"class_name": self.__class__.__name__}
        )

    def handle_app_closing(self):
        """Handle application closing event."""
        logger.info("TorrentManager received app closing notification", extra={"class_name": self.__class__.__name__})
        # Cleanup torrent operations
        self.cleanup_torrents()

    def update_torrent_count(self, active: int, total: int):
        """Publish torrent count update to all subscribers."""
        self.dbus_manager.publish_torrent_count_update(active, total)
        logger.info(
            f"TorrentManager published torrent count: {active}/{total}", extra={"class_name": self.__class__.__name__}
        )

    def cleanup_torrents(self):
        """Example cleanup method."""
        logger.info("Cleaning up torrents...", extra={"class_name": self.__class__.__name__})


class ExampleStatusManager:
    """Example class showing how status manager can use D-Bus communication."""

    def __init__(self):
        # Get singleton instance of D-Bus manager
        self.dbus_manager = DBusCommunicationManager.get_instance()

        # Subscribe to torrent count changes
        self.dbus_manager.subscribe(DBusEvent.TORRENT_COUNT_CHANGED, self.handle_torrent_count_change, "StatusManager")

        logger.info("StatusManager subscribed to D-Bus events", extra={"class_name": self.__class__.__name__})

    def handle_torrent_count_change(self, active_count: int, total_count: int):
        """Handle torrent count changes from other components."""
        logger.info(
            f"StatusManager received torrent count update: {active_count}/{total_count}",
            extra={"class_name": self.__class__.__name__},
        )
        # Update status display
        self.update_status_display(active_count, total_count)

    def update_status_display(self, active: int, total: int):
        """Update status display and broadcast to other components."""
        status_text = f"Active: {active}, Total: {total} torrents"
        self.dbus_manager.publish_status_update(status_text)
        logger.info(f"StatusManager published status: {status_text}", extra={"class_name": self.__class__.__name__})


class ExamplePeerManager:
    """Example class showing how peer manager can use D-Bus communication."""

    def __init__(self):
        # Get singleton instance of D-Bus manager
        self.dbus_manager = DBusCommunicationManager.get_instance()

        # Subscribe to application closing to cleanup connections
        self.dbus_manager.subscribe(DBusEvent.APPLICATION_CLOSING, self.handle_app_closing, "PeerManager")

        logger.info("PeerManager subscribed to D-Bus events", extra={"class_name": self.__class__.__name__})

    def handle_app_closing(self):
        """Handle application closing event."""
        logger.info("PeerManager received app closing notification", extra={"class_name": self.__class__.__name__})
        # Close all peer connections
        self.close_all_connections()

    def close_all_connections(self):
        """Example connection cleanup method."""
        logger.info("Closing all peer connections...", extra={"class_name": self.__class__.__name__})


def example_usage():
    """Example showing how to use the D-Bus manager pub/sub system."""

    # Create example components
    torrent_manager = ExampleTorrentManager()
    status_manager = ExampleStatusManager()  # noqa: F841
    peer_manager = ExamplePeerManager()  # noqa: F841

    # Example: TorrentManager updates count, StatusManager receives it and updates status
    torrent_manager.update_torrent_count(5, 10)

    # Example: Simulate application closing
    dbus_manager = DBusCommunicationManager.get_instance()
    dbus_manager.publish_application_closing()

    # Check subscriber counts
    show_window_subscribers = dbus_manager.get_subscriber_count(DBusEvent.SHOW_WINDOW)
    status_subscribers = dbus_manager.get_subscriber_count(DBusEvent.STATUS_CHANGED)

    logger.info(f"Subscriber counts - SHOW_WINDOW: {show_window_subscribers}, STATUS_CHANGED: {status_subscribers}")


if __name__ == "__main__":
    example_usage()
