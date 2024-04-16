#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: s3_external_access_org_boundary
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


logger = logging.getLogger(__name__)


class s3_external_access_org_boundary(Query):
    """List active AWS IAM Access Analyzer external findings associated with Amazon S3 buckets.
You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your S3 buckets at the organization level. You can use the global condition key [aws:PrincipalOrgId](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) to limit access to your resources to principals belonging to your AWS organization.
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        self.depends_on_resource_type = []
        super().__init__(
            name,
            self.depends_on_resource_type,
            depends_on_iam_access_analyzer=True,
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Retrieve AWS IAM Access Analyzer findings tied to Amazon S3 buckets"""
        query = ""
        ExternalAccessFindings()
        if ExternalAccessFindings.is_enabled() is not True:
            return {
                "query": query,
                "dataframe": pandas.DataFrame()
            }
        result = ExternalAccessFindings.get_findings_as_df(
            get_only_active=True,
            account_id=account_id,
            resource_type="AWS::S3::Bucket"
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
