<!-- markdownlint-disable MD041 -->
![DFakeSeeder screenshot](https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/images/dfakeseeder.png)

# D' Fake Seeder

A sophisticated Python GTK4 BitTorrent client that simulates seeding activity with advanced peer-to-peer networking capabilities, comprehensive settings management, and multi-language support.

## Features

### Core Functionality
- **Multi-Torrent Support**: Handle multiple torrents simultaneously with individual configuration
- **Protocol Support**: Full HTTP and UDP tracker compatibility with BitTorrent protocol (BEP-003)
- **Peer-to-Peer Networking**: Advanced P2P implementation with incoming/outgoing connection management
- **Real-time Monitoring**: Live connection tracking and performance metrics

### Advanced Features
- **PyPy Compatibility**: Optimized for both CPython and PyPy interpreters
- **Type Safety**: Full MyPy type checking support with comprehensive type annotations
- **Internationalization**: 15 languages supported with runtime language switching
- **Desktop Integration**: XDG-compliant with proper icon themes and desktop files
- **Settings Management**: Comprehensive configuration with validation and profiles

### User Interface
- **GTK4 Modern UI**: Clean, responsive interface with modular component architecture
- **Multi-Tab Settings**: Organized configuration categories (General, Connection, Peer Protocol, Advanced)
- **Real-time Translation**: Dynamic language changes without application restart
- **Performance Tracking**: Built-in timing and performance monitoring

![DFakeSeeder screenshot](https://github.com/dmzoneill/dFakeSeeder/blob/main/d_fake_seeder/images/screenshot.png)

## Installation & Usage

### PyPI Installation (Recommended)
```bash
# Install from PyPI
pip install d-fake-seeder

# Install desktop integration (optional)
dfs-install-desktop

# Run the application
dfs                    # Short command
dfakeseeder           # Full command
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
curl -sL $(curl -s https://api.github.com/repos/dmzoneill/dfakeseeder/releases/latest | grep browser_download_url | cut -d\" -f4 | grep deb) -o dfakeseeder.deb
sudo dpkg -i dfakeseeder.deb
gtk-launch dfakeseeder
```

#### RHEL/Fedora
```bash
curl -sL $(curl -s https://api.github.com/repos/dmzoneill/dfakeseeder/releases/latest | grep browser_download_url | cut -d\" -f4 | grep rpm) -o dfakeseeder.rpm
sudo rpm -i dfakeseeder.rpm
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
- **PyPy Compatible**: Optimized for both CPython and PyPy interpreters
- **Type Safe**: Full MyPy type checking with comprehensive annotations
- **Code Quality**: Black, flake8, and isort formatting standards
- **Testing**: Pytest framework with comprehensive test coverage

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
make deb                 # Build Debian package
make rpm                 # Build RPM package
make flatpak            # Build Flatpak package
make docker             # Build Docker image
```

### Architecture
- **MVC Pattern**: Clean separation with Model, View, Controller
- **Component System**: Modular UI components with GTK4
- **Signal-Based**: GObject signals for loose coupling
- **Internationalization**: Runtime language switching with 15 languages
- **Performance**: Automatic timing and performance tracking

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
# Install desktop files and icons
dfs-install-desktop

# Launch via desktop environment
gtk-launch dfakeseeder
# Or search "D' Fake Seeder" in application menu

# Uninstall desktop integration
dfs-uninstall-desktop
```

### Supported Languages
English, Spanish, French, German, Italian, Portuguese, Russian, Chinese, Japanese, Korean, Arabic, Hindi, Dutch, Swedish, Polish

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