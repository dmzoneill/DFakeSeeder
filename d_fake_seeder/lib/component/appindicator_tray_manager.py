"""
AppIndicator3 Tray Manager for DFakeSeeder

Provides native system tray integration using AppIndicator3.
This requires libappindicator-gtk3-devel and uses GTK3 alongside the main GTK4 application.
"""

import os
from typing import Callable, Optional

from lib.logger import logger

try:
    import gi

    gi.require_version("Gtk", "3.0")  # AppIndicator3 requires GTK3
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3, GLib, Gtk

    APPINDICATOR_AVAILABLE = True
except (ImportError, ValueError) as e:
    logger.info(f"AppIndicator3 not available: {e}", extra={"class_name": "AppIndicatorTrayManager"})
    APPINDICATOR_AVAILABLE = False


class AppIndicatorTrayManager:
    """
    System tray manager using native AppIndicator3.

    Provides system tray functionality with proper menu support for GNOME Shell
    and other desktop environments that support AppIndicator/StatusNotifierItem.
    """

    def __init__(self):
        self.indicator: Optional[AppIndicator3.Indicator] = None
        self.menu: Optional[Gtk.Menu] = None
        self.is_active = False
        self.translation_func: Optional[Callable[[str], str]] = None
        self.show_window_callback: Optional[Callable] = None
        self.quit_callback: Optional[Callable] = None

        # Always log initialization with extensive debugging
        print("🔧 AppIndicatorTrayManager.__init__() - Starting initialization")
        logger.info("AppIndicatorTrayManager initialization starting", extra={"class_name": self.__class__.__name__})

        # Log environment and availability
        print(f"🔍 DFS_PATH environment: {os.environ.get('DFS_PATH', 'NOT_SET')}")
        print(f"🔍 APPINDICATOR_AVAILABLE: {APPINDICATOR_AVAILABLE}")
        dfs_path = os.environ.get("DFS_PATH", "NOT_SET")
        logger.info(
            f"Environment check - DFS_PATH: {dfs_path}, AppIndicator available: {APPINDICATOR_AVAILABLE}",
            extra={"class_name": self.__class__.__name__},
        )

        print("✅ AppIndicatorTrayManager initialization completed")
        logger.info("AppIndicatorTrayManager initialization completed", extra={"class_name": self.__class__.__name__})

    def is_available(self) -> bool:
        """Check if AppIndicator3 is available on this system."""
        print(f"🔍 is_available() called - result: {APPINDICATOR_AVAILABLE}")
        logger.debug(
            f"AppIndicator availability check: {APPINDICATOR_AVAILABLE}", extra={"class_name": self.__class__.__name__}
        )
        return APPINDICATOR_AVAILABLE

    def set_translation_function(self, translation_func: Callable[[str], str]):
        """Set the translation function for menu items."""
        print("🌍 set_translation_function() called")
        logger.info("Setting translation function for tray manager", extra={"class_name": self.__class__.__name__})

        self.translation_func = translation_func
        logger.debug("Translation function set", extra={"class_name": self.__class__.__name__})

        # Refresh menu if it exists
        if self.menu and self.is_active:
            print("🔄 Updating menu translations after function set")
            logger.debug("Updating menu translations after function set", extra={"class_name": self.__class__.__name__})
            self._update_menu_translations()
        else:
            print(f"🔍 Menu state - exists: {self.menu is not None}, active: {self.is_active}")
            logger.debug(
                f"Menu state - exists: {self.menu is not None}, active: {self.is_active}",
                extra={"class_name": self.__class__.__name__},
            )

    def set_callbacks(self, show_window_callback: Callable, quit_callback: Callable):
        """Set the callback functions for menu actions."""
        print("📞 set_callbacks() called")
        logger.info("Setting tray callback functions", extra={"class_name": self.__class__.__name__})

        self.show_window_callback = show_window_callback
        self.quit_callback = quit_callback

        show_cb = self.show_window_callback is not None
        quit_cb = self.quit_callback is not None
        print(f"✅ Callbacks set - show_window: {show_cb}, quit: {quit_cb}")
        logger.debug(
            f"Callbacks set - show_window: {show_cb}, quit: {quit_cb}",
            extra={"class_name": self.__class__.__name__},
        )

    def setup_tray(self) -> bool:
        """
        Set up the system tray indicator.

        Returns:
            bool: True if successfully set up, False otherwise
        """
        print(f"🔧 setup_tray() called - Available: {self.is_available()}")
        logger.info(
            f"Setting up system tray - available: {self.is_available()}", extra={"class_name": self.__class__.__name__}
        )

        if not self.is_available():
            print("❌ AppIndicator3 not available, cannot setup tray")
            logger.warning(
                "AppIndicator3 not available, cannot setup tray", extra={"class_name": self.__class__.__name__}
            )
            return False

        try:
            print("✅ AppIndicator3 is available, creating indicator...")
            logger.info("Creating AppIndicator3.Indicator", extra={"class_name": self.__class__.__name__})

            # Get default icon first
            default_icon = self._get_default_icon()
            print(f"🎨 Default icon determined: {default_icon}")
            logger.debug(f"Default icon: {default_icon}", extra={"class_name": self.__class__.__name__})

            # Create the indicator
            print("🏗️ Creating AppIndicator3.Indicator.new()...")
            self.indicator = AppIndicator3.Indicator.new(
                "dfakeseeder",  # Unique ID
                default_icon,  # Initial icon
                AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            )
            print("✅ AppIndicator3.Indicator.new() completed")

            logger.info("AppIndicator3.Indicator created successfully", extra={"class_name": self.__class__.__name__})

            # Set up the icon
            print("🎨 Setting up tray icon...")
            logger.debug("Setting up tray icon", extra={"class_name": self.__class__.__name__})
            self._setup_icon()

            # Create the menu
            print("📋 Creating tray menu...")
            logger.debug("Creating tray menu", extra={"class_name": self.__class__.__name__})
            self._create_menu()

            # Set status to active to show the indicator
            print("🔄 Setting indicator status to ACTIVE...")
            logger.debug("Setting indicator status to ACTIVE", extra={"class_name": self.__class__.__name__})
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
            self.is_active = True
            print("✅ Indicator status set to ACTIVE")

            print("🎯 AppIndicator tray setup completed successfully!")
            logger.info("AppIndicator tray setup completed successfully", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            print(f"💥 EXCEPTION in setup_tray(): {e}")
            logger.error(
                f"Error setting up AppIndicator tray: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            return False

    def _get_default_icon(self) -> str:
        """Get the default icon name or path."""
        print("🎨 _get_default_icon() called")
        logger.debug("Getting default icon for tray", extra={"class_name": self.__class__.__name__})

        # Try custom icon first, then fallback to system icon
        dfs_path = os.environ.get("DFS_PATH", "")
        custom_icon_path = os.path.join(dfs_path, "images", "dfakeseeder.png")

        print(f"🔍 Checking custom icon path: {custom_icon_path}")
        logger.debug(f"Checking custom icon path: {custom_icon_path}", extra={"class_name": self.__class__.__name__})

        if os.path.exists(custom_icon_path):
            print(f"✅ Found custom icon: {custom_icon_path}")
            logger.debug(f"Using custom icon: {custom_icon_path}", extra={"class_name": self.__class__.__name__})
            return custom_icon_path

        fallback_icon = "application-default-icon"
        print(f"⚠️ Custom icon not found, using fallback: {fallback_icon}")
        logger.debug(
            f"Custom icon not found, using fallback: {fallback_icon}", extra={"class_name": self.__class__.__name__}
        )
        return fallback_icon

    def _setup_icon(self):
        """Set up the tray icon."""
        print("🎨 _setup_icon() called")
        logger.debug("Setting up tray icon", extra={"class_name": self.__class__.__name__})

        if not self.indicator:
            print("❌ No indicator available for icon setup")
            logger.warning("No indicator available for icon setup", extra={"class_name": self.__class__.__name__})
            return

        try:
            # Try to find the DFakeSeeder icon
            icon_paths = [
                os.path.join(os.environ.get("DFS_PATH", ""), "images", "dfakeseeder.png"),
                os.path.expanduser("~/.local/share/icons/hicolor/48x48/apps/dfakeseeder.png"),
                "/usr/share/icons/hicolor/48x48/apps/dfakeseeder.png",
            ]

            print(f"🔍 Checking {len(icon_paths)} possible icon paths:")
            for i, path in enumerate(icon_paths, 1):
                print(f"   {i}. {path}")
            logger.debug(f"Checking icon paths: {icon_paths}", extra={"class_name": self.__class__.__name__})

            for icon_path in icon_paths:
                print(f"🔍 Checking icon path: {icon_path}")
                if os.path.exists(icon_path):
                    print(f"✅ Found icon at: {icon_path}")
                    logger.debug(f"Found icon at: {icon_path}", extra={"class_name": self.__class__.__name__})

                    # For file paths, use set_icon_full
                    print(f"🎨 Setting icon with set_icon_full(): {icon_path}")
                    self.indicator.set_icon_full(icon_path, "D' Fake Seeder")
                    print(f"✅ Icon set successfully: {icon_path}")
                    logger.info(f"Icon set successfully: {icon_path}", extra={"class_name": self.__class__.__name__})
                    return
                else:
                    print(f"❌ Icon not found at: {icon_path}")

            # Use fallback icon name
            fallback_icon = "application-default-icon"
            print(f"⚠️ No custom icons found, using fallback: {fallback_icon}")
            logger.debug(
                f"No custom icons found, using fallback: {fallback_icon}", extra={"class_name": self.__class__.__name__}
            )

            print(f"🎨 Setting fallback icon with set_icon(): {fallback_icon}")
            self.indicator.set_icon(fallback_icon)
            print(f"✅ Fallback icon set: {fallback_icon}")
            logger.debug("Fallback icon set", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            print(f"💥 EXCEPTION in _setup_icon(): {e}")
            logger.error(f"Error setting up icon: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)

    def _create_menu(self):
        """Create the context menu for the indicator."""
        print("📋 _create_menu() called")
        logger.debug("Creating tray context menu", extra={"class_name": self.__class__.__name__})

        if not self.indicator:
            print("❌ No indicator available for menu creation")
            logger.warning("No indicator available for menu creation", extra={"class_name": self.__class__.__name__})
            return

        try:
            print("🏗️ Creating Gtk.Menu()...")
            self.menu = Gtk.Menu()
            print("✅ Gtk.Menu() created")

            # Show D' Fake Seeder item
            show_label = self._translate("Show D' Fake Seeder")
            print(f"📝 Creating 'Show' menu item: '{show_label}'")
            show_item = Gtk.MenuItem(label=show_label)
            show_item.connect("activate", self._on_show_window)
            self.menu.append(show_item)
            print("✅ 'Show' menu item added")

            # Separator
            print("➖ Adding separator 1")
            separator1 = Gtk.SeparatorMenuItem()
            self.menu.append(separator1)

            # Status item (disabled)
            status_label = self._translate("Status: Running")
            print(f"📝 Creating 'Status' menu item: '{status_label}'")
            status_item = Gtk.MenuItem(label=status_label)
            status_item.set_sensitive(False)
            self.menu.append(status_item)
            print("✅ 'Status' menu item added (disabled)")

            # Separator
            print("➖ Adding separator 2")
            separator2 = Gtk.SeparatorMenuItem()
            self.menu.append(separator2)

            # Quit item
            quit_label = self._translate("Quit")
            print(f"📝 Creating 'Quit' menu item: '{quit_label}'")
            quit_item = Gtk.MenuItem(label=quit_label)
            quit_item.connect("activate", self._on_quit)
            self.menu.append(quit_item)
            print("✅ 'Quit' menu item added")

            # Show all menu items
            print("👁️ Calling menu.show_all()...")
            self.menu.show_all()
            print("✅ Menu items shown")

            # Set the menu on the indicator
            print("🔗 Setting menu on indicator...")
            self.indicator.set_menu(self.menu)
            print("✅ Menu attached to indicator")

            logger.info(
                "Menu created and attached to indicator successfully", extra={"class_name": self.__class__.__name__}
            )

        except Exception as e:
            print(f"💥 EXCEPTION in _create_menu(): {e}")
            logger.error(f"Error creating menu: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)

    def _translate(self, text: str) -> str:
        """Translate text using the provided translation function."""
        result = text
        if self.translation_func:
            result = self.translation_func(text)
            print(f"🌍 Translated '{text}' -> '{result}'")
            logger.debug(f"Translated '{text}' -> '{result}'", extra={"class_name": self.__class__.__name__})
        else:
            print(f"🌍 No translation function, using original: '{text}'")
            logger.debug(
                f"No translation function, using original: '{text}'", extra={"class_name": self.__class__.__name__}
            )
        return result

    def _update_menu_translations(self):
        """Update menu item translations."""
        if not self.menu:
            return

        try:
            menu_items = self.menu.get_children()
            if len(menu_items) >= 3:
                # Update translatable menu items
                show_item = menu_items[0]
                status_item = menu_items[2]
                quit_item = menu_items[4] if len(menu_items) > 4 else None

                show_item.set_label(self._translate("Show D' Fake Seeder"))
                status_item.set_label(self._translate("Status: Running"))
                if quit_item:
                    quit_item.set_label(self._translate("Quit"))

                logger.debug("Menu translations updated", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error updating menu translations: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def _on_show_window(self, widget):
        """Handle show window request."""
        print("👆 _on_show_window() called - User clicked 'Show' in tray menu")
        logger.info("Show window requested from AppIndicator menu", extra={"class_name": self.__class__.__name__})

        if self.show_window_callback:
            print("📞 Calling show_window_callback via GLib.idle_add")
            logger.debug(
                "Calling show_window_callback via GLib.idle_add", extra={"class_name": self.__class__.__name__}
            )
            # Use GLib.idle_add to safely call GTK4 code from GTK3 context
            GLib.idle_add(self.show_window_callback)
            print("✅ show_window_callback scheduled")
        else:
            print("❌ No show_window_callback available!")
            logger.warning("No show_window_callback available", extra={"class_name": self.__class__.__name__})

    def _on_quit(self, widget):
        """Handle quit request."""
        print("👆 _on_quit() called - User clicked 'Quit' in tray menu")
        logger.info("Quit requested from AppIndicator menu", extra={"class_name": self.__class__.__name__})

        if self.quit_callback:
            print("📞 Calling quit_callback via GLib.idle_add")
            logger.debug("Calling quit_callback via GLib.idle_add", extra={"class_name": self.__class__.__name__})
            # Use GLib.idle_add to safely call GTK4 code from GTK3 context
            GLib.idle_add(self.quit_callback)
            print("✅ quit_callback scheduled")
        else:
            print("❌ No quit_callback available!")
            logger.warning("No quit_callback available", extra={"class_name": self.__class__.__name__})

    def update_status(self, status_text: str):
        """Update the status text in the menu."""
        print(f"📊 update_status() called with: '{status_text}'")
        logger.debug(f"Updating tray status to: {status_text}", extra={"class_name": self.__class__.__name__})

        if not self.menu:
            print("❌ No menu available for status update")
            logger.warning("No menu available for status update", extra={"class_name": self.__class__.__name__})
            return

        try:
            menu_items = self.menu.get_children()
            print(f"🔍 Menu has {len(menu_items)} items")

            if len(menu_items) >= 3:
                status_item = menu_items[2]
                new_label = self._translate(f"Status: {status_text}")
                print(f"📝 Setting status item label to: '{new_label}'")
                status_item.set_label(new_label)
                print(f"✅ Status updated successfully: {status_text}")
                logger.info(f"Status updated: {status_text}", extra={"class_name": self.__class__.__name__})
            else:
                print(f"❌ Not enough menu items ({len(menu_items)}) to update status")
                logger.warning(
                    f"Not enough menu items ({len(menu_items)}) to update status",
                    extra={"class_name": self.__class__.__name__},
                )

        except Exception as e:
            print(f"💥 EXCEPTION in update_status(): {e}")
            logger.error(f"Error updating status: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)

    def hide_tray(self):
        """Hide the tray indicator."""
        print("🙈 hide_tray() called")
        logger.debug("Hiding tray indicator", extra={"class_name": self.__class__.__name__})

        if self.indicator and self.is_active:
            try:
                print("🔄 Setting indicator status to PASSIVE")
                self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
                self.is_active = False
                print("✅ Tray indicator hidden")
                logger.info("Tray indicator hidden", extra={"class_name": self.__class__.__name__})
            except Exception as e:
                print(f"💥 EXCEPTION in hide_tray(): {e}")
                logger.error(f"Error hiding tray: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)
        else:
            print(f"❌ Cannot hide tray - indicator: {self.indicator is not None}, active: {self.is_active}")
            logger.warning(
                f"Cannot hide tray - indicator: {self.indicator is not None}, active: {self.is_active}",
                extra={"class_name": self.__class__.__name__},
            )

    def show_tray(self):
        """Show the tray indicator."""
        print("👁️ show_tray() called")
        logger.debug("Showing tray indicator", extra={"class_name": self.__class__.__name__})

        if self.indicator and not self.is_active:
            try:
                print("🔄 Setting indicator status to ACTIVE")
                self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
                self.is_active = True
                print("✅ Tray indicator shown")
                logger.info("Tray indicator shown", extra={"class_name": self.__class__.__name__})
            except Exception as e:
                print(f"💥 EXCEPTION in show_tray(): {e}")
                logger.error(f"Error showing tray: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)
        else:
            print(f"❌ Cannot show tray - indicator: {self.indicator is not None}, active: {self.is_active}")
            logger.warning(
                f"Cannot show tray - indicator: {self.indicator is not None}, active: {self.is_active}",
                extra={"class_name": self.__class__.__name__},
            )

    def cleanup(self):
        """Clean up the tray manager."""
        print("🧹 cleanup() called")
        logger.info("Cleaning up tray manager", extra={"class_name": self.__class__.__name__})

        try:
            if self.indicator and self.is_active:
                print("🔄 Setting indicator status to PASSIVE before cleanup")
                self.indicator.set_status(AppIndicator3.IndicatorStatus.PASSIVE)
                print("✅ Indicator set to PASSIVE")

            print("🗑️ Clearing indicator and menu references")
            self.indicator = None
            self.menu = None
            self.is_active = False
            print("✅ References cleared")

            print("✅ AppIndicator tray manager cleanup completed")
            logger.info("AppIndicator tray manager cleaned up", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            print(f"💥 EXCEPTION in cleanup(): {e}")
            logger.error(f"Error during cleanup: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)
