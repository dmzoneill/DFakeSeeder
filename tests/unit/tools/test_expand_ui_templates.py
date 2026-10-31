"""
Tests for tools/expand_ui_templates.py, the build-time row-macro expander for the settings UI.

Besides unit tests of the expander, this checks that resolving the XIncludes of
components/ui/settings.xml and expanding the macros reproduces the committed
generated/settings_generated.xml exactly (same elements, ids, properties and text),
so the compact tab sources and the UI the app loads cannot drift apart.
"""

import importlib.util
import re
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
UI_DIR = ROOT / "d_fake_seeder" / "components" / "ui"
GENERATED = UI_DIR / "generated" / "settings_generated.xml"
INCLUDE = re.compile(r'^[ \t]*<xi:include\b[^>]*\bhref="([^"]+)"[^>]*/>', re.MULTILINE)
DECLARATION = re.compile(r"^<\?xml[^>]*\?>\s*")
COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
TOKEN = re.compile(r"<[^>]+>|[^<]+")
TRANSLATABLE = re.compile(r'<(?:property\s+name="(?:label|tooltip-text)"\s+|item\s+)translatable="yes">([^<]+)</')


def _load_expander() -> ModuleType:
    spec = importlib.util.spec_from_file_location("expand_ui_templates", ROOT / "tools" / "expand_ui_templates.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


expander = _load_expander()


def _canonical(xml: str) -> list[str]:
    """Tags (whitespace-normalised, xml:base dropped) and non-blank text, in document order; comments ignored."""
    tokens = []
    for token in TOKEN.findall(COMMENT.sub("", DECLARATION.sub("", xml))):
        if token.startswith("<"):
            token = re.sub(r'\s+xml:base="[^"]*"', "", " ".join(token.split()))
            tokens.append(token.replace(" />", "/>").replace(" >", ">"))
        elif token.strip():
            tokens.append(token.strip())
    return tokens


def _build_settings_ui() -> str:
    """What `make ui-build` produces: XIncludes resolved (each tab file inlined), then macros expanded."""

    def include(match: re.Match[str]) -> str:
        return DECLARATION.sub("", (UI_DIR / match.group(1)).read_text(encoding="utf-8"))

    settings = INCLUDE.sub(include, (UI_DIR / "settings.xml").read_text(encoding="utf-8"))
    built: str = expander.expand(settings, expander.load_templates())
    return built


def test_compact_sources_expand_to_committed_generated_ui() -> None:
    """Expanded sources are semantically identical to the committed generated settings UI."""
    built = _build_settings_ui()
    assert "dfs-use" not in built
    assert "xi:include" not in built
    assert _canonical(built) == _canonical(GENERATED.read_text(encoding="utf-8"))


def test_committed_generated_ui_has_no_macros_left() -> None:
    """The file the app loads contains plain GtkBuilder XML only."""
    assert "<dfs-use" not in GENERATED.read_text(encoding="utf-8")


def test_translatable_strings_survive_expansion() -> None:
    """Every translatable string of the expanded speed tab is in the generated UI the extractor scans."""
    templates = expander.load_templates()
    speed = expander.expand((UI_DIR / "settings" / "speed.xml").read_text(encoding="utf-8"), templates)
    strings = set(TRANSLATABLE.findall(speed))
    assert {"Upload limit (KB/s):", "Download Distribution", "Stopped max %:", "Pareto"} <= strings
    assert strings <= set(TRANSLATABLE.findall(GENERATED.read_text(encoding="utf-8")))


def test_expand_indents_escapes_and_nests() -> None:
    """Placeholders are XML-escaped, bodies re-indented, nested macros expanded."""
    templates = {
        "outer": '<child>\n    <dfs-use template="inner" text="{title}"/>\n</child>',
        "inner": '<object class="GtkLabel" id="x">\n    <property name="label">{text}</property>\n</object>',
    }
    text = '<root>\n  <dfs-use template="outer" title="&lt;b&gt;A &amp; &quot;B&quot;&lt;/b&gt;"/>\n</root>'
    assert expander.expand(text, templates) == (
        "<root>\n"
        "  <child>\n"
        '      <object class="GtkLabel" id="x">\n'
        '          <property name="label">&lt;b&gt;A &amp; &quot;B&quot;&lt;/b&gt;</property>\n'
        "      </object>\n"
        "  </child>\n"
        "</root>"
    )


def test_expand_errors() -> None:
    """Unknown templates and missing parameters fail the build instead of emitting bad XML."""
    with pytest.raises(expander.TemplateError):
        expander.expand('<dfs-use template="nope"/>', {})
    with pytest.raises(expander.TemplateError):
        expander.expand('<dfs-use template="t"/>', {"t": "<a>{missing}</a>"})


def test_main_rewrites_file_in_place(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The CLI expands the given file with the shipped templates."""
    templates = expander.load_templates()
    monkeypatch.setattr(expander, "load_templates", lambda: templates)
    monkeypatch.setattr(expander, "REPO_ROOT", tmp_path.resolve())
    target = tmp_path / "ui.xml"
    target.write_text(
        '<interface>\n    <dfs-use template="spin-row" id="s" label="L" lower="0" upper="9" value="1"'
        ' step="1" page="5" tooltip="T"/>\n</interface>\n',
        encoding="utf-8",
    )
    assert expander.main([str(target)]) == 0
    assert '<object class="GtkSpinButton" id="s">' in target.read_text(encoding="utf-8")
    assert expander.main([]) == 2


def test_main_refuses_paths_outside_repo(tmp_path: Path) -> None:
    """Only .xml files inside the repository are rewritten."""
    outside = tmp_path / "ui.xml"
    outside.write_text("<interface/>\n", encoding="utf-8")
    with pytest.raises(expander.TemplateError):
        expander.main([str(outside)])
    with pytest.raises(expander.TemplateError):
        expander.main([str(expander.REPO_ROOT / "Makefile")])
