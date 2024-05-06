#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts end-to-end test function
"""
import logging
import shutil
from pathlib import (
    Path
)

import pytest


logger = logging.getLogger(__name__)


def pytest_addoption(parser):
    parser.addoption(
        "--list-account", action="store", dest="list_account"
    )
    parser.addoption(
        "--variable-file", action="store", dest="variable_file",
        default=None
    )
    parser.addoption(
        "--dph-conf-file", action="store", dest="dph_conf_file",
        default=None
    )


@pytest.fixture(scope='session')
def read_cli_args(request):
    logger.info("Argument passed to pytest: %s", request.config.option)
    return {
        "list_account": request.config.option.list_account,
        "variable_file": request.config.option.variable_file,
        "dph_conf_file": request.config.option.dph_conf_file,
    }


def delete_output_folder() -> None:
    """Delete the outputs folder if it exists"""
    try:
        shutil.rmtree(str(Path(__file__).absolute().parent / 'outputs'))
    except FileNotFoundError:
        pass


@pytest.fixture(scope='session')
def clean_outputs():
    """Called to delete the outputs folder if it exists then get the hand
    back to tests and attemps again to delete the outputs folder
    if it exists"""
    delete_output_folder()
    yield
    delete_output_folder()
