# PyPI Packaging Guide for DFakeSeeder

This document explains how DFakeSeeder is packaged for PyPI distribution and how it maintains compatibility with both PyPI and RPM packaging systems.

## Overview

DFakeSeeder supports multiple distribution methods:
1. **PyPI** (`pip install d-fake-seeder`) - Python package repository
2. **RPM** (`dnf install dfakeseeder`) - Red Hat/Fedora package format
3. **Debian** (`.deb`) - Debian/Ubuntu package format
4. **Flatpak** - Universal Linux package

This guide focuses on PyPI packaging while maintaining compatibility with other distribution methods.

## PyPI vs RPM: Key Differences

### PyPI Installation
- Installs to Python site-packages (e.g., `/usr/local/lib/python3.11/site-packages/`)
- Uses `pip` for dependency management
- Desktop integration via post-install scripts
- User-level installation: `~/.local/`
- Config from embedded `d_fake_seeder/config/default.json`

### RPM Installation
- Installs to system directories (`/opt/dfakeseeder/`, `/etc/dfakeseeder/`)
- Uses system package manager (`dnf`/`yum`) for dependencies
- System-wide desktop integration
- Wrapper script in `/usr/bin/dfakeseeder`
- Config from `/etc/dfakeseeder/default.json` (system-wide)

## Package Structure

### Files Included in PyPI Distribution

```
d-fake-seeder/
├── d_fake_seeder/
│   ├── __init__.py
│   ├── dfakeseeder.py           # Main application
│   ├── dfakeseeder_tray.py      # Tray application
│   ├── controller.py            # MVC controller
│   ├── model.py                 # MVC model
│   ├── view.py                  # MVC view
│   ├── post_install.py          # Desktop integration helper
│   ├── dfakeseeder.desktop      # Desktop file
│   ├── components/
│   │   ├── images/              # Icons (all sizes)
│   │   └── ui/                  # GTK4 UI XML files
│   ├── config/
│   │   ├── default.json         # Default config (PyPI)
│   │   └── rpm-default.json     # RPM-specific (excluded from PyPI)
│   ├── domain/                  # Domain logic
│   ├── lib/                     # Core libraries
│   └── locale/                  # Translations (15 languages)
├── setup.py                     # PyPI build configuration
├── MANIFEST.in                  # Package inclusion rules
├── README.md                    # Documentation
└── LICENSE                      # MIT License
```

### Files Excluded from PyPI

The `MANIFEST.in` explicitly excludes:
- `packaging/` - RPM wrapper scripts
- `dfakeseeder.spec` - RPM spec file
- `control` - Debian control file
- `rpmbuild/` - RPM build artifacts
- `debbuild/` - Debian build artifacts

## Dependencies

### Runtime Dependencies

Defined in `setup.py`:

```python
install_requires = [
    "requests>=2.31.0",      # HTTP client for tracker communication
    "typer>=0.12.3",         # CLI framework
    "urllib3>=1.26.18",      # HTTP library
    "PyGObject>=3.42.0",     # GTK4 Python bindings
    "watchdog>=4.0.0",       # File system monitoring
    "bencodepy>=0.9.5",      # Torrent file parsing
]
```

### System Dependencies

Not managed by pip (must be installed separately):
- Python 3.11+
- GTK4 libraries
- GObject Introspection

**Installation example:**
```bash
# Fedora/RHEL
sudo dnf install python3-gobject gtk4

# Debian/Ubuntu
sudo apt install python3-gi gir1.2-gtk-4.0

# Arch Linux
sudo pacman -S python-gobject gtk4
```

## Configuration System Compatibility

### PyPI Installation Flow

1. **Package Installation**:
   ```bash
   pip install d-fake-seeder
   ```

2. **First Run** (AppSettings initialization):
   - Checks for system config: `/etc/dfakeseeder/default.json`
   - If not found, uses embedded: `d_fake_seeder/config/default.json`
   - Creates user config: `~/.config/dfakeseeder/settings.json`
   - Creates torrents dir: `~/.config/dfakeseeder/torrents/`

3. **Desktop Integration** (optional):
   ```bash
   dfs-install-desktop
   ```

### RPM Installation Flow

1. **Package Installation**:
   ```bash
   sudo dnf install dfakeseeder
   ```

2. **System Setup** (automatic):
   - Installs wrapper: `/usr/bin/dfakeseeder`
   - Installs system config: `/etc/dfakeseeder/default.json`
   - Installs desktop file: `/usr/share/applications/dfakeseeder.desktop`
   - Installs icons: `/usr/share/icons/hicolor/*/apps/`

3. **First Run**:
   - Uses system config: `/etc/dfakeseeder/default.json`
   - Creates user config: `~/.config/dfakeseeder/settings.json`

### Shared Configuration Logic

Both installations use the same `AppSettings` class:

```python
# From d_fake_seeder/domain/app_settings.py (lines 131-154)

# Determine source config file (priority order):
# 1. System-wide RPM config: /etc/dfakeseeder/default.json
# 2. Package default: d_fake_seeder/config/default.json
system_config = Path("/etc/dfakeseeder/default.json")
if system_config.exists():
    source_path = str(system_config)  # RPM installation
else:
    source_path = str(self.default_config_file)  # PyPI installation
```

This ensures:
- ✅ PyPI installations work without system config
- ✅ RPM installations prefer system config
- ✅ Both use same config format and structure
- ✅ User configs are portable between installation methods

## Building for PyPI

### Prerequisites

```bash
# Install build tools
pip install build twine

# Optional: Install development dependencies
pip install -e .[dev]
```

### Build Process

```bash
# Clean previous builds
make clean

# Build UI (compile XML files)
make ui-build

# Run linting
make lint

# Build PyPI package
make pypi-build

# This creates:
# - dist/d-fake-seeder-0.0.46.tar.gz (source distribution)
# - dist/d_fake_seeder-0.0.46-py3-none-any.whl (wheel)
```

### Validation

```bash
# Check package validity
make pypi-check

# Or manually:
twine check dist/*

# Verify package contents
tar -tzf dist/d-fake-seeder-0.0.46.tar.gz
unzip -l dist/d_fake_seeder-0.0.46-py3-none-any.whl
```

### Testing PyPI Upload

```bash
# Upload to Test PyPI
make pypi-test-upload

# Test installation from Test PyPI
pip install --index-url https://test.pypi.org/simple/ d-fake-seeder
```

### Production Upload

```bash
# Upload to production PyPI
make pypi-upload

# Verify on PyPI
# https://pypi.org/project/d-fake-seeder/
```

## Desktop Integration

### PyPI Post-Install Script

After `pip install`, users can optionally install desktop integration:

```bash
# Install desktop files and icons
dfs-install-desktop

# Uninstall desktop integration
dfs-uninstall-desktop
```

This script (`d_fake_seeder/post_install.py`):
1. Copies desktop file to `~/.local/share/applications/`
2. Installs icons to `~/.local/share/icons/hicolor/`
3. Updates icon cache: `gtk-update-icon-cache`
4. Updates desktop database: `update-desktop-database`

### RPM Post-Install Script

RPM automatically runs desktop integration during `%post`:
- System-wide icons in `/usr/share/icons/`
- User icons copied to `~/.local/share/icons/` (if sudo used)
- Desktop file in `/usr/share/applications/`
- No user action required

## Entry Points

### PyPI Console Scripts

Defined in `setup.py`:

```python
entry_points = {
    "console_scripts": [
        "dfs = d_fake_seeder.dfakeseeder:app",
        "dfakeseeder = d_fake_seeder.dfakeseeder:app",
        "dfs-tray = d_fake_seeder.dfakeseeder_tray:main",
        "dfs-install-desktop = d_fake_seeder.post_install:install_desktop_integration",
        "dfs-uninstall-desktop = d_fake_seeder.post_install:uninstall_desktop_integration",
    ]
}
```

After PyPI installation:
- `dfs` - Launch main application
- `dfakeseeder` - Launch main application (alias)
- `dfs-tray` - Launch tray application
- `dfs-install-desktop` - Install desktop integration
- `dfs-uninstall-desktop` - Remove desktop integration

### RPM Wrapper Script

RPM provides `/usr/bin/dfakeseeder`:
- `dfakeseeder` - Launch main application
- `dfakeseeder --with-tray` - Launch with tray
- `dfakeseeder --tray-only` - Launch tray only

## Desktop File Differences

### PyPI Desktop File

Path: `d_fake_seeder/dfakeseeder.desktop`

```desktop
[Desktop Entry]
Exec=/usr/bin/dfakeseeder
Icon=dfakeseeder
Actions=with-tray;tray-only;

[Desktop Action with-tray]
Exec=/usr/bin/dfakeseeder --with-tray

[Desktop Action tray-only]
Exec=/usr/bin/dfakeseeder --tray-only
```

After `dfs-install-desktop`:
- Exec paths adjusted for PyPI installation
- Icons installed to user directories
- Desktop file in `~/.local/share/applications/`

### RPM Desktop File

Same source file, modified during RPM build:
- Exec paths use `/usr/bin/dfakeseeder` wrapper
- System-wide icons in `/usr/share/icons/`
- Desktop file in `/usr/share/applications/`

## Compatibility Testing

### Test PyPI Installation

```bash
# Create test environment
python3 -m venv test-venv
source test-venv/bin/activate

# Install system dependencies (outside venv)
sudo dnf install python3-gobject gtk4

# Install from PyPI
pip install d-fake-seeder

# Test entry points
dfs --help
dfs-tray
dfs-install-desktop

# Test application launch
dfs

# Cleanup
deactivate
rm -rf test-venv
```

### Test RPM Installation

```bash
# Build RPM
make rpm

# Install RPM
make rpm-install

# Test launch methods
dfakeseeder --help
dfakeseeder --with-tray
gtk-launch dfakeseeder

# Check files
rpm -ql dfakeseeder
rpm -qi dfakeseeder

# Cleanup
sudo dnf remove dfakeseeder
```

## Common Issues

### Missing GTK4 Dependencies

**Problem**: `ModuleNotFoundError: No module named 'gi'`

**Solution**: Install system GTK4 packages:
```bash
# Fedora
sudo dnf install python3-gobject gtk4

# Ubuntu
sudo apt install python3-gi gir1.2-gtk-4.0
```

### Desktop File Not Showing

**Problem**: Application not in menu after PyPI install

**Solution**: Run desktop integration:
```bash
dfs-install-desktop
```

### Config Not Found

**Problem**: Application creates fresh config every run

**Solution**: Check config permissions:
```bash
ls -la ~/.config/dfakeseeder/
chmod 644 ~/.config/dfakeseeder/settings.json
```

### Icons Not Showing

**Problem**: Default icon in application menu

**Solution**: Update icon cache:
```bash
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor/
# Restart desktop environment or logout/login
```

## Version Management

When updating the version:

1. **Update version in all files**:
   - `setup.py` → `version = "0.0.47"`
   - `dfakeseeder.spec` → `Version: 0.0.47`
   - `control` → `Version: 0.0.47`

2. **Update changelog**:
   - `dfakeseeder.spec` → `%changelog` section
   - GitHub releases

3. **Rebuild packages**:
   ```bash
   make pypi-build
   make rpm
   make deb
   ```

4. **Test both distributions**:
   - PyPI: `pip install --upgrade d-fake-seeder`
   - RPM: `sudo dnf upgrade dfakeseeder`

## Best Practices

### For PyPI Releases

1. ✅ Always run `make ui-build` before building
2. ✅ Test in clean virtualenv
3. ✅ Upload to TestPyPI first
4. ✅ Verify package contents with `twine check`
5. ✅ Test desktop integration separately
6. ✅ Include all locale files
7. ✅ Document system dependencies in README

### For RPM Compatibility

1. ✅ Keep config format identical
2. ✅ Use same file structure in `d_fake_seeder/`
3. ✅ Exclude RPM-specific files from PyPI via `MANIFEST.in`
4. ✅ Test config fallback logic (system → package → user)
5. ✅ Ensure desktop file works in both contexts
6. ✅ Maintain separate wrapper script for RPM only

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Publishing](https://pypi.org/help/)
- [setuptools Documentation](https://setuptools.pypa.io/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [XDG Base Directory Spec](https://specifications.freedesktop.org/basedir-spec/)

## Support

For PyPI packaging issues:
- GitHub Issues: https://github.com/dmzoneill/DFakeSeeder/issues
- PyPI Project: https://pypi.org/project/d-fake-seeder/
- Check build logs: `make pypi-build`
