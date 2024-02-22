import os
from lib.settings import Settings
from lib.logger import logger


# Cont roller
class Controller:
    def __init__(self, view, model):
        logger.info("Controller Startup", extra={"class_name": self.__class__.__name__})
        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.view = view
        self.model = model
        self.view.set_model(self.model)
        self.view.connect_signals()

    def run(self):
        logger.info("Controller Run", extra={"class_name": self.__class__.__name__})
        for filename in os.listdir(self.settings.directory):
            if filename.endswith(".torrent"):
                torrent_file = os.path.join(self.settings.directory, filename)
                self.model.add_torrent(torrent_file)

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "Controller settings changed", extra={"class_name": self.__class__.__name__}
        )
        # print(key + " = " + value)
