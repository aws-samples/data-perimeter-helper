#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module hosts functions to automatically import and instanciate ResourceType class
'''
import logging
import importlib
from pathlib import (
    Path
)
from typing import (
    Dict,
    List
)


logger = logging.getLogger(__name__)


def get_available_resource_type() -> List[Dict[str, str]]:
    """Get all resource type available path"""
    # Path: ./referential/
    package_folder = Path(__file__).absolute().parent.parent
    referential_folder = package_folder / "referential"
    list_file = []
    list_file.extend(
        list(referential_folder.glob('[!_]*.py'))
    )
    # Creates a dict object with key equals to query name
    list_referential_file = []
    excluded_files = [
        'config_adv',
        'generic',
        'import_referential',
        'Referential',
        'ResourceType',
    ]
    for file in list_file:
        file_name = str(file.stem)
        if file_name in excluded_files:
            continue
        list_referential_file.append({
            "file_path": str(file),
            "file_name": file_name,
            "module_path": f"{package_folder.name}.{referential_folder.name}.{file_name}"
        })
    return list_referential_file


def instanciate_class(
    list_referential_file: List[Dict[str, str]]
) -> None:
    """Import queries from 'referential' folder, then instanciate them"""
    try:
        for file in list_referential_file:
            logger.debug("Importing: %s", str(file['module_path']))
            module = importlib.import_module(  # nosemgrep: non-literal-import
                str(file['module_path'])
            )
            getattr(module, file['file_name'])()
    except AttributeError as error:
        logger.error(  # nosemgrep: logging-error-without-handling
            "Mismatch between query name and class name - %s", error
        )
        raise ValueError(
            "Mismatch between query name and class name"
        ) from error


def auto_import() -> None:
    """Retrieves the list of query to perform based on user input"""
    referential_file = get_available_resource_type()
    instanciate_class(referential_file)
