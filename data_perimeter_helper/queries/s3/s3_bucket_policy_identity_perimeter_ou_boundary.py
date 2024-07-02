#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: s3_bucket_policy_identity_perimeter_ou_boundary
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


def explain_result(
    principal_account_id: str,
    list_principal_in_org: List[str],
) -> str:
    if isinstance(principal_account_id, str) and principal_account_id == "anonymous":
        return "Unauthenticated API call"
    if not isinstance(principal_account_id, str) and not len(
        principal_account_id
    ) == 12:
        return ""
    if principal_account_id not in list_principal_in_org:
        return "Principal is not part of the current organization"
    return "Principal is not part of the same organizational unit (OU) boundary"


class s3_bucket_policy_identity_perimeter_ou_boundary(Query):
    """List AWS API calls made on S3 buckets in the selected account by principals that do **NOT** belong to the same organizational unit (OU) boundary, filtering out calls that align with your definition of trusted identities.

You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your S3 buckets at the organizational unit (OU) level. You can use the global condition key [aws:PrincipalOrgPaths](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgpaths) to limit access to your resources only to principals belonging to specific OUs.

You can declare your OU boundaries in the `data perimeter helper` configuration file (`org_unit_boundary` parameter).
OU boundaries allow you to logically regroup your accounts for analysis based on their location in your AWS organization. For example, you can declare OUs `ou-xxxxx-1111111` and `ou-xxxxx-2222222` (and all OUs contained within them) as your `production` boundary. Then you can run this query for one of the accounts in these OUs to review the API calls made by principals that do **NOT** belong to the same boundary (in this example: non-production accounts).
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        depends_on_resource_type = [
            'AWS::IAM::Role',
            'AWS::Organizations::Tree',
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
        keep_selected_account_s3_bucket = helper_s3.get_athena_selected_account_s3_bucket(
            account_id=account_id,
            with_negation=False,
        )
        remove_selected_account_org_unit_boundary = helper.get_athena_account_org_unit_boundary(
            account_id=account_id,
            with_negation=True,
        )
        identity_perimeter_trusted_account = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="identity_perimeter_trusted_account",
            column_name="useridentity.accountid",
            params=params,
            with_negation=True
        )
        identity_perimeter_trusted_principal_arn = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="identity_perimeter_trusted_principal",
            column_name="useridentity.sessioncontext.sessionissuer.arn",
            params=params,
            with_negation=True
        )
        identity_perimeter_trusted_principal_id = helper.get_athena_dph_configuration(
            account_id=account_id,
            configuration_key="identity_perimeter_trusted_principal",
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
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator
    {keep_selected_account_s3_bucket}
    -- Remove API calls from principals belonging to the same OU boundary
    {remove_selected_account_org_unit_boundary}
    -- Remove API calls made by principals belonging to identity perimeter trusted accounts - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_account` parameter).
    {identity_perimeter_trusted_account}
    -- Remove API calls made by identity perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_principal` parameter).
    {identity_perimeter_trusted_principal_arn}
    {identity_perimeter_trusted_principal_id}
    -- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
    AND useridentity.principalid != 'AWSService'
    -- Remove S3 preflight requests which are unauthenticated and used to determine the cross-origin resource sharing (CORS) configuration
    AND eventname != 'PreflightRequest'
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
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
        logger.debug("[~] Removing bucket specific exceptions")
        result = self.remove_all_resource_exception(
            account_id=account_id,
            dataframe=result,
            resource_type="AWS::S3::Bucket",
            resource_id_column_name="bucketname",
            list_exception_type_to_consider=[
                "identity_perimeter_trusted_principal"
            ]
        )
        list_org_principal = helper.get_list_account_id()
        if isinstance(list_org_principal, list) and list_org_principal:
            if len(result.index):
                logger.debug("[~] Writing parameters [controlType && findings]")
                result['controlType'] = "identity_perimeter"
                result['findings'] = [
                    explain_result(principal_account_id, list_org_principal)
                    for principal_account_id in result["principal_accountid"]
                ]
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
