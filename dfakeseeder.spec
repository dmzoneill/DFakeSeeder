Name:           dfakeseeder
Version:        0.0.47
Release:        1%{?dist}
Summary:        BitTorrent seeding simulator for testing and development

License:        MIT
URL:            https://github.com/dmzoneill/DFakeSeeder
Source0:        %{name}-%{version}.tar.gz

BuildArch:      noarch

# Python and GTK dependencies
Requires:       python3 >= 3.11
Requires:       python3-pip
Requires:       gtk4
Requires:       libadwaita
Requires:       python3-gobject

# Python package dependencies from Pipfile
Requires:       python3-requests >= 2.31.0
Requires:       python3-urllib3 >= 1.26.18
Requires:       python3-watchdog

# Note: bencodepy not available as RPM, installed via pip in %post

# System utilities
Requires:       gtk-update-icon-cache
Requires:       desktop-file-utils

%description
D' Fake Seeder is a BitTorrent seeding simulator designed for testing and
development purposes. It simulates torrent seeding activity with support for
both HTTP and UDP tracker protocols, comprehensive peer-to-peer networking,
and full internationalization (i18n) support for 15 languages.

Features:
- HTTP and UDP tracker protocol support
- Peer-to-peer networking with BitTorrent protocol implementation
- GTK4 modern user interface
- System tray integration
- Comprehensive settings management
- Multi-language support (15 languages)
- Seeding profiles (conservative, balanced, aggressive)

%prep
%setup -q

%build
# No build required for Python application

%install
# Create directory structure
install -d %{buildroot}/opt/dfakeseeder/
install -d %{buildroot}/etc/dfakeseeder/
install -d %{buildroot}/usr/bin/
install -d %{buildroot}/usr/share/applications/
install -d %{buildroot}/usr/share/icons/hicolor/16x16/apps/
install -d %{buildroot}/usr/share/icons/hicolor/32x32/apps/
install -d %{buildroot}/usr/share/icons/hicolor/48x48/apps/
install -d %{buildroot}/usr/share/icons/hicolor/64x64/apps/
install -d %{buildroot}/usr/share/icons/hicolor/96x96/apps/
install -d %{buildroot}/usr/share/icons/hicolor/128x128/apps/
install -d %{buildroot}/usr/share/icons/hicolor/192x192/apps/
install -d %{buildroot}/usr/share/icons/hicolor/256x256/apps/

# Install application files (maintain d_fake_seeder package structure)
cp -r d_fake_seeder %{buildroot}/opt/dfakeseeder/

# Install Pipfile and Pipfile.lock for pipenv
cp Pipfile %{buildroot}/opt/dfakeseeder/d_fake_seeder/
cp Pipfile.lock %{buildroot}/opt/dfakeseeder/d_fake_seeder/

# Install system-wide default configuration
install -m 0644 d_fake_seeder/config/rpm-default.json %{buildroot}/etc/dfakeseeder/default.json

# Install wrapper script
install -m 0755 packaging/dfakeseeder-wrapper.sh %{buildroot}/usr/bin/dfakeseeder

# Install desktop file
install -m 0644 d_fake_seeder/dfakeseeder.desktop %{buildroot}/usr/share/applications/dfakeseeder.desktop

# Fix desktop file to use wrapper script
sed -i 's#Exec=.*#Exec=/usr/bin/dfakeseeder#g' %{buildroot}/usr/share/applications/dfakeseeder.desktop
sed -i 's#Path=.*##g' %{buildroot}/usr/share/applications/dfakeseeder.desktop

# Add desktop actions for tray modes
cat >> %{buildroot}/usr/share/applications/dfakeseeder.desktop << 'EOF'
Actions=with-tray;tray-only;

[Desktop Action with-tray]
Name=Launch with System Tray
Exec=/usr/bin/dfakeseeder --with-tray
Icon=dfakeseeder

[Desktop Action tray-only]
Name=Launch Tray Only
Exec=/usr/bin/dfakeseeder --tray-only
Icon=dfakeseeder
EOF

# Install icons to system directories (all sizes)
for size in 16 32 48 64 96 128 192 256; do
    install -m 0644 d_fake_seeder/components/images/dfakeseeder.png \
        %{buildroot}/usr/share/icons/hicolor/${size}x${size}/apps/dfakeseeder.png
done

%files
%defattr(-,root,root,-)
%dir /opt/dfakeseeder
/opt/dfakeseeder/*
%dir /etc/dfakeseeder
%config(noreplace) /etc/dfakeseeder/default.json
/usr/bin/dfakeseeder
/usr/share/applications/dfakeseeder.desktop
/usr/share/icons/hicolor/*/apps/dfakeseeder.png

%post
# Install Python packages not available as RPM in Fedora
pip3 install --no-cache-dir bencodepy typer==0.12.3 2>/dev/null || :

# Update icon cache for system-wide icons
gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || :

# Update desktop database
update-desktop-database -q /usr/share/applications 2>/dev/null || :

# Install icons to user directories for current user (if running as user)
if [ -n "$SUDO_USER" ]; then
    # Get the actual user's home directory
    USER_HOME=$(getent passwd "$SUDO_USER" | cut -d: -f6)

    for size in 16 32 48 64 96 128 192 256; do
        mkdir -p "$USER_HOME/.local/share/icons/hicolor/${size}x${size}/apps" 2>/dev/null || :
        cp -f /usr/share/icons/hicolor/${size}x${size}/apps/dfakeseeder.png \
            "$USER_HOME/.local/share/icons/hicolor/${size}x${size}/apps/" 2>/dev/null || :
        chown -R "$SUDO_USER:" "$USER_HOME/.local/share/icons/" 2>/dev/null || :
    done

    # Update user icon cache
    if [ -d "$USER_HOME/.local/share/icons/hicolor" ]; then
        su - "$SUDO_USER" -c "gtk-update-icon-cache -q -t -f $USER_HOME/.local/share/icons/hicolor" 2>/dev/null || :
    fi

    # Clear GNOME Shell cache for immediate recognition
    rm -rf "$USER_HOME/.cache/gnome-shell/" 2>/dev/null || :
fi

echo ""
echo "=========================================="
echo "D' Fake Seeder installed successfully!"
echo "=========================================="
echo ""
echo "Launch options:"
echo "  1. Application menu: Search for 'D' Fake Seeder'"
echo "  2. Command line: dfakeseeder"
echo "  3. With tray:    dfakeseeder --with-tray"
echo "  4. Desktop file: gtk-launch dfakeseeder"
echo ""
echo "Configuration will be created at:"
echo "  ~/.config/dfakeseeder/settings.json"
echo ""
echo "System default config installed at:"
echo "  /etc/dfakeseeder/default.json"
echo ""
echo "GNOME users: Press Alt+F2, type 'r', and press Enter to restart GNOME Shell."
echo ""

%postun
# Clean up icon cache on uninstall
if [ $1 -eq 0 ]; then
    gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor 2>/dev/null || :
    update-desktop-database -q /usr/share/applications 2>/dev/null || :
fi

%changelog
* Wed Nov 27 2024 David O Neill <dmz.oneill@gmail.com> - 0.0.47-1
- Comprehensive RPM packaging with system-wide config
- Added wrapper script for CLI and tray support
- System-wide icon installation with user fallback
- Full dependency specification from Pipfile
- Desktop integration with .desktop file
- First run config initialization from /etc/dfakeseeder/default.json
