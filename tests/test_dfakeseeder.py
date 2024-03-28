import unittest
from unittest.mock import patch, call
from d_fake_seeder.dfakeseeder import DFakeSeeder
import pytest


class TestDFakeSeeder(unittest.TestCase):
    @patch("d_fake_seeder.dfakeseeder.logger.info")
    @pytest.mark.timeout(5)
    def test_init(self, mock_start, mock_logger_info):
        DFakeSeeder()
        mock_logger_info.assert_has_calls(
            [
                call("Startup", extra={"class_name": "DFakeSeeder"}),
                call("Settings get instance", extra={"class_name": "Settings"}),
            ]
        )

    @patch("d_fake_seeder.dfakeseeder.logger.info")
    @patch("d_fake_seeder.dfakeseeder.Controller.run")
    @pytest.mark.timeout(5)
    def test_do_activate(self, mock_controller_run, mock_logger_info):
        DFakeSeeder().do_activate()

        expected_calls = [
            call("Startup", extra={"class_name": "DFakeSeeder"}),
            call("Run Controller", extra={"class_name": "DFakeSeeder"}),
            call("Settings get instance", extra={"class_name": "Settings"}),
            call("View instantiate", extra={"class_name": "View"}),
            call("Model instantiate", extra={"class_name": "Model"}),
        ]

        actual_calls = mock_logger_info.call_args_list
        for expected_call in expected_calls:
            assert expected_call in actual_calls

        mock_controller_run.assert_called_once()

    @patch("d_fake_seeder.dfakeseeder.logger.info")
    @patch("d_fake_seeder.dfakeseeder.DFakeSeeder.start")
    @pytest.mark.timeout(5)
    def test_handle_settings_changed(self, mock_start, mock_logger_info):
        fake_seeder = DFakeSeeder()
        fake_seeder.handle_settings_changed(None, "key", "value")
        mock_logger_info.assert_called_with(
            "Settings changed", extra={"class_name": "DFakeSeeder"}
        )


if __name__ == "__main__":
    unittest.main()
