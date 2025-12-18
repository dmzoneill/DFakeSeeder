# fmt: off
from abc import abstractmethod
from typing import Any

from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.cleanup_mixin import CleanupMixin

# fmt: on


class Component(CleanupMixin):
    def __init__(self) -> None:
        """Initialize component."""
        CleanupMixin.__init__(self)
        self.model = None

    @staticmethod
    def to_str(bind: Any, from_value: Any) -> Any:
        return str(from_value)

    @abstractmethod
    def handle_model_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        logger.trace(
            "Component Model changed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def handle_attribute_changed(self, source: Any, key: Any, value: Any) -> None:
        logger.trace(
            "Component Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def handle_settings_changed(self, source: Any, data_obj: Any, _data_changed: Any) -> None:
        logger.trace(
            "Component settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def update_view(self, model: Any, torrent: Any, attribute: Any) -> None:
        logger.trace(
            "Component update view",
            extra={"class_name": self.__class__.__name__},
        )

    def set_model(self, model: Any) -> None:
        self.model = model
        # subscribe to model changes and track signal for cleanup
        handler_id = self.model.connect("data-changed", self.handle_model_changed)  # type: ignore[attr-defined]
        self.track_signal(self.model, handler_id)

    def model_selection_changed(self, source: Any, model: Any, torrent: Any) -> Any:
        logger.trace(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
