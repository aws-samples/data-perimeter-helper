#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module hosts a template of data perimeter helper queries
To add a new query, copy/paste this template file
- The class name must match the file name
- Query must inherit from the class `Query`
'''
import logging
from typing import (
    Dict,
    Union,
    List,
    Tuple
)

import pandas

from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.queries import (
    helper
)
from data_perimeter_helper.queries.Query import (
    Query
)


logger = logging.getLogger(__name__)


class query_name_replace_me(Query):
    """Add the description of your query here
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        logger.debug("[~] Query: %s, has been initialized", name)
        super().__init__(
            name=name,
            # Adapt list to needed items from referential
            depends_on_resource_type=[
                'AWS::IAM::Role',
                'AWS::Organizations::Account'
            ],
            # Set to True if your query depends on IAM Access Analyzer external access findings.
            depends_on_iam_access_analyzer=False,
            # Set the variable `use_split_table`:
            #   - If you store CloudTrail management events and data events in two different buckets:
            #     -	Set `use_split_table = True` if you want to analyze data events as part of your query.
            #     -	Set `use_split_table = False` if the analyzed services do not support data events or you do not want to analyze data events.
            #   - If you store all CloudTrail logs in one bucket:
            #     -	Set `use_split_table = False`.
            use_split_table=False,
        )

    def generate_athena_statement(
        self,
        account_id: str
    ) -> Union[None, Tuple[str, List[str]]]:
        """Generate an Athena SQL query"""
        params: List[str] = []
        # Adapt this Athena query to your need.
        # If you inject variables using f-string interpolation
        # in the variable `statement` you need to initialize them in the same
        # order as they appear in the query.
        statement = f"""-- Query: {self.name} | {account_id}
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    vpcendpointid,
    sourceipaddress
"""   # nosec B608
        return statement, params

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit an Athena SQL query and perform data processing"""
        athena_query, result = self.submit_athena_query(
            self.name, account_id
        )
        if len(result.index) == 0:
            logger.debug("[~] No result retrieved - DataFrame is empty")
            return {
                "query": athena_query,
                "dataframe": result
            }
        # Add here post-Athena query data processing
        #################################
        #################################
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
