#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: referential_sagemaker_notebook
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


class referential_sagemaker_notebook(Query):
    """List the Amazon SageMaker notebooks inventoried in your AWS Config aggregator.   
You can use this query, for example, to review your notebook instances that allow *direct internet access*.
For details on the direct internet access configuration, see [Connect a Notebook Instance in a VPC to External Resources](https://docs.aws.amazon.com/sagemaker/latest/dg/appendix-notebook-and-internet-access.html).
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::SageMaker::NotebookInstance'
            ]
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit a query and perform data processing"""
        dataframe = Referential.get_resource_type(
            'AWS::SageMaker::NotebookInstance'
        ).dataframe
        assert isinstance(dataframe, pandas.DataFrame)  # nosec: B101
        return {
            "query": "",
            "dataframe": dataframe
        }
