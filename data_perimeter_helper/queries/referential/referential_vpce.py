#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: referential_vpce
'''
import logging
from typing import (
    Dict,
    Union,
)

import pandas

from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.referential.Referential import (
    Referential
)
from data_perimeter_helper.queries.referential import (
    helper_referential
)


logger = logging.getLogger(__name__)


class referential_vpce(Query):
    """List the Amazon Virtual Private Cloud (Amazon VPC) endpoints in your Config aggregator.
Use this query to review the VPC endpoints that have a default policy or a policy that contains one of the [AWS global condition context keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html) aws:PrincipalOrgId/PrincipalOrgPaths/PrincipalAccount or aws:ResourceOrgId/ResourceOrgPaths/ResourceAccount.
You can use this query to assess and accelerate the implementation of your [**identity perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) and  [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls on your VPC endpoints.
"""  # noqa: W291

    default_policy_statement = """{"Version":"2008-10-17","Statement":[{"Effect":"Allow","Principal":"*","Action":"*","Resource":"*"}]}"""

    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::EC2::VPCEndpoint'
            ]
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit a query and perform data processing"""
        dataframe = Referential.get_resource_type('AWS::EC2::VPCEndpoint').dataframe
        assert isinstance(dataframe, pandas.DataFrame)  # nosec: B101
        dataframe["isDefaultPolicy"] = [
            policy == self.default_policy_statement
            for policy in dataframe["policyDocument"]
        ]
        helper_referential.add_column_contains_condition_principal_wildcard(
            dataframe,
            column_name_policy='policyDocument'
        )
        helper_referential.add_column_contains_condition_resource_wildcard(
            dataframe,
            column_name_policy='policyDocument'
        )
        return {
            "query": "",
            "dataframe": dataframe
        }
