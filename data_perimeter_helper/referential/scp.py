#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `scp` used to retrieve the tree
structure of the organization
"""
import logging
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed as concurrent_completed
)
from typing import (
    List,
    Dict,
    Union
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


class scp(ResourceType):
    """"""

    def __init__(self):
        super().__init__(
            type_name="AWS::Organizations::SCP",
            unknown_value="ORGANIZATION_NOT_ENABLED"
        )

    def populate(self, *args, **kwargs) -> pandas.DataFrame:
        """List all service control policies (SCPs)
        :return: DataFrame with all service control policies (SCPs)
        :rtype: pandas.DataFrame
        """
        list_scp = self.list_policies_org_api()
        log_msg = f"{len(list_scp)} SCPs retrieved!"
        tqdm.write(utils.Icons.INFO + log_msg)
        log_msg = "Describing SCPs..."
        tqdm.write(utils.Icons.HAND_POINTING + log_msg)
        self.describe_policy_thread(list_scp)
        log_msg = "Listing targets of SCPs..."
        tqdm.write(utils.Icons.HAND_POINTING + log_msg)
        self.list_targets_thread(list_scp)
        df = pandas.DataFrame(list_scp)
        # Add column isAttached set to True when the SCP has at least one target
        df['isAttached'] = [
            True if len(targets) > 0 else False
            for targets in df['targets']
        ]
        # Drop AWS managed policies
        df = df[~df.AwsManaged]
        # Drop the unneeded columns
        df = df.drop(columns=['AwsManaged', 'Type'])
        return df

    @staticmethod
    def list_policies_org_api(
    ) -> List[Dict[str, Union[str, List[Dict[str, str]]]]]:
        """List all service control policies (SCPs)
        :param next_token: Token to retrieve the next set of results
        :return: List of service control policies (SCPs)
        :rtype: List[Dict[str, str]]
        """
        try:
            results: List[str] = []
            assert Var.org_client is not None  # nosec: B101
            paginator = Var.org_client.get_paginator('list_policies')
            page_iterator = paginator.paginate(
                Filter='SERVICE_CONTROL_POLICY'
            )
            for page in page_iterator:
                for item in page['Policies']:
                    results.append(item)
            return results
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " [organizations:ListPolicies]"
                )
            raise

    @classmethod
    def describe_policy_thread(cls, list_policy: List[Dict[str, Union[str, List[Dict[str, str]]]]]) -> None:
        """Describe service control policies (SCPs) using threading
        :param list_policy: List of SCPs
        :type list_policy: List[Dict[str, str]]
        """
        pool = {}
        nb_policy = len(list_policy)
        with tqdm(
            total=nb_policy,
            desc="Described SCPs",
            unit="SCPs",
            leave=False
        ) as pbar:
            with ThreadPoolExecutor(
                # Quota for DescribePolicy is 2 per second
                # See https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
                max_workers=2
            ) as executor:
                for policy in list_policy:
                    pool.update({
                        executor.submit(
                            cls.describe_policy_org_api,
                            str(policy['Id'])
                        ): policy
                    })
                for request_in_pool in concurrent_completed(pool):
                    exception = request_in_pool.exception()
                    if exception:
                        raise exception
                    content = request_in_pool.result()
                    policy = pool[request_in_pool]
                    policy['policyDocument'] = content
                    pbar.update(1)

    @staticmethod
    def describe_policy_org_api(
        policy_id: str
    ) -> str:
        """Describe a service control policy (SCP)
        :param policy_id: ID of the policy
        :return: SCP policy document
        :rtype: str
        """
        try:
            assert Var.org_client is not None  # nosec: B101
            res = Var.org_client.describe_policy(
                PolicyId=policy_id
            )
            retry_attempts = res['ResponseMetadata']['RetryAttempts']
            if retry_attempts > 1:
                logger.debug("Retry attempts: %s", retry_attempts)
            if retry_attempts > 10:
                logger.warning("Retry attempts: %s", retry_attempts)
            return res['Policy']['Content']
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " [organizations:DescribePolicy]"
                )
            raise

    @classmethod
    def list_targets_thread(cls, list_policy: List[Dict[str, Union[str, List[Dict[str, str]]]]]) -> None:
        """List targets of SCPs using threading
        :param list_policy: List of SCPs
        :type list_policy: List[Dict[str, Union[str, List[Dict[str, str]]]]]
        """
        pool = {}
        nb_policy = len(list_policy)
        with tqdm(
            total=nb_policy,
            desc="SCP targets retrieved",
            unit="SCPs",
            leave=False
        ) as pbar:
            with ThreadPoolExecutor(
                # Quota for DescribePolicy is 5 per second
                # See https://docs.aws.amazon.com/organizations/latest/userguide/orgs_reference_limits.html
                max_workers=3
            ) as executor:
                for policy in list_policy:
                    pool.update({
                        executor.submit(
                            cls.list_targets_org_api,
                            str(policy['Id'])
                        ): policy
                    })
                for request_in_pool in concurrent_completed(pool):
                    exception = request_in_pool.exception()
                    if exception:
                        raise exception
                    targets = request_in_pool.result()
                    policy = pool[request_in_pool]
                    policy['targets'] = targets
                    pbar.update(1)

    @staticmethod
    def list_targets_org_api(
        policy_id: str
    ) -> List[Dict[str, str]]:
        """List the target of a policy
        :param policy_id: ID of the policy
        :return: List of targets
        :rtype: List[Dict[str, str]]
        """
        try:
            results: List[str] = []
            assert Var.org_client is not None  # nosec: B101
            paginator = Var.org_client.get_paginator('list_targets_for_policy')
            page_iterator = paginator.paginate(
                PolicyId=policy_id
            )
            for page in page_iterator:
                retry_attempts = page['ResponseMetadata']['RetryAttempts']
                if retry_attempts > 1:
                    logger.debug("Retry attempts: %s", retry_attempts)
                if retry_attempts > 10:
                    logger.warning("Retry attempts: %s", retry_attempts)
                for item in page['Targets']:
                    results.append(item)
            return results
        except ClientError as error:
            logger.error("[!] Error from AWS client: %s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " [organizations:ListTargetsForPolicy]"
                )
            raise
