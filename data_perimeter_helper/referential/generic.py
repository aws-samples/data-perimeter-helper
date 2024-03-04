#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class generic used to retrieve any AWS Config resource type supported
"""
import logging
import json

import pandas

from data_perimeter_helper.referential import (
    config_adv
)
from data_perimeter_helper.referential.ResourceType import ResourceType

logger = logging.getLogger(__name__)


class generic(ResourceType):
    """Get all resource of a given resource type"""
    def __init__(self, resource_type: str):
        self.resource_type = resource_type
        resource_type_as_array = resource_type.split("::")
        resource_name = "_".join(resource_type_as_array[-2:])
        unknown_value = f"{resource_name}_NOT_IN_CONFIG_AGGREGATOR".upper()
        super().__init__(
            type_name=resource_type,
            unknown_value=unknown_value
        )

    def populate(self) -> pandas.DataFrame:
        """ Retrieves data for a given resource type """
        logger.debug(
            "[~] Using a generic Config advanced query to retrieve"
            " resource type: %s",
            self.resource_type
        )
        config_query = f'''
SELECT
    accountId, awsRegion, resourceId
WHERE
    resourceType = '{self.resource_type}'
    '''
        logger.debug("[~] Submitting Config advanced query")
        results = config_adv.submit_config_advanced_query(
            query=config_query,
            transform_to_pandas=False,
        )
        logger.debug("[~] Converting results to DataFrame")
        assert isinstance(results, list)  # nosec: B101
        results = pandas.DataFrame(
            [json.loads(_) for _ in results]
        )
        logger.debug(results)
        return results
