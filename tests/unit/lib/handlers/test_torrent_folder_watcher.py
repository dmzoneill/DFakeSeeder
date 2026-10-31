"""
Unit tests for the torrent watch-folder handler.

These cover the behaviour-preserving refactor of torrent_folder_watcher:
watch-path validation (exercised through the public ``start``), the
watchdog-unavailable fallbacks, and the file-processing pipeline (dedup,
copy-to-config, model add, optional delete, notification). The heavy GTK
``View`` dependency is mocked so the module imports headless.
"""

import contextlib
import sys
import types
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import MagicMock, patch


@contextlib.contextmanager
def loaded_watcher() -> Iterator[ModuleType]:
    """Import the watcher module with the heavy GTK ``View`` dependency mocked."""
    import importlib

    fake_view = types.ModuleType("d_fake_seeder.view")
    view_stub = MagicMock()
    view_stub.instance = None
    setattr(fake_view, "View", view_stub)
    saved_view = sys.modules.get("d_fake_seeder.view")
    sys.modules["d_fake_seeder.view"] = fake_view
    sys.modules.pop("d_fake_seeder.lib.handlers.torrent_folder_watcher", None)
    try:
        yield importlib.import_module("d_fake_seeder.lib.handlers.torrent_folder_watcher")
    finally:
        sys.modules.pop("d_fake_seeder.lib.handlers.torrent_folder_watcher", None)
        if saved_view is not None:
            sys.modules["d_fake_seeder.view"] = saved_view
        else:
            sys.modules.pop("d_fake_seeder.view", None)


def test_stub_fallbacks_expose_noop_interface() -> None:
    """When watchdog is unavailable the stubs provide the called methods as no-ops."""
    with loaded_watcher() as mod:
        if mod.WATCHDOG_AVAILABLE:
            import pytest

            pytest.skip("watchdog is installed; fallback stubs are not in use")

        observer = mod.Observer()
        assert observer.schedule("handler", "/path", recursive=False) is None
        assert observer.start() is None
        assert observer.stop() is None
        assert observer.join(timeout=1.0) is None

        event_handler = mod.FileSystemEventHandler()
        assert event_handler.dispatch(object()) is None
        assert event_handler.on_any_event(object()) is None


def test_start_returns_false_when_watchdog_unavailable() -> None:
    """start() must short-circuit to False when the watchdog library is missing."""
    with loaded_watcher() as mod, patch.object(mod, "WATCHDOG_AVAILABLE", False):
        watcher = mod.TorrentFolderWatcher(MagicMock(), MagicMock())
        assert watcher.start() is False


def _watcher_with_config(mod: ModuleType, config: dict) -> Any:
    settings = MagicMock()
    settings.watch_folder = config
    return mod.TorrentFolderWatcher(MagicMock(), settings)


def test_start_false_when_disabled() -> None:
    """A disabled watch folder makes start() return False."""
    with (
        loaded_watcher() as mod,
        patch.object(mod, "WATCHDOG_AVAILABLE", True),
        patch.object(mod, "Observer", MagicMock()),
    ):
        watcher = _watcher_with_config(mod, {"enabled": False, "path": "/tmp"})
        assert watcher.start() is False


def test_start_false_when_no_path() -> None:
    """An enabled watch folder with no path makes start() return False."""
    with (
        loaded_watcher() as mod,
        patch.object(mod, "WATCHDOG_AVAILABLE", True),
        patch.object(mod, "Observer", MagicMock()),
    ):
        watcher = _watcher_with_config(mod, {"enabled": True, "path": ""})
        assert watcher.start() is False


def test_start_false_when_path_missing(tmp_path: Path) -> None:
    """A non-existent watch path makes start() return False."""
    with (
        loaded_watcher() as mod,
        patch.object(mod, "WATCHDOG_AVAILABLE", True),
        patch.object(mod, "Observer", MagicMock()),
    ):
        watcher = _watcher_with_config(mod, {"enabled": True, "path": str(tmp_path / "missing")})
        assert watcher.start() is False


def test_start_false_when_path_is_file(tmp_path: Path) -> None:
    """A watch path pointing at a file (not a directory) makes start() return False."""
    a_file = tmp_path / "a_file.txt"
    a_file.write_text("x")
    with (
        loaded_watcher() as mod,
        patch.object(mod, "WATCHDOG_AVAILABLE", True),
        patch.object(mod, "Observer", MagicMock()),
    ):
        watcher = _watcher_with_config(mod, {"enabled": True, "path": str(a_file)})
        assert watcher.start() is False


def test_start_true_for_valid_directory(tmp_path: Path) -> None:
    """A valid, existing directory makes start() succeed and schedule the observer."""
    observer_cls = MagicMock()
    with (
        loaded_watcher() as mod,
        patch.object(mod, "WATCHDOG_AVAILABLE", True),
        patch.object(mod, "Observer", observer_cls),
    ):
        watcher = _watcher_with_config(mod, {"enabled": True, "path": str(tmp_path)})
        assert watcher.start() is True
        assert watcher.is_running is True
        observer_cls.return_value.schedule.assert_called_once()
        observer_cls.return_value.start.assert_called_once()


def _make_handler(mod: ModuleType, **config: object) -> tuple[Any, Any]:
    model = MagicMock()
    handler = mod.TorrentFileEventHandler(model, config)
    return handler, model


def test_process_copies_torrent_and_adds_to_model(tmp_path: Path) -> None:
    """A new torrent is copied into <config>/torrents and handed to the model."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    source = tmp_path / "new.torrent"
    source.write_bytes(b"d4:infod4:name4:testee")

    with loaded_watcher() as mod:
        handler, model = _make_handler(mod)
        with patch.object(mod, "get_config_dir", return_value=str(config_dir)):
            handler.process_torrent_file(str(source))

    destination = config_dir / "torrents" / "new.torrent"
    assert destination.exists()
    model.add_torrent.assert_called_once_with(str(destination))


def test_process_skips_duplicate_within_dedup_window(tmp_path: Path) -> None:
    """Calling process twice in quick succession adds the torrent only once."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    source = tmp_path / "recent.torrent"
    source.write_bytes(b"d4:infod4:name4:testee")

    with loaded_watcher() as mod:
        handler, model = _make_handler(mod)
        with patch.object(mod, "get_config_dir", return_value=str(config_dir)):
            handler.process_torrent_file(str(source))
            handler.process_torrent_file(str(source))

    model.add_torrent.assert_called_once()


def test_process_deletes_source_when_configured(tmp_path: Path) -> None:
    """With delete_added_torrents, the source file is removed after adding."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    source = tmp_path / "temp.torrent"
    source.write_bytes(b"d4:infod4:name4:testee")

    with loaded_watcher() as mod:
        handler, model = _make_handler(mod, delete_added_torrents=True)
        with patch.object(mod, "get_config_dir", return_value=str(config_dir)):
            handler.process_torrent_file(str(source))

    assert not source.exists()
    model.add_torrent.assert_called_once()


def test_process_notifies_when_view_active(tmp_path: Path) -> None:
    """When a View is active, processing a torrent emits a notification."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    source = tmp_path / "shown.torrent"
    source.write_bytes(b"d4:infod4:name4:testee")

    with loaded_watcher() as mod:
        mod.View.instance = MagicMock()
        handler, _ = _make_handler(mod)
        with patch.object(mod, "get_config_dir", return_value=str(config_dir)):
            handler.process_torrent_file(str(source))
        mod.View.instance.notify.assert_called_once()
