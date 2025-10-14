<!-- markdownlint-disable MD041 -->
![DFakeSeeder screenshot](https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/components/images/dfakeseeder.png)

# D' Fake Seeder

A sophisticated Python GTK4 BitTorrent client that simulates seeding activity with advanced peer-to-peer networking capabilities, comprehensive settings management, and multi-language support.

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

![DFakeSeeder screenshot](https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/components/images/screenshot.png)

## Installation & Usage

### PyPI Installation (Recommended)
```bash
# Install system dependencies first
# Fedora/RHEL
sudo dnf install gtk4 python3-gobject

# Debian/Ubuntu
sudo apt install gir1.2-gtk-4.0 python3-gi

# Install from PyPI
pip install d-fake-seeder

# Install desktop integration (icons, desktop file, tray autostart)
dfs-install-desktop

# GNOME Shell users: Restart GNOME Shell for immediate recognition
# Press Alt+F2, type 'r', and press Enter

# Run the application
dfs                    # Short command
dfakeseeder           # Full command
dfs-tray              # Tray application only

# Launch from application menu
gtk-launch dfakeseeder
# Or search "D' Fake Seeder" in application menu
```

### Development Setup
```bash
# Setup pipenv environment
make setup-venv

# Run with debug output (pipenv)
make run-debug-venv

# Run with Docker
make run-debug-docker
```

### Package Installations

#### Debian/Ubuntu
```bash
# Download and install
curl -sL $(curl -s https://api.github.com/repos/dmzoneill/dfakeseeder/releases/latest | grep browser_download_url | cut -d\" -f4 | grep deb) -o dfakeseeder.deb
sudo dpkg -i dfakeseeder.deb

# Desktop integration is automatic (icons, desktop file, cache updates)
# GNOME Shell users: Press Alt+F2, type 'r', and press Enter to restart GNOME Shell

# Launch
gtk-launch dfakeseeder
```

#### RHEL/Fedora
```bash
# Download and install
curl -sL $(curl -s https://api.github.com/repos/dmzoneill/dfakeseeder/releases/latest | grep browser_download_url | cut -d\" -f4 | grep rpm) -o dfakeseeder.rpm
sudo rpm -i dfakeseeder.rpm

# Desktop integration is automatic (icons, desktop file, cache updates)
# GNOME Shell users: Press Alt+F2, type 'r', and press Enter to restart GNOME Shell

# Launch
gtk-launch dfakeseeder
```

#### Docker
```bash
# Local build
make docker

# Docker Hub/GHCR
xhost +local:
docker run --rm --net=host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" --volume="/tmp/.X11-unix:/tmp/.X11-unix" -it ghcr.io/dmzoneill/dfakeseeder
```

## Development

### Code Quality
- **Code Quality**: Black, flake8, and isort formatting standards (max-line-length: 120)
- **Testing**: Pytest framework with comprehensive test coverage
- **Performance**: Automatic timing and structured logging throughout
- **Dependency Management**: Pipfile/Pipfile.lock (primary), setup.py for PyPI publishing

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
```

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

# This installs:
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
```

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

## Links
- **GitHub**: https://github.com/dmzoneill/DFakeSeeder
- **Issues**: https://github.com/dmzoneill/DFakeSeeder/issues
- **PyPI**: https://pypi.org/project/d-fake-seeder/