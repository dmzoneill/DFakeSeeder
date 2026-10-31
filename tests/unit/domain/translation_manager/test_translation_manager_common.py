"""
Unit tests for the shared GTK 3 / GTK 4 translation manager logic.

GTK is replaced by small fake widget classes, so both implementations are exercised
headless; the real repository locale directory provides a compiled catalogue.
"""

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import pytest

LOCALEDIR = str(Path(__file__).resolve().parents[4] / "d_fake_seeder" / "components" / "locale")
_GI = ("gi", "gi.repository", "gi.repository.Gtk", "gi.repository.Gio", "gi.repository.GLib")
_TM = (
    "d_fake_seeder.domain.translation_manager.common",
    "d_fake_seeder.domain.translation_manager.gtk3_implementation",
    "d_fake_seeder.domain.translation_manager.gtk4_implementation",
)


class FakeWidget:
    """Minimal widget: text getters/setters plus a tooltip."""

    def __init__(self, label: str = "", tooltip: str = "") -> None:
        self.label = label
        self.tooltip = tooltip
        self.realized = True

    def get_label(self) -> str:
        """Current label."""
        return self.label

    def set_label(self, value: str) -> None:
        """Set the label."""
        self.label = value

    def get_tooltip_text(self) -> str:
        """Current tooltip."""
        return self.tooltip

    def set_tooltip_text(self, value: str) -> None:
        """Set the tooltip."""
        self.tooltip = value

    def get_visible(self) -> bool:
        """Always visible."""
        return True

    def get_realized(self) -> bool:
        """Whether realized."""
        return self.realized


class Label(FakeWidget):
    """Fake label."""


class Button(FakeWidget):
    """Fake button."""


class Window(FakeWidget):
    """Fake window with a title."""

    def get_title(self) -> str:
        """Title (shares the label text)."""
        return self.label


def make_builder(objects: list[Any]) -> SimpleNamespace:
    """Fake builder returning a fixed object list."""
    return SimpleNamespace(get_objects=lambda: objects)


@pytest.fixture(name="tm")
def fixture_tm() -> Iterator[SimpleNamespace]:
    """Import both implementations against a fake ``gi_gtk4.Gtk``; restore sys.modules afterwards."""
    names = (*_GI, "d_fake_seeder.lib.gi_gtk4", *_TM)
    saved = {n: sys.modules.get(n) for n in names}
    for n in _GI:
        sys.modules[n] = MagicMock()
    gtk = SimpleNamespace(
        Widget=FakeWidget,
        Label=Label,
        Button=Button,
        CheckButton=type("CheckButton", (FakeWidget,), {}),
        Window=Window,
        Dialog=type("Dialog", (Window,), {}),
        MenuButton=type("MenuButton", (FakeWidget,), {}),
        Entry=type("Entry", (FakeWidget,), {}),
        Scale=type("Scale", (FakeWidget,), {}),
    )
    fake_bootstrap = ModuleType("d_fake_seeder.lib.gi_gtk4")
    vars(fake_bootstrap)["Gtk"] = gtk
    sys.modules["d_fake_seeder.lib.gi_gtk4"] = fake_bootstrap
    for n in _TM:
        sys.modules.pop(n, None)
    try:
        gtk3 = importlib.import_module("d_fake_seeder.domain.translation_manager.gtk3_implementation")
        gtk4 = importlib.import_module("d_fake_seeder.domain.translation_manager.gtk4_implementation")
        yield SimpleNamespace(gtk3=gtk3.TranslationManagerGTK3, gtk4=gtk4.TranslationManagerGTK4)
    finally:
        for n, mod in saved.items():
            if mod is not None:
                sys.modules[n] = mod
            else:
                sys.modules.pop(n, None)


@pytest.mark.parametrize("version", ["3", "4"])
def test_discovery_and_switching(tm: SimpleNamespace, version: str) -> None:
    """Languages come from the locale dir; a real catalogue translates, unknown codes fall back."""
    manager = getattr(tm, f"gtk{version}")(domain="dfakeseeder", localedir=LOCALEDIR)
    assert manager.gtk_version == version
    assert {"en", "de", "fr"} <= manager.get_supported_languages()
    assert manager.get_available_languages() == sorted(manager.supported_languages)

    assert manager.switch_language("de") == "de"
    assert manager.current_language == "de"
    assert manager.get_translate_func() is manager.translate_func
    assert manager.get_translation_coverage("de")["coverage_percent"] == 100
    assert manager.get_translation_coverage("xx")["coverage_percent"] == 0

    assert manager.switch_language("en") == "en"
    assert manager.translate_func("Settings") == "Settings"


@pytest.mark.parametrize("version", ["3", "4"])
def test_supported_languages_override_and_tmp_locale(tm: SimpleNamespace, version: str, tmp_path: Path) -> None:
    """Only dirs named like a language code with a .mo file count as discovered."""
    (tmp_path / "es" / "LC_MESSAGES").mkdir(parents=True)
    (tmp_path / "es" / "LC_MESSAGES" / "messages.mo").write_bytes(b"")
    (tmp_path / "not-a-lang" / "LC_MESSAGES").mkdir(parents=True)
    (tmp_path / "it" / "LC_MESSAGES").mkdir(parents=True)
    manager = getattr(tm, f"gtk{version}")(localedir=str(tmp_path))
    assert manager.refresh_supported_languages() == {"en", "es"}
    fixed = getattr(tm, f"gtk{version}")(localedir=str(tmp_path), supported_languages={"en", "ga"})
    assert fixed.supported_languages == {"en", "ga"}


@pytest.mark.parametrize("version", ["3", "4"])
def test_registry_scan_refresh_and_clear(tm: SimpleNamespace, version: str) -> None:
    """Builder scan registers text once per widget/property; refresh pushes translations; clear empties."""
    manager = getattr(tm, f"gtk{version}")(localedir=LOCALEDIR)
    label, button, window = Label("Name"), Button("Start", tooltip="Begin"), Window("Main")
    builder = make_builder([label, button, window, object()])
    manager.scan_builder_widgets(builder)
    manager.scan_builder_widgets(builder)  # already scanned: no duplicates
    registered = {(type(w["widget"]).__name__, w["property_name"]) for w in manager.translatable_widgets}
    assert registered == {("Label", "label"), ("Button", "label"), ("Button", "tooltip_text"), ("Window", "title")}
    assert len(manager.get_translatable_widgets()) == 4

    manager.register_widget(label, "Name")  # duplicate widget+property ignored
    assert len(manager.translatable_widgets) == 4

    manager.translate_func = str.upper
    manager.refresh_all_translations()
    assert (label.label, button.label, button.tooltip) == ("NAME", "START", "BEGIN")

    manager.set_widget_state("w", "clicked", True)
    assert manager.get_widget_state("w", "clicked") is True
    assert manager.get_widget_state("w", "missing", 5) == 5
    manager.clear_registrations()
    assert not manager.translatable_widgets
    assert not manager.state_storage


def test_gtk3_skips_unrealized_widgets(tm: SimpleNamespace) -> None:
    """GTK 3 only updates realized widgets."""
    manager = tm.gtk3(localedir=LOCALEDIR)
    label = Label("Name")
    label.realized = False
    manager.register_translation_function(label, lambda: "Name")
    manager.translate_func = str.upper
    manager.update_translations()
    assert label.label == "Name"
    assert manager.get_language_name("de") == "Deutsch"
    assert manager.create_translated_menu_items([{"key": "Quit", "action": "app.quit"}]) == [
        {"text": "QUIT", "action": "app.quit"}
    ]


def test_gtk4_menus_refresh_on_switch(tm: SimpleNamespace) -> None:
    """GTK 4 rebuilds registered menus when the language switches; GTK 3 does not."""
    for factory, expected_calls in ((tm.gtk4, 1), (tm.gtk3, 0)):
        manager = factory(domain="dfakeseeder", localedir=LOCALEDIR)
        menu = MagicMock()
        manager.register_menu(menu, [{"key": "Quit", "action": "app.quit"}])
        manager.register_menu(menu, [])  # duplicate ignored
        assert len(manager.translatable_menus) == 1
        manager.switch_language("de")
        assert menu.remove_all.call_count == expected_calls


def test_gtk4_options(tm: SimpleNamespace) -> None:
    """GTK 4 keeps the config_file option and rejects unknown options."""
    assert tm.gtk4(localedir=LOCALEDIR, config_file="/tmp/c.json").config_file == "/tmp/c.json"
    with pytest.raises(TypeError):
        tm.gtk4(localedir=LOCALEDIR, bogus=1)
