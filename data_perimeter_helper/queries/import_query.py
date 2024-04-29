#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module hosts functions to list Query child class and automatically import and instanciate them
'''
import logging
import importlib
from pathlib import (
    Path
)
from typing import (
    Dict,
    List,
    Union
)

from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.toolbox import (
    utils
)
from data_perimeter_helper.variables import (
    Variables as Var
)


logger = logging.getLogger(__name__)


def get_available_query() -> Dict[str, Dict[str, str]]:
    """Get all queries available path"""
    # Path: ./queries/{query_type}/{query_name}
    package_folder = Path(__file__).absolute().parent.parent
    query_root_folder = package_folder / "queries"
    # Get queries subfolder {query_type}
    list_query_folder_path = [
        path
        for path in query_root_folder.iterdir()
        if path.is_dir() and path.name != '__pycache__'
    ]
    logger.debug("List of query folder: %s", list_query_folder_path)
    # For each subfolder list queries' files
    list_query_path = []
    for query_folder_path in list_query_folder_path:
        list_query_path.extend(
            list(query_folder_path.glob('[!_]*.py'))
        )
    # Creates a dict object with key equals to query name
    queries = {}
    for query_path in list_query_path:
        query_name = str(query_path.stem)
        query_parent_folder_name = str(query_path.parent.name)
        if query_name.startswith(query_parent_folder_name):
            queries[query_name] = {
                'file_path': str(query_path),
                'module_path': f"{package_folder.name}.{query_root_folder.name}.{query_parent_folder_name}.{query_name}",
                'folder_path': str(package_folder / "queries" / query_parent_folder_name),
                'type': query_parent_folder_name
            }
    return queries


def import_query(
    available_query: Dict[str, Dict[str, str]],
    list_selected_query: List[str]
) -> Dict[str, Dict[str, Dict[str, Union[str, Query]]]]:
    """Import queries from 'queries' folder, then instanciate them"""
    dict_query_instance: Dict[str, Dict[str, Dict[str, Union[str, Query]]]] = {
        "standard": {}
    }
    for standalone_query in Var.standalone_query_types:
        dict_query_instance[standalone_query] = {}
    try:
        for selected_query in list_selected_query:
            module = importlib.import_module(  # nosemgrep: non-literal-import
                str(available_query[selected_query]['module_path'])
            )
            # Instanciate the query
            query_instance = getattr(module, selected_query)(
                name=selected_query,
            )
            query_type = "standard"  # default value
            for standalone_query in Var.standalone_query_types:
                if selected_query.startswith(standalone_query):
                    query_type = standalone_query
            dict_query_instance[query_type][selected_query] = {
                'instance': query_instance,
                'folder_path': available_query[selected_query]['folder_path'],
                'type': available_query[selected_query]['type']
            }
    except AttributeError as error:
        logger.error(  # nosemgrep: logging-error-without-handling
            "Mismatch between query name and class name", error
        )
        raise ValueError(
            "Mismatch between query name and class name"
        ) from error
    return dict_query_instance


def get_queries_to_perform(
    list_user_query: list
) -> Dict[str, Dict[str, Dict[str, Union[str, Query]]]]:
    """Retrieve the list of query to perform based on user input"""
    available_query = get_available_query()
    list_valid_query_name = list(available_query.keys())
    list_selected_query = []
    if 'all' in list_user_query:
        list_selected_query = list_valid_query_name
    else:
        for query_name in list_user_query:
            list_selected_query.extend(
                [
                    valid_query
                    for valid_query in list_valid_query_name
                    if query_name in valid_query
                ]
            )
        list_selected_query = list(set(list_selected_query))
    nb_selected_query = len(list_selected_query)
    if nb_selected_query == 0:
        raise ValueError(
            f"No valid query selected, provided queries: {list_user_query} - "
            f"valid queries: {list_valid_query_name}"
        )
    queries = import_query(available_query, list_selected_query)
    str_selected_query = ' | '.join(list_selected_query)
    if nb_selected_query > 1:
        msg = f"{nb_selected_query} data perimeter helper queries selected: {str_selected_query}"
    else:
        msg = f"{nb_selected_query} data perimeter helper query selected: {str_selected_query}"
    logger.debug(msg)
    print(utils.Icons.HAND_POINTING + msg)
    return queries
