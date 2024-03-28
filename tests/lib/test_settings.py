import unittest
from unittest.mock import patch
from d_fake_seeder.lib.settings import Settings
import pytest


class TestSettings(unittest.TestCase):
    @patch("d_fake_seeder.lib.settings.Observer")
    @patch("d_fake_seeder.lib.settings.FileModifiedEventHandler")
    def setUp(self, mock_file_handler, mock_observer):
        self.file_path = "test_settings.json"
        self.settings = Settings.get_instance(self.file_path)

    @pytest.mark.timeout(5)
    def test_get_instance(self):
        file_path = "test_settings.json"
        instance = Settings.get_instance(file_path)
        self.assertEqual(instance._file_path, file_path)

    @pytest.mark.timeout(5)
    def test_load_settings_file_not_found(self):
        self.settings.load_settings()
        # Add assertions based on expected behavior

    @patch("d_fake_seeder.lib.settings.json.load")
    @pytest.mark.timeout(5)
    def test_load_settings_file_found(self, mock_json_load):
        self.settings._last_modified = 0
        self.settings.load_settings()
        # Add assertions based on expected behavior

    @patch("d_fake_seeder.lib.settings.json.dump")
    @pytest.mark.timeout(5)
    def test_save_settings(self, mock_json_dump):
        self.settings.save_settings()
        # Add assertions based on expected behavior

    @pytest.mark.timeout(5)
    def test_save_quit(self):
        with patch.object(self.settings, "save_settings") as mock_save_settings:
            self.settings.save_quit()
            mock_save_settings.assert_called_once()

    @pytest.mark.timeout(5)
    def test_getattr_settings(self):
        attr_name = "upload_speed"
        attr_value = self.settings.__getattr__(attr_name)
        self.assertEqual(attr_value, self.settings._settings[attr_name])

    @pytest.mark.timeout(5)
    def test_getattr_non_existent_setting(self):
        with self.assertRaises(AttributeError):
            self.settings.__getattr__("non_existent_setting")

    @pytest.mark.timeout(5)
    def test_setattr_settings(self):
        attr_name = "upload_speed"
        new_value = 100
        self.settings.__setattr__(attr_name, new_value)
        self.assertEqual(self.settings._settings[attr_name], new_value)

    @pytest.mark.timeout(5)
    def test_setattr_non_settings_attribute(self):
        with self.assertRaises(AttributeError):
            self.settings.__setattr__("non_setting_attribute", "value")


if __name__ == "__main__":
    unittest.main()
