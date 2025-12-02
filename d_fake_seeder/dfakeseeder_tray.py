#!/usr/bin/env python3
"""
DFakeSeeder System Tray Application

Comprehensive system tray interface for DFakeSeeder with full feature support.
Communicates with main application via D-Bus for settings management.
"""
# isort: skip_file

# fmt: off
import json
import os
import signal
import sys
from typing import Any

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("AppIndicator3", "0.1")
gi.require_version("Notify", "0.7")
gi.require_version("Gio", "2.0")

# isort: split
# GTK3 translation manager must be imported before gi.repository to prevent version conflicts
from d_fake_seeder.domain.translation_manager.gtk3_implementation import (  # noqa: E402
    TranslationManagerGTK3,
)

# isort: split
# gi.repository imports after translation manager to maintain GTK version isolation
from gi.repository import AppIndicator3, Gio, GLib, Gtk, Notify  # noqa: E402

from d_fake_seeder.lib.dbus_client import DBusClient  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402
from d_fake_seeder.lib.util.language_config import (  # noqa: E402
    get_language_display_names,
    get_supported_language_codes,
)
from d_fake_seeder.lib.util.single_instance import MultiMethodSingleInstance  # noqa: E402

# fmt: on


class TrayApplication:
    """Main tray application with comprehensive menu system"""

    def __init__(self, instance_checker=None):
        logger.debug(
            "Initializing TrayApplication",
            extra={"class_name": self.__class__.__name__},
        )

        # Store instance checker for cleanup
        self.instance_checker = instance_checker

        # Initialize components
        self.indicator = None
        self.menu = None
        self.dbus_client = None
        self.translation_manager = None
        self._ = None
        self.settings_cache = {}

        # Menu item references for dynamic updates
        self.menu_items = {}

        # Connection state
        self.connected = False
        self.update_timer = None
        self.dbus_handlers_setup = False

        # Menu caching to avoid full rebuilds
        self.menu_structure_cached = False
        self.last_connection_state = None

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Initialize notification system
        Notify.init("DFakeSeeder")

    def run(self):
        """Start the tray application"""
        logger.info("Starting tray application", extra={"class_name": self.__class__.__name__})

        if not self._initialize():
            logger.error(
                "Failed to initialize tray application",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        try:
            Gtk.main()
        except KeyboardInterrupt:
            logger.info(
                "Tray application interrupted",
                extra={"class_name": self.__class__.__name__},
            )
        finally:
            self.quit()

        return True

    def _initialize(self) -> bool:
        """Initialize tray application components"""
        try:
            # Create system tray indicator
            self._create_indicator()

            # Initialize D-Bus connection
            self._connect_to_dbus()

            # Load initial settings from main app (not from file!)
            self._load_initial_settings()

            # Initialize translation manager with language from D-Bus settings
            # Do NOT let it access AppSettings/file system - only use D-Bus cache
            self._setup_translations()
            logger.debug(
                "Translation manager initialized",
                extra={"class_name": self.__class__.__name__},
            )

            # Create menu
            self._create_menu()

            # Set up D-Bus signal handlers
            if self.connected:
                self._setup_dbus_handlers()

            # Start periodic updates
            self._start_update_timer()

            return True

        except Exception as e:
            logger.error(
                f"Failed to initialize tray application: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _setup_translations(self):
        """Setup GTK3 TranslationManager for tray application"""
        try:
            # Create GTK3 translation manager
            localedir = os.path.join(os.environ.get("DFS_PATH", "."), "components", "locale")
            self.translation_manager = TranslationManagerGTK3(
                domain="dfakeseeder",
                localedir=localedir,
                fallback_language="en",
            )

            # Get language from D-Bus settings cache (NOT from AppSettings file!)
            # This avoids race conditions with the main app
            target_language = self.settings_cache.get("language", "auto")

            # Handle "auto" by detecting system language
            if target_language == "auto":
                import locale

                try:
                    current_locale = locale.getlocale()[0]
                    system_locale = current_locale if current_locale else locale.getdefaultlocale()[0]
                    if system_locale:
                        target_language = system_locale.split("_")[0].lower()
                    else:
                        target_language = "en"
                except Exception:
                    target_language = "en"

            logger.debug(
                f"Tray using language from D-Bus cache: {target_language}",
                extra={"class_name": self.__class__.__name__},
            )

            # Switch to the language from D-Bus settings (no auto-detect to avoid AppSettings)
            self.translation_manager.switch_language(target_language)
            self._ = self.translation_manager.get_translate_func()

            logger.debug(
                "GTK3 TranslationManager initialized for tray",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.warning(
                f"Could not setup GTK3 TranslationManager: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self._ = lambda x: x  # Fallback function

    def _switch_language(self, language_code: str):
        """Switch to a different language using GTK3 TranslationManager"""
        try:
            if self.translation_manager:
                actual_language = self.translation_manager.switch_language(language_code)
                self._ = self.translation_manager.get_translate_func()
                logger.debug(
                    f"Tray switched to language: {actual_language}",
                    extra={"class_name": self.__class__.__name__},
                )
                return actual_language
            else:
                logger.warning(
                    "TranslationManager not available for language switch",
                    extra={"class_name": self.__class__.__name__},
                )
                return "en"
        except Exception as e:
            logger.warning(
                f"Could not switch to language {language_code}: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return "en"

    def _create_indicator(self):
        """Create AppIndicator3 system tray indicator"""
        try:
            self.indicator = AppIndicator3.Indicator.new(
                "dfakeseeder-tray",
                "dfakeseeder-idle",  # Default icon
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )

            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.indicator.set_title("DFakeSeeder")
            # Don't set label - we want only the icon to show

            # Set icon using absolute path to dfakeseeder.png
            dfs_path = os.environ.get("DFS_PATH", ".")
            icon_path = os.path.join(dfs_path, "components", "images", "dfakeseeder.png")

            if os.path.exists(icon_path):
                self.indicator.set_icon_full(icon_path, "DFakeSeeder")
                logger.debug(
                    f"Using tray icon from: {icon_path}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                # Try system icon theme as fallback
                icon_theme = Gtk.IconTheme.get_default()
                if icon_theme.has_icon("dfakeseeder"):
                    self.indicator.set_icon("dfakeseeder")
                    logger.debug(
                        "Using system theme dfakeseeder icon",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    # Final fallback to generic icon
                    self.indicator.set_icon("application-default-icon")
                    logger.warning(
                        "Using fallback icon - dfakeseeder icon not found",
                        extra={"class_name": self.__class__.__name__},
                    )

            logger.debug(
                "System tray indicator created",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to create indicator: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _connect_to_dbus(self):
        """Connect to D-Bus service (reconnection handled by periodic update)"""
        try:
            self.dbus_client = DBusClient()
            self.connected = self.dbus_client.connected

            if self.connected:
                logger.debug(
                    "Connected to main application via D-Bus",
                    extra={"class_name": self.__class__.__name__},
                )
                self._update_indicator_status(True)
            else:
                logger.debug(
                    "Failed to connect to main application",
                    extra={"class_name": self.__class__.__name__},
                )
                self._update_indicator_status(False)
                # Note: Reconnection is handled by _periodic_update, no need for separate timer

        except Exception as e:
            logger.error(
                f"D-Bus connection error: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self.connected = False
            self._update_indicator_status(False)

    def _update_indicator_status(self, connected: bool):
        """Update indicator icon based on connection status"""
        try:
            if self.indicator:
                # Use the same dfakeseeder icon for all states (can be enhanced later with different state icons)
                dfs_path = os.environ.get("DFS_PATH", ".")
                icon_path = os.path.join(dfs_path, "components", "images", "dfakeseeder.png")

                if os.path.exists(icon_path):
                    self.indicator.set_icon_full(icon_path, "DFakeSeeder")
                else:
                    # Fallback to theme icon
                    icon_theme = Gtk.IconTheme.get_default()
                    if icon_theme.has_icon("dfakeseeder"):
                        self.indicator.set_icon("dfakeseeder")
                    else:
                        self.indicator.set_icon("application-default-icon")

                # Update tooltip to reflect status
                if connected:
                    seeding_paused = self.settings_cache.get("seeding_paused", False)
                    status_text = "DFakeSeeder - Paused" if seeding_paused else "DFakeSeeder - Active"
                else:
                    status_text = "DFakeSeeder - Disconnected"

                self.indicator.set_title(status_text)

        except Exception as e:
            logger.error(
                f"Failed to update indicator status: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _load_initial_settings(self):
        """Load initial settings cache from main app"""
        try:
            if self.dbus_client:
                settings_json = self.dbus_client.get_settings()
                if settings_json:
                    self.settings_cache = json.loads(settings_json)
                    logger.debug(
                        f"Loaded {len(self.settings_cache)} settings",
                        extra={"class_name": self.__class__.__name__},
                    )
        except Exception as e:
            logger.error(
                f"Could not load initial settings: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _setup_dbus_handlers(self):
        """Set up D-Bus signal handlers (only once to avoid duplicate subscriptions)"""
        try:
            # Only subscribe once to avoid duplicate signal handlers
            if not self.dbus_handlers_setup:
                self.dbus_client.subscribe("SettingsChanged", self._on_settings_changed)
                self.dbus_handlers_setup = True
                logger.debug(
                    "D-Bus signal handlers set up",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.debug(
                    "D-Bus handlers already set up, skipping",
                    extra={"class_name": self.__class__.__name__},
                )
        except Exception as e:
            logger.error(
                f"Could not set up D-Bus handlers: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_settings_changed(
        self,
        connection,
        sender,
        object_path,
        interface_name,
        signal_name,
        parameters,
        user_data,
    ):
        """Handle settings changes from main app"""
        try:
            changes_json = parameters.unpack()[0] if parameters else "{}"
            changes = json.loads(changes_json)

            # Check for language changes first (before updating cache)
            language_changed = False
            if "language" in changes:
                logger.debug(
                    f"Language change detected in tray: {changes['language']}",
                    extra={"class_name": self.__class__.__name__},
                )
                language_changed = True
                new_language = changes["language"]

            # Update local cache
            for key, value in changes.items():
                self._update_cache_value(key, value)

            # Handle language change
            if language_changed:
                self._handle_language_change(new_language)
            else:
                # Regular menu update
                self._update_menu()

            # Update indicator status
            self._update_indicator_status(True)

        except Exception as e:
            logger.error(
                f"Error handling settings change: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _update_cache_value(self, key: str, value: Any):
        """Update a value in the settings cache"""
        if "." in key:
            # Handle nested keys
            keys = key.split(".")
            current = self.settings_cache
            for k in keys[:-1]:
                current = current.setdefault(k, {})
            current[keys[-1]] = value
        else:
            self.settings_cache[key] = value

    def _handle_language_change(self, new_language: str):
        """Handle language change by updating translations and recreating menu"""
        try:
            logger.debug(
                f"Tray handling language change to: {new_language}",
                extra={"class_name": self.__class__.__name__},
            )

            # Switch language using TranslationManager
            if self.translation_manager:
                actual_language = self._switch_language(new_language)
                logger.debug(
                    f"Tray TranslationManager switched to: {actual_language}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    "TranslationManager not available for language change",
                    extra={"class_name": self.__class__.__name__},
                )

            # Recreate entire menu with new translations
            self._recreate_menu_with_translations()

        except Exception as e:
            logger.error(
                f"Error handling language change in tray: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _recreate_menu_with_translations(self):
        """Recreate the entire menu with updated translations"""
        try:
            logger.debug(
                "Recreating tray menu with new translations",
                extra={"class_name": self.__class__.__name__},
            )

            # Invalidate menu cache to force full rebuild with new translations
            self.menu_structure_cached = False

            # Clear the existing menu
            if self.menu:
                # Remove all items
                for child in self.menu.get_children():
                    self.menu.remove(child)

            # Recreate menu with new translations
            self._create_menu()

            logger.debug(
                "Tray menu recreated with new translations",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Error recreating tray menu: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _create_menu(self):
        """Create tray context menu with localized strings (minimal when disconnected)"""
        # Check if full rebuild is needed based on connection state change
        connection_state_changed = self.last_connection_state != self.connected

        # Only rebuild menu structure if connection state changed or not yet cached
        if not self.menu_structure_cached or connection_state_changed:
            logger.debug(
                f"Full menu rebuild (cached={self.menu_structure_cached}, "
                f"state_changed={connection_state_changed})",
                extra={"class_name": self.__class__.__name__},
            )
            self._rebuild_menu_structure()
            self.menu_structure_cached = True
            self.last_connection_state = self.connected
        else:
            # Menu structure is cached, just update dynamic values
            logger.debug(
                "Using cached menu, updating dynamic values only",
                extra={"class_name": self.__class__.__name__},
            )
            self._update_menu()

    def _rebuild_menu_structure(self):
        """Rebuild the complete menu structure (expensive operation)"""
        self.menu = Gtk.Menu()

        # Get translation function
        _ = self._ or (lambda x: x)

        # Connection status
        if self.connected:
            status_item = Gtk.MenuItem(label=_("Connected to DFakeSeeder"))
            status_item.set_sensitive(False)
            self.menu.append(status_item)

            # When connected, show all menu sections
            # Separator
            self.menu.append(Gtk.SeparatorMenuItem())

            # Speed control section
            self._create_speed_menu_section(_)

            # Separator
            self.menu.append(Gtk.SeparatorMenuItem())

            # Seeding control section
            self._create_seeding_menu_section(_)

            # Separator
            self.menu.append(Gtk.SeparatorMenuItem())

            # Window management section
            self._create_window_menu_section(_)

            # Separator
            self.menu.append(Gtk.SeparatorMenuItem())

            # Language selection
            self._create_language_menu_section(_)

            # Separator
            self.menu.append(Gtk.SeparatorMenuItem())

            # Application actions (includes preferences, about, quit)
            self._create_app_menu_section(_)
        else:
            # When disconnected, show minimal menu
            status_item = Gtk.MenuItem(label=_("Disconnected from DFakeSeeder"))
            status_item.set_sensitive(False)
            self.menu.append(status_item)

            # Separator
            self.menu.append(Gtk.SeparatorMenuItem())

            # Launch Main App option
            launch_item = Gtk.MenuItem(label=_("Launch Main Application"))
            launch_item.connect("activate", self._launch_main_app)
            self.menu.append(launch_item)

            # Separator
            self.menu.append(Gtk.SeparatorMenuItem())

            # Only show Quit option when disconnected
            quit_item = Gtk.MenuItem(label=_("Quit DFakeSeeder"))
            quit_item.connect("activate", self._on_quit_tray_only)
            self.menu.append(quit_item)

        # Show all menu items
        self.menu.show_all()

        # Register menu items for translation if TranslationManager supports it
        if self.translation_manager and hasattr(self.translation_manager, "register_simple_text"):
            logger.debug(
                "Menu items could be registered for automatic translation",
                extra={"class_name": self.__class__.__name__},
            )

        # Set menu on indicator
        if self.indicator:
            self.indicator.set_menu(self.menu)

    def _create_speed_menu_section(self, _):
        """Create speed control menu section"""
        # Speed control submenu
        speed_item = Gtk.MenuItem(label=_("Speed Control"))
        speed_submenu = Gtk.Menu()

        # Normal/Alternative speed toggle
        alt_speed_enabled = self.settings_cache.get("alternative_speed_enabled", False)
        speed_toggle = Gtk.CheckMenuItem(label=_("Alternative Speed Limits"))
        speed_toggle.set_active(alt_speed_enabled)
        speed_toggle.connect("toggled", self._on_speed_toggle)
        self.menu_items["speed_toggle"] = speed_toggle
        speed_submenu.append(speed_toggle)

        # Speed values display
        if alt_speed_enabled:
            up_speed = self.settings_cache.get("alternative_upload_speed", 25)
            down_speed = self.settings_cache.get("alternative_download_speed", 100)
        else:
            up_speed = self.settings_cache.get("upload_speed", 50)
            down_speed = self.settings_cache.get("download_speed", 500)

        speed_info = Gtk.MenuItem(label=f"↑ {up_speed} KB/s  ↓ {down_speed} KB/s")
        speed_info.set_sensitive(False)
        self.menu_items["speed_info"] = speed_info
        speed_submenu.append(speed_info)

        speed_item.set_submenu(speed_submenu)
        self.menu.append(speed_item)

    def _create_seeding_menu_section(self, _):
        """Create seeding control menu section"""
        # Pause/Resume all seeding
        seeding_paused = self.settings_cache.get("seeding_paused", False)
        if seeding_paused:
            pause_item = Gtk.MenuItem(label=_("Resume All Torrents"))
        else:
            pause_item = Gtk.MenuItem(label=_("Pause All Torrents"))
        pause_item.connect("activate", self._on_pause_toggle)
        self.menu_items["pause_toggle"] = pause_item
        self.menu.append(pause_item)

        # Seeding profile submenu
        profile_item = Gtk.MenuItem(label=_("Seeding Profile"))
        profile_submenu = Gtk.Menu()

        current_profile = self.settings_cache.get("current_seeding_profile", "balanced")
        profiles = [
            ("conservative", _("Conservative")),
            ("balanced", _("Balanced")),
            ("aggressive", _("Aggressive")),
        ]

        profile_group = None
        for profile_id, profile_name in profiles:
            profile_radio = Gtk.RadioMenuItem(group=profile_group, label=profile_name)
            if profile_group is None:
                profile_group = profile_radio
            profile_radio.set_active(profile_id == current_profile)
            profile_radio.connect("toggled", self._on_profile_change, profile_id)
            profile_submenu.append(profile_radio)

        profile_item.set_submenu(profile_submenu)
        self.menu.append(profile_item)

    def _create_window_menu_section(self, _):
        """Create window management menu section"""
        # Show/Hide main window
        window_visible = self.settings_cache.get("window_visible", True)
        if window_visible:
            window_item = Gtk.MenuItem(label=_("Hide Main Window"))
        else:
            window_item = Gtk.MenuItem(label=_("Show Main Window"))
        window_item.connect("activate", self._on_window_toggle)
        self.menu_items["window_toggle"] = window_item
        self.menu.append(window_item)

    def _create_language_menu_section(self, _):
        """Create language selection menu section"""
        lang_item = Gtk.MenuItem(label=_("Language"))
        lang_submenu = Gtk.Menu()

        current_language = self.settings_cache.get("language", "auto")

        # Get available languages from centralized config
        try:
            language_codes = get_supported_language_codes()
            language_names = get_language_display_names(use_native_names=True)

            # Build language list with auto-detect option first
            languages = [("auto", _("Auto Detect"))]
            for lang_code in language_codes:
                lang_name = language_names.get(lang_code, lang_code.upper())
                languages.append((lang_code, lang_name))

            logger.debug(
                f"Loaded {len(languages)} languages for tray menu",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Error loading language config, using minimal fallback: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            # Minimal fallback if config loading fails
            languages = [
                ("auto", _("Auto Detect")),
                ("en", "English"),
            ]

        lang_group = None
        for lang_code, lang_name in languages:
            lang_radio = Gtk.RadioMenuItem(group=lang_group, label=lang_name)
            if lang_group is None:
                lang_group = lang_radio
            lang_radio.set_active(lang_code == current_language)
            lang_radio.connect("toggled", self._on_language_change, lang_code)
            lang_submenu.append(lang_radio)

        lang_item.set_submenu(lang_submenu)
        self.menu.append(lang_item)

    def _create_app_menu_section(self, _):
        """Create application actions menu section"""
        # Preferences
        prefs_item = Gtk.MenuItem(label=_("Preferences"))
        prefs_item.connect("activate", self._on_show_preferences)
        self.menu.append(prefs_item)

        # About
        about_item = Gtk.MenuItem(label=_("About"))
        about_item.connect("activate", self._on_show_about)
        self.menu.append(about_item)

        # Separator
        self.menu.append(Gtk.SeparatorMenuItem())

        # Quit
        quit_item = Gtk.MenuItem(label=_("Quit DFakeSeeder"))
        quit_item.connect("activate", self._on_quit_application)
        self.menu.append(quit_item)

    def _update_menu(self):
        """Update menu items based on current settings"""
        try:
            # Update speed toggle
            if "speed_toggle" in self.menu_items:
                alt_speed_enabled = self.settings_cache.get("alternative_speed_enabled", False)
                self.menu_items["speed_toggle"].set_active(alt_speed_enabled)

            # Update speed info
            if "speed_info" in self.menu_items:
                alt_speed_enabled = self.settings_cache.get("alternative_speed_enabled", False)
                if alt_speed_enabled:
                    up_speed = self.settings_cache.get("alternative_upload_speed", 25)
                    down_speed = self.settings_cache.get("alternative_download_speed", 100)
                else:
                    up_speed = self.settings_cache.get("upload_speed", 50)
                    down_speed = self.settings_cache.get("download_speed", 500)
                self.menu_items["speed_info"].set_label(f"↑ {up_speed} KB/s  ↓ {down_speed} KB/s")

            # Update pause toggle
            if "pause_toggle" in self.menu_items:
                _ = self._ or (lambda x: x)
                seeding_paused = self.settings_cache.get("seeding_paused", False)
                if seeding_paused:
                    self.menu_items["pause_toggle"].set_label(_("Resume All Torrents"))
                else:
                    self.menu_items["pause_toggle"].set_label(_("Pause All Torrents"))

            # Update window toggle
            if "window_toggle" in self.menu_items:
                _ = self._ or (lambda x: x)
                window_visible = self.settings_cache.get("window_visible", True)
                if window_visible:
                    self.menu_items["window_toggle"].set_label(_("Hide Main Window"))
                else:
                    self.menu_items["window_toggle"].set_label(_("Show Main Window"))

        except Exception as e:
            logger.error(
                f"Error updating menu: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    # Menu event handlers
    def _on_speed_toggle(self, menu_item):
        """Handle speed toggle"""
        try:
            enabled = menu_item.get_active()
            changes = {"alternative_speed_enabled": enabled}
            if self.dbus_client:
                self.dbus_client.update_settings(changes)
        except Exception as e:
            logger.error(
                f"Error toggling speed: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_pause_toggle(self, menu_item):
        """Handle pause/resume toggle"""
        try:
            current_paused = self.settings_cache.get("seeding_paused", False)
            changes = {"seeding_paused": not current_paused}
            if self.dbus_client:
                self.dbus_client.update_settings(changes)
        except Exception as e:
            logger.error(
                f"Error toggling pause: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_profile_change(self, menu_item, profile_id):
        """Handle seeding profile change"""
        try:
            if menu_item.get_active():
                changes = {"current_seeding_profile": profile_id}
                if self.dbus_client:
                    self.dbus_client.update_settings(changes)
        except Exception as e:
            logger.error(
                f"Error changing profile: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_window_toggle(self, menu_item):
        """Handle window visibility toggle"""
        try:
            current_visible = self.settings_cache.get("window_visible", True)
            changes = {"window_visible": not current_visible}
            if self.dbus_client:
                self.dbus_client.update_settings(changes)
        except Exception as e:
            logger.error(
                f"Error toggling window: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_language_change(self, menu_item, language_code):
        """Handle language change"""
        try:
            if menu_item.get_active():
                changes = {"language": language_code}
                if self.dbus_client:
                    self.dbus_client.update_settings(changes)
        except Exception as e:
            logger.error(
                f"Error changing language: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_show_preferences(self, menu_item):
        """Handle show preferences"""
        try:
            if not self.dbus_client or not self.dbus_client.connected:
                logger.warning(
                    "D-Bus not connected, cannot show preferences",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            # Call the dedicated ShowPreferences D-Bus method
            result = self.dbus_client.proxy.call_sync(
                "ShowPreferences",
                None,
                Gio.DBusCallFlags.NONE,
                5000,
                None,  # 5 second timeout
            )

            if result and result.unpack()[0]:
                logger.debug(
                    "Preferences dialog opened successfully",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    "Failed to open preferences dialog",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Error showing preferences: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_show_about(self, menu_item):
        """Handle show about"""
        try:
            if not self.dbus_client or not self.dbus_client.connected:
                logger.warning(
                    "D-Bus not connected, cannot show about dialog",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            # Call the dedicated ShowAbout D-Bus method
            result = self.dbus_client.proxy.call_sync(
                "ShowAbout",
                None,
                Gio.DBusCallFlags.NONE,
                5000,
                None,  # 5 second timeout
            )

            if result and result.unpack()[0]:
                logger.debug(
                    "About dialog opened successfully",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                logger.warning(
                    "Failed to open about dialog",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            logger.error(
                f"Error showing about: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _launch_main_app(self, menu_item):
        """Launch the main DFakeSeeder application"""
        try:
            import shutil
            import subprocess

            # Try multiple launch methods in order of preference
            # Note: Only methods that work in distributed/installed application
            launch_methods = [
                # Method 1: Try installed CLI command 'dfs'
                (["dfs"], "installed 'dfs' command"),
                # Method 2: Try installed CLI command 'dfakeseeder'
                (["dfakeseeder"], "installed 'dfakeseeder' command"),
                # Method 3: Run as Python module (works for both installed and development)
                ([sys.executable, "-m", "d_fake_seeder.dfakeseeder"], "Python module"),
                # Method 4: Direct script execution (development fallback)
                (
                    [sys.executable, os.path.join(os.environ.get("DFS_PATH", "."), "d_fake_seeder/dfakeseeder.py")],
                    "source script",
                ),
            ]

            launched = False
            for cmd, method_name in launch_methods:
                # Check if command exists (for CLI commands)
                if cmd[0] in ["dfs", "dfakeseeder"]:
                    if not shutil.which(cmd[0]):
                        logger.debug(
                            f"Command '{cmd[0]}' not found, trying next method",
                            extra={"class_name": self.__class__.__name__},
                        )
                        continue

                try:
                    # Launch the main app in the background
                    process = subprocess.Popen(
                        cmd,
                        cwd=os.environ.get("DFS_PATH", "."),
                        env={**os.environ, "LOG_LEVEL": "INFO"},
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )

                    logger.info(
                        f"Launched main application using {method_name} (PID: {process.pid})",
                        extra={"class_name": self.__class__.__name__},
                    )

                    # Show notification
                    notification = Notify.Notification.new(
                        "DFakeSeeder",
                        f"Launching main application...\nUsing: {method_name}",
                        "dfakeseeder",
                    )
                    notification.show()

                    # Start trying to reconnect after a delay
                    GLib.timeout_add_seconds(3, self._try_reconnect_after_launch)

                    launched = True
                    break

                except Exception as e:
                    logger.debug(
                        f"Failed to launch via {method_name}: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    continue

            if not launched:
                error_msg = "Failed to launch main application using any method"
                logger.error(error_msg, extra={"class_name": self.__class__.__name__})

                # Show error notification
                notification = Notify.Notification.new(
                    "DFakeSeeder Error", "Failed to launch main application.\nPlease start it manually.", "dialog-error"
                )
                notification.show()

        except Exception as e:
            logger.error(
                f"Failed to launch main application: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _try_reconnect_after_launch(self):
        """Try to reconnect after launching main app"""
        try:
            self._connect_to_dbus()
            return False  # Don't repeat
        except Exception as e:
            logger.debug(
                f"Reconnection after launch failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _on_quit_application(self, menu_item):
        """Handle quit application"""
        try:
            changes = {"application_quit_requested": True}
            if self.dbus_client and self.connected:
                logger.debug(
                    "🚀 TRAY QUIT: Sending quit signal to main application via D-Bus",
                    extra={"class_name": self.__class__.__name__},
                )
                try:
                    result = self.dbus_client.update_settings(changes)
                    logger.debug(
                        f"✅ TRAY QUIT: Quit signal sent successfully, result: {result}",
                        extra={"class_name": self.__class__.__name__},
                    )
                except Exception as e:
                    # Main app may disconnect immediately on quit, which is expected
                    logger.debug(
                        f"Main app disconnected during quit (expected): {e}",
                        extra={"class_name": self.__class__.__name__},
                    )

                # Give main app time to shut down, then quit tray
                GLib.timeout_add_seconds(2, self.quit)  # Increased to 2 seconds
            else:
                logger.warning(
                    "No D-Bus connection to main app, quitting tray only",
                    extra={"class_name": self.__class__.__name__},
                )
                # If not connected, just quit the tray
                self.quit()
        except Exception as e:
            logger.error(
                f"Error quitting application: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            # Fallback: quit tray anyway after a delay
            GLib.timeout_add_seconds(1, self.quit)

    def _on_quit_tray_only(self, menu_item):
        """Handle quit tray only (when main app is not running)"""
        try:
            logger.debug(
                "Quitting tray application only",
                extra={"class_name": self.__class__.__name__},
            )
            # Just quit the tray - no need to communicate with main app since it's not running
            self.quit()
        except Exception as e:
            logger.error(
                f"Error quitting tray: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _start_update_timer(self):
        """Start periodic update timer"""
        self.update_timer = GLib.timeout_add_seconds(10, self._periodic_update)

    def _periodic_update(self):
        """Periodic update function"""
        try:
            # Check connection health
            if self.connected and self.dbus_client:
                # Ping the main application to verify it's still alive
                if not self.dbus_client.ping():
                    logger.debug(
                        "Main application no longer responding, marking as disconnected",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.connected = False
                    self._update_indicator_status(False)
                    # Invalidate cache and recreate menu to show launch option
                    self.menu_structure_cached = False
                    self._create_menu()
                    # Note: periodic update will handle reconnection, no need for separate timer
            elif not self.connected:
                # Try to reconnect if we're not connected
                logger.debug(
                    "Attempting to reconnect to main application",
                    extra={"class_name": self.__class__.__name__},
                )
                # Try to reconnect using existing client or create new one
                if self.dbus_client:
                    reconnected = self.dbus_client.reconnect()
                    self.connected = self.dbus_client.connected
                else:
                    self._connect_to_dbus()
                    reconnected = self.connected

                if reconnected and self.connected:
                    logger.debug(
                        "Main application is now available, reconnected",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self._update_indicator_status(True)
                    self._setup_dbus_handlers()
                    self._load_initial_settings()
                    # Invalidate cache and recreate menu to remove launch option
                    self.menu_structure_cached = False
                    self._create_menu()

            return True  # Continue timer

        except Exception as e:
            logger.error(
                f"Error in periodic update: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return True

    def quit(self):
        """Quit the tray application"""
        logger.debug(
            "Shutting down tray application",
            extra={"class_name": self.__class__.__name__},
        )

        # Stop timers
        if self.update_timer:
            GLib.source_remove(self.update_timer)

        # Set indicator to passive
        if self.indicator:
            self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)

        # Cleanup D-Bus
        if self.dbus_client:
            self.dbus_client.cleanup()

        # Cleanup instance checker locks
        if self.instance_checker:
            self.instance_checker.cleanup()

        # Quit GTK main loop
        Gtk.main_quit()

    def _signal_handler(self, signum, frame):
        """Handle system signals"""
        logger.info(f"Received signal {signum}", extra={"class_name": self.__class__.__name__})
        GLib.idle_add(self.quit)


def _show_tray_console_message(detection_method: str):
    """Show console message when another tray instance is detected"""
    print(f"\nDFakeSeeder Tray is already running (detected via {detection_method})")
    print("Please check your system tray.\n")


def main():
    """Main entry point for tray application"""
    # ========== MULTI-METHOD SINGLE INSTANCE CHECK ==========
    # GTK3 doesn't have built-in single instance support like GTK4
    # Use D-Bus, Socket, and PID file checking
    logger.debug("Checking for existing tray instance using multi-method approach", "TrayApplication")

    # Note: Use different app_name and different D-Bus service for tray
    # Tray doesn't register D-Bus service, so we skip D-Bus check
    instance_checker = MultiMethodSingleInstance(
        app_name="dfakeseeder-tray",
        dbus_service=None,  # Tray doesn't use D-Bus service registration
        use_pidfile=True,
    )

    is_running, detected_by = instance_checker.is_already_running()

    if is_running:
        logger.info(
            f"Existing tray instance detected via {detected_by} - exiting",
            extra={"class_name": "TrayApplication"},
        )
        _show_tray_console_message(detected_by)
        instance_checker.cleanup()
        return False

    logger.debug(
        "No existing tray instance detected - proceeding with tray startup",
        "TrayApplication",
    )

    # Create and run tray application
    app = TrayApplication(instance_checker=instance_checker)
    return app.run()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
