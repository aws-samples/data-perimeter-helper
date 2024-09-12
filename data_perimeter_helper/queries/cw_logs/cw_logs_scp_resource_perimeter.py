#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: cw_logs_scp_resource_perimeter
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


class cw_logs_scp_resource_perimeter(Query):
    """List AWS API call `PutSubscriptionFilter` made by principals in the selected account on Amazon CloudWatch Logs destinations not owned by accounts in the same organization as the selected account.
You can use this query to accelerate implementation of the [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls using service control policies (SCPs).
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        depends_on_resource_type = [
            'AWS::IAM::Role',
            'AWS::Organizations::Account',
        ]
        super().__init__(
            name,
            depends_on_resource_type,
            use_split_table=True
        )

    def generate_athena_statement(
        self,
        account_id: str
    ) -> Union[None, Tuple[str, List[str]]]:
        """Generate the Athena SQL query"""
        params: List[str] = []
        keep_selected_account_principal = helper.get_athena_selected_account_principals(
            account_id=account_id,
            with_negation=False,
        )
        list_all_account_id = helper.get_athena_all_account_contains_operator()
        resource_perimeter_trusted_logs_destination_arn = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="resource_perimeter_trusted_logs_destination_arn",
            column_name="JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn')",
            params=params,
            with_negation=True
        )
        resource_perimeter_trusted_principal_arn = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="resource_perimeter_trusted_principal",
            column_name="useridentity.sessioncontext.sessionissuer.arn",
            params=params,
            with_negation=True
        )
        resource_perimeter_trusted_principal_id = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="resource_perimeter_trusted_principal",
            column_name="useridentity.principalid",
            params=params,
            with_negation=True
        )
        statement = f"""-- Query: {self.name} | {account_id}
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventname,
    JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn') AS destinationArn,
    TRY(SPLIT(JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'), ':')[5]) AS destinationAccountId,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 'logs.amazonaws.com'
    AND eventname = 'PutSubscriptionFilter'
    -- Keep only API calls made by principals in the selected account
    {keep_selected_account_principal}
    -- Remove API calls on CloudWatch destinations owned by accounts belonging to the same AWS organization as the selected account.
    AND TRY(SPLIT(JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'), ':')[5]) NOT IN ({list_all_account_id})
    -- Remove API calls made on trusted CloudWatch Logs destination tables - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_ecr_repository_arn` parameter).
    {resource_perimeter_trusted_logs_destination_arn}
    -- Remove API calls made by resource perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_principal` parameter).
    {resource_perimeter_trusted_principal_arn}
    {resource_perimeter_trusted_principal_id}
    -- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
    AND useridentity.principalid != 'AWSService'
    -- Remove API calls made by service-linked roles in the selected account
    AND COALESCE(NOT regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)'), True)
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventname,
    JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'),
    TRY(SPLIT(JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'), ':')[5])
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
        result = self.remove_calls_by_service_linked_role(result)
        if len(result.index):
            logger.debug("[~] Writing parameters [controlType && findings]")
            result['controlType'] = "resource_perimeter"
            result['findings'] = "Principal is calling a resource not "\
                "owned by the same organization as the selected account"
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
