Name: DFakeSeeder
Version:    1.0
Release:    1%{?dist}
Summary:    Deluge fake seeder

License:    GPL
URL:        http://example.com

Source0:    %{name}-%{version}.tar.gz


%description
...

%prep
%autosetup

%build
python3 setup.py build

%install
python3 setup.py install --root=%{buildroot}

%files
%defattr(-,root,root,-)
%{python3_sitelib}/*

%changelog
...
