#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Define the class SecurityHub"""
import logging
from typing import (
    Dict,
    List,
    Optional
)

import pandas
from tqdm import (
    tqdm
)
from botocore.exceptions import (
    ClientError
)

from data_perimeter_helper.variables import Variables as Var
from data_perimeter_helper.toolbox import utils
from data_perimeter_helper.findings.ExternalAccessAnalyzer import (
    ExternalAccessAnalyzer
)


logger = logging.getLogger(__name__)


class SecurityHub():
    """Represents an AWS SecurityHub """
    enabled = False
    cache_iam_aa_findings: Dict[str, List[Dict[str, str]]] = {}
    sh_client = None

    def __init__(self) -> None:
        ExternalAccessAnalyzer()
        if Var.external_access_findings != 'SECURITY_HUB':
            return
        if SecurityHub.enabled is True:
            return
        SecurityHub.enabled = True
        assert Var.session_iam_aa is not None  # nosec: B101
        SecurityHub.sh_client = Var.session_iam_aa.client(
            'securityhub',
            region_name=Var.region
        )

    @classmethod
    def is_enabled(cls) -> bool:
        """Return True if the data source 'SecurityHub' is enabled"""
        return cls.enabled is True

    @staticmethod
    def cache_key_iam_aa_findings(
        account_id: Optional[str],
        resource_type: Optional[str]
    ) -> str:
        resource_type = resource_type if resource_type is not None else "ALL"
        account_id = account_id if account_id is not None else "ALL"
        return f"{account_id}_{resource_type}"

    @classmethod
    def get_iam_aa_external_access_findings(
        cls,
        account_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """List all AWS IAM Access Analyzer findings coming from external
        access analyzers with an organization scope"""
        cache_key = cls.cache_key_iam_aa_findings(account_id, resource_type)
        if cache_key in cls.cache_iam_aa_findings:
            return cls.cache_iam_aa_findings[cache_key]
        findings = []
        analyzer_per_region = ExternalAccessAnalyzer\
            .get_analyzer_arn_per_region()
        list_analyzer_arn = list(analyzer_per_region.values())
        nb_analyzer = len(list_analyzer_arn)
        offset = 0
        max_filter_size = 20
        filter_baseline = {
            # Get only findings from AWS IAM Access Analyzer
            'GeneratorId': [
                {
                    'Value': 'aws/access-analyzer',
                    'Comparison': 'EQUALS'
                }
            ],
            # Get only findings that are not archived
            'RecordState': [
                {
                    'Value': 'ARCHIVED',
                    'Comparison': 'NOT_EQUALS'
                }
            ]
        }
        if resource_type is not None:
            filter_baseline['Description'] = [
                {
                    'Comparison': 'PREFIX',
                    'Value': resource_type,
                }
            ]
        if account_id is not None:
            filter_baseline['ProductFields'] = [
                {
                    'Key': 'ResourceOwnerAccount',
                    'Comparison': 'EQUALS',
                    'Value': str(account_id),
                }
            ]
        log_msg = "Retrieving external access findings..."\
            " (source: AWS Security Hub)"
        tqdm.write(utils.Icons.HAND_POINTING + log_msg)
        logger.debug(log_msg)
        for offset in range(0, nb_analyzer, max_filter_size):
            filter = filter_baseline.copy()
            batch = list_analyzer_arn[offset:offset + max_filter_size]
            filter['Id'] = [
                {
                    'Value': analyzer_arn,
                    'Comparison': 'PREFIX'
                }
                for analyzer_arn in batch
            ]
            logger.debug(filter)
            findings.extend(
                SecurityHub.api_get_findings(filter)
            )
        cls.cache_iam_aa_findings[cache_key] = findings
        log_msg = f"{len(findings)} external access findings retrieved!"
        " (source: AWS Security Hub)"
        tqdm.write(
            utils.color_string(
                utils.Icons.FULL_CHECK_GREEN + log_msg, utils.Colors.GREEN_BOLD
            )
        )
        logger.debug(log_msg)
        return findings

    @classmethod
    def get_iam_aa_external_access_findings_as_df(
        cls,
        account_id: Optional[str] = None,
        resource_type: Optional[str] = None
    ) -> pandas.DataFrame:
        """List all AWS IAM Access Analyzer findings coming from external
        access analyzers with an organization scope"""
        findings = cls.get_iam_aa_external_access_findings(
            account_id=account_id,
            resource_type=resource_type
        )
        logger.debug("[~] Converting results to pandas DataFrame...")
        df = pandas.DataFrame(findings)
        return df

    @classmethod
    def get_resource_type_from_description(
        cls,
        description: str
    ) -> str:
        unknown_value = "UNKNOWN"
        if "/" not in description:
            return unknown_value
        resource_type = description.split('/')[0]
        if resource_type.startswith("AWS"):
            return resource_type
        return unknown_value

    @classmethod
    def build_iam_aa_finding(
        cls,
        securityhub_finding
    ) -> Dict[str, str]:
        return {
            'region': securityhub_finding['Region'],
            'resource': securityhub_finding['Resources'][0]['Id'],
            'resourceType': cls.get_resource_type_from_description(
                securityhub_finding['Description']
            ),
            'resourceOwner': securityhub_finding['ProductFields'][
                'ResourceOwnerAccount'],
            'details': securityhub_finding['Resources'][0]['Details']['Other'],
        }

    @classmethod
    def api_get_findings(
        cls,
        filters: Dict[str, List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        findings: List[Dict[str, str]] = []
        assert cls.sh_client is not None  # nosec: B101
        paginator = cls.sh_client.get_paginator('get_findings')
        try:
            page_iterator = paginator.paginate(
                Filters=filters
            )
            for page in page_iterator:
                for item in page['Findings']:
                    findings.append(
                        cls.build_iam_aa_finding(item)
                    )
        except ClientError as error:
            logger.error("[!] Error from AWS client:\n%s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Access denied to AWS Security Hub"
                    " [securityhub:GetFinding]"
                )
            if error.response['Error']['Code'] == 'TooManyRequestsException':
                logger.error(
                    "[!] Too many requests to AWS Security Hub"
                    " [securityhub:GetFinding]"
                )
            raise
        return findings
