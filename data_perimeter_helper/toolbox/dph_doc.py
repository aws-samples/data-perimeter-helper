#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module implements the functions to generate automatically data perimeter helper query documentation in README files
'''
import logging
import re
import inspect
from typing import (
    List,
    Dict,
    Union
)
from collections import (
    OrderedDict
)

from data_perimeter_helper.queries import (
    import_query
)
from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.toolbox import (
    cli,
    utils,
    exporter
)
from data_perimeter_helper.variables import (
    Variables as Var
)


WHERE_DOCUMENTATION = {
    "{network_perimeter_expected_public_cidr}": "Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).",
    "{network_perimeter_expected_vpc_endpoint}": "Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).",
    "{network_perimeter_trusted_account}": "Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).",
    "{network_perimeter_trusted_principal_arn}": "Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).",
    "{network_perimeter_trusted_principal_id}": "Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).",
    "{identity_perimeter_trusted_account}": "Remove API calls made by principals belonging to identity perimeter trusted accounts - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_account` parameter).",
    "{identity_perimeter_trusted_principal_arn}": "Remove API calls made by identity perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_principal` parameter).",
    "{identity_perimeter_trusted_principal_id}": "Remove API calls made by identity perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_principal` parameter).",
    "{resource_perimeter_trusted_bucket_name}": "Remove API calls made on trusted S3 buckets - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_bucket_name` parameter).",
    "{resource_perimeter_trusted_principal_arn}": "Remove API calls made by resource perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_principal` parameter).",
    "{resource_perimeter_trusted_principal_id}": "Remove API calls made by resource perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_principal` parameter).",
    "{remove_org_account_principals}": "Remove API calls made by principals belonging to the same AWS organization as the selected account - list of account ID retrieved from AWS Organizations.",
    "{keep_selected_account_s3_bucket}": "Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator.",
    "{remove_selected_account_org_unit_boundary}": "Remove API calls from principals belonging to the same OU boundary.",
    "{keep_selected_account_principal}": "Keep only API calls made by principals in the selected account.",
    "{remove_selected_account_vpce}": "Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.",
    "{keep_selected_account_vpce}": "Keep API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.",
    "p_account in ({helper.get_athena_all_account_contains_operator()})": "Keep API calls on all AWS accounts in the AWS organization.",
    "AND eventsource = 's3.amazonaws.com'": "Keep only S3 API calls.",
    "AND eventsource = 'sns.amazonaws.com'": "Keep only SNS API calls.",
    "AND vpcendpointid IS NULL": "Remove API calls made through VPC endpoints - `vpcendpointid` field in CloudTrail log is `NULL`.",
    "AND vpcendpointid IS NOT NULL": "Keep only API calls made through a VPC endpoint.",
    "AND COALESCE(NOT regexp_like(sourceipaddress, ':'), True)": "Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.",
    "AND COALESCE(NOT regexp_like(sourceipaddress, '(?i)(:|amazonaws|Internal)'), True)": [
        "Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.",
        "Remove API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`."
    ],
    "AND regexp_like(sourceipaddress, '(?i)(amazonaws|Internal)')": "Keep only API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.",
    "AND COALESCE(NOT regexp_like(sourceipaddress, '(?i)(amazonaws|Internal)'), True)": "Remove API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.",
    "AND COALESCE(NOT regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)'), True)": "Remove API calls made by service-linked roles in the selected account.",
    "AND regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)')": "Keep only API calls made by service-linked roles in the selected account - `useridentity.sessioncontext.sessionissuer.arn` field in CloudTrail log contains `:role/aws-service-role/`. For cross-account API calls, the field `useridentity.sessioncontext.sessionissuer.arn` IS NULL, therefore, you need to run this query in each account you would like to analyze.",
    "AND useridentity.principalid != 'AWSService'": "Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.",
    "AND COALESCE(NOT regexp_like(useridentity.accountid, '(?i)(anonymous)'), True)": "Remove unauthenticated calls.",
    "AND errorcode IS NULL": "Remove API calls with errors.",
    "AND errorcode in ('Client.UnauthorizedOperation', 'Client.InvalidPermission.NotFound', 'Client.OperationNotPermitted', 'AccessDenied')": "Keep only API calls with access denied error code.",
    "AND JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') IS NOT NULL": "Remove S3 API calls without a bucket name in the request parameters (example: s3:ListAllMyBuckets) - for these API calls the requestparameters.bucketName field in CloudTrail logs is NULL.",
    "AND useridentity.type = 'AssumedRole'": "Keep only API calls performed by assumed roles.",
    "{helper_s3.athena_remove_s3_event_name_at_account_scope()}": "Remove API calls at the account scope, such API calls are not applied to resources not owned by the selected account.",
    "AND COALESCE(NOT regexp_like(requestparameters, ':{account_id}:storage-lens|{account_id}.s3-control'), True)": "Remove API calls with the selected account ID in the request parameters (example: GetStorageLensConfiguration).",
    "AND unnested_resources.type IS DISTINCT FROM 'AWS::S3::Object'": "Remove the unnested values of the `resources` field in CloudTrail with `resource.type`=`AWS::S3::Object`. Another unnested row exists with `resources.type`=`AWS::S3::Bucket` and `resources.accountid` distinct from NULL.",
    "AND COALESCE(unnested_resources.accountid NOT IN ({list_all_account_id}), True)": "Remove API calls on S3 buckets owned by accounts belonging to the same AWS organization as the selected account.",
    "AND eventname != 'PreflightRequest'": "Remove preflight requests which are unauthenticated and used to determine the cross-origin resource sharing (CORS) configuration."
}

WHERE_SKIP_DOCUMENTATION = [
    "p_account = '{account_id}'",
    "AND p_date {helper.get_athena_date_partition()}"
]

STANDARD_SUBMIT_QUERY = """    def submit_query(
        self,
        account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        \"\"\"Submit an Athena SQL query and perform data processing\"\"\"
        athena_query, result = self.submit_athena_query(
            self.name, account_id
        )
        if len(result.index) == 0:
            logger.debug("[~] No result retrieved - DataFrame is empty")
            return {
                "query": athena_query,
                "dataframe": result
            }"""

DATA_PROCESSING_DOCUMENTATION = {
    "result = self.remove_all_resource_exception(": "Remove resource specific exceptions.",
    "result = self.remove_calls_by_service_linked_role(result)": "Remove API calls made by service-linked roles inventoried in AWS Config aggregator.",
    "result = self.remove_calls_from_service_on_behalf_of_principal(": """Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.""",
    "result = self.remove_expected_vpc_id(": "Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).",
    "result = helper_s3.remove_call_on_bucket_in_organization(result)": "Remove API calls on S3 buckets inventoried in AWS Config aggregator.",
}

ADD_COLUMN_DOCUMENTATION = {
    "self.add_column_vpc_id(result)": "vpcId",
    "self.add_column_vpce_account_id(result)": "vpceAccountId",
    "self.add_column_is_assumable_by(result)": "isAssumableBy",
    "self.add_column_is_service_role(result)": "isServiceRole",
    "self.add_column_is_service_linked_role(result)": "isServiceLinkedRole",
}

logger = utils.configure_logging(
    Var.logging_export_folder_path,
    Var.logging_file_name
)


def quality_gate_expected_instruction_present(
    query_name: str,
    set_instruction: set,
    set_expected_instruction: set
) -> None:
    """Check if any element of set `set_expected_instruction`
    is present in `set_instruction`. If yes, ensure that all items are
    present."""
    if any(
        instruction in set_expected_instruction
        for instruction in set_instruction
    ):
        for instruction in set_expected_instruction:
            if instruction not in set_instruction:
                if "trusted_account" in instruction and "scp" in query_name:
                    continue
                logger.warning(
                    "[query: %s] The `%s` instruction is missing in the"
                    " WHERE clause",
                    query_name, instruction
                )


def detect_anomalies_where_clause(
    query_name: str,
    list_where_processed: List[str]
) -> None:
    """Detect anomalies in the WHERE clause"""
    list_instruction = []
    for filter in list_where_processed:
        if filter.startswith("--"):
            continue
        list_instruction.append(filter)
    set_instruction = set(list_instruction)
    # Network perimeter trusted identities
    set_network_perimeter_trusted_identities = {
        "{network_perimeter_trusted_account}",
        "{network_perimeter_trusted_principal_arn}",
        "{network_perimeter_trusted_principal_id}"
    }
    quality_gate_expected_instruction_present(
        query_name, set_instruction, set_network_perimeter_trusted_identities
    )
    # Identity perimeter trusted identities
    set_identity_perimeter_trusted_identities = {
        "{identity_perimeter_trusted_account}",
        "{identity_perimeter_trusted_principal_arn}",
        "{identity_perimeter_trusted_principal_id}"
    }
    quality_gate_expected_instruction_present(
        query_name, set_instruction, set_identity_perimeter_trusted_identities
    )


def add_where_documentation(
    query_name: str,
    instruction: str,
    inline_comment: str,
    where_documentation: List[str]
):
    """Get expected documentation for an instruction and check inline comment"""
    expected_doc = WHERE_DOCUMENTATION[instruction]
    if isinstance(expected_doc, str):
        if inline_comment != "" and inline_comment != expected_doc:
            logger.debug(
                "[query: %s] Last inline comment [%s] does not match"
                " expected documentation [%s]",
                query_name, inline_comment, expected_doc
            )
            print("Inline comment mismatch")
            print(f"Query   : {query_name}")
            print(f"Current : {inline_comment}")
            print(f"Expected: {expected_doc}")
            print("======")
        where_documentation.append(expected_doc)
    elif isinstance(expected_doc, list):
        where_documentation.extend(expected_doc)


def parse_where_clause(query_name: str, where_clause: str) -> List[str]:
    """Parse the WHERE clause of a Query Athena SQL statement"""
    list_where = where_clause.split("\n")
    list_where_processed = [
        where_filter.strip() for where_filter in list_where
    ]
    where_documentation: List[str] = []
    inline_comment = ""
    skip_multiline = False
    multiline_instruction = ""
    detect_anomalies_where_clause(query_name, list_where_processed)
    for instruction in list_where_processed:
        if instruction.startswith("--"):
            skip_multiline = False
            if len(multiline_instruction) > 0:
                add_where_documentation(
                    query_name, multiline_instruction, inline_comment,
                    where_documentation
                )
                multiline_instruction = ""
            inline_comment = instruction.replace("--", "").strip()
            if not inline_comment.endswith("."):
                inline_comment = f"{inline_comment}."
            continue
        if skip_multiline is True:
            logger.debug("Skipping multiline: %s", instruction)
            multiline_instruction += instruction
            continue
        if instruction in WHERE_SKIP_DOCUMENTATION:
            continue
        if instruction.endswith("("):
            multiline_instruction = instruction
            skip_multiline = True
        elif instruction in WHERE_DOCUMENTATION:
            add_where_documentation(
                query_name, instruction, inline_comment, where_documentation
            )
        else:
            logger.info(
                "[query: %s] This clause is not documented: %s",
                query_name, instruction
            )
    # Remove duplicate while keeping order
    # OrderedDict is used for compatibility with Python 3.5 and older versions
    return list(OrderedDict.fromkeys(where_documentation))


def parse_data_processing(data_processing: str) -> tuple[List[str], List[str]]:
    """Parse the data processing of a Query Athena SQL statement"""
    data_processing_doc: List[str] = []
    list_add_column: List[str] = []
    only_in_data_processing_doc: List[str] = []
    list_instruction = data_processing.split("\n")
    list_instruction_processed = [
        instruction.strip() for instruction in list_instruction
    ]
    for instruction in list_instruction_processed:
        if instruction in DATA_PROCESSING_DOCUMENTATION:
            data_processing_doc.append(
                DATA_PROCESSING_DOCUMENTATION[instruction]
            )
        if "add_column" in instruction:
            if instruction in ADD_COLUMN_DOCUMENTATION:
                list_add_column.append(ADD_COLUMN_DOCUMENTATION[instruction])
    if len(list_add_column) > 0:
        list_add_column = [f"`{add_column}`" for add_column in list_add_column]
        str_added_column = ", ".join(list_add_column)
        only_in_data_processing_doc.append(
            f"Following columns are injected to ease analysis: {str_added_column}."
        )
    return data_processing_doc, only_in_data_processing_doc


def document_where_clause(
    query_name: str,
    source_generate_athena_statement: str
) -> List[str]:
    """Document the WHERE clause of a Query Athena SQL statement"""
    where_clause_find = re.findall(
        r"WHERE(.*)GROUP BY",
        source_generate_athena_statement, flags=re.DOTALL
    )
    if where_clause_find:
        where_clause = where_clause_find[0].strip()
        return parse_where_clause(query_name, where_clause)
    else:
        raise ValueError(
            f"WHERE clause not found for query: {query_name}"
        )


def extract_athena_query(
    query_name: str,
    source_generate_athena_statement: str
) -> str:
    """Extract the Athena SQL statement from a Query"""
    sql_query_find = re.findall(
        r"SELECT.*\"\"\"",
        source_generate_athena_statement, flags=re.DOTALL
    )
    if sql_query_find:
        return sql_query_find[0].strip().strip('"').strip()
    else:
        raise ValueError(f"SQL query not found for query: {query_name}")


def document_athena_query(query: Query):
    """Document an Athena SQL statement of a Query"""
    source_generate_athena_statement = inspect.getsource(
        query.generate_athena_statement
    )
    query_name = query.name
    # Get the WHERE clause documentation
    where_documentation = document_where_clause(
        query_name, source_generate_athena_statement
    )
    # Extract the Athena SQL query
    sql_query = extract_athena_query(
        query_name, source_generate_athena_statement
    )
    return where_documentation, sql_query


def manage_data_processing(query: Query) -> tuple[List[str], List[str]]:
    """Extract the data processing from code and
    call the parsing function"""
    source_submit_query = inspect.getsource(
        query.submit_query
    )
    data_processing_find = source_submit_query.replace(
        STANDARD_SUBMIT_QUERY, ""
    )
    data_processing_doc, only_in_data_processing_doc = parse_data_processing(
        data_processing_find
    )
    return data_processing_doc, only_in_data_processing_doc


def generate_query_documentation(
    query: Query,
    query_type: str
) -> Dict[str, Union[str, List[str]]]:
    """Generate the documentation for a Query Athena SQL statement
    :param query: Query instance
    :param query_type: Type of the query
    :return: Dictionary with the documentation information
    The dictionary has the following keys:
    - query_name: Name of the query
    - description: Description of the query
    - sql_query: SQL query of the query
    - where_documentation: List of the documentation of the WHERE clause
    - data_processing_documentation: List of the documentation of the
    data processing"""
    query_name = query.name
    if query_type == "referential":
        where_documentation = []
        sql_query = ""
        data_processing_documentation: List[str] = []
        only_in_data_processing_doc: List[str] = []
    else:
        where_documentation, sql_query = document_athena_query(
            query
        )
        data_processing_documentation, only_in_data_processing_doc = \
            manage_data_processing(query)
    docstring = query.__doc__
    if docstring is None:
        docstring = "No description has been provided for this query, please update your query class with a docstring"
    documentation: Dict[str, Union[str, List[str]]] = {
        'query_name': query_name,
        'description': docstring,
        'sql_query': sql_query,
        'where_documentation': where_documentation,
        'data_processing_documentation': data_processing_documentation,
        'only_in_data_processing_doc': only_in_data_processing_doc,
    }
    return documentation


def document_all_queries(selected_queries: List[str]) -> Dict[str, Dict[str, Union[str, List[Dict[str, Union[str, List[str]]]]]]]:
    """Generate the documentation for all the queries
    :param selected_queries: List of the selected queries to document
    :return: Dictionary with the query type as key and a dict with the
    documentation information as value.
    The last dict with the documentation has the following keys:
    - list_documentation: List of all the documentation dictionaries
    - export_folder: Folder path where to export the documentation to
    """
    queries = import_query.get_queries_to_perform(selected_queries)
    standard_queries = queries.get('standard', {})
    referential_queries = queries.get('referential', {})
    all_queries_flat = {**standard_queries, **referential_queries}
    doc_query_type: Dict[str, Dict[str, Union[str, List[Dict[str, Union[str, List[str]]]]]]] = {}
    for query_value in all_queries_flat.values():
        query_type = query_value['type']
        assert isinstance(query_type, str)  # nosec: B101
        assert isinstance(query_value['folder_path'], str)  # nosec: B101
        if query_type not in doc_query_type:
            doc_query_type[query_type] = {
                'list_documentation': [],
                'export_folder': query_value['folder_path'],
            }
        assert isinstance(query_value['instance'], Query)  # nosec: B101
        doc_query_type[query_type]['list_documentation'].append(  # type: ignore
            generate_query_documentation(
                query_value['instance'],
                query_type
            )
        )
    return doc_query_type


def export_documentation(doc_query_type: Dict[str, Dict[str, Union[str, List[Dict[str, Union[str, List[str]]]]]]]):
    """Loop over each query type and export the generated documentation"""
    for query_type_value in doc_query_type.values():
        assert isinstance(query_type_value, dict)  # nosec: B101
        assert isinstance(query_type_value['list_documentation'], list)  # nosec: B101
        assert isinstance(query_type_value['export_folder'], str)  # nosec: B101
        exporter.export_queries_documentation(
            list_query_doc=query_type_value['list_documentation'],
            export_folder=query_type_value['export_folder']
        )


@utils.decorator_elapsed_time(
    message="dph_doc completed in: ",
    color=utils.Colors.GREEN_BOLD
)
def main(args=None) -> int:
    """Main function for dph_doc"""
    arguments = cli.setup_dph_doc_args_parser(args)
    # Set logging level if verbose enabled
    if arguments.verbose:
        utils.set_log_level(logging.DEBUG)
    if arguments.version:
        return utils.print_dph_version()
    # Get the documentation for all the queries
    doc_query_type = document_all_queries(arguments.list_query)
    # Export the documentation to markdown files
    export_documentation(doc_query_type)
    return 0
