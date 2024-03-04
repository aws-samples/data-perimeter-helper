#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: common_from_vpc_endpoint
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


class common_through_vpc_endpoint(Query):
    """List AWS API calls made through any VPC endpoints.  
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls by reviewing API calls made through through a VPC endpoint. You can then use the global condition keys [aws:SourceVpce](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-sourcevpce) or [aws:SourceVpc](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-sourcevpc) to ensure that your API calls are only made through your expected VPC endpoint IDs or VPC IDs, respectively.
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::IAM::Role',
                'AWS::Organizations::Account',
                'AWS::EC2::VPCEndpoint'
            ],
            use_split_table=True
        )

    def generate_athena_statement(
        self,
        account_id: str
    ) -> Union[None, Tuple[str, List[str]]]:
        """Generate Athena SQL query"""
        params: List[str] = []
        network_perimeter_expected_vpc_endpoint = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="network_perimeter_expected_vpc_endpoint",
            column_name="vpcendpointid",
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
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Keep only API calls made through a VPC endpoint
    AND vpcendpointid IS NOT NULL
    -- Remove API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.
    AND COALESCE(NOT regexp_like(sourceipaddress, '(?i)(amazonaws|Internal)'), True)
    -- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
    {network_perimeter_expected_vpc_endpoint}
    -- Remove API calls made via AWS Management Console with `S3Console` and `AWSCloudTrail` user agent - this is to manage temporary situations where the field `vpcendpointid` contains AWS owned VPC endpoint IDs.
    AND COALESCE(NOT regexp_like(useragent, '(?i)(S3Console|AWSCloudTrail)'), True)
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress,
    vpcendpointid
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
        logger.debug("[~] Writing parameters [controlType && findings]")
        result['controlType'] = "network_perimeter"
        result['findings'] = "Principal is performing AWS API calls through an unexpected VPC endpoint or an AWS-owned VPC endpoint"
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
