Name: DFakeSeeder
Version:    0.0.36
Release:    1%{?dist}
Summary:    Deluge fake seeder

License:    GPL
URL:        https://github.com/dmzoneill/DFakeSeeder

Source0:    %{name}-%{version}.tar.gz

%description
D' Fake seeder, torrent fake seeding

%prep

%install
# Install files to desired locations
install -d %{buildroot}/opt/dfakeseeder/
cp -r ../SOURCE/* %{buildroot}/opt/dfakeseeder/
mkdir -vp %{buildroot}/usr/share/applications/
cp -r ../SOURCE/dfakeseeder.desktop %{buildroot}/usr/share/applications/

%files
%defattr(-,root,root,-)
/opt/dfakeseeder/*
/usr/share/applications/dfakeseeder.desktop

%post
# Copy files to desired locations
echo "All done"
