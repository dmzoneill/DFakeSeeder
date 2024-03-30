import time

import requests
from lib.logger import logger
from lib.settings import Settings
from lib.util.helpers import humanbytes


class Statusbar:
    def __init__(self, builder, model):
        logger.info("StatusBar startup", extra={"class_name": self.__class__.__name__})
        self.builder = builder
        self.model = model

        # subscribe to settings changed
        self.settings = Settings.get_instance()
        self.settings.connect("attribute-changed", self.handle_settings_changed)

        self.ip = "0.0.0.0"

        self.status_uploading = self.builder.get_object("status_uploading")
        self.status_uploaded = self.builder.get_object("status_uploaded")
        self.status_downloading = self.builder.get_object("status_downloading")
        self.status_downloaded = self.builder.get_object("status_downloaded")
        self.status_ip = self.builder.get_object("status_ip")

        self.last_session_uploaded = 0
        self.last_session_downloaded = 0
        self.last_execution_time = time.time()

        self.status_bar = builder.get_object("status_bar")
        self.status_bar.set_css_name("statusbar")

        # Adjust padding of the box
        self.status_bar.set_margin_top(10)
        self.status_bar.set_margin_bottom(10)
        self.status_bar.set_margin_start(10)
        self.status_bar.set_margin_end(10)

    def set_model(self, model):
        self.model = model

    def get_ip(self):
        try:
            if self.ip != "0.0.0.0":
                return self.ip
            response = requests.get("https://ifconfig.me/")
            if response.status_code == 200:
                self.ip = response.content.decode("UTF-8")
                return self.ip
            else:
                self.ip = ""
                return self.ip
        except requests.exceptions.RequestException:
            self.ip = ""
            return self.ip

    def sum_column_values(self, column_name):
        column_names, liststore = self.model.get_liststore()
        column_index = column_names.index(column_name)

        total_sum = 0
        for row in liststore:
            total_sum += row[column_index]

        return total_sum

    def update_view(self, model, _, torrent, attribute):
        current_time = time.time()
        if current_time < self.last_execution_time + self.settings.tickspeed:
            return False
        self.last_execution_time = current_time

        session_uploaded = self.sum_column_values("session_uploaded")
        session_upload_speed = (session_uploaded - self.last_session_uploaded) / int(
            self.settings.tickspeed
        )
        self.last_session_uploaded = session_uploaded

        session_upload_speed = humanbytes(session_upload_speed)
        session_uploaded = humanbytes(session_uploaded)

        total_uploaded = self.sum_column_values("total_uploaded")
        total_uploaded = humanbytes(total_uploaded)

        session_downloaded = self.sum_column_values("session_downloaded")
        session_downloaded_speed = (
            session_downloaded - self.last_session_downloaded
        ) / int(self.settings.tickspeed)
        self.last_session_downloaded = session_downloaded

        session_download_speed = humanbytes(session_downloaded_speed)
        session_downloaded = humanbytes(session_downloaded)

        total_downloaded = self.sum_column_values("total_downloaded")
        total_downloaded = humanbytes(total_downloaded)

        self.status_uploading.set_text(" " + session_upload_speed + " /s")
        self.status_uploaded.set_text(
            "  {} / {}".format(session_uploaded, total_uploaded)
        )
        self.status_downloading.set_text(" " + session_download_speed + " /s")
        self.status_downloaded.set_text(
            "  {} / {}".format(session_downloaded, total_downloaded)
        )
        self.status_ip.set_text("  " + self.get_ip())

    def handle_settings_changed(self, source, key, value):
        logger.info(
            "StatusBar settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        # print(key + " = " + value)
