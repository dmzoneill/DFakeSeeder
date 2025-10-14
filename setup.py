# -*- coding: utf-8 -*-
from setuptools import find_packages, setup

# Read dependencies from Pipfile
# For PyPI publishing, we specify the core dependencies explicitly
install_requires = [
    "requests>=2.31.0",
    "typer>=0.12.3",
    "urllib3>=1.26.18",
    "PyGObject>=3.42.0",
    "watchdog>=4.0.0",
]

# Read long description from README
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Python GTK4 fake torrent seeder for testing and development"

packages = find_packages(include=["d_fake_seeder", "d_fake_seeder.*"])

package_data = {
    "d_fake_seeder": [
        "images/*",
        "ui/**/*",
        "config/*",
        "locale/**/*",
        "domain/config/*",
        "*.desktop",
        "*.desktop.template",
    ]
}

entry_points = {
    "console_scripts": [
        "dfs = d_fake_seeder.dfakeseeder:app",
        "dfakeseeder = d_fake_seeder.dfakeseeder:app",
        "dfs-tray = d_fake_seeder.dfakeseeder_tray:main",
        "dfs-install-desktop = d_fake_seeder.post_install:install_desktop_integration",
        "dfs-uninstall-desktop = d_fake_seeder.post_install:uninstall_desktop_integration",
    ]
}

setup_kwargs = {
    "name": "d-fake-seeder",
    "version": "0.0.45",
    "description": "BitTorrent seeding simulator for testing and development",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": "David O Neill",
    "author_email": "dmz.oneill@gmail.com",
    "url": "https://github.com/dmzoneill/DFakeSeeder",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "include_package_data": True,
    "python_requires": ">=3.11",
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Testing",
        "Topic :: Communications :: File Sharing",
    ],
    "keywords": "bittorrent torrent seeder testing development gtk4",
}


setup(**setup_kwargs)
