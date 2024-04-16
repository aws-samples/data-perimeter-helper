#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the Referential class
"""
import logging
from typing import (
    Optional,
    Union,
    List,
    ItemsView
)
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed as concurrent_completed
)
from time import (
    perf_counter,
)

from pandas._libs.missing import (
    NAType
)
from tqdm import (
    tqdm
)
from data_perimeter_helper.toolbox import utils
from data_perimeter_helper.referential import (
    vpce,
    generic
)
from data_perimeter_helper.referential.ResourceType import ResourceType
from data_perimeter_helper.variables import Variables as Var


logger = logging.getLogger(__name__)


class Referential:
    """Used as an interface to ResourceType class"""

    @classmethod
    def batch_get_resource_type(
        cls,
        list_resources: Optional[List[str]] = None
    ):
        """Get all supported resources in batch through threading"""
        if list_resources is None:
            list_resources = ResourceType.supported_types()
        assert isinstance(list_resources, list)  # nosec: B101
        nb_items = len(list_resources)
        str_resource_type = " | ".join(list_resources)
        if nb_items == 0:
            return
        if nb_items > 1:
            msg = f"{nb_items} resource types to collect: {str_resource_type}"
        else:
            msg = f"{nb_items} resource type to collect: {str_resource_type}"
        logger.debug(msg)
        print(utils.Icons.HAND_POINTING + msg)
        with tqdm(
            total=nb_items,
            desc="Referential items retrieved: ", unit="items"
        ) as pbar:
            with ThreadPoolExecutor(
                max_workers=Var.thread_max_worker
            ) as executor:
                pool = {
                    executor.submit(
                        cls.get_resource_type,
                        resource_type
                    ): {
                        'resource_type': resource_type,
                        'start_time': perf_counter(),
                    }
                    for resource_type in list_resources
                }
                for request_in_pool in concurrent_completed(pool):
                    exception = request_in_pool.exception()
                    if exception:
                        raise exception
                    resource_type = pool[request_in_pool]['resource_type']
                    exec_time = utils.get_elapsed_time(
                        pool[request_in_pool]['start_time']  # type: ignore
                    )
                    log_msg = "Get resource type completed for "\
                        f"`{resource_type}` in {exec_time}"
                    pbar.write(
                        utils.color_string(
                            utils.Icons.FULL_CHECK_GREEN + log_msg, utils.Colors.GREEN_BOLD
                        )
                    )
                    logger.debug(log_msg)
                    pbar.update(1)

    @classmethod
    def get_resource_type(
        cls,
        resource_type: str
    ) -> ResourceType:
        """Get all resources of a given resource type"""
        resource_type_lower = resource_type.lower()
        if resource_type_lower not in ResourceType.registry:
            # If the resource_type is a VPC endpoint, example: "AWS::EC2::VPCEndpoint::S3"
            if "aws::ec2::vpcendpoint::" in resource_type_lower:
                vpce.vpce(resource_type)
            else:
                generic.generic(resource_type)
        resource = ResourceType.get_from_registry(resource_type)
        assert isinstance(resource, ResourceType)  # nosec: B101
        resource.get_df()
        return resource

    @classmethod
    def get_resource_attribute(
        cls,
        resource_type: str,
        lookup_value: str,
        lookup_column: str,
        attribute: str,
        return_all_values_as_list: bool = False,
    ) -> Union[List[str], str, NAType]:
        """Get a given resource attribute"""
        res_type = cls.get_resource_type(resource_type)
        if return_all_values_as_list:
            return res_type.attribute_list(
                lookup_value,
                lookup_column,
                attribute
            )
        return res_type.attribute_value(
            lookup_value,
            lookup_column,
            attribute
        )

    @staticmethod
    def get_resource_type_registry_items() -> ItemsView[str, ResourceType]:
        return ResourceType.registry.items()
