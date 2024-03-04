#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts helper functions for Athena queries
"""
import logging
from ipaddress import (
    ip_address,
    ip_network
)
from typing import (
    Optional,
    List,
    Union,
)

import pandas

from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.toolbox import (
    utils
)
from data_perimeter_helper.referential.Referential import (
    Referential
)
from data_perimeter_helper.referential.account import (
    account
)


logger = logging.getLogger(__name__)


def is_ip_public(ip: str) -> Union[bool, None]:
    """Returns True if IP is public"""
    try:
        if ip_address(ip).is_private:  # nosemgrep: is-function-without-parentheses
            return False
    except ValueError:
        return None
    return True


def is_ip_in_cidr(ip: str, cidr: str) -> Union[bool, None]:
    """Returns True if IP is in cidr"""
    try:
        if ip_address(ip) in ip_network(cidr):
            return True
    except ValueError:
        return None
    return False


def basic_explain_network_perimeter_findings(
    is_service_role: str,
    ip: str,
    vpcendpoint: str,
    vpc_id: str
) -> str:
    """Provide a basic explanation for network perimeter findings"""
    if isinstance(ip, str) and "amazonaws.com" in ip:
        if is_service_role:
            return "Principal is a service role which performed API calls from an AWS service network"
        return "Principal performed API calls from an AWS service network"
    ip_is_public = is_ip_public(ip)
    ip_is_private = not ip_is_public
    # Public CIDR
    if ip_is_public:
        return f"Principal is performing API calls from an unexpected public IP address: ({ip})"
    # Unexpected VPC endpoint
    if ip_is_private:
        if isinstance(vpc_id, str):
            if "vpc" in vpc_id:
                return f"Principal made calls through the VPC endpoint ({vpcendpoint}) attached to a VPC ({vpc_id}) that is unexpected"
            return "Principal made calls through a VPC endpoint that is not inventoried in Config aggregator"
    return ""


def comment_injected_sql(sql: str, key: str) -> str:
    """Comment an SQL statement"""
    return f"-- START injected: {key}\n" + sql.strip("\n") + "\n  -- END"


def get_list_account_id() -> Union[None, List[str]]:
    """Get all AWS account IDs as list"""
    account_df = Referential.get_resource_type(
        resource_type="AWS::Organizations::Account"
    ).dataframe
    if isinstance(account_df, pandas.DataFrame):
        return account_df['accountid'].values.tolist()
    return None


def get_athena_all_account_contains_operator() -> Union[None, str]:
    """Get a list of all accounts as a string joined with comma"""
    list_of_accounts = get_list_account_id()
    if list_of_accounts is None:
        raise ValueError("Cannot get list of account IDs")
    p_account = [
        f"'{account}'" for account in list_of_accounts
    ]
    return ','.join(p_account)


def get_athena_date_partition() -> str:
    """Get the date to use in Athena query"""
    if Var.partition_date_regex is not None:
        return f"LIKE {Var.partition_date_regex}"
    if Var.partition_date_start is not None and Var.partition_date_end is not None:
        return f"BETWEEN '{Var.partition_date_start}' AND '{Var.partition_date_end}'"
    if Var.partition_date_interval is not None:
        return f"BETWEEN DATE_FORMAT(CURRENT_DATE - INTERVAL '{Var.partition_date_interval_value}' {Var.partition_date_interval_unit}, '%Y/%m/%d') AND DATE_FORMAT(CURRENT_DATE, '%Y/%m/%d')"
    raise ValueError(
        "[!] Date variable is not set"
    )


def get_athena_sql_limit(account_id: str) -> int:
    """Get SQL limit field"""
    try:
        list_sql_limit = Var.get_account_configuration(
            account_id=account_id,
            configuration_key="athena_sql_limit"
        )
        max_sql_limit = max([int(x) for x in list_sql_limit])
    except ValueError:
        logger.debug("[~] No SQL limit has been set")
        return 0
    if max_sql_limit is None:
        logger.debug("[~] No SQL limit has been set")
        return 0
    logger.debug(
        "[~] SQL limit: %s, account ID: %s", max_sql_limit, account_id
    )
    return max_sql_limit


def athena_cloudtrail_with_union() -> bool:
    """Return True if table UNION is needed, else False.
    Used to manage the case where 2 athena table are used,
    one with management events the other with data ones"""
    return Var.athena_cloudtrail_table_configuration == "SPLIT"


def get_athena_selected_account_vpce(
    account_id: str,
    service_name: Optional[str] = None,
    with_negation: bool = True
) -> str:
    """Get the list of VPC endpoints for a given account ID and service"""
    if service_name is None:
        result = Referential.get_resource_attribute(
            resource_type="AWS::EC2::VPCEndpoint",
            lookup_value=account_id,
            lookup_column='ownerId',
            attribute='vpcEndpointId',
            return_all_values_as_list=True
        )
    else:
        result = Referential.get_resource_attribute(
            resource_type=f"AWS::EC2::VPCEndpoint::{service_name}",
            lookup_value=account_id,
            lookup_column='ownerId',
            attribute='vpcEndpointId',
            return_all_values_as_list=True
        )
    if not isinstance(result, list) or len(result) == 0:
        return f"-- No VPC endpoint available for service: {service_name}"
    list_vpce_as_str = utils.str_sanitizer(
        "|".join(result)
    )
    if with_negation:
        return comment_injected_sql(
            f"""AND COALESCE(NOT regexp_like(vpcendpointid, {list_vpce_as_str}), True)""",
            "list_account_vpc_endpoint_id"
        )
    return comment_injected_sql(
        f"""AND regexp_like(vpcendpointid, {list_vpce_as_str})""",
        "list_account_vpc_endpoint_id"
    )


def get_athena_selected_account_principals(
    account_id: str, with_negation: bool = True
) -> str:
    """Get SQL conditions to include or exclude principals
    of a given account ID"""
    if with_negation:
        return comment_injected_sql(
            f"""AND useridentity.accountid DISTINCT FROM '{account_id}'""",
            "Current account's principals"
        )
    return comment_injected_sql(
        f"""AND useridentity.accountid = '{account_id}'""",
        "Current account's principals"
    )


def get_athena_selected_org_account_principals(
    with_negation: bool = True,
) -> Union[None, str]:
    """Get SQL conditions to include or exclude principals
    of the organization"""
    list_account_id = get_list_account_id()
    if list_account_id is None:
        return None
    comment = "Same organization principals"
    if with_negation:
        return comment_injected_sql(
            f"""AND COALESCE(NOT regexp_like(useridentity.accountid, '({"|".join(list_account_id)})'), True)""",
            comment
        )
    return comment_injected_sql(
        f"""AND regexp_like(useridentity.accountid, '({"|".join(list_account_id)})')""",
        comment
    )


def get_athena_account_org_unit_boundary(
    account_id: str,
    with_negation: bool = True,
) -> str:
    """Get SQL conditions to include/exclude calls from principals part of
    the same OU boundaries than the selected account ID"""
    # Get account ResourceType object
    account_resource_type = Referential.get_resource_type(
        resource_type="AWS::Organizations::Account"
    )
    assert isinstance(account_resource_type, account)  # nosec: B101
    # Get account's orgUnitBoundary attribute
    # The function `get_resource_attribute` returns a string representation
    # of a list
    str_account_org_unit_boundary = Referential.get_resource_attribute(
        resource_type="AWS::Organizations::Account",
        lookup_value=account_id,
        lookup_column='accountid',
        attribute='orgUnitBoundary',
    )
    no_result_comment = "-- No account ID linked to OU boundary to inject"
    if isinstance(str_account_org_unit_boundary, type(pandas.NA)):
        return no_result_comment
    assert isinstance(str_account_org_unit_boundary, str)  # nosec: B101
    list_account_org_unit_boundary = str_account_org_unit_boundary.strip(
        "[]").replace("'", "").replace(" ", "").split(",")
    list_account_id = []
    for org_unit_boundary in list_account_org_unit_boundary:
        list_account_id.extend(
            account_resource_type.get_account_in_org_unit_boundary(
                org_unit_boundary
            )
        )
    if len(list_account_id) == 0:
        return no_result_comment
    comment = "organization unit (OU) boundaries"
    if with_negation:
        return comment_injected_sql(
            f"""AND COALESCE(NOT regexp_like(useridentity.accountid, '({"|".join(list_account_id)})'), True)""",
            comment
        )
    return comment_injected_sql(
        f"""AND regexp_like(useridentity.accountid, '({"|".join(list_account_id)})')""",
        comment
    )


def athena_trino_regex_escape(item: str) -> str:
    """Escape characters used in AWS resources name
    that are interpreted by Trino"""
    item = str(item)
    item = item.replace("+", r"\+")
    item = item.replace("=", r"\=")
    item = item.replace(".", r"\.")
    return item


def get_athena_dph_configuration_cidr(
    configuration_key: str,
    list_cidr: List[str],
    params: List[str],
    with_negation: bool = True
):
    """Get SQL conditions to include or exclude the provided list of CIDRs
    ranges"""
    statement = ""
    column_name = "sourceipaddress"
    for cidr in list_cidr:
        params.append(utils.str_sanitizer(cidr))
        if with_negation:
            statement += f"AND COALESCE(NOT contains(?, \
TRY_CAST({column_name} AS IPADDRESS)), True)\n"
        else:
            statement += f"AND contains(?, TRY_CAST({column_name} \
AS IPADDRESS))\n"
    return comment_injected_sql(statement, configuration_key)


def get_athena_dph_configuration(
    account_id: str,
    configuration_key: str,
    column_name: str,
    params: List[str],
    with_negation: bool = True
) -> str:
    """Get SQL conditions to include or exclude the given trusted
    configuration extracted from the configuration file"""
    conf = Var.get_account_configuration(
        account_id=account_id,
        configuration_key=configuration_key
    )
    if isinstance(conf, (str, int)):
        conf = [conf]
    if len(conf) == 0:
        return f"-- Nothing to inject for: {configuration_key}"
    if column_name == 'sourceipaddress':
        return get_athena_dph_configuration_cidr(
            configuration_key,
            conf,
            params,
            with_negation
        )
    statement = ""
    if with_negation:
        for chunk in utils.generator_list_as_str_chunker(conf):
            value_trino = athena_trino_regex_escape(chunk)
            params.append(utils.str_sanitizer(value_trino))
            statement += f"""AND COALESCE(NOT regexp_like({column_name}, ?), True)\n"""
    else:
        or_stmt = []
        for chunk in utils.generator_list_as_str_chunker(conf):
            value_trino = athena_trino_regex_escape(chunk)
            params.append(utils.str_sanitizer(value_trino))
            or_stmt.append(f"""regexp_like({column_name}, ?)""")
        statement = f"""AND ({" OR ".join(or_stmt)})"""
    return comment_injected_sql(statement, configuration_key)
