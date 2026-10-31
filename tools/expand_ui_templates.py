#!/usr/bin/env python3
"""
Expand ``<dfs-use .../>`` row macros in a generated GtkBuilder XML file.

The settings tabs (``components/ui/settings/*.xml``) describe repeated rows compactly::

    <dfs-use template="spin-row" id="settings_upload_limit" label="Upload limit (KB/s):" .../>

``make ui-build`` pipes the XInclude-resolved output of xmllint through this filter, which
replaces every macro with the named template from
``components/ui/templates/*.xml.in`` (``{param}`` placeholders filled with the XML-escaped
attribute values, re-indented to the macro's column). Templates may use further macros.
Everything outside the macros is left byte-for-byte unchanged, so widget IDs, properties
and the ``translatable="yes"`` markup the i18n extraction scans for are exactly as written.

Usage: xmllint --xinclude settings.xml | expand_ui_templates.py > generated/settings_generated.xml
"""

import re
import sys
from html import unescape
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "d_fake_seeder" / "components" / "ui" / "templates"
TEMPLATE_START_RE = re.compile(r'<template name="([\w-]+)">')
TEMPLATE_END = "</template>"
MACRO_RE = re.compile(r"<dfs-use\b[^>]*>")
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
XML_ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}
MAX_DEPTH = 10


class TemplateError(ValueError):
    """A macro names an unknown template or misses a parameter."""


def load_templates(template_dir: Path = TEMPLATE_DIR) -> dict[str, str]:
    """All templates found in ``template_dir/*.xml.in``, by name."""
    templates: dict[str, str] = {}
    for path in sorted(template_dir.glob("*.xml.in")):
        name, body = "", list[str]()
        for line in path.read_text(encoding="utf-8").split("\n"):
            start = TEMPLATE_START_RE.fullmatch(line)
            if start:
                name, body = start.group(1), []
            elif name and line == TEMPLATE_END:
                if name in templates:
                    raise TemplateError(f"Duplicate template {name!r} in {path}")
                templates[name], name = "\n".join(body), ""
            elif name:
                body.append(line)
    return templates


def _xml_escape(value: str) -> str:
    return "".join(XML_ESCAPES.get(char, char) for char in value)


def _attributes(macro: str) -> dict[str, str]:
    """Attributes of ``<dfs-use a="1" b="2"/>`` as a dict (values unescaped)."""
    parts = macro.split('"')
    return {
        parts[i].rstrip().removesuffix("=").split()[-1]: unescape(parts[i + 1]) for i in range(0, len(parts) - 1, 2)
    }


def _render(macro: str, indent: str, templates: dict[str, str]) -> str:
    params = _attributes(macro)
    if not macro.endswith("/>"):
        raise TemplateError(f"Macro must be an empty element: {macro}")
    name = params.pop("template", "")
    if name not in templates:
        raise TemplateError(f"Unknown template {name!r} in {macro}")

    def fill(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in params:
            raise TemplateError(f"Template {name!r} needs parameter {key!r} ({macro})")
        return _xml_escape(params[key])

    body = PLACEHOLDER_RE.sub(fill, templates[name])
    return "\n".join(f"{indent}{line}" if line and i else line for i, line in enumerate(body.split("\n")))


def expand(text: str, templates: dict[str, str]) -> str:
    """Replace every macro (recursively) with its rendered template."""
    for _ in range(MAX_DEPTH):
        if not MACRO_RE.search(text):
            return text
        text = MACRO_RE.sub(
            lambda m: _render(m.group(0), _line_indent(m.string, m.start()), templates),
            text,
        )
    raise TemplateError(f"Macros nested deeper than {MAX_DEPTH} levels")


def _line_indent(text: str, position: int) -> str:
    line_start = text.rfind("\n", 0, position) + 1
    prefix = text[line_start:position]
    return prefix if not prefix.strip() else ""


def main() -> int:
    """Filter: read GtkBuilder XML on stdin, write it with all macros expanded to stdout."""
    sys.stdout.write(expand(sys.stdin.read(), load_templates()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
