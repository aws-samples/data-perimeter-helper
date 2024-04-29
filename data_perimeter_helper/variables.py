#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the Variable class with shared variables and configuration
"""
import logging
import os
import re
import argparse
from typing import (
    Union,
    Optional,
    List,
    Dict,
    Literal
)
from pathlib import (
    Path
)

import boto3
from botocore.config import Config

from data_perimeter_helper.toolbox import (
    utils
)


logger = logging.getLogger(__name__)
regex_date_regexp = re.compile(
    r"^(\d{1,4}|\d{3}%|\d{2}%|\d{1}%)/(\d{2}|\d{1}%|%)/(\d{2}|\d{1}%|%)$"
)
regex_date = re.compile(
    r"^(\d{1,4})/(\d{2})/(\d{2})$"
)
regex_date_interval = re.compile(
    r"^(?P<interval>\d{1,}) (?P<unit>day|month|year)$",
    re.IGNORECASE
)
regex_is_accountid = re.compile(r"^\d{12}$")


class Variables:
    """
    Hosts all variables and exceptions retrieved from
    account_configuration.py > per_account_configuration
    The variables between the "To be set" comments have to be updated
    """
    # ##########################################
    # AWS region where API calls are performed (example: Amazon Athena, AWS Config)
    region = None
    # Credential profile to use for access to Amazon Athena (see README file for required permissions)
    profile_athena_access = None
    ''' Credential profile to use for access to AWS Config advanced query
    the profile needs to be associated with the account where an organization
    aggregator exists (see README file for required permissions)
    '''
    profile_config_access = None
    # Credential profile to use for access to AWS organization (see README file for required permissions)
    profile_org_access = None
    # Credential profile to use for access to AWS IAM Access Analyzer (see README file for required permissions)
    profile_iam_access_analyzer = None
    external_access_findings: Optional[Literal['SECURITY_HUB', 'IAM_ACCESS_ANALYZER']] = None
    # AWS Config aggregator name
    config_aggregator_name = None
    # Athena Workgroup name
    athena_workgroup = None
    # Athena database name
    athena_database = None
    athena_ctas_approach = False
    '''
    athena_cloudtrail_table_configuration = UNIQUE
        Athena queries will be performed against the table name provided by
        athena_table_name_mgmt_data_event
    athena_cloudtrail_table_configuration = SPLIT
        Athena queries will be performed against the tables names provided by
        athena_table_name_mgmt_event for management events
        athena_table_name_data_event for data events
    '''
    athena_cloudtrail_table_configuration = None
    athena_table_name_mgmt_data_event = None
    athena_table_name_mgmt_event = None
    athena_table_name_data_event = None
    '''
    partition_date_regex can be equal to
        - a regex following date format and supported by Athena
            - Example: '2023/03/%' for all queries performed in March 2023
        - None
    If partition_date_regex is None then partition_date_start and
    partition_date_end need to be set
    '''
    partition_date_regex = None
    partition_date_start = None
    partition_date_end = None
    partition_date_interval = None
    partition_date_interval_value = None
    partition_date_interval_unit = None
    # Boto3
    session_config = None
    session_org = None
    session_iam_aa = None
    config_client = None
    org_client = None
    # Python
    package_path = Path(__file__).absolute().parent  # data_perimeter_helper/
    package_parent_path = package_path.parent  # parent of data_perimeter_helper/
    # variables yaml file
    variable_yaml_file_name = "variables.yaml"
    variable_yaml_full_path = str(package_path / variable_yaml_file_name)
    variable_yaml_section = "default"
    # logging file
    logging_export_folder_path = str(package_parent_path / "outputs")  # Folder where logs are written
    logging_file_name = "logs.txt"
    # result path
    result_export_folder = str(package_parent_path / "outputs")  # Folder name for outputs
    thread_max_worker = min(32, (os.cpu_count() or 1) + 4)  # Number of workers for threading
    thread_max_worker_organizations = 3
    print_query = False
    print_result = False
    use_parameterized_queries = True
    list_account_id: list = []
    list_ou_id: list = []
    # Data perimeter configuration file
    dph_yaml_file_name = "data_perimeter.yaml"
    dph_yaml_full_path = str(
        package_path / dph_yaml_file_name
    )
    dph_configuration = None
    dph_configuration_baseline = None
    dph_configuration_per_account: Dict[str, dict] = {}
    standalone_query_types = ["referential", "findings"]

    def __init__(
        self,
        arguments: argparse.Namespace
    ):
        Variables.list_account_id = arguments.list_account
        Variables.list_ou_id = arguments.list_ou
        Variables.print_query = arguments.print_query
        Variables.print_result = arguments.print_result
        # Set custom variable file or custom section
        if arguments.variable_file is not None:
            Variables.variable_yaml_full_path = arguments.variable_file
        if arguments.variable_yaml_section is not None:
            Variables.variable_yaml_section = arguments.variable_yaml_section
        if arguments.dph_conf_file is not None:
            Variables.dph_yaml_full_path = arguments.dph_conf_file
        if arguments.output_folder is not None:
            Variables.result_export_folder = arguments.output_folder
        Variables.init_data_perimeter_definition()
        Variables.init_variables_from_yaml_file(
            Variables.variable_yaml_full_path,
            Variables.variable_yaml_section
        )
        Variables.init_boto3_var()
        # Variables.augment_variables()
        Variables.validate_variables()
        logger.debug(
            "[~] Variable class:\n%s",
            Variables.__dict__
        )

    @classmethod
    def init_boto3_var(cls):
        """Init boto3 clients and sessions"""
        cls.session_config = boto3.session.Session(
            profile_name=cls.profile_config_access,
            region_name=cls.region
        )
        cls.session_org = boto3.session.Session(
            profile_name=cls.profile_org_access,
            region_name=cls.region
        )
        client_config_bump_max_attemps = Config(
            retries={
                'max_attempts': 15
            }
        )
        cls.config_client = cls.session_config.client("config")
        cls.org_client = cls.session_org.client(
            "organizations",
            config=client_config_bump_max_attemps
        )
        if cls.external_access_findings in (
            'SECURITY_HUB', 'IAM_ACCESS_ANALYZER'
        ):
            cls.session_iam_aa = boto3.session.Session(
                profile_name=cls.profile_iam_access_analyzer,
                region_name=cls.region
            )

    @classmethod
    def init_data_perimeter_definition(cls):
        """Retrieve data perimeters definition from configuration file"""
        cls.dph_configuration = utils.load_yaml_config_file(
            cls.dph_yaml_full_path
        )
        assert isinstance(cls.dph_configuration, dict)  # nosec: B101
        # Convert all dict keys to string
        cls.dph_configuration = {
            str(k): v for k, v in cls.dph_configuration.items()
        }
        # Save the baseline
        cls.dph_configuration_baseline = cls.dph_configuration.get(
            "baseline"
        )
        assert isinstance(cls.dph_configuration_baseline, dict)  # nosec: B101
        # Build for each account its data perimeter definition by merging
        # account specific configuration with the baseline
        for account_id in cls.list_account_id:
            cls.dph_configuration_per_account[account_id] = utils.merge_list_dict(
                [
                    cls.dph_configuration_baseline,
                    cls.dph_configuration.get(account_id, {})
                ]
            )

    @classmethod
    def set_var(
        cls,
        key: str,
        var_file: dict,
        default: Optional[Union[str, bool]] = None,
        mandatory: bool = False
    ) -> Union[str, bool, None]:
        """Set a given class variables identified by its `key`. Check first
        the environment variables, then the configuration file and finally the
        default value"""
        value = utils.get_env_var(key) or var_file.get(key) or default
        if value is None and mandatory is True:
            logger.error(
                "Variable [%s] needs to be defined in provided variable file "
                "or as an environment variable",
                key
            )
            raise KeyError(f"Variable '{key}' needs to be defined")
        setattr(cls, key, value)
        return value

    @classmethod
    def init_variables_from_yaml_file(
        cls,
        variable_file_path: str,
        section_name: str
    ) -> None:
        """Init variables from the variable configuration file"""
        var_file = utils.load_yaml_config_file(
            variable_file_path,
            section_name
        )
        logger.debug(
            "[~] Retrieved variables from file [%s]: %s",
            variable_file_path, var_file
        )
        assert isinstance(var_file, dict)  # nosec: B101
        cls.set_var("region", var_file)
        cls.set_var("profile_athena_access", var_file)
        cls.set_var("profile_config_access", var_file)
        cls.set_var("profile_org_access", var_file)
        cls.set_var("external_access_findings", var_file, default=False)
        cls.set_var("profile_iam_access_analyzer", var_file)
        cls.set_var("config_aggregator_name", var_file, mandatory=True)
        cls.set_var("athena_workgroup", var_file, mandatory=True)
        cls.set_var("athena_database", var_file, mandatory=True)
        cls.set_var("athena_ctas_approach", var_file, default=False)
        cls.set_var(
            "athena_cloudtrail_table_configuration",
            var_file,
            default="UNIQUE"
        )
        cls.set_var("athena_table_name_mgmt_data_event", var_file)
        cls.set_var("athena_table_name_mgmt_event", var_file)
        cls.set_var("athena_table_name_data_event", var_file)
        cls.set_var("partition_date_regex", var_file)
        cls.set_var("partition_date_start", var_file)
        cls.set_var("partition_date_end", var_file)
        cls.set_var("partition_date_interval", var_file)
        if Variables.partition_date_interval is not None:
            regex_res = regex_date_interval.search(
                Variables.partition_date_interval
            )
            if regex_res is not None:
                Variables.partition_date_interval_value = regex_res.group('interval')
                Variables.partition_date_interval_unit = regex_res.group('unit')
            else:
                raise ValueError(
                    f"Invalid date format - partition_date_interval in {variable_file_path}"
                )
        cls.set_var(
            "use_parameterized_queries",
            var_file,
            default=True
        )

    @classmethod
    def augment_variables(cls) -> None:
        target_list_account_id = []
        if len(cls.list_account_id) == 1 and cls.list_account_id[0] == 'all':
            logger.debug(
                "-la CLI parameter set to `all`,"
                " expanding the list of account..."
            )
            cls.list_account_id = utils.get_list_all_accounts()
            return None
        for item in cls.list_account_id:
            if regex_is_accountid.match(item):
                target_list_account_id.append(item)
            else:
                target_list_account_id.append(
                    utils.get_account_id_from_name(item)
                )
        if len(cls.list_ou_id) > 0:
            for item in cls.list_ou_id:
                if item.startswith('ou-'):
                    target_list_account_id.extend(
                        utils.get_ou_descendant(item)
                    )
        cls.list_account_id = list(set(target_list_account_id))
        return None

    @classmethod
    def validate_variables(cls) -> None:
        """Validate class variables"""
        if cls.partition_date_regex is None:
            if (cls.partition_date_start is None) or (cls.partition_date_end is None):
                if cls.partition_date_interval is None:
                    raise ValueError(
                        "No valid date provided in variable file "
                        f"{cls.variable_yaml_full_path}"
                    )
        if cls.partition_date_regex is not None:
            if not regex_date_regexp.match(cls.partition_date_regex):
                raise ValueError(
                    f"Invalid date format - partition_date_regex in {cls.variable_yaml_full_path}"
                )
        if cls.partition_date_start is not None:
            if not regex_date.match(cls.partition_date_start):
                raise ValueError(
                    f"Invalid date format - partition_date_start in {cls.variable_yaml_full_path}"
                )
            if not regex_date.match(cls.partition_date_end):
                raise ValueError(
                    f"Invalid date format - partition_date_end in {cls.variable_yaml_full_path}"
                )
        if cls.partition_date_interval is not None:
            if not regex_date_interval.match(cls.partition_date_interval):
                raise ValueError(
                    f"Invalid date_interval format in file {cls.variable_yaml_full_path} - expected: {regex_date_interval.pattern}"
                )

    @classmethod
    def get_account_configuration(
        cls,
        account_id: str,
        configuration_key: str
    ) -> List[str]:
        """Get data perimeter definition for a given account id and
        configuration type (example:, network_perimeter_expected_vpc)"""
        assert isinstance(cls.dph_configuration_per_account, dict)  # nosec: B101
        if account_id not in cls.dph_configuration_per_account:
            assert isinstance(cls.dph_configuration_baseline, dict)  # nosec: B101
            return cls.dph_configuration_baseline.get(configuration_key, [])
        return cls.dph_configuration_per_account.get(account_id, {}).get(
            configuration_key, {}
        )

    @classmethod
    def get_baseline_configuration(
        cls,
        key_name: str
    ):
        """Get the baseline key from the configuration file content"""
        assert isinstance(cls.dph_configuration_baseline, dict)  # nosec: B101
        return cls.dph_configuration_baseline.get(key_name, {})

    @classmethod
    def get_account_resource_exception(
        cls,
        account_id: str,
        resource_type: str
    ) -> dict:
        """Get exceptions for a given account ID and resource type from the
        configuration file"""
        return cls.dph_configuration.get(  # type: ignore
            account_id, {}
        ).get(resource_type, {})
