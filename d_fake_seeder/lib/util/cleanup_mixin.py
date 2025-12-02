"""
Cleanup Mixin for GTK Components

Provides automatic tracking and cleanup of:
- GObject signal connections
- GObject property bindings
- GLib timeout/idle sources
- ListStore/TreeStore data

Usage:
    class MyComponent(CleanupMixin):
        def __init__(self):
            CleanupMixin.__init__(self)

            # Track signal connections
            handler_id = obj.connect("signal", self.callback)
            self.track_signal(obj, handler_id)

            # Track property bindings
            binding = source.bind_property(...)
            self.track_binding(binding)

            # Track timeout sources
            timeout_id = GLib.timeout_add(1000, self.callback)
            self.track_timeout(timeout_id)

        def cleanup(self):
            # Clean up all tracked resources
            super().cleanup()
"""

# isort: skip_file

# fmt: off
import weakref
from typing import Any, List, Tuple

import gi

from d_fake_seeder.lib.logger import logger

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, GObject  # noqa: E402

# fmt: on


class CleanupMixin:
    """
    Mixin class providing automatic resource cleanup tracking.

    Tracks and cleans up:
    - Signal connections
    - Property bindings
    - Timeout/idle sources
    - ListStore data
    """

    def __init__(self):
        """Initialize cleanup tracking structures."""
        # Track signal connections: [(weakref(object), handler_id), ...]
        self._tracked_signals: List[Tuple[Any, int]] = []

        # Track property bindings: [binding, ...]
        self._tracked_bindings: List[GObject.Binding] = []

        # Track timeout/idle sources: [source_id, ...]
        self._tracked_timeouts: List[int] = []

        # Track ListStore instances: [weakref(store), ...]
        self._tracked_stores: List[Any] = []

        # Cleanup performed flag
        self._cleanup_done = False

        logger.debug("CleanupMixin initialized", extra={"class_name": self.__class__.__name__})

    def track_signal(self, obj: GObject.Object, handler_id: int) -> int:
        """
        Track a signal connection for automatic cleanup.

        Args:
            obj: GObject that signal is connected to
            handler_id: Handler ID returned from connect()

        Returns:
            The handler_id (for convenience)
        """
        # Use weak reference to avoid keeping object alive
        try:
            obj_ref = weakref.ref(obj)
            self._tracked_signals.append((obj_ref, handler_id))
            logger.debug(
                f"Tracking signal handler {handler_id} on {obj.__class__.__name__}",
                extra={"class_name": self.__class__.__name__},
            )
        except TypeError:
            # Object doesn't support weak references, store strong ref
            logger.warning(
                f"Object {obj.__class__.__name__} doesn't support weakref, using strong reference",
                extra={"class_name": self.__class__.__name__},
            )
            self._tracked_signals.append((obj, handler_id))

        return handler_id

    def track_binding(self, binding: GObject.Binding) -> GObject.Binding:
        """
        Track a property binding for automatic cleanup.

        Args:
            binding: GBinding object returned from bind_property()

        Returns:
            The binding (for convenience)
        """
        self._tracked_bindings.append(binding)
        logger.debug("Tracking property binding", extra={"class_name": self.__class__.__name__})
        return binding

    def track_timeout(self, source_id: int) -> int:
        """
        Track a timeout/idle source for automatic cleanup.

        Args:
            source_id: Source ID returned from GLib.timeout_add() or GLib.idle_add()

        Returns:
            The source_id (for convenience)
        """
        self._tracked_timeouts.append(source_id)
        logger.debug(
            f"Tracking timeout source {source_id}",
            extra={"class_name": self.__class__.__name__},
        )
        return source_id

    def track_store(self, store) -> Any:
        """
        Track a ListStore/TreeStore for automatic cleanup.

        Args:
            store: Gio.ListStore or similar store object

        Returns:
            The store (for convenience)
        """
        try:
            store_ref = weakref.ref(store)
            self._tracked_stores.append(store_ref)
            logger.debug(
                f"Tracking store {store.__class__.__name__}",
                extra={"class_name": self.__class__.__name__},
            )
        except TypeError:
            # Store doesn't support weak references
            logger.warning(
                f"Store {store.__class__.__name__} doesn't support weakref, using strong reference",
                extra={"class_name": self.__class__.__name__},
            )
            self._tracked_stores.append(store)

        return store

    def cleanup(self):
        """
        Clean up all tracked resources.

        This method should be called when the component is being destroyed.
        It will:
        - Disconnect all tracked signals
        - Unbind all tracked property bindings
        - Remove all tracked timeout/idle sources
        - Clear all tracked ListStore data
        """
        if self._cleanup_done:
            logger.debug(
                "Cleanup already performed, skipping",
                extra={"class_name": self.__class__.__name__},
            )
            return

        logger.debug(
            f"Cleaning up resources: {len(self._tracked_signals)} signals, "
            f"{len(self._tracked_bindings)} bindings, "
            f"{len(self._tracked_timeouts)} timeouts, "
            f"{len(self._tracked_stores)} stores",
            extra={"class_name": self.__class__.__name__},
        )

        # Disconnect signal handlers
        self._cleanup_signals()

        # Unbind property bindings
        self._cleanup_bindings()

        # Remove timeout sources
        self._cleanup_timeouts()

        # Clear list stores
        self._cleanup_stores()

        self._cleanup_done = True
        logger.debug("Cleanup completed", extra={"class_name": self.__class__.__name__})

    def _cleanup_signals(self):
        """Disconnect all tracked signal handlers."""
        disconnected = 0
        failed = 0

        for obj_or_ref, handler_id in self._tracked_signals:
            try:
                # Dereference if it's a weakref
                if isinstance(obj_or_ref, weakref.ref):
                    obj = obj_or_ref()
                    if obj is None:
                        # Object already garbage collected
                        continue
                else:
                    obj = obj_or_ref

                # Try to disconnect
                obj.disconnect(handler_id)
                disconnected += 1

            except Exception as e:
                logger.debug(
                    f"Failed to disconnect handler {handler_id}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                failed += 1

        self._tracked_signals.clear()

        if disconnected > 0:
            logger.debug(
                f"Disconnected {disconnected} signal handlers ({failed} failed)",
                extra={"class_name": self.__class__.__name__},
            )

    def _cleanup_bindings(self):
        """Unbind all tracked property bindings."""
        unbound = 0
        failed = 0

        for binding in self._tracked_bindings:
            try:
                binding.unbind()
                unbound += 1
            except Exception as e:
                logger.debug(
                    f"Failed to unbind binding: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                failed += 1

        self._tracked_bindings.clear()

        if unbound > 0:
            logger.debug(
                f"Unbound {unbound} property bindings ({failed} failed)",
                extra={"class_name": self.__class__.__name__},
            )

    def _cleanup_timeouts(self):
        """Remove all tracked timeout/idle sources."""
        removed = 0
        failed = 0

        for source_id in self._tracked_timeouts:
            try:
                if GLib.source_remove(source_id):
                    removed += 1
                else:
                    # Source already removed or invalid
                    pass
            except Exception as e:
                logger.debug(
                    f"Failed to remove timeout source {source_id}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                failed += 1

        self._tracked_timeouts.clear()

        if removed > 0:
            logger.debug(
                f"Removed {removed} timeout sources ({failed} failed)",
                extra={"class_name": self.__class__.__name__},
            )

    def _cleanup_stores(self):
        """Clear all tracked ListStore/TreeStore data."""
        cleared = 0
        failed = 0

        for store_or_ref in self._tracked_stores:
            try:
                # Dereference if it's a weakref
                if isinstance(store_or_ref, weakref.ref):
                    store = store_or_ref()
                    if store is None:
                        # Store already garbage collected
                        continue
                else:
                    store = store_or_ref

                # Clear the store
                if hasattr(store, "remove_all"):
                    store.remove_all()
                    cleared += 1
                elif hasattr(store, "clear"):
                    store.clear()
                    cleared += 1

            except Exception as e:
                logger.debug(
                    f"Failed to clear store: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                failed += 1

        self._tracked_stores.clear()

        if cleared > 0:
            logger.debug(
                f"Cleared {cleared} data stores ({failed} failed)",
                extra={"class_name": self.__class__.__name__},
            )

    def __del__(self):
        """Ensure cleanup is called when object is garbage collected."""
        if not self._cleanup_done:
            logger.warning(
                "CleanupMixin.__del__() called but cleanup() was never called! "
                "Please call cleanup() explicitly before destruction.",
                extra={"class_name": self.__class__.__name__},
            )
            try:
                self.cleanup()
            except Exception as e:
                logger.error(
                    f"Error during __del__ cleanup: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
