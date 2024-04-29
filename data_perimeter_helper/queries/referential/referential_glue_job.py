#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: referential_glue_job
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


class referential_glue_job(Query):
    """List the AWS Glue jobs inventoried in your AWS Config aggregator.   
You can use this query, for example, to review your Glue jobs that do **not** have any connection nor the special job argument `--disable-proxy-v2` set.
For details on the special job parameter `disable-proxy-v2`, see [Configuring AWS calls to go through your VPC
](https://docs.aws.amazon.com/glue/latest/dg/connection-VPC-disable-proxy.html). For details on AWS Glue connection, see [Connecting to data](https://docs.aws.amazon.com/glue/latest/dg/glue-connections.html). Note that some Glue connection do not require to configure an Amazon Virtual Private Cloud (VPC).
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::Glue::Job'
            ]
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit a query and perform data processing"""
        dataframe = Referential.get_resource_type('AWS::Glue::Job').dataframe
        assert isinstance(dataframe, pandas.DataFrame)  # nosec: B101
        return {
            "query": "",
            "dataframe": dataframe
        }
