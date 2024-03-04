#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts all functions related to AWS Config advanced queries
"""
import logging
import json
from typing import (
    Union,
    List
)

import pandas
from botocore.exceptions import (
    ClientError
)

from data_perimeter_helper.variables import (
    Variables as Var
)


logger = logging.getLogger(__name__)


def submit_config_advanced_query(
    query: str,
    limit: int = 100,
    transform_to_pandas: bool = True,
) -> Union[pandas.DataFrame, list]:
    """Perform an AWS Config advanced query
    API documentation
    https://docs.aws.amazon.com/config/latest/APIReference/API_SelectAggregateResourceConfig.html

    :param query: Advanced Query for AWS Config aggregator to submit
    :param limit: limit per request, defaults to 100
    :param return_results: if True return the retrieved results, defaults to False
    :param transform_to_pandas: if True transform results to pandas DataFrame, defaults to True
    :param print_result: if True print the results, defaults to True
    :return: Result of AWS Config advanced query, as a list or a pandas DataFrame
    depending on argument transform_to_pandas
    """
    logger.debug(
        "Config aggregator used:%s, Config advanced query:\n%s",
        Var.config_aggregator_name, query
    )
    if Var.print_query:
        print(f"Config advanced query:\n{query}")
    list_result: List[str] = []
    assert Var.config_client is not None  # nosec: B101
    try:
        paginator = Var.config_client.get_paginator('select_aggregate_resource_config')
        page_iterator = paginator.paginate(
            Expression=query,
            ConfigurationAggregatorName=Var.config_aggregator_name,
            Limit=limit
        )
        for page in page_iterator:
            for item in page['Results']:
                list_result.append(item)
    except ClientError as error:
        logger.error("[!] Error from AWS client:\n%s", error.response)  # nosemgrep: logging-error-without-handling
        if error.response['Error']['Code'] == 'AccessDeniedException':
            logger.error(
                "[!] Current principal is not authorized to perform action on [Config]"
            )
        if error.response['Error']['Code'] == 'NoSuchConfigurationAggregatorException':
            logger.error(
                "[!] AWS Config aggregator [%s] not found",
                Var.config_aggregator_name
            )
        if error.response['Error']['Code'] == 'ExpiredTokenException':
            logger.error(
                "[!] Your credentials have expired, renew them and try again"
            )
        raise
    logger.debug("[~] Converting Config advanced query result to dataframe")
    if transform_to_pandas or Var.print_result:
        df_result = pandas.DataFrame([json.loads(_) for _ in list_result])
        if Var.print_result:
            print(f"Config advanced query results:\n{df_result}")
        if transform_to_pandas:
            return df_result
    return list_result
