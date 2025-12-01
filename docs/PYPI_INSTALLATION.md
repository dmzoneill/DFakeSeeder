# PyPI Installation Guide

## Automated Installation Process

The PyPI installation of D' Fake Seeder now provides an automated setup experience similar to the RPM package installation.

## Installation

### Basic Installation

```bash
pip install d-fake-seeder
```

### What Happens After Installation

After `pip install` completes, you'll see an automated post-installation message:

```
============================================================
D' Fake Seeder - Installation Complete
============================================================

🎉 D' Fake Seeder has been installed successfully!

📋 NEXT STEPS:

1. Check system dependencies and setup:
   dfs-setup

   This will:
   • Check for required system packages (GTK4, LibAdwaita)
   • Offer to install desktop integration
   • Show launch instructions

2. Or skip setup and launch directly:
   dfs

============================================================

Would you like to run setup now? [Y/n]:
```

### Interactive Setup (Recommended)

If you're installing interactively (in a terminal), the installer will ask if you want to run setup immediately. Press Enter or type 'y' to run the automated setup.

The setup process will:

1. **Check System Dependencies**
   - Verifies GTK4 is installed
   - Verifies LibAdwaita is installed
   - Verifies PyGObject is available
   - Shows OS-specific installation commands if dependencies are missing

2. **Offer Desktop Integration**
   - Asks if you want to install desktop integration
   - Installs application icons to `~/.local/share/icons/hicolor/`
   - Installs desktop file to `~/.local/share/applications/`
   - Updates desktop and icon caches

3. **Show Launch Instructions**
   - Displays available launch methods
   - Shows configuration file locations

### Manual Setup

If you skip the automated setup or want to run it later:

```bash
dfs-setup
```

### Non-Interactive Installation

If installing via scripts or in non-interactive environments (like CI/CD), the post-installation message will be printed but won't prompt for input. You can run `dfs-setup` manually afterward.

## System Dependencies

### Required System Packages

Before installing D' Fake Seeder, ensure these system packages are installed:

**Fedora/RHEL:**
```bash
sudo dnf install gtk4 libadwaita python3-gobject
```

**Debian/Ubuntu:**
```bash
sudo apt install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1
```

**Arch Linux:**
```bash
sudo pacman -S gtk4 libadwaita python-gobject
```

### Verification

The `dfs-setup` command will automatically check for these dependencies and show OS-specific installation instructions if any are missing.

## Desktop Integration

### What's Included

Desktop integration provides:
- Application icon in system icon theme
- Desktop file for application menu integration
- Proper taskbar icon display
- Launch shortcuts via application menus
- System tray autostart (optional)

### Installation Commands

```bash
# Install desktop integration (done automatically via dfs-setup)
dfs-install-desktop

# Uninstall desktop integration
dfs-uninstall-desktop
```

### File Locations

After desktop integration:
- **Icons**: `~/.local/share/icons/hicolor/{size}/apps/dfakeseeder.png`
- **Desktop File**: `~/.local/share/applications/dfakeseeder.desktop`
- **Tray Autostart**: `~/.config/autostart/dfakeseeder-tray.desktop`
- **Application ID**: `ie.fio.dfakeseeder`

## Launch Methods

### Command Line

```bash
# Short command
dfs

# Full command
dfakeseeder

# With system tray
dfs --with-tray

# Tray only
dfs-tray
```

### Desktop Environment

```bash
# Via desktop launcher
gtk-launch dfakeseeder

# Or search "D' Fake Seeder" in application menu
```

### Help

```bash
dfs --help
```

## Configuration

### User Configuration

On first launch, D' Fake Seeder creates:

- **Config Directory**: `~/.config/dfakeseeder/`
- **Settings File**: `~/.config/dfakeseeder/settings.json`
- **Torrents Directory**: `~/.config/dfakeseeder/torrents/`

### Configuration Management

Settings can be managed through:
- The graphical settings dialog in the application
- Direct editing of `settings.json`
- Export/import via the settings dialog

## Comparison: PyPI vs RPM Installation

| Feature | PyPI Installation | RPM Installation |
|---------|------------------|------------------|
| **Package Management** | pip (user-level) | dnf/yum (system-level) |
| **Dependencies** | Python packages auto-installed | System packages via RPM |
| **Setup Process** | Interactive setup prompt | Automatic in %post script |
| **Desktop Integration** | Optional, via `dfs-setup` | Automatic during install |
| **System Dependencies** | Manual installation needed | Automatic via RPM deps |
| **Wrapper Script** | Not needed (direct Python) | Uses `/usr/bin/dfs` wrapper |
| **Installation Location** | `~/.local/` (user) | `/usr/share/` (system) |
| **Update Process** | `pip install --upgrade` | `dnf update` |
| **Uninstallation** | `pip uninstall d-fake-seeder` | `dnf remove dfakeseeder` |

## Troubleshooting

### Missing System Dependencies

If you see errors about missing GTK4 or LibAdwaita:

1. Run `dfs-setup` to check dependencies
2. Follow the OS-specific installation instructions
3. Install missing system packages
4. Try launching again

### Desktop Integration Not Working

If the application doesn't appear in your application menu:

1. Ensure desktop integration was installed: `ls ~/.local/share/applications/dfakeseeder.desktop`
2. Reinstall if needed: `dfs-install-desktop`
3. Update desktop database: `update-desktop-database ~/.local/share/applications/`
4. For GNOME Shell: Press Alt+F2, type 'r', press Enter to restart the shell

### Icon Not Showing

If icons aren't displaying:

1. Check icons are installed: `ls ~/.local/share/icons/hicolor/*/apps/dfakeseeder.png`
2. Update icon cache: `gtk-update-icon-cache ~/.local/share/icons/hicolor/`
3. Restart your desktop environment

## Development Installation

For development purposes:

```bash
# Clone repository
git clone https://github.com/dmzoneill/DFakeSeeder.git
cd DFakeSeeder

# Install in development mode
pip install -e .

# Or use pipenv for isolated environment
make setup-venv
make run-debug-venv
```

## Uninstallation

### Complete Uninstallation

```bash
# Remove desktop integration
dfs-uninstall-desktop

# Uninstall package
pip uninstall d-fake-seeder

# Optionally remove user configuration
rm -rf ~/.config/dfakeseeder/
```

## Support

For issues or questions:
- GitHub Issues: https://github.com/dmzoneill/DFakeSeeder/issues
- Documentation: See other docs in this directory

## See Also

- [PACKAGING.md](PACKAGING.md) - Packaging documentation for all formats
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration system documentation
- [LOCALIZATION.md](LOCALIZATION.md) - Internationalization system documentation
