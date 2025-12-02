# fmt: off
# isort: skip_file
import time

import requests

from d_fake_seeder.components.component.base_component import Component
from d_fake_seeder.domain.app_settings import AppSettings
from d_fake_seeder.domain.torrent.connection_manager import get_connection_manager
from d_fake_seeder.lib.logger import logger
from d_fake_seeder.lib.util.format_helpers import format_number, format_size

# fmt: on


class Statusbar(Component):
    def __init__(self, builder, model):
        super().__init__()

        logger.debug("startup", extra={"class_name": self.__class__.__name__})
        self.builder = builder
        self.model = model

        # subscribe to settings changed
        self.settings = AppSettings.get_instance()
        self.track_signal(
            self.settings,
            self.settings.connect("attribute-changed", self.handle_settings_changed),
        )

        # Load UI margin settings
        ui_settings = getattr(self.settings, "ui_settings", {})
        self.ui_margin_large = ui_settings.get("ui_margin_large", 10)

        self.ip = "0.0.0.0"

        self.status_uploading = self.builder.get_object("status_uploading")
        self.status_uploaded = self.builder.get_object("status_uploaded")
        self.status_downloading = self.builder.get_object("status_downloading")
        self.status_downloaded = self.builder.get_object("status_downloaded")
        self.status_peers = self.builder.get_object("status_peers")
        self.status_ip = self.builder.get_object("status_ip")

        self.last_session_uploaded = 0
        self.last_session_downloaded = 0
        self.last_execution_time = time.time()

        self.status_bar = builder.get_object("status_bar")
        self.status_bar.set_css_name("statusbar")

        # Adjust padding of the box
        self.status_bar.set_margin_top(self.ui_margin_large)
        self.status_bar.set_margin_bottom(self.ui_margin_large)
        self.status_bar.set_margin_start(self.ui_margin_large)
        self.status_bar.set_margin_end(self.ui_margin_large)

        # Register for connection updates to update statusbar immediately
        connection_manager = get_connection_manager()
        connection_manager.add_update_callback(self.update_connection_status)

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
        total_sum = 0

        # Get the list of attributes for each entry in the torrent_list
        attribute_list = [getattr(entry, column_name) for entry in self.model.torrent_list]

        # Sum the values based on the specified attribute
        total_sum = sum(attribute_list)

        return total_sum

    def update_view(self, model, torrent, attribute):
        current_time = time.time()
        if current_time < self.last_execution_time + self.settings.tickspeed:
            return False

        self.last_execution_time = current_time

        session_uploaded = self.sum_column_values("session_uploaded")
        session_upload_speed = (session_uploaded - self.last_session_uploaded) / int(self.settings.tickspeed)
        self.last_session_uploaded = session_uploaded

        session_upload_speed = format_size(session_upload_speed)
        session_uploaded = format_size(session_uploaded)

        total_uploaded = self.sum_column_values("total_uploaded")
        total_uploaded = format_size(total_uploaded)

        session_downloaded = self.sum_column_values("session_downloaded")
        session_downloaded_speed = (session_downloaded - self.last_session_downloaded) / int(self.settings.tickspeed)
        self.last_session_downloaded = session_downloaded

        session_download_speed = format_size(session_downloaded_speed)
        session_downloaded = format_size(session_downloaded)

        total_downloaded = self.sum_column_values("total_downloaded")
        total_downloaded = format_size(total_downloaded)

        self.status_uploading.set_text(" " + session_upload_speed + " /s")
        self.status_uploaded.set_text("  {} / {}".format(session_uploaded, total_uploaded))
        self.status_downloading.set_text(" " + session_download_speed + " /s")
        self.status_downloaded.set_text("  {} / {}".format(session_downloaded, total_downloaded))

        # Update connection metrics: current connections / maximum allowed connections
        try:
            connection_manager = get_connection_manager()

            # Get current total connections excluding old failed ones and max limits
            current_connections = connection_manager.get_global_connection_count_excluding_old_failed()
            _, _, max_total_connections = connection_manager.get_max_connections()

            self.status_peers.set_text(
                "  {} / {}".format(
                    format_number(current_connections, 0),
                    format_number(max_total_connections, 0),
                )
            )
        except Exception as e:
            logger.error(
                f"Error updating connection status: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self.status_peers.set_text("  0 / 250")

        self.status_ip.set_text("  " + self.get_ip())

    def update_connection_status(self):
        """Update only the connection status in the status bar"""
        try:
            connection_manager = get_connection_manager()

            # Get current total connections excluding old failed ones and max limits
            current_connections = connection_manager.get_global_connection_count_excluding_old_failed()
            _, _, max_total_connections = connection_manager.get_max_connections()

            self.status_peers.set_text(
                "  {} / {}".format(
                    format_number(current_connections, 0),
                    format_number(max_total_connections, 0),
                )
            )
        except Exception as e:
            logger.error(
                f"Error updating connection status: {e}",
                extra={"class_name": self.__class__.__name__},
            )
            self.status_peers.set_text("  0 / 250")

    def handle_settings_changed(self, source, key, value):
        logger.debug(
            "Torrents view settings changed",
            extra={"class_name": self.__class__.__name__},
        )

    def handle_model_changed(self, source, data_obj, data_changed):
        logger.debug(
            "StatusBar settings changed",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_view(None, None, None)

    def handle_attribute_changed(self, source, key, value):
        logger.debug(
            "Attribute changed",
            extra={"class_name": self.__class__.__name__},
        )
        self.update_view(None, None, None)

    def model_selection_changed(self, source, model, torrent):
        logger.debug(
            "Model selection changed",
            extra={"class_name": self.__class__.__name__},
        )
