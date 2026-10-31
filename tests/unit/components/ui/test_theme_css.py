"""
Static checks for the theme stylesheets loaded by View.apply_theme().

Both themes import the shared styles-base.css first; rules kept there must not be
redefined by a theme (so moving them into the base cannot change the cascade).
"""

import re
from pathlib import Path

import pytest

CSS_DIR = Path(__file__).resolve().parents[4] / "d_fake_seeder" / "components" / "ui" / "css"
THEMES = ("styles-classic.css", "styles-modern.css")
IMPORT_BASE = '@import url("styles-base.css");'


def _selectors(css: str) -> set[str]:
    """Top-level rule selectors of a stylesheet (comments stripped)."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    return {
        selector.strip()
        for match in re.finditer(r"([^{};]+)\{", css)
        for selector in match.group(1).split(",")
        if not selector.strip().startswith("@")
    }


@pytest.mark.parametrize("theme", THEMES)
def test_theme_imports_base_first(theme: str) -> None:
    """The base import is the first statement, so theme rules always come after it."""
    first_line = (CSS_DIR / theme).read_text(encoding="utf-8").splitlines()[0]
    assert first_line == IMPORT_BASE


@pytest.mark.parametrize("theme", THEMES)
def test_base_rules_not_redefined_by_theme(theme: str) -> None:
    """Selectors in the base stylesheet are not also defined by a theme."""
    base = _selectors((CSS_DIR / "styles-base.css").read_text(encoding="utf-8"))
    assert base
    assert not base & _selectors((CSS_DIR / theme).read_text(encoding="utf-8"))


def test_view_theme_files_exist() -> None:
    """Every stylesheet path View.apply_theme() loads is shipped."""
    view = (CSS_DIR.parents[2] / "view.py").read_text(encoding="utf-8")
    loaded = set(re.findall(r'"components/ui/css/([\w.-]+\.css)"', view))
    assert loaded == set(THEMES)
    assert all((CSS_DIR / name).is_file() for name in loaded)
