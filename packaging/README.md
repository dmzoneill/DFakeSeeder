# DFakeSeeder RPM Packaging

This directory contains files and documentation for building RPM packages of DFakeSeeder.

## Quick Start

Build and install the RPM package:

```bash
# Build RPM (includes ui-build and lint automatically)
make rpm

# Install the built RPM
make rpm-install

# Or install manually
sudo dnf install ./rpmbuild/RPMS/noarch/dfakeseeder-*.rpm
```

## Package Structure

### Installed Files

After installation, the RPM creates the following structure:

```
/opt/dfakeseeder/              # Main application directory
├── config/                    # Application config templates
├── components/                # UI components and images
├── lib/                       # Core libraries
├── domain/                    # Domain logic
├── locale/                    # Translations (15 languages)
├── dfakeseeder.py            # Main application
└── dfakeseeder_tray.py       # Tray application

/etc/dfakeseeder/              # System-wide configuration
└── default.json              # Clean default config (no user data)

/usr/bin/
└── dfakeseeder               # Wrapper script (CLI entry point)

/usr/share/applications/
└── dfakeseeder.desktop       # Desktop integration

/usr/share/icons/hicolor/*/apps/
└── dfakeseeder.png           # Icons (all sizes: 16-256px)
```

### User Configuration

On first run, the application:
1. Checks for system config: `/etc/dfakeseeder/default.json`
2. Creates user config directory: `~/.config/dfakeseeder/`
3. Copies system config to: `~/.config/dfakeseeder/settings.json`
4. Creates torrents directory: `~/.config/dfakeseeder/torrents/`

## Launch Methods

### 1. Command Line

```bash
# Launch main application
dfakeseeder

# Launch with system tray
dfakeseeder --with-tray

# Launch tray only (main window hidden)
dfakeseeder --tray-only

# Show help
dfakeseeder --help

# Show version
dfakeseeder --version
```

### 2. Desktop Environment

**From Application Menu:**
- Search for "D' Fake Seeder" in your application launcher
- Right-click for launch options:
  - Launch with System Tray
  - Launch Tray Only

**From Command Line:**
```bash
gtk-launch dfakeseeder
```

## Configuration

### System Default Config

The RPM installs a clean default configuration at `/etc/dfakeseeder/default.json`:
- No user-specific data (empty torrents, reset window positions)
- Sane defaults for all settings
- `window_pos_x` and `window_pos_y` set to `-1` (auto-position)
- Empty `watch_folder.path`
- Default seeding profile: "balanced"

### User Config

User settings are stored at `~/.config/dfakeseeder/settings.json`:
- Created automatically on first run from system defaults
- User modifications persist across updates
- Torrent data stored in `~/.config/dfakeseeder/torrents/`

### Environment Variables

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=DEBUG dfakeseeder

# Override application path
DFS_PATH=/custom/path dfakeseeder

# Custom Python interpreter
PYTHON=/usr/bin/python3.12 dfakeseeder
```

## Build System

### Makefile Target

The `make rpm` target performs:
1. **UI Build**: Compiles XML UI files with XInclude
2. **Lint**: Runs black, flake8, isort for code quality
3. **Clean**: Removes old rpmbuild directory
4. **Create Tarball**: Packages source with proper structure
5. **RPM Build**: Builds binary and source RPMs
6. **Architecture**: Includes architecture in filename (e.g., `.fc43.noarch.rpm`)

### Build Dependencies

Automatically installed by `make rpm`:
- `rpm-build`: RPM packaging tools
- `rpmlint`: RPM linting and validation
- `python3-setuptools`: Python packaging utilities

### Manual Build

```bash
# Ensure UI is built
make ui-build

# Run linting
make lint

# Build RPM manually
rpmbuild --define "_topdir $(pwd)/rpmbuild" -ba dfakeseeder.spec
```

## Package Contents

### Wrapper Script (`packaging/dfakeseeder-wrapper.sh`)

The wrapper script provides:
- CLI interface with `--with-tray` and `--tray-only` options
- Environment variable support (LOG_LEVEL, DFS_PATH)
- Help and version commands
- Proper PYTHONPATH and working directory setup
- Tray application coordination

### Desktop File (`d_fake_seeder/dfakeseeder.desktop`)

Enhanced desktop integration:
- Main application launcher
- Desktop actions for tray modes
- Icon theming support
- Proper WM_CLASS for window management
- Categories: Network, P2P

### RPM Spec (`dfakeseeder.spec`)

The spec file includes:
- Full dependency specification from Pipfile
- System-wide and user icon installation
- GTK icon cache updates
- Desktop database updates
- Post-install information display
- Proper file permissions and ownership

## Dependencies

### Runtime Requirements

**Python Packages** (from Pipfile):
- python3-requests >= 2.31.0
- python3-urllib3 >= 1.26.18
- python3-watchdog
- python3-bencodepy

**System Libraries**:
- python3 >= 3.11
- gtk4
- python3-gobject
- gtk-update-icon-cache
- desktop-file-utils

### Optional Dependencies

- `rpmlint`: For package validation
- `dnf`/`yum`: For installation

## Testing

### Build Test

```bash
# Test build process
make rpm

# Verify RPM contents
rpm -qlp ./rpmbuild/RPMS/noarch/dfakeseeder-*.rpm

# Check package info
rpm -qip ./rpmbuild/RPMS/noarch/dfakeseeder-*.rpm

# Validate with rpmlint
rpmlint ./rpmbuild/RPMS/noarch/dfakeseeder-*.rpm
```

### Installation Test

```bash
# Install in test environment
make rpm-install

# Verify installation
rpm -q dfakeseeder

# Test launch
dfakeseeder --help

# Test desktop integration
gtk-launch dfakeseeder
```

### Uninstallation Test

```bash
# Remove package
sudo dnf remove dfakeseeder

# Verify cleanup
rpm -q dfakeseeder  # Should report "not installed"
```

## Build Artifacts

### Build Directory Structure

```
rpmbuild/
├── BUILD/              # Unpacked sources during build
├── BUILDROOT/          # Installed files before packaging
├── RPMS/
│   └── noarch/        # Built binary RPM
│       └── dfakeseeder-0.0.46-1.fc43.noarch.rpm
├── SOURCES/           # Source tarball
│   └── dfakeseeder-0.0.46.tar.gz
├── SPECS/             # Spec file copy
│   └── dfakeseeder.spec
└── SRPMS/             # Source RPM
    └── dfakeseeder-0.0.46-1.fc43.src.rpm
```

### .gitignore

The `rpmbuild/` directory is already in `.gitignore` to prevent committing build artifacts.

## Distribution

### Local Installation

```bash
# Install on local system
sudo dnf install ./rpmbuild/RPMS/noarch/dfakeseeder-*.rpm
```

### Repository Distribution

```bash
# Copy to repository
cp ./rpmbuild/RPMS/noarch/dfakeseeder-*.rpm /path/to/repo/

# Update repository metadata
createrepo /path/to/repo/
```

### COPR (Fedora Build System)

```bash
# Upload source RPM to COPR
copr-cli build your-project ./rpmbuild/SRPMS/dfakeseeder-*.src.rpm
```

## Troubleshooting

### Build Failures

**Missing dependencies:**
```bash
sudo dnf install rpm-build rpmlint python3-setuptools
```

**Permission errors:**
```bash
# Don't run rpmbuild as root
# Build in user directory (current method)
```

**Tarball errors:**
```bash
# Ensure proper directory structure
ls -la rpmbuild/dfakeseeder-0.0.46/d_fake_seeder/
```

### Installation Issues

**Dependency conflicts:**
```bash
# Check missing dependencies
sudo dnf install --allowerasing dfakeseeder-*.rpm

# Or use RPM directly
sudo rpm -ivh --nodeps dfakeseeder-*.rpm  # Not recommended
```

**Icon not showing:**
```bash
# Update icon cache
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor/
sudo gtk-update-icon-cache -f -t /usr/share/icons/hicolor/

# Restart GNOME Shell (GNOME users)
# Press Alt+F2, type 'r', press Enter
```

**Desktop file not appearing:**
```bash
# Update desktop database
update-desktop-database ~/.local/share/applications/
sudo update-desktop-database /usr/share/applications/
```

## Maintenance

### Version Updates

1. Update version in:
   - `setup.py`: `version` field
   - `dfakeseeder.spec`: `Version` field
   - `control`: `Version` field (for Debian)

2. Update changelog in `dfakeseeder.spec`:
   ```spec
   %changelog
   * Wed Nov 27 2024 David O Neill <dmz.oneill@gmail.com> - 0.0.47-1
   - New feature description
   - Bug fixes
   ```

3. Rebuild package:
   ```bash
   make rpm
   ```

### Configuration Updates

To update system default config:
1. Edit `d_fake_seeder/config/rpm-default.json`
2. Rebuild RPM: `make rpm`
3. Users get new defaults on fresh install
4. Existing users: config marked `%config(noreplace)` preserves user settings

## References

- [RPM Packaging Guide](https://rpm-packaging-guide.github.io/)
- [Fedora Packaging Guidelines](https://docs.fedoraproject.org/en-US/packaging-guidelines/)
- [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/)
- [Icon Theme Specification](https://specifications.freedesktop.org/icon-theme-spec/)

## Support

For issues with RPM packaging:
- GitHub Issues: https://github.com/dmzoneill/DFakeSeeder/issues
- Check logs: `journalctl -xe` (post-install script errors)
- Validate package: `rpmlint dfakeseeder-*.rpm`
