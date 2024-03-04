#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: common_from_public_cidr_ipv4
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


class common_from_public_cidr_ipv4(Query):
    """List AWS API calls made from public IPv4 addresses.   
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls controls by reviewing API calls made from public IPv4 addresses. You can then use the global condition key [aws:SourceIp](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-sourceip) to help ensure your API calls are only made from expected public CIDR ranges.
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
        """Generate the Athena SQL query"""
        params: List[str] = []
        network_perimeter_expected_public_cidr = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="network_perimeter_expected_public_cidr",
            column_name="sourceipaddress",
            params=params,
            with_negation=True
        )
        network_perimeter_trusted_account = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="network_perimeter_trusted_account",
            column_name="useridentity.accountid",
            params=params,
            with_negation=True
        )
        network_perimeter_trusted_principal_arn = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="network_perimeter_trusted_principal",
            column_name="useridentity.sessioncontext.sessionissuer.arn",
            params=params,
            with_negation=True
        )
        network_perimeter_trusted_principal_id = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="network_perimeter_trusted_principal",
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
    eventsource,
    eventname,
    sourceipaddress,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Remove API calls made by service-linked roles in the selected account
    AND COALESCE(NOT regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)'), True)
    -- Remove IPv6 calls and calls from AWS service networks
    AND COALESCE(NOT regexp_like(sourceipaddress, '(?i)(:|amazonaws|Internal)'), True)
    -- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
    {network_perimeter_expected_public_cidr}
    -- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
    {network_perimeter_trusted_account}
    -- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
    {network_perimeter_trusted_principal_arn}
    {network_perimeter_trusted_principal_id}
    -- Remove API calls made through VPC endpoints - `vpcendpointid` field in CloudTrail log is `NULL`.
    AND vpcendpointid IS NULL
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
        self.add_column_is_service_linked_role(result)
        result = self.remove_calls_by_service_linked_role(result)
        logger.debug("[~] Writing parameters [controlType && findings]")
        result['controlType'] = "network_perimeter"
        result['findings'] = "Principal is performing AWS API calls from an unexpected public CIDR"
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
