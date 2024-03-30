import unittest
from unittest.mock import Mock, patch
from gi.repository import Gtk
from d_fake_seeder.lib.model import Model
import pytest


class TestModel(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    @patch("d_fake_seeder.lib.model.Torrent")
    @pytest.mark.timeout(5)
    def test_add_torrent(self, mock_torrent_class):
        mock_torrent_instance = Mock()  # Create a new Mock instance
        mock_torrent_instance.id = 2  # Set id attribute to integer

        mock_torrent_class.return_value = (
            mock_torrent_instance  # Set return value for Torrent class
        )

        mock_filepath = "test_filepath"
        mock_torrent = Mock()
        mock_torrent.id = 1
        mock_torrent_list = [mock_torrent]

        test_instance = Model()
        test_instance.torrent_list = mock_torrent_list
        test_instance.on_attribute_changed = Mock()
        test_instance.connect = Mock()
        test_instance.emit = Mock()

        test_instance.add_torrent(mock_filepath)

        self.assertEqual(len(test_instance.torrent_list), 2)
        self.assertTrue(
            all(t.id == i + 1 for i, t in enumerate(test_instance.torrent_list))
        )

        test_instance.emit.assert_called_once_with(
            "data-changed", test_instance, mock_torrent_instance, "add"
        )

    @patch("d_fake_seeder.lib.model.Torrent")
    @pytest.mark.timeout(5)
    def test_remove_torrent(self, mock_torrent_class):
        mock_filepath = "test_filepath"
        mock_torrent = Mock()
        mock_torrent_list = [mock_torrent]

        test_instance = Model()
        test_instance.torrent_list = mock_torrent_list
        test_instance.on_attribute_changed = Mock()
        test_instance.connect = Mock()
        test_instance.emit = Mock()

        test_instance.remove_torrent(mock_filepath)

        self.assertEqual(len(test_instance.torrent_list), 2)
        test_instance.emit.assert_called()

    @pytest.mark.timeout(5)
    def test_on_attribute_changed(self):
        mock_model = Mock()
        mock_torrent = Mock()
        mock_attributes = {"attribute1": "value1", "attribute2": "value2"}

        test_instance = Model()
        test_instance.emit = Mock()

        test_instance.on_attribute_changed(mock_model, mock_torrent, mock_attributes)

        test_instance.emit.assert_called_once_with(
            "data-changed", mock_model, mock_torrent, mock_attributes
        )

    @pytest.mark.timeout(5)
    def test_get_liststore(self):
        mock_filter_torrent = Mock()
        mock_torrent_list = [
            Mock(
                filepath="test_filepath",
                attribute1="value1",
                attribute2="value2",
            )
        ]

        test_instance = Model()
        test_instance.torrent_list = mock_torrent_list
        test_instance.logger = Mock()

        result = test_instance.get_liststore(mock_filter_torrent)

        # Verify the structure of result
        self.assertEqual(len(result), 2)
        self.assertIsInstance(result[0], list)
        self.assertIsInstance(result[1], Gtk.ListStore)

    @pytest.mark.timeout(5)
    def test_get_liststore_model(self):
        test_instance = Model()
        test_instance.logger = Mock()

        result = test_instance.get_liststore_model()

        self.assertIsInstance(result, Gtk.ListStore)

    @pytest.mark.timeout(5)
    def test_get_trackers_liststore(self):
        mock_torrent_list = [
            Mock(seeder=Mock(tracker="http://tracker1.com")),
            Mock(seeder=Mock(tracker="http://tracker2.com")),
        ]

        test_instance = Model()
        test_instance.torrent_list = mock_torrent_list
        test_instance.logger = Mock()

        result = test_instance.get_trackers_liststore()

        self.assertIsInstance(result, Gtk.ListStore)

    @pytest.mark.timeout(5)
    def test_get_liststore_item(self):
        mock_torrent_list = [Mock(), Mock()]

        test_instance = Model()
        test_instance.torrent_list = mock_torrent_list
        test_instance.logger = Mock()

        index = 0
        result = test_instance.get_liststore_item(index)

        self.assertEqual(result, mock_torrent_list[index])

    @pytest.mark.timeout(5)
    def test_handle_settings_changed(self):
        test_instance = Model()
        test_instance.logger = Mock()

        source = Mock()
        key = "test_key"
        value = "test_value"

        test_instance.handle_settings_changed(source, key, value)


if __name__ == "__main__":
    unittest.main()
