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

    # Note: Most BitTorrent settings use manual loading/saving due to nested structure
    # and custom user agent logic
    WIDGET_MAPPINGS: list = []

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
                "enable_lpd": self.builder.get_object("settings_enable_lpd"),
                # Encryption
                "encryption_mode": self.builder.get_object("settings_encryption_mode"),
                # User agent
                "user_agent": self.builder.get_object("settings_user_agent"),
                # Section container (hardcoded to sensitive=False in XML)
                "custom_agent_box": self.builder.get_object("settings_custom_agent_box"),
                "custom_user_agent": self.builder.get_object("settings_custom_user_agent"),
                # Peer ID prefix
                "peer_id_prefix": self.builder.get_object("settings_peer_id_prefix"),
                # Announce intervals
                "announce_interval": self.builder.get_object("settings_announce_interval"),
                "min_announce_interval": self.builder.get_object("settings_min_announce_interval"),
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
            # Load BitTorrent protocol settings using nested keys
            self._load_bittorrent_settings()
            self.logger.info("BitTorrent tab settings loaded")
        except Exception as e:
            self.logger.error(f"Error loading BitTorrent tab settings: {e}")

    def _load_bittorrent_settings(self) -> None:
        """Load BitTorrent protocol settings using nested keys."""
        try:
            # Protocol features - use set_switch_state for proper visual sync
            dht = self.get_widget("enable_dht")
            if dht:
                value = self.app_settings.get("bittorrent.enable_dht", True)
                self.set_switch_state(dht, value)

            pex = self.get_widget("enable_pex")
            if pex:
                value = self.app_settings.get("bittorrent.enable_pex", True)
                self.set_switch_state(pex, value)

            lpd = self.get_widget("enable_lpd")
            if lpd:
                value = self.app_settings.get("bittorrent.enable_lpd", True)
                self.set_switch_state(lpd, value)

            # Encryption mode
            encryption_mode = self.get_widget("encryption_mode")
            if encryption_mode:
                encryption_value = self.app_settings.get("bittorrent.encryption_mode", "enabled")
                # Map encryption modes to dropdown index: disabled=0, enabled=1, forced=2
                encryption_mapping = {"disabled": 0, "enabled": 1, "forced": 2}
                encryption_mode.set_selected(encryption_mapping.get(encryption_value, 1))

            # User agent dropdown
            self._update_user_agent_dropdown()

            # Peer ID prefix
            peer_id_prefix = self.get_widget("peer_id_prefix")
            if peer_id_prefix:
                value = self.app_settings.get("bittorrent.peer_id_prefix", "-DE2003-")
                peer_id_prefix.set_text(value)

            # Announce intervals
            announce = self.get_widget("announce_interval")
            if announce:
                value = self.app_settings.get("bittorrent.announce_interval_seconds", 1800)
                announce.set_value(value)

            min_announce = self.get_widget("min_announce_interval")
            if min_announce:
                value = self.app_settings.get("bittorrent.min_announce_interval_seconds", 300)
                min_announce.set_value(value)

            scrape_interval = self.get_widget("scrape_interval")
            if scrape_interval:
                value = self.app_settings.get("bittorrent.scrape_interval_seconds", 900)
                scrape_interval.set_value(value)

        except Exception as e:
            self.logger.error(f"Error loading BitTorrent settings: {e}")

    def _setup_user_agent_dropdown(self) -> None:
        """Set up the user agent dropdown.

        Note: The dropdown model is already defined in the XML with predefined agents.
        This method just logs that setup is complete.
        """
        try:
            user_agent_dropdown = self.get_widget("user_agent")
            if not user_agent_dropdown:
                return

            # The XML already defines the dropdown model with these agents:
            # Deluge, qBittorrent, Transmission, uTorrent, Vuze, BitTorrent, rTorrent, Custom
            self.logger.trace("User agent dropdown initialized from XML model")

        except Exception as e:
            self.logger.error(f"Error setting up user agent dropdown: {e}")

    def _update_user_agent_dropdown(self) -> None:
        """Update user agent dropdown selection."""
        try:
            user_agent_dropdown = self.get_widget("user_agent")
            if not user_agent_dropdown:
                return

            current_user_agent = self.app_settings.get("bittorrent.user_agent", "Deluge/2.0.3 libtorrent/2.0.5.0")

            # The XML dropdown has these predefined agents:
            # Deluge/2.0.3, qBittorrent/4.3.1, Transmission/3.00, uTorrent/3.5.5,
            # Vuze/5.7.6.0, BitTorrent/7.10.5, rTorrent/0.9.6, Custom
            predefined_agents = [
                "Deluge/2.0.3 libtorrent/2.0.5.0",
                "qBittorrent/4.3.1",
                "Transmission/3.00",
                "uTorrent/3.5.5",
                "Vuze/5.7.6.0",
                "BitTorrent/7.10.5",
                "rTorrent/0.9.6",
            ]

            try:
                current_index = predefined_agents.index(current_user_agent)
                user_agent_dropdown.set_selected(current_index)
            except ValueError:
                # Custom user agent - select "Custom" option (index 7)
                user_agent_dropdown.set_selected(7)
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
        settings: Dict[str, Any] = {}

        # Collect BitTorrent settings with nested keys
        bittorrent_settings = self._collect_bittorrent_settings()
        settings.update(bittorrent_settings)

        self.logger.trace(f"Collected {len(settings)} settings from BitTorrent tab")
        return settings

    def _collect_bittorrent_settings(self) -> Dict[str, Any]:
        """Collect BitTorrent protocol settings with nested keys."""
        settings: Dict[str, Any] = {}

        try:
            # Protocol features
            dht = self.get_widget("enable_dht")
            if dht:
                settings["bittorrent.enable_dht"] = dht.get_active()

            pex = self.get_widget("enable_pex")
            if pex:
                settings["bittorrent.enable_pex"] = pex.get_active()

            lpd = self.get_widget("enable_lpd")
            if lpd:
                settings["bittorrent.enable_lpd"] = lpd.get_active()

            # Encryption mode
            encryption_mode = self.get_widget("encryption_mode")
            if encryption_mode:
                selected = encryption_mode.get_selected()
                encryption_modes = ["disabled", "enabled", "forced"]
                if selected < len(encryption_modes):
                    settings["bittorrent.encryption_mode"] = encryption_modes[selected]

            # User agent
            user_agent_dropdown = self.get_widget("user_agent")
            if user_agent_dropdown:
                selected_index = user_agent_dropdown.get_selected()
                if selected_index == 7:  # Custom
                    custom_user_agent = self.get_widget("custom_user_agent")
                    if custom_user_agent:
                        settings["bittorrent.user_agent"] = custom_user_agent.get_text()
                else:
                    predefined_agents = [
                        "Deluge/2.0.3 libtorrent/2.0.5.0",
                        "qBittorrent/4.3.1",
                        "Transmission/3.00",
                        "uTorrent/3.5.5",
                        "Vuze/5.7.6.0",
                        "BitTorrent/7.10.5",
                        "rTorrent/0.9.6",
                    ]
                    if selected_index < len(predefined_agents):
                        settings["bittorrent.user_agent"] = predefined_agents[selected_index]

            # Peer ID prefix
            peer_id_prefix = self.get_widget("peer_id_prefix")
            if peer_id_prefix:
                settings["bittorrent.peer_id_prefix"] = peer_id_prefix.get_text()

            # Announce intervals
            announce = self.get_widget("announce_interval")
            if announce:
                settings["bittorrent.announce_interval_seconds"] = int(announce.get_value())

            min_announce = self.get_widget("min_announce_interval")
            if min_announce:
                settings["bittorrent.min_announce_interval_seconds"] = int(min_announce.get_value())

            scrape_interval = self.get_widget("scrape_interval")
            if scrape_interval:
                settings["bittorrent.scrape_interval_seconds"] = int(scrape_interval.get_value())

        except Exception as e:
            self.logger.error(f"Error collecting BitTorrent settings: {e}")

        return settings

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

    def on_user_agent_changed(self, dropdown: Gtk.DropDown, param: Any) -> None:
        """Handle user agent selection change."""
        try:
            self.update_dependencies()
            selected_index = dropdown.get_selected()

            # NOTE: Setting will be saved in batch via _collect_settings()
            predefined_agents = [
                "Deluge/2.0.3 libtorrent/2.0.5.0",
                "qBittorrent/4.3.1",
                "Transmission/3.00",
                "uTorrent/3.5.5",
                "Vuze/5.7.6.0",
                "BitTorrent/7.10.5",
                "rTorrent/0.9.6",
            ]

            if selected_index < len(predefined_agents):
                user_agent = predefined_agents[selected_index]
                self.app_settings.set("bittorrent.user_agent", user_agent)
                self.logger.trace(f"User agent changed to: {user_agent}")
            elif selected_index == 7:  # Custom
                self.logger.trace("Custom user agent selected")

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

            lpd = self.get_widget("enable_lpd")
            if lpd:
                self.set_switch_state(lpd, True)

            # Reset encryption mode to "Enabled" (index 1)
            encryption_mode = self.get_widget("encryption_mode")
            if encryption_mode:
                encryption_mode.set_selected(1)

            # Reset user agent to default (index 0 = Deluge)
            user_agent = self.get_widget("user_agent")
            if user_agent:
                user_agent.set_selected(0)

            # Reset peer ID prefix
            peer_id_prefix = self.get_widget("peer_id_prefix")
            if peer_id_prefix:
                peer_id_prefix.set_text("-DE2003-")

            # Reset announce intervals
            announce = self.get_widget("announce_interval")
            if announce:
                announce.set_value(1800)  # 30 minutes

            min_announce = self.get_widget("min_announce_interval")
            if min_announce:
                min_announce.set_value(300)  # 5 minutes

            scrape_interval = self.get_widget("scrape_interval")
            if scrape_interval:
                scrape_interval.set_value(900)  # 15 minutes

            self.update_dependencies()
            self.show_notification("BitTorrent settings reset to defaults", "success")

        except Exception as e:
            self.logger.error(f"Error resetting BitTorrent tab to defaults: {e}")

    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
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
