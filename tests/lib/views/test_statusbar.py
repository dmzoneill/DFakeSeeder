import unittest
from unittest.mock import patch, MagicMock
from d_fake_seeder.lib.views.statusbar import Statusbar
import pytest


class TestStatusbar(unittest.TestCase):
    @patch("d_fake_seeder.lib.views.statusbar.logger.info")
    @pytest.mark.timeout(5)
    def test_init(self, mock_logger_info):
        builder = MagicMock()
        model = MagicMock()
        statusbar = Statusbar(builder, model)

        self.assertEqual(statusbar.builder, builder)
        self.assertEqual(statusbar.model, model)
        self.assertIsNotNone(statusbar.settings)
        self.assertEqual(statusbar.ip, "0.0.0.0")
        self.assertIsNotNone(statusbar.status_uploading)
        self.assertIsNotNone(statusbar.status_uploaded)
        self.assertIsNotNone(statusbar.status_downloading)
        self.assertIsNotNone(statusbar.status_downloaded)
        self.assertIsNotNone(statusbar.status_ip)
        self.assertEqual(statusbar.last_session_uploaded, 0)
        self.assertEqual(statusbar.last_session_downloaded, 0)
        self.assertIsNotNone(statusbar.last_execution_time)
        mock_logger_info.assert_called_with(
            "StatusBar startup", extra={"class_name": "Statusbar"}
        )

    @patch("d_fake_seeder.lib.views.statusbar.requests.get")
    @pytest.mark.timeout(5)
    def test_get_ip(self, mock_requests_get):
        statusbar = Statusbar(MagicMock(), MagicMock())

        # Test case where response code is 200
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.content.decode.return_value = "192.168.1.1"
        self.assertEqual(statusbar.get_ip(), "192.168.1.1")

        # Test case where response code is not 200
        mock_requests_get.return_value.status_code = 404
        self.assertEqual(statusbar.get_ip(), "")

    @pytest.mark.timeout(5)
    def test_sum_column_values(self):
        statusbar = Statusbar(MagicMock(), MagicMock())
        statusbar.model.get_liststore = MagicMock(
            return_value=(
                ["session_uploaded", "total_uploaded"],
                [[100, 200], [150, 250]],
            )
        )

        self.assertEqual(statusbar.sum_column_values("session_uploaded"), 250)
        self.assertEqual(statusbar.sum_column_values("total_uploaded"), 450)

    @patch("d_fake_seeder.lib.views.statusbar.humanbytes")
    @patch("d_fake_seeder.lib.views.statusbar.time.time")
    @pytest.mark.timeout(5)
    def test_update_view(self, mock_time, mock_humanbytes):
        statusbar = Statusbar(MagicMock(), MagicMock())
        statusbar.settings = MagicMock(tickspeed=1)
        statusbar.model.get_liststore = MagicMock(
            return_value=(
                ["session_uploaded", "total_uploaded"],
                [[100, 200], [150, 250]],
            )
        )

        mock_time.return_value = 0
        statusbar.last_execution_time = 0
        statusbar.last_session_uploaded = 0
        statusbar.last_session_downloaded = 0

        mock_humanbytes.side_effect = lambda x: f"{x}B"

        statusbar.update_view(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        self.assertEqual(statusbar.status_uploading.get_text(), " 100B /s")
        self.assertEqual(statusbar.status_uploaded.get_text(), " 100B / 200B")
        self.assertEqual(statusbar.status_downloading.get_text(), " 150B /s")
        self.assertEqual(statusbar.status_downloaded.get_text(), " 150B / 250B")
        self.assertEqual(statusbar.status_ip.get_text(), "  0.0.0.0")

    @patch("d_fake_seeder.lib.views.statusbar.logger.info")
    @pytest.mark.timeout(5)
    def test_handle_settings_changed(self, mock_logger_info):
        statusbar = Statusbar(MagicMock(), MagicMock())
        statusbar.handle_settings_changed("source", "key", "value")

        mock_logger_info.assert_called_with(
            "StatusBar settings changed", extra={"class_name": "Statusbar"}
        )


if __name__ == "__main__":
    unittest.main()
