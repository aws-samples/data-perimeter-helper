#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `account` used to retrieve accounts data
through AWS Organizations API calls
"""
import logging
from typing import (
    List,
    Dict,
    Optional,
    Union,
)
from concurrent.futures import (
    ThreadPoolExecutor,
    Future,
    as_completed as concurrent_completed
)

import pandas
from botocore.exceptions import (
    ClientError
)

from data_perimeter_helper.variables import (
    Variables as Var
)
from data_perimeter_helper.referential.ResourceType import ResourceType


logger = logging.getLogger(__name__)


class account(ResourceType):
    """All accounts"""
    # Cache to avoid redundand calls to AWS Organizations API, key is the child
    # ID and the value its parent ID
    cache_direct_parent: Dict[str, str] = {}
    cache_account_in_org_unit_boundary: Dict[str, List[str]] = {}
    cache_ou_by_id: Dict[str, Dict[str, str]] = {}
    cache_ou_by_name: Dict[str, Dict[str, str]] = {}
    USE_THREAD_FOR_LIST_PARENT = True

    def __init__(self):
        super().__init__(
            type_name="AWS::Organizations::Account",
            unknown_value="ACCOUNT_NOT_IN_CURRENT_ORGANIZATION"
        )

    def populate(self, *args, **kwargs) -> pandas.DataFrame:
        """List all AWS account ID in the AWS organization
        :type org_client: boto3.client, optional
        :return: DataFrame with all account ids
        :rtype: pandas.DataFrame
        """
        logger.debug("[~] Retrieving list of all accounts in the organization")
        assert Var.org_client is not None  # nosec: B101
        paginator = Var.org_client.get_paginator('list_accounts')
        page_iterator = paginator.paginate()
        results = []
        for page in page_iterator:
            for item in page['Accounts']:
                res = {
                    'accountid': item['Id'],
                    'name': item['Name'],
                }
                if account.USE_THREAD_FOR_LIST_PARENT is False:
                    res['parent'] = self.get_list_all_parents(item['Id'])
                results.append(res)
        if account.USE_THREAD_FOR_LIST_PARENT is True:
            account.get_list_all_parents_thread(results)
        logger.debug("[~] List of retrieved accounts: %s", results)
        df = pandas.DataFrame.from_dict(results)  # type: ignore
        account.describe_all_parents(df)
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

    @classmethod
    def describe_all_parents(cls, df: pandas.DataFrame) -> None:
        """Describe all parents"""
        all_parents = []
        # Build a distinct list of OU IDs
        for list_parent_id in df['parent']:
            all_parents.extend(list_parent_id)
        all_parents = list(set(all_parents))
        logger.debug("[~] List of all parents: %s", all_parents)
        # Describe each list item using threads
        cls.api_describe_ou_thread(all_parents)
        # Update the initial dataframe
        df['parent_name'] = [
            cls.get_ou_name_for_list(
                list_parent_id
            )
            for list_parent_id in df['parent']
        ]

    @staticmethod
    def api_describe_ou_thread(all_parents: List[str]) -> None:
        """Perform the API describe OU using threads"""
        pool: Dict[Future, dict] = {}
        # Number of worker divided by two to manage nested threads
        with ThreadPoolExecutor(
            max_workers=int(Var.thread_max_worker / 2)
        ) as executor:
            for ou_id in all_parents:
                pool.update({
                    executor.submit(
                        account.api_describe_ou,
                        ou_id
                    ): {}
                })
            for request_in_pool in concurrent_completed(pool):
                exception = request_in_pool.exception()
                if exception:
                    raise exception

    @classmethod
    def get_ou_name_for_list(cls, list_ou_id: List[str]) -> List[str]:
        """Return a list of OU name with a list of OU IDs as input"""
        return [
            cls.get_ou_name(ou_id)
            for ou_id in list_ou_id
        ]

    @classmethod
    def get_ou_name(cls, ou_id: str) -> str:
        """Get the name of an OU using its ID"""
        return cls.api_describe_ou(ou_id)['Name']

    @classmethod
    def api_describe_ou(cls, ou_id: str) -> Dict[str, str]:
        """Describe parents of a list of accounts
        returns Dict['Id', 'Arn', 'Name']
        """
        if ou_id in cls.cache_ou_by_id:
            return cls.cache_ou_by_id[ou_id]
        if ou_id.startswith('r-'):
            return {'Id': 'N/A', 'Arn': 'N/A', 'Name': 'Root'}
        assert Var.org_client is not None  # nosec: B101
        try:
            res = Var.org_client.describe_organizational_unit(
                OrganizationalUnitId=ou_id
            )['OrganizationalUnit']
            cls.cache_ou_by_id[ou_id] = res
            cls.cache_ou_by_name[res['Name']] = res
            return res
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " [organizations:DescribeOrganizationalUnit]"
                )
            raise

    @staticmethod
    def get_list_all_parents_thread(list_account):
        pool = {}
        # Number of worker divided by two to manage nested threads
        with ThreadPoolExecutor(
            max_workers=int(Var.thread_max_worker / 2)
        ) as executor:
            for dict_account in list_account:
                pool.update({
                    executor.submit(
                        account.get_list_all_parents,
                        dict_account['accountid']
                    ): {
                        'dict_account': dict_account
                    }
                })
            for request_in_pool in concurrent_completed(pool):
                exception = request_in_pool.exception()
                if exception:
                    raise exception
                dict_account = pool[request_in_pool]['dict_account']
                dict_account['parent'] = request_in_pool.result()

    @staticmethod
    def get_list_all_parents(
        child_id: str,
        list_parent: Optional[List[str]] = None,
        depth: int = 1
    ) -> List[str]:
        """Get all parents of a given child in AWS Organizations"""
        # max depth is 6 since max nested OU quotas is 5 and root is counted
        # as a member of the org path
        if depth > 6:
            raise ValueError("Too many nested OU")
        if list_parent is None:
            list_parent = []
        # if the parent has been cached, return the known parent id
        if child_id in account.cache_direct_parent:
            parent_id = account.cache_direct_parent[child_id]
        # else perform API call
        else:
            parent_id = account.get_direct_parent_org_api(child_id)
            if parent_id is None:
                return list_parent
            account.cache_direct_parent[child_id] = parent_id
        list_parent.append(
            parent_id
        )
        if parent_id.startswith('r-'):
            return list_parent
        return account.get_list_all_parents(
            parent_id, list_parent, depth + 1
        )

    @staticmethod
    def get_direct_parent_org_api(child_id: str) -> str:
        """Call AWS Organizations APIs to retrieve direct parent of a child.
        The API supports AWS account ID or OU ID - root ID is not supported"""
        try:
            assert Var.org_client is not None  # nosec: B101
            parent = Var.org_client.list_parents(
                ChildId=child_id
            ).get('Parents', [])
            parent_id = parent[0].get('Id')
            if parent_id is None:
                raise ValueError(
                    "Parent of an AWS organization member must have an Id"
                )
            return parent_id
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " [organizations:ListParents]"
                )
            raise

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

    @classmethod
    def get_ou_id_from_name(
        cls,
        ou_name: str
    ) -> str:
        """Get the OU ID from its name"""
        if ou_name in cls.cache_ou_by_name:
            return cls.cache_ou_by_name[ou_name]['Id']
        raise ValueError(f"OU name {ou_name} not found")
