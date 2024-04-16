#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Entry point for Data perimeter helper
Help
data_perimeter_helper -h

Examples:
data_perimeter_helper -la <ACCOUNT_ID> -lq <QUERY_NAME>
data_perimeter_helper -la <ACCOUNT_ID> -lq all
"""
# PEP 366 - Main module explicit relative imports:
# https://peps.python.org/pep-0366/
if __name__ == "__main__" and __package__ is None:
    __package__ = "data_perimeter_helper"
    import sys
    from pathlib import (
        Path
    )
    package_parent_path = str(Path(__file__).absolute().parent.parent)
    sys.path.append(package_parent_path)
    print(
        "[~] Execution outside package detected, below path has been added, "
        f"sys.path += {package_parent_path}"
    )
import logging
from typing import (
    List,
    Dict,
    Union
)
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed as concurrent_completed
)
from time import (
    perf_counter,
)

import pandas
from tqdm import (
    tqdm
)

from data_perimeter_helper.toolbox import (
    cli,
    utils,
    exporter
)
from data_perimeter_helper.queries import (
    import_query
)
from data_perimeter_helper.queries.Query import (
    Query
)
from data_perimeter_helper.referential import (
    import_referential
)
from data_perimeter_helper.referential.Referential import (
    Referential
)
from data_perimeter_helper.findings.ExternalAccessFindings import (
    ExternalAccessFindings
)
from data_perimeter_helper.variables import (
    Variables as Var
)


logger = utils.configure_logging(
    Var.logging_export_folder_path,
    Var.logging_file_name
)


def export_to_file(
    list_export_format: List[str],
    list_items: List[Dict[str, Union[str, pandas.DataFrame]]],
    account_id: str
) -> None:
    """Calls export functions based on the """
    # Sort alphabetically the performed queries
    if len(list_export_format) == 0 or len(list_items) == 0:
        return
    list_queries_name = sorted([item.get("name") for item in list_items])  # type: ignore
    list_items = sorted(
        list_items,
        key=(lambda i: list_queries_name.index(i['name']))
    )
    if "html" in list_export_format:
        exporter.export_list_dataframe_to_html(
            list_items=list_items,
            account_id=account_id
        )
    if "excel" in list_export_format:
        exporter.export_list_dataframe_to_excel(
            list_items=list_items,
            account_id=account_id
        )
    if "json" in list_export_format:
        exporter.export_list_dataframe_to_json(
            list_items=list_items,
            account_id=account_id
        )


def export_all_queries(
    list_account_id: List[str],
    df_per_account: Dict[str, List[Dict[str, Union[str, pandas.DataFrame]]]],
    list_export_format: List[str]
):
    """Calls the export functions for each type of query"""
    # Export standard queries
    for account_id in list_account_id:
        export_to_file(
            list_export_format=list_export_format,
            list_items=df_per_account[account_id],
            account_id=account_id
        )
    # Export referential queries
    referential_queries_result: List[Dict[str, Union[str, pandas.DataFrame]]] = df_per_account.get("referential", [])
    if len(referential_queries_result) > 0:
        export_to_file(
            list_export_format=list_export_format,
            list_items=referential_queries_result,
            account_id="referential"
        )


def export_referential(list_export_format: List[str]) -> None:
    """Export referential (example:, results from AWS Config advanced queries)"""
    list_dataframes: List[Dict[str, Union[str, pandas.DataFrame]]] = []
    registry = Referential.get_resource_type_registry_items()
    for resource_type, res in registry:
        if isinstance(res.dataframe, pandas.DataFrame):
            list_dataframes.append({
                'name': resource_type,
                'dataframe': res.dataframe
            })
    if len(list_dataframes) > 0:
        export_to_file(
            list_export_format=list_export_format,
            list_items=list_dataframes,
            account_id="all_referential"
        )


def query_per_account(
    # list_account_id: List[str],
    queries: Dict[str, Dict[str, Dict[str, Union[str, Query]]]],
    list_export_format: List[str]
) -> None:
    """For a given account, performs all the requested queries
    :param account_id: List of AWS account IDs
    :param list_query: List of queries to be applied
    :return: List of pandas dataframes with all queries results
    """
    Var.augment_variables()
    standard_queries = queries.get("standard", {})
    referential_queries = queries.get("referential", {})
    nb_query = (len(Var.list_account_id) * len(standard_queries)) +\
        len(referential_queries)
    df_per_account: Dict[str, List[Dict[str, Union[str, pandas.DataFrame]]]] = {}
    with tqdm(
        total=nb_query,
        desc="Nb queries performed: ", unit="Queries", position=99
    ) as pbar:
        # Manage standard queries
        for account_id in Var.list_account_id:
            df_per_account[account_id] = []
            for query_name, query_value in standard_queries.items():
                start_time = perf_counter()
                result = query_value['instance'].submit_query(  # type: ignore
                    account_id=account_id
                )
                exec_time = utils.get_elapsed_time(start_time)
                df_per_account[account_id].append(
                    {
                        'name': query_name,
                        'query': result['query'],
                        'dataframe': result['dataframe'],
                        'exec_time': exec_time
                    }
                )
                log_msg = f"Completed query `{query_name}` for account"\
                    f" {account_id} in {exec_time}"
                pbar.write(
                    utils.color_string(
                        utils.Icons.FULL_CHECK_GREEN + log_msg,
                        utils.Colors.GREEN_BOLD
                    )
                )
                logger.debug(log_msg)
                pbar.update(1)
        # Manage referential queries
        df_per_account["referential"] = []
        for query_name, query_value in referential_queries.items():
            start_time = perf_counter()
            assert isinstance(query_value['instance'], Query)  # nosec: B101
            result = query_value['instance'].submit_query(
                account_id="referential"
            )
            exec_time = utils.get_elapsed_time(start_time)
            df_per_account["referential"].append(
                {
                    'name': query_name,
                    'query': result['query'],
                    'dataframe': result['dataframe'],
                    'exec_time': exec_time
                }
            )
            log_msg = f"Completed referential query `{query_name}`"\
                f" in {exec_time}"
            pbar.write(
                utils.color_string(
                    utils.Icons.FULL_CHECK_GREEN + log_msg, utils.Colors.GREEN_BOLD
                )
            )
            logger.debug(log_msg)
            pbar.update(1)
    export_all_queries(
        list_account_id=Var.list_account_id,
        df_per_account=df_per_account,
        list_export_format=list_export_format,
    )


def query_in_parrallel(
    # list_account_id: List[str],
    queries: Dict[str, Dict[str, Dict[str, Union[str, Query]]]],
    list_export_format: List[str],
):
    """Runs queries by using threads
    Number of concurrent threads is defined in variables.py file
    :param list_account_id: List of AWS account IDs retrieved from CLI args
    :param queries: Dict with queries
    :raises exception: if a thread returns an exceptions
    """
    Referential.batch_get_resource_type(
        list_resources=Query.depends_on_resource_type
    )
    Var.augment_variables()
    df_per_account: Dict[str, List[Dict[str, Union[str, pandas.DataFrame]]]] = {}
    pool = {}
    standard_queries = queries.get("standard", {})
    referential_queries = queries.get("referential", {})
    nb_query = (len(Var.list_account_id) * len(standard_queries)) +\
        len(referential_queries)
    with tqdm(
        total=nb_query, desc="Nb queries performed: ",
        unit="Queries", position=99
    ) as pbar:
        with ThreadPoolExecutor(max_workers=Var.thread_max_worker) as executor:
            # Manage standard queries
            for account_id in Var.list_account_id:
                df_per_account[account_id] = []
                pool.update({
                    executor.submit(
                        query_value['instance'].submit_query,  # type: ignore
                        account_id
                    ): {
                        'account_id': account_id,
                        'query_name': query_name,
                        'start_time': perf_counter()
                    }
                    for query_name, query_value in standard_queries.items()
                })
            # Manage referential queries
            df_per_account["referential"] = []
            for query_name, query_value in referential_queries.items():
                assert isinstance(query_value['instance'], Query)  # nosec: B101
                pool.update({
                    executor.submit(
                        query_value['instance'].submit_query,
                        "referential"
                    ): {
                        'account_id': "referential",
                        'query_name': query_name,
                        'start_time': perf_counter()
                    }
                })
            for request_in_pool in concurrent_completed(pool):
                exception = request_in_pool.exception()
                if exception:
                    raise exception
                account_id = str(pool[request_in_pool]['account_id'])
                query_name = str(pool[request_in_pool]['query_name'])
                exec_time = utils.get_elapsed_time(
                    pool[request_in_pool]['start_time']  # type: ignore
                )
                result = request_in_pool.result()
                df_per_account[account_id].append({
                    'name': query_name,
                    'query': result['query'],
                    'dataframe': result['dataframe'],
                    'exec_time': exec_time
                })
                if account_id == "referential":
                    log_msg = f"Completed referential query `{query_name}`"\
                        f" in {exec_time}"
                else:
                    log_msg = f"Completed query `{query_name}` for account"\
                        f" {account_id} in {exec_time}"
                pbar.write(
                    utils.color_string(
                        utils.Icons.FULL_CHECK_GREEN + log_msg,
                        utils.Colors.GREEN_BOLD
                    )
                )
                logger.debug(log_msg)
                pbar.update(1)
    export_all_queries(
        list_account_id=Var.list_account_id,
        df_per_account=df_per_account,
        list_export_format=list_export_format,
    )


def init_iam_access_analyzer_external_access_findings() -> bool:
    """Initialize AWS IAM Access Analyzer external access findings if a
    requested query depends on it"""
    if Query.depends_on_iam_access_analyzer is True:
        ExternalAccessFindings()
        return True
    return False


@utils.decorator_elapsed_time(
    message="Data perimeter helper completed in: ",
    color=utils.Colors.GREEN_BOLD
)
def main(args=None) -> int:
    """Main function
    :return: 0 if succeeds
    """
    arguments = cli.setup_dph_args_parser(args)
    # Retrieve arguments that result in an exit
    if arguments.version:
        return utils.print_dph_version()
    # Set logging level if verbose enabled
    if arguments.verbose:
        utils.set_log_level(logging.DEBUG)
    logger.debug("Provided arguments: %s", arguments)
    try:
        import_referential.auto_import()
        queries = import_query.get_queries_to_perform(arguments.list_query)
        Var(arguments)
        init_iam_access_analyzer_external_access_findings()
        if arguments.disable_thread:
            logger.info("[!] Queries are not performed with threading")
            query_per_account(
                queries,
                arguments.list_export_format
            )
        else:
            logger.debug(
                "[+] Data perimeter helper uses threading with `%s` workers",
                Var.thread_max_worker
            )
            query_in_parrallel(
                queries,
                arguments.list_export_format
            )
        if arguments.export_referential:
            export_referential(list_export_format=arguments.list_export_format)
    except BaseException:
        logger.exception("[!] Fatal expection catched")  # nosemgrep: logging-error-without-handling
        raise
    return 0


if __name__ == "__main__":
    # Called when this file is directly executed
    main()
