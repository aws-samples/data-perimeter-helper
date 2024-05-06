#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: findings_sh_external_access_org_boundary
'''
import logging
from typing import (
    Dict,
    Union,
)

import pandas

from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.findings.ExternalAccessFindings import (
    ExternalAccessFindings
)
from data_perimeter_helper.findings.SecurityHub import SecurityHub


logger = logging.getLogger(__name__)


class findings_sh_external_access_org_boundary(Query):
    """This query extracts all AWS SecurityHub findings tied to IAM Access Analyzer external access findings with the organization as zone of trust.
Note that (1) IAM Access Analyzer external access findings in error are not sent to SecurityHub and (2) IAM Access Analyzer external access findings in SecurityHub contains only one external principal even if the resource-based policy allows multiple principals.
You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your resources. You can use the global condition key [aws:PrincipalOrgId](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) to limit access to your resources to principals belonging to your AWS organization.
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        self.depends_on_resource_type = []
        super().__init__(
            name,
            self.depends_on_resource_type,
            depends_on_iam_access_analyzer=True,
            use_split_table=False
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Retrieve all AWS IAM Access Analyzer findings for an organization
        external access analyzer"""
        query = ""
        ExternalAccessFindings()
        if SecurityHub.is_enabled() is False:
            return {
                "query": query,
                "dataframe": pandas.DataFrame()
            }
        result = SecurityHub.get_iam_aa_external_access_findings_as_df(
        )
        if len(result.index) == 0:
            logger.debug("[~] No result retrieved - DataFrame is empty")
            return {
                "query": query,
                "dataframe": result
            }
        if Var.print_result:
            logger.info(result)
        return {
            "query": query,
            "dataframe": result
        }
