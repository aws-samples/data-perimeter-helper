#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""
This module hosts the class `iam_role` used to retrieve AWS IAM roles
through AWS Config advanced queries
"""
import logging
import json
import re
import urllib.parse

import pandas

from data_perimeter_helper.referential import (
    config_adv
)
from data_perimeter_helper.referential.ResourceType import ResourceType

logger = logging.getLogger(__name__)
regex_service_name = re.compile(r'(.*)\.amazonaws\.com')
regex_service_linked_role = re.compile(
    r"arn:aws:iam::\d+:role/aws-service-role/([^/]+)/.*"
)


class iam_role(ResourceType):
    """All AWS IAM roles"""
    def __init__(self):
        super().__init__(
            type_name="AWS::IAM::Role",
            unknown_value="IAM_ROLE_NOT_IN_CONFIG_AGGREGATOR"
        )

    def populate(self, *args, **kwargs) -> pandas.DataFrame:
        """ Retrieve all IAM roles inventoried in AWS Config aggregator
    https://github.com/awslabs/aws-config-resource-schema/blob/master/config/properties/resource-types/AWS::IAM::Role.properties.json
        :return: DataFrame with all IAM roles
        """
        config_query = '''
SELECT
    configuration.assumeRolePolicyDocument,
    configuration.roleId,
    configuration.arn,
    configuration.tags
WHERE
    resourceType = 'AWS::IAM::Role'
'''
        logger.debug("[-] Submitting Config advanced query")
        results = config_adv.submit_config_advanced_query(
            query=config_query,
            transform_to_pandas=False,
        )
        logger.debug("[+] Submitting Config advanced query")
        logger.debug("[-] Converting results to DataFrame")
        assert isinstance(results, list)  # nosec: B101
        results = pandas.DataFrame(
            [json.loads(_) for _ in results]
        )
        if len(results.index) == 0:
            return results
        results = pandas.json_normalize(results['configuration'])  # type: ignore
        logger.debug("[+] Converting results to DataFrame")
        self.detect_duplicate(results)
        logger.debug("[-] Enriching result")
        # Flat the list of tags [{'key': "mykey", 'value': "myvalue"}]
        results['listTags'] = [
            iam_role.flat_list_tag(list_tag)
            for list_tag in results['tags']
        ]
        results = results.drop(columns=['tags'])
        # URL decode trust policy
        results['assumeRolePolicyDocument'] = [
            json.loads(urllib.parse.unquote(trust_policy))
            for trust_policy in results['assumeRolePolicyDocument']
        ]
        # Retrieves allowed principals from trust policy
        results['allowedPrincipalList'] = [
            iam_role.get_principal_from_trust_policy(trust_policy)
            for trust_policy in results['assumeRolePolicyDocument']
        ]
        # Checks if any Principal is assumable by an AWS service
        results['isServiceRole'] = [
            iam_role.is_service_role(arn, allowed_principal_list)
            for arn, allowed_principal_list in zip(
                results['arn'], results['allowedPrincipalList']
            )
        ]
        # Checks if any Principal is a Service-linked-role
        results['isServiceLinkedRole'] = [
            iam_role.is_service_linked_role(arn)
            for arn in results['arn']
        ]
        # Dropping uneeded columns
        results = results.drop(columns=['assumeRolePolicyDocument'])
        return results

    @staticmethod
    def detect_duplicate(
        dataframe: pandas.DataFrame
    ) -> bool:
        """Detect duplicate of IAM roles and raise a warning.
        This can happen if AWS Config has been configured to record global
        resources in multiple AWS regions"""
        logger.debug("[-] Checking for duplicates in results")
        if len(dataframe.index) == 0:
            return False
        if "roleId" not in dataframe:
            return False
        lookup_column = "roleId"
        lookup_value = dataframe[lookup_column].iloc[0]
        lookup_first = dataframe.loc[
            dataframe[lookup_column] == lookup_value
        ]
        if len(lookup_first.index) > 1:
            logger.warning(
                "Duplicates records of AWS IAM roles detected in AWS Config "
                "advanced query results. You may have enabled in AWS Config "
                "recording of global resources for multiple AWS regions. "
                "The best practice is to record global resources only in your "
                "main AWS region."
            )
            return True
        return False

    @staticmethod
    def flat_list_tag(list_tag: list) -> dict:
        """Take a list of tag formatted as [{'key': str, 'value': str}] and
        return a flatten dict"""
        tags = {}
        if not isinstance(list_tag, list):
            return tags
        for tag_as_dict in list_tag:
            try:
                tags[tag_as_dict['key']] = tag_as_dict['value']
            except KeyError:
                logger.error("Malformatted tags: %s", tag_as_dict)
                continue
        return tags

    @staticmethod
    def get_principal_from_principal_field(statement: dict) -> list:
        """ Retrieves allowed principals for a given statement in the trust
        relationship policy

        :param statement: statement of the trust relationship policy
        :raises ValueError: if the trust policy contains unexpected values
        :return: List of allowed principals in the statement
            [
                {
                    'type': 'Service' | 'Principal', 'PRINCIPAL_AS_STRING',
                    'principal': str
                }
            ]
        """
        principal_field = statement['Principal']
        list_principal_statement = []
        if isinstance(principal_field, str):
            list_principal_statement = [
                {
                    "type": "PRINCIPAL_AS_STRING",
                    "principal": principal_field
                }
            ]
        elif isinstance(principal_field, dict):
            for principal_type, principal_value in principal_field.items():
                if isinstance(principal_value, list):
                    list_principal_statement.extend([
                        {
                            "type": principal_type,
                            "principal": item
                        } for item in principal_value
                    ])
                elif isinstance(principal_value, str):
                    list_principal_statement.extend([
                        {
                            "type": principal_type,
                            "principal": principal_value
                        }
                    ])
                else:
                    raise ValueError(
                        "principal_value is neither a string or a list"
                    )
        else:
            raise ValueError(
                "principal_field is neither a string or a list"
            )
        return list_principal_statement

    @staticmethod
    def get_principal_from_trust_policy(trust_policy: dict) -> list:
        """ Parse statements of an IAM Trust Policy and call function
        get_principal_from_principal_field for each statement

        :param trust_policy: list of statements in the trust policy
        :return: List of allowed principals in the trust relationship policy
            [
                {
                    'type': 'Service' | 'Principal',
                    'principal': str
                }
            ]
        """
        list_principal_from_trust_policy = []
        list_statement = trust_policy['Statement']
        for statement in list_statement:
            list_principal_from_trust_policy.extend(
                iam_role.get_principal_from_principal_field(statement)
            )
        return list_principal_from_trust_policy

    @staticmethod
    def is_service_role(role_arn: str, list_allowed_principal: list) -> bool:
        """ Return True if an IAM Role is a service role

        :param role_arn: IAM Role ARN
        :param list_allowed_principal: List of allowed principal in the trust
        relationship policy of the IAM Role
        :return: True if Principal is a service role
        """
        if regex_service_linked_role.match(role_arn):
            return False
        for allowed_principal in list_allowed_principal:
            if allowed_principal['type'] == 'Service':
                if regex_service_name.match(allowed_principal['principal']):
                    return True
        return False

    @staticmethod
    def is_service_linked_role(role_arn: str) -> bool:
        """ Return True if IAM Role is a service-linked role

        :param role_arn: Role ARN
        :return: True if IAM Role is a service-linked role
        """
        if regex_service_linked_role.match(role_arn):
            return True
        return False
