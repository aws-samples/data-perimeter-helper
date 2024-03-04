#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts functions to test if the helper CLI works for the python package
"""
import context
import pytest
from data_perimeter_helper.main import (
    main
)


@pytest.mark.parametrize("option", ("-h", "--help"))
def test_help(capsys, option):
    try:
        main([option])
    except SystemExit:
        pass
    output = capsys.readouterr().out
    assert "data perimeter helper" in output, "Package is not working as expected, package may not be correctly installed"
