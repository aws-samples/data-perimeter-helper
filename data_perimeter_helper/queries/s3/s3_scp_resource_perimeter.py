#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: s3_scp_resource_perimeter
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
from data_perimeter_helper.queries.s3 import (
    helper_s3
)
from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.queries.Query import (
    Query
)


logger = logging.getLogger(__name__)


class s3_scp_resource_perimeter(Query):
    """List AWS API calls made by principals in the selected account on Amazon S3 buckets not owned by accounts in the same organization as the selected account nor inventoried in your Config aggregator.
You can use this query to accelerate implementation of the [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls using service control policies (SCPs).
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        depends_on_resource_type = [
            'AWS::IAM::Role',
            'AWS::Organizations::Account',
            'AWS::S3::Bucket'
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
        resource_perimeter_trusted_bucket_name = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="resource_perimeter_trusted_bucket_name",
            column_name="JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName')",
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
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    unnested_resources.accountid as bucket_accountid,
    unnested_resources.arn as bucket_arn,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
LEFT JOIN UNNEST(
    resources
) u(unnested_resources) ON TRUE
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep only API calls made by principals in the selected account
    {keep_selected_account_principal}
    -- Remove API calls at the account scope, such API calls are not applied to resources not owned by the selected account.
    {helper_s3.athena_remove_s3_event_name_at_account_scope()}
    -- Remove API calls with the selected account ID in the request parameters (example: GetStorageLensConfiguration).
    AND COALESCE(NOT regexp_like(requestparameters, ':{account_id}:storage-lens|{account_id}.s3-control'), True)
    -- Remove the unnested values of the `resources` field in CloudTrail with `resource.type`=`AWS::S3::Object`. Another unnested row exists with `resources.type`=`AWS::S3::Bucket` and `resources.accountid` distinct from NULL.
    AND unnested_resources.type IS DISTINCT FROM 'AWS::S3::Object'
    -- Remove API calls on S3 buckets owned by accounts belonging to the same AWS organization as the selected account.
    AND COALESCE(unnested_resources.accountid NOT IN ({list_all_account_id}), True)
    -- Remove API calls made on trusted S3 buckets - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_bucket_name` parameter).
    {resource_perimeter_trusted_bucket_name}
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
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
    unnested_resources.accountid,
    unnested_resources.arn
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
        # self.add_column_vpc_id(result)
        self.add_column_is_assumable_by(result)
        self.add_column_is_service_role(result)
        result = self.remove_calls_by_service_linked_role(result)
        result = helper_s3.remove_call_on_bucket_in_organization(result)
        if len(result.index):
            logger.debug("[~] Writing parameters [controlType && findings]")
            result['controlType'] = "resource_perimeter"
            result['findings'] = "Principal is calling a resource not "\
                "owned by the same organization as the selected account nor inventoried in AWS Config aggregator"
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
