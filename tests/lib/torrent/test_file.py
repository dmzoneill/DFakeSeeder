import unittest
from unittest.mock import MagicMock, patch

import pytest

from d_fake_seeder.lib.torrent.file import File


class TestFile(unittest.TestCase):
    @patch("d_fake_seeder.lib.torrent.file.logger.info")
    @patch("builtins.open")
    @pytest.mark.timeout(5)
    def test_file_init_success(self, mock_open, mock_logger_info):
        mock_file = MagicMock()
        mock_file.read.return_value = b"dummy_data"
        mock_open.return_value = mock_file

        file = File("dummy_filepath")

        self.assertEqual(file.filepath, "dummy_filepath")
        self.assertTrue(file.raw_torrent)
        self.assertTrue(file.torrent_header)
        self.assertTrue(file.announce)
        self.assertTrue(file.file_hash)
        mock_logger_info.assert_called_with("File Startup", extra={"class_name": "File"})

    @pytest.mark.timeout(5)
    @patch("d_fake_seeder.lib.torrent.file.logger.info")
    @patch("builtins.open")
    def test_file_init_exception(self, mock_open, mock_logger_info):
        mock_open.side_effect = Exception("Mocked exception")

        file = File("dummy_filepath")

        self.assertIsNone(file.announce)
        self.assertIsNone(file.file_hash)
        mock_logger_info.assert_called_with(
            "File read error: Mocked exception",
            extra={"class_name": "File"},
        )

    @pytest.mark.timeout(5)
    def test_total_size_single_file_mode(self):
        file = File("dummy_filepath")
        file.torrent_header = {b"info": {b"length": 100}}
        self.assertEqual(file.total_size, 100)

    @pytest.mark.timeout(5)
    def test_total_size_multiple_file_mode(self):
        file = File("dummy_filepath")
        file.torrent_header = {b"info": {b"files": [{b"length": 50}, {b"length": 75}]}}
        self.assertEqual(file.total_size, 125)

    @pytest.mark.timeout(5)
    def test_name(self):
        file = File("dummy_filepath")
        file.torrent_header = {b"info": {b"name": b"test_file"}}
        self.assertEqual(file.name, "test_file")

    @patch("d_fake_seeder.lib.torrent.file.logger.debug")
    @pytest.mark.timeout(5)
    def test_str_method(self, mock_logger_debug):
        file = File("dummy_filepath")
        file.torrent_header = {
            b"announce": b"dummy_announce",
            b"creation date": 1633372800,
            b"created by": b"dummy_creator",
            b"encoding": b"utf-8",
            b"info": {
                b"piece length": 65536,
                b"pieces": b"1234567890" * 20,
                b"name": b"test_torrent",
                b"length": 1024,
                b"md5sum": b"abc123",
            },
        }

        result = str(file)

        expected_result = "Announce: dummy_announce\n"
        expected_result += "Date: 2021/10/05 00:00:00\n"
        expected_result += "Created by: dummy_creator\n"
        expected_result += "Encoding:   utf-8\n"
        expected_result += "Piece len: 64.0KiB\n"
        expected_result += "Pieces: 1\n"
        expected_result += "Name: test_torrent\n"
        expected_result += "Length: 1.0KiB\n"
        expected_result += "Md5: abc123\n"

        self.assertEqual(result, expected_result)
        mock_logger_debug.assert_called_with(
            "File attribute", extra={"class_name": "File"}
        )
