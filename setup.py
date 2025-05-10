# -*- coding: utf-8 -*-
from setuptools import setup

packages = ["d_fake_seeder"]

package_data = {"": ["*", "d_fake_seeder/*"]}

install_requires = ["requests"]

entry_points = {
    "console_scripts": [
        "dfs = d_fake_seeder.dfakeseeder:app",
    ]
}

setup_kwargs = {
    "name": "d-fake-seeder",
    "version": "0.0.41",
    "description": "Python gtk4 fake torrent seeder",
    "long_description": "",
    "author": "David O Neill",
    "author_email": "dmz.oneill@gmail.com",
    "maintainer": None,
    "maintainer_email": None,
    "url": "https://github.com/dmzoneill/DFakeSeeder",
    "packages": packages,
    "package_data": package_data,
    "install_requires": install_requires,
    "entry_points": entry_points,
    "include_package_data": True,
    "python_requires": ">=3.8,<4.0",
}


setup(**setup_kwargs)
