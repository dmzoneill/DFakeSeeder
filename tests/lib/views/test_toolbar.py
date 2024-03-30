import unittest
from unittest.mock import MagicMock, patch

import pytest

from d_fake_seeder.lib.views.toolbar import Toolbar


class TestToolbar(unittest.TestCase):
    @patch("d_fake_seeder.lib.views.toolbar.logger.info")
    @pytest.mark.timeout(5)
    def test_init(self, mock_logger_info):
        builder = MagicMock()
        model = MagicMock()
        toolbar = Toolbar(builder, model)

        self.assertEqual(toolbar.builder, builder)
        self.assertEqual(toolbar.model, model)
        self.assertIsNotNone(toolbar.settings)
        self.assertIsNotNone(toolbar.toolbar_add_button)
        self.assertIsNotNone(toolbar.toolbar_remove_button)
        self.assertIsNotNone(toolbar.toolbar_pause_button)
        self.assertIsNotNone(toolbar.toolbar_resume_button)
        self.assertIsNotNone(toolbar.toolbar_up_button)
        self.assertIsNotNone(toolbar.toolbar_down_button)
        self.assertIsNotNone(toolbar.toolbar_settings_button)
        self.assertIsNotNone(toolbar.toolbar_refresh_rate)
        mock_logger_info.assert_called_with(
            "Toolbar startup", extra={"class_name": "Toolbar"}
        )

    @patch("d_fake_seeder.lib.views.toolbar.os.remove")
    @pytest.mark.timeout(5)
    def test_on_toolbar_remove_clicked(self, mock_os_remove):
        toolbar = Toolbar(MagicMock(), MagicMock())
        toolbar.get_selected_torrent = MagicMock(
            return_value=MagicMock(id=1, filepath="example/file.torrent")
        )
        toolbar.model.torrent_list = [MagicMock(id=1)]

        toolbar.on_toolbar_remove_clicked(MagicMock())
        mock_os_remove.assert_called_with("example/file.torrent")
        self.assertEqual(toolbar.model.torrent_list, [])

    @patch("d_fake_seeder.lib.views.toolbar.logger.info")
    @pytest.mark.timeout(5)
    def test_on_toolbar_pause_clicked(self, mock_logger_info):
        toolbar = Toolbar(MagicMock(), MagicMock())
        toolbar.get_selected_torrent = MagicMock(return_value=MagicMock(active=True))

        toolbar.on_toolbar_pause_clicked(MagicMock())
        self.assertFalse(toolbar.get_selected_torrent().active)
        mock_logger_info.assert_called_with(
            "Toolbar pause button clicked", extra={"class_name": "Toolbar"}
        )

    @patch("d_fake_seeder.lib.views.toolbar.logger.info")
    @pytest.mark.timeout(5)
    def test_on_toolbar_resume_clicked(self, mock_logger_info):
        toolbar = Toolbar(MagicMock(), MagicMock())
        toolbar.get_selected_torrent = MagicMock(return_value=MagicMock(active=False))

        toolbar.on_toolbar_resume_clicked(MagicMock())
        self.assertTrue(toolbar.get_selected_torrent().active)
        mock_logger_info.assert_called_with(
            "Toolbar resume button clicked", extra={"class_name": "Toolbar"}
        )

    @patch("d_fake_seeder.lib.views.toolbar.logger.info")
    @pytest.mark.timeout(5)
    def test_on_toolbar_up_clicked(self, mock_logger_info):
        toolbar = Toolbar(MagicMock(), MagicMock())
        toolbar.get_selected_torrent = MagicMock(return_value=MagicMock(id=1))
        toolbar.model.torrent_list = [MagicMock(id=1), MagicMock(id=2)]

        toolbar.on_toolbar_down_clicked(MagicMock())
        self.assertEqual(toolbar.model.torrent_list[0].id, 2)
        self.assertEqual(toolbar.model.torrent_list[1].id, 1)
        mock_logger_info.assert_called_with(
            "Toolbar down button clicked", extra={"class_name": "Toolbar"}
        )

    @patch("d_fake_seeder.lib.views.toolbar.logger.info")
    @pytest.mark.timeout(5)
    def test_on_toolbar_settings_clicked(self, mock_logger_info):
        toolbar = Toolbar(MagicMock(), MagicMock())
        toolbar.get_selected_torrent = MagicMock(return_value=None)

        toolbar.on_toolbar_settings_clicked(MagicMock())
        mock_logger_info.assert_not_called()

        toolbar.get_selected_torrent = MagicMock(return_value=MagicMock())
        toolbar.on_toolbar_settings_clicked(MagicMock())
        mock_logger_info.assert_called_with(
            "Toolbar settings button clicked", extra={"class_name": "Toolbar"}
        )
