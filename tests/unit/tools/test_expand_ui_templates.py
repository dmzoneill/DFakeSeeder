"""
Tests for tools/expand_ui_templates.py, the build-time row-macro expander for the settings UI.

Besides unit tests of the expander, this checks that resolving the XIncludes of
components/ui/settings.xml and expanding the macros reproduces the committed
generated/settings_generated.xml exactly (same elements, ids, properties and text),
so the compact tab sources and the UI the app loads cannot drift apart.
"""

import importlib.util
import io
import re
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
UI_DIR = ROOT / "d_fake_seeder" / "components" / "ui"
GENERATED = UI_DIR / "generated" / "settings_generated.xml"
MAIN_GENERATED = UI_DIR / "generated" / "generated.xml"
BUILDS = [("settings.xml", GENERATED), ("ui.xml", MAIN_GENERATED)]
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
    return _collapse_empty_elements(tokens)


def _collapse_empty_elements(tokens: list[str]) -> list[str]:
    """``<a x="1"></a>`` and ``<a x="1"/>`` are the same element (xmllint writes the short form)."""
    collapsed: list[str] = []
    for token in tokens:
        previous = collapsed[-1] if collapsed else ""
        name = previous[1:].split(" ", 1)[0].rstrip(">")
        if token == f"</{name}>" and not previous.startswith("</") and not previous.endswith("/>"):
            collapsed[-1] = previous[:-1] + "/>"
        else:
            collapsed.append(token)
    return collapsed


def _resolve_includes(path: Path) -> str:
    """Inline every XInclude of ``path`` (hrefs relative to the including file), recursively."""

    def include(match: re.Match[str]) -> str:
        return DECLARATION.sub("", _resolve_includes(path.parent / match.group(1)))

    return INCLUDE.sub(include, path.read_text(encoding="utf-8"))


def _build_ui(source: str) -> str:
    """What `make ui-build` produces: XIncludes resolved, then macros expanded."""
    built: str = expander.expand(_resolve_includes(UI_DIR / source), expander.load_templates())
    return built


@pytest.mark.parametrize(("source", "generated"), BUILDS, ids=[source for source, _ in BUILDS])
def test_compact_sources_expand_to_committed_generated_ui(source: str, generated: Path) -> None:
    """Expanded sources are semantically identical to the committed generated UI."""
    built = _build_ui(source)
    assert "dfs-use" not in built
    assert "xi:include" not in built
    assert _canonical(built) == _canonical(generated.read_text(encoding="utf-8"))


@pytest.mark.parametrize("generated", [generated for _, generated in BUILDS], ids=[s for s, _ in BUILDS])
def test_committed_generated_ui_has_no_macros_left(generated: Path) -> None:
    """The files the app loads contain plain GtkBuilder XML only."""
    assert "<dfs-use" not in generated.read_text(encoding="utf-8")


@pytest.mark.parametrize("tab", sorted(path.name for path in (UI_DIR / "settings").glob("*.xml")))
def test_translatable_strings_survive_expansion(tab: str) -> None:
    """Every translatable string of an expanded settings tab is in the generated UI the extractor scans."""
    expanded = expander.expand((UI_DIR / "settings" / tab).read_text(encoding="utf-8"), expander.load_templates())
    assert "<dfs-use" not in expanded
    assert set(TRANSLATABLE.findall(expanded)) <= set(TRANSLATABLE.findall(GENERATED.read_text(encoding="utf-8")))


def test_template_strings_reach_generated_ui() -> None:
    """Strings passed to row templates end up translatable in the generated UI."""
    strings = set(TRANSLATABLE.findall(GENERATED.read_text(encoding="utf-8")))
    assert {"Upload limit (KB/s):", "Download Distribution", "Stopped max %:", "Pareto"} <= strings
    assert {"Enable Web UI", "Enable CSRF protection", "Session timeout (min):"} <= strings
    assert {"Automatic logout after inactivity (5-1440 minutes)"} <= strings
    assert {"Handshake timeout (seconds):", "Deluge Theme", "Japanese"} <= strings


def test_notebook_template_strings_reach_main_ui() -> None:
    """Tab labels and empty-state texts passed to the notebook templates are translatable in generated.xml."""
    strings = set(TRANSLATABLE.findall(MAIN_GENERATED.read_text(encoding="utf-8")))
    assert {"Details", "Trackers", "No Torrent Selected", "Select a torrent to view its details"} <= strings


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


def test_list_parameter_repeats_its_line() -> None:
    """A {key[]} line is emitted once per |-separated value, each XML-escaped."""
    templates = {"list": "<items>\n    <item>{items[]}</item>\n</items>"}
    assert expander.expand('  <dfs-use template="list" items="A|B &amp; C"/>', templates) == (
        "  <items>\n      <item>A</item>\n      <item>B &amp; C</item>\n  </items>"
    )
    with pytest.raises(expander.TemplateError):
        expander.expand('<dfs-use template="list"/>', templates)


def test_expand_errors() -> None:
    """Unknown templates and missing parameters fail the build instead of emitting bad XML."""
    with pytest.raises(expander.TemplateError):
        expander.expand('<dfs-use template="nope"/>', {})
    with pytest.raises(expander.TemplateError):
        expander.expand('<dfs-use template="t"/>', {"t": "<a>{missing}</a>"})
    with pytest.raises(expander.TemplateError):
        expander.expand('<dfs-use template="t"></dfs-use>', {"t": "<a/>"})


def test_main_filters_stdin_to_stdout(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """The CLI expands stdin with the shipped templates (as `make ui-build` pipes xmllint into it)."""
    source = (
        '<interface>\n    <dfs-use template="spin-row" id="s" label="L" lower="0" upper="9" value="1"'
        ' step="1" page="5" tooltip="T"/>\n</interface>\n'
    )
    monkeypatch.setattr("sys.stdin", io.StringIO(source))
    assert expander.main() == 0
    assert '<object class="GtkSpinButton" id="s">' in capsys.readouterr().out
