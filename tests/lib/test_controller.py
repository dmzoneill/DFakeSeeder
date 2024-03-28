import unittest
from unittest.mock import MagicMock
from d_fake_seeder.lib.controller import Controller
import os
import pytest


class TestController(unittest.TestCase):
    def setUp(self):
        self.view = MagicMock()
        self.model = MagicMock()
        self.controller = Controller(self.view, self.model)

    @pytest.mark.timeout(5)
    def test_run(self):
        os.listdir = MagicMock(return_value=["file1.torrent", "file2.torrent"])
        os.path.join = MagicMock(return_value="/path/to/file1.torrent")
        self.controller.run()
        self.model.add_torrent.assert_called_with("/path/to/file1.torrent")

    @pytest.mark.timeout(5)
    def test_handle_settings_changed(self):
        self.controller.handle_settings_changed("source", "key", "value")
        # Add assertions based on expected behavior


if __name__ == "__main__":
    unittest.main()
