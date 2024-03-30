import unittest
from unittest.mock import patch, MagicMock
from d_fake_seeder.lib.settings import Settings
import pytest


class TestSettings(unittest.TestCase):
    @pytest.mark.timeout(5)
    @patch("d_fake_seeder.lib.settings.os")
    @patch("d_fake_seeder.lib.settings.shutil")
    def test_get_instance_returns_existing_instance(self, mock_shutil, mock_os):
        mock_os.path.exists.return_value = (
            False  # Simulate destination directory doesn't exist
        )
        mock_settings = MagicMock()
        mock_settings._file_path = "test_settings.json"
        Settings._instance = mock_settings  # Simulate an existing instance
        instance = Settings.get_instance()
        self.assertEqual(instance, mock_settings)


if __name__ == "__main__":
    unittest.main()
