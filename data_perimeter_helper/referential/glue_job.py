#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `glue_job` used to retrieve AWS Glue jobs
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


class glue_job(ResourceType):
    """List AWS Glue jobs inventoried in AWS Config aggregator"""
    def __init__(self):
        super().__init__(
            type_name="AWS::Glue::Job",
            unknown_value="GLUE_JOB_NOT_IN_CONFIG_AGGREGATOR"
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
    configuration.Connections.Connections,
    configuration.DefaultArguments
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
        if 'DefaultArguments.--disable-proxy-v2' not in df_configuration:
            df_configuration['DefaultArguments.--disable-proxy-v2'] = "Not set"
        if 'Connections.Connections' not in df_configuration:
            df_configuration['Connections.Connections'] = "Not set"
        df_configuration = df_configuration[
            ['DefaultArguments.--disable-proxy-v2', 'Connections.Connections']
        ]
        df_configuration = df_configuration.rename(
            columns={
                'DefaultArguments.--disable-proxy-v2': 'DisableProxyV2ArgumentValue',
                'Connections.Connections': 'ConnectionNames'
            }
        )
        df_configuration = df_configuration.replace(
            {
                "true": True,
                "false": False
            }
        )
        df_configuration = df_configuration.fillna(pandas.NA).replace(
            {pandas.NA: None}
        )
        df = pandas.concat([df, df_configuration], axis=1)
        # Dropping uneeded columns
        df = df.drop(columns=['configuration'])
        logger.debug("[+] Converting results to DataFrame")
        return df
