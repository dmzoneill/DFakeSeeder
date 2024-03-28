import unittest
from unittest.mock import patch, MagicMock
from d_fake_seeder.lib.views.states import States
import pytest


class TestStates(unittest.TestCase):
    @patch("d_fake_seeder.lib.views.states.logger.info")
    @pytest.mark.timeout(5)
    def test_init(self, mock_logger_info):
        builder = MagicMock()
        model = MagicMock()
        states = States(builder, model)

        self.assertEqual(states.builder, builder)
        self.assertEqual(states.model, model)
        self.assertIsNotNone(states.settings)
        self.assertIsNotNone(states.states_treeview)
        mock_logger_info.assert_called_with(
            "States startup", extra={"class_name": "States"}
        )

    @patch("d_fake_seeder.lib.views.states.logger.debug")
    @pytest.mark.timeout(5)
    def test_update_view(self, mock_logger_debug):
        states = States(MagicMock(), MagicMock())
        states.states_treeview = MagicMock()
        states.model.get_trackers_liststore = MagicMock(return_value=MagicMock())

        states.update_view(MagicMock(), MagicMock(), MagicMock(), MagicMock())

        self.assertTrue(states.states_treeview.set_model.called)
        self.assertEqual(len(states.states_treeview.append_column.call_args_list), 2)

    @patch("d_fake_seeder.lib.views.states.logger.debug")
    @pytest.mark.timeout(5)
    def test_handle_settings_changed(self, mock_logger_debug):
        states = States(MagicMock(), MagicMock())
        states.handle_settings_changed("source", "key", "value")

        mock_logger_debug.assert_called_with(
            "States settings update", extra={"class_name": "States"}
        )


if __name__ == "__main__":
    unittest.main()
