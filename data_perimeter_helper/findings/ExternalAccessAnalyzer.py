#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Defines the class ExternalAccessAnalyzer, which represents an AWS IAM Access Analyzer external access analyzer"""
import logging
from typing import (
    List,
    Dict,
    Optional,
    Union
)
from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed as concurrent_completed,
    Future
)

import pandas
from botocore.client import (BaseClient)
from botocore.exceptions import (
    ClientError
)
from botocore.config import (
    Config
)
from tqdm import (
    tqdm
)

from data_perimeter_helper.variables import Variables as Var
from data_perimeter_helper.toolbox import utils

logger = logging.getLogger(__name__)


class ExternalAccessAnalyzer():
    """Represents an AWS IAM Access Analyzer external access analyzer"""
    enabled = False
    cache_describe_findings: Dict[str, List[Dict[str, str]]] = {}
    account_id: Optional[str] = None
    list_enabled_region: List[str] = []
    analyzer_arn_per_region: Dict[str, str] = {}

    cache_boto3_client: Dict[str, Dict[str, BaseClient]] = {}
    boto3_config_increase_retry = Config(
        retries={
            'max_attempts': 15
        }
    )

    def __init__(self) -> None:
        if Var.external_access_findings not in (
            'IAM_ACCESS_ANALYZER', 'SECURITY_HUB'
        ):
            logger.info(
                "[i] AWS IAM Access Analyzer external findings are not"
                " retrieved"
            )
            return
        if ExternalAccessAnalyzer.enabled is True:
            return
        ExternalAccessAnalyzer.enabled = True
        self.get_analyzer_arn_per_region()

    @classmethod
    def is_enabled(cls) -> bool:
        """Return True if the data source 'IAM Access Analyzer' is enabled"""
        return cls.enabled is True

    @classmethod
    def get_boto3_client(
        cls,
        service_name: str = 'accessanalyzer',
        region_name: Optional[str] = None
    ):
        """Generate a boto3 client or retrieve it from cache"""
        if region_name is None:
            region_name = Var.region
        if region_name in cls.cache_boto3_client:
            if service_name in cls.cache_boto3_client[region_name]:
                return cls.cache_boto3_client[region_name][service_name]
        assert Var.session_iam_aa is not None  # nosec: B101
        client = Var.session_iam_aa.client(
            service_name,
            region_name=region_name,
            config=cls.boto3_config_increase_retry
        )
        assert isinstance(region_name, str)  # nosec: B101
        cls.cache_boto3_client.setdefault(region_name, {}).setdefault(
            service_name, client)
        return client

    @classmethod
    def get_enabled_regions(cls):
        """Get enabled AWS regions"""
        if len(cls.list_enabled_region) > 0:
            return cls.list_enabled_region
        list_region_code = []
        account_client = cls.get_boto3_client('account')
        try:
            list_region = account_client.list_regions(
                RegionOptStatusContains=[
                    'ENABLED', 'ENABLED_BY_DEFAULT'
                ]
            ).get('Regions', [])
        except ClientError as error:
            logger.error("[!] Error from AWS client:\n%s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Access denied to AWS Account Management"
                    " [account:ListRegions]"
                )
            raise
        for region in list_region:
            list_region_code.append(
                region['RegionName']
            )
        cls.list_enabled_region = list_region_code
        return list_region_code

    @classmethod
    def get_analyzer_arn_per_region(cls):
        """Get external access analyzer ARNs for all enabled regions"""
        if len(cls.analyzer_arn_per_region) > 0:
            return cls.analyzer_arn_per_region
        list_enabled_region = cls.get_enabled_regions()
        pool = {}
        log_msg = "Discovering the AWS IAM Access Analyzer external access"\
            " analyzer ARNs for all enabled regions..."
        tqdm.write(utils.Icons.HAND_POINTING + log_msg)
        logger.debug(log_msg)
        with ThreadPoolExecutor(
            max_workers=Var.thread_max_worker
        ) as executor:
            for region in list_enabled_region:
                pool.update({
                    executor.submit(
                        cls.get_organization_external_access_analyzer_arn,
                        region
                    ): {}
                })
            for request_in_pool in concurrent_completed(pool):
                exception = request_in_pool.exception()
                if exception:
                    raise exception
        logger.debug(cls.analyzer_arn_per_region)
        log_msg = f"{len(cls.analyzer_arn_per_region)} external access"\
            " analyzer ARNs retrieved! (source: AWS IAM Access Analyzer)"
        tqdm.write(
            utils.color_string(
                utils.Icons.FULL_CHECK_GREEN + log_msg, utils.Colors.GREEN_BOLD
            )
        )
        return cls.analyzer_arn_per_region

    @classmethod
    def get_cache_key_describe_findings(
        cls,
        region: str,
        get_only_active: bool,
        account_id: Optional[str],
        resource_type: Optional[str],
    ):
        """Get an unique cache key entry for the function describe_findings"""
        active = 'ACTIVE' if get_only_active else 'RESOLVED'
        account_id = 'ALL' if account_id is None else account_id
        resource_type = 'ALL' if resource_type is None else resource_type
        return f"{region}_{active}_{account_id}_{resource_type}"

    @classmethod
    def describe_findings_all_regions(
        cls,
        get_only_active: bool = True,
        account_id: Optional[str] = None,
        resource_type: Optional[str] = None,
    ):
        result = []
        pool: Dict[Future, Dict[str, str]] = {}
        with ThreadPoolExecutor(
            max_workers=Var.thread_max_worker
        ) as executor:
            for region in cls.analyzer_arn_per_region:
                pool.update({
                    executor.submit(
                        cls.describe_findings,
                        region,
                        get_only_active,
                        account_id,
                        resource_type
                    ): {}
                })
            for request_in_pool in concurrent_completed(pool):
                exception = request_in_pool.exception()
                if exception:
                    raise exception
                result.extend(request_in_pool.result())
        if account_id is not None:
            f"{len(result)} external access findings retrieved!"
            f" for account {account_id} (source: AWS IAM Access Analyzer)"
        else:
            log_msg = f"{len(result)} external access findings retrieved!"\
                      " (source: AWS IAM Access Analyzer)"
        tqdm.write(
            utils.color_string(
                utils.Icons.FULL_CHECK_GREEN + log_msg, utils.Colors.GREEN_BOLD
            )
        )
        logger.debug(log_msg)
        return result

    @classmethod
    def describe_findings_all_regions_as_df(
        cls,
        get_only_active: bool = True,
        account_id: Optional[str] = None,
        resource_type: Optional[str] = None,
    ):
        if not cls.is_enabled():
            logger.info("[!] Data source 'IAM Access Analyzer' is disabled")
            return pandas.DataFrame()
        result = cls.describe_findings_all_regions(
            get_only_active, account_id, resource_type
        )
        logger.debug("[~] Converting results to pandas DataFrame...")
        df = pandas.DataFrame(result)
        return df

    @classmethod
    def describe_findings(
        cls,
        region: str,
        get_only_active: bool = True,
        account_id: Optional[str] = None,
        resource_type: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """List IAM Access Analyzer findings and then describe them"""
        result = []
        if not cls.is_enabled():
            logger.debug("[!] Data source 'IAM Access Analyzer' is disabled")
            return []
        cache_key = cls.get_cache_key_describe_findings(
            region, get_only_active, account_id, resource_type
        )
        if cache_key in cls.cache_describe_findings:
            logger.debug("[+] Found cached results for key %s", cache_key)
            return cls.cache_describe_findings[cache_key]
        if account_id is not None:
            log_msg = "Retrieving external access findings for"\
                f" account {account_id} in region {region}"\
                " (source: AWS IAM Access Analyzer)..."
        else:
            log_msg = "Retrieving external access findings for"\
                f" region {region} (source: AWS IAM Access Analyzer)..."
        tqdm.write(f"{utils.Icons.HAND_POINTING}{log_msg}")
        list_account_id = None if account_id is None else [account_id]
        list_resource_type = None if resource_type is None else [resource_type]
        list_finding = cls.api_list_findings_v2(
            region=region,
            get_only_active=get_only_active,
            list_account_id=list_account_id,
            list_resource_type=list_resource_type
        )
        if len(list_finding) == 0:
            logger.debug(
                "[+] No IAM Access Analyzer findings found for region %s",
                region
            )
        else:
            result = cls.api_get_finding_v2_thread(region, list_finding)
        cls.cache_describe_findings[cache_key] = result
        return result

    @classmethod
    def describe_findings_as_df(
        cls,
        region: str,
        get_only_active: bool = True,
        account_id: Optional[str] = None,
        resource_type: Optional[str] = None,
    ):
        """List IAM Access Analyzer findings, describe them and convert
        results to a DataFrame"""
        if not cls.is_enabled():
            logger.info("[!] Data source 'IAM Access Analyzer' is disabled")
            return pandas.DataFrame()
        result = cls.describe_findings(
            region=region,
            get_only_active=get_only_active,
            account_id=account_id,
            resource_type=resource_type
        )
        logger.debug("[-] Converting results to pandas DataFrame")
        return pandas.DataFrame(result)

    @classmethod
    def api_list_analyzers(
        cls,
        region
    ) -> List[Dict[str, str]]:
        """List AWS IAM Access Analyzer analyzers"""
        try:
            logger.debug("[~] Listing IAM Access Analyzer analysers...")
            return cls.get_boto3_client(region_name=region)\
                .list_analyzers().get('analyzers', [])
        except ClientError as error:
            logger.error("[!] Error from AWS client:\n%s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Access denied to AWS IAM Access Analyzer"
                    " [ListAnalyzer]"
                )
            raise

    @classmethod
    def get_organization_external_access_analyzer_arn(
        cls,
        region: str,
        list_analyzer: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        """Get the ARN of an organization external access analyzer"""
        if list_analyzer is None:
            list_analyzer = cls.api_list_analyzers(region)
            logger.debug(list_analyzer)
        for analyzer in list_analyzer:
            if analyzer.get('type') == 'ORGANIZATION':
                analyzer_arn = analyzer['arn']
                logger.debug(
                    "[~] Organization external access analyzer ARN: %s",
                    analyzer_arn
                )
                cls.analyzer_arn_per_region[region] = analyzer_arn
                return True
        logger.debug(
            "[!] No organization external access analyzer found for region %s",
            region
        )
        return False

    @classmethod
    def api_list_findings_v2(
        cls,
        region: str,
        get_only_active: bool = True,
        list_account_id: Optional[List[str]] = None,
        list_resource_type: Optional[List[str]] = None,
    ) -> List[Dict[str, str]]:
        """List findings of an organization external access analyzer"""
        list_finding: List[Dict[str, str]] = []
        if region not in cls.analyzer_arn_per_region:
            return list_finding
        filter: Dict[str, Dict[str, List[str]]] = {}
        if get_only_active is True:
            filter['status'] = {
                'eq': ['ACTIVE']
            }
        if list_account_id is not None:
            filter['resourceOwnerAccount'] = {
                'eq': list_account_id
            }
        if list_resource_type is not None:
            filter['resourceType'] = {
                'eq': list_resource_type
            }
        try:
            analyzer_arn = cls.analyzer_arn_per_region[region]
            logger.debug(
                "[~] Listing findings for analyzer: %s...", analyzer_arn
            )
            paginator = cls.get_boto3_client(region_name=region)\
                .get_paginator('list_findings_v2')
            page_iterator = paginator.paginate(
                analyzerArn=analyzer_arn,
                filter=filter
            )
            for page in page_iterator:
                for item in page['findings']:
                    list_finding.append(item)
            logger.debug("[~] %s findings found", len(list_finding))
            return list_finding
        except ClientError as error:
            logger.error("[!] Error from AWS client:\n%s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error("[!] Access denied to AWS IAM Access Analyzer [ListFindings]")
            raise

    @classmethod
    def api_get_finding_v2(
        cls,
        region: str,
        list_finding: List[Dict[str, str]]
    ) -> List[Dict[str, Union[str, None]]]:
        """Get an access analyzer finding"""
        list_finding_summary: List[Dict[str, Union[str, None]]] = []
        if region not in cls.analyzer_arn_per_region:
            return list_finding_summary
        try:
            for finding in list_finding:
                finding_id = finding.get('id')
                res: dict = \
                    cls.get_boto3_client(region_name=region).get_finding_v2(
                        analyzerArn=cls.analyzer_arn_per_region[region],
                        id=finding_id
                    )
                findings_details = res.get('findingDetails')
                assert isinstance(findings_details, list)  # nosec: B101
                details = findings_details[0].get('externalAccessDetails')
                assert isinstance(details, dict)  # nosec: B101
                list_finding_summary.append({
                    'id': res.get('id'),
                    'analyzer_region': region,
                    'resource': res.get('resource'),
                    'resourceType': res.get('resourceType'),
                    'resourceOwnerAccount': res.get('resourceOwnerAccount'),
                    'isPublic': details.get('isPublic'),
                    'principal': details.get('principal'),
                    'condition': details.get('condition'),
                    'action': details.get('action'),
                    'sources': details.get('sources'),
                })
            return list_finding_summary
        except ClientError as error:
            logger.error("[!] Error from AWS client:\n%s", error.response)  # nosemgrep: logging-error-without-handling
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error("[!] Access denied to AWS IAM Access Analyzer [access-analyzer:GetFinding]")
            if error.response['Error']['Code'] == 'TooManyRequestsException':
                logger.error("[!] Too many requests to AWS IAM Access Analyzer [access-analyzer:GetFinding]")
            raise

    @classmethod
    def api_get_finding_v2_thread(
        cls,
        region,
        list_finding: List[Dict[str, str]]
    ) -> List[Dict[str, str]]:
        """Get list of access analyzer findings with threading"""
        list_finding_summary: List[Dict[str, str]] = []
        pool = {}
        offset = 0
        nb_finding = len(list_finding)
        logger.debug(
            "%s external access findings to retrieve for region %s",
            nb_finding, region
        )
        max_batch_size = 25
        logger.debug("[~] Starting %s thread worker(s)", 2)
        with tqdm(
            total=nb_finding,
            desc=f"External access findings ({region}) (source: AWS IAM Access Analyzer): ",
            unit="findings",
            leave=False
        ) as pbar:
            with ThreadPoolExecutor(
                    max_workers=2
            ) as executor:
                batch_index = 0
                for offset in range(0, nb_finding, max_batch_size):
                    batch = list_finding[offset:offset + max_batch_size]
                    batch_size = len(batch)
                    logger.debug(
                        "Batch #%s: [%s - %s], size: %s",
                        batch_index, offset, offset + max_batch_size, batch_size
                    )
                    pool.update({
                        executor.submit(
                            cls.api_get_finding_v2,
                            region,
                            batch
                        ): {
                            'p_update': batch_size
                        }
                    })
                    batch_index += 1
                for request_in_pool in concurrent_completed(pool):
                    exception = request_in_pool.exception()
                    if exception:
                        raise exception
                    result = request_in_pool.result()
                    if isinstance(result, list):
                        list_finding_summary.extend(result)  # type: ignore
                    pbar.update(pool[request_in_pool]['p_update'])
        return list_finding_summary
