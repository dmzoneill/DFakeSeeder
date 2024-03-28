import unittest
from unittest.mock import patch, MagicMock
from d_fake_seeder.lib.torrent.torrent import Torrent
import pytest


class TestTorrent(unittest.TestCase):
    @patch("d_fake_seeder.lib.torrent.torrent.logger.info")
    @pytest.mark.timeout(5)
    def test_torrent_init(self, mock_logger_info):
        filepath = "dummy_filepath"
        torrent = Torrent(filepath)

        self.assertTrue(torrent.settings)
        self.assertTrue(torrent.torrent_file)
        self.assertTrue(torrent.seeder)
        self.assertTrue(torrent.torrent_worker_stop_event)
        self.assertTrue(torrent.torrent_worker.is_alive())
        mock_logger_info.assert_called_with(
            "Torrent instantiate", extra={"class_name": "Torrent"}
        )

    @patch("d_fake_seeder.lib.torrent.torrent.GLib.idle_add")
    @patch("time.sleep")
    @patch("d_fake_seeder.lib.torrent.torrent.logger.info")
    @pytest.mark.timeout(5)
    def test_update_torrent_worker(
        self, mock_logger_info, mock_time_sleep, mock_idle_add
    ):
        torrent = Torrent("dummy_filepath")
        torrent.torrent_worker_stop_event.set()

        torrent.update_torrent_worker()

        self.assertFalse(torrent.torrent_worker.is_alive())
        mock_logger_info.assert_called_with(
            "Torrent update worker", extra={"class_name": "Torrent"}
        )

    @patch("d_fake_seeder.lib.torrent.torrent.GLib.idle_add")
    @patch("time.sleep")
    @patch("d_fake_seeder.lib.torrent.torrent.logger.debug")
    @pytest.mark.timeout(5)
    def test_update_torrent_callback(
        self, mock_logger_debug, mock_time_sleep, mock_idle_add
    ):
        torrent = Torrent("dummy_filepath")
        torrent.active = True
        torrent.settings.tickspeed = 5

        torrent.update_torrent_callback()

        self.assertTrue(torrent.name)
        self.assertTrue(torrent.total_size)
        self.assertTrue(torrent.seeders)
        self.assertTrue(torrent.leechers)
        self.assertTrue(torrent.threshold)
        self.assertTrue(torrent.uploading)
        self.assertTrue(torrent.session_uploaded)
        self.assertTrue(torrent.session_downloaded)
        self.assertTrue(torrent.total_uploaded)
        self.assertTrue(torrent.total_downloaded)
        self.assertTrue(torrent.next_update)
        mock_logger_debug.assert_called_with(
            "Torrent torrent update callback", extra={"class_name": "Torrent"}
        )

    @patch("d_fake_seeder.lib.torrent.torrent.logger.info")
    @patch("d_fake_seeder.lib.torrent.torrent.View.instance.notify")
    @pytest.mark.timeout(5)
    def test_stop(self, mock_view_notify, mock_logger_info):
        torrent = Torrent("dummy_filepath")
        torrent.torrent_worker_stop_event.set()

        torrent.stop()

        self.assertFalse(torrent.torrent_worker.is_alive())
        mock_logger_info.assert_called_with(
            "Torrent stop", extra={"class_name": "Torrent"}
        )
        mock_view_notify.assert_called_with("Stopping fake seeder " + torrent.name)

    @patch("d_fake_seeder.lib.torrent.torrent.logger.info")
    @pytest.mark.timeout(5)
    def test_get_seeder(self, mock_logger_info):
        torrent = Torrent("dummy_filepath")
        seeder = torrent.get_seeder()

        self.assertEqual(seeder, torrent.seeder)
        mock_logger_info.assert_called_with(
            "Torrent get seeder", extra={"class_name": "Torrent"}
        )

    @patch("d_fake_seeder.lib.torrent.torrent.GObject.Object.emit")
    @patch("time.sleep")
    @patch("d_fake_seeder.lib.torrent.torrent.logger.debug")
    @pytest.mark.timeout(5)
    def test_handle_settings_changed(
        self, mock_logger_debug, mock_time_sleep, mock_gobject_emit
    ):
        torrent = Torrent("dummy_filepath")
        source = "source"
        key = "key"
        value = "value"

        torrent.handle_settings_changed(source, key, value)

        mock_logger_debug.assert_called_with(
            "Torrent settings changed", extra={"class_name": "Torrent"}
        )
        mock_gobject_emit.assert_called_with(
            "attribute-changed", torrent, {source: key}
        )

    @patch("d_fake_seeder.lib.torrent.torrent.logger.info")
    @pytest.mark.timeout(5)
    def test_getattr(self, mock_logger_info):
        torrent = Torrent("dummy_filepath")
        attr = "name"
        torrent.name = "test_name"

        result = torrent.__getattr__(attr)

        self.assertEqual(result, "test_name")

    @patch("d_fake_seeder.lib.torrent.torrent.logger.info")
    @pytest.mark.timeout(5)
    def test_setattr(self, mock_logger_info):
        torrent = Torrent("dummy_filepath")
        attr = "name"
        value = "test_name"

        torrent.__setattr__(attr, value)

        self.assertEqual(torrent.name, "test_name")
