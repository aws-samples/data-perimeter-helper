#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Setup file for setuptools
Install: pip install -e ./
Uninstall: pip uninstall data_perimeter_helper
"""
import os
import re
from setuptools import (
    setup,
    find_packages
)


package_name = "data_perimeter_helper"
package_folder = os.path.dirname(os.path.realpath(__file__))


# retrieve version
version_file_path = package_folder + '/' + package_name + '/' + '__init__.py'
if os.path.isfile(version_file_path):
    with open(version_file_path, encoding="utf-8") as f:
        version_file_content = f.read()
        __version__ = re.search(
            r'__version__\s*=\s*[\'"]([^\'"]*)[\'"]', version_file_content
        ).group(1)


# retrieve requirements.txt
package_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = package_folder + '/requirements.txt'
install_requires = []
if os.path.isfile(requirement_path):
    with open(requirement_path, encoding="utf-8") as f:
        install_requires = f.read().splitlines()


extras_require = {
    'test': ['pytest==8.2.0']
}


setup(
    name=package_name,
    version=__version__,
    description='Helper tool to build data perimeter controls',
    author='Achraf MOUSSADEK-KABDANI',
    license="MIT",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        'console_scripts': [
            f'data_perimeter_helper = {package_name}.main:main',
            f'dph = {package_name}.main:main',
            f'dph_doc = {package_name}.toolbox.dph_doc:main'
        ]
    },
    packages=find_packages()
)
