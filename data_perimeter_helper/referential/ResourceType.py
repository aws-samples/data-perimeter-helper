#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the ResourceType class
"""
import logging
from typing import (
    Union,
    List,
    Dict,
    Optional
)

import pandas
from pandas._libs.missing import (
    NAType
)


logger = logging.getLogger(__name__)


class ResourceType:
    """Represent an AWS resource type (example:, "AWS::IAM::Role")"""
    registry: Dict[str, 'ResourceType'] = {}

    def __init__(
        self,
        type_name: str,
        unknown_value: str = "RESOURCE_NOT_IN_REFERENTIAL"
    ) -> None:
        """
        Init a resource type
        self.lookup_cache = Dict(
            'column_name': {
                'lookup_value': dataframe.index (if cache hit) | None (else)
            }
        )
        """
        self.type_name = type_name
        self.type_name_lower = type_name.lower()
        logger.debug("Initialization of resource type: %s", self.type_name)
        self.unknown_value = unknown_value
        self.dataframe: Optional[pandas.DataFrame] = None
        self.lookup_cache: Dict[str, Dict[str, Union[pandas.Index, None]]] = {}
        if self.type_name not in ResourceType.registry:
            ResourceType.registry[self.type_name_lower] = self

    def populate(self, *args, **kwargs) -> pandas.DataFrame:
        """Needs to be overridden by childs.
        Generate the query Athena statement"""
        raise NotImplementedError("Must be overridden by childs queries")

    def get_df(self, *args, **kwargs) -> pandas.DataFrame:
        """Get dataframe with resources, if the dataframe is not initialized,
        populate the dataframe by calling the attribute get_all_fct"""
        if self.dataframe is not None:
            return self.dataframe
        logger.debug("[-] Getting resource type: %s", self.type_name)
        self.dataframe = self.populate(*args, **kwargs)
        assert isinstance(self.dataframe, pandas.DataFrame)  # nosec: B101
        logger.debug("[+] Getting resource type: %s > DONE", self.type_name)
        return self.dataframe

    def lookup(
        self,
        lookup_value: str,
        lookup_column: str
    ) -> Union[str, pandas.DataFrame]:
        """Perform a query to identify results based on a specific value
        on a specific column"""
        if self.dataframe is None:
            self.get_df()
        assert isinstance(self.dataframe, pandas.DataFrame)  # nosec: B101
        if len(self.dataframe.index) == 0:
            return self.unknown_value
        cache_selected_column = self.lookup_cache.setdefault(
            lookup_column, {}
        )
        if lookup_value in cache_selected_column:
            index_from_cache = cache_selected_column[lookup_value]
            if index_from_cache is None:
                return self.unknown_value
            return self.dataframe.iloc[
                index_from_cache
            ]
        lookup_resource = self.dataframe.loc[
            self.dataframe[lookup_column] == lookup_value
        ]
        if len(lookup_resource.index) == 0:
            cache_selected_column[lookup_value] = None
            return self.unknown_value
        cache_selected_column[lookup_value] = lookup_resource.index
        return lookup_resource

    def exists(
        self,
        lookup_id: str,
        lookup_column: str
    ) -> bool:
        """Return ture is the resource is found"""
        return isinstance(
            self.lookup(lookup_id, lookup_column),
            pandas.DataFrame
        )

    def attribute_value(
        self,
        lookup_id: str,
        lookup_column: str,
        attribute: str
    ) -> Union[str, NAType]:
        """Perform a call to lookup, expect max. 1 result
        and return the value"""
        resource_df = self.lookup(
            lookup_id,
            lookup_column
        )
        if not isinstance(resource_df, pandas.DataFrame):
            return self.unknown_value
        if attribute in resource_df:
            attr_as_array = resource_df[attribute].array
            if len(attr_as_array) > 1:
                logger.debug(
                    "[!] More than 1 match for attribute %s - %s",
                    attribute,
                    attr_as_array
                )
            return str(attr_as_array[0])
        return pandas.NA

    def attribute_list(
        self,
        lookup_id: str,
        lookup_column: str,
        attribute: str
    ) -> List[str]:
        """Perform a call to lookup, convert the result (DataFrame)
        to a list and return it"""
        resource_df = self.lookup(
            lookup_id,
            lookup_column
        )
        if not isinstance(resource_df, pandas.DataFrame):
            return []
        if attribute in resource_df:
            return resource_df[attribute].to_list()
        return []

    @classmethod
    def get_from_registry(cls, type_name: str) -> 'ResourceType':
        """Get a ResourceType object from the class attribute registry"""
        type_as_lower = type_name.lower()
        if type_as_lower not in cls.registry:
            raise ValueError(f"[!] Unknown resource type: {type_name}")
        return cls.registry[type_as_lower]

    @classmethod
    def supported_types(cls) -> List[str]:
        """Return a list of supported resources"""
        return list(cls.registry.keys())
