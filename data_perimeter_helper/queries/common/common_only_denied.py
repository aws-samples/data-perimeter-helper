#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: common_only_denied
'''
import logging
from typing import (
    Dict,
    Union,
    Tuple,
    List
)

import pandas

from data_perimeter_helper.queries import (
    helper
)
from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.queries.Query import (
    Query
)


logger = logging.getLogger(__name__)


class common_only_denied(Query):
    """List AWS API calls with an access denied error code.
You can use this query to troubleshoot access denied error messages after deployment of your data perimeter controls.
    """  # noqa: W291
    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=None,
            use_split_table=True
        )

    def generate_athena_statement(
        self,
        account_id: str
    ) -> Union[None, Tuple[str, List[str]]]:
        """Generate the Athena SQL query"""
        params: List[str] = []
        statement = f"""-- Query: {self.name} | {account_id}
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    errorcode,
    errormessage,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Keep only API calls with access denied error code.
    AND errorcode in ('Client.UnauthorizedOperation', 'Client.InvalidPermission.NotFound', 'Client.OperationNotPermitted', 'AccessDenied')
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    errorcode,
    errormessage,
    sourceipaddress,
    vpcendpointid
"""  # nosec B608
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
        self.add_column_is_assumable_by(result)
        self.add_column_is_service_role(result)
        self.add_column_is_service_linked_role(result)
        logger.debug("[~] Writing parameters [controlType && findings]")
        result['controlType'] = "All"
        result['findings'] = "Principal performed API calls with an access denied error message"
        if Var.print_result:
            logger.info(result)
        return {
            "query": athena_query,
            "dataframe": result
        }
