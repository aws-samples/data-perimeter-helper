#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
Used to add the package to sys path
PEP 366 - Main module explicit relative imports: https://peps.python.org/pep-0366/
"""
import sys
from pathlib import (
    Path
)
package_path = str(Path(__file__).absolute().parent.parent)
sys.path.append(package_path)
print(
    "\n[~] Execution outside package detected, below path has been added, "\
    f"sys.path += {package_path}"
)
