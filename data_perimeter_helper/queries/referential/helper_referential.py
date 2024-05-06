#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the helper functions specific to the referential queries
'''
import logging

import pandas


logger = logging.getLogger(__name__)


def add_column_contains_condition_resource_wildcard(
    df: pandas.DataFrame,
    column_name_policy: str
) -> None:
    """Add a column to the dataframe to denote if the column
    `column_name_policy` contains one of the following condition keys:
    aws:ResourceOrgId/OrgPaths/Account"""
    df['containsConditionKeyResource'] = df[column_name_policy].str.contains(
        r'aws:Resource(?:OrgId|OrgPaths|Account)',
        case=False,
        na=False
    )


def add_column_contains_condition_principal_wildcard(
    df: pandas.DataFrame,
    column_name_policy: str
) -> None:
    """Add a column to the dataframe to denote if the column
    `column_name_policy` contains one of the following condition keys:
    aws:PrincipalOrgId/OrgPaths/Account"""
    df['containsConditionKeyPrincipal'] = df[column_name_policy].str.contains(
        r'aws:Principal(?:OrgId|OrgPaths|Account)',
        case=False,
        na=False
    )


def add_column_contains_condition_network_perimeter(
    df: pandas.DataFrame,
    column_name_policy: str
) -> None:
    """Add a column to the dataframe to denote if the column
    `column_name_policy` contains one of the following condition keys:
    aws:SourceIp, aws:SourceVPC, aws:SourceVPCe"""
    df['containsConditionKeySourceNetwork'] = df[column_name_policy].str.contains(
        r'(aws:SourceVPC|aws:SourceVPCe|aws:SourceIP)',
        case=False,
        na=False
    )
