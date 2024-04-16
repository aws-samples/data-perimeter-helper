#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Define the class ExternalAccessFindings"""
import logging
from typing import (
    Optional
)

from tqdm import tqdm

from data_perimeter_helper.variables import Variables as Var
from data_perimeter_helper.findings.ExternalAccessAnalyzer import (
    ExternalAccessAnalyzer
)
from data_perimeter_helper.findings.SecurityHub import (
    SecurityHub
)
from data_perimeter_helper.toolbox import utils


logger = logging.getLogger(__name__)


class ExternalAccessFindings():
    enabled = False

    def __init__(self) -> None:
        if ExternalAccessFindings.enabled is True:
            return
        if Var.external_access_findings == 'SECURITY_HUB':
            SecurityHub()
        elif Var.external_access_findings == 'IAM_ACCESS_ANALYZER':
            ExternalAccessAnalyzer()
        else:
            log_msg = "AWS IAM Access Analyzer external findings are not " \
                "retrieved. If you need to retrieve them, set " \
                "the variable `external_access_findings`."
            tqdm.write(
                utils.color_string(
                    utils.Icons.INFO + log_msg, utils.Colors.YELLOW
                )
            )
            return
        ExternalAccessFindings.enabled = True

    @classmethod
    def is_enabled(cls):
        return cls.enabled is True

    @classmethod
    def get_findings_as_df(
        cls,
        get_only_active: bool = True,
        account_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ):
        """Depending on the chosen data source retrieves AWS IAM Access
        Analyzer external access findings from IAM Access Analyzer or
        AWS SecurityHub"""
        if not cls.is_enabled():
            return
        if Var.external_access_findings == 'IAM_ACCESS_ANALYZER':
            return ExternalAccessAnalyzer.describe_findings_all_regions_as_df(
                get_only_active=get_only_active,
                account_id=account_id,
                resource_type=resource_type
            )
        if Var.external_access_findings == 'SECURITY_HUB':
            return SecurityHub.get_iam_aa_external_access_findings_as_df(
                account_id=account_id,
                resource_type=resource_type,
            )
