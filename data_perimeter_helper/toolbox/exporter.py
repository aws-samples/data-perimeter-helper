#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts functions to export data to HTML, Excel or JSON files
"""
import logging
import re
import json
from datetime import (
    datetime
)
from typing import (
    Union,
    Tuple,
    Optional,
    List,
    Dict
)

import pandas
from jinja2 import (
    Environment,
    FileSystemLoader
)

from data_perimeter_helper.toolbox import utils
from data_perimeter_helper.variables import (
    Variables as Var
)


logger = logging.getLogger(__name__)


def write_to_file(
    export_folder: str,
    file_name: str,
    file_extension: str,
    content: str
) -> bool:
    """Write a given content to a given file in a given folder

    :param export_folder: Folder name to write file to (example:, "./outputs/")
    :param file_name: File name to write content to
    :param content: Content to write
    :return: True if write has succeed
    """
    if export_folder is None:
        return False
    if not export_folder.endswith('/'):
        export_folder = f"{export_folder}/"
    utils.create_folder(export_folder)
    full_path = f"{export_folder}{file_name}.{file_extension}"
    logger.debug(
        "[~] Exporting dataframes as %s file to [%s]",
        file_extension, full_path
    )
    try:
        with open(full_path, 'w', encoding="utf-8") as file:
            file.write(
                content
            )
            log = utils.color_string(
                f"Outputs exported as `{file_extension}` file to [{full_path}]",
                utils.Colors.GREEN_BOLD
            )
            logger.debug(log)
            print(utils.Icons.FULL_CHECK_GREEN + log)
    except PermissionError:
        logger.error(
            "Permission error while exporting file [%s]",
            full_path
        )
        return False
    return True


def render_jinja_template(
    template_name: str,
    context: dict
):
    """Render a Jinja2 template"""
    environment = Environment(  # nosemgrep: direct-use-of-jinja2
        loader=FileSystemLoader(
            str(Var.package_path / "toolbox" / "templates/")
        ),
        autoescape=True
    )
    template = environment.get_template(template_name)
    return template.render(  # nosemgrep: direct-use-of-jinja2
        context
    )


def export_queries_documentation(
    list_query_doc: list,
    export_folder: str,
    file_name: str = "README.auto.local",
    file_extension: str = "md"
) -> None:
    """Export queries documentation to markdown"""
    context = {
        "list_query_doc": list_query_doc
    }
    content = render_jinja_template(
        "readme_query.j2.md",
        context
    )
    write_to_file(
        export_folder=export_folder,
        file_name=file_name,
        file_extension=file_extension,
        content=content
    )
    return None


def export_list_dataframe_to_html(
    list_items: list,
    account_id: Union[str, None],
    return_html: bool = False,
    write_export_to_file: bool = True,
) -> Union[str, None]:
    """Export a list of dataframes to a HTML file"""
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    context = {
        "title": f"Data perimeter helper - {account_id}",
        "date": current_date,
        "list_table": list_items
    }
    html_content = render_jinja_template(
        "data_perimeter_helper.j2.html",
        context
    )
    if write_export_to_file:
        if account_id is not None:
            write_to_file(
                export_folder=Var.result_export_folder,
                file_name=f"{account_id}_data_perimeter",
                file_extension="html",
                content=html_content
            )
    if return_html:
        return html_content
    return None


def excel_convert_date_type(df: pandas.DataFrame) -> None:
    """Convert date types for Excel exports"""
    date_columns = df.select_dtypes(
        include=['datetime64[ns, UTC]']  # type: ignore
    ).columns
    for date_column in date_columns:
        df[date_column] = df[date_column].dt.date


def write_dataframe_to_excel(
    writer: pandas.ExcelWriter,
    query_name: str,
    dataframe: pandas.DataFrame,
    freeze_pane: Tuple[int, int] = (1, 1)
) -> None:
    """Export a dataframe to Excel"""
    sheet_name = re.sub('[^0-9a-zA-Z]+', '_', query_name)[0:30]
    df = dataframe.copy()
    excel_convert_date_type(df)
    df.to_excel(
        writer,
        sheet_name=sheet_name,
        index=False,
        freeze_panes=freeze_pane
    )


def export_list_dataframe_to_excel(
    list_items: list,
    account_id: str,
    export_folder: Optional[str] = None,
) -> bool:
    """
    Exports a list of dataframes to an Excel file
    """
    export_folder = export_folder or Var.result_export_folder
    if not export_folder.endswith('/'):
        export_folder = f"{export_folder}/"
    utils.create_folder(export_folder)
    full_path = f"{export_folder}{account_id}_data_perimeter.xlsx"
    logger.debug("[~] Exporting dataframes as Excel file to [%s]", full_path)
    list_sql_queries: List[Dict[str, str]] = []
    try:
        with pandas.ExcelWriter(full_path) as writer:
            for item in list_items:
                write_dataframe_to_excel(
                    writer,
                    item['name'],
                    item['dataframe']
                )
                if 'query' in item:
                    list_sql_queries.append({
                        "QueryName": item['name'],
                        "AthenaSQLQuery": item['query'],
                        "ExecTime": item.get('exec_time')
                    })
            if len(list_sql_queries) > 0:
                write_dataframe_to_excel(
                    writer,
                    "sql_queries",
                    pandas.DataFrame(list_sql_queries)
                )
        log = utils.color_string(
            f"Outputs exported as `excel` file to [{full_path}]",
            utils.Colors.GREEN_BOLD
        )
        logger.debug(log)
        print(utils.Icons.FULL_CHECK_GREEN + log)
        return True
    except PermissionError:
        logger.error(
            "[!] Permission error while exporting file [%s]. "
            "Close the file to allow export.",
            full_path
        )
        logger.info("[!] Skipping export for [%s]", full_path)
        return False


def write_dataframe_to_json(
    export_folder: str,
    account_id: str,
    query_name: str,
    query: str,
    exec_time: str,
    dataframe: pandas.DataFrame
) -> None:
    """Write a pandas Dataframe to a JSON file"""
    file_name = re.sub(
        '[^0-9a-zA-Z]+',
        '_',
        f"{account_id}_{query_name}"
    )[0:120].lower()
    df_as_dict = dataframe.to_dict(orient='records')
    extra_dict: Dict[str, Union[str, List[dict]]] = {
        'QueryResults': df_as_dict
    }
    if query is not None:
        extra_dict['AthenaSQLQuery'] = query
        extra_dict['ExecTime'] = exec_time
    write_to_file(
        export_folder=export_folder,
        file_name=file_name,
        file_extension="json",
        content=json.dumps(extra_dict)
    )


def export_list_dataframe_to_json(
    list_items: list,
    account_id: str,
    export_folder: Optional[str] = None,
) -> None:
    """Exports a list of DataFrames to json files"""
    export_folder = export_folder or f"{Var.result_export_folder}/json/"
    if not export_folder.endswith('/'):
        export_folder = f"{export_folder}/"
    utils.create_folder(export_folder)
    for item in list_items:
        write_dataframe_to_json(
            export_folder,
            account_id,
            item['name'],
            item.get('query'),
            item.get('exec_time'),
            item['dataframe']
        )


def write_dataframe_to_parquet(
    dataframe: pandas.DataFrame,
    export_folder: str,
    file_name: str,
    file_extension: str = "parquet"
) -> str:
    """Write a pandas Dataframe to a parquet file"""
    utils.create_folder(export_folder)
    file_name = re.sub(
        '[^0-9a-zA-Z]+',
        '_',
        file_name
    )[0:120].lower()
    path = f"{export_folder}{file_name}.{file_extension}"
    dataframe.to_parquet(
        path=path,
        compression='gzip'
    )
    return path
