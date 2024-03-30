import unittest
from unittest.mock import MagicMock

import pytest

from d_fake_seeder.lib.handlers import FileModifiedEventHandler


class TestFileModifiedEventHandler(unittest.TestCase):
    def setUp(self):
        self.settings_instance = MagicMock()
        self.file_event_handler = FileModifiedEventHandler(self.settings_instance)

    @pytest.mark.timeout(5)
    def test_on_modified_with_matching_path(self):
        event = MagicMock(src_path="file_path")
        self.settings_instance._file_path = "file_path"

        self.file_event_handler.on_modified(event)

        self.settings_instance.load_settings.assert_called_once()

    @pytest.mark.timeout(5)
    def test_on_modified_with_non_matching_path(self):
        event = MagicMock(src_path="other_path")
        self.settings_instance._file_path = "file_path"

        self.file_event_handler.on_modified(event)

        self.settings_instance.load_settings.assert_not_called()


if __name__ == "__main__":
    unittest.main()
