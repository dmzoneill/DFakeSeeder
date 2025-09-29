"""
D-Bus Tray Manager for DFakeSeeder

Manages GTK3 tray subprocess via D-Bus communication, providing system tray
functionality for the main GTK4 application without version conflicts.
"""

import os
import subprocess
import time
from typing import Callable, Optional

from lib.component.dbus_tray_server import TrayDBusServer
from lib.logger import logger


class DBusTrayManager:
    """
    D-Bus-based tray manager that spawns a GTK3 subprocess for system tray.

    Provides the same interface as AppIndicatorTrayManager but uses a separate
    GTK3 process to avoid GTK version conflicts.
    """

    def __init__(self):
        """Initialize the D-Bus tray manager."""
        self.dbus_server: Optional[TrayDBusServer] = None
        self.tray_process: Optional[subprocess.Popen] = None
        self.is_active = False
        self.translation_func: Optional[Callable[[str], str]] = None
        self.show_window_callback: Optional[Callable] = None
        self.quit_callback: Optional[Callable] = None

        logger.info("D-Bus tray manager initialized", extra={"class_name": self.__class__.__name__})

    def is_available(self) -> bool:
        """
        Check if D-Bus tray system is available.

        Returns:
            bool: True if D-Bus and required dependencies are available
        """
        try:
            # Check if D-Bus is available
            import dbus  # noqa: F401

            # Check if GTK3 tray script exists
            script_path = self._get_tray_script_path()
            if not os.path.exists(script_path):
                logger.warning(
                    f"GTK3 tray script not found: {script_path}", extra={"class_name": self.__class__.__name__}
                )
                return False

            # Check if python3-gi for GTK3 is available (basic check)
            try:
                import gi

                gi.require_version("AppIndicator3", "0.1")
                # Don't actually import to avoid conflicts, just check version requirement
                logger.debug("AppIndicator3 requirement check passed", extra={"class_name": self.__class__.__name__})
            except (ImportError, ValueError):
                logger.warning(
                    "AppIndicator3 not available for subprocess", extra={"class_name": self.__class__.__name__}
                )
                return False

            logger.debug("D-Bus tray system is available", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.warning(f"D-Bus tray system not available: {e}", extra={"class_name": self.__class__.__name__})
            return False

    def set_translation_function(self, translation_func: Callable[[str], str]):
        """
        Set the translation function for menu items.

        Args:
            translation_func: Function to translate text
        """
        self.translation_func = translation_func
        logger.debug("Translation function set for D-Bus tray", extra={"class_name": self.__class__.__name__})

    def set_callbacks(self, show_window_callback: Callable, quit_callback: Callable):
        """
        Set the callback functions for menu actions.

        Args:
            show_window_callback: Function to call when showing window
            quit_callback: Function to call when quitting
        """
        self.show_window_callback = show_window_callback
        self.quit_callback = quit_callback

        # Configure D-Bus server callbacks if it exists
        if self.dbus_server:
            self.dbus_server.set_callbacks(show_window_callback, quit_callback, self._get_status_callback)

        logger.debug("Tray callbacks configured", extra={"class_name": self.__class__.__name__})

    def setup_tray(self) -> bool:
        """
        Set up the D-Bus tray system.

        Returns:
            bool: True if successfully set up, False otherwise
        """
        logger.info("Setting up D-Bus tray system", extra={"class_name": self.__class__.__name__})

        if not self.is_available():
            logger.warning("D-Bus tray system not available", extra={"class_name": self.__class__.__name__})
            return False

        try:
            # Start D-Bus server
            if not self._start_dbus_server():
                return False

            # Give server a moment to initialize
            time.sleep(0.5)

            # Start GTK3 tray subprocess
            if not self._start_tray_subprocess():
                self._cleanup_dbus_server()
                return False

            self.is_active = True
            logger.info("D-Bus tray system setup completed successfully", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Error setting up D-Bus tray system: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            self.cleanup()
            return False

    def _start_dbus_server(self) -> bool:
        """Start the D-Bus server in the main process."""
        try:
            self.dbus_server = TrayDBusServer()

            # Set callbacks if they're available
            if self.show_window_callback and self.quit_callback:
                self.dbus_server.set_callbacks(self.show_window_callback, self.quit_callback, self._get_status_callback)

            logger.info("D-Bus tray server started", extra={"class_name": self.__class__.__name__})
            return True

        except Exception as e:
            logger.error(
                f"Error starting D-Bus server: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )
            return False

    def _start_tray_subprocess(self) -> bool:
        """Start the GTK3 tray subprocess."""
        try:
            script_path = self._get_tray_script_path()
            dfs_path = os.environ.get("DFS_PATH", "")

            # Find custom icon if available
            icon_path = self._get_icon_path()

            # Build command
            cmd = ["python3", script_path, "--dfs-path", dfs_path]
            if icon_path:
                cmd.extend(["--icon", icon_path])

            # Add debug flag if needed
            log_level = os.environ.get("LOG_LEVEL", "").upper()
            if log_level in ["DEBUG", "TRACE"]:
                cmd.append("--debug")

            logger.info(
                f"Starting GTK3 tray subprocess: {' '.join(cmd)}", extra={"class_name": self.__class__.__name__}
            )

            # Start subprocess
            self.tray_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True,  # Prevent signals from propagating
            )

            # Check if process started successfully
            time.sleep(1.0)
            if self.tray_process.poll() is not None:
                # Process exited immediately, capture output
                stdout, stderr = self.tray_process.communicate()
                logger.error(
                    f"GTK3 tray process failed to start. stdout: {stdout.decode()}, stderr: {stderr.decode()}",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            logger.info(
                f"GTK3 tray subprocess started successfully (PID: {self.tray_process.pid})",
                extra={"class_name": self.__class__.__name__},
            )
            return True

        except Exception as e:
            logger.error(
                f"Error starting GTK3 tray subprocess: {e}",
                extra={"class_name": self.__class__.__name__},
                exc_info=True,
            )
            return False

    def _get_tray_script_path(self) -> str:
        """Get the path to the GTK3 tray script."""
        base_path = os.environ.get("DFS_PATH", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(base_path, "lib", "component", "gtk3_tray_process.py")

    def _get_icon_path(self) -> Optional[str]:
        """Get path to custom tray icon if available."""
        dfs_path = os.environ.get("DFS_PATH", "")
        if dfs_path:
            icon_path = os.path.join(dfs_path, "images", "dfakeseeder.png")
            if os.path.exists(icon_path):
                return icon_path
        return None

    def _get_status_callback(self) -> str:
        """Get current application status."""
        # This could be enhanced to return actual application status
        return "Running"

    def update_status(self, status_text: str):
        """
        Update the status text in the tray menu.

        Args:
            status_text: New status text to display
        """
        if self.dbus_server and self.is_active:
            try:
                self.dbus_server.update_tray_status(status_text)
                logger.debug(f"Tray status updated: {status_text}", extra={"class_name": self.__class__.__name__})
            except Exception as e:
                logger.error(
                    f"Error updating tray status: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
                )

    def update_torrent_count(self, active_count: int, total_count: int):
        """
        Update torrent count information in the tray.

        Args:
            active_count: Number of active torrents
            total_count: Total number of torrents
        """
        if self.dbus_server and self.is_active:
            try:
                self.dbus_server.update_torrent_count(active_count, total_count)
                logger.debug(
                    f"Torrent count updated: {active_count}/{total_count}",
                    extra={"class_name": self.__class__.__name__},
                )
            except Exception as e:
                logger.error(
                    f"Error updating torrent count: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
                )

    def hide_tray(self):
        """Hide the tray indicator (terminate subprocess)."""
        if self.is_active and self.tray_process:
            try:
                logger.info("Hiding tray (terminating subprocess)", extra={"class_name": self.__class__.__name__})
                self.tray_process.terminate()
                self.tray_process = None
                self.is_active = False
            except Exception as e:
                logger.error(f"Error hiding tray: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True)

    def show_tray(self):
        """Show the tray indicator (restart subprocess if needed)."""
        if not self.is_active:
            logger.info("Showing tray (restarting if needed)", extra={"class_name": self.__class__.__name__})
            self.setup_tray()

    def cleanup(self):
        """Clean up tray resources."""
        logger.info("Cleaning up D-Bus tray manager", extra={"class_name": self.__class__.__name__})

        try:
            # Notify D-Bus clients of shutdown
            if self.dbus_server:
                self.dbus_server.notify_application_closing()

            # Clean up subprocess
            self._cleanup_tray_subprocess()

            # Clean up D-Bus server
            self._cleanup_dbus_server()

            self.is_active = False

            logger.info("D-Bus tray manager cleanup completed", extra={"class_name": self.__class__.__name__})

        except Exception as e:
            logger.error(
                f"Error during tray cleanup: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
            )

    def _cleanup_tray_subprocess(self):
        """Clean up the GTK3 tray subprocess."""
        if self.tray_process:
            try:
                if self.tray_process.poll() is None:  # Process still running
                    logger.debug("Terminating GTK3 tray subprocess", extra={"class_name": self.__class__.__name__})
                    self.tray_process.terminate()

                    # Give it a moment to clean up
                    try:
                        self.tray_process.wait(timeout=3.0)
                    except subprocess.TimeoutExpired:
                        logger.warning(
                            "GTK3 tray subprocess did not terminate cleanly, killing",
                            extra={"class_name": self.__class__.__name__},
                        )
                        self.tray_process.kill()

                self.tray_process = None

            except Exception as e:
                logger.error(
                    f"Error cleaning up tray subprocess: {e}",
                    extra={"class_name": self.__class__.__name__},
                    exc_info=True,
                )

    def _cleanup_dbus_server(self):
        """Clean up the D-Bus server."""
        if self.dbus_server:
            try:
                self.dbus_server.cleanup()
                self.dbus_server = None
            except Exception as e:
                logger.error(
                    f"Error cleaning up D-Bus server: {e}", extra={"class_name": self.__class__.__name__}, exc_info=True
                )
