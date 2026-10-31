"""
Unit tests for SpeedDistributionManager (shared upload/download redistribution).

AppSettings and GLib are replaced by in-memory fakes; the real distribution
algorithms are used so the applied speeds are what the app would apply.
"""

import importlib
import sys
from collections.abc import Iterator
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

_GI = ("gi", "gi.repository", "gi.repository.GLib", "gi.repository.Gio", "gi.repository.GObject")
_MODULES = (
    *_GI,
    "d_fake_seeder.domain.app_settings",
    "d_fake_seeder.lib.gi_base",
    "d_fake_seeder.lib.util.speed_distribution_manager",
)


class FakeSettings:
    """AppSettings stand-in: per-direction distribution attributes plus get/set/connect."""

    def __init__(self, **overrides: Any) -> None:
        for direction in ("upload", "download"):
            vars(self).update(
                {
                    f"{direction}_distribution_algorithm": "pareto",
                    f"{direction}_distribution_spread_percentage": 0,
                    f"{direction}_distribution_redistribution_mode": "tick",
                    f"{direction}_distribution_custom_interval_minutes": 5,
                    f"{direction}_distribution_stopped_min_percentage": 0,
                    f"{direction}_distribution_stopped_max_percentage": 0,
                }
            )
        vars(self).update(overrides)
        self.values: dict[str, Any] = {"speed.upload_limit_kbps": 1000, "speed.download_limit_kbps": 0}
        self.disconnected: list[int] = []

    def get(self, key: str, default: Any = None) -> Any:
        """Read a dotted setting."""
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Write a dotted setting."""
        self.values[key] = value

    def connect(self, _signal: str, _handler: Any) -> int:
        """Pretend to connect a signal handler."""
        return 7

    def disconnect(self, handler_id: int) -> None:
        """Record a disconnect."""
        self.disconnected.append(handler_id)


@pytest.fixture(name="env")
def fixture_env() -> Iterator[SimpleNamespace]:
    """Import the manager against fake AppSettings/GLib; restore sys.modules afterwards."""
    saved = {n: sys.modules.get(n) for n in _MODULES}
    for n in _GI:
        sys.modules[n] = MagicMock()
    settings_holder = SimpleNamespace(settings=FakeSettings())
    app_settings = ModuleType("d_fake_seeder.domain.app_settings")
    vars(app_settings)["AppSettings"] = SimpleNamespace(get_instance=lambda: settings_holder.settings)
    sys.modules["d_fake_seeder.domain.app_settings"] = app_settings
    glib = MagicMock()
    glib.timeout_add_seconds.side_effect = [101, 102, 103, 104]
    gi_base = ModuleType("d_fake_seeder.lib.gi_base")
    vars(gi_base)["GLib"] = glib
    sys.modules["d_fake_seeder.lib.gi_base"] = gi_base
    sys.modules.pop("d_fake_seeder.lib.util.speed_distribution_manager", None)
    try:
        module = importlib.import_module("d_fake_seeder.lib.util.speed_distribution_manager")
        yield SimpleNamespace(module=module, holder=settings_holder, glib=glib)
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


def _torrents(count: int, upload: int = 10, download: int = 20) -> list[SimpleNamespace]:
    return [
        SimpleNamespace(file_path=f"/t/{i}", name=f"torrent {i}", upload_speed=upload, download_speed=download)
        for i in range(count)
    ]


def _manager(env: SimpleNamespace, torrents: list[Any], **settings: Any) -> Any:
    env.holder.settings = FakeSettings(**settings)
    model = SimpleNamespace(get_torrents=lambda: torrents)
    return env.module.SpeedDistributionManager(model)


def test_upload_uses_configured_limit(env: SimpleNamespace) -> None:
    """With a limit and 0% spread the full limit is distributed and stored."""
    torrents = _torrents(4)
    manager = _manager(env, torrents)
    manager.redistribute_upload_speeds()
    assert sum(t.upload_speed for t in torrents) == pytest.approx(1000, abs=4)
    values = manager.settings.values
    assert values["speed_distribution.upload.current_speed"] == 1000
    assert set(values["speed_distribution.upload.current_values"]) == {t.file_path for t in torrents}
    assert manager.last_upload_redistribution > 0
    assert manager.last_download_redistribution == 0


def test_download_without_limit_uses_current_sum(env: SimpleNamespace) -> None:
    """No download limit: the sum of current download speeds is redistributed."""
    torrents = _torrents(3, download=20)
    manager = _manager(env, torrents)
    manager.redistribute_download_speeds()
    assert manager.settings.values["speed_distribution.download.current_speed"] == 60
    assert all(t.upload_speed == 10 for t in torrents)


def test_alternative_limits_and_legacy_fallback(env: SimpleNamespace) -> None:
    """Alternative speeds win; otherwise the global limit, else the legacy total."""
    torrents = _torrents(2)
    manager = _manager(env, torrents, total_download_speed=50)
    manager.redistribute_download_speeds()
    assert manager.settings.values["speed_distribution.download.current_speed"] == 50

    manager.settings.values.update({"speed.enable_alternative_speeds": True, "speed.alt_upload_limit_kbps": 300})
    manager.redistribute_upload_speeds()
    assert manager.settings.values["speed_distribution.upload.current_speed"] == 300


def test_off_algorithm_and_no_torrents_do_nothing(env: SimpleNamespace) -> None:
    """Distribution disabled or nothing active: speeds and settings untouched."""
    torrents = _torrents(2)
    manager = _manager(env, torrents, upload_distribution_algorithm="off")
    manager.redistribute_upload_speeds()
    assert [t.upload_speed for t in torrents] == [10, 10]
    empty = _manager(env, [])
    empty.redistribute_upload_speeds()
    assert "speed_distribution.upload.current_speed" not in empty.settings.values


def test_check_redistribution_matches_mode(env: SimpleNamespace) -> None:
    """Each direction redistributes only on the event its mode names."""
    torrents = _torrents(2)
    manager = _manager(env, torrents, download_distribution_redistribution_mode="announce")
    manager.check_redistribution("tick")
    assert "speed_distribution.upload.current_speed" in manager.settings.values
    assert "speed_distribution.download.current_speed" not in manager.settings.values
    manager.check_redistribution("announce")
    assert "speed_distribution.download.current_speed" in manager.settings.values


def test_errors_are_logged_not_raised(env: SimpleNamespace) -> None:
    """A bad setting value is caught so the tick loop keeps running."""
    manager = _manager(env, _torrents(2), upload_distribution_spread_percentage="bad")
    manager.redistribute_upload_speeds()
    assert "speed_distribution.upload.current_speed" not in manager.settings.values


def test_custom_timers_start_and_stop(env: SimpleNamespace) -> None:
    """Custom mode starts a GLib timer per direction; stop removes them and disconnects."""
    manager = _manager(
        env,
        _torrents(1),
        upload_distribution_redistribution_mode="custom",
        download_distribution_redistribution_mode="custom",
        download_distribution_custom_interval_minutes=2,
    )
    manager.start()
    assert (manager.upload_timer_id, manager.download_timer_id) == (101, 102)
    calls = env.glib.timeout_add_seconds.call_args_list
    assert [c.args[0] for c in calls] == [300, 120]
    assert calls[0].args[1](*calls[0].args[2:]) is True  # timer callback keeps running

    manager.stop()
    assert (manager.upload_timer_id, manager.download_timer_id) == (None, None)
    assert [c.args[0] for c in env.glib.source_remove.call_args_list] == [101, 102]
    assert manager.settings.disconnected == [7]
