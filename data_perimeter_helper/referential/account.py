#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `account` used to retrieve accounts data
through AWS Organizations API calls
"""
import logging
from concurrent.futures import (
    ThreadPoolExecutor,
    Future,
    as_completed as concurrent_completed
)
from typing import (
    List,
    Dict,
    Union,
    Literal,
    Optional
)

import pandas
from tqdm import (
    tqdm
)
from botocore.exceptions import (
    ClientError
)

from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.toolbox import utils
from data_perimeter_helper.referential.ResourceType import ResourceType


logger = logging.getLogger(__name__)


class account(ResourceType):
    """All accounts"""
    cache_account_in_org_unit_boundary: Dict[str, List[str]] = {}
    root_id = None
    list_tree_path: List[List[str]] = []
    list_parents_per_children: Dict[str, List[str]] = {}
    QUOTA_MAX_OU = 5

    def __init__(self):
        super().__init__(
            type_name="AWS::Organizations::Account",
            unknown_value="ACCOUNT_NOT_IN_CURRENT_ORGANIZATION"
        )

    def populate(self, *args, **kwargs) -> pandas.DataFrame:
        """List all AWS account ID in the AWS organization
        :return: DataFrame with all account ids
        :rtype: pandas.DataFrame
        """
        logger.debug("[~] Retrieving list of all accounts in the organization")
        list_account = self.list_account()
        self.add_parent_to_list_account(list_account)
        df = pandas.DataFrame.from_dict(list_account)  # type: ignore
        org_unit_boundary_definition = account.get_org_unit_boundary_definition()
        if org_unit_boundary_definition is None:
            return df
        df['orgUnitBoundary'] = [
            account.get_account_org_unit_boundary(
                list_parent_id, org_unit_boundary_definition
            )
            for list_parent_id in df['parent']
        ]
        return df

    @staticmethod
    def list_account() -> List[Dict[str, Union[str, List[str]]]]:
        """List all accounts"""
        assert Var.org_client is not None  # nosec: B101
        log_msg = "Listing accounts..."
        tqdm.write(utils.Icons.HAND_POINTING + log_msg)
        list_account = []
        try:
            paginator = Var.org_client.get_paginator('list_accounts')
            page_iterator = paginator.paginate()
            for page in page_iterator:
                for item in page['Accounts']:
                    list_account.append({
                        'accountid': item['Id'],
                        'name': item['Name'],
                    })
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Principal is not authorized to perform"
                    " [organizations:ListAccounts]"
                )
            raise
        nb_account = len(list_account)
        logger.debug("[~] %s account retrieved: %s", nb_account, list_account)
        log_msg = f"{nb_account} accounts retrieved!"
        tqdm.write(utils.Icons.INFO + log_msg)
        return list_account

    @classmethod
    def add_parent_to_list_account(
        cls,
        list_account: List[Dict[str, Union[str, List[str]]]]
    ):
        log_msg = "Listing organizational units (OUs)..."
        tqdm.write(utils.Icons.HAND_POINTING + log_msg)
        cls.get_all_ou()
        log_msg = "Listing OU children..."
        tqdm.write(utils.Icons.HAND_POINTING + log_msg)
        cls.get_ou_children_thread()
        for dict_account in list_account:
            account_id = dict_account['accountid']
            assert isinstance(account_id, str)  # nosec: B101
            list_parent = cls.list_parents_per_children.get(account_id)
            if list_parent is None:
                raise ValueError(
                    "List of parents has **not** been retrieved for "
                    f"account {account_id}"
                )
            dict_account['parent'] = list_parent

    @classmethod
    def get_all_ou(
        cls,
        parent_id: Optional[str] = None,
        tree_path: Optional[List] = None
    ):
        """Parse the organization tree starting from the root"""
        if parent_id is None:
            parent_id = cls.get_root_id()
            cls.list_tree_path.append([parent_id])
        if tree_path is None:
            tree_path = [parent_id]
        if len(tree_path) > cls.QUOTA_MAX_OU + 1:
            return
        list_direct_ou = cls.get_direct_children_per_type_org_api(
            parent_id, 'ORGANIZATIONAL_UNIT'
        )
        if len(list_direct_ou) == 0:
            cls.list_tree_path.append(tree_path)
            return
        pool: Dict[Future, None] = {}
        with ThreadPoolExecutor(
            max_workers=Var.thread_max_worker_organizations
        ) as executor:
            for direct_ou in list_direct_ou:
                pool.update({
                    executor.submit(
                        cls.get_all_ou,
                        direct_ou,
                        tree_path + [direct_ou]
                    ): None
                })
            for request_in_pool in concurrent_completed(pool):
                exception = request_in_pool.exception()
                if exception:
                    raise exception

    @classmethod
    def get_root_id(cls):
        """Get the root ID"""
        if cls.root_id is not None:
            return account.root_id
        assert Var.org_client is not None  # nosec: B101
        try:
            res_api = Var.org_client.list_roots()
            cls.root_id = res_api['Roots'][0]['Id']
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " [organizations:ListRoots]"
                )
            raise
        return cls.root_id

    @staticmethod
    def get_direct_children_per_type_org_api(
        child_id: str,
        child_type: Literal['ACCOUNT', 'ORGANIZATIONAL_UNIT']
    ) -> List[str]:
        """Call AWS Organizations APIs to retrieve direct children.
        The API supports root ID or OU ID"""
        try:
            results: List[str] = []
            assert Var.org_client is not None  # nosec: B101
            paginator = Var.org_client.get_paginator('list_children')
            page_iterator = paginator.paginate(
                ParentId=child_id,
                ChildType=child_type
            )
            for page in page_iterator:
                retry_attempts = page['ResponseMetadata']['RetryAttempts']
                if retry_attempts > 1:
                    logger.debug("Retry attempts: %s", retry_attempts)
                if retry_attempts > 10:
                    logger.warning("Retry attempts: %s", retry_attempts)
                for item in page['Children']:
                    results.append(item['Id'])
            return results
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " [organizations:ListChildren]"
                )
            raise

    @classmethod
    def get_ou_children_thread(cls) -> None:
        """Get the list of OU children"""
        logger.debug("Getting list of OU children")
        pool = {}
        list_last_descendant: List[Dict[str, Union[str, List[str]]]] = []
        for tree_path in cls.list_tree_path:
            list_last_descendant.append({
                'ou_id': tree_path[-1],
                'tree_path': tree_path
            })
        with ThreadPoolExecutor(
            max_workers=Var.thread_max_worker_organizations
        ) as executor:
            for last_descendant in list_last_descendant:
                ou_id = last_descendant.get('ou_id')
                assert isinstance(ou_id, str)  # nosec: B101
                pool.update({
                    executor.submit(
                        cls.get_direct_children_per_type_org_api,
                        ou_id,
                        'ACCOUNT'
                    ): last_descendant
                })
            for request_in_pool in concurrent_completed(pool):
                exception = request_in_pool.exception()
                if exception:
                    raise exception
                list_direct_account = request_in_pool.result()
                request_tree_path = pool[request_in_pool]['tree_path']
                assert isinstance(request_tree_path, list)  # nosec: B101
                if len(list_direct_account) != 0:
                    for direct_account in list_direct_account:
                        cls.list_parents_per_children[direct_account] =\
                            request_tree_path
        return None

    def get_account_in_org_unit_boundary(
        self,
        ou_perimeter_name: str
    ) -> List[str]:
        """Get list of AWS account IDs in a given OU boundary"""
        logger.debug(
            "Getting list of AWS account ID for OU boundary: %s",
            ou_perimeter_name
        )
        list_account_id: List[str] = []
        if self.dataframe is None:
            raise ValueError("You need to populate `account` class")
        # if org_unit_boundary is not used return an empty list
        if 'orgUnitBoundary' not in self.dataframe:
            return list_account_id
        # re-use cache result if relevant
        if ou_perimeter_name in self.cache_account_in_org_unit_boundary:
            return self.cache_account_in_org_unit_boundary[ou_perimeter_name]
        df = self.dataframe.copy()
        df['in_boundary'] = [
            {ou_perimeter_name}.issubset(list_ou_perimeter)
            for list_ou_perimeter in df['orgUnitBoundary']
        ]
        list_account_id = df[
            df['in_boundary'].isin([True])
        ]['accountid'].to_list()
        self.cache_account_in_org_unit_boundary[ou_perimeter_name] = list_account_id
        return list_account_id

    @staticmethod
    def get_org_unit_boundary_definition(
    ) -> Union[None, Dict[str, List[str]]]:
        """Read the key org_unit_boundary from data perimeter definition
        file and perform data cleansing"""
        input = Var.get_baseline_configuration(
            "org_unit_boundary"
        )
        if not isinstance(input, dict) or len(input) == 0:
            return None
        assert isinstance(input, dict)  # nosec: B101
        org_unit_boundary: Dict[str, List[str]] = {}
        for category_name, org_unit in input.items():
            org_unit_boundary[category_name] = []
            if not isinstance(org_unit, list):
                org_unit = [org_unit]
            for item in org_unit:
                org_unit_boundary[category_name].append(
                    account.manage_str_org_unit_input(item)
                )
        return org_unit_boundary

    @staticmethod
    def manage_str_org_unit_input(ou_input: str) -> str:
        """Read the input as provided in the data perimeter configuration file
        and perform data validation and cleansing"""
        ou_input = str(ou_input)
        ou_input = ou_input.strip(" ").strip("*").strip("/")
        if "/" in ou_input:
            return ou_input.split("/")[-1]
        return ou_input

    @staticmethod
    def get_account_org_unit_boundary(
        list_parent_id: List[str],
        org_unit_boundary: Dict[str, List[str]]
    ) -> List[str]:
        """Get for a given list of parent IDs, the list of associated
        OU boundary name"""
        list_category_name = []
        for parent_id in list_parent_id:
            for category_name, org_unit in org_unit_boundary.items():
                if parent_id in org_unit:
                    list_category_name.append(category_name)
        return list(set(list_category_name))
