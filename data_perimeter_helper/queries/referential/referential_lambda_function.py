#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: referential_lambda_function
'''
import logging
from typing import (
    Dict,
    Union,
)

import pandas

from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.referential.Referential import (
    Referential
)


logger = logging.getLogger(__name__)


class referential_lambda_function(Query):
    """List all AWS Lambda functions inventoried in your AWS Config aggregator.   
You can use this query, for example, to review your Lambda functions that are **not** connected to your  Virtual Private Cloud (VPC).
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::Lambda::Function'
            ],
            use_split_table=False
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit an Athena SQL query and perform data processing"""
        dataframe = Referential.get_resource_type('AWS::Lambda::Function').dataframe
        assert isinstance(dataframe, pandas.DataFrame)  # nosec: B101
        return {
            "query": "",
            "dataframe": dataframe
        }
