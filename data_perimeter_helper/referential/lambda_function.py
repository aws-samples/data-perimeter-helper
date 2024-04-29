#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `lambda_function` used to retrieve AWS Lambda
functions with AWS Config advanced queries
"""
import logging
import json

import pandas

from data_perimeter_helper.referential import (
    config_adv
)
from data_perimeter_helper.referential.ResourceType import ResourceType


logger = logging.getLogger(__name__)


class lambda_function(ResourceType):
    """List AWS Lambda function inventoried in AWS Config aggregator"""
    def __init__(self):
        super().__init__(
            type_name="AWS::Lambda::Function",
            unknown_value="LAMBDA_FUNCTION_NOT_IN_CONFIG_AGGREGATOR"
        )

    def populate(self, *args, **kwargs) -> pandas.DataFrame:
        """Retrieve all AWS Lambda functions inventoried in AWS Config aggregator
    https://github.com/awslabs/aws-config-resource-schema/blob/master/config/properties/resource-types/AWS%3A%3ALambda%3A%3AFunction.properties.json
        :return: DataFrame with all Lambda functions
        """
        config_query = f'''
SELECT
    accountId,
    arn,
    configuration.vpcConfig.subnetIds
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
        results = pandas.DataFrame(
            [json.loads(_) for _ in results]
        )
        results = results.drop(columns='configuration').join(
            pandas.json_normalize(results['configuration'])  # type: ignore
        )
        results['inVpc'] = [
            True
            if isinstance(list_subnet_id, list) and len(list_subnet_id) > 0
            else False  # type: ignore
            for list_subnet_id in results['vpcConfig.subnetIds']
        ]
        # Drop column vpcConfig.subnetIds
        results = results.drop(columns='vpcConfig.subnetIds')
        results = results.fillna(value="N/A")
        logger.debug("[+] Converting results to DataFrame")
        return results
