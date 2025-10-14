Name: DFakeSeeder
Version:    0.0.44
Release:    1%{?dist}
Summary:    BitTorrent seeding simulator for testing and development

License:    MIT
URL:        https://github.com/dmzoneill/DFakeSeeder

Source0:    %{name}-%{version}.tar.gz

BuildArch:  noarch
Requires:   python3 >= 3.11
Requires:   gtk4
Requires:   python3-gobject

%description
D' Fake Seeder is a BitTorrent seeding simulator designed for testing and
development purposes. It simulates torrent seeding activity with support for
both HTTP and UDP tracker protocols, comprehensive peer-to-peer networking,
and full internationalization (i18n) support for 21 languages.

%prep

%install
# Install application files
install -d %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/config %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/images %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/lib %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/ui %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/locale %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/domain %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/components %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/dfakeseeder.py %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/dfakeseeder_tray.py %{buildroot}/opt/dfakeseeder/

# Install desktop file
mkdir -vp %{buildroot}/usr/share/applications/
cp ../SOURCE/dfakeseeder.desktop %{buildroot}/usr/share/applications/
# Fix desktop file paths for installed location
sed -i 's#Exec=env LOG_LEVEL=DEBUG /usr/bin/python3 dfakeseeder.py#Exec=/usr/bin/python3 /opt/dfakeseeder/dfakeseeder.py#g' %{buildroot}/usr/share/applications/dfakeseeder.desktop
sed -i 's#Path=.*##g' %{buildroot}/usr/share/applications/dfakeseeder.desktop

%files
%defattr(-,root,root,-)
/opt/dfakeseeder/*
/usr/share/applications/dfakeseeder.desktop

%post
# Install icons to user directories
for X in 16 32 48 64 96 128 192 256; do
  mkdir -vp $HOME/.icons/hicolor/${X}x${X}/apps
  mkdir -vp $HOME/.local/share/icons/hicolor/${X}x${X}/apps
  cp -f /opt/dfakeseeder/images/dfakeseeder.png $HOME/.local/share/icons/hicolor/${X}x${X}/apps/ 2>/dev/null || true
  cp -f /opt/dfakeseeder/images/dfakeseeder.png $HOME/.icons/hicolor/${X}x${X}/apps/ 2>/dev/null || true
done

# Update icon caches
if [ -d $HOME/.local/share/icons/hicolor ]; then
  cd $HOME/.local/share/icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true
fi
if [ -d $HOME/.icons/hicolor ]; then
  cd $HOME/.icons/ && gtk-update-icon-cache -t -f hicolor 2>/dev/null || true
fi

# Update desktop database
update-desktop-database $HOME/.local/share/applications/ 2>/dev/null || true

# Clear GNOME Shell cache for immediate recognition
rm -rf $HOME/.cache/gnome-shell/ 2>/dev/null || true

echo "Desktop integration installed. GNOME users: Press Alt+F2, type 'r', and press Enter to restart GNOME Shell."
