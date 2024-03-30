import unittest
from unittest.mock import patch, MagicMock
from gi.repository import Gtk, GLib
import webbrowser

from d_fake_seeder.lib.view import View  # Import your View class here
from d_fake_seeder.lib.logger import logger
import pytest


class TestViewSetupWindow(unittest.TestCase):
    @pytest.mark.timeout(5)
    def test_setup_window(self):
        view = View(MagicMock())

        view.window = MagicMock()
        view.window.get_screen.return_value.get_width.return_value = 1920
        view.window.get_screen.return_value.get_height.return_value = 1080

        view.window.get_size.return_value = (800, 600)

        view.setup_window()

        view.window.set_icon.assert_called()
        view.window.set_title.assert_called()
        view.window.set_position.assert_called()
        view.window.move.assert_called()

    @pytest.mark.timeout(5)
    def test_show_splash_image(self):
        view = View(MagicMock())
        view.overlay = MagicMock()
        view.fade_out_image = MagicMock()

        view.show_splash_image()

        view.splash_image.set_from_file.assert_called()
        view.splash_image.show.assert_called()
        view.splash_image.set_valign.assert_called()
        view.splash_image.set_halign.assert_called()
        view.overlay.add_overlay.assert_called()
        GLib.timeout_add_seconds.assert_called_with(2, view.fade_out_image)

    @pytest.mark.timeout(5)
    def test_fade_out_image(self):
        view = View(MagicMock())
        view.splash_image = MagicMock()
        view.fade_image = MagicMock()

        view.fade_out_image()

        view.splash_image.fade_out = 1.0
        GLib.timeout_add.assert_called_with(75, view.fade_image)

    @pytest.mark.timeout(5)
    def test_fade_image(self):
        view = View(MagicMock())
        view.splash_image = MagicMock()
        view.splash_image.fade_out = 0.5

        self.assertTrue(view.fade_image())

        view.splash_image.set_opacity.assert_called_with(0.475)

    @pytest.mark.timeout(5)
    def test_resize_panes(self):
        view = View(MagicMock())
        view.main_paned = MagicMock()
        view.main_paned.get_allocation.return_value.height = 800

        view.resize_panes()

        view.main_paned.set_position.assert_called_with(400)
        self.assertEqual(view.status_position, 400)

    @pytest.mark.timeout(5)
    def test_notify(self):
        view = View(MagicMock())
        view.notify_label = MagicMock()
        view.status = MagicMock()
        view.timeout_id = 1

        view.notify("Test Notification")

        view.notify_label.set_no_show_all.assert_called_with(False)
        view.notify_label.set_visible.assert_called_with(True)
        view.notify_label.set_text.assert_called_with("Test Notification")
        view.status.set_text.assert_called_with("Test Notification")
        GLib.timeout_add.assert_called_with(3000, view.notify_label.set_no_show_all)

    @pytest.mark.timeout(5)
    def test_set_model(self):
        view = View(MagicMock())
        model = MagicMock()

        view.set_model(model)

        self.assertEqual(view.model, model)
        view.notebook.set_model.assert_called_with(model)
        view.toolbar.set_model.assert_called_with(model)
        view.torrents.set_model.assert_called_with(model)
        view.states.set_model.assert_called_with(model)
        view.statusbar.set_model.assert_called_with(model)

    @pytest.mark.timeout(5)
    def test_connect_signals(self):
        view = View(MagicMock())
        view.window = MagicMock()
        view.quit_menu_item = MagicMock()
        view.help_menu_item = MagicMock()
        view.model = MagicMock()

        view.connect_signals()

        view.window.connect.assert_any_call("destroy", view.quit)
        view.window.connect.assert_any_call("delete-event", view.quit)
        view.quit_menu_item.connect.assert_called_with("activate", view.on_quit_clicked)
        view.help_menu_item.connect.assert_called_with("activate", view.on_help_clicked)
        view.model.connect.assert_any_call("data-changed", view.torrents.update_view)
        view.model.connect.assert_any_call("data-changed", view.notebook.update_view)
        view.model.connect.assert_any_call("data-changed", view.states.update_view)
        view.model.connect.assert_any_call("data-changed", view.statusbar.update_view)

    @pytest.mark.timeout(5)
    def test_remove_signals(self):
        view = View(MagicMock())
        view.model = MagicMock()
        view.torrents.update_view = MagicMock()
        view.notebook.update_view = MagicMock()
        view.states.update_view = MagicMock()
        view.statusbar.update_view = MagicMock()

        view.remove_signals()

        view.model.disconnect_by_func.assert_any_call(view.torrents.update_view)
        view.model.disconnect_by_func.assert_any_call(view.notebook.update_view)
        view.model.disconnect_by_func.assert_any_call(view.states.update_view)
        view.model.disconnect_by_func.assert_any_call(view.statusbar.update_view)

    @pytest.mark.timeout(5)
    def test_on_quit_clicked(self):
        view = View(MagicMock())
        view.remove_signals = MagicMock()
        view.quit = MagicMock()
        menu_item = MagicMock()

        view.on_quit_clicked(menu_item)

        view.remove_signals.assert_called()
        view.quit.assert_called()

    @pytest.mark.timeout(5)
    def test_on_help_clicked(self):
        view = View(MagicMock())
        view.settings = MagicMock()
        view.settings.issues_page = "https://github.com/issues"
        webbrowser.open = MagicMock()
        menu_item = MagicMock()

        view.on_help_clicked(menu_item)

        webbrowser.open.assert_called_with("https://github.com/issues")

    @patch("sys.exit")
    @patch("builtins.exit")
    @pytest.mark.timeout(5)
    def test_quit(self, mock_exit, sys_exit):
        view = View(MagicMock())
        view.model = MagicMock()
        view.model.torrent_list = [MagicMock(), MagicMock()]
        view.settings = MagicMock()
        view.window = MagicMock()

        view.quit()

        for torrent in view.model.torrent_list:
            torrent.stop.assert_called()
        view.settings.save_quit.assert_called()
        view.window.destroy.assert_called()
        Gtk.main_quit.assert_called()
        mock_exit.assert_called_with(0)

    @pytest.mark.timeout(5)
    def test_handle_settings_changed(self):
        view = View(MagicMock())
        source = MagicMock()
        key = "test_key"
        value = "test_value"

        view.handle_settings_changed(source, key, value)

        logger.info.assert_called_with(
            "View settings changed",
            extra={"class_name": view.__class__.__name__},
        )


if __name__ == "__main__":
    unittest.main()
