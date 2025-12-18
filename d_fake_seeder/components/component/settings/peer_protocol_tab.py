"""
Peer Protocol settings tab for the settings dialog.

Handles peer protocol timeouts, seeder settings, and peer behavior configuration.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")

from .base_tab import BaseSettingsTab  # noqa: E402
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import UtilityMixin, ValidationMixin  # noqa: E402

# fmt: on


class PeerProtocolTab(BaseSettingsTab, NotificationMixin, ValidationMixin, UtilityMixin):
    """
    Peer Protocol settings tab component.

    Manages:
    - Peer protocol timeout settings (handshake, message read, keep-alive)
    - Seeder protocol configuration (UDP/HTTP timeouts, ports)
    - Peer behavior settings (activity probabilities, distributions)
    """

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS = [
        # Peer Protocol Timeouts
        {
            "id": "settings_handshake_timeout",
            "name": "handshake_timeout",
            "setting_key": "peer_protocol.handshake_timeout_seconds",
            "type": float,
        },
        {
            "id": "settings_message_read_timeout",
            "name": "message_read_timeout",
            "setting_key": "peer_protocol.message_read_timeout_seconds",
            "type": float,
        },
        {
            "id": "settings_keep_alive_interval",
            "name": "keep_alive_interval",
            "setting_key": "peer_protocol.keep_alive_interval_seconds",
            "type": float,
        },
        {
            "id": "settings_peer_contact_interval",
            "name": "peer_contact_interval",
            "setting_key": "peer_protocol.contact_interval_seconds",
            "type": float,
        },
        # Seeder Protocol Settings
        {
            "id": "settings_udp_seeder_timeout",
            "name": "udp_seeder_timeout",
            "setting_key": "seeders.udp_timeout_seconds",
            "type": int,
        },
        {
            "id": "settings_http_seeder_timeout",
            "name": "http_seeder_timeout",
            "setting_key": "seeders.http_timeout_seconds",
            "type": int,
        },
        {
            "id": "settings_seeder_port_min",
            "name": "seeder_port_min",
            "setting_key": "seeders.port_range_min",
            "type": int,
        },
        {
            "id": "settings_seeder_port_max",
            "name": "seeder_port_max",
            "setting_key": "seeders.port_range_max",
            "type": int,
        },
        {
            "id": "settings_transaction_id_min",
            "name": "transaction_id_min",
            "setting_key": "seeders.transaction_id_min",
            "type": int,
        },
        {
            "id": "settings_transaction_id_max",
            "name": "transaction_id_max",
            "setting_key": "seeders.transaction_id_max",
            "type": int,
        },
        {
            "id": "settings_peer_request_count",
            "name": "peer_request_count",
            "setting_key": "seeders.peer_request_count",
            "type": int,
        },
        # Peer Behavior Settings
        {
            "id": "settings_seeder_upload_activity_probability",
            "name": "seeder_upload_activity",
            "setting_key": "peer_behavior.seeder_upload_activity_probability",
            "type": float,
        },
        {
            "id": "settings_peer_idle_chance",
            "name": "peer_idle_chance",
            "setting_key": "peer_behavior.peer_idle_chance",
            "type": float,
        },
        {
            "id": "settings_progress_distribution_start",
            "name": "progress_dist_start",
            "setting_key": "peer_behavior.progress_distribution_start",
            "type": float,
        },
        {
            "id": "settings_progress_distribution_middle",
            "name": "progress_dist_middle",
            "setting_key": "peer_behavior.progress_distribution_middle",
            "type": float,
        },
        {
            "id": "settings_progress_distribution_almost",
            "name": "progress_dist_almost",
            "setting_key": "peer_behavior.progress_distribution_almost_done",
            "type": float,
        },
        {
            "id": "settings_peer_behavior_analysis_probability",
            "name": "peer_behavior_analysis",
            "setting_key": "peer_behavior.peer_behavior_analysis_probability",
            "type": float,
        },
        {
            "id": "settings_peer_status_change_probability",
            "name": "peer_status_change",
            "setting_key": "peer_behavior.peer_status_change_probability",
            "type": float,
        },
        {
            "id": "settings_peer_dropout_probability",
            "name": "peer_dropout",
            "setting_key": "peer_behavior.peer_dropout_probability",
            "type": float,
        },
        {
            "id": "settings_connection_rotation_percentage",
            "name": "connection_rotation",
            "setting_key": "peer_behavior.connection_rotation_percentage",
            "type": float,
        },
    ]

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "Peer Protocol"

    def _init_widgets(self) -> None:
        """Initialize Peer Protocol tab widgets."""
        # Cache commonly used widgets
        self._widgets.update(
            {
                # Peer Protocol Timeouts
                "handshake_timeout": self.builder.get_object("settings_handshake_timeout"),
                "message_read_timeout": self.builder.get_object("settings_message_read_timeout"),
                "keep_alive_interval": self.builder.get_object("settings_keep_alive_interval"),
                "peer_contact_interval": self.builder.get_object("settings_peer_contact_interval"),
                # Seeder Protocol Settings
                "udp_seeder_timeout": self.builder.get_object("settings_udp_seeder_timeout"),
                "http_seeder_timeout": self.builder.get_object("settings_http_seeder_timeout"),
                "seeder_port_min": self.builder.get_object("settings_seeder_port_min"),
                "seeder_port_max": self.builder.get_object("settings_seeder_port_max"),
                "transaction_id_min": self.builder.get_object("settings_transaction_id_min"),
                "transaction_id_max": self.builder.get_object("settings_transaction_id_max"),
                "peer_request_count": self.builder.get_object("settings_peer_request_count"),
                # Peer Behavior Settings
                "seeder_upload_activity": self.builder.get_object("settings_seeder_upload_activity_probability"),
                "peer_idle_chance": self.builder.get_object("settings_peer_idle_chance"),
                "progress_dist_start": self.builder.get_object("settings_progress_distribution_start"),
                "progress_dist_middle": self.builder.get_object("settings_progress_distribution_middle"),
                "progress_dist_almost": self.builder.get_object("settings_progress_distribution_almost"),
                "peer_behavior_analysis": self.builder.get_object("settings_peer_behavior_analysis_probability"),
                "peer_status_change": self.builder.get_object("settings_peer_status_change_probability"),
                "peer_dropout": self.builder.get_object("settings_peer_dropout_probability"),
                "connection_rotation": self.builder.get_object("settings_connection_rotation_percentage"),
            }
        )

    def _connect_signals(self) -> None:
        """Connect signal handlers for Peer Protocol tab."""
        # All 20 widgets (peer protocol timeouts, seeder settings, peer behavior settings)
        # are now auto-connected via WIDGET_MAPPINGS - no manual signal connections needed

    def _load_settings(self) -> None:
        """Load current settings into Peer Protocol tab widgets."""
        try:
            # Load peer protocol settings from nested structure
            peer_protocol = self.app_settings.get("peer_protocol", {})
            if peer_protocol is None:
                peer_protocol = {}
            self._load_peer_protocol_settings(peer_protocol)

            # Load seeder settings from nested structure
            seeders = self.app_settings.get("seeders", {})
            if seeders is None:
                seeders = {}
            self._load_seeder_settings(seeders)

            # Load peer behavior settings from nested structure
            peer_behavior = self.app_settings.get("peer_behavior", {})
            if peer_behavior is None:
                peer_behavior = {}
            self._load_peer_behavior_settings(peer_behavior)

            self.logger.info("Peer Protocol tab settings loaded")

        except Exception as e:
            self.logger.error(f"Error loading Peer Protocol tab settings: {e}")

    def _load_peer_protocol_settings(self, peer_protocol: Dict[str, Any]) -> None:
        """Load peer protocol timeout settings."""
        try:
            handshake_timeout = self.get_widget("handshake_timeout")
            if handshake_timeout:
                handshake_timeout.set_value(peer_protocol.get("handshake_timeout_seconds", 30.0))

            message_read_timeout = self.get_widget("message_read_timeout")
            if message_read_timeout:
                message_read_timeout.set_value(peer_protocol.get("message_read_timeout_seconds", 60.0))

            keep_alive_interval = self.get_widget("keep_alive_interval")
            if keep_alive_interval:
                keep_alive_interval.set_value(peer_protocol.get("keep_alive_interval_seconds", 120.0))

            peer_contact_interval = self.get_widget("peer_contact_interval")
            if peer_contact_interval:
                peer_contact_interval.set_value(peer_protocol.get("contact_interval_seconds", 300.0))

        except Exception as e:
            self.logger.error(f"Error loading peer protocol settings: {e}")

    def _load_seeder_settings(self, seeders: Dict[str, Any]) -> None:
        """Load seeder protocol settings."""
        try:
            udp_seeder_timeout = self.get_widget("udp_seeder_timeout")
            if udp_seeder_timeout:
                udp_seeder_timeout.set_value(seeders.get("udp_timeout_seconds", 5))

            http_seeder_timeout = self.get_widget("http_seeder_timeout")
            if http_seeder_timeout:
                http_seeder_timeout.set_value(seeders.get("http_timeout_seconds", 10))

            seeder_port_min = self.get_widget("seeder_port_min")
            if seeder_port_min:
                seeder_port_min.set_value(seeders.get("port_range_min", 1025))

            seeder_port_max = self.get_widget("seeder_port_max")
            if seeder_port_max:
                seeder_port_max.set_value(seeders.get("port_range_max", 65000))

            transaction_id_min = self.get_widget("transaction_id_min")
            if transaction_id_min:
                transaction_id_min.set_value(seeders.get("transaction_id_min", 1))

            transaction_id_max = self.get_widget("transaction_id_max")
            if transaction_id_max:
                transaction_id_max.set_value(seeders.get("transaction_id_max", 2147483647))

            peer_request_count = self.get_widget("peer_request_count")
            if peer_request_count:
                peer_request_count.set_value(seeders.get("peer_request_count", 200))

        except Exception as e:
            self.logger.error(f"Error loading seeder settings: {e}")

    def _load_peer_behavior_settings(self, peer_behavior: Dict[str, Any]) -> None:
        """Load peer behavior settings."""
        try:
            seeder_upload_activity = self.get_widget("seeder_upload_activity")
            if seeder_upload_activity:
                seeder_upload_activity.set_value(peer_behavior.get("seeder_upload_activity_probability", 0.9))

            peer_idle_chance = self.get_widget("peer_idle_chance")
            if peer_idle_chance:
                peer_idle_chance.set_value(peer_behavior.get("peer_idle_chance", 0.1))

            progress_dist_start = self.get_widget("progress_dist_start")
            if progress_dist_start:
                progress_dist_start.set_value(peer_behavior.get("progress_distribution_start", 0.2))

            progress_dist_middle = self.get_widget("progress_dist_middle")
            if progress_dist_middle:
                progress_dist_middle.set_value(peer_behavior.get("progress_distribution_middle", 0.5))

            progress_dist_almost = self.get_widget("progress_dist_almost")
            if progress_dist_almost:
                progress_dist_almost.set_value(peer_behavior.get("progress_distribution_almost_done", 0.3))

            peer_behavior_analysis = self.get_widget("peer_behavior_analysis")
            if peer_behavior_analysis:
                peer_behavior_analysis.set_value(peer_behavior.get("peer_behavior_analysis_probability", 0.05))

            peer_status_change = self.get_widget("peer_status_change")
            if peer_status_change:
                peer_status_change.set_value(peer_behavior.get("peer_status_change_probability", 0.1))

            peer_dropout = self.get_widget("peer_dropout")
            if peer_dropout:
                peer_dropout.set_value(peer_behavior.get("peer_dropout_probability", 0.02))

            connection_rotation = self.get_widget("connection_rotation")
            if connection_rotation:
                connection_rotation.set_value(peer_behavior.get("connection_rotation_percentage", 0.1))

        except Exception as e:
            self.logger.error(f"Error loading peer behavior settings: {e}")

    def _setup_dependencies(self) -> None:
        """Set up dependencies for Peer Protocol tab."""
        pass

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from Peer Protocol tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        # Collect from WIDGET_MAPPINGS
        settings = self._collect_mapped_settings()

        # Collect peer protocol settings with proper key prefixes
        peer_protocol_settings = self._collect_peer_protocol_settings()
        for key, value in peer_protocol_settings.items():
            settings[f"peer_protocol.{key}"] = value

        # Collect seeder settings with proper key prefixes
        seeder_settings = self._collect_seeder_settings()
        for key, value in seeder_settings.items():
            settings[f"seeders.{key}"] = value

        # Collect peer behavior settings with proper key prefixes
        peer_behavior_settings = self._collect_peer_behavior_settings()
        for key, value in peer_behavior_settings.items():
            settings[f"peer_behavior.{key}"] = value

        self.logger.trace(f"Collected {len(settings)} settings from Peer Protocol tab")
        return settings

    def _collect_peer_protocol_settings(self) -> Dict[str, Any]:
        """Collect peer protocol timeout settings."""
        peer_protocol = {}

        try:
            handshake_timeout = self.get_widget("handshake_timeout")
            if handshake_timeout:
                peer_protocol["handshake_timeout_seconds"] = handshake_timeout.get_value()

            message_read_timeout = self.get_widget("message_read_timeout")
            if message_read_timeout:
                peer_protocol["message_read_timeout_seconds"] = message_read_timeout.get_value()

            keep_alive_interval = self.get_widget("keep_alive_interval")
            if keep_alive_interval:
                peer_protocol["keep_alive_interval_seconds"] = keep_alive_interval.get_value()

            peer_contact_interval = self.get_widget("peer_contact_interval")
            if peer_contact_interval:
                peer_protocol["contact_interval_seconds"] = peer_contact_interval.get_value()

        except Exception as e:
            self.logger.error(f"Error collecting peer protocol settings: {e}")

        return peer_protocol

    def _collect_seeder_settings(self) -> Dict[str, Any]:
        """Collect seeder protocol settings."""
        seeders = {}

        try:
            udp_seeder_timeout = self.get_widget("udp_seeder_timeout")
            if udp_seeder_timeout:
                seeders["udp_timeout_seconds"] = int(udp_seeder_timeout.get_value())

            http_seeder_timeout = self.get_widget("http_seeder_timeout")
            if http_seeder_timeout:
                seeders["http_timeout_seconds"] = int(http_seeder_timeout.get_value())

            seeder_port_min = self.get_widget("seeder_port_min")
            if seeder_port_min:
                seeders["port_range_min"] = int(seeder_port_min.get_value())

            seeder_port_max = self.get_widget("seeder_port_max")
            if seeder_port_max:
                seeders["port_range_max"] = int(seeder_port_max.get_value())

            transaction_id_min = self.get_widget("transaction_id_min")
            if transaction_id_min:
                seeders["transaction_id_min"] = int(transaction_id_min.get_value())

            transaction_id_max = self.get_widget("transaction_id_max")
            if transaction_id_max:
                seeders["transaction_id_max"] = int(transaction_id_max.get_value())

            peer_request_count = self.get_widget("peer_request_count")
            if peer_request_count:
                seeders["peer_request_count"] = int(peer_request_count.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting seeder settings: {e}")

        return seeders

    def _collect_peer_behavior_settings(self) -> Dict[str, Any]:
        """Collect peer behavior settings."""
        peer_behavior = {}

        try:
            seeder_upload_activity = self.get_widget("seeder_upload_activity")
            if seeder_upload_activity:
                peer_behavior["seeder_upload_activity_probability"] = seeder_upload_activity.get_value()

            peer_idle_chance = self.get_widget("peer_idle_chance")
            if peer_idle_chance:
                peer_behavior["peer_idle_chance"] = peer_idle_chance.get_value()

            progress_dist_start = self.get_widget("progress_dist_start")
            if progress_dist_start:
                peer_behavior["progress_distribution_start"] = progress_dist_start.get_value()

            progress_dist_middle = self.get_widget("progress_dist_middle")
            if progress_dist_middle:
                peer_behavior["progress_distribution_middle"] = progress_dist_middle.get_value()

            progress_dist_almost = self.get_widget("progress_dist_almost")
            if progress_dist_almost:
                peer_behavior["progress_distribution_almost_done"] = progress_dist_almost.get_value()

            peer_behavior_analysis = self.get_widget("peer_behavior_analysis")
            if peer_behavior_analysis:
                peer_behavior["peer_behavior_analysis_probability"] = peer_behavior_analysis.get_value()

            peer_status_change = self.get_widget("peer_status_change")
            if peer_status_change:
                peer_behavior["peer_status_change_probability"] = peer_status_change.get_value()

            peer_dropout = self.get_widget("peer_dropout")
            if peer_dropout:
                peer_behavior["peer_dropout_probability"] = peer_dropout.get_value()

            connection_rotation = self.get_widget("connection_rotation")
            if connection_rotation:
                peer_behavior["connection_rotation_percentage"] = connection_rotation.get_value()

        except Exception as e:
            self.logger.error(f"Error collecting peer behavior settings: {e}")

        return peer_behavior

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate Peer Protocol tab settings."""
        errors = {}

        try:
            # Validate port ranges
            seeder_port_min = self.get_widget("seeder_port_min")
            seeder_port_max = self.get_widget("seeder_port_max")
            if seeder_port_min and seeder_port_max:
                min_port = int(seeder_port_min.get_value())
                max_port = int(seeder_port_max.get_value())
                if min_port >= max_port:
                    errors["seeder_port_range"] = "Minimum port must be less than maximum port"

            # Validate transaction ID ranges
            transaction_id_min = self.get_widget("transaction_id_min")
            transaction_id_max = self.get_widget("transaction_id_max")
            if transaction_id_min and transaction_id_max:
                min_id = int(transaction_id_min.get_value())
                max_id = int(transaction_id_max.get_value())
                if min_id >= max_id:
                    errors["transaction_id_range"] = "Minimum transaction ID must be less than maximum"

        except Exception as e:
            self.logger.error(f"Error validating Peer Protocol tab settings: {e}")
            errors["general"] = str(e)

        return errors

    def _reset_tab_defaults(self) -> None:
        """Reset Peer Protocol tab to default values."""
        try:
            # Reset peer protocol timeouts
            handshake_timeout = self.get_widget("handshake_timeout")
            if handshake_timeout:
                handshake_timeout.set_value(30.0)

            message_read_timeout = self.get_widget("message_read_timeout")
            if message_read_timeout:
                message_read_timeout.set_value(60.0)

            keep_alive_interval = self.get_widget("keep_alive_interval")
            if keep_alive_interval:
                keep_alive_interval.set_value(120.0)

            peer_contact_interval = self.get_widget("peer_contact_interval")
            if peer_contact_interval:
                peer_contact_interval.set_value(300.0)

            # Reset seeder settings
            udp_seeder_timeout = self.get_widget("udp_seeder_timeout")
            if udp_seeder_timeout:
                udp_seeder_timeout.set_value(5)

            http_seeder_timeout = self.get_widget("http_seeder_timeout")
            if http_seeder_timeout:
                http_seeder_timeout.set_value(10)

            seeder_port_min = self.get_widget("seeder_port_min")
            if seeder_port_min:
                seeder_port_min.set_value(1025)

            seeder_port_max = self.get_widget("seeder_port_max")
            if seeder_port_max:
                seeder_port_max.set_value(65000)

            # Reset peer behavior settings to reasonable defaults
            seeder_upload_activity = self.get_widget("seeder_upload_activity")
            if seeder_upload_activity:
                seeder_upload_activity.set_value(0.9)

            peer_idle_chance = self.get_widget("peer_idle_chance")
            if peer_idle_chance:
                peer_idle_chance.set_value(0.1)

            self.show_notification("Peer Protocol settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting Peer Protocol tab to defaults: {e}")

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        """Update view based on model changes."""
        self.logger.trace(
            "PeerProtocolTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference
        self.model = model
        # Set initialization flag to prevent triggering language changes during setup
        self._language_change_connected = True
