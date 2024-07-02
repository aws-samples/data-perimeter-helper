#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the query: referential_vpce
'''
import logging
import re
import json
from typing import (
    Dict,
    Union,
)

import pandas

from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.queries.referential import (
    helper_referential
)

from data_perimeter_helper.referential.Referential import (
    Referential
)
from data_perimeter_helper.toolbox.exporter import (
    write_to_file
)
from data_perimeter_helper.variables import (
    Variables as Var
)


logger = logging.getLogger(__name__)


class referential_scp(Query):
    """List the service control policies (SCPs) in your organization.
Use this query to review your SCPs and identify policies that implement resource perimeter or network perimeter controls.
The query exports the SCPs to readable JSON files under a subfolder `scp` of your configured output folder.
You can use this query to assess and accelerate the implemention of your [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) and [**network perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls in your SCPs.
"""  # noqa: W291

    def __init__(self, name):
        self.name = name
        super().__init__(
            name,
            depends_on_resource_type=[
                'AWS::Organizations::SCP'
            ]
        )

    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Submit a query and perform data processing"""
        dataframe = Referential.get_resource_type('AWS::Organizations::SCP').dataframe
        assert isinstance(dataframe, pandas.DataFrame)  # nosec: B101
        helper_referential.add_column_contains_condition_resource_wildcard(
            dataframe,
            column_name_policy='policyDocument'
        )
        helper_referential.add_column_contains_condition_network_perimeter(
            dataframe,
            column_name_policy='policyDocument'
        )
        self.export_scp_readable_format(dataframe)
        return {
            "query": "",
            "dataframe": dataframe
        }

    def export_scp_readable_format(self, df: pandas.DataFrame) -> None:
        """Export SCPs to files in a readable format"""
        baseline_export_folder = f"{Var.result_export_folder}/scp"
        for policy_id, policy_name, policy_document, targets in zip(
            df['Id'],
            df['Name'],
            df['policyDocument'],
            df['targets']
        ):
            if len(targets) == 0:
                export_folder = f"{baseline_export_folder}/unattached/"
            else:
                export_folder = f"{baseline_export_folder}/attached/"
            file_name = re.sub(
                '[^0-9a-zA-Z]+',
                '_',
                f"{policy_id}-{policy_name}"
            )[0:120].lower()
            str_policy_document = json.dumps(
                json.loads(policy_document),
                indent=2
            )
            file_content = f"""// Name: {policy_name} | ID: {policy_id}
// Targets: {targets}
{str_policy_document}
"""
            write_to_file(
                export_folder=export_folder,
                file_name=file_name,
                file_extension="jsonc",
                content=file_content
            )
        return None
