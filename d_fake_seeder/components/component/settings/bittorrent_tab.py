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

    # Auto-connect simple widgets with WIDGET_MAPPINGS
    WIDGET_MAPPINGS = [
        # Protocol features
        {
            "id": "settings_enable_dht",
            "name": "enable_dht",
            "setting_key": "bittorrent.enable_dht",
            "type": bool,
            "on_change": lambda self, value: self.show_notification(
                f"DHT {'enabled' if value else 'disabled'}", "success"
            ),
        },
        {
            "id": "settings_enable_pex",
            "name": "enable_pex",
            "setting_key": "bittorrent.enable_pex",
            "type": bool,
            "on_change": lambda self, value: self.show_notification(
                f"PEX {'enabled' if value else 'disabled'}", "success"
            ),
        },
        {
            "id": "settings_enable_lsd",
            "name": "enable_lsd",
            "setting_key": "bittorrent.enable_lsd",
            "type": bool,
            "on_change": lambda self, value: self.show_notification(
                f"LSD {'enabled' if value else 'disabled'}", "success"
            ),
        },
        {
            "id": "settings_enable_utp",
            "name": "enable_utp",
            "setting_key": "bittorrent.enable_utp",
            "type": bool,
            "on_change": lambda self, value: self.show_notification(
                f"uTP {'enabled' if value else 'disabled'}", "success"
            ),
        },
        # Custom user agent
        {
            "id": "settings_custom_user_agent",
            "name": "custom_user_agent",
            "setting_key": "bittorrent.user_agent",
            "type": str,
        },
        # Announce intervals
        {
            "id": "settings_announce_interval",
            "name": "announce_interval",
            "setting_key": "bittorrent.announce_interval_seconds",
            "type": int,
        },
        {
            "id": "settings_min_announce_interval",
            "name": "min_announce_interval",
            "setting_key": "bittorrent.min_announce_interval_seconds",
            "type": int,
        },
        # Peer settings
        {
            "id": "settings_max_peers_global",
            "name": "max_peers_global",
            "setting_key": "bittorrent.max_peers_global",
            "type": int,
        },
        {
            "id": "settings_max_peers_torrent",
            "name": "max_peers_torrent",
            "setting_key": "bittorrent.max_peers_per_torrent",
            "type": int,
        },
        {
            "id": "settings_max_upload_slots_global",
            "name": "max_upload_slots_global",
            "setting_key": "bittorrent.max_upload_slots_global",
            "type": int,
        },
        {
            "id": "settings_max_upload_slots_torrent",
            "name": "max_upload_slots_torrent",
            "setting_key": "bittorrent.max_upload_slots_per_torrent",
            "type": int,
        },
        # Encryption mode with transform
        {
            "id": "settings_encryption_mode",
            "name": "encryption_mode",
            "setting_key": "bittorrent.encryption_mode",
            "transform": lambda index: {0: "disabled", 1: "prefer", 2: "require"}.get(index, "prefer"),
            "on_change": lambda self, value: self.show_notification(f"Encryption mode: {value}", "success"),
        },
        # Scrape interval
        {
            "id": "settings_scrape_interval",
            "name": "scrape_interval",
            "setting_key": "bittorrent.scrape_interval_seconds",
            "type": int,
        },
    ]

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
                # Section container (hardcoded to sensitive=False in XML)
                "custom_agent_box": self.builder.get_object("settings_custom_agent_box"),
                "custom_user_agent": self.builder.get_object("settings_custom_user_agent"),
                # Announce intervals
                "announce_interval": self.builder.get_object("settings_announce_interval"),
                "min_announce_interval": self.builder.get_object("settings_min_announce_interval"),
                # Peer settings
                "max_peers_global": self.builder.get_object("settings_max_peers_global"),
                "max_peers_torrent": self.builder.get_object("settings_max_peers_torrent"),
                "max_upload_slots_global": self.builder.get_object("settings_max_upload_slots_global"),
                "max_upload_slots_torrent": self.builder.get_object("settings_max_upload_slots_torrent"),
                # Encryption and scrape
                "encryption_mode": self.builder.get_object("settings_encryption_mode"),
                "scrape_interval": self.builder.get_object("settings_scrape_interval"),
            }
        )

        # Initialize user agent dropdown
        self._setup_user_agent_dropdown()

    def _connect_signals(self) -> None:
        """Connect signal handlers for BitTorrent tab."""
        # Simple widgets (protocol features, custom_user_agent, announce intervals,
        # peer settings, encryption_mode, scrape_interval) are now auto-connected via WIDGET_MAPPINGS

        # User agent dropdown (has complex logic with dependencies)
        user_agent = self.get_widget("user_agent")
        if user_agent:
            self.track_signal(
                user_agent,
                user_agent.connect("notify::selected", self.on_user_agent_changed),
            )

    def _load_settings(self) -> None:
        """Load current settings into BitTorrent tab widgets."""
        try:
            # Load BitTorrent protocol settings
            bittorrent_settings = getattr(self.app_settings, "bittorrent", {})
            self._load_bittorrent_settings(bittorrent_settings)

            self.logger.info("BitTorrent tab settings loaded")

        except Exception as e:
            self.logger.error(f"Error loading BitTorrent tab settings: {e}")

    def _load_bittorrent_settings(self, bittorrent_settings: Dict[str, Any]) -> None:
        """Load BitTorrent protocol settings."""
        try:
            # Protocol features - use set_switch_state for proper visual sync
            dht = self.get_widget("enable_dht")
            if dht:
                self.set_switch_state(dht, bittorrent_settings.get("enable_dht", True))

            pex = self.get_widget("enable_pex")
            if pex:
                self.set_switch_state(pex, bittorrent_settings.get("enable_pex", True))

            lsd = self.get_widget("enable_lsd")
            if lsd:
                self.set_switch_state(lsd, bittorrent_settings.get("enable_lsd", True))

            utp = self.get_widget("enable_utp")
            if utp:
                self.set_switch_state(utp, bittorrent_settings.get("enable_utp", True))

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

            # Encryption mode
            encryption_mode = self.get_widget("encryption_mode")
            if encryption_mode:
                encryption_value = bittorrent_settings.get("encryption_mode", "prefer")
                # Map encryption modes to dropdown index: disabled=0, prefer=1, require=2
                encryption_mapping = {"disabled": 0, "prefer": 1, "require": 2}
                encryption_mode.set_selected(encryption_mapping.get(encryption_value, 1))

            # Scrape interval
            scrape_interval = self.get_widget("scrape_interval")
            if scrape_interval:
                scrape_interval.set_value(bittorrent_settings.get("scrape_interval_seconds", 1800))

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

            self.logger.trace(f"User agent dropdown set up with {len(user_agents)} options")

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
            # IMPORTANT: Enable the parent box first (hardcoded to sensitive=False in XML)
            self.update_widget_sensitivity("custom_agent_box", is_custom)
            self.update_widget_sensitivity("custom_user_agent", is_custom)

        except Exception as e:
            self.logger.error(f"Error updating user agent dependencies: {e}")

    def _collect_settings(self) -> Dict[str, Any]:
        """Collect current settings from BitTorrent tab widgets.

        Returns:
            Dictionary of setting_key -> value pairs for all widgets
        """
        # Collect from WIDGET_MAPPINGS
        settings = self._collect_mapped_settings()

        # Collect BitTorrent settings with proper key prefixes
        bittorrent_settings = self._collect_bittorrent_settings()
        for key, value in bittorrent_settings.items():
            settings[f"bittorrent.{key}"] = value

        self.logger.trace(f"Collected {len(settings)} settings from BitTorrent tab")
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

    def on_user_agent_changed(self, dropdown: Gtk.DropDown, param) -> None:
        """Handle user agent selection change."""
        try:
            self.update_dependencies()
            selected_index = dropdown.get_selected()

            # NOTE: Setting will be saved in batch via _collect_settings()
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
                    self.logger.trace(f"User agent will change to: {user_agent}")

        except Exception as e:
            self.logger.error(f"Error changing user agent: {e}")

    def _reset_tab_defaults(self) -> None:
        """Reset BitTorrent tab to default values."""
        try:
            # Reset protocol features - use set_switch_state for proper visual sync
            dht = self.get_widget("enable_dht")
            if dht:
                self.set_switch_state(dht, True)

            pex = self.get_widget("enable_pex")
            if pex:
                self.set_switch_state(pex, True)

            lsd = self.get_widget("enable_lsd")
            if lsd:
                self.set_switch_state(lsd, True)

            utp = self.get_widget("enable_utp")
            if utp:
                self.set_switch_state(utp, True)

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

    def update_view(self, model, torrent, attribute):
        """Update view based on model changes."""
        self.logger.trace(
            "BitTorrentTab update view",
            extra={"class_name": self.__class__.__name__},
        )
        # Store model reference for translation access
        self.model = model

        # Translate dropdown items now that we have the model
        # But prevent TranslationMixin from connecting to language-changed signal to avoid loops
        self._language_change_connected = True  # Block TranslationMixin from connecting
        self.translate_common_dropdowns()
