"""
Static checks for the theme stylesheets loaded by View.apply_theme().
"""

import re
from pathlib import Path

CSS_DIR = Path(__file__).resolve().parents[4] / "d_fake_seeder" / "components" / "ui" / "css"
THEMES = {"styles-classic.css", "styles-modern.css"}


def test_view_theme_files_exist() -> None:
    """Every stylesheet path View.apply_theme() loads is shipped."""
    view = (CSS_DIR.parents[2] / "view.py").read_text(encoding="utf-8")
    loaded = set(re.findall(r'"components/ui/css/([\w.-]+\.css)"', view))
    assert loaded == THEMES
    assert all((CSS_DIR / name).is_file() for name in loaded)


def test_only_loaded_stylesheets_are_shipped() -> None:
    """No orphan stylesheet: every shipped .css file is one apply_theme() can load."""
    assert {path.name for path in CSS_DIR.glob("*.css")} == THEMES
