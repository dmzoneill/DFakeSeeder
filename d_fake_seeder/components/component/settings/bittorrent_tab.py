"""
BitTorrent settings tab for the settings dialog.

Handles BitTorrent protocol features, user agent settings, and announce intervals.
"""

# fmt: off
from typing import Any, Dict

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from .base_tab import BaseSettingsTab  # noqa
from .settings_mixins import NotificationMixin  # noqa: E402
from .settings_mixins import TranslationMixin  # noqa: E402
from .settings_mixins import UtilityMixin, ValidationMixin  # noqa: E402

# fmt: on


class BitTorrentTab(BaseSettingsTab, NotificationMixin, TranslationMixin, ValidationMixin, UtilityMixin):
    """
    BitTorrent settings tab component.

    Manages:
    - Protocol features (DHT, PEX)
    - User agent configuration
    - Announce interval settings
    - BitTorrent-specific behavior
    """

    @property
    def tab_name(self) -> str:
        """Return the name of this tab."""
        return "BitTorrent"

    def _init_widgets(self) -> None:
        """Initialize BitTorrent tab widgets."""
        # Cache commonly used widgets
        self._widgets.update(
            {
                # Protocol features
                "enable_dht": self.builder.get_object("settings_enable_dht"),
                "enable_pex": self.builder.get_object("settings_enable_pex"),
                "enable_lsd": self.builder.get_object("settings_enable_lsd"),
                "enable_utp": self.builder.get_object("settings_enable_utp"),
                # User agent
                "user_agent": self.builder.get_object("settings_user_agent"),
                "custom_user_agent": self.builder.get_object("settings_custom_user_agent"),
                # Announce intervals
                "announce_interval": self.builder.get_object("settings_announce_interval"),
                "min_announce_interval": self.builder.get_object("settings_min_announce_interval"),
                # Peer settings
                "max_peers_global": self.builder.get_object("settings_max_peers_global"),
                "max_peers_torrent": self.builder.get_object("settings_max_peers_torrent"),
                "max_upload_slots_global": self.builder.get_object("settings_max_upload_slots_global"),
                "max_upload_slots_torrent": self.builder.get_object("settings_max_upload_slots_torrent"),
            }
        )

        # Initialize user agent dropdown
        self._setup_user_agent_dropdown()

    def _connect_signals(self) -> None:
        """Connect signal handlers for BitTorrent tab."""
        # Protocol features
        dht = self.get_widget("enable_dht")
        if dht:
            self.track_signal(dht, dht.connect("state-set", self.on_dht_changed))

        pex = self.get_widget("enable_pex")
        if pex:
            self.track_signal(pex, pex.connect("state-set", self.on_pex_changed))

        lsd = self.get_widget("enable_lsd")
        if lsd:
            self.track_signal(lsd, lsd.connect("state-set", self.on_lsd_changed))

        utp = self.get_widget("enable_utp")
        if utp:
            self.track_signal(utp, utp.connect("state-set", self.on_utp_changed))

        # User agent
        user_agent = self.get_widget("user_agent")
        if user_agent:
            self.track_signal(
                user_agent,
                user_agent.connect("notify::selected", self.on_user_agent_changed),
            )

        custom_user_agent = self.get_widget("custom_user_agent")
        if custom_user_agent:
            self.track_signal(
                custom_user_agent,
                custom_user_agent.connect("changed", self.on_custom_user_agent_changed),
            )

        # Announce intervals
        announce = self.get_widget("announce_interval")
        if announce:
            self.track_signal(
                announce,
                announce.connect("value-changed", self.on_announce_interval_changed),
            )

        min_announce = self.get_widget("min_announce_interval")
        if min_announce:
            self.track_signal(
                min_announce,
                min_announce.connect("value-changed", self.on_min_announce_interval_changed),
            )

        # Peer settings
        max_peers_global = self.get_widget("max_peers_global")
        if max_peers_global:
            self.track_signal(
                max_peers_global,
                max_peers_global.connect("value-changed", self.on_max_peers_global_changed),
            )

        max_peers_torrent = self.get_widget("max_peers_torrent")
        if max_peers_torrent:
            self.track_signal(
                max_peers_torrent,
                max_peers_torrent.connect("value-changed", self.on_max_peers_torrent_changed),
            )

        max_upload_slots_global = self.get_widget("max_upload_slots_global")
        if max_upload_slots_global:
            self.track_signal(
                max_upload_slots_global,
                max_upload_slots_global.connect("value-changed", self.on_max_upload_slots_global_changed),
            )

        max_upload_slots_torrent = self.get_widget("max_upload_slots_torrent")
        if max_upload_slots_torrent:
            self.track_signal(
                max_upload_slots_torrent,
                max_upload_slots_torrent.connect("value-changed", self.on_max_upload_slots_torrent_changed),
            )

    def _load_settings(self) -> None:
        """Load current settings into BitTorrent tab widgets."""
        try:
            # Load BitTorrent protocol settings
            bittorrent_settings = getattr(self.app_settings, "bittorrent", {})
            self._load_bittorrent_settings(bittorrent_settings)

            self.logger.debug("BitTorrent tab settings loaded")

        except Exception as e:
            self.logger.error(f"Error loading BitTorrent tab settings: {e}")

    def _load_bittorrent_settings(self, bittorrent_settings: Dict[str, Any]) -> None:
        """Load BitTorrent protocol settings."""
        try:
            # Protocol features
            dht = self.get_widget("enable_dht")
            if dht:
                dht.set_active(bittorrent_settings.get("enable_dht", True))

            pex = self.get_widget("enable_pex")
            if pex:
                pex.set_active(bittorrent_settings.get("enable_pex", True))

            lsd = self.get_widget("enable_lsd")
            if lsd:
                lsd.set_active(bittorrent_settings.get("enable_lsd", True))

            utp = self.get_widget("enable_utp")
            if utp:
                utp.set_active(bittorrent_settings.get("enable_utp", True))

            # User agent
            self._update_user_agent_dropdown(bittorrent_settings)

            # Announce intervals
            announce = self.get_widget("announce_interval")
            if announce:
                announce.set_value(bittorrent_settings.get("announce_interval_seconds", 1800))

            min_announce = self.get_widget("min_announce_interval")
            if min_announce:
                min_announce.set_value(bittorrent_settings.get("min_announce_interval_seconds", 300))

            # Peer settings
            max_peers_global = self.get_widget("max_peers_global")
            if max_peers_global:
                max_peers_global.set_value(bittorrent_settings.get("max_peers_global", 200))

            max_peers_torrent = self.get_widget("max_peers_torrent")
            if max_peers_torrent:
                max_peers_torrent.set_value(bittorrent_settings.get("max_peers_per_torrent", 50))

            max_upload_slots_global = self.get_widget("max_upload_slots_global")
            if max_upload_slots_global:
                max_upload_slots_global.set_value(bittorrent_settings.get("max_upload_slots_global", 4))

            max_upload_slots_torrent = self.get_widget("max_upload_slots_torrent")
            if max_upload_slots_torrent:
                max_upload_slots_torrent.set_value(bittorrent_settings.get("max_upload_slots_per_torrent", 2))

        except Exception as e:
            self.logger.error(f"Error loading BitTorrent settings: {e}")

    def _setup_user_agent_dropdown(self) -> None:
        """Set up the user agent dropdown with common clients."""
        try:
            user_agent_dropdown = self.get_widget("user_agent")
            if not user_agent_dropdown:
                return

            # Common BitTorrent clients
            # Get translation function if available
            translate_func = (
                self.model.get_translate_func()
                if hasattr(self, "model") and hasattr(self.model, "get_translate_func")
                else lambda x: x
            )

            user_agents = [
                "DFakeSeeder/1.0",
                "µTorrent/3.5.5",
                "BitTorrent/7.10.5",
                "qBittorrent/4.5.0",
                "Deluge/2.1.1",
                "Transmission/3.00",
                "libtorrent/2.0.6",
                translate_func("Custom"),
            ]

            # Create string list model
            string_list = Gtk.StringList()
            for agent in user_agents:
                string_list.append(agent)

            # Set model
            user_agent_dropdown.set_model(string_list)

            self.logger.debug(f"User agent dropdown set up with {len(user_agents)} options")

        except Exception as e:
            self.logger.error(f"Error setting up user agent dropdown: {e}")

    def _update_user_agent_dropdown(self, bittorrent_settings: Dict[str, Any]) -> None:
        """Update user agent dropdown selection."""
        try:
            user_agent_dropdown = self.get_widget("user_agent")
            if not user_agent_dropdown:
                return

            current_user_agent = bittorrent_settings.get("user_agent", "DFakeSeeder/1.0")

            # Get translation function if available
            translate_func = (
                self.model.get_translate_func()
                if hasattr(self, "model") and hasattr(self.model, "get_translate_func")
                else lambda x: x
            )

            # Find index of current user agent
            predefined_agents = [
                "DFakeSeeder/1.0",
                "µTorrent/3.5.5",
                "BitTorrent/7.10.5",
                "qBittorrent/4.5.0",
                "Deluge/2.1.1",
                "Transmission/3.00",
                "libtorrent/2.0.6",
                translate_func("Custom"),
            ]

            try:
                current_index = predefined_agents.index(current_user_agent)
                user_agent_dropdown.set_selected(current_index)
            except ValueError:
                # Custom user agent
                user_agent_dropdown.set_selected(len(predefined_agents) - 1)  # Custom option
                custom_user_agent = self.get_widget("custom_user_agent")
                if custom_user_agent:
                    custom_user_agent.set_text(current_user_agent)

            self._update_user_agent_dependencies()

        except Exception as e:
            self.logger.error(f"Error updating user agent dropdown: {e}")

    def _setup_dependencies(self) -> None:
        """Set up dependencies for BitTorrent tab."""
        self._update_user_agent_dependencies()

    def _update_tab_dependencies(self) -> None:
        """Update BitTorrent tab dependencies."""
        self._update_user_agent_dependencies()

    def _update_user_agent_dependencies(self) -> None:
        """Update user agent-related widget dependencies."""
        try:
            user_agent_dropdown = self.get_widget("user_agent")
            if not user_agent_dropdown:
                return

            # Enable custom user agent entry if "Custom" is selected
            is_custom = user_agent_dropdown.get_selected() == 7  # Custom is last option
            self.update_widget_sensitivity("custom_user_agent", is_custom)

        except Exception as e:
            self.logger.error(f"Error updating user agent dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from BitTorrent tab widgets."""
        settings = {}

        try:
            # Collect BitTorrent settings
            settings["bittorrent"] = self._collect_bittorrent_settings()

        except Exception as e:
            self.logger.error(f"Error collecting BitTorrent tab settings: {e}")

        return settings

    def _collect_bittorrent_settings(self) -> Dict[str, Any]:
        """Collect BitTorrent protocol settings."""
        bittorrent_settings = {}

        try:
            # Protocol features
            dht = self.get_widget("enable_dht")
            if dht:
                bittorrent_settings["enable_dht"] = dht.get_active()

            pex = self.get_widget("enable_pex")
            if pex:
                bittorrent_settings["enable_pex"] = pex.get_active()

            lsd = self.get_widget("enable_lsd")
            if lsd:
                bittorrent_settings["enable_lsd"] = lsd.get_active()

            utp = self.get_widget("enable_utp")
            if utp:
                bittorrent_settings["enable_utp"] = utp.get_active()

            # User agent
            user_agent_dropdown = self.get_widget("user_agent")
            if user_agent_dropdown:
                selected_index = user_agent_dropdown.get_selected()
                if selected_index == 7:  # Custom
                    custom_user_agent = self.get_widget("custom_user_agent")
                    if custom_user_agent:
                        bittorrent_settings["user_agent"] = custom_user_agent.get_text()
                else:
                    predefined_agents = [
                        "DFakeSeeder/1.0",
                        "µTorrent/3.5.5",
                        "BitTorrent/7.10.5",
                        "qBittorrent/4.5.0",
                        "Deluge/2.1.1",
                        "Transmission/3.00",
                        "libtorrent/2.0.6",
                    ]
                    if selected_index < len(predefined_agents):
                        bittorrent_settings["user_agent"] = predefined_agents[selected_index]

            # Announce intervals
            announce = self.get_widget("announce_interval")
            if announce:
                bittorrent_settings["announce_interval_seconds"] = int(announce.get_value())

            min_announce = self.get_widget("min_announce_interval")
            if min_announce:
                bittorrent_settings["min_announce_interval_seconds"] = int(min_announce.get_value())

            # Peer settings
            max_peers_global = self.get_widget("max_peers_global")
            if max_peers_global:
                bittorrent_settings["max_peers_global"] = int(max_peers_global.get_value())

            max_peers_torrent = self.get_widget("max_peers_torrent")
            if max_peers_torrent:
                bittorrent_settings["max_peers_per_torrent"] = int(max_peers_torrent.get_value())

            max_upload_slots_global = self.get_widget("max_upload_slots_global")
            if max_upload_slots_global:
                bittorrent_settings["max_upload_slots_global"] = int(max_upload_slots_global.get_value())

            max_upload_slots_torrent = self.get_widget("max_upload_slots_torrent")
            if max_upload_slots_torrent:
                bittorrent_settings["max_upload_slots_per_torrent"] = int(max_upload_slots_torrent.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting BitTorrent settings: {e}")

        return bittorrent_settings

    def _validate_tab_settings(self) -> Dict[str, str]:
        """Validate BitTorrent tab settings."""
        errors = {}

        try:
            # Validate announce intervals
            announce = self.get_widget("announce_interval")
            min_announce = self.get_widget("min_announce_interval")
            if announce and min_announce:
                announce_interval = int(announce.get_value())
                min_announce_interval = int(min_announce.get_value())
                if min_announce_interval >= announce_interval:
                    errors["announce_interval"] = "Minimum announce interval must be less than announce interval"

            # Validate custom user agent
            user_agent_dropdown = self.get_widget("user_agent")
            if user_agent_dropdown and user_agent_dropdown.get_selected() == 7:  # Custom
                custom_user_agent = self.get_widget("custom_user_agent")
                if custom_user_agent:
                    custom_text = custom_user_agent.get_text().strip()
                    if not custom_text:
                        errors["custom_user_agent"] = "Custom user agent cannot be empty"

        except Exception as e:
            self.logger.error(f"Error validating BitTorrent tab settings: {e}")
            errors["general"] = str(e)

        return errors

    # Signal handlers
    def on_dht_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle DHT setting change."""
        try:
            self.app_settings.set("bittorrent.enable_dht", state)
            message = "DHT enabled" if state else "DHT disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing DHT setting: {e}")

    def on_pex_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle PEX setting change."""
        try:
            self.app_settings.set("bittorrent.enable_pex", state)
            message = "PEX enabled" if state else "PEX disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing PEX setting: {e}")

    def on_lsd_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle LSD setting change."""
        try:
            self.app_settings.set("bittorrent.enable_lsd", state)
            message = "LSD enabled" if state else "LSD disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing LSD setting: {e}")

    def on_utp_changed(self, switch: Gtk.Switch, state: bool) -> None:
        """Handle uTP setting change."""
        try:
            self.app_settings.set("bittorrent.enable_utp", state)
            message = "uTP enabled" if state else "uTP disabled"
            self.show_notification(message, "success")
        except Exception as e:
            self.logger.error(f"Error changing uTP setting: {e}")

    def on_user_agent_changed(self, dropdown: Gtk.DropDown, param) -> None:
        """Handle user agent selection change."""
        try:
            self.update_dependencies()
            selected_index = dropdown.get_selected()

            if selected_index < 7:  # Not custom
                predefined_agents = [
                    "DFakeSeeder/1.0",
                    "µTorrent/3.5.5",
                    "BitTorrent/7.10.5",
                    "qBittorrent/4.5.0",
                    "Deluge/2.1.1",
                    "Transmission/3.00",
                    "libtorrent/2.0.6",
                ]
                if selected_index < len(predefined_agents):
                    user_agent = predefined_agents[selected_index]
                    self.app_settings.set("bittorrent.user_agent", user_agent)
                    self.logger.debug(f"User agent changed to: {user_agent}")

        except Exception as e:
            self.logger.error(f"Error changing user agent: {e}")

    def on_custom_user_agent_changed(self, entry: Gtk.Entry) -> None:
        """Handle custom user agent change."""
        try:
            user_agent = entry.get_text()
            self.app_settings.set("bittorrent.user_agent", user_agent)
            self.logger.debug(f"Custom user agent changed to: {user_agent}")
        except Exception as e:
            self.logger.error(f"Error changing custom user agent: {e}")

    def on_announce_interval_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle announce interval change."""
        try:
            interval = int(spin_button.get_value())
            self.app_settings.set("bittorrent.announce_interval_seconds", interval)
            self.logger.debug(f"Announce interval changed to: {interval}")
        except Exception as e:
            self.logger.error(f"Error changing announce interval: {e}")

    def on_min_announce_interval_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle minimum announce interval change."""
        try:
            interval = int(spin_button.get_value())
            self.app_settings.set("bittorrent.min_announce_interval_seconds", interval)
            self.logger.debug(f"Minimum announce interval changed to: {interval}")
        except Exception as e:
            self.logger.error(f"Error changing minimum announce interval: {e}")

    def on_max_peers_global_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle global max peers change."""
        try:
            max_peers = int(spin_button.get_value())
            self.app_settings.set("bittorrent.max_peers_global", max_peers)
            self.logger.debug(f"Global max peers changed to: {max_peers}")
        except Exception as e:
            self.logger.error(f"Error changing global max peers: {e}")

    def on_max_peers_torrent_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle per-torrent max peers change."""
        try:
            max_peers = int(spin_button.get_value())
            self.app_settings.set("bittorrent.max_peers_per_torrent", max_peers)
            self.logger.debug(f"Per-torrent max peers changed to: {max_peers}")
        except Exception as e:
            self.logger.error(f"Error changing per-torrent max peers: {e}")

    def on_max_upload_slots_global_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle global max upload slots change."""
        try:
            max_slots = int(spin_button.get_value())
            self.app_settings.set("bittorrent.max_upload_slots_global", max_slots)
            self.logger.debug(f"Global max upload slots changed to: {max_slots}")
        except Exception as e:
            self.logger.error(f"Error changing global max upload slots: {e}")

    def on_max_upload_slots_torrent_changed(self, spin_button: Gtk.SpinButton) -> None:
        """Handle per-torrent max upload slots change."""
        try:
            max_slots = int(spin_button.get_value())
            self.app_settings.set("bittorrent.max_upload_slots_per_torrent", max_slots)
            self.logger.debug(f"Per-torrent max upload slots changed to: {max_slots}")
        except Exception as e:
            self.logger.error(f"Error changing per-torrent max upload slots: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset BitTorrent tab to default values."""
        try:
            # Reset protocol features
            dht = self.get_widget("enable_dht")
            if dht:
                dht.set_active(True)

            pex = self.get_widget("enable_pex")
            if pex:
                pex.set_active(True)

            lsd = self.get_widget("enable_lsd")
            if lsd:
                lsd.set_active(True)

            utp = self.get_widget("enable_utp")
            if utp:
                utp.set_active(True)

            # Reset user agent to default
            user_agent = self.get_widget("user_agent")
            if user_agent:
                user_agent.set_selected(0)  # DFakeSeeder/1.0

            # Reset announce intervals
            announce = self.get_widget("announce_interval")
            if announce:
                announce.set_value(1800)  # 30 minutes

            min_announce = self.get_widget("min_announce_interval")
            if min_announce:
                min_announce.set_value(300)  # 5 minutes

            # Reset peer settings
            max_peers_global = self.get_widget("max_peers_global")
            if max_peers_global:
                max_peers_global.set_value(200)

            max_peers_torrent = self.get_widget("max_peers_torrent")
            if max_peers_torrent:
                max_peers_torrent.set_value(50)

            self.update_dependencies()
            self.show_notification("BitTorrent settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting BitTorrent tab to defaults: {e}")

    def handle_model_changed(self, source, data_obj, _data_changed):
        """Handle model change events."""
        self.logger.debug(
            "BitTorrentTab model changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_attribute_changed(self, source, key, value):
        """Handle attribute change events."""
        self.logger.debug(
            "BitTorrentTab attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_settings_changed(self, source, data_obj, _data_changed):
        """Handle settings change events."""
        self.logger.debug(
            "BitTorrentTab settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.debug(
            "BitTorrentTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()
