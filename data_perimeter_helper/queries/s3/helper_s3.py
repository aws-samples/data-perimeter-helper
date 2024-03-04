#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the helper functions specific to the s3 queries
'''
import logging

import pandas

from data_perimeter_helper.referential.Referential import (
    Referential
)
from data_perimeter_helper.toolbox import (
    utils
)
from data_perimeter_helper.queries import (
    helper as generic_helper
)

logger = logging.getLogger(__name__)


def get_athena_selected_account_s3_bucket(
    account_id: str,
    with_negation: bool = True
) -> str:
    """Get the list of S3 bucket for a given account ID"""
    result = Referential.get_resource_attribute(
        resource_type="AWS::S3::Bucket",
        lookup_value=account_id,
        lookup_column='accountId',
        attribute='resourceId',
        return_all_values_as_list=True
    )
    if not isinstance(result, list) or len(result) == 0:
        return "-- No S3 bucket to inject"
    list_s3_bucket_as_str = utils.str_sanitizer(
        "|".join(result)
    )
    if with_negation:
        return generic_helper.comment_injected_sql(
            f"""AND COALESCE(NOT regexp_like(JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'), {list_s3_bucket_as_str}), True)""",
            "list_account_s3_bucket"
        )
    return generic_helper.comment_injected_sql(
        f"""AND regexp_like(JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'), {list_s3_bucket_as_str})""",
        "list_account_s3_bucket"
    )


def remove_call_on_bucket_in_organization(
    result: pandas.DataFrame
) -> pandas.DataFrame:
    """Remove API calls on Amazon S3 buckets in by the AWS organization -
    the list of S3 buckets in the AWS organization is retrieved from
    AWS Config aggregator"""
    s3_buckets = Referential.get_resource_type("AWS::S3::Bucket")
    logger.debug("[~] Adding column [isBucketInConfAgg]")
    result['isBucketInConfAgg'] = [
        s3_buckets.exists(
            bucket_name,
            'resourceId'
        )
        for bucket_name in result['bucketname']
    ]
    logger.debug(
        "[~] API calls to bucket not inventoried in Config aggregator"
        "are removed"
    )
    return result.drop(
        result[
            result['isBucketInConfAgg'].isin([True, 'True'])
        ].index
    )


def athena_remove_s3_event_name_at_account_scope() -> str:
    """Remove API calls at the account scope, such API calls are not applied to resources not owned by the selected account."""
    return """AND eventname NOT IN (
        'CreateBucket', 'CreateJob', 'CreateStorageLensGroup', 'GetAccessPoint', 'GetAccountPublicAccessBlock', 'ListAccessGrantsInstances', 'ListAccessPoints', 'ListAccessPointsForObjectLambda', 'ListAllMyBuckets',
        'ListBuckets', 'ListJobs', 'ListMultiRegionAccessPoints', 'ListStorageLensConfigurations', 'ListStorageLensGroups', 'PutAccessPointPublicAccessBlock',
        'PutAccountPublicAccessBlock', 'PutStorageLensConfiguration'
    )"""
