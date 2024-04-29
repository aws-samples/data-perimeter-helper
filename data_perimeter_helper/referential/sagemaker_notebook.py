#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `sagemaker_notebook` used to retrieve Amazon
SageMaker notebook.
"""
import logging
import json

import pandas

from data_perimeter_helper.referential import (
    config_adv
)
from data_perimeter_helper.referential.ResourceType import ResourceType


logger = logging.getLogger(__name__)


class sagemaker_notebook(ResourceType):
    """List Amazon SageMaker notebooks inventoried in AWS Config aggregator"""
    def __init__(self):
        super().__init__(
            type_name="AWS::SageMaker::NotebookInstance",
            unknown_value="SAGEMAKER_NOTEBOOK_NOT_IN_CONFIG_AGGREGATOR"
        )

    def populate(self, *args, **kwargs) -> pandas.DataFrame:
        """Retrieve all AWS Glue jobs inventoried in AWS Config aggregator
    https://github.com/awslabs/aws-config-resource-schema/blob/master/config/properties/resource-types/AWS%3A%3AGlue%3A%3AJob.properties.json
        :return: DataFrame with all Glue jobs
        """
        config_query = f'''
SELECT
    accountId,
    arn,
    configuration.DirectInternetAccess,
    configuration.SubnetId,
    configuration.SecurityGroupIds
WHERE
    resourceType = '{self.type_name}'
'''
        logger.debug("[-] Submitting Config advanced query")
        results = config_adv.submit_config_advanced_query(
            query=config_query,
            transform_to_pandas=False,
        )
        logger.debug("[+] Submitting Config advanced query")
        assert isinstance(results, list)  # nosec: B101
        if len(results) == 0:
            return pandas.DataFrame()
        logger.debug("[-] Converting results to DataFrame")
        df = pandas.DataFrame(
            [json.loads(_) for _ in results]
        )
        df_configuration = pandas.json_normalize(df['configuration'])  # type: ignore

        df = pandas.concat([df, df_configuration], axis=1)
        # Dropping uneeded columns
        df = df.drop(columns=['configuration'])
        df = df.fillna(value="Not set")
        logger.debug("[+] Converting results to DataFrame")
        return df
