#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
'''
This module hosts the class Query from which all data perimeter helper's
queries inherit
'''
import logging
import re
from typing import (
    Callable,
    Union,
    Optional,
    Dict,
    List,
    Tuple,
)

import boto3
import pandas
import awswrangler as wr
from awswrangler.exceptions import (
    QueryFailed
)
from botocore.exceptions import (
    ClientError
)
from pandas._libs.missing import (
    NAType
)

from data_perimeter_helper.queries import (
    helper
)
from data_perimeter_helper.toolbox import (
    utils
)
from data_perimeter_helper.referential.Referential import (
    Referential
)
from data_perimeter_helper.variables import (
    Variables as Var
)


logger = logging.getLogger(__name__)


class Query:
    '''Parent class of all data perimeter helper's queries'''
    queries: Dict[str, 'Query'] = {}
    depends_on_resource_type: List[str] = []
    depends_on_iam_access_analyzer = False

    def __init__(
        self,
        name: str,
        depends_on_resource_type: List[str],
        depends_on_iam_access_analyzer: bool = False,
        use_split_table: bool = False,
    ):
        """Init function of Query class"""
        Query.queries[name] = self
        self.name = name
        self.use_split = use_split_table
        if depends_on_resource_type is not None and len(depends_on_resource_type):
            Query.depends_on_resource_type.extend(depends_on_resource_type)
            Query.depends_on_resource_type = list(set(
                Query.depends_on_resource_type
            ))
        if depends_on_iam_access_analyzer is True:
            Query.depends_on_iam_access_analyzer = True
        logger.debug("[~] Query: %s, has been initialized", name)

    def generate_athena_statement(
        self, account_id: str
    ) -> Union[None, Tuple[str, List[str]]]:
        """Needs to be overridden by childs.
        Generate the Athena query statement"""
        raise NotImplementedError("Must be overridden by childs queries")

    def submit_query(
        self, account_id: str
    ) -> Dict[str, Union[str, pandas.DataFrame]]:
        """Needs to be overridden by childs.
        Submit a query"""
        raise NotImplementedError("Must be overridden by childs queries")

    def submit_athena_query(
        self,
        query_name: str,
        account_id: str
    ) -> Tuple[str, pandas.DataFrame]:
        """Generate the Athena query and then submit it"""
        context_infos = f"(account_id: {account_id} | query: {query_name}"\
            f" | use_param: {Var.use_parameterized_queries})"
        logger.debug("[-] Generating Athena query %s", context_infos)
        tuple_query_param = self.generate_athena_query(
            function_generate_statement=self.generate_athena_statement,
            account_id=account_id
        )
        if tuple_query_param is None:
            logger.warning("[!] No query generated %s", context_infos)
            return "", pandas.DataFrame()
        query, params = tuple_query_param
        readable_query = Query.generate_readable_query(query, params)
        logger.debug("[+] Generating Athena query %s", context_infos)
        logger.debug("[-] Executing Athena query %s", context_infos)
        if Var.use_parameterized_queries is True:
            result = self.read_sql_query(
                query, params, query_name, account_id,
            )
        else:
            result = self.read_sql_query(
                readable_query, [], query_name, account_id,
            )
        logger.debug(readable_query)
        logger.debug("[+] Executing Athena query %s", context_infos)
        return readable_query, result

    @staticmethod
    def _exception_read_sql_query(
        query: str,
        params: List[str],
        query_name: str,
        account_id: str
    ) -> None:
        """Helper to print error when a query fails"""
        logger.error("Query: %s", query)
        if Var.use_parameterized_queries is True:
            logger.error(
                "Readable query: %s",
                Query.generate_readable_query(query, params)
            )
        logger.error(
            "The query `%s` for account `%s` has failed",
            query_name, account_id
        )

    @staticmethod
    def read_sql_query(
        query: str,
        params: List[str],
        query_name: str,
        account_id: str,
    ) -> pandas.DataFrame:
        """Submit an Athena query"""
        try:
            boto3_session_thread = boto3.session.Session(
                profile_name=Var.profile_athena_access,
                region_name=Var.region
            )
            if Var.print_query:
                logger.info("Athena query:\n%s", query)
            exception_raised = False
            read_sql_params = {
                "sql": query,
                "workgroup": Var.athena_workgroup,
                "database": Var.athena_database,
                "ctas_approach": Var.athena_ctas_approach,
                "boto3_session": boto3_session_thread,
                "use_threads": True,
            }
            if Var.use_parameterized_queries is True:
                read_sql_params["params"] = params
                read_sql_params["paramstyle"] = "qmark"
                return wr.athena.read_sql_query(**read_sql_params)  # type: ignore
            return wr.athena.read_sql_query(**read_sql_params)  # type: ignore
        except ClientError as error:
            logger.error("[!] Error from AWS client:\n%s", error.response)  # nosemgrep: logging-error-without-handling
            exception_raised = True
            if error.response['Error']['Code'] == 'AccessDeniedException':
                logger.error(
                    "[!] Current principal is not authorized to perform"
                    " action on [athena or s3 or kms]"
                )
            raise
        except QueryFailed as error:
            exception_raised = True
            logger.error(error)  # nosemgrep: logging-error-without-handling
            raise
        finally:
            if exception_raised is True:
                Query._exception_read_sql_query(
                    query, params, query_name, account_id
                )

    @staticmethod
    def generate_athena_query(
        function_generate_statement: Callable,
        account_id: str,
        post_statement: Optional[str] = None
    ) -> Union[Tuple[str, List[str]], None]:
        """Generate the Athena SQL query by calling Query object function
        <function_generate_statement>. Returns None if the function
        <function_generate_statement> returns None. Else returns the generated
        SQL query"""
        query = ""
        stmt, params = function_generate_statement(account_id)
        if stmt is None:
            return None
        if helper.athena_cloudtrail_with_union():
            params.extend(params)
            stmt_mgmt_event = stmt.replace(
                "__ATHENA_TABLE_NAME_PLACEHOLDER__",
                Var.athena_table_name_mgmt_event
            )
            stmt_data_event = stmt.replace(
                "__ATHENA_TABLE_NAME_PLACEHOLDER__",
                Var.athena_table_name_data_event
            )
            query = f'''{stmt_mgmt_event}
UNION ALL
{stmt_data_event}
'''
        else:
            query = stmt.replace(
                "__ATHENA_TABLE_NAME_PLACEHOLDER__",
                Var.athena_table_name_mgmt_data_event
            )
        if post_statement is None:
            post_statement = '''-- Default Post Statement'''
            sql_limit = helper.get_athena_sql_limit(account_id)
            if sql_limit != 0:
                post_statement += f"\nLIMIT {sql_limit}"
        query += post_statement
        return query, params

    @staticmethod
    def generate_readable_query(query: str, params: List[str]) -> str:
        """Replace question marks from a parameterized query
        with associated parameters to ease readability"""
        copy_params = params.copy()

        def get_param():
            if len(copy_params) > 0:
                return copy_params.pop(0)
            raise ValueError(
                "Cannot generate query - number of parameter does not match"
            )
        return re.sub(r'\?(?![i])', lambda x: get_param(), query)

    def add_column_vpc_id(
        self,
        dataframe: pandas.DataFrame
    ) -> None:
        """Add column vpcid to provided DataFrame"""
        logger.debug("[~] Enriching data with column: vpcid")
        if not utils.df_columns_exist(
            dataframe,
            {'vpcendpointid', 'sourceipaddress'}
        ):
            logger.error(
                "Unable to perform operation"
                " `add_column_vpc_id`"
                " for query: %s",
                self.name
            )
            return
        dataframe['vpcId'] = [
            Referential.get_resource_attribute(
                resource_type="AWS::EC2::VPCEndpoint",
                lookup_value=vpce_id,
                lookup_column='vpcEndpointId',
                attribute='vpcId'
            )
            if not pandas.isna(vpce_id) and "amazonaws" not in ip
            else pandas.NA
            for vpce_id, ip in zip(
                dataframe['vpcendpointid'],
                dataframe['sourceipaddress']
            )
        ]

    def add_column_vpce_account_id(
        self,
        dataframe: pandas.DataFrame
    ) -> None:
        """Add column vpceAccountId to provided dataframe"""
        logger.debug("[~] Enriching data with column: vpceAccountId")
        if not utils.df_columns_exist(
            dataframe,
            {'vpcendpointid', 'sourceipaddress'}
        ):
            logger.error(
                "Unable to perform operation"
                " `add_column_vpce_account_id`"
                " for query: %s",
                self.name
            )
            return
        dataframe['vpceAccountId'] = [
            Referential.get_resource_attribute(
                resource_type="AWS::EC2::VPCEndpoint",
                lookup_value=vpce_id,
                lookup_column='vpcEndpointId',
                attribute='ownerId'
            )
            if not pandas.isna(vpce_id) and "amazonaws" not in ip
            else pandas.NA
            for vpce_id, ip in zip(
                dataframe['vpcendpointid'],
                dataframe['sourceipaddress']
            )
        ]

    def add_column_is_assumable_by(
        self,
        dataframe: pandas.DataFrame
    ) -> None:
        """Add column isAssumableBy to provided DataFrame"""
        logger.debug("[~] Enriching data with column: isAssumableBy")
        list_account_id = helper.get_list_account_id()
        if list_account_id is None:
            return
        if not utils.df_columns_exist(
            dataframe,
            {'principal_accountid', 'principalid'}
        ):
            logger.error(
                "Unable to perform operation"
                " `add_column_is_assumable_by`"
                " for query: %s",
                self.name
            )
            return
        dataframe['isAssumableBy'] = [
            "PRINCIPAL_NOT_IN_ORGANIZATION"
            if pandas.isna(account_id) or account_id not in list_account_id
            else (
                Referential.get_resource_attribute(
                    resource_type="AWS::IAM::Role",
                    lookup_value=role_id.split(
                        ":"
                    )[0] if ":" in role_id else role_id,
                    lookup_column='roleId',
                    attribute='allowedPrincipalList'
                )
                if not pandas.isna(role_id) else pandas.NA
            )
            for account_id, role_id in zip(
                dataframe['principal_accountid'], dataframe['principalid']
            )
        ]

    def add_column_is_service_role(
        self,
        dataframe: pandas.DataFrame
    ) -> None:
        """Add column isServiceRole to provided DataFrame"""
        logger.debug("[~] Enriching data with column: isServiceRole")
        list_account_id = helper.get_list_account_id()
        if list_account_id is None:
            return
        if not utils.df_columns_exist(
            dataframe,
            {'principal_accountid', 'principalid'}
        ):
            logger.error(
                "Unable to perform operation"
                " `add_column_is_service_role`"
                " for query: %s",
                self.name
            )
            return
        dataframe['isServiceRole'] = [
            "PRINCIPAL_NOT_IN_ORGANIZATION"
            if pandas.isna(account_id) or account_id not in list_account_id
            else (
                Referential.get_resource_attribute(
                    resource_type="AWS::IAM::Role",
                    lookup_value=role_id.split(":")[0] if ":" in role_id else role_id,
                    lookup_column='roleId',
                    attribute='isServiceRole'
                )
                if not pandas.isna(role_id) else pandas.NA
            )
            for account_id, role_id in zip(
                dataframe['principal_accountid'], dataframe['principalid']
            )
        ]

    def add_column_is_service_linked_role(
        self,
        dataframe: pandas.DataFrame
    ) -> None:
        """Add column isServiceLinkedRole to provided DataFrame"""
        logger.debug("[~] Enriching data with column: isServiceLinkedRole")
        list_account_id = helper.get_list_account_id()
        if list_account_id is None:
            return
        if not utils.df_columns_exist(
            dataframe,
            {'principal_accountid', 'principalid'}
        ):
            logger.error(
                "Unable to perform operation"
                " `add_column_is_service_linked_role`"
                " for query: %s",
                self.name
            )
            return
        dataframe['isServiceLinkedRole'] = [
            "PRINCIPAL_NOT_IN_ORGANIZATION"
            if pandas.isna(account_id) or account_id not in list_account_id
            else (
                Referential.get_resource_attribute(
                    resource_type="AWS::IAM::Role",
                    lookup_value=role_id.split(":")[0] if ":" in role_id else role_id,
                    lookup_column='roleId',
                    attribute='isServiceLinkedRole'
                )
                if not pandas.isna(role_id) else pandas.NA
            )
            for account_id, role_id in zip(
                dataframe['principal_accountid'], dataframe['principalid']
            )
        ]

    @staticmethod
    def is_service_role_used_by_service_not_in_trust_policy(
        list_service_trust_policy: Union[List[str], NAType],
        sourceipaddress: str
    ) -> bool:
        """Return True is the Principal is a service role used from an
        AWS service not present in the Principal trust policy.
        Returns False otherwise"""
        # If list_service_trust_policy equals to pandas.NA or is empty
        # the principal is not a service role - False is returned
        if not isinstance(list_service_trust_policy, list):
            return False
        if len(list_service_trust_policy) > 0:
            return False
        # If sourceipaddress is not an AWS service's DNS name, False is returned
        if not sourceipaddress.endswith('amazonaws.com'):
            return False
        # If the call is made from a service in the trust policy
        # False is returned - the call is NOT made on behalf of the principal
        # by a serivce
        if sourceipaddress in list_service_trust_policy:
            return False
        return True

    def remove_calls_from_service_on_behalf_of_principal(
        self,
        dataframe: pandas.DataFrame
    ) -> pandas.DataFrame:
        """Remove a subset of API calls performed by an AWS service using
        forward access sessions (FAS)"""
        logger.debug(
            "[~] Removing calls by service role from an AWS "
            "service not in the service role's trust policy"
        )
        if not utils.df_columns_exist(
            dataframe,
            {
                'isAssumableBy', 'sourceipaddress', 'isServiceRole'
            }
        ):
            logger.error(
                "Unable to perform operation"
                " `remove_calls_from_service_on_behalf_of_principal`"
                " for query: %s",
                self.name
            )
            return dataframe
        # 1. Drop API calls by service role from an AWS service not in the
        # service role's trust policy
        # 1.1 Creates a column name with a list of all AWS services contained
        # in the trust policy
        dataframe['isAssumableByAWServiceName'] = [
            [
                item.get('principal', '')
                for item in is_assumable_by
                if item.get('type', '') == 'Service'
            ]
            if isinstance(is_assumable_by, list)
            else pandas.NA
            for is_assumable_by in dataframe['isAssumableBy']
        ]
        # 1.2 Create column viaAWSServiceRole_ServiceRole that is set to
        # True if call is made by a service role and coming from
        # an AWS service not in the service role's trust policy
        dataframe['viaAWSServiceRole_ServiceRole'] = [
            Query.is_service_role_used_by_service_not_in_trust_policy(
                list_service_trust_policy,
                sourceipaddress
            )
            for list_service_trust_policy, sourceipaddress in zip(
                dataframe['isAssumableByAWServiceName'],
                dataframe['sourceipaddress']
            )
        ]
        # 1.3 Drop the identified calls
        dataframe = dataframe.drop(
            dataframe[
                dataframe['viaAWSServiceRole_ServiceRole'].isin([True, 'True'])
            ].index
        )
        # 1.4 Drop the columns used only for processing
        dataframe = dataframe.drop(
            columns=[
                'isAssumableByAWServiceName',
                'viaAWSServiceRole_ServiceRole'
            ]
        )
        logger.debug(
            "[~] Removing calls by principals that are not service roles"
            " from AWS service networks"
        )
        # 2. Drop API calls from AWS service networks by principals
        # that are not service roles nor service-linked roles
        # 2.1 Add the column isServiceLinkedRole if it does not exit
        drop_is_service_linked_role = False
        if not utils.df_columns_exist(
            dataframe, {'isServiceLinkedRole'}, log_error=False
        ):
            self.add_column_is_service_linked_role(dataframe)
            drop_is_service_linked_role = True
        dataframe = dataframe.drop(
            dataframe[
                dataframe['isServiceRole'].isin([False, 'False'])
                & dataframe['isServiceLinkedRole'].isin([False, 'False'])
                & dataframe['sourceipaddress'].str.contains("amazonaws")
            ].index
        )
        if drop_is_service_linked_role is True:
            dataframe = dataframe.drop(columns=['isServiceLinkedRole'])
        return dataframe

    def remove_calls_by_service_linked_role(
        self,
        dataframe: pandas.DataFrame
    ) -> pandas.DataFrame:
        """Remove API calls performed by service-linked roles.
        You can filter in the Athena query, API calls made by the selected
        account service-linked roles using the field `useridentity.sessioncontext.sessionissuer.arn`.
        For cross-account API calls, the field `useridentity.sessioncontext.sessionissuer.arn` is NULL.
        Use can use this function in your data processing logic to remove
        cross-account API calls by service-linked roles"""
        drop_is_service_linked_role = False
        # Add the `isServiceLinkedRole` column if it does not exist
        if not utils.df_columns_exist(
            dataframe, {'isServiceLinkedRole'}, log_error=False
        ):
            self.add_column_is_service_linked_role(dataframe)
            drop_is_service_linked_role = True
        dataframe = dataframe.drop(
            dataframe[
                dataframe['isServiceLinkedRole'].isin([True, 'True'])
            ].index
        )
        if drop_is_service_linked_role is True:
            dataframe = dataframe.drop(columns=['isServiceLinkedRole'])
        return dataframe

    def remove_expected_vpc_id(
        self,
        account_id,
        dataframe: pandas.DataFrame
    ) -> pandas.DataFrame:
        """Remove API calls from expected VPCs ids"""
        logger.debug("[~] Removing calls performed from expected VPC IDs")
        if not utils.df_columns_exist(
            dataframe,
            {'vpcId'}
        ):
            logger.error(
                "Unable to perform operation"
                " `remove_expected_vpc_id`"
                " for query: %s",
                self.name
            )
            return dataframe
        list_expected_vpc = Var.get_account_configuration(
            account_id=account_id,
            configuration_key='network_perimeter_expected_vpc'
        )
        if len(list_expected_vpc):
            dataframe = dataframe.drop(
                dataframe[
                    dataframe['vpcId'].isin(list_expected_vpc)
                ].index
            )
        return dataframe

    @staticmethod
    def remove_resource_exception(
        dataframe: pandas.DataFrame,
        lookup_column: str,
        resource_id_value: str,
        exceptions: dict,
        list_exception_type_to_consider: list
    ) -> pandas.DataFrame:
        """Remove exceptions types for a given resource type and
        exception type"""
        for exception_type, exception in exceptions.items():
            logger.debug(
                "exception_type:%s, exception:%s, list_exception:%s",
                exception_type, exception, list_exception_type_to_consider
            )
            if exception_type not in list_exception_type_to_consider:
                continue
            if exception_type in (
                'network_perimeter_trusted_principal',
                'identity_perimeter_trusted_principal'
            ):
                dataframe = dataframe.drop(
                    dataframe[
                        (dataframe[lookup_column] == resource_id_value)
                        & (dataframe['principal_arn'].str.contains(
                            '|'.join(exception)
                        ))
                    ].index
                )
            elif exception_type == "network_perimeter_expected_vpc_endpoint":
                dataframe = dataframe.drop(
                    dataframe[
                        (dataframe[lookup_column] == resource_id_value)
                        & (dataframe['vpcendpointid'].str.contains(
                            '|'.join(exception)
                        ))
                    ].index
                )
            elif exception_type == "network_perimeter_expected_vpc":
                dataframe = dataframe.drop(
                    dataframe[
                        (dataframe[lookup_column] == resource_id_value)
                        & (dataframe['vpcId'].str.contains('|'.join(exception)))
                    ].index
                )
            elif exception_type == "network_perimeter_expected_public_cidr":
                for cidr in exception:
                    dataframe = dataframe.drop(
                        dataframe[
                            (dataframe[lookup_column] == resource_id_value)
                            & (dataframe['sourceipaddress'].map(lambda ip: helper.is_ip_in_cidr(ip, cidr)))
                        ].index
                    )
        return dataframe

    @staticmethod
    def remove_all_resource_exception(
        account_id: str,
        dataframe: pandas.DataFrame,
        resource_type: str,
        resource_id_column_name: str,
        list_exception_type_to_consider: list
    ) -> pandas.DataFrame:
        """Get exceptions for a given account/resource type;
        then remove exceptions for each resource"""
        conf = Var.get_account_resource_exception(
            account_id=account_id,
            resource_type=resource_type
        )
        logger.debug("Exceptions: %s", conf)
        for resource_name, exceptions in conf.items():
            dataframe = Query.remove_resource_exception(
                dataframe,
                resource_id_column_name,
                resource_name,
                exceptions,
                list_exception_type_to_consider
            )
        return dataframe
