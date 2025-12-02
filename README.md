<!-- markdownlint-disable MD041 -->
![DFakeSeeder screenshot](<<https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/components/images/dfakeseeder.png>>)

# D' Fake Seeder

[![RPM E2E Tests](<<https://github.com/dmzoneill/DFakeSeeder/workflows/RPM%20End-to-End%20Tests/badge.svg>>)](<<https://github.com/dmzoneill/DFakeSeeder/actions/workflows/rpm-e2e-tests.yml>>)
[![PyPI E2E Tests](<<https://github.com/dmzoneill/DFakeSeeder/workflows/PyPI%20End-to-End%20Tests/badge.svg>>)](<<https://github.com/dmzoneill/DFakeSeeder/actions/workflows/pypi-e2e-tests.yml>>)
[![DEB E2E Tests](<<https://github.com/dmzoneill/DFakeSeeder/workflows/DEB%20End-to-End%20Tests/badge.svg>>)](<<https://github.com/dmzoneill/DFakeSeeder/actions/workflows/deb-e2e-tests.yml>>)

A sophisticated Python GTK4 BitTorrent client that simulates seeding activity with advanced peer-to-peer networking capabilities, comprehensive settings management, multi-language support, and extensive automated testing.

## About the Name

The name "D' Fake Seeder" is a playful nod to the Irish English accent. In Irish pronunciation, the "th" sound in "the" is often rendered as a hard "d" sound - so "the" becomes "de" or "d'". This linguistic quirk gives us "D' Fake Seeder" instead of "The Fake Seeder", celebrating the project's Irish heritage while describing exactly what it does: simulates (fakes) torrent seeding activity.

## Features

### Core Functionality
- **Multi-Torrent Support**: Handle multiple torrents simultaneously with individual configuration
- **Protocol Support**: Full HTTP and UDP tracker compatibility with BitTorrent protocol (BEP-003)
- **Peer-to-Peer Networking**: Advanced P2P implementation with incoming/outgoing connection management
- **Real-time Monitoring**: Live connection tracking and performance metrics

### Advanced Features
- **System Tray Integration**: Full tray application with D-Bus IPC for seamless desktop integration
- **Internationalization**: 21 languages supported with runtime language switching
- **Desktop Integration**: XDG-compliant with proper icon themes, desktop files, and GNOME Shell support
- **Settings Management**: Comprehensive configuration with validation, profiles, and D-Bus sync
- **Performance Tracking**: Built-in automatic timing and performance monitoring

### User Interface
- **GTK4 Modern UI**: Clean, responsive interface with modular component architecture
- **Multi-Tab Settings**: Organized configuration categories (General, Connection, Peer Protocol, Advanced)
- **Real-time Translation**: Dynamic language changes without application restart
- **Performance Tracking**: Built-in timing and performance monitoring

![DFakeSeeder screenshot](<<https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/components/images/screenshot.png>>)

## Installation & Usage

### PyPI Installation (Recommended)
```bash
# Install from PyPI
pip install d-fake-seeder

# Run automated setup (checks dependencies, offers desktop integration)
dfs-setup
# This will
#  - Check for required system packages (GTK4, LibAdwaita, PyGObject)
#  - Show OS-specific installation commands if dependencies are missing
#  - Offer to install desktop integration (icons, menu entries)
#  - Display launch instructions

# Or skip setup and install system dependencies manually
# Fedora/RHEL
sudo dnf install gtk4 libadwaita python3-gobject

# Debian/Ubuntu
sudo apt install gir1.2-gtk-4.0 libadwaita-1-0 gir1.2-adw-1 python3-gi

# Launch the application
dfs                    # Short command
dfakeseeder           # Full command
dfs --with-tray       # Launch with system tray
dfs-tray              # Tray application only

# Launch from application menu (after desktop integration)
gtk-launch dfakeseeder
# Or search "D' Fake Seeder" in application menu
```text
### Development Setup
```bash
# Setup pipenv environment
make setup-venv

# Run with debug output (pipenv)
make run-debug-venv

# Run with Docker
make run-debug-docker
```text
### Package Installations

#### Debian/Ubuntu (.deb)
```bash
# Download and install
curl -sL $(curl -s https://api.github.com/repos/dmzoneill/dfakeseeder/releases/latest | grep browser_download_url | cut -d\" -f4 | grep deb) -o dfakeseeder.deb
sudo dpkg -i dfakeseeder.deb

# Everything is automatic
#  - All dependencies installed (GTK4, LibAdwaita, Python packages)
#  - Desktop integration (icons, menu entries, cache updates)
#  - Command-line launchers: dfs, dfakeseeder

# Launch from command line
dfs                    # Short command
dfakeseeder           # Full command

# Or launch from application menu
gtk-launch dfakeseeder
# Search "D' Fake Seeder" in application menu

# GNOME Shell users: Press Alt+F2, type 'r', Enter to restart shell
```text
#### RHEL/Fedora (.rpm)
```bash
# Download and install
curl -sL $(curl -s https://api.github.com/repos/dmzoneill/dfakeseeder/releases/latest | grep browser_download_url | cut -d\" -f4 | grep rpm) -o dfakeseeder.rpm
sudo rpm -i dfakeseeder.rpm

# Everything is automatic
#  - All dependencies installed (GTK4, LibAdwaita, Python packages)
#  - Desktop integration (icons, menu entries, cache updates)
#  - Command-line launchers: dfs, dfakeseeder

# Launch from command line
dfs                    # Short command
dfakeseeder           # Full command

# Or launch from application menu
gtk-launch dfakeseeder
# Search "D' Fake Seeder" in application menu

# GNOME Shell users: Press Alt+F2, type 'r', Enter to restart shell
```text
#### Docker
```bash
# Local build
make docker

# Docker Hub/GHCR
xhost +local:
docker run --rm --net=host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it ghcr.io/dmzoneill/dfakeseeder
```text
## Development

### Code Quality
- **Code Quality**: Black, flake8, and isort formatting standards (max-line-length: 120)
- **Testing**: Pytest framework with comprehensive unit and E2E test coverage
- **CI/CD**: GitHub Actions with automated E2E testing across 12 OS configurations
- **Performance**: Automatic timing and structured logging throughout
- **Dependency Management**: Pipfile/Pipfile.lock (primary), setup.py for PyPI publishing

### Testing Infrastructure

#### End-to-End Testing
Comprehensive E2E test suite with **140+ automated tests** across all package formats:

```bash
# Run all E2E tests (RPM, PyPI, DEB)
make test-e2e-all

# Run specific package format tests
make test-e2e          # RPM packages (Fedora)
make test-e2e-pypi     # PyPI packages (Fedora + Ubuntu)
make test-e2e-deb      # DEB packages (Ubuntu + Debian)
```text
**Coverage:**
- **RPM E2E**: Fedora latest, 42, 41 (50 tests per version)
- **PyPI E2E**: Fedora latest, 42, 41 + Ubuntu 22.04, 24.04 (43 tests per version)
- **DEB E2E**: Ubuntu 22.04, 24.04 + Debian 12, 11 (52 tests per version)

**Tests Include:**
- Package building and validation
- Installation and dependency resolution
- Desktop integration verification
- Application launch in headless environment
- Core component initialization
- Configuration file creation
- Wrapper script functionality
- Uninstallation cleanup

**GitHub Actions:**
All E2E tests run automatically on every push and PR with results visible in status checks.

### Build System
```bash
# Setup development environment
make setup-venv          # Create pipenv environment
make required            # Install dependencies

# Code quality
make lint                # Run black, flake8, isort
make test-venv           # Run tests with pipenv

# UI development
make ui-build            # Compile UI from XML components
make icons               # Install application icons

# Package building
make deb                 # Build Debian package (full desktop integration)
make rpm                 # Build RPM package (full desktop integration)
make flatpak             # Build Flatpak package
make docker              # Build Docker image

# PyPI publishing
make pypi-build          # Build source distribution and wheel
make pypi-check          # Validate package quality
make pypi-test-upload    # Upload to TestPyPI
make pypi-upload         # Upload to production PyPI

# E2E Testing
make test-e2e-all        # Run all E2E tests (RPM + PyPI + DEB)
make test-e2e            # RPM E2E tests
make test-e2e-pypi       # PyPI E2E tests
make test-e2e-deb        # DEB E2E tests
make clean-e2e-deb       # Clean DEB test artifacts
make clean-e2e-pypi      # Clean PyPI test artifacts
```text
### Package Format Feature Parity

All three package formats (RPM, DEB, PyPI) provide the same installation experience:

| Feature | RPM | DEB | PyPI |
| --------- | ----- | ----- | ------ |
| **Command-line launcher** | ✅ `dfs` / `dfakeseeder` | ✅ `dfs` / `dfakeseeder` | ✅ `dfs` / `dfakeseeder` |
| **Desktop integration** | ✅ Automatic | ✅ Automatic | ✅ via `dfs-setup` |
| **All dependencies** | ✅ Automatic | ✅ Automatic | ✅ Manual GTK4/LibAdwaita |
| **System tray** | ✅ Included | ✅ Included | ✅ Included |
| **Wrapper script** | ✅ `/usr/bin/dfakeseeder` | ✅ `/usr/bin/dfakeseeder` | ✅ Direct Python |
| **Auto-updates** | ✅ via dnf/yum | ✅ via apt | ✅ via pip |
| **E2E tested** | ✅ 3 Fedora versions | ✅ 4 Ubuntu/Debian versions | ✅ 5 OS versions |
```text
### Architecture
- **MVC Pattern**: Clean separation with Model, View, Controller
- **Component System**: Modular UI components with GTK4
- **Signal-Based**: GObject signals for loose coupling
- **D-Bus IPC**: Main app and tray communicate via D-Bus for seamless integration
- **Internationalization**: Runtime language switching with 21 languages
- **Performance**: Automatic timing and structured logging with class context

### Contributing
- All pull requests welcome
- Follow existing code style (black, flake8, isort)
- Include tests for new functionality
- Update documentation as needed


## Configuration

### File Locations
- **User Config**: `~/.config/dfakeseeder/settings.json` (auto-created from defaults)
- **Torrent Directory**: `~/.config/dfakeseeder/torrents/`
- **Default Config**: `d_fake_seeder/config/default.json` (comprehensive defaults)

### Settings Categories
- **Application**: Auto-start, themes, language preferences
- **Connection**: Network ports, proxy settings, connection limits
- **Peer Protocol**: Timeout settings, keep-alive intervals
- **BitTorrent**: DHT, PEX, announce intervals, user agents
- **Advanced**: Logging, performance tuning, debug options

### Desktop Integration
After PyPI installation, run desktop integration:
```bash
# Install desktop files, icons, and tray autostart
dfs-install-desktop

# This installs
# - Application icons (multiple sizes) to ~/.local/share/icons/
# - Desktop launcher to ~/.local/share/applications/
# - Updates icon and desktop caches
# - Clears GNOME Shell cache for immediate recognition

# GNOME Shell users: Restart GNOME Shell
# Press Alt+F2, type 'r', and press Enter

# Launch via desktop environment
gtk-launch dfakeseeder
# Or search "D' Fake Seeder" in application menu

# Uninstall desktop integration
dfs-uninstall-desktop
```text
### Supported Languages (21)
English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Swedish, Polish, Bengali, Persian, Irish, Indonesian, Turkish, Vietnamese

Runtime language switching without application restart.

### Example Configuration
The application auto-creates `~/.config/dfakeseeder/settings.json` with comprehensive defaults including:
- Speed limits and announce intervals
- Peer connection settings
- UI customization options
- Client identification strings
- Protocol timeouts and networking
- Internationalization preferences

## Documentation

- **[PyPI Installation Guide](docs/PYPI_INSTALLATION.md)** - Comprehensive PyPI installation and setup documentation
- **[GitHub Actions CI/CD](docs/GITHUB_ACTIONS.md)** - Complete guide to CI/CD workflows and E2E testing
- **[Packaging Guide](docs/PACKAGING.md)** - Documentation for all package formats (RPM, DEB, PyPI)
- **[Configuration Guide](docs/CONFIGURATION.md)** - Settings system documentation
- **[Localization Guide](docs/LOCALIZATION.md)** - Internationalization system documentation

## Links
- **GitHub**: <<https://github.com/dmzoneill/DFakeSeeder>>
- **Issues**: <<https://github.com/dmzoneill/DFakeSeeder/issues>>
- **PyPI**: https://pypi.org/project/d-fake-seeder/
- **Actions**: <<https://github.com/dmzoneill/DFakeSeeder/actions>>

## License

MIT License - See [LICENSE](LICENSE) file for details