# -*- coding: utf-8 -*-
import sys

from setuptools import find_packages, setup
from setuptools.command.install import install

# Read dependencies from Pipfile
# For PyPI publishing, we specify the core dependencies explicitly
install_requires = [
    "requests>=2.31.0",
    "typer>=0.12.3",
    "urllib3>=1.26.18",
    "PyGObject>=3.42.0",
    "watchdog>=4.0.0",
    "bencodepy>=0.9.5",
    # Web UI server
    "aiohttp>=3.8.0",
    "aiohttp-session>=2.12.0",
    # UPnP port forwarding
    "miniupnpc>=2.2.0",
    # Protocol encryption (MSE/PE)
    "pycryptodome>=3.15.0",
    # Process monitoring
    "psutil>=5.9.0",
]

# Optional dependencies (kept for backwards compatibility with pip install d-fake-seeder[all])
extras_require = {
    "webui": [],  # Now included by default
    "upnp": [],  # Now included by default
    "encryption": [],  # Now included by default
    "all": [],  # All features now included by default
}

# Read long description from README
try:
    with open("README.md", "r", encoding="utf-8") as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "Python GTK4 fake torrent seeder for testing and development"

packages = find_packages(include=["d_fake_seeder", "d_fake_seeder.*"])

package_data = {
    "d_fake_seeder": [
        "components/images/*",
        "components/ui/**/*",
        "config/*",
        "locale/**/*",
        "domain/config/*",
        "desktop/*",
        "*.desktop",
        "*.desktop.template",
    ]
}

entry_points = {
    "console_scripts": [
        "dfs = d_fake_seeder.dfakeseeder:app",
        "dfakeseeder = d_fake_seeder.dfakeseeder:app",
        "dfs-tray = d_fake_seeder.dfakeseeder_tray:main",
        "dfs-setup = d_fake_seeder.setup_helper:post_install_setup",
        "dfs-install-desktop = d_fake_seeder.post_install:install_desktop_integration",
        "dfs-uninstall-desktop = d_fake_seeder.post_install:uninstall_desktop_integration",
    ]
}


class PostInstallCommand(install):
    """Custom install command to run post-installation setup automatically."""

    def run(self):
        # Run the standard install
        install.run(self)

        # Print post-installation instructions
        print("\n" + "=" * 60)
        print("D' Fake Seeder - Installation Complete")
        print("=" * 60)
        print("\n🎉 D' Fake Seeder has been installed successfully!")
        print("\n📋 NEXT STEPS:")
        print("\n1. Check system dependencies and setup:")
        print("   dfs-setup")
        print("\n   This will:")
        print("   • Check for required system packages (GTK4, LibAdwaita)")
        print("   • Offer to install desktop integration")
        print("   • Show launch instructions")
        print("\n2. Or skip setup and launch directly:")
        print("   dfs")
        print("\n" + "=" * 60 + "\n")

        # Try to run setup automatically if interactive
        if sys.stdin.isatty():
            try:
                response = input("Would you like to run setup now? [Y/n]: ").strip().lower()
                if response in ("", "y", "yes"):
                    print()
                    from d_fake_seeder.setup_helper import post_install_setup

                    post_install_setup()
            except (KeyboardInterrupt, EOFError):
                print("\n\nYou can run setup later with: dfs-setup\n")
        else:
            print("Run 'dfs-setup' to complete the installation.\n")


setup_kwargs = {
    "name": "d-fake-seeder",
    "version": "0.0.56",
    "description": "BitTorrent seeding simulator for testing and development",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": "David O Neill",
    "author_email": "dmz.oneill@gmail.com",
    "url": "https://github.com/dmzoneill/DFakeSeeder",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "extras_require": extras_require,
    "entry_points": entry_points,
    "cmdclass": {"install": PostInstallCommand},
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
