#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts shared utils functions
"""
import logging
import re
import math
from os import (
    makedirs,
    environ as environment_variables
)
from time import (
    perf_counter,
    gmtime,
    strftime
)
from functools import (
    wraps
)
from logging.handlers import (
    RotatingFileHandler
)
from typing import (
    Union,
    Dict,
    List,
    Set,
    Callable,
    Optional,
    Generator,
)

from data_perimeter_helper.referential.Referential import Referential
from data_perimeter_helper.referential.account import account

import yaml
import pandas
from yaml.composer import (
    ComposerError
)

from data_perimeter_helper import (
    __version__
)
from data_perimeter_helper.queries import helper


logger = logging.getLogger(__name__)
regex_str_sanitizer = re.compile(r"[^\w\*/\-_\+\=\,\@\_\:\.\|\[\]\{\}\\]")


class Colors:
    """Basic colors"""
    GREY = "\x1b[38;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    RED_BOLD = "\x1b[31;1m"
    GREEN_BOLD = "\x1b[32;1m"
    RESET = "\x1b[0m"


class Icons:
    """Basic icons"""
    FULL_CHECK_GREEN = "✅ "
    HAND_POINTING = "👉 "
    WARNING = "⚠️ "
    ERROR = "❌ "
    SPARKLE = "✨ "
    INFO = "🛈 "


class FancyLogFormatter(logging.Formatter):
    """Logging formatter that supports color for console output"""

    def __init__(self, log_fmt: str, datefmt: str, use_color: bool = True):
        super().__init__(
            fmt=log_fmt,
            datefmt=datefmt
        )
        self.use_color = use_color
        log_fmt_warning = log_fmt.replace(
            "%(message)s", f" {Icons.WARNING} %(message)s"
        )
        log_fmt_error = log_fmt.replace(
            "%(message)s", f" {Icons.ERROR} %(message)s"
        )
        self.FORMATS = {
            logging.DEBUG: Colors.GREY + log_fmt + Colors.RESET,
            logging.INFO: Colors.GREY + log_fmt + Colors.RESET,
            logging.WARNING: Colors.YELLOW + log_fmt_warning + Colors.RESET,
            logging.ERROR: Colors.RED + log_fmt_error + Colors.RESET,
            logging.CRITICAL: Colors.RED_BOLD + log_fmt_error + Colors.RESET
        }

    def format(self, record):
        """Format function for logging formatter"""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def print_dph_version() -> int:
    """Print dph version"""
    print(f"Data perimeter helper - v{__version__}")
    return 0


def create_folder(
    folder_path: str
) -> None:
    try:
        makedirs(
            name=folder_path,
            exist_ok=True,
            mode=0o766
        )
    except OSError as err:
        print(f"[!] Error while creating folder {err}")
        raise


def configure_logging(
    logging_export_folder_path: str,
    logging_export_file_name: str
) -> logging.Logger:
    """Configures python logger
    Console: Output logs with a log level DEBUG or above into stdout
    Silents as well boto3 logs below CRITICAL
    :return: logger object
    :rtype: logging.Logger
    """
    root = logging.getLogger()
    if root.hasHandlers():
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.getLogger().setLevel(logging.NOTSET)
    # File handler
    formatter_file = logging.Formatter(
        '%(asctime)s - %(filename)s:%(lineno)s - %(funcName)s - %(levelname)s - %(message)s',
        '%Y-%m-%d %H:%M:%S'
    )
    # Makes sure that the export folder exists
    create_folder(logging_export_folder_path)
    if logging_export_folder_path.endswith('/'):
        log_file_path = f"{logging_export_folder_path}{logging_export_file_name}"
    else:
        log_file_path = f"{logging_export_folder_path}/{logging_export_file_name}"
    rotating_file_handler = RotatingFileHandler(
        filename=log_file_path,
        maxBytes=10 * 1000000,
        backupCount=3
    )
    rotating_file_handler.setLevel(logging.DEBUG)
    rotating_file_handler.setFormatter(formatter_file)
    logging.getLogger().addHandler(rotating_file_handler)

    # Console handler
    formatter_console = FancyLogFormatter(
        log_fmt='%(asctime)s - %(filename)s:%(lineno)s - %(funcName)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(formatter_console)
    logging.getLogger().addHandler(console)
    # Log only critical boto3 logs
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    logging.getLogger('boto3').setLevel(logging.CRITICAL)
    logging.getLogger('botocore').setLevel(logging.CRITICAL)
    logging.getLogger('s3transfer').setLevel(logging.CRITICAL)
    logging.getLogger('urllib3').setLevel(logging.CRITICAL)
    # Log only critical awswrangler logs
    logging.getLogger('awswrangler').setLevel(logging.CRITICAL)
    return logging.getLogger()


def set_log_level(log_level):
    logger = logging.getLogger()
    for handler in logger.handlers:
        handler.setLevel(log_level)


def decorator_elapsed_time(
    decorated_fct: Optional[Callable] = None,
    message: Optional[str] = None,
    color: str = Colors.GREY
) -> Callable:
    """Decorator to measure execution time of a function

    :param decorated_function: function to measure execution time
    :return: a wrapper of the function
    """
    def _decorator(_fct):
        @wraps(_fct)
        def wrapper(*args, **kwargs):
            start_time = current_time()
            result = _fct(*args, **kwargs)
            if (result is None) or (result is False):
                return result
            log = color_string(
                f"{message}{get_elapsed_time(start_time)}",
                color
            )
            logger.debug(log)
            print(Icons.SPARKLE + log)
            return result
        return wrapper
    return _decorator if callable(decorated_fct) else _decorator


def current_time() -> float:
    """Return current timestamp"""
    return perf_counter()


def get_elapsed_time(start_time: float) -> str:
    """Return elapsed"""
    return strftime("%Hh:%Mm:%Ss", gmtime(current_time() - start_time))


def color_string(input: str, color: str) -> str:
    """Return a string with the provided color"""
    return f"{color}{input}{Colors.RESET}"


def merge_list_dict(list_dicts: List[dict]) -> Dict[str, list]:
    '''Merge a list of dict'''
    conf_merged: Dict[str, list] = {}
    list_keys = set().union(*list_dicts)  # list of all dicts keys
    for key in list_keys:
        for _dict in list_dicts:
            conf_merged.setdefault(
                key, []
            )
            item = _dict.get(key, None)
            if item is None:
                continue
            if isinstance(item, list):
                conf_merged.get(key).extend(  # type: ignore
                    item
                )
            elif isinstance(item, (str, int)):
                conf_merged.get(key).append(  # type: ignore
                    item
                )
            else:
                logger.debug(
                    "Below key has not been merged, key: %s, type: %s",
                    key, type(item)
                )
        conf_merged[key] = list(set(conf_merged.get(key)))  # type: ignore
    logger.debug("[~] Merged configuration: %s", conf_merged)
    return conf_merged


def load_yaml_config_file(
    file_path: str,
    config_section_name: Optional[str] = None
) -> Union[Dict, List]:
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = yaml.load(file, Loader=yaml.SafeLoader)
            if config_section_name is None:
                return data
            if config_section_name in data:
                return data[config_section_name]
            raise ValueError(
                f"[!] YAML config file [{file_path}] does not contain"
                f" [{config_section_name}] section. Change section name"
                " or set a different section using "
                "flag --variable-yaml-section"
            )
    except FileNotFoundError as file_not_found:
        logger.exception(file_not_found)
        raise
    except (ComposerError, yaml.parser.ParserError) as yaml_error:
        raise RuntimeError(
            f"Error while loading yaml file {file_path}."
        ) from yaml_error


def str_sanitizer(value: str) -> str:
    """Sanitize a string by allowing only a subset of characters.
    Remove the char ', and encapsulate the result between ' to avoid sql
    injection. Based on AWS SDK for pandas function to parametrize queries
    on customer side"""
    str_value = str(value)
    if regex_str_sanitizer.search(str_value, re.IGNORECASE):
        logger.error("Error while formatting: %s", str_value)
        raise ValueError(
            f"Error while formatting inputs: {str_value} - inputs need to "
            f"follow below regex pattern: {regex_str_sanitizer.pattern}"
        )
    return f"""'{str_value.replace("'", "''")}'"""


def generator_list_as_str_chunker(
    list_input: List[str],
    max_size: int = 1020,
    separator: str = "|"
) -> Generator[str, None, None]:
    """Generator that chunk a list into string joined with a separator and
    a max length"""
    str_input = separator.join(list_input)
    len_str_input = len(str_input)
    logger.debug(
        "List as string chunker: (%s) %s",
        len_str_input, str_input
    )
    len_input_as_list = len(list_input)
    if len_str_input < max_size:
        yield str_input
    else:
        partie_entiere = math.floor(len_input_as_list / 2)
        yield from generator_list_as_str_chunker(
            list_input[0:partie_entiere], max_size
        )
        yield from generator_list_as_str_chunker(
            list_input[partie_entiere:len_input_as_list], max_size
        )


def get_env_var(var_name: str) -> Union[str, None]:
    """Get environment variable, return None if not found"""
    return environment_variables.get(var_name)


def df_columns_exist(
    dataframe: pandas.DataFrame,
    required_columns: Set[str],
    log_error: bool = True
) -> bool:
    if not required_columns.issubset(dataframe.columns):
        if log_error:
            logger.error(
                "Below columns are required: %s",
                required_columns
            )
        return False
    return True


def get_list_all_accounts() -> List[str]:
    """Return a list with all account IDs"""
    return helper.get_list_account_id()


def get_ou_descendant(ou_id: str) -> List[str]:
    """Return all descendants under an OU ID"""
    df = Referential.get_resource_type(
        resource_type="AWS::Organizations::Account"
    ).dataframe
    assert isinstance(df, pandas.DataFrame)  # nosec: B101
    list_descendant = []
    for account_id, list_parent in zip(df['accountid'], df['parent']):
        if ou_id in list_parent:
            list_descendant.append(
                account_id
            )
    if len(list_descendant) == 0:
        logger.warning(
            "No descendant found for organizational unit ID: %s",
            ou_id
        )
    return list_descendant


def get_account_id_from_name(account_name: str) -> str:
    df = Referential.get_resource_type(
        resource_type="AWS::Organizations::Account"
    ).dataframe
    assert isinstance(df, pandas.DataFrame)  # nosec: B101
    for account_id, account_name_ in zip(df['accountid'], df['name']):
        if account_name_ == account_name:
            return account_id
    raise ValueError(f"Account name {account_name} not found")


def get_ou_id_from_name(ou_name: str) -> str:
    Referential.get_resource_type(
        resource_type="AWS::Organizations::Account"
    )
    return account.get_ou_id_from_name(ou_name)
