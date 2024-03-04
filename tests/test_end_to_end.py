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


@pytest.mark.parametrize("arguments", [
    (["-lq", "common"]),
    (["-lq", "bucket"]),
    (["-lq", "sns"]),
],
ids = [
    "common_queries",
    "s3_queries",
    "sns_queries",
]
)
def test_end_to_end(capsys, read_cli_args, arguments: list) -> None:
    """Test data perimeter helper from end-to-end"""
    logger.info("CLI arguments: %s", read_cli_args)
    arguments.extend(
        [
            "-v",
            "-la", read_cli_args["list_account"],
            "-vf", read_cli_args["variable_file"],
            "-dphf", read_cli_args["dph_conf_file"],
        ]
    )
    logger.info("All arguments: %s", arguments)
    res = main(arguments)
    assert res == 0
