#!/usr/bin/env python3
"""
Window Manager - GTK4 native window management for DFakeSeeder

Provides clean window control operations integrated with AppSettings.
Replaces external window manipulation tools with native GTK4 functionality.
"""
# isort: skip_file

# fmt: off
import os
from pathlib import Path
from typing import Any, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, Gtk  # noqa: E402

from d_fake_seeder.domain.app_settings import AppSettings  # noqa: E402
from d_fake_seeder.lib.logger import logger  # noqa: E402

# fmt: on


class WindowManager:
    """
    GTK4 native window management with AppSettings integration

    Provides clean window operations without external dependencies.
    Integrates with AppSettings for persistent window state management.
    """

    # Path to tray PID lock file
    TRAY_LOCK_FILE = "~/.config/dfakeseeder/dfakeseeder-tray.lock"

    def __init__(self, window: Optional[Gtk.Window] = None) -> None:
        """
        Initialize window manager

        Args:
            window: GTK4 window to manage (optional, can be set later)
        """
        logger.trace("Initializing WindowManager", extra={"class_name": self.__class__.__name__})

        self.window = window
        self.app_settings = AppSettings.get_instance()

        # Window state tracking - initialize with defaults
        self._last_position = (0, 0)
        self._last_size = (1024, 600)
        self._is_maximized = False
        self._is_minimized = False

        # Setup window event handlers and load state if window is provided
        if self.window:
            self._setup_window_handlers()
            self._load_window_state()

    def set_window(self, window: Gtk.Window) -> None:
        """
        Set the window to manage

        Args:
            window: GTK4 window instance
        """
        self.window = window
        self._setup_window_handlers()
        self._load_window_state()
        logger.trace("Window set for management", extra={"class_name": self.__class__.__name__})

    def is_tray_running(self) -> bool:
        """
        Check if the tray application is running.

        Uses PID file lock to detect if tray is alive.
        Returns True if tray is running and responsive, False otherwise.
        """
        try:
            lock_path = Path(os.path.expanduser(self.TRAY_LOCK_FILE))

            if not lock_path.exists():
                logger.trace(
                    "Tray lock file does not exist - tray not running",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Read PID from lock file
            try:
                pid_str = lock_path.read_text().strip()
                pid = int(pid_str)
            except (ValueError, OSError) as e:
                logger.trace(
                    f"Could not read tray PID from lock file: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Check if the process is actually running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                logger.trace(
                    f"Tray process is running (PID: {pid})",
                    extra={"class_name": self.__class__.__name__},
                )
                return True
            except OSError:
                logger.trace(
                    f"Tray process not found (stale PID: {pid})",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

        except Exception as e:
            logger.error(
                f"Error checking if tray is running: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _setup_window_handlers(self) -> None:
        """Setup window event handlers for state tracking"""
        if not self.window:
            return

        try:
            # Connect to window state change signals
            self.window.connect("notify::is-active", self._on_window_state_changed)
            self.window.connect("close-request", self._on_close_request)

            # Connect to size and position changes
            self.window.connect("notify::default-width", self._on_size_changed)
            self.window.connect("notify::default-height", self._on_size_changed)

            logger.trace(
                "Window event handlers connected",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Failed to setup window handlers: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _load_window_state(self) -> None:
        """Load saved window state from AppSettings"""
        try:
            # Check if we should remember window size
            remember_size = self.app_settings.get("remember_window_size", True)

            if remember_size:
                # Load window dimensions from saved settings
                width = self.app_settings.get("window_width", 1024)
                height = self.app_settings.get("window_height", 600)
                self._last_size = (width, height)

                # Load window position if saved
                pos_x = self.app_settings.get("window_pos_x", 0)
                pos_y = self.app_settings.get("window_pos_y", 0)
                self._last_position = (pos_x, pos_y)

                # Apply saved state if window is available
                if self.window:
                    self.window.set_default_size(width, height)

                logger.trace(
                    f"Loaded window state: size={self._last_size}, pos={self._last_position}",
                    extra={"class_name": self.__class__.__name__},
                )
            else:
                # Use default size
                self._last_size = (1024, 600)
                self._last_position = (0, 0)

                if self.window:
                    self.window.set_default_size(1024, 600)

                logger.trace(
                    "Remember window size disabled - using defaults",
                    extra={"class_name": self.__class__.__name__},
                )

            # Load window visibility state (always respected)
            visible = self.app_settings.get("window_visible", True)
            if self.window:
                # Set visibility directly without calling show()/hide() to avoid side effects during init
                self.window.set_visible(visible)

        except Exception as e:
            logger.error(
                f"Failed to load window state: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _save_window_state(self) -> None:
        """Save current window state to AppSettings"""
        try:
            logger.trace(
                "_save_window_state called",
                extra={"class_name": self.__class__.__name__},
            )

            if not self.window:
                logger.trace(
                    "No window to save state for",
                    extra={"class_name": self.__class__.__name__},
                )
                return

            # Check if we should remember window size
            remember_size = self.app_settings.get("remember_window_size", True)

            if remember_size:
                logger.trace(
                    "Getting window dimensions",
                    extra={"class_name": self.__class__.__name__},
                )
                # Save window size
                width = self.window.get_width()
                height = self.window.get_height()
                logger.trace(
                    f"Window dimensions: {width}x{height}",
                    extra={"class_name": self.__class__.__name__},
                )

                if width > 0 and height > 0:
                    self.app_settings.set("window_width", width)
                    self.app_settings.set("window_height", height)
                    self._last_size = (width, height)
                    logger.trace(
                        "Window size saved",
                        extra={"class_name": self.__class__.__name__},
                    )
            else:
                logger.trace(
                    "Remember window size disabled - skipping size save",
                    extra={"class_name": self.__class__.__name__},
                )

            # Save visibility state (always saved, not affected by remember_window_size)
            visible = self.window.get_visible()
            self.app_settings.set("window_visible", visible)
            logger.trace(
                f"Window visibility saved: {visible}",
                extra={"class_name": self.__class__.__name__},
            )

        except Exception as e:
            logger.error(
                f"Failed to save window state: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )

    def show(self) -> Any:
        """Show the window"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to show",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            self.window.set_visible(True)
            self.window.present()

            # Update settings
            self.app_settings.set("window_visible", True)

            logger.trace("Window shown", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to show window: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def hide(self) -> Any:
        """Hide the window"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to hide",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Save state before hiding
            self._save_window_state()

            self.window.set_visible(False)

            # Update settings
            self.app_settings.set("window_visible", False)

            logger.trace("Window hidden", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to hide window: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def minimize(self) -> Any:
        """Minimize the window"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to minimize",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            self.window.minimize()
            self._is_minimized = True

            # Check if we should minimize to tray
            minimize_to_tray = self.app_settings.get("minimize_to_tray", True)
            if minimize_to_tray:
                # Only hide to tray if tray is actually running
                if self.is_tray_running():
                    self.hide()
                    logger.trace(
                        "Window minimized to tray",
                        extra={"class_name": self.__class__.__name__},
                    )
                else:
                    logger.trace(
                        "minimize_to_tray enabled but tray not running - just minimizing",
                        extra={"class_name": self.__class__.__name__},
                    )

            logger.trace("Window minimized", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to minimize window: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def maximize(self) -> Any:
        """Maximize the window"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to maximize",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            self.window.maximize()
            self._is_maximized = True

            logger.trace("Window maximized", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to maximize window: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def unmaximize(self) -> Any:
        """Restore window from maximized state"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to unmaximize",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            self.window.unmaximize()
            self._is_maximized = False

            logger.trace("Window unmaximized", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to unmaximize window: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def toggle_visibility(self) -> Any:
        """Toggle window visibility (show/hide)"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to toggle",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            if self.window.get_visible():
                return self.hide()
            else:
                return self.show()

        except Exception as e:
            logger.error(
                f"Failed to toggle window visibility: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def toggle_maximize(self) -> Any:
        """Toggle window maximized state"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to toggle maximize",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            if self._is_maximized:
                return self.unmaximize()
            else:
                return self.maximize()

        except Exception as e:
            logger.error(
                f"Failed to toggle window maximize: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def restore(self) -> Any:
        """Restore window to normal state (not minimized, not maximized)"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to restore",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Show window if hidden
            if not self.window.get_visible():
                self.show()

            # Unmaximize if maximized
            if self._is_maximized:
                self.unmaximize()

            # Present to bring to front
            self.window.present()

            self._is_minimized = False

            logger.trace("Window restored", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Failed to restore window: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def center_on_screen(self) -> Any:
        """Center window on the current monitor"""
        try:
            if not self.window:
                logger.warning(
                    "No window available to center",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Get the display and monitor
            display = Gdk.Display.get_default()
            if not display:
                logger.warning(
                    "No display available",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            surface = self.window.get_surface()
            if not surface:
                logger.warning(
                    "No surface available for window",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            monitor = display.get_monitor_at_surface(surface)
            if not monitor:
                # Fallback to primary monitor
                monitor = display.get_monitors().get_item(0)

            if monitor:
                geometry = monitor.get_geometry()
                window_width, window_height = self._last_size

                # Calculate center position
                center_x = geometry.x + (geometry.width - window_width) // 2
                center_y = geometry.y + (geometry.height - window_height) // 2

                # Note: GTK4 doesn't have set_position, but we can save the position
                self._last_position = (center_x, center_y)

                # Only save position if remember_window_size is enabled
                remember_size = self.app_settings.get("remember_window_size", True)
                if remember_size:
                    self.app_settings.set("window_pos_x", center_x)
                    self.app_settings.set("window_pos_y", center_y)

                logger.trace(
                    f"Window position set to center: ({center_x}, {center_y})",
                    extra={"class_name": self.__class__.__name__},
                )
                return True

        except Exception as e:
            logger.error(
                f"Failed to center window: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _on_window_state_changed(self, window: Any, pspec: Any) -> None:
        """Handle window state changes"""
        try:
            # Save current state
            self._save_window_state()
        except Exception as e:
            logger.error(
                f"Error handling window state change: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_size_changed(self, window: Any, pspec: Any) -> None:
        """Handle window size changes"""
        try:
            # Save current size
            self._save_window_state()
        except Exception as e:
            logger.error(
                f"Error handling window size change: {e}",
                extra={"class_name": self.__class__.__name__},
            )

    def _on_close_request(self, window: Any) -> Any:
        """Handle window close request"""
        try:
            # Check if we should close to tray
            close_to_tray = self.app_settings.get("close_to_tray", False)

            logger.trace(
                f"Close request received, close_to_tray={close_to_tray}",
                extra={"class_name": self.__class__.__name__},
            )

            if close_to_tray:
                # Check if tray is actually running before hiding
                if self.is_tray_running():
                    # Hide instead of closing
                    logger.info(
                        "Hiding window to tray instead of quitting",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.hide()
                    return True  # Prevent default close behavior  # type: ignore
                else:
                    # Tray is not running - close the app instead of hiding
                    logger.warning(
                        "close_to_tray enabled but tray is not running - closing app instead",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self._save_window_state()
                    return False  # Allow normal close  # type: ignore
            else:
                # Allow normal close behavior - let view.quit() handle it
                logger.trace(
                    "Allowing normal close/quit behavior",
                    extra={"class_name": self.__class__.__name__},
                )
                self._save_window_state()
                return False  # Allow other handlers to process  # type: ignore

        except Exception as e:
            logger.error(
                f"Error handling close request: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def get_window_info(self) -> dict:
        """Get current window information"""
        try:
            if not self.window:
                return {
                    "available": False,
                    "visible": False,
                    "size": self._last_size,
                    "position": self._last_position,
                }

            return {
                "available": True,
                "visible": self.window.get_visible(),
                "size": (self.window.get_width(), self.window.get_height()),
                "position": self._last_position,
                "maximized": self._is_maximized,
                "minimized": self._is_minimized,
            }

        except Exception as e:
            logger.error(
                f"Failed to get window info: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return {"available": False, "error": str(e)}

    def cleanup(self) -> Any:
        """Clean up window manager resources"""
        try:
            logger.trace(
                "WindowManager cleanup starting",
                extra={"class_name": self.__class__.__name__},
            )

            # Skip saving window state during cleanup to avoid deadlocks during shutdown
            # Window state has already been saved during normal operation
            logger.trace(
                "Skipping window state save during cleanup (already saved)",
                extra={"class_name": self.__class__.__name__},
            )

            # Clear window reference
            logger.trace(
                "Clearing window reference",
                extra={"class_name": self.__class__.__name__},
            )
            self.window = None

            logger.trace(
                "WindowManager cleaned up",
                extra={"class_name": self.__class__.__name__},
            )
        except Exception as e:
            logger.error(
                f"Error during WindowManager cleanup: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
