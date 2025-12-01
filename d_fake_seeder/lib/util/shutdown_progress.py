"""
Shutdown Progress Tracking System

Provides visual feedback during application shutdown by tracking the progress
of various component shutdowns (torrents, peer managers, threads, etc.).
"""

# fmt: off
import time
from typing import Callable, Dict, List

from d_fake_seeder.lib.logger import logger

# fmt: on


class ShutdownProgressTracker:
    """Tracks shutdown progress across different component types"""

    def __init__(self):
        self.components = {
            "model_torrents": {"total": 0, "completed": 0, "status": "pending"},
            "peer_managers": {"total": 0, "completed": 0, "status": "pending"},
            "background_workers": {"total": 0, "completed": 0, "status": "pending"},
            "network_connections": {"total": 0, "completed": 0, "status": "pending"},
        }
        self.callbacks: List[Callable] = []
        self.start_time = time.time()
        self.force_shutdown_timer = 15.0  # seconds
        self.is_shutting_down = False

    def register_component(self, component_type: str, count: int):
        """Register how many items of this type need to be shut down"""
        if component_type in self.components:
            self.components[component_type]["total"] = count
            self.components[component_type]["status"] = "pending" if count > 0 else "complete"
            logger.debug(
                f"📊 Registered {count} {component_type} for shutdown tracking",
                extra={"class_name": self.__class__.__name__},
            )
            self._notify_callbacks()

    def mark_completed(self, component_type: str, count: int = 1):
        """Mark items as completed for this component type"""
        if component_type in self.components:
            component = self.components[component_type]
            component["completed"] = min(component["completed"] + count, component["total"])

            # Update status
            if component["completed"] >= component["total"] and component["total"] > 0:
                component["status"] = "complete"
            elif component["completed"] > 0:
                component["status"] = "in_progress"

            logger.debug(
                f"✅ Marked {count} {component_type} as completed " f"({component['completed']}/{component['total']})",
                extra={"class_name": self.__class__.__name__},
            )
            self._notify_callbacks()

    def start_component_shutdown(self, component_type: str):
        """Mark a component type as starting shutdown"""
        if component_type in self.components:
            self.components[component_type]["status"] = "in_progress"
            logger.debug(
                f"🔄 Started shutdown of {component_type}",
                extra={"class_name": self.__class__.__name__},
            )
            self._notify_callbacks()

    def mark_component_timeout(self, component_type: str):
        """Mark a component as timed out (forced shutdown)"""
        if component_type in self.components:
            self.components[component_type]["status"] = "timeout"
            logger.warning(
                f"⚠️ {component_type} shutdown timed out",
                extra={"class_name": self.__class__.__name__},
            )
            self._notify_callbacks()

    def get_progress_percentage(self) -> float:
        """Calculate overall progress percentage"""
        total_items = sum(comp["total"] for comp in self.components.values())
        completed_items = sum(comp["completed"] for comp in self.components.values())

        if total_items == 0:
            return 100.0

        return (completed_items / total_items) * 100.0

    def get_time_elapsed(self) -> float:
        """Get time elapsed since shutdown started"""
        return time.time() - self.start_time

    def get_time_remaining(self) -> float:
        """Get time remaining before force shutdown"""
        elapsed = self.get_time_elapsed()
        return max(0, self.force_shutdown_timer - elapsed)

    def is_force_shutdown_time(self) -> bool:
        """Check if it's time for force shutdown"""
        return self.get_time_elapsed() >= self.force_shutdown_timer

    def is_complete(self) -> bool:
        """Check if all components are shut down"""
        for component in self.components.values():
            if component["total"] > 0 and component["status"] not in [
                "complete",
                "timeout",
            ]:
                return False
        return True

    def get_status_summary(self) -> Dict[str, Dict]:
        """Get a summary of all component statuses"""
        return {name: comp.copy() for name, comp in self.components.items()}

    def add_callback(self, callback: Callable):
        """Add a callback to be notified when progress changes"""
        self.callbacks.append(callback)

    def remove_callback(self, callback: Callable):
        """Remove a progress change callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

    def start_shutdown(self):
        """Mark shutdown as started"""
        self.is_shutting_down = True
        self.start_time = time.time()
        logger.info(
            "🛑 Shutdown progress tracking started",
            extra={"class_name": self.__class__.__name__},
        )
        self._notify_callbacks()

    def _notify_callbacks(self):
        """Notify all registered callbacks of progress changes"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(
                    f"Error in shutdown progress callback: {e}",
                    extra={"class_name": self.__class__.__name__},
                )
                # Remove problematic callback to prevent repeated errors
                try:
                    self.callbacks.remove(callback)
                except ValueError:
                    pass

    def get_component_display_name(self, component_type: str) -> str:
        """Get user-friendly display name for component type"""
        display_names = {
            "model_torrents": "Model & Torrents",
            "peer_managers": "Peer Managers",
            "background_workers": "Background Workers",
            "network_connections": "Network Connections",
        }
        return display_names.get(component_type, component_type.replace("_", " ").title())

    def get_status_icon(self, component_type: str) -> str:
        """Get status icon for component type"""
        status = self.components[component_type]["status"]
        icons = {
            "pending": "⏳",
            "in_progress": "🔄",
            "complete": "✅",
            "timeout": "⚠️",
        }
        return icons.get(status, "❓")
