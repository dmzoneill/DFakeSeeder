import unittest
from unittest.mock import patch, MagicMock
from d_fake_seeder.lib.torrent.seeder import Seeder
import pytest


class TestSeeder(unittest.TestCase):
    @patch("d_fake_seeder.lib.torrent.seeder.logger.info")
    @pytest.mark.timeout(5)
    def test_seeder_init(self, mock_logger_info):
        seeder = Seeder(torrent=MagicMock())

        self.assertTrue(seeder.tracker_semaphore)
        self.assertEqual(seeder.peer_id, "-DE13F0-" + "mock_id")
        self.assertTrue(seeder.download_key)
        self.assertTrue(seeder.port)
        self.assertFalse(seeder.info)
        self.assertFalse(seeder.active)
        mock_logger_info.assert_called_with(
            "Seeder Startup", extra={"class_name": "Seeder"}
        )

    @patch("d_fake_seeder.lib.torrent.seeder.logger.info")
    @pytest.mark.timeout(5)
    def test_recreate_semaphore(self, mock_logger_info):
        seeder = Seeder(torrent=MagicMock())
        seeder.settings.concurrent_http_connections = 5

        Seeder.recreate_semaphore(seeder)

        self.assertEqual(Seeder.tracker_semaphore._value, 5)
        mock_logger_info.assert_called_with(
            "Seeder recreate_semaphore", extra={"class_name": "Seeder"}
        )

    @patch("d_fake_seeder.lib.torrent.seeder.requests.get")
    @patch("d_fake_seeder.lib.torrent.seeder.logger.info")
    @pytest.mark.timeout(5)
    def test_load_peers_http_success(self, mock_logger_info, mock_requests_get):
        seeder = Seeder(torrent=MagicMock())
        seeder.torrent.announce = "http://test-tracker.com"
        seeder.settings.proxies = {}
        seeder.settings.http_headers = {}
        mock_requests_get.return_value.content = b"dummy_data"

        result = seeder.load_peers()

        self.assertTrue(result)
        self.assertTrue(seeder.info)
        mock_logger_info.assert_called_with(
            "Seeder load peers", extra={"class_name": "Seeder"}
        )

    @patch("d_fake_seeder.lib.torrent.seeder.logger.info")
    @pytest.mark.timeout(5)
    def test_load_peers_no_announce(self, mock_logger_info):
        seeder = Seeder(torrent=MagicMock())
        result = seeder.load_peers()

        self.assertFalse(result)
        self.assertFalse(seeder.info)
        mock_logger_info.assert_called_with(
            "Seeder load peers", extra={"class_name": "Seeder"}
        )

    # Add more test cases as needed


if __name__ == "__main__":
    unittest.main()
