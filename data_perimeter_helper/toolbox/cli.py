#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts CLI arguments parser
"""
import logging
import re
import argparse
from typing import (
    List
)


logger = logging.getLogger(__name__)
regex_is_accountid = re.compile(r"^\d{12}$")


def validate_args(arguments: argparse.Namespace) -> None:
    """ Validates format of CLI arguments

    :param arguments: arguments provided in the CLI
    :type arguments: argparse.Namespace
    :raises ValueError: if an argument does not comply to expected format
    :return: arguments provided in the CLI
    :rtype: argparse.Namespace
    """
    logging.debug(arguments)
    if arguments.version is True:
        return
    list_account: List[str] = arguments.list_account
    list_query: List[str] = arguments.list_query
    list_ou: List[str] = arguments.list_ou
    if len(list_query) == 0:
        raise ValueError("--list-query/-lq must be defined")
    if len(list_account) == 0 and len(list_ou) == 0:
        referential_query_present = False
        standard_query_present = False
        for query in list_query:
            if query.startswith("referential"):
                referential_query_present = True
            else:
                standard_query_present = True
                break
        if (referential_query_present is False) or (standard_query_present is True):
            raise ValueError("--list-account/-la or --list-ou/-lo must be defined")


def setup_dph_args_parser(args) -> argparse.Namespace:
    """ Parser for arguments passed to command line (CLI) for dph

    :return: List of arguments passed to command line
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Description: data perimeter helper is a tool that"
        " helps you design and anticipate the impact of your data perimeter"
        " controls by analyzing access activity in your AWS CloudTrail logs.",
        add_help=False
    )
    required_params = parser.add_argument_group('required arguments')
    optional_params = parser.add_argument_group('optional arguments')
    required_params.add_argument(
        '-lq',
        '--list-query',
        dest="list_query",
        nargs='*',
        default=[],
        help='list of queries to perform'
    )
    optional_params.add_argument(
        '-la',
        '--list-account',
        dest="list_account",
        nargs='*',
        default=[],
        help='list of AWS account IDs'
    )
    optional_params.add_argument(
        '-lo',
        '--list-ou',
        dest="list_ou",
        nargs='*',
        default=[],
        help='list of organizational unit IDs'
    )
    optional_params.add_argument(
        '-h',
        '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='show this help message and exit'
    )
    optional_params.add_argument(
        '-pq',
        '--print-query',
        dest="print_query",
        action='store_true',
        help='Boolean value, denotes if queries are printed to the standard input (stdin)'
    )
    optional_params.add_argument(
        '-pr',
        '--print-result',
        dest="print_result",
        action='store_true',
        help='Boolean value, denotes if results are printed to the standard input (stdin)'
    )
    optional_params.add_argument(
        '-er',
        '--export-referential',
        dest="export_referential",
        action='store_true',
        help='Boolean value, denotes if referential items are exported.'
    )
    optional_params.add_argument(
        '-dt',
        '--disable-thread',
        dest="disable_thread",
        action='store_true',
        help='disable threading'
    )
    supported_format = ["html", "excel", "json"]
    default_format = ["html", "excel"]
    optional_params.add_argument(
        '-ef',
        '--export-format',
        dest="list_export_format",
        nargs='+',
        choices=supported_format,
        default=default_format,
        help='export format to be used'
    )
    optional_params.add_argument(
        '-v',
        '--verbose',
        dest="verbose",
        action='store_true',
        help='enable verbose logs in console'
    )
    optional_params.add_argument(
        '-vf',
        '--variable-file',
        dest="variable_file",
        default=None,
        help='YAML variable file to use, defaults to "variables.yaml"'
    )
    optional_params.add_argument(
        '-vys',
        '--variable-yaml-section',
        dest="variable_yaml_section",
        default=None,
        help='YAML variable section file to use, defaults to "default"'
    )
    optional_params.add_argument(
        '-dphf',
        '--dph-conf-file',
        dest="dph_conf_file",
        default=None,
        help='YAML file with data perimeter helper configuration, defaults to "data_perimeter.yaml"'
    )
    optional_params.add_argument(
        '-of',
        '--output-folder',
        dest="output_folder",
        help='Output folder path for data perimeter helper results'
    )
    optional_params.add_argument(
        '--version',
        dest="version",
        action='store_true',
        help='Display data perimeter helper version'
    )
    arguments = parser.parse_args(args)
    validate_args(arguments)
    return arguments


def setup_dph_doc_args_parser(args) -> argparse.Namespace:
    """ Parser for arguments passed to the command line (CLI) for dph-doc

    :return: List of arguments passed to command line
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description="Description: you can use this helper to generate "
        "automatically data perimeter helper queries documentation.",
        add_help=False
    )
    optional_params = parser.add_argument_group('optional arguments')
    optional_params.add_argument(
        '-lq',
        '--list-query',
        dest="list_query",
        nargs='*',
        default=["all"],
        help='list of queries to document'
    )
    optional_params.add_argument(
        '-v',
        '--verbose',
        dest="verbose",
        action='store_true',
        help='enable verbose logs in console'
    )
    optional_params.add_argument(
        '--version',
        dest="version",
        action='store_true',
        help='Display data perimeter helper version'
    )
    optional_params.add_argument(
        '-h',
        '--help',
        action='help',
        default=argparse.SUPPRESS,
        help='show this help message and exit'
    )
    arguments = parser.parse_args(args)
    return arguments
