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


class account(ResourceType):
    """All accounts"""

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
        return pandas.DataFrame.from_dict(list_account)  # type: ignore

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
