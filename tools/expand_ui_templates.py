#!/usr/bin/env python3
"""
Expand ``<dfs-use .../>`` row macros in a generated GtkBuilder XML file.

The settings tabs (``components/ui/settings/*.xml``) describe repeated rows compactly::

    <dfs-use template="spin-row" id="settings_upload_limit" label="Upload limit (KB/s):" .../>

``make ui-build`` resolves the XIncludes with xmllint and then runs this script on the
output, replacing every macro with the named template from
``components/ui/templates/*.xml.in`` (``{param}`` placeholders filled with the XML-escaped
attribute values, re-indented to the macro's column). Templates may use further macros.
Everything outside the macros is left byte-for-byte unchanged, so widget IDs, properties
and the ``translatable="yes"`` markup the i18n extraction scans for are exactly as written.

Usage: expand_ui_templates.py FILE [FILE ...]   (files are rewritten in place)
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "d_fake_seeder" / "components" / "ui" / "templates"
TEMPLATE_RE = re.compile(r'^<template name="([\w-]+)">\n(.*?)\n</template>$', re.MULTILINE | re.DOTALL)
MACRO_RE = re.compile(r"<dfs-use\b[^>]*/>")
PLACEHOLDER_RE = re.compile(r"\{(\w+)\}")
MAX_DEPTH = 10


class TemplateError(ValueError):
    """A macro names an unknown template or misses a parameter."""


def load_templates(template_dir: Path = TEMPLATE_DIR) -> dict[str, str]:
    """All templates found in ``template_dir/*.xml.in``, by name."""
    templates: dict[str, str] = {}
    for path in sorted(template_dir.glob("*.xml.in")):
        for name, body in TEMPLATE_RE.findall(path.read_text(encoding="utf-8")):
            if name in templates:
                raise TemplateError(f"Duplicate template {name!r} in {path}")
            templates[name] = body
    return templates


def _render(macro: str, indent: str, templates: dict[str, str]) -> str:
    params = dict(ET.fromstring(macro).attrib)
    name = params.pop("template", "")
    if name not in templates:
        raise TemplateError(f"Unknown template {name!r} in {macro}")

    def fill(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in params:
            raise TemplateError(f"Template {name!r} needs parameter {key!r} ({macro})")
        return escape(params[key], {'"': "&quot;"})

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


def main(argv: list[str]) -> int:
    """Expand macros in each file given on the command line, in place."""
    if not argv:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    templates = load_templates()
    for name in argv:
        path = Path(name)
        path.write_text(expand(path.read_text(encoding="utf-8"), templates), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
