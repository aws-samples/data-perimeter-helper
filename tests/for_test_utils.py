#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts all shared function between tests
"""
import os.path


def file_exists(path: str) -> bool:
    """ Returns True if the path exists, False otherwise """
    return os.path.isfile(path)
