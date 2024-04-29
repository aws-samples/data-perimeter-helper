#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: referential_service_role
'''
import logging
from typing import (
    Dict,
    Union,
)

import pandas

from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.referential.Referential import (
    Referential
)


logger = logging.getLogger(__name__)


class referential_service_role(Query):
    """List the service roles inventoried in your AWS Config aggregator.
You can use this query, for example, to review your service roles and check if the correct tagging strategy is in place.
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::IAM::Role',
                'AWS::Organizations::Account'
            ],
            use_split_table=False
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit a query and perform data processing"""
        dataframe = Referential.get_resource_type("AWS::IAM::Role").dataframe
        assert isinstance(dataframe, pandas.DataFrame)  # nosec: B101
        # Remove principals that are not service roles
        dataframe = dataframe.drop(
            dataframe[
                dataframe['isServiceRole'].isin([False, 'False'])
            ].index
        )
        # Keep only relevant columns
        simplified_df = dataframe[
            [
                'accountId', 'roleId', 'arn', 'listTags',
                'allowedPrincipalList'
            ]
        ]
        if Var.print_result:
            logger.info(simplified_df)
        return {
            "query": "",
            "dataframe": simplified_df
        }
