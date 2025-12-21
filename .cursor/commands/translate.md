# Translation Workflow

Run the full translation workflow for DFakeSeeder.

## Command
```bash
make translate-workflow
```

## What This Does
1. **Extract** - Scans Python and XML files for translatable strings
2. **Sync** - Updates language files with new strings
3. **Sync-keys** - Ensures all language files have consistent keys
4. **Identify-fallbacks** - Finds strings needing translation
5. **Translate-fallbacks** - Translates missing strings
6. **Update-from-fallbacks** - Merges translations back
7. **Build** - Compiles PO files to MO binary files
8. **Analyze** - Reports translation coverage

## Manual Steps (if needed)
```bash
python3 tools/translation_build_manager.py extract
python3 tools/translation_build_manager.py sync
python3 tools/translation_build_manager.py sync-keys
python3 tools/translation_build_manager.py identify-fallbacks
python3 tools/translation_build_manager.py translate-fallbacks
python3 tools/translation_build_manager.py update-from-fallbacks
python3 tools/translation_build_manager.py build
python3 tools/translation_build_manager.py analyze
```

## ⚠️ CRITICAL RULES
- **NEVER** edit `tools/translations/{en,de,es,...}.json` directly
- **DO** edit `tools/translations/*_fallbacks_to_translate.json` files
- Then run `make translate-workflow`

## Key Files
- Translation manager: `tools/translation_build_manager.py`
- Locale files: `d_fake_seeder/components/locale/`
- Translation JSONs: `tools/translations/`

