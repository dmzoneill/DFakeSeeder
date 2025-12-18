#!/usr/bin/env python3
"""
DFakeSeeder Tray Launcher

Launches the system tray application with connection management and error handling.
Provides automatic retry logic and graceful error recovery.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# fmt: off
from typing import Any

# Add the parent directory to Python path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from lib.logger import logger
except ImportError:
    # Fallback logging if main logger not available
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# fmt: on


class TrayLauncher:
    """
    Tray application launcher with connection management

    Handles launching the tray application with automatic retry logic
    and graceful error handling for improved reliability.
    """

    def __init__(self) -> None:
        self.max_retries = 5
        self.retry_delay = 3  # seconds
        self.process = None
        self.running = True

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def launch(self) -> Any:
        """Launch the tray application with retry logic"""
        logger.info("Starting DFakeSeeder tray launcher")

        retry_count = 0
        while self.running and retry_count < self.max_retries:
            try:
                logger.info(f"Launching tray application (attempt {retry_count + 1}/{self.max_retries})")

                # Launch tray application
                result = self._launch_tray()

                if result:
                    logger.info("Tray application launched successfully")
                    return True
                else:
                    retry_count += 1
                    if retry_count < self.max_retries:
                        logger.error(f"Launch failed, retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)

            except KeyboardInterrupt:
                logger.info("Launch interrupted by user")
                break
            except Exception as e:
                logger.error(f"Launch error: {e}")
                retry_count += 1
                if retry_count < self.max_retries:
                    time.sleep(self.retry_delay)

        if retry_count >= self.max_retries:
            logger.error("Failed to launch tray application after maximum retries")
            return False

        return True

    def _launch_tray(self) -> Any:
        """Launch the actual tray application"""
        try:
            # Get the path to the tray application
            tray_script = parent_dir / "dfakeseeder_tray.py"

            if not tray_script.exists():
                logger.error(f"Tray script not found: {tray_script}")
                return False

            # Set environment variables
            env = os.environ.copy()
            env["PYTHONPATH"] = str(parent_dir)

            # Launch the tray application
            self.process = subprocess.Popen(  # type: ignore[assignment]
                [sys.executable, str(tray_script)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Wait a moment to see if it starts successfully
            time.sleep(self._get_startup_delay())  # type: ignore[attr-defined]

            if self.process.poll() is None:  # type: ignore[attr-defined]
                # Process is still running, wait for it to complete
                stdout, stderr = self.process.communicate()  # type: ignore[attr-defined]

                if self.process.returncode == 0:  # type: ignore[attr-defined]
                    logger.info("Tray application completed successfully")
                    return True
                else:
                    logger.error(f"Tray application failed with code {self.process.returncode}")  # type: ignore[attr-defined]  # noqa: E501
                    if stderr:
                        logger.error(f"Error output: {stderr}")
                    return False
            else:
                # Process exited immediately
                logger.error("Tray application exited immediately")
                return False

        except Exception as e:
            logger.error(f"Failed to launch tray application: {e}")
            return False

    def _check_dependencies(self) -> Any:
        """Check if required dependencies are available"""
        try:
            import gi

            gi.require_version("AppIndicator3", "0.1")
            gi.require_version("Notify", "0.7")
            from gi.repository import AppIndicator3, Notify

            # Verify modules are available
            logger.info(f"System tray dependencies available: {AppIndicator3.__name__}, {Notify.__name__}")
            return True
        except ImportError as e:
            logger.error(f"Missing system tray dependencies: {e}")
            logger.error("Please install: gir1.2-appindicator3-0.1 gir1.2-notify-0.7")
            return False

    def _check_dbus_service(self) -> Any:
        """Check if main DFakeSeeder application is running"""
        try:
            import gi

            gi.require_version("Gio", "2.0")
            from gi.repository import Gio

            connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            if not connection:
                return False

            # Try to create proxy to main application
            proxy = Gio.DBusProxy.new_sync(
                connection,
                Gio.DBusProxyFlags.NONE,
                None,
                "ie.fio.dfakeseeder",
                "/ie/fio/dfakeseeder",
                "ie.fio.dfakeseeder.Settings",
                None,
            )

            # Try to ping the service
            result = proxy.call_sync("Ping", None, Gio.DBusCallFlags.NONE, 1000, None)
            return result.unpack()[0] if result else False

        except Exception as e:
            logger.error(f"D-Bus service check failed: {e}")
            return False

    def _signal_handler(self, signum: Any, frame: Any) -> Any:
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down")
        self.running = False

        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                # Give it time to terminate gracefully
                time.sleep(self._get_retry_delay())
                if self.process.poll() is None:
                    self.process.kill()
            except Exception as e:
                logger.error(f"Error terminating tray process: {e}")

    def run_diagnostics(self) -> None:
        """Run diagnostic checks"""
        logger.info("Running tray launcher diagnostics...")

        # Check dependencies
        deps_ok = self._check_dependencies()
        logger.info(f"Dependencies available: {deps_ok}")

        # Check D-Bus service
        dbus_ok = self._check_dbus_service()
        logger.info(f"Main application running: {dbus_ok}")

        # Check tray script exists
        tray_script = parent_dir / "dfakeseeder_tray.py"
        script_ok = tray_script.exists()
        logger.info(f"Tray script exists: {script_ok}")

        return deps_ok and script_ok  # type: ignore[return-value]


def main() -> Any:
    """Main entry point"""
    launcher = TrayLauncher()

    # Check if we should run diagnostics
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        return launcher.run_diagnostics()

    # Run the launcher
    return launcher.launch()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
