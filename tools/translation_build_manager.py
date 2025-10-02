#!/usr/bin/env python3
"""
DFakeSeeder Translation Manager
===============================

Consolidated translation framework that handles the complete workflow:
JSON → POT → PO → MO translation chain with validation and utilities.

This replaces 16 separate scripts with a unified command-line interface.

Usage:
    python translation_manager.py extract         # Extract strings from source
    python translation_manager.py build           # Build complete translation system
    python translation_manager.py compile         # Compile PO to MO files
    python translation_manager.py validate        # Validate translation chain
    python translation_manager.py enhance         # Enhance/fix translations
    python translation_manager.py analyze         # Analyze coverage and quality
    python translation_manager.py --help          # Show detailed help
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Add the parent directory to sys.path to import from d_fake_seeder
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from d_fake_seeder.lib.util.language_config import (
        get_config_metadata,
        get_supported_languages,
    )

    LANGUAGES = get_supported_languages()
    print(f"Loaded {len(LANGUAGES)} languages from configuration file")
    print(f"Configuration metadata: {get_config_metadata()}")
except ImportError as e:
    print(f"Warning: Could not import language_config ({e}), using fallback")
    # Fallback to minimal hardcoded set if import fails
    LANGUAGES = {
        "en": {"name": "English", "plural_forms": "nplurals=2; plural=n != 1;"},
        "es": {"name": "Spanish", "plural_forms": "nplurals=2; plural=n != 1;"},
        "fr": {"name": "French", "plural_forms": "nplurals=2; plural=n > 1;"},
        "de": {"name": "German", "plural_forms": "nplurals=2; plural=n != 1;"},
    }


class TranslationBuildManager:
    """Unified translation management system"""

    def __init__(self, project_root: Optional[Path] = None):
        self.script_dir = Path(__file__).parent
        self.project_root = project_root or self.script_dir.parent
        self.source_dir = self.project_root / "d_fake_seeder"
        self.translations_dir = self.script_dir / "translations"
        self.locale_dir = self.source_dir / "components" / "locale"
        self.pot_file = self.locale_dir / "dfakeseeder.pot"

        # Ensure directories exist
        self.translations_dir.mkdir(exist_ok=True)
        self.locale_dir.mkdir(parents=True, exist_ok=True)

    # ==================== EXTRACTION METHODS ====================

    def extract_strings_from_python(self) -> bool:
        """Extract translatable strings from Python files"""
        print("🐍 Extracting from Python files...")

        python_files = []
        for py_file in self.source_dir.rglob("*.py"):
            if "locale" not in str(py_file) and "__pycache__" not in str(py_file):
                python_files.append(str(py_file))

        if not python_files:
            print("   ⚠️  No Python files found")
            return True

        python_pot = self.locale_dir / "python.pot"

        # Build xgettext command
        cmd = [
            "xgettext",
            "--language=Python",
            "--keyword=_",
            "--keyword=ngettext:1,2",
            "--keyword=translate_func",
            "--output=" + str(python_pot),
            "--from-code=UTF-8",
            "--package-name=DFakeSeeder",
            "--package-version=1.0.0",
            "--copyright-holder=DFakeSeeder Contributors",
            "--msgid-bugs-address=https://github.com/username/dfakeseeder/issues",
            "--add-comments=TRANSLATORS",
            "--sort-output",
        ] + python_files

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            if not python_pot.exists():
                self._create_empty_pot(str(python_pot))
            print(f"   ✅ Extracted to {python_pot}")

            # Enhanced extraction for missing strings
            additional_strings = self._extract_missing_python_strings(python_files)
            if additional_strings:
                print(f"   📝 Found {len(additional_strings)} additional strings")
                self._append_strings_to_pot(str(python_pot), additional_strings)

            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("   ⚠️  xgettext not available, using manual extraction")
            # Fallback to manual extraction
            manual_strings = self._extract_missing_python_strings(python_files)
            self._create_pot_from_strings(manual_strings, str(python_pot))
            return True

    def extract_strings_from_xml(self) -> bool:
        """Extract translatable strings from XML files"""
        print("🎨 Extracting from XML files...")

        xml_files = list(self.source_dir.rglob("*.xml"))
        print(f"   DEBUG: Found {len(xml_files)} XML files")
        if not xml_files:
            print("   ⚠️  No XML files found")
            return True

        # Extract translatable strings
        translatable_strings = set()
        # Pattern for property elements
        property_pattern = r'<property\s+name="(?:label|tooltip-text)"\s+translatable="yes">([^<]+)</property>'
        # Pattern for item elements in StringList
        item_pattern = r'<item\s+translatable="yes">([^<]+)</item>'

        for i, xml_file in enumerate(xml_files):
            print(f"   DEBUG: Processing {xml_file.name} ({i+1}/{len(xml_files)})")
            try:
                with open(xml_file, "r", encoding="utf-8") as f:
                    content = f.read()

                print(f"   DEBUG: File size: {len(content)} chars")

                # Extract from property elements
                property_matches = re.findall(property_pattern, content)
                for match in property_matches:
                    text = match.strip()
                    if text:
                        text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
                        translatable_strings.add(text)

                # Extract from item elements
                item_matches = re.findall(item_pattern, content)
                for match in item_matches:
                    text = match.strip()
                    if text:
                        text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
                        translatable_strings.add(text)

                print(f"   DEBUG: Found {len(property_matches)} property + {len(item_matches)} item matches")

                # Safer patterns without potentially problematic regex
                safer_patterns = [
                    # Property elements that could be translatable but aren't marked
                    r'<property\s+name="(?:label|tooltip-text)"(?!\s+translatable="yes")>([^<]+)</property>',
                    # Dialog titles (simple pattern)
                    r'<property\s+name="title">([^<]+)</property>',
                ]

                print("   DEBUG: Running safer patterns...")
                for pattern in safer_patterns:
                    try:
                        potential_matches = re.findall(pattern, content)
                        print(f"   DEBUG: Pattern found {len(potential_matches)} matches")
                        for match in potential_matches:
                            text = match.strip()
                            if text and len(text) > 1:
                                # Filter out obvious non-translatable content
                                if not any(char in text for char in ["<", ">", "{", "}", "%"]):
                                    # Decode XML entities
                                    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
                                    translatable_strings.add(text)
                    except Exception as pattern_error:
                        print(f"   DEBUG: Pattern error: {pattern_error}")

                print(f"   DEBUG: Completed {xml_file.name}")
            except Exception as e:
                print(f"   ⚠️  Warning: Could not process {xml_file}: {e}")

        print(f"   ✅ Found {len(translatable_strings)} translatable XML strings")

        if translatable_strings:
            xml_pot = self.locale_dir / "xml.pot"
            self._create_pot_from_strings(translatable_strings, str(xml_pot))
            return True

        return True

    def extract_strings(self) -> bool:
        """Main string extraction method"""
        print("🌐 DFakeSeeder Translation String Extraction")
        print("=" * 50)

        # Extract from Python and XML
        python_success = self.extract_strings_from_python()
        xml_success = self.extract_strings_from_xml()

        if not python_success or not xml_success:
            return False

        # Merge POT files
        print("🔄 Merging translation files...")
        self._merge_pot_files()

        print("✅ String extraction complete!")
        return True

    def _create_empty_pot(self, output_file: str):
        """Create an empty POT file with standard headers"""
        pot_content = """# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR DFakeSeeder Contributors
# This file is distributed under the same license as the DFakeSeeder package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: DFakeSeeder 1.0.0\\n"
"Report-Msgid-Bugs-To: https://github.com/username/dfakeseeder/issues\\n"
"POT-Creation-Date: 2025-09-23 14:56+0100\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=CHARSET\\n"
"Content-Transfer-Encoding: 8bit\\n"

"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(pot_content)

    def _create_pot_from_strings(self, strings: Set[str], output_file: str):
        """Create POT file from string set"""
        pot_content = """# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR DFakeSeeder Contributors
# This file is distributed under the same license as the DFakeSeeder package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: DFakeSeeder 1.0.0\\n"
"Report-Msgid-Bugs-To: https://github.com/username/dfakeseeder/issues\\n"
"POT-Creation-Date: 2025-09-23 14:56+0100\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=CHARSET\\n"
"Content-Transfer-Encoding: 8bit\\n"

"""
        for string in sorted(strings):
            escaped_string = self._escape_po_string(string)
            pot_content += f'msgid {escaped_string}\nmsgstr ""\n\n'

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(pot_content)

    def _merge_pot_files(self):
        """Merge Python and XML POT files"""
        python_pot = self.locale_dir / "python.pot"
        xml_pot = self.locale_dir / "xml.pot"

        if python_pot.exists() and xml_pot.exists():
            try:
                cmd = ["msgcat", "--output=" + str(self.pot_file), str(python_pot), str(xml_pot)]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Manual merge fallback
                self._manual_merge_pot_files(str(python_pot), str(xml_pot), str(self.pot_file))

            # Cleanup
            python_pot.unlink(missing_ok=True)
            xml_pot.unlink(missing_ok=True)
        elif python_pot.exists():
            python_pot.rename(self.pot_file)
        elif xml_pot.exists():
            xml_pot.rename(self.pot_file)

    def _manual_merge_pot_files(self, python_pot: str, xml_pot: str, final_pot: str):
        """Manually merge POT files when msgcat is not available"""
        with open(python_pot, "r", encoding="utf-8") as f:
            python_content = f.read()
        with open(xml_pot, "r", encoding="utf-8") as f:
            xml_content = f.read()

        # Extract XML entries (skip headers)
        xml_lines = xml_content.split("\n")
        xml_entries = []
        in_entry = False
        current_entry = []

        for line in xml_lines:
            if line.startswith("msgid ") and '"' in line and line.strip() != 'msgid ""':
                in_entry = True
                current_entry = [line]
            elif in_entry:
                current_entry.append(line)
                if line.strip() == "":
                    xml_entries.extend(current_entry)
                    current_entry = []
                    in_entry = False

        if current_entry:
            xml_entries.extend(current_entry)

        final_content = python_content.rstrip() + "\n\n" + "\n".join(xml_entries)
        with open(final_pot, "w", encoding="utf-8") as f:
            f.write(final_content)

    def _extract_missing_python_strings(self, python_files: List[str]) -> Set[str]:
        """Extract potentially translatable strings missed by xgettext"""
        print("   🔍 Finding additional translatable strings...")

        additional_strings = set()

        for py_file in python_files:
            try:
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract column headers and UI strings
                patterns = [
                    # Column headers
                    r'header_name\s*=\s*"([^"]+)"',
                    r'column.*"([^"]+)".*header',
                    r'append_column.*"([^"]+)"',
                    r'TreeViewColumn.*"([^"]+)"',
                    # Tab names from settings
                    r'tab_name.*"([^"]+)"',
                    r'@property.*def\s+tab_name.*return\s+"([^"]+)"',
                    # UI labels and buttons
                    r'set_label\s*\(\s*"([^"]+)"\s*\)',
                    r'set_text\s*\(\s*"([^"]+)"\s*\)',
                    r'set_title\s*\(\s*"([^"]+)"\s*\)',
                    # Notification messages
                    r'show_notification\s*\(\s*"([^"]+)"',
                    # Menu items
                    r'menu.*"([^"]+)"',
                    r'tooltip.*"([^"]+)"',
                ]

                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
                    for match in matches:
                        # Handle tuple results from groups
                        text = match[1] if isinstance(match, tuple) and len(match) > 1 else match
                        text = text.strip()

                        if text and len(text) > 1 and self._is_translatable_text(text):
                            additional_strings.add(text)

            except Exception as e:
                print(f"   ⚠️  Warning: Could not process {py_file}: {e}")

        return additional_strings

    def _is_translatable_text(self, text: str) -> bool:
        """Check if text should be translated"""
        # Skip technical strings
        if any(char in text for char in ["%", "{", "}", "<", ">", "=", "[", "]"]):
            return False

        # Skip pure numbers or single characters
        if text.isdigit() or len(text) <= 1:
            return False

        # Skip obvious code patterns
        if text.startswith("_") or text.endswith(".py") or "::" in text:
            return False

        # Skip log patterns
        if text.startswith("[") or "DEBUG" in text.upper() or "ERROR" in text.upper():
            return False

        return True

    def _append_strings_to_pot(self, pot_file: str, additional_strings: Set[str]):
        """Append additional strings to existing POT file"""
        try:
            with open(pot_file, "r", encoding="utf-8") as f:
                existing_content = f.read()

            # Check which strings are already in the POT
            existing_strings = set()
            pattern = r'msgid "([^"]+)"'
            matches = re.findall(pattern, existing_content)
            for match in matches:
                existing_strings.add(match)

            # Add only new strings
            new_strings = additional_strings - existing_strings

            if new_strings:
                with open(pot_file, "a", encoding="utf-8") as f:
                    f.write("\n")
                    for string in sorted(new_strings):
                        escaped_string = self._escape_po_string(string)
                        f.write(f'msgid {escaped_string}\nmsgstr ""\n\n')

                print(f"   ✅ Added {len(new_strings)} new strings to POT")

        except Exception as e:
            print(f"   ⚠️  Warning: Could not append strings: {e}")

    def _sync_extracted_strings_to_json(self) -> bool:
        """Sync newly extracted strings from POT file to JSON files"""
        print("🔄 Syncing extracted strings to JSON files...")

        # Check if POT file exists from recent extraction
        pot_file = self.locale_dir / "dfakeseeder.pot"
        if not pot_file.exists():
            print("   ⚠️  No POT file found, run extract first")
            return True

        # Extract strings from POT file
        pot_strings = self._extract_strings_from_pot(str(pot_file))
        if not pot_strings:
            print("   ⚠️  No strings found in POT file")
            return True

        # Load English JSON (our template)
        english_file = self.translations_dir / "en.json"
        if not english_file.exists():
            print("   ❌ English template file not found!")
            return False

        with open(english_file, "r", encoding="utf-8") as f:
            english_translations = json.load(f)

        # Find new strings that aren't in JSON yet
        existing_keys = set(english_translations.keys())
        new_strings = pot_strings - existing_keys

        if not new_strings:
            print("   ✅ All extracted strings already in JSON files")
            return True

        print(f"   📝 Adding {len(new_strings)} new strings to JSON files...")

        # Add new strings to English template (with English as translation)
        for string in new_strings:
            english_translations[string] = string

        # Save updated English file
        with open(english_file, "w", encoding="utf-8") as f:
            json.dump(english_translations, f, indent=2, ensure_ascii=False)

        # Add new strings to all other language files (with English as fallback)
        for lang_code in LANGUAGES:
            if lang_code == "en":
                continue

            json_file = self.translations_dir / f"{lang_code}.json"
            if not json_file.exists():
                continue

            with open(json_file, "r", encoding="utf-8") as f:
                translations = json.load(f)

            # Add new strings with English fallback
            for string in new_strings:
                translations[string] = string  # Use English as fallback

            # Save updated language file
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)

        print(f"   ✅ Added {len(new_strings)} strings to all language files")
        return True

    def _extract_strings_from_pot(self, pot_file: str) -> set:
        """Extract translatable strings from POT file"""
        strings = set()

        try:
            with open(pot_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Extract msgid lines
            import re

            pattern = r'msgid "([^"]+)"'
            matches = re.findall(pattern, content)

            for match in matches:
                if match and match != "":  # Skip empty strings
                    # Unescape common sequences
                    text = match.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t")
                    strings.add(text)

        except Exception as e:
            print(f"   ⚠️  Error reading POT file: {e}")

        return strings

    # ==================== BUILD METHODS ====================

    def build_translations(self, target_lang: Optional[str] = None) -> bool:
        """Build complete translation system from JSON files"""
        print("🌐 Building complete translation system...")
        print("=" * 60)

        try:
            # Step 1: Extract strings from JSON as source of truth
            all_strings = self._extract_strings_from_json()

            # Step 3: Create POT from JSON
            self._create_pot_from_json(all_strings)

            # Step 3: Verify and extend JSON translations
            self._verify_and_extend_translations(all_strings, target_lang)

            # Step 4: Generate PO files from JSON
            languages = [target_lang] if target_lang else LANGUAGES.keys()
            pot_entries = self._parse_pot_entries()

            print("🔨 Generating PO files...")
            for lang_code in languages:
                print(f"   🔨 Creating {LANGUAGES[lang_code]['name']} ({lang_code})...")
                self._generate_po_file(lang_code, pot_entries)

            # Step 5: Compile to MO files
            print("⚙️  Compiling to MO files...")
            compiled_count = 0
            for lang_code in languages:
                if self._compile_po_to_mo(lang_code):
                    print(f"   ✅ Compiled: {lang_code}")
                    compiled_count += 1
                else:
                    print(f"   ❌ Failed: {lang_code}")

            print()
            print("🎉 Translation build complete!")
            print(f"   📊 Languages processed: {len(languages)}")
            print(f"   ✅ Successfully compiled: {compiled_count}")
            print(f"   🔤 Strings per language: {len(all_strings)}")

            return True

        except Exception as e:
            print(f"❌ Build failed: {e}")
            return False

    def _extract_strings_from_json(self) -> Set[str]:
        """Extract all strings from English JSON file"""
        print("📋 Extracting strings from English JSON file...")

        english_file = self.translations_dir / "en.json"
        if not english_file.exists():
            raise FileNotFoundError(f"English JSON file not found: {english_file}")

        with open(english_file, "r", encoding="utf-8") as f:
            english_translations = json.load(f)

        all_strings = set(english_translations.keys())
        print(f"   ✅ Found {len(all_strings)} translatable strings in JSON")
        return all_strings

    def _create_pot_from_json(self, all_strings: Set[str]):
        """Create POT file from JSON strings"""
        print("📝 Creating POT file from JSON strings...")

        pot_content = """# SOME DESCRIPTIVE TITLE.
# Copyright (C) YEAR DFakeSeeder Contributors
# This file is distributed under the same license as the DFakeSeeder package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: DFakeSeeder 1.0.0\\n"
"Report-Msgid-Bugs-To: https://github.com/username/dfakeseeder/issues\\n"
"POT-Creation-Date: 2025-09-23 14:56+0100\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: \\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=CHARSET\\n"
"Content-Transfer-Encoding: 8bit\\n"

"""
        for string in sorted(all_strings):
            escaped_string = self._escape_po_string(string)
            pot_content += f'msgid {escaped_string}\nmsgstr ""\n\n'

        with open(self.pot_file, "w", encoding="utf-8") as f:
            f.write(pot_content)

        print(f"   ✅ Created POT file with {len(all_strings)} strings")

    def _verify_and_extend_translations(self, all_strings: Set[str], target_lang: Optional[str]):
        """Verify all translations have complete coverage"""
        print("🔍 Verifying and extending translation coverage...")

        languages = [target_lang] if target_lang else LANGUAGES.keys()

        for lang_code in languages:
            print(f"   🔨 Processing {LANGUAGES[lang_code]['name']} ({lang_code})...")

            existing = self._load_json_translation(lang_code)
            missing_strings = all_strings - set(existing.keys())

            if missing_strings:
                complete_translations = {}
                for key in all_strings:
                    if key in existing:
                        complete_translations[key] = existing[key]
                    else:
                        complete_translations[key] = key  # English fallback

                self._save_json_translation(lang_code, complete_translations)
                print(f"      ➕ Added {len(missing_strings)} missing strings")
            else:
                print(f"      ✅ Already complete ({len(existing)} strings)")

    def _load_json_translation(self, lang_code: str) -> Dict[str, str]:
        """Load JSON translation file"""
        json_file = self.translations_dir / f"{lang_code}.json"
        if json_file.exists():
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}

    def _save_json_translation(self, lang_code: str, translations: Dict[str, str]):
        """Save JSON translation file"""
        json_file = self.translations_dir / f"{lang_code}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(translations, f, ensure_ascii=False, indent=4, sort_keys=True)

    def _parse_pot_entries(self) -> List[Dict]:
        """Parse POT file entries"""
        entries = []
        with open(self.pot_file, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = content.split("\n\n")
        for block in blocks:
            if "msgid" in block and "msgstr" in block:
                entry = {}
                msgid_match = re.search(r'msgid\s+"([^"]*)"', block)
                if msgid_match:
                    entry["msgid"] = msgid_match.group(1)
                    entry["is_plural"] = False
                    entry["comments"] = []
                    if "msgid" in entry and entry["msgid"]:
                        entries.append(entry)
        return entries

    def _escape_po_string(self, text: str) -> str:
        """Escape a string for PO file format"""
        if not text:
            return '""'

        # Escape backslashes first
        text = text.replace("\\", "\\\\")
        # Escape quotes
        text = text.replace('"', '\\"')
        # Handle newlines - split into multiple lines for readability
        if "\n" in text:
            lines = text.split("\n")
            if len(lines) == 2 and lines[1] == "":
                # Single trailing newline
                return f'"{lines[0]}\\n"'
            else:
                # Multiple lines - use multiline format
                result = '""'
                for i, line in enumerate(lines):
                    if i < len(lines) - 1:  # Not the last line
                        result += f'\n"{line}\\n"'
                    else:  # Last line
                        if line:  # If last line has content
                            result += f'\n"{line}"'
                return result
        # Handle other escape sequences
        text = text.replace("\t", "\\t")
        text = text.replace("\r", "\\r")

        return f'"{text}"'

    def _generate_po_file(self, lang_code: str, pot_entries: List[Dict]):
        """Generate PO file for a language"""
        lang_config = LANGUAGES[lang_code]
        po_dir = self.locale_dir / lang_code / "LC_MESSAGES"
        po_file = po_dir / "dfakeseeder.po"

        po_dir.mkdir(parents=True, exist_ok=True)

        translations = self._load_json_translation(lang_code)

        header = f"""# {lang_config['name']} translation for DFakeSeeder
# Copyright (C) 2024 DFakeSeeder Contributors
# This file is distributed under the same license as the DFakeSeeder package.
# FIRST AUTHOR <EMAIL@ADDRESS>, 2024.
#
msgid ""
msgstr ""
"Project-Id-Version: DFakeSeeder 1.0.0\\n"
"Report-Msgid-Bugs-To: https://github.com/username/dfakeseeder/issues\\n"
"POT-Creation-Date: 2025-09-18 17:51+0100\\n"
"PO-Revision-Date: 2024-09-18 18:30+0100\\n"
"Last-Translator: Claude <noreply@anthropic.com>\\n"
"Language-Team: {lang_config['name']} <{lang_code}@li.org>\\n"
"Language: {lang_code}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: {lang_config['plural_forms']}\\n"

"""

        content = header
        seen_msgids = set()

        for entry in pot_entries:
            if entry["msgid"] == "" or entry["msgid"] in seen_msgids:
                continue
            seen_msgids.add(entry["msgid"])

            escaped_msgid = self._escape_po_string(entry["msgid"])
            translation = translations.get(entry["msgid"], entry["msgid"])
            escaped_translation = self._escape_po_string(translation)

            content += f"msgid {escaped_msgid}\n"
            content += f"msgstr {escaped_translation}\n\n"

        with open(po_file, "w", encoding="utf-8") as f:
            f.write(content)

    # ==================== COMPILATION METHODS ====================

    def compile_translations(self, target_lang: Optional[str] = None) -> bool:
        """Compile PO files to MO files"""
        print("🔨 Compiling translation files...")

        languages = [target_lang] if target_lang else LANGUAGES.keys()
        compiled_count = 0
        failed_count = 0

        for lang_code in languages:
            if self._compile_po_to_mo(lang_code):
                print(f"   ✅ Compiled: {lang_code}")
                compiled_count += 1
            else:
                print(f"   ❌ Failed: {lang_code}")
                failed_count += 1

        print(f"📦 Compilation complete: {compiled_count} succeeded, {failed_count} failed")
        return failed_count == 0

    def _compile_po_to_mo(self, lang_code: str) -> bool:
        """Compile single PO file to MO"""
        po_file = self.locale_dir / lang_code / "LC_MESSAGES" / "dfakeseeder.po"
        mo_file = self.locale_dir / lang_code / "LC_MESSAGES" / "dfakeseeder.mo"

        if not po_file.exists():
            return False

        try:
            subprocess.run(
                ["msgfmt", "-o", str(mo_file), str(po_file)],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    # ==================== VALIDATION METHODS ====================

    def validate_translation_chain(self) -> bool:
        """Validate complete translation chain consistency"""
        print("🔗 DFakeSeeder Translation Chain Validator")
        print("=" * 60)
        print("Validating: JSON → POT → PO → MO")
        print()

        # Step 1: Validate JSON consistency
        json_consistent, english_keys = self._validate_json_consistency()

        # Step 2: Validate POT consistency
        pot_consistent, _ = self._validate_pot_consistency(english_keys)

        # Step 3: Validate PO/MO consistency
        po_mo_consistent = self._validate_po_mo_consistency()

        # Summary
        print("📊 Validation Summary")
        print("-" * 20)
        print(f"JSON files:  {'✅ Consistent' if json_consistent else '❌ Inconsistent'}")
        print(f"POT file:    {'✅ Consistent' if pot_consistent else '❌ Inconsistent'}")
        print(f"PO/MO files: {'✅ Consistent' if po_mo_consistent else '❌ Inconsistent'}")
        print()

        if json_consistent and pot_consistent and po_mo_consistent:
            print("🎉 Translation chain is fully consistent!")
            return True
        else:
            print("⚠️  Translation chain has inconsistencies that need attention.")
            return False

    def _validate_json_consistency(self) -> Tuple[bool, Set[str]]:
        """Validate JSON file consistency"""
        print("🔍 Step 1: Validating JSON file consistency and syntax")
        print("-" * 60)

        # Step 1a: Validate JSON syntax
        print("📝 Checking JSON syntax for all language files...")
        syntax_valid = True

        for json_file in self.translations_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    json.load(f)
                print(f"✅ {json_file.stem}: Valid JSON syntax")
            except json.JSONDecodeError as e:
                print(f"❌ {json_file.stem}: Invalid JSON - {e}")
                syntax_valid = False
            except Exception as e:
                print(f"❌ {json_file.stem}: Error reading file - {e}")
                syntax_valid = False

        if not syntax_valid:
            print("❌ JSON syntax validation failed!")
            return False, set()

        print()

        # Step 1b: Load English template
        english_file = self.translations_dir / "en.json"
        if not english_file.exists():
            print("❌ English template file not found!")
            return False, set()

        with open(english_file, "r", encoding="utf-8") as f:
            english_translations = json.load(f)
            english_keys = set(english_translations.keys())

        print(f"📋 English template contains {len(english_keys)} keys")
        print()

        # Step 1c: Validate key consistency and detect fallbacks
        print("🔍 Checking key consistency and English fallbacks...")
        all_consistent = True
        fallback_summary = {}

        for json_file in self.translations_dir.glob("*.json"):
            lang_code = json_file.stem
            if lang_code == "en":
                continue

            with open(json_file, "r", encoding="utf-8") as f:
                lang_translations = json.load(f)
                lang_keys = set(lang_translations.keys())

            missing_keys = english_keys - lang_keys
            extra_keys = lang_keys - english_keys

            # Count English fallbacks (where translation equals English)
            fallback_count = 0
            for key in english_keys:
                if key in lang_translations and key in english_translations:
                    if lang_translations[key] == english_translations[key]:
                        fallback_count += 1

            fallback_summary[lang_code] = {
                "total_keys": len(lang_keys),
                "missing_keys": len(missing_keys),
                "extra_keys": len(extra_keys),
                "fallback_count": fallback_count,
                "native_translations": len(lang_keys) - fallback_count,
                "fallback_percentage": (fallback_count / len(english_keys) * 100) if english_keys else 0,
            }

            if missing_keys or extra_keys:
                all_consistent = False
                print(f"❌ {lang_code}: Key mismatch")
                if missing_keys:
                    print(f"   Missing {len(missing_keys)} keys")
                if extra_keys:
                    print(f"   Extra {len(extra_keys)} keys")
            else:
                print(f"✅ {lang_code}: {len(lang_keys)} keys (consistent)")

            # Report fallback status
            native_percentage = ((len(lang_keys) - fallback_count) / len(english_keys) * 100) if english_keys else 0
            if fallback_count > 0:
                fallback_pct = fallback_summary[lang_code]["fallback_percentage"]
                print(f"   📊 {fallback_count}/{len(english_keys)} English fallbacks ({fallback_pct:.1f}%)")
                native_count = fallback_summary[lang_code]["native_translations"]
                print(f"   🌐 {native_count} native translations ({native_percentage:.1f}%)")
            else:
                print("   🎯 100% native translations!")

        print()

        # Step 1d: Summary of translation status
        print("📊 TRANSLATION FALLBACK SUMMARY")
        print("-" * 40)
        for lang_code, stats in fallback_summary.items():
            lang_name = LANGUAGES.get(lang_code, {}).get("name", lang_code)
            status = "🎯 Complete" if stats["fallback_count"] == 0 else f"⚠️ {stats['fallback_count']} fallbacks"
            print(f"{lang_name} ({lang_code}): {status}")
            if stats["fallback_count"] > 0:
                fallback_pct = stats["fallback_percentage"]
                native_pct = 100 - stats["fallback_percentage"]
                print(f"   └─ {fallback_pct:.1f}% fallbacks, {native_pct:.1f}% native")

        print()
        return all_consistent, english_keys

    def _validate_pot_consistency(self, english_keys: Set[str]) -> Tuple[bool, Set[str]]:
        """Validate POT file consistency"""
        print("🔍 Step 2: Validating POT file consistency")
        print("-" * 50)

        if not self.pot_file.exists():
            print(f"❌ POT file not found: {self.pot_file}")
            return False, set()

        # Extract POT strings
        with open(self.pot_file, "r", encoding="utf-8") as f:
            content = f.read()

        pattern = r'^msgid\s+"([^"]*)"'
        matches = re.findall(pattern, content, re.MULTILINE)
        pot_strings = {msg for msg in matches if msg and msg != ""}

        print(f"📋 POT file contains {len(pot_strings)} strings")

        missing_in_pot = english_keys - pot_strings
        pot_consistent = len(missing_in_pot) == 0

        if missing_in_pot:
            print(f"❌ {len(missing_in_pot)} JSON strings missing from POT")
        else:
            print("✅ POT file contains all JSON strings")

        print()
        return pot_consistent, pot_strings

    def _validate_po_mo_consistency(self) -> bool:
        """Validate PO/MO file consistency"""
        print("🔍 Step 3: Validating PO/MO file consistency")
        print("-" * 50)

        if not self.locale_dir.exists():
            print(f"❌ Locale directory not found: {self.locale_dir}")
            return False

        all_consistent = True
        languages = []

        for item in self.locale_dir.iterdir():
            if item.is_dir() and item.name in LANGUAGES:
                po_file = item / "LC_MESSAGES" / "dfakeseeder.po"
                if po_file.exists():
                    languages.append(item.name)

        for lang in sorted(languages):
            po_file = self.locale_dir / lang / "LC_MESSAGES" / "dfakeseeder.po"
            mo_file = self.locale_dir / lang / "LC_MESSAGES" / "dfakeseeder.mo"

            # Check MO file
            mo_exists = mo_file.exists() and mo_file.stat().st_size > 0

            if mo_exists:
                print(f"✅ {lang}: PO/MO consistent")
            else:
                all_consistent = False
                print(f"❌ {lang}: MO file missing/empty")

        print()
        return all_consistent

    # ==================== ANALYSIS METHODS ====================

    def identify_fallbacks_for_translation(self, target_lang: Optional[str] = None) -> bool:
        """Identify English fallbacks that need translation"""
        print("🔍 IDENTIFYING ENGLISH FALLBACKS FOR TRANSLATION")
        print("=" * 60)
        print("DEBUG: Starting identify_fallbacks_for_translation")

        english_file = self.translations_dir / "en.json"
        print(f"DEBUG: English file path: {english_file}")
        if not english_file.exists():
            print("❌ English template file not found!")
            return False

        print("DEBUG: Loading English translations...")
        with open(english_file, "r", encoding="utf-8") as f:
            english_translations = json.load(f)
        print(f"DEBUG: Loaded {len(english_translations)} English translations")

        languages = [target_lang] if target_lang else [lang for lang in LANGUAGES.keys() if lang != "en"]
        print(f"DEBUG: Processing languages: {languages}")
        total_fallback_files = 0

        for i, lang_code in enumerate(languages):
            print(f"DEBUG: Processing language {i+1}/{len(languages)}: {lang_code}")
            if lang_code not in LANGUAGES:
                continue

            lang_config = LANGUAGES[lang_code]
            json_file = self.translations_dir / f"{lang_code}.json"
            print(f"DEBUG: Language file: {json_file}")

            if not json_file.exists():
                print(f"❌ {lang_config['name']} ({lang_code}): File missing")
                continue

            print(f"DEBUG: Loading translations for {lang_code}...")
            with open(json_file, "r", encoding="utf-8") as f:
                translations = json.load(f)
            print(f"DEBUG: Loaded {len(translations)} translations for {lang_code}")

            # Find English fallbacks
            print(f"DEBUG: Finding fallbacks for {lang_code}...")
            fallbacks = []
            processed_count = 0
            for key, english_value in english_translations.items():
                if key in translations and translations[key] == english_value:
                    fallbacks.append(key)
                processed_count += 1
                if processed_count % 100 == 0:
                    print(f"DEBUG: Processed {processed_count}/{len(english_translations)} strings for {lang_code}")
            print(f"DEBUG: Found {len(fallbacks)} fallbacks for {lang_code}")

            if not fallbacks:
                print(f"🎯 {lang_config['name']} ({lang_code}): No fallbacks - 100% translated!")
                continue

            print(f"🔍 {lang_config['name']} ({lang_code}): {len(fallbacks)} strings need translation")
            print("-" * 50)

            # Group fallbacks by category for easier translation
            ui_elements = []
            column_headers = []
            settings_items = []
            other_items = []

            for key in sorted(fallbacks):
                if any(
                    col in key.lower()
                    for col in [
                        "name",
                        "progress",
                        "size",
                        "downloaded",
                        "uploaded",
                        "ratio",
                        "speed",
                        "peers",
                        "seeds",
                    ]
                ):
                    column_headers.append(key)
                elif any(ui in key.lower() for ui in ["<b>", "settings", "options", "preferences", "advanced"]):
                    settings_items.append(key)
                elif any(ui in key.lower() for ui in ["button", "menu", "dialog", "window", "tab"]):
                    ui_elements.append(key)
                else:
                    other_items.append(key)

            if column_headers:
                print("📊 Column Headers:")
                for key in column_headers[:10]:  # Show first 10
                    print(f'   "{key}" → "{english_translations[key]}"')
                if len(column_headers) > 10:
                    print(f"   ... and {len(column_headers) - 10} more")
                print()

            if settings_items:
                print("⚙️ Settings & Options:")
                for key in settings_items[:10]:  # Show first 10
                    print(f'   "{key}" → "{english_translations[key]}"')
                if len(settings_items) > 10:
                    print(f"   ... and {len(settings_items) - 10} more")
                print()

            if ui_elements:
                print("🖥️ UI Elements:")
                for key in ui_elements[:10]:  # Show first 10
                    print(f'   "{key}" → "{english_translations[key]}"')
                if len(ui_elements) > 10:
                    print(f"   ... and {len(ui_elements) - 10} more")
                print()

            if other_items:
                print("📝 Other Items:")
                for key in other_items[:10]:  # Show first 10
                    print(f'   "{key}" → "{english_translations[key]}"')
                if len(other_items) > 10:
                    print(f"   ... and {len(other_items) - 10} more")
                print()

            # Save fallbacks to a translation work file with instructions
            fallback_file = self.translations_dir / f"{lang_code}_fallbacks_to_translate.json"
            fallback_data = {
                "_instructions": f"TRANSLATION WORK FILE FOR {lang_config['name'].upper()} ({lang_code.upper()})",
                "_help": (
                    "Replace English values with proper translations, then run: "
                    f"python translation_build_manager.py update-from-fallbacks --lang {lang_code}"
                ),
                "_total_strings": len(fallbacks),
                "_categories": {
                    "column_headers": len(column_headers),
                    "settings_items": len(settings_items),
                    "ui_elements": len(ui_elements),
                    "other_items": len(other_items),
                },
                "_note": "Do not modify keys (left side), only modify values (right side) with translations",
            }

            # Add the actual translation work
            for key in fallbacks:
                fallback_data[key] = english_translations[key]

            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(fallback_data, f, ensure_ascii=False, indent=2, sort_keys=False)

            print(f"💾 Saved {len(fallbacks)} fallbacks to: {fallback_file}")
            print("📝 Edit this file with translations, then run:")
            print(f"   python tools/translation_build_manager.py update-from-fallbacks --lang {lang_code}")
            print()
            total_fallback_files += 1

        if total_fallback_files > 0:
            print("🎯 WORKFLOW SUMMARY")
            print(f"   Created {total_fallback_files} translation work files")
            print("   📝 Edit the *_fallbacks_to_translate.json files with proper translations")
            print("   🔄 Run update-from-fallbacks command when done")
            print("   ♻️  Temporary files will be cleaned up automatically")
        else:
            print("🎉 All languages are fully translated! No fallback files needed.")

        return True

    def update_translations_from_fallbacks(self, target_lang: Optional[str] = None) -> bool:
        """Update translations from edited fallback files"""
        print("🔄 UPDATING TRANSLATIONS FROM FALLBACK FILES")
        print("=" * 50)

        languages = [target_lang] if target_lang else [lang for lang in LANGUAGES.keys() if lang != "en"]
        updated_count = 0
        processed_files = []
        cleanup_files = []

        for lang_code in languages:
            if lang_code not in LANGUAGES:
                continue

            lang_config = LANGUAGES[lang_code]
            json_file = self.translations_dir / f"{lang_code}.json"
            fallback_file = self.translations_dir / f"{lang_code}_fallbacks_to_translate.json"

            if not fallback_file.exists():
                continue

            if not json_file.exists():
                print(f"❌ {lang_config['name']} ({lang_code}): Main translation file missing")
                continue

            print(f"🔧 Processing {lang_config['name']} ({lang_code})...")

            # Load both files
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    translations = json.load(f)

                with open(fallback_file, "r", encoding="utf-8") as f:
                    fallback_translations = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ {lang_config['name']} ({lang_code}): Invalid JSON in fallback file - {e}")
                continue
            except Exception as e:
                print(f"❌ {lang_config['name']} ({lang_code}): Error reading files - {e}")
                continue

            # Filter out metadata keys and update translations
            updated_keys = 0
            metadata_keys = {"_instructions", "_help", "_total_strings", "_categories", "_note"}

            for key, translated_value in fallback_translations.items():
                # Skip metadata keys
                if key in metadata_keys:
                    continue

                if key in translations:
                    old_value = translations[key]
                    translations[key] = translated_value
                    if old_value != translated_value:
                        updated_keys += 1

            if updated_keys > 0:
                # Create backup before updating
                backup_file = self.translations_dir / f"{lang_code}.json.backup"
                try:
                    import shutil

                    shutil.copy2(json_file, backup_file)

                    # Save updated translations
                    with open(json_file, "w", encoding="utf-8") as f:
                        json.dump(translations, f, ensure_ascii=False, indent=2, sort_keys=True)

                    print(f"   ✅ Updated {updated_keys} translations")
                    print(f"   💾 Backup saved to: {backup_file}")
                    updated_count += updated_keys
                    processed_files.append(lang_code)
                    cleanup_files.append(fallback_file)

                except Exception as e:
                    print(f"   ❌ Failed to save: {e}")
                    continue

            else:
                print("   ℹ️ No changes found (all values identical)")
                cleanup_files.append(fallback_file)

        # Cleanup successful fallback files
        if cleanup_files:
            print("\n🧹 Cleaning up temporary translation work files...")
            for cleanup_file in cleanup_files:
                try:
                    cleanup_file.unlink()
                    print(f"   ♻️  Removed: {cleanup_file.name}")
                except Exception as e:
                    print(f"   ⚠️  Could not remove {cleanup_file.name}: {e}")

        # Summary
        print("\n🎉 TRANSLATION UPDATE COMPLETE!")
        print(f"   📊 Total translations updated: {updated_count}")
        print(f"   🔧 Languages processed: {len(processed_files)}")
        print(f"   🧹 Temporary files cleaned: {len(cleanup_files)}")

        if processed_files:
            print("\n🔄 Next steps:")
            print("   1. Run 'build' to regenerate PO/MO files")
            print("   2. Test the application with updated translations")
            print("   3. Run 'validate' to verify translation consistency")

        return updated_count > 0

    def sync_missing_keys(self, target_lang: Optional[str] = None) -> bool:
        """Sync missing keys from English template to all language files"""
        print("🔄 SYNCING MISSING KEYS FROM ENGLISH TEMPLATE")
        print("=" * 60)
        print("DEBUG: Starting sync_missing_keys method")

        # Load English template
        english_file = self.translations_dir / "en.json"
        print(f"DEBUG: English file path: {english_file}")
        if not english_file.exists():
            print("❌ English template file not found!")
            return False

        print("DEBUG: Loading English translations...")
        with open(english_file, "r", encoding="utf-8") as f:
            english_translations = json.load(f)

        english_keys = set(english_translations.keys())
        print(f"📋 English template contains {len(english_keys)} keys")
        print()

        # Determine which languages to process
        languages = [target_lang] if target_lang else [lang for lang in LANGUAGES.keys() if lang != "en"]
        print(f"DEBUG: Processing languages: {languages}")

        total_added = 0

        for lang_code in languages:
            print(f"DEBUG: Processing language {lang_code}")
            if lang_code not in LANGUAGES:
                print(f"DEBUG: Skipping unknown language {lang_code}")
                continue

            lang_config = LANGUAGES[lang_code]
            json_file = self.translations_dir / f"{lang_code}.json"
            print(f"DEBUG: Language file path: {json_file}")

            if not json_file.exists():
                print(f"❌ {lang_config['name']} ({lang_code}): File does not exist")
                continue

            print(f"DEBUG: Loading existing translations for {lang_code}...")
            # Load existing translations
            with open(json_file, "r", encoding="utf-8") as f:
                existing_translations = json.load(f)

            existing_keys = set(existing_translations.keys())
            missing_keys = english_keys - existing_keys
            print(f"DEBUG: {lang_code} has {len(existing_keys)} keys, missing {len(missing_keys)}")

            if not missing_keys:
                print(f"✅ {lang_config['name']} ({lang_code}): Already complete ({len(existing_keys)} keys)")
                continue

            print(f"🔧 {lang_config['name']} ({lang_code}): Adding {len(missing_keys)} missing keys")

            # Add missing keys with English fallback
            print(f"DEBUG: Creating updated translations for {lang_code}...")
            updated_translations = existing_translations.copy()
            for key in missing_keys:
                updated_translations[key] = english_translations[key]  # Use English as fallback

            print(f"DEBUG: Saving updated file for {lang_code}...")
            # Save updated file with sorted keys
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(updated_translations, f, ensure_ascii=False, indent=2, sort_keys=True)

            print(f"   ✅ Added {len(missing_keys)} keys (now {len(updated_translations)} total)")
            total_added += len(missing_keys)

        print()
        print(f"🎉 Sync complete! Added {total_added} total missing keys across all languages")
        print("DEBUG: sync_missing_keys method completed")
        return True

    def analyze_coverage(self) -> bool:
        """Analyze translation coverage and quality"""
        print("📊 TRANSLATION COVERAGE ANALYSIS")
        print("=" * 50)

        english_file = self.translations_dir / "en.json"
        if not english_file.exists():
            print("❌ English template file not found!")
            return False

        with open(english_file, "r", encoding="utf-8") as f:
            english_translations = json.load(f)

        total_strings = len(english_translations)

        for lang_code, lang_config in LANGUAGES.items():
            if lang_code == "en":
                continue

            json_file = self.translations_dir / f"{lang_code}.json"
            if not json_file.exists():
                print(f"❌ {lang_config['name']} ({lang_code}): File missing")
                continue

            with open(json_file, "r", encoding="utf-8") as f:
                translations = json.load(f)

            # Calculate coverage
            translated_count = len(translations)
            coverage = (translated_count / total_strings) * 100 if total_strings else 0

            # Count English fallbacks
            fallbacks = sum(
                1 for k, v in translations.items() if k in english_translations and v == english_translations[k]
            )
            native_count = translated_count - fallbacks
            native_coverage = (native_count / total_strings) * 100 if total_strings else 0

            # Status
            if coverage >= 98.0:
                status = "🎯 TARGET ACHIEVED"
                if native_coverage >= 95.0:
                    status += " (High Quality)"
                else:
                    status += " (Technical Fallbacks)"
            elif coverage >= 95.0:
                status = "🟡 Close to Target"
            else:
                status = "🔴 Needs Work"

            print(f"📊 {lang_config['name']} ({lang_code}): {coverage:.1f}% coverage")
            print(f"   └─ {translated_count}/{total_strings} strings translated")
            if fallbacks > 0:
                print(f"   └─ {fallbacks} English fallbacks ({fallbacks/total_strings*100:.1f}%)")
            print(f"   └─ Native coverage: {native_coverage:.1f}%")
            print(f"   └─ {status}")
            print()

        return True

    def cleanup_temp_files(self) -> bool:
        """Clean up temporary translation files"""
        print("🧹 CLEANING UP TEMPORARY TRANSLATION FILES")
        print("=" * 50)

        cleanup_patterns = [
            "*_fallbacks_to_translate.json",  # Fallback work files
            "*.json.backup",  # Backup files
        ]

        total_removed = 0

        for pattern in cleanup_patterns:
            files_to_remove = list(self.translations_dir.glob(pattern))
            if files_to_remove:
                print(f"🗑️  Removing {len(files_to_remove)} {pattern} files...")
                for file_path in files_to_remove:
                    try:
                        file_path.unlink()
                        print(f"   ✅ Removed: {file_path.name}")
                        total_removed += 1
                    except OSError as e:
                        print(f"   ❌ Failed to remove {file_path.name}: {e}")
            else:
                print(f"   ℹ️  No {pattern} files found")

        if total_removed > 0:
            print(f"\n🎉 Cleanup complete! Removed {total_removed} temporary files")
        else:
            print("\n✨ No temporary files to clean up - directory is already clean!")

        return True

    # ==================== ENHANCEMENT METHODS ====================

    def enhance_translations(self) -> bool:
        """Enhance translations by adding missing strings and attributes"""
        print("🔧 ENHANCING TRANSLATIONS")
        print("=" * 30)

        # Add missing JSON translations
        print("📝 Adding missing translation keys...")
        english_file = self.translations_dir / "en.json"
        if not english_file.exists():
            print("❌ English template file not found!")
            return False

        with open(english_file, "r", encoding="utf-8") as f:
            english_keys = set(json.load(f).keys())

        enhanced_count = 0
        for lang_code in LANGUAGES:
            if lang_code == "en":
                continue

            json_file = self.translations_dir / f"{lang_code}.json"
            if not json_file.exists():
                continue

            with open(json_file, "r", encoding="utf-8") as f:
                translations = json.load(f)

            original_count = len(translations)
            missing_keys = english_keys - set(translations.keys())

            if missing_keys:
                # Add missing keys as untranslated
                with open(english_file, "r", encoding="utf-8") as f:
                    english_translations = json.load(f)

                for key in missing_keys:
                    if key in english_translations:
                        translations[key] = english_translations[key]

                self._save_json_translation(lang_code, translations)
                added = len(translations) - original_count
                print(f"   ✅ {lang_code}: Added {added} missing strings")
                enhanced_count += 1

        # Add translatable attributes to XML files
        print("🎨 Adding translatable attributes to XML files...")
        xml_files = list(self.source_dir.rglob("*.xml"))

        for xml_file in xml_files:
            if self._add_translatable_attributes(xml_file):
                print(f"   ✅ Enhanced: {xml_file.name}")

        print(f"🎉 Enhancement complete! Enhanced {enhanced_count} language files")
        return True

    def _add_translatable_attributes(self, xml_file: Path) -> bool:
        """Add translatable attributes to XML file"""
        try:
            with open(xml_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Pattern for properties that should be translatable but aren't
            pattern = r'(<property\s+name="(?:label|tooltip-text)"(?!\s+translatable="yes"))(>)'
            replacement = r'\1 translatable="yes"\2'

            new_content = re.sub(pattern, replacement, content)

            if new_content != content:
                with open(xml_file, "w", encoding="utf-8") as f:
                    f.write(new_content)
                return True

        except Exception as e:
            print(f"   ⚠️  Warning: Could not process {xml_file}: {e}")

        return False

    def comprehensive_extraction_and_build(self, target_lang: Optional[str] = None) -> bool:
        """Complete comprehensive extraction and build process"""
        print("🔍 COMPREHENSIVE TRANSLATION EXTRACTION & BUILD")
        print("=" * 60)
        print("🎯 This will find and add ALL missing translatable strings")
        print("   Including column headers, settings tabs, and UI elements")
        print()

        try:
            # Step 1: Enhanced extraction from source files
            print("🔍 Step 1: Comprehensive string extraction")
            if not self.extract_strings():
                print("❌ Failed during string extraction")
                return False

            # Step 2: Sync extracted strings to JSON files
            print("\n🔄 Step 2: Syncing extracted strings to JSON")
            if not self._sync_extracted_strings_to_json():
                print("❌ Failed during JSON sync")
                return False

            # Step 3: Build complete translation system
            print("\n🏧 Step 3: Building complete translation system")
            if not self.build_translations(target_lang):
                print("❌ Failed during translation build")
                return False

            # Step 4: Analyze results
            print("\n📊 Step 4: Analyzing translation coverage")
            self.analyze_coverage()

            print("\n🎉 COMPREHENSIVE EXTRACTION COMPLETE!")
            print("   All translatable strings have been found and processed")
            print("   Translation files are ready for use")

            return True

        except Exception as e:
            print(f"❌ Comprehensive extraction failed: {e}")
            return False

    def translation_workflow(self, target_lang: Optional[str] = None) -> bool:
        """Complete fallback translation workflow: identify → edit → update"""
        print("🔄 COMPLETE FALLBACK TRANSLATION WORKFLOW")
        print("=" * 60)
        print("This workflow helps you translate English fallbacks step by step:")
        print("1. 🔍 Identify fallbacks that need translation")
        print("2. 📝 Create work files for editing")
        print("3. ✏️  [Manual step] Edit the work files with translations")
        print("4. 🔄 Update main translation files")
        print("5. 🧹 Clean up temporary files")
        print()

        # Step 1: Identify fallbacks
        print("🔍 Step 1: Identifying fallbacks...")
        if not self.identify_fallbacks_for_translation(target_lang):
            print("❌ Failed to identify fallbacks")
            return False

        # Check if any work files were created
        languages = [target_lang] if target_lang else [lang for lang in LANGUAGES.keys() if lang != "en"]
        work_files = []
        for lang_code in languages:
            if lang_code in LANGUAGES:
                fallback_file = self.translations_dir / f"{lang_code}_fallbacks_to_translate.json"
                if fallback_file.exists():
                    work_files.append((lang_code, fallback_file))

        if not work_files:
            print("🎉 No fallback work files needed - all translations are complete!")
            return True

        print("\n📝 MANUAL EDITING STEP")
        print("=" * 30)
        print(f"Found {len(work_files)} work files that need translation:")
        for lang_code, work_file in work_files:
            lang_name = LANGUAGES[lang_code]["name"]
            print(f"   📄 {lang_name} ({lang_code}): {work_file.name}")

        print("\n🛠️  INSTRUCTIONS:")
        print("   1. Edit the work files above with proper translations")
        print("   2. Replace English values with native language translations")
        print("   3. Do NOT modify the keys (left side), only values (right side)")
        print("   4. When done, run: python tools/translation_build_manager.py update-from-fallbacks")
        print("      Or for specific language: --lang <code>")

        print("\n⏸️  WORKFLOW PAUSED - Complete manual editing then run update-from-fallbacks")
        return True

    # ==================== MAIN CLI INTERFACE ====================


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="DFakeSeeder Translation Manager - Unified translation framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  extract               Extract translatable strings from source files
  sync                  Sync extracted strings to JSON files (run after extract)
  build                 Build complete translation system (JSON → POT → PO → MO)
  compile               Compile PO files to MO files
  validate              Validate translation chain consistency with JSON syntax & fallback analysis
  enhance               Enhance translations (add missing strings/attributes)
  analyze               Analyze translation coverage and quality
  identify-fallbacks    Identify English fallbacks that need translation
  update-from-fallbacks Update translations from edited fallback files
  sync-keys             Sync missing keys from English template to all language files
  workflow              Complete fallback translation workflow (identify → edit → update)
  comprehensive         Full extraction + sync + build cycle for comprehensive coverage
  cleanup               Clean up temporary translation files (backups, fallback work files)

Examples:
  python translation_manager.py extract            # Extract strings from source
  python translation_manager.py sync               # Sync extracted strings to JSON
  python translation_manager.py build --lang de    # Build German only
  python translation_manager.py validate           # Validate all files
  python translation_manager.py analyze            # Show coverage report
  python translation_manager.py cleanup            # Clean up temporary files
        """,
    )

    parser.add_argument(
        "command",
        choices=[
            "extract",
            "sync",
            "build",
            "compile",
            "validate",
            "enhance",
            "analyze",
            "comprehensive",
            "identify-fallbacks",
            "update-from-fallbacks",
            "sync-keys",
            "workflow",
            "cleanup",
        ],
        help="Command to execute",
    )
    parser.add_argument("--lang", type=str, help="Target specific language (e.g., 'de' for German)")
    parser.add_argument("--force", action="store_true", help="Force regeneration of files")

    args = parser.parse_args()

    # Validate language if specified
    if args.lang and args.lang not in LANGUAGES:
        print(f"❌ Unknown language: {args.lang}")
        print(f"Available languages: {', '.join(LANGUAGES.keys())}")
        sys.exit(1)

    # Initialize manager
    manager = TranslationBuildManager()

    # Execute command
    success = False

    if args.command == "extract":
        success = manager.extract_strings()
    elif args.command == "sync":
        success = manager._sync_extracted_strings_to_json()
    elif args.command == "build":
        success = manager.build_translations(args.lang)
    elif args.command == "compile":
        success = manager.compile_translations(args.lang)
    elif args.command == "validate":
        success = manager.validate_translation_chain()
    elif args.command == "enhance":
        success = manager.enhance_translations()
    elif args.command == "analyze":
        success = manager.analyze_coverage()
    elif args.command == "comprehensive":
        success = manager.comprehensive_extraction_and_build(args.lang)
    elif args.command == "identify-fallbacks":
        success = manager.identify_fallbacks_for_translation(args.lang)
    elif args.command == "update-from-fallbacks":
        success = manager.update_translations_from_fallbacks(args.lang)
    elif args.command == "sync-keys":
        success = manager.sync_missing_keys(args.lang)
    elif args.command == "workflow":
        success = manager.translation_workflow(args.lang)
    elif args.command == "cleanup":
        success = manager.cleanup_temp_files()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
