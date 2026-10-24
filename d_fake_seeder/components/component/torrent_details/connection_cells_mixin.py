"""
Shared cell rendering for the incoming/outgoing connection tabs.

Both connection tabs display ConnectionPeer rows with the same widgets and
formatting; only the direction-specific property names differ, which each tab
declares via the class attributes below.
"""

# isort: skip_file

# fmt: off
import datetime
from typing import Any
from collections.abc import Callable

import gi

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.lib.logger import logger

gi.require_version("Gtk", "4.0")

from gi.repository import GLib, GObject, Gtk, Pango  # noqa: E402

# fmt: on


class ConnectionCellsMixin:
    """setup_cell/bind_cell/format_bytes for connection column views."""

    BOOL_PROPERTIES: tuple[str, ...] = ()
    BYTES_PROPERTY: str = ""
    RATE_PROPERTY: str = ""
    COUNT_PROPERTIES: tuple[str, ...] = ()

    # Provided by the concrete tab (BaseTorrentTab / CleanupMixin)
    kb_threshold: int
    mb_threshold: int
    gb_threshold: int
    track_binding: Callable[[Any], Any]

    def setup_cell(self, widget: Any, item: Any, property_name: Any) -> None:
        """Setup cell widget based on property type"""

        def setup_when_idle() -> None:
            obj = item.get_item()
            if obj is None:
                return

            # Use appropriate widget type
            if property_name in self.BOOL_PROPERTIES:
                widget_obj = Gtk.CheckButton()
                widget_obj.set_sensitive(False)  # Read-only
            else:
                widget_obj = Gtk.Label()
                # Add ellipsization to prevent forcing column/window width
                widget_obj.set_ellipsize(Pango.EllipsizeMode.END)
                widget_obj.set_width_chars(5)
                # Align based on text direction (RTL for Arabic, Hebrew, etc.)
                text_direction = widget_obj.get_direction()
                if text_direction == Gtk.TextDirection.RTL:
                    widget_obj.set_xalign(1)  # Right align for RTL
                else:
                    widget_obj.set_xalign(0)  # Left align for LTR

            item.set_child(widget_obj)

        GLib.idle_add(setup_when_idle)

    def bind_cell(self, widget: Any, item: Any, property_name: Any) -> None:
        """Bind cell data to widget"""

        def bind_when_idle() -> None:
            try:
                # Early validation - exit immediately if any required objects are None
                if item is None:
                    return

                child = item.get_child()
                obj = item.get_item()

                # Check if both child and obj are valid before proceeding
                if obj is None or child is None:
                    return

                # Validate that obj has the property we're trying to bind
                if not hasattr(obj, property_name):
                    return

                # Re-check validity right before each operation to handle race conditions
                if property_name in self.BOOL_PROPERTIES:
                    # Double check before binding - ensure child has expected properties
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, property_name)
                        and hasattr(child, "active")
                        and hasattr(obj, "bind_property")
                    ):
                        try:
                            binding = obj.bind_property(
                                property_name,
                                child,
                                "active",
                                GObject.BindingFlags.SYNC_CREATE,
                            )
                            self.track_binding(binding)
                        except Exception as e:
                            logger.error(
                                f"Error binding boolean property {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name == "connection_time":
                    # Format timestamp with additional checks
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, "connection_time")
                        and hasattr(child, "set_text")
                    ):
                        try:
                            dt = datetime.datetime.fromtimestamp(obj.connection_time)
                            child.set_text(dt.strftime("%H:%M:%S"))
                        except Exception as e:
                            logger.error(
                                f"Error formatting connection time: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name in (self.BYTES_PROPERTY, self.RATE_PROPERTY, *self.COUNT_PROPERTIES):
                    # Format bytes/rates/counts with additional checks
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, property_name)
                        and hasattr(child, "set_text")
                    ):
                        try:
                            value = getattr(obj, property_name)
                            if property_name == self.BYTES_PROPERTY:
                                child.set_text(self.format_bytes(value))
                            elif property_name == self.RATE_PROPERTY:
                                child.set_text(f"{value:.1f} B/s")
                            elif property_name in self.COUNT_PROPERTIES:
                                child.set_text(str(value))
                        except Exception as e:
                            logger.error(
                                f"Error formatting {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name == "status":
                    # Format status with visual indicators
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(child, "set_text")
                        and hasattr(child, "add_css_class")
                    ):
                        try:
                            status = getattr(obj, property_name, "unknown")
                            status_icons = {
                                "connecting": "🔌",
                                "connected": "✅",
                                "failed": "❌",
                                "disconnected": "🔴",
                            }
                            icon = status_icons.get(status, "❓")
                            child.set_text(f"{icon} {status.title()}")

                            # Set color based on status
                            if status == "failed":
                                child.add_css_class("error")
                            elif status == "connected":
                                child.add_css_class("success")
                        except Exception as e:
                            logger.error(
                                f"Error formatting status: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name in ["address", "client"]:
                    # Direct text setting for address and client fields
                    if obj is not None and child is not None and hasattr(child, "set_text"):
                        try:
                            value = getattr(obj, property_name, "")
                            if property_name == "address" and hasattr(obj, "port"):
                                # Combine address and port for display
                                port = getattr(obj, "port", 0)
                                if value and port:
                                    child.set_text(f"{value}:{port}")
                                elif value:
                                    child.set_text(value)
                                else:
                                    child.set_text("")
                            else:
                                child.set_text(str(value) if value else "")
                        except Exception as e:
                            logger.error(
                                f"Error formatting {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                elif property_name == "failure_reason":
                    # Only show failure reason if status is failed
                    if obj is not None and child is not None and hasattr(child, "set_text"):
                        try:
                            status = getattr(obj, "status", "")
                            if status == "failed":
                                reason = getattr(obj, property_name, "")
                                child.set_text(reason if reason else "Unknown error")
                            else:
                                child.set_text("")
                        except Exception as e:
                            logger.error(
                                f"Error formatting failure reason: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
                else:
                    # Default property binding with additional checks
                    if (
                        obj is not None
                        and child is not None
                        and hasattr(obj, property_name)
                        and hasattr(child, "label")
                        and hasattr(obj, "bind_property")
                    ):
                        try:
                            binding = obj.bind_property(
                                property_name,
                                child,
                                "label",
                                GObject.BindingFlags.SYNC_CREATE,
                                Component.to_str,
                            )
                            self.track_binding(binding)
                        except Exception as e:
                            logger.error(
                                f"Error binding default property {property_name}: {e}",
                                extra={"class_name": self.__class__.__name__},
                            )
            except Exception as e:
                logger.error(
                    f"Error binding cell {property_name}: {e}",
                    extra={"class_name": self.__class__.__name__},
                )

        GLib.idle_add(bind_when_idle)

    def format_bytes(self, bytes_value: Any) -> Any:
        """Format bytes in human readable format using configurable thresholds"""
        if bytes_value < self.kb_threshold:
            return f"{bytes_value} B"
        elif bytes_value < self.mb_threshold:
            return f"{bytes_value / self.kb_threshold:.1f} KB"
        elif bytes_value < self.gb_threshold:
            return f"{bytes_value / self.mb_threshold:.1f} MB"
        else:
            return f"{bytes_value / self.gb_threshold:.1f} GB"
