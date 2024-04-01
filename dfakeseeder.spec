Name: DFakeSeeder
Version:    0.0.23
Release:    1%{?dist}
Summary:    Deluge fake seeder

License:    GPL
URL:        https://github.com/dmzoneill/DFakeSeeder

Source0:    %{name}-%{version}.tar.gz

%description
...

%prep
%setup -n %{name}-%{version}
# Optionally, apply any patches here if needed


%build
python3 setup.py build

%install
python3 setup.py install --root=%{buildroot}

%files
%defattr(-,root,root,-)
%{python3_sitelib}/*
%dir %{_datadir}/d_fake_seeder
%{_datadir}/d_fake_seeder/*