#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `vpce` used to retrieve Amazon EC2 VPC endpoints
through AWS Config advanced queries
"""
import json
import logging
from typing import (
    Optional
)

import pandas

from data_perimeter_helper.referential import (
    config_adv
)
from data_perimeter_helper.referential.ResourceType import ResourceType


logger = logging.getLogger(__name__)


class vpce(ResourceType):
    """List all Amazon VPC endpoints"""
    def __init__(
        self,
        resource_type: str = "AWS::EC2::VPCEndpoint",
    ):
        self.resource_type = resource_type.lower()
        self.service_name: Optional[str] = None
        if "aws::ec2::vpcendpoint::" in self.resource_type:
            resource_type_as_array = self.resource_type.split("::")
            self.service_name = resource_type_as_array[-1]
            logger.debug("Adding custom VPC endpoint: %s", self.service_name)
        super().__init__(
            type_name=self.resource_type,
            unknown_value="VPCE_NOT_IN_CONFIG_AGGREGATOR"
        )

    def populate(self) -> pandas.DataFrame:
        """ Retrieve all VPC endpoint inventoried in AWS Config aggregator
        :return: DataFrame with all VPC endpoints
        Configuration element is retrieved from Config
        https://github.com/awslabs/aws-config-resource-schema/blob/master/config/properties/resource-types/AWS::EC2::VPCEndpoint.properties.json
        """
        config_query = """SELECT
    configuration.serviceName,
    configuration.ownerId,
    configuration.vpcEndpointId,
    configuration.vpcId
WHERE
    resourceType = 'AWS::EC2::VPCEndpoint'"""
        if self.service_name is not None:
            config_query += f"""
    AND configuration.serviceName LIKE 'com.amazonaws.%.{self.service_name.lower()}'"""
        logger.debug("[-] Submitting Config advanced query")
        results = config_adv.submit_config_advanced_query(
            query=config_query,
            transform_to_pandas=False,
        )
        logger.debug("[+] Submitting Config advanced query")
        logger.debug("[-] Converting results to DataFrame")
        assert isinstance(results, list)  # nosec: B101
        results = pandas.DataFrame(
            [json.loads(_) for _ in results]
        )
        if len(results.index) == 0:
            return results
        results = pandas.json_normalize(
            results['configuration']  # type: ignore
        )
        logger.debug("[+] Converting results to DataFrame")
        return results
