"""
Single Instance Utilities for DFakeSeeder

Provides multiple methods to ensure only one instance of the application runs:
1. GTK Application single-instance (GTK4 only)
2. D-Bus service registration check
3. PID file locking
4. Unix socket locking (most robust)
"""

import atexit
import os
import socket
from pathlib import Path
from typing import Optional

from d_fake_seeder.lib.logger import logger


class SingleInstanceChecker:
    """Base class for single instance checking"""

    def __init__(self, name: str):
        self.name = name
        self.locked = False

    def is_already_running(self) -> bool:
        """Check if another instance is running"""
        raise NotImplementedError

    def cleanup(self):
        """Clean up resources"""
        pass


class DBusSingleInstance(SingleInstanceChecker):
    """D-Bus based single instance check"""

    def __init__(self, service_name: str = "ie.fio.dfakeseeder"):
        super().__init__("dbus")
        self.service_name = service_name

    def is_already_running(self) -> bool:
        """Check if D-Bus service is already registered"""
        try:
            import gi

            gi.require_version("Gio", "2.0")
            from gi.repository import Gio, GLib

            connection = Gio.bus_get_sync(Gio.BusType.SESSION, None)
            if not connection:
                logger.debug(
                    "D-Bus connection failed, cannot check for existing instance",
                    extra={"class_name": self.__class__.__name__},
                )
                return False

            # Check if service is already registered
            try:
                name_owner = connection.call_sync(
                    "org.freedesktop.DBus",
                    "/org/freedesktop/DBus",
                    "org.freedesktop.DBus",
                    "GetNameOwner",
                    GLib.Variant("(s)", (self.service_name,)),
                    None,
                    Gio.DBusCallFlags.NONE,
                    1000,  # 1 second timeout
                    None,
                )
                if name_owner:
                    logger.info(
                        f"D-Bus service '{self.service_name}' is already registered",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return True
            except GLib.Error as e:
                error_msg = str(e)
                if "NameHasNoOwner" in error_msg or "org.freedesktop.DBus.Error.NameHasNoOwner" in error_msg:
                    # Service not registered - no other instance
                    logger.debug(
                        f"D-Bus service '{self.service_name}' not registered - no existing instance",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return False
                else:
                    logger.debug(
                        f"D-Bus check error: {e}",
                        extra={"class_name": self.__class__.__name__},
                    )
                    return False

            return False

        except Exception as e:
            logger.debug(
                f"D-Bus instance check failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False


class PIDFileLock(SingleInstanceChecker):
    """PID file based single instance lock"""

    def __init__(self, lockfile_path: str):
        super().__init__("pidfile")
        self.lockfile = Path(lockfile_path)
        self.locked = False

    def is_already_running(self) -> bool:
        """Check if lock file indicates another instance is running"""
        try:
            # Ensure directory exists
            self.lockfile.parent.mkdir(parents=True, exist_ok=True)

            if self.lockfile.exists():
                try:
                    # Read PID from file
                    pid_str = self.lockfile.read_text().strip()
                    if not pid_str:
                        # Empty file - remove it
                        self.lockfile.unlink()
                        return False

                    pid = int(pid_str)

                    # Check if process is actually running
                    if self._is_process_running(pid):
                        logger.info(
                            f"PID file indicates instance is running (PID: {pid})",
                            extra={"class_name": self.__class__.__name__},
                        )
                        return True
                    else:
                        # Stale lock file - remove it
                        logger.debug(
                            f"Stale PID file found (PID: {pid}), removing",
                            extra={"class_name": self.__class__.__name__},
                        )
                        self.lockfile.unlink()
                        return False
                except (ValueError, OSError) as e:
                    # Corrupted lock file - remove it
                    logger.debug(
                        f"Corrupted PID file: {e}, removing",
                        extra={"class_name": self.__class__.__name__},
                    )
                    self.lockfile.unlink()
                    return False

            # No lock file - create it with current PID
            self.lockfile.write_text(str(os.getpid()))
            self.locked = True
            atexit.register(self.cleanup)
            logger.debug(
                f"Created PID file: {self.lockfile}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        except Exception as e:
            logger.error(
                f"PID file check failed: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

    def _is_process_running(self, pid: int) -> bool:
        """Check if a process with given PID is running"""
        try:
            # Send signal 0 - doesn't kill, just checks if process exists
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def cleanup(self):
        """Remove lock file"""
        try:
            if self.locked and self.lockfile.exists():
                self.lockfile.unlink()
                logger.debug(
                    f"Removed PID file: {self.lockfile}",
                    extra={"class_name": self.__class__.__name__},
                )
        except OSError as e:
            logger.debug(
                f"Error removing PID file: {e}",
                extra={"class_name": self.__class__.__name__},
            )


class SocketLock(SingleInstanceChecker):
    """Unix socket based single instance lock (most robust)"""

    def __init__(self, name: str):
        super().__init__(name)
        self.socket: Optional[socket.socket] = None
        self.socket_address = f"\0dfakeseeder_{name}"  # Abstract namespace

    def is_already_running(self) -> bool:
        """Try to bind to abstract Unix socket"""
        try:
            # Create abstract Unix socket (Linux-specific)
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

            # Try to bind - will fail if another instance holds the socket
            self.socket.bind(self.socket_address)
            self.socket.listen(1)
            self.locked = True

            atexit.register(self.cleanup)
            logger.debug(
                f"Socket lock acquired: {self.socket_address}",
                extra={"class_name": self.__class__.__name__},
            )
            return False

        except OSError as e:
            # Socket already bound - another instance is running
            logger.info(
                f"Socket lock failed - another instance detected: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            if self.socket:
                self.socket.close()
                self.socket = None
            return True
        except Exception as e:
            logger.error(
                f"Socket lock error: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            if self.socket:
                self.socket.close()
                self.socket = None
            return False

    def cleanup(self):
        """Close socket"""
        try:
            if self.locked and self.socket:
                self.socket.close()
                logger.debug(
                    f"Socket lock released: {self.socket_address}",
                    extra={"class_name": self.__class__.__name__},
                )
        except Exception as e:
            logger.debug(
                f"Error releasing socket lock: {e}",
                extra={"class_name": self.__class__.__name__},
            )


class MultiMethodSingleInstance:
    """
    Multi-method single instance checker with fallbacks.

    Tries multiple methods in order:
    1. D-Bus check (if available)
    2. Socket lock (most robust)
    3. PID file (fallback)
    """

    def __init__(self, app_name: str, dbus_service: Optional[str] = None, use_pidfile: bool = True):
        self.app_name = app_name
        self.dbus_service = dbus_service
        self.use_pidfile = use_pidfile
        self.locks = []
        self.detected_by = None

    def is_already_running(self) -> tuple[bool, Optional[str]]:
        """
        Check if another instance is already running.

        Returns:
            (is_running: bool, detected_by: str or None)
        """
        # Method 1: D-Bus check (non-locking, just detection)
        if self.dbus_service:
            dbus_checker = DBusSingleInstance(self.dbus_service)
            if dbus_checker.is_already_running():
                return True, "D-Bus"

        # Method 2: Socket lock (try first, most robust)
        socket_lock = SocketLock(self.app_name)
        if socket_lock.is_already_running():
            return True, "Socket"

        # Socket acquired successfully
        self.locks.append(socket_lock)

        # Method 3: PID file (additional safety)
        if self.use_pidfile:
            pidfile_path = os.path.expanduser(f"~/.config/dfakeseeder/{self.app_name}.lock")
            pid_lock = PIDFileLock(pidfile_path)
            if pid_lock.is_already_running():
                # Another instance detected by PID file
                # Clean up socket lock
                socket_lock.cleanup()
                return True, "PID File"

            # PID file acquired successfully
            self.locks.append(pid_lock)

        # No other instance detected
        return False, None

    def cleanup(self):
        """Clean up all locks"""
        for lock in self.locks:
            lock.cleanup()
        self.locks.clear()
