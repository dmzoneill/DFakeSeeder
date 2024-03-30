import unittest
from unittest.mock import MagicMock, patch

import pytest

from d_fake_seeder.lib.views.notebook import Notebook


class TestNotebook(unittest.TestCase):
    @patch("d_fake_seeder.lib.views.notebook.logger.info")
    @pytest.mark.timeout(5)
    def test_init(self, mock_logger_info):
        builder = MagicMock()
        model = MagicMock()
        notebook = Notebook(builder, model)

        self.assertEqual(notebook.builder, builder)
        self.assertEqual(notebook.model, model)
        self.assertIsNone(notebook.selected_path)
        self.assertIsNotNone(notebook.notebook)
        self.assertIsNotNone(notebook.torrents_treeview)
        self.assertIsNotNone(notebook.peers_treeview)
        self.assertIsNotNone(notebook.log_scroll)
        self.assertIsNotNone(notebook.log_viewer)
        self.assertIsNotNone(notebook.settings)
        mock_logger_info.assert_called_with(
            "Notebook view startup", extra={"class_name": "Notebook"}
        )

    @patch("d_fake_seeder.lib.views.notebook.logger.info")
    @pytest.mark.timeout(5)
    def test_get_selected_torrent(self, mock_logger_info):
        notebook = Notebook(MagicMock(), MagicMock())
        notebook.torrents_treeview = MagicMock()
        notebook.model = MagicMock()
        notebook.model.torrent_list = [MagicMock(id=1), MagicMock(id=2)]
        notebook.torrents_treeview.get_selection().get_selected.return_value = (  # noqa
            None,
            None,
        )

        result = notebook.get_selected_torrent()

        self.assertFalse(result)

        notebook.torrents_treeview.get_selection().get_selected.return_value = (  # noqa
            MagicMock(),
            MagicMock(),
        )
        result = notebook.get_selected_torrent()

        self.assertTrue(result)
        self.assertEqual(result.id, 1)

    @patch("d_fake_seeder.lib.views.notebook.logger.info")
    @pytest.mark.timeout(5)
    def test_on_selection_changed(self, mock_logger_info):
        notebook = Notebook(MagicMock(), MagicMock())
        notebook.torrents_treeview = MagicMock()
        notebook.torrents_treeview.get_selection().get_selected.return_value = (  # noqa
            None,
            None,
        )

        notebook.on_selection_changed(MagicMock())

        notebook.torrents_treeview.get_selection().get_selected.return_value = (  # noqa
            MagicMock(),
            MagicMock(),
        )
        notebook.model = MagicMock(
            get_liststore_item=MagicMock(),
            torrent_list=[MagicMock(get_seeder=MagicMock(peers=[1, 2]))],
        )

        notebook.on_selection_changed(MagicMock())

        self.assertTrue(notebook.model.get_liststore_item.called)
        self.assertTrue(notebook.update_notebook_peers.called)

    @patch("d_fake_seeder.lib.views.notebook.logger.info")
    @pytest.mark.timeout(5)
    def test_update_notebook_peers(self, mock_logger_info):
        notebook = Notebook(MagicMock(), MagicMock())
        notebook.peers_treeview = MagicMock()

        # Case where store is None
        notebook.model.get_liststore_item.return_value.get_seeder.return_value.peers = (
            [  # noqa
                1,
                2,
            ]
        )
        notebook.update_notebook_peers(1)

        self.assertTrue(notebook.peers_treeview.set_model.called)
        self.assertTrue(notebook.peers_treeview.get_model.called)
        self.assertEqual(
            len(notebook.peers_treeview.get_model().append.call_args_list), 2
        )

        # Case where store already has rows
        store = MagicMock()
        store.clear = MagicMock()
        notebook.peers_treeview.get_model.return_value = store
        notebook.model.get_liststore_item.return_value.get_seeder.return_value.peers = (
            [  # noqa
                1,
                2,
                3,
            ]
        )

        notebook.update_notebook_peers(1)

        self.assertTrue(store.clear.called)
        self.assertEqual(
            len(notebook.peers_treeview.get_model().append.call_args_list), 3
        )

    @patch("d_fake_seeder.lib.views.notebook.logger.info")
    @pytest.mark.timeout(5)
    def test_update_notebook_options(self, mock_logger_info):
        notebook = Notebook(MagicMock(), MagicMock())
        notebook.model = MagicMock(torrent_list=[MagicMock(id=1, emit=MagicMock())])
        notebook.settings = MagicMock(
            editwidgets={"attr1": "Gtk.Switch", "attr2": "Gtk.Adjustment"}
        )
        notebook.builder = MagicMock()
        notebook.builder.get_object = MagicMock(return_value=MagicMock())

        notebook.update_notebook_options(1)

        self.assertEqual(len(notebook.builder.get_object.call_args_list), 4)

    @patch("d_fake_seeder.lib.views.notebook.logger.info")
    @pytest.mark.timeout(5)
    def test_update_notebook_status(self, mock_logger_info):
        notebook = Notebook(MagicMock(), MagicMock())
        notebook.model = MagicMock(
            get_liststore=MagicMock(return_value=(["attr1", "attr2"], MagicMock()))
        )
        notebook.selected_path = 1

        notebook.update_notebook_status(1)

        self.assertTrue(notebook.status_tab.add.called)

    @patch("d_fake_seeder.lib.views.notebook.logger.info")
    @pytest.mark.timeout(5)
    def test_handle_settings_changed(self, mock_logger_info):
        notebook = Notebook(MagicMock(), MagicMock())
        notebook.handle_settings_changed("source", "key", "value")

        mock_logger_info.assert_called_with(
            "Notebook settings changed", extra={"class_name": "Notebook"}
        )


if __name__ == "__main__":
    unittest.main()
