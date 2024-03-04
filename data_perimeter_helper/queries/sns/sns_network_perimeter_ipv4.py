#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: sns_network_perimeter_ipv4
https://docs.aws.amazon.com/sns/latest/dg/sns-access-policy-language-api-permissions-reference.html
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


class sns_network_perimeter_ipv4(Query):
    """
List SNS API calls filtering out calls that align with your definition of expected networks.
You can use this query to accelerate implementation of the [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls using your SNS topic policies or service control policies (SCPs).
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        depends_on_resource_type = [
            'AWS::IAM::Role',
            "AWS::SNS::Topic",
            'AWS::Organizations::Account',
            'AWS::EC2::VPCEndpoint::SNS',
        ]
        super().__init__(
            name,
            depends_on_resource_type,
            use_split_table=False
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
        remove_selected_account_vpce = helper.get_athena_selected_account_vpce(
            account_id=account_id,
            service_name="sns",
            with_negation=True
        )
        network_perimeter_expected_vpc_endpoint = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="network_perimeter_expected_vpc_endpoint",
            column_name="vpcendpointid",
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
    eventname,
    COALESCE(
        JSON_EXTRACT_SCALAR(requestparameters, '$.topicArn'),
        JSON_EXTRACT_SCALAR(requestparameters, '$.resourceArn'),
        JSON_EXTRACT_SCALAR(responseelements, '$.topicArn')
    ) AS topicArn,
    resources,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 'sns.amazonaws.com'
    -- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
    AND COALESCE(NOT regexp_like(sourceipaddress, ':'), True)
    -- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
    {network_perimeter_expected_public_cidr}
    -- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator
    {remove_selected_account_vpce}
    -- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
    {network_perimeter_expected_vpc_endpoint}
    -- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
    {network_perimeter_trusted_account}
    -- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
    {network_perimeter_trusted_principal_arn}
    {network_perimeter_trusted_principal_id}
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
    COALESCE(
        JSON_EXTRACT_SCALAR(requestparameters, '$.topicArn'),
        JSON_EXTRACT_SCALAR(requestparameters, '$.resourceArn'),
        JSON_EXTRACT_SCALAR(responseelements, '$.topicArn')
    ),
    resources,
    vpcendpointid,
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
        self.add_column_vpc_id(result)
        self.add_column_vpce_account_id(result)
        self.add_column_is_assumable_by(result)
        self.add_column_is_service_role(result)
        result = self.remove_calls_by_service_linked_role(result)
        result = self.remove_expected_vpc_id(
            account_id,
            result
        )
        result = self.remove_calls_from_service_on_behalf_of_principal(
            result
        )
        if len(result.index):
            logger.debug("[~] Writing parameters [controlType && findings]")
            result['controlType'] = "network_perimeter"
            result['findings'] = [
                helper.basic_explain_network_perimeter_findings(
                    is_service_role, ip, vpce_id, vpc_id
                )
                for is_service_role, ip, vpce_id, vpc_id
                in zip(
                    result['isServiceRole'],
                    result['sourceipaddress'],
                    result['vpcendpointid'],
                    result['vpcId']
                )
            ]
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
