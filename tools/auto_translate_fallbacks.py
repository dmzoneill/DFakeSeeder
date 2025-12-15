#!/usr/bin/env python3
"""
Automatically translate fallback files using Claude Code Agent.

This script processes *_fallbacks_to_translate.json files and uses Claude
to provide translations for each language.
"""

import json
import os
import sys
from pathlib import Path


def load_fallback_file(filepath):
    """Load a fallback translation file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_translated_file(filepath, data):
    """Save translated data back to the fallback file."""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_language_name(lang_code):
    """Get full language name from code."""
    language_names = {
        'ar': 'Arabic',
        'bn': 'Bengali',
        'de': 'German',
        'es': 'Spanish',
        'fa': 'Persian',
        'fr': 'French',
        'ga': 'Irish',
        'hi': 'Hindi',
        'id': 'Indonesian',
        'it': 'Italian',
        'ja': 'Japanese',
        'ko': 'Korean',
        'nl': 'Dutch',
        'pl': 'Polish',
        'pt': 'Portuguese',
        'ru': 'Russian',
        'sv': 'Swedish',
        'tr': 'Turkish',
        'vi': 'Vietnamese',
        'zh': 'Chinese',
    }
    return language_names.get(lang_code, lang_code.upper())


def translate_with_claude(strings_to_translate, lang_code, lang_name):
    """
    Use Claude Code Agent to translate strings.

    This creates a task that Claude can pick up and process.
    """
    # Create a translation prompt for Claude
    prompt = f"""Please translate the following English strings to {lang_name} ({lang_code}).

IMPORTANT TRANSLATION RULES:
1. Do NOT translate:
   - Technical terms: BitTorrent, DHT, qBittorrent, µTorrent, Transmission, Vuze, Deluge, rTorrent
   - Product names: "D' Fake Seeder", "DFakeSeeder", BiglyBT
   - URLs and IP addresses: "127.0.0.1", "http://localhost:8080"
   - Symbols and punctuation: "#", ":", "ℹ️"
   - Keyboard shortcuts: "Ctrl+F", "Ctrl+R", "Ctrl+,"
   - Technical identifiers: "open-menu-symbolic", "id", "status", "name"
   - Distribution algorithm names: "Pareto", "Log-Normal"
   - Theme names: "Modern Chunky", "Standard"

2. DO translate:
   - UI element names: "Simulation", "Tracker", "Torrent", "Torrents"
   - General words: "Name", "Port", "Status", "Server:", "Seed"
   - Action words: "OK"
   - Common terms: "normal"

3. Keep the same JSON format with metadata fields intact.

Strings to translate:
{json.dumps(strings_to_translate, ensure_ascii=False, indent=2)}

Return ONLY the JSON with translated values (do not translate the keys, only the values).
"""

    print(f"\n{'='*70}")
    print(f"🌍 Translation Request for {lang_name} ({lang_code})")
    print(f"{'='*70}")
    print(f"📝 Need to translate {len([k for k in strings_to_translate if not k.startswith('_')])} strings")
    print(f"\n⚠️  MANUAL TRANSLATION REQUIRED")
    print(f"This script cannot automatically translate without API access.")
    print(f"Please translate manually or integrate with translation API.\n")

    # For now, return the original (this would be replaced with actual API call)
    return strings_to_translate


def process_fallback_files(translations_dir):
    """Process all fallback files in the translations directory."""
    fallback_files = list(Path(translations_dir).glob('*_fallbacks_to_translate.json'))

    if not fallback_files:
        print("✅ No fallback files found - all translations complete!")
        return True

    print(f"\n🔍 Found {len(fallback_files)} fallback files to process")

    for fallback_file in fallback_files:
        # Extract language code from filename: de_fallbacks_to_translate.json -> de
        lang_code = fallback_file.stem.split('_')[0]
        lang_name = get_language_name(lang_code)

        print(f"\n📋 Processing {lang_name} ({lang_code})...")

        # Load the fallback file
        data = load_fallback_file(fallback_file)

        # Filter out metadata fields
        metadata_keys = {k for k in data.keys() if k.startswith('_')}
        translatable_keys = {k for k in data.keys() if not k.startswith('_')}

        if not translatable_keys:
            print(f"   ✅ No strings to translate for {lang_name}")
            continue

        print(f"   📝 {len(translatable_keys)} strings need translation")

        # Create strings dict for translation
        strings_to_translate = {k: data[k] for k in translatable_keys}

        # Attempt translation (currently manual prompt)
        translated = translate_with_claude(strings_to_translate, lang_code, lang_name)

        # Note: In a real implementation, you would:
        # 1. Send strings_to_translate to Claude API or other translation service
        # 2. Receive translated_strings back
        # 3. Update data with translations
        # 4. Save the file
        # 5. Then run update-from-fallbacks

        # For now, we just inform the user
        print(f"   ⏳ Manual translation required for {lang_name}")
        print(f"   📁 File: {fallback_file}")

    print("\n" + "="*70)
    print("❌ Automatic translation not implemented")
    print("="*70)
    print("\n💡 To complete translation workflow:")
    print("   1. Manually edit the *_fallbacks_to_translate.json files")
    print("   2. Run: python tools/translation_build_manager.py update-from-fallbacks")
    print("   3. Run: python tools/translation_build_manager.py analyze")
    print("   4. Run: python tools/translation_build_manager.py validate")
    print("   5. Run: python tools/translation_build_manager.py cleanup\n")

    return False


def main():
    """Main execution function."""
    # Get the translations directory
    script_dir = Path(__file__).parent
    translations_dir = script_dir / "translations"

    if not translations_dir.exists():
        print(f"❌ Translations directory not found: {translations_dir}")
        return 1

    # Process all fallback files
    success = process_fallback_files(translations_dir)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
