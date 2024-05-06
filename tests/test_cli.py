#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts end-to-end test function
"""
import context
import pytest
import logging
from data_perimeter_helper.main import (
    main
)


logger = logging.getLogger(__name__)


def test_cli_no_query(capsys, read_cli_args) -> None:
    """Test data perimeter helper CLI"""
    logger.info("CLI arguments: %s", read_cli_args)
    arguments = [
        "-v",
        # "-lq", "s3_",
        "-la", read_cli_args["list_account"],
        "-vf", read_cli_args["variable_file"],
        "-dphf", read_cli_args["dph_conf_file"],
    ]
    logger.info("All arguments: %s", arguments)
    with pytest.raises(
        ValueError,
        match="--list-query/-lq must be defined"
    ):
        main(arguments)


def test_cli_no_account(capsys, read_cli_args) -> None:
    """Test data perimeter helper CLI"""
    logger.info("CLI arguments: %s", read_cli_args)
    arguments = [
        "-v",
        "-lq", "s3_",
        # "-la", read_cli_args["list_account"],
        "-vf", read_cli_args["variable_file"],
        "-dphf", read_cli_args["dph_conf_file"],
    ]
    logger.info("All arguments: %s", arguments)
    with pytest.raises(
        ValueError,
        match="--list-account/-la or --list-ou/-lo must be defined"
    ):
        main(arguments)
