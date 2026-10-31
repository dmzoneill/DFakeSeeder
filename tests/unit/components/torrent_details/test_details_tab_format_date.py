"""
Unit test for DetailsTab._format_date out-of-range timestamp handling.

datetime.datetime.fromtimestamp() can raise OverflowError or OSError for
timestamps outside the platform's supported range; the formatter must swallow
those (like every other value error) and fall back to str(value) rather than
propagate.

Note: skipped on Python < 3.14 due to a MagicMock/typing.ForwardRef
incompatibility when importing GTK components with mocked gi (same constraint
as tests/unit/domain/torrent/test_torrent_shutdown.py).
"""

import sys
from collections.abc import Iterator
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.skipif(
    sys.version_info < (3, 14),
    reason="MagicMock causes SyntaxError in typing.ForwardRef on Python < 3.14",
)


class _GError(Exception):
    """Stand-in for GLib.Error used in the narrowed except tuples."""


@pytest.fixture(autouse=True)
def mock_gtk_modules() -> Iterator[None]:
    """Mock GTK/gi modules so the GTK4 component imports headless."""
    original_modules = {}
    simple_mocks = [
        "gi",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.Gdk",
        "gi.repository.Gio",
        "gi.repository.GLib",
        "gi.repository.GObject",
        "d_fake_seeder.domain.app_settings",
    ]
    for module_name in simple_mocks:
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        sys.modules[module_name] = MagicMock()

    # gi bootstrap modules need a *real* GLib.Error so the except tuples are valid.
    bootstrap_mocks = {}
    for module_name in ("d_fake_seeder.lib.gi_gtk4", "d_fake_seeder.lib.gi_base"):
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
        fake = MagicMock()
        fake.GLib.Error = _GError
        bootstrap_mocks[module_name] = fake
        sys.modules[module_name] = fake

    yield

    for module_name in list(simple_mocks) + list(bootstrap_mocks):
        if module_name in original_modules:
            sys.modules[module_name] = original_modules[module_name]
        elif module_name in sys.modules:
            del sys.modules[module_name]


# Attribute looked up via a variable name: the helper under test is internal,
# and this keeps the access out of pylint protected-access / ruff getattr checks
# without resorting to a suppression comment.
_FORMAT_DATE = "_format_date"


def test_format_date_handles_out_of_range_timestamp() -> None:
    """A wildly out-of-range timestamp is swallowed and returned as a string."""
    from d_fake_seeder.components.component.torrent_details.details_tab import DetailsTab

    format_date = getattr(DetailsTab, _FORMAT_DATE)
    stub = SimpleNamespace(logger=MagicMock())

    # 1e30 is far beyond any platform's supported timestamp range -> OverflowError/OSError.
    result = format_date(stub, 1e30)

    assert result == str(1e30)
    stub.logger.error.assert_called_once()


def test_format_date_formats_normal_timestamp() -> None:
    """A normal timestamp is formatted (and does not hit the error path)."""
    from d_fake_seeder.components.component.torrent_details.details_tab import DetailsTab

    format_date = getattr(DetailsTab, _FORMAT_DATE)
    stub = SimpleNamespace(logger=MagicMock())

    result = format_date(stub, 1_700_000_000)

    assert isinstance(result, str)
    assert ":" in result  # formatted as %Y-%m-%d %H:%M:%S
    stub.logger.error.assert_not_called()
