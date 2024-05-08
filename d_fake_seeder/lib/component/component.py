from abc import ABC, abstractmethod

from lib.logger import logger


class Component(ABC):
    @staticmethod
    def to_str(bind, from_value):
        return str(from_value)

    @abstractmethod
    def handle_model_changed(self, source, data_obj, data_changed):
        logger.debug(
            "Component Model changed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def handle_attribute_changed(self, source, key, value):
        logger.debug(
            "Component Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def handle_settings_changed(self, source, data_obj, data_changed):
        logger.debug(
            "Component settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    @abstractmethod
    def update_view(self, model, torrent, attribute):
        logger.debug(
            "Component update view",
            extra={"class_name": self.__class__.__name__},
        )

    def set_model(self, model):
        self.model = model
        # subscribe to model changes
        self.model.connect("data-changed", self.handle_model_changed)

    def model_selection_changed(self, source, model, torrent):
        logger.debug(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
