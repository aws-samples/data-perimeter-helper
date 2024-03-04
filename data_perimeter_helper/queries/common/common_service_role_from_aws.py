#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: common_service_role_from_aws
'''
import logging
from typing import (
    Dict,
    Union,
    List,
    Tuple
)

import pandas

from data_perimeter_helper.queries import (
    helper
)
from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.queries.Query import (
    Query
)


logger = logging.getLogger(__name__)


class common_service_role_from_aws(Query):
    """List AWS API calls made by service roles from AWS service networks.   
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls.
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::IAM::Role',
                'AWS::Organizations::Account'
            ],
            use_split_table=True
        )

    def generate_athena_statement(
        self,
        account_id: str
    ) -> Union[None, Tuple[str, List[str]]]:
        """Generate Athena SQL query"""
        params: List[str] = []
        statement = f"""-- Query: {self.name} | {account_id}
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Keep only API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.
    AND regexp_like(sourceipaddress, '(?i)(amazonaws|Internal)')
    -- Keep only API calls performed by assumed roles
    AND useridentity.type = 'AssumedRole'
    -- Remove API calls made by service-linked roles in the selected account
    AND COALESCE(NOT regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)'), True)
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress
"""  # nosec B608
        return statement, params

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit an Athena SQL query and perform data processing"""
        athena_query, result = self.submit_athena_query(
            self.name, account_id
        )
        if len(result.index) == 0:
            logger.debug("[~] No result retrieved - DataFrame is empty")
            return {
                "query": athena_query,
                "dataframe": result
            }
        self.add_column_is_assumable_by(result)
        self.add_column_is_service_role(result)
        logger.debug("[-] principals that are not service roles are removed")
        result = result.drop(
            result[
                result['isServiceRole'].isin([False, 'False'])
            ].index
        )
        result = self.remove_calls_by_service_linked_role(result)
        result = self.remove_calls_from_service_on_behalf_of_principal(
            result
        )
        if len(result.index):
            logger.debug("[~] Writing parameters [controlType && findings]")
            result['controlType'] = "network_perimeter"
            result['findings'] = "Principal is a service role and made API calls from an AWS service network"
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
