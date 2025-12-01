"""
Peer Protocol settings tab for the settings dialog.

Handles peer protocol timeouts, seeder settings, and peer behavior configuration.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .base_tab import BaseSettingsTab  # noqa
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
        # Peer Protocol Timeouts
        handshake_timeout = self.get_widget("handshake_timeout")
        if handshake_timeout:
            self.track_signal(
                handshake_timeout,
                handshake_timeout.connect("value-changed", self.on_handshake_timeout_changed),
            )

        message_read_timeout = self.get_widget("message_read_timeout")
        if message_read_timeout:
            self.track_signal(
                message_read_timeout,
                message_read_timeout.connect("value-changed", self.on_message_read_timeout_changed),
            )

        keep_alive_interval = self.get_widget("keep_alive_interval")
        if keep_alive_interval:
            self.track_signal(
                keep_alive_interval,
                keep_alive_interval.connect("value-changed", self.on_keep_alive_interval_changed),
            )

        peer_contact_interval = self.get_widget("peer_contact_interval")
        if peer_contact_interval:
            self.track_signal(
                peer_contact_interval,
                peer_contact_interval.connect("value-changed", self.on_peer_contact_interval_changed),
            )

        # Seeder Protocol Settings
        udp_seeder_timeout = self.get_widget("udp_seeder_timeout")
        if udp_seeder_timeout:
            self.track_signal(
                udp_seeder_timeout,
                udp_seeder_timeout.connect("value-changed", self.on_udp_seeder_timeout_changed),
            )

        http_seeder_timeout = self.get_widget("http_seeder_timeout")
        if http_seeder_timeout:
            self.track_signal(
                http_seeder_timeout,
                http_seeder_timeout.connect("value-changed", self.on_http_seeder_timeout_changed),
            )

        seeder_port_min = self.get_widget("seeder_port_min")
        if seeder_port_min:
            self.track_signal(
                seeder_port_min,
                seeder_port_min.connect("value-changed", self.on_seeder_port_min_changed),
            )

        seeder_port_max = self.get_widget("seeder_port_max")
        if seeder_port_max:
            self.track_signal(
                seeder_port_max,
                seeder_port_max.connect("value-changed", self.on_seeder_port_max_changed),
            )

        transaction_id_min = self.get_widget("transaction_id_min")
        if transaction_id_min:
            self.track_signal(
                transaction_id_min,
                transaction_id_min.connect("value-changed", self.on_transaction_id_min_changed),
            )

        transaction_id_max = self.get_widget("transaction_id_max")
        if transaction_id_max:
            self.track_signal(
                transaction_id_max,
                transaction_id_max.connect("value-changed", self.on_transaction_id_max_changed),
            )

        peer_request_count = self.get_widget("peer_request_count")
        if peer_request_count:
            self.track_signal(
                peer_request_count,
                peer_request_count.connect("value-changed", self.on_peer_request_count_changed),
            )

        # Peer Behavior Settings
        seeder_upload_activity = self.get_widget("seeder_upload_activity")
        if seeder_upload_activity:
            self.track_signal(
                seeder_upload_activity,
                seeder_upload_activity.connect("value-changed", self.on_seeder_upload_activity_probability_changed),
            )

        peer_idle_chance = self.get_widget("peer_idle_chance")
        if peer_idle_chance:
            self.track_signal(
                peer_idle_chance,
                peer_idle_chance.connect("value-changed", self.on_peer_idle_chance_changed),
            )

        progress_dist_start = self.get_widget("progress_dist_start")
        if progress_dist_start:
            self.track_signal(
                progress_dist_start,
                progress_dist_start.connect("value-changed", self.on_progress_distribution_start_changed),
            )

        progress_dist_middle = self.get_widget("progress_dist_middle")
        if progress_dist_middle:
            self.track_signal(
                progress_dist_middle,
                progress_dist_middle.connect("value-changed", self.on_progress_distribution_middle_changed),
            )

        progress_dist_almost = self.get_widget("progress_dist_almost")
        if progress_dist_almost:
            self.track_signal(
                progress_dist_almost,
                progress_dist_almost.connect("value-changed", self.on_progress_distribution_almost_changed),
            )

        peer_behavior_analysis = self.get_widget("peer_behavior_analysis")
        if peer_behavior_analysis:
            self.track_signal(
                peer_behavior_analysis,
                peer_behavior_analysis.connect("value-changed", self.on_peer_behavior_analysis_probability_changed),
            )

        peer_status_change = self.get_widget("peer_status_change")
        if peer_status_change:
            self.track_signal(
                peer_status_change,
                peer_status_change.connect("value-changed", self.on_peer_status_change_probability_changed),
            )

        peer_dropout = self.get_widget("peer_dropout")
        if peer_dropout:
            self.track_signal(
                peer_dropout,
                peer_dropout.connect("value-changed", self.on_peer_dropout_probability_changed),
            )

        connection_rotation = self.get_widget("connection_rotation")
        if connection_rotation:
            self.track_signal(
                connection_rotation,
                connection_rotation.connect("value-changed", self.on_connection_rotation_percentage_changed),
            )

    def _load_settings(self) -> None:
        """Load current settings into Peer Protocol tab widgets."""
        try:
            # Load peer protocol settings
            peer_protocol = getattr(self.app_settings, "peer_protocol", {})
            self._load_peer_protocol_settings(peer_protocol)

            # Load seeder settings
            seeders = getattr(self.app_settings, "seeders", {})
            self._load_seeder_settings(seeders)

            # Load peer behavior settings
            peer_behavior = getattr(self.app_settings, "peer_behavior", {})
            self._load_peer_behavior_settings(peer_behavior)

            self.logger.debug("Peer Protocol tab settings loaded")

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
        """Collect current settings from Peer Protocol tab widgets."""
        settings = {}

        try:
            # Collect peer protocol settings
            settings["peer_protocol"] = self._collect_peer_protocol_settings()
            settings["seeders"] = self._collect_seeder_settings()
            settings["peer_behavior"] = self._collect_peer_behavior_settings()

        except Exception as e:
            self.logger.error(f"Error collecting Peer Protocol tab settings: {e}")

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

    # Signal handlers
    def on_handshake_timeout_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle handshake timeout change."""
        try:
            timeout = spin_button.get_value()
            self.app_settings.set("peer_protocol.handshake_timeout_seconds", timeout)
            self.logger.debug(f"Handshake timeout changed to: {timeout}")
        except Exception as e:
            self.logger.error(f"Error changing handshake timeout: {e}")

    def on_message_read_timeout_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle message read timeout change."""
        try:
            timeout = spin_button.get_value()
            self.app_settings.set("peer_protocol.message_read_timeout_seconds", timeout)
            self.logger.debug(f"Message read timeout changed to: {timeout}")
        except Exception as e:
            self.logger.error(f"Error changing message read timeout: {e}")

    def on_keep_alive_interval_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle keep alive interval change."""
        try:
            interval = spin_button.get_value()
            self.app_settings.set("peer_protocol.keep_alive_interval_seconds", interval)
            self.logger.debug(f"Keep alive interval changed to: {interval}")
        except Exception as e:
            self.logger.error(f"Error changing keep alive interval: {e}")

    def on_peer_contact_interval_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle peer contact interval change."""
        try:
            interval = spin_button.get_value()
            self.app_settings.set("peer_protocol.contact_interval_seconds", interval)
            self.logger.debug(f"Peer contact interval changed to: {interval}")
        except Exception as e:
            self.logger.error(f"Error changing peer contact interval: {e}")

    def on_udp_seeder_timeout_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle UDP seeder timeout change."""
        try:
            timeout = int(spin_button.get_value())
            self.app_settings.set("seeders.udp_timeout_seconds", timeout)
            self.logger.debug(f"UDP seeder timeout changed to: {timeout}")
        except Exception as e:
            self.logger.error(f"Error changing UDP seeder timeout: {e}")

    def on_http_seeder_timeout_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle HTTP seeder timeout change."""
        try:
            timeout = int(spin_button.get_value())
            self.app_settings.set("seeders.http_timeout_seconds", timeout)
            self.logger.debug(f"HTTP seeder timeout changed to: {timeout}")
        except Exception as e:
            self.logger.error(f"Error changing HTTP seeder timeout: {e}")

    def on_seeder_port_min_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle seeder minimum port change."""
        try:
            port = int(spin_button.get_value())
            self.app_settings.set("seeders.port_range_min", port)
            self.logger.debug(f"Seeder minimum port changed to: {port}")
        except Exception as e:
            self.logger.error(f"Error changing seeder minimum port: {e}")

    def on_seeder_port_max_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle seeder maximum port change."""
        try:
            port = int(spin_button.get_value())
            self.app_settings.set("seeders.port_range_max", port)
            self.logger.debug(f"Seeder maximum port changed to: {port}")
        except Exception as e:
            self.logger.error(f"Error changing seeder maximum port: {e}")

    def on_transaction_id_min_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle transaction ID minimum change."""
        try:
            min_id = int(spin_button.get_value())
            self.app_settings.set("seeders.transaction_id_min", min_id)
            self.logger.debug(f"Transaction ID minimum changed to: {min_id}")
        except Exception as e:
            self.logger.error(f"Error changing transaction ID minimum: {e}")

    def on_transaction_id_max_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle transaction ID maximum change."""
        try:
            max_id = int(spin_button.get_value())
            self.app_settings.set("seeders.transaction_id_max", max_id)
            self.logger.debug(f"Transaction ID maximum changed to: {max_id}")
        except Exception as e:
            self.logger.error(f"Error changing transaction ID maximum: {e}")

    def on_peer_request_count_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle peer request count change."""
        try:
            count = int(spin_button.get_value())
            self.app_settings.set("seeders.peer_request_count", count)
            self.logger.debug(f"Peer request count changed to: {count}")
        except Exception as e:
            self.logger.error(f"Error changing peer request count: {e}")

    def on_seeder_upload_activity_probability_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle seeder upload activity probability change."""
        try:
            probability = spin_button.get_value()
            self.app_settings.set("peer_behavior.seeder_upload_activity_probability", probability)
            self.logger.debug(f"Seeder upload activity probability changed to: {probability}")
        except Exception as e:
            self.logger.error(f"Error changing seeder upload activity probability: {e}")

    def on_peer_idle_chance_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle peer idle chance change."""
        try:
            chance = spin_button.get_value()
            self.app_settings.set("peer_behavior.peer_idle_chance", chance)
            self.logger.debug(f"Peer idle chance changed to: {chance}")
        except Exception as e:
            self.logger.error(f"Error changing peer idle chance: {e}")

    def on_progress_distribution_start_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle progress distribution start change."""
        try:
            distribution = spin_button.get_value()
            self.app_settings.set("peer_behavior.progress_distribution_start", distribution)
            self.logger.debug(f"Progress distribution start changed to: {distribution}")
        except Exception as e:
            self.logger.error(f"Error changing progress distribution start: {e}")

    def on_progress_distribution_middle_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle progress distribution middle change."""
        try:
            distribution = spin_button.get_value()
            self.app_settings.set("peer_behavior.progress_distribution_middle", distribution)
            self.logger.debug(f"Progress distribution middle changed to: {distribution}")
        except Exception as e:
            self.logger.error(f"Error changing progress distribution middle: {e}")

    def on_progress_distribution_almost_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle progress distribution almost done change."""
        try:
            distribution = spin_button.get_value()
            self.app_settings.set("peer_behavior.progress_distribution_almost_done", distribution)
            self.logger.debug(f"Progress distribution almost done changed to: {distribution}")
        except Exception as e:
            self.logger.error(f"Error changing progress distribution almost done: {e}")

    def on_peer_behavior_analysis_probability_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle peer behavior analysis probability change."""
        try:
            probability = spin_button.get_value()
            self.app_settings.set("peer_behavior.peer_behavior_analysis_probability", probability)
            self.logger.debug(f"Peer behavior analysis probability changed to: {probability}")
        except Exception as e:
            self.logger.error(f"Error changing peer behavior analysis probability: {e}")

    def on_peer_status_change_probability_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle peer status change probability change."""
        try:
            probability = spin_button.get_value()
            self.app_settings.set("peer_behavior.peer_status_change_probability", probability)
            self.logger.debug(f"Peer status change probability changed to: {probability}")
        except Exception as e:
            self.logger.error(f"Error changing peer status change probability: {e}")

    def on_peer_dropout_probability_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle peer dropout probability change."""
        try:
            probability = spin_button.get_value()
            self.app_settings.set("peer_behavior.peer_dropout_probability", probability)
            self.logger.debug(f"Peer dropout probability changed to: {probability}")
        except Exception as e:
            self.logger.error(f"Error changing peer dropout probability: {e}")

    def on_connection_rotation_percentage_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle connection rotation percentage change."""
        try:
            percentage = spin_button.get_value()
            self.app_settings.set("peer_behavior.connection_rotation_percentage", percentage)
            self.logger.debug(f"Connection rotation percentage changed to: {percentage}")
        except Exception as e:
            self.logger.error(f"Error changing connection rotation percentage: {e}")

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

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.debug(
            "PeerProtocolTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "PeerProtocolTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "PeerProtocolTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.debug(
            "PeerProtocolTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference
        self.model = model
        # Set initialization flag to prevent triggering language changes during setup
        self._language_change_connected = True
