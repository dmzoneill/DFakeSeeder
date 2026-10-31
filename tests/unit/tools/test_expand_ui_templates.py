"""
Tests for tools/expand_ui_templates.py, the build-time row-macro expander for the settings UI.

Besides unit tests of the expander, this checks that resolving the XIncludes of
components/ui/settings.xml and expanding the macros reproduces the committed
generated/settings_generated.xml exactly (same elements, ids, properties and text),
so the compact tab sources and the UI the app loads cannot drift apart.
"""

import importlib.util
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from types import ModuleType
from xml.etree import ElementInclude

import pytest

ROOT = Path(__file__).resolve().parents[3]
UI_DIR = ROOT / "d_fake_seeder" / "components" / "ui"
GENERATED = UI_DIR / "generated" / "settings_generated.xml"
XML_BASE = "{http://www.w3.org/XML/1998/namespace}base"
TRANSLATABLE = re.compile(r'<(?:property\s+name="(?:label|tooltip-text)"\s+|item\s+)translatable="yes">([^<]+)</')


def _load_expander() -> ModuleType:
    spec = importlib.util.spec_from_file_location("expand_ui_templates", ROOT / "tools" / "expand_ui_templates.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


expander = _load_expander()


def _canonical(element: ET.Element) -> tuple[object, ...]:
    """Tag, attributes (minus xml:base), stripped text and children; comments ignored."""
    attrib = tuple(sorted((k, v) for k, v in element.attrib.items() if k != XML_BASE))
    children = tuple(_canonical(child) for child in element if isinstance(child.tag, str))
    return element.tag, attrib, (element.text or "").strip(), children


def _build_settings_ui() -> str:
    """What `make ui-build` produces: XIncludes resolved, then macros expanded."""
    tree = ET.parse(UI_DIR / "settings.xml")
    root = tree.getroot()
    ElementInclude.include(root, base_url=str(UI_DIR / "settings.xml"))
    return expander.expand(ET.tostring(root, encoding="unicode"), expander.load_templates())


def test_compact_sources_expand_to_committed_generated_ui() -> None:
    """Expanded sources are semantically identical to the committed generated settings UI."""
    built = _build_settings_ui()
    assert "dfs-use" not in built
    assert _canonical(ET.fromstring(built)) == _canonical(ET.parse(GENERATED).getroot())


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


def test_main_rewrites_file_in_place(tmp_path: Path) -> None:
    """The CLI expands the given file with the shipped templates."""
    target = tmp_path / "ui.xml"
    target.write_text(
        '<interface>\n    <dfs-use template="spin-row" id="s" label="L" lower="0" upper="9" value="1"'
        ' step="1" page="5" tooltip="T"/>\n</interface>\n',
        encoding="utf-8",
    )
    assert expander.main([str(target)]) == 0
    spin = ET.parse(target).getroot().find(".//object[@id='s']")
    assert spin is not None
    assert spin.get("class") == "GtkSpinButton"
    assert expander.main([]) == 2
