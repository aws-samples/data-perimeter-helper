<!-- # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0 -->
# Description

You can use `common` queries to analyze activity in your AWS organization against data perimeter objectives without focusing on a specific AWS service. Example: review API calls from public IPv4 addresses.    
The `common` queries are prefixed with the keyword `common` and are **not** tied to a specific AWS service.


## List of common queries

* [common_from_public_cidr_ipv4](#query-name-common_from_public_cidr_ipv4)
* [common_network_perimeter_ipv4](#query-name-common_network_perimeter_ipv4)
* [common_only_denied](#query-name-common_only_denied)
* [common_service_linked_roles](#query-name-common_service_linked_roles)
* [common_service_role_from_aws](#query-name-common_service_role_from_aws)
* [common_through_vpc_endpoint](#query-name-common_through_vpc_endpoint)


# Query name: common_from_public_cidr_ipv4

### Query description

List AWS API calls made from public IPv4 addresses.   
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls by reviewing API calls made from public IPv4 addresses. You can then use the global condition key [aws:SourceIp](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-sourceip) to help ensure your API calls are only made from expected public CIDR ranges.

### Query results filtering

Below filters are applied:
- Remove API calls made by service-linked roles in the selected account.
- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
- Remove API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.
- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
- Remove API calls made through VPC endpoints - `vpcendpointid` field in CloudTrail log is `NULL`.
- Remove API calls with errors.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Remove API calls made by service-linked roles in the selected account
    AND COALESCE(NOT regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)'), True)
    -- Remove IPv6 calls and calls from AWS service networks
    AND COALESCE(NOT regexp_like(sourceipaddress, '(?i)(:|amazonaws|Internal)'), True)
    -- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
    {network_perimeter_expected_public_cidr}
    -- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
    {network_perimeter_trusted_account}
    -- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
    {network_perimeter_trusted_principal_arn}
    {network_perimeter_trusted_principal_id}
    -- Remove API calls made through VPC endpoints - `vpcendpointid` field in CloudTrail log is `NULL`.
    AND vpcendpointid IS NULL
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `isAssumableBy`, `isServiceRole`, `isServiceLinkedRole`.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
</details>



# Query name: common_network_perimeter_ipv4

### Query description

List AWS API calls that do not align with your expected networks definition documented in the `data perimeter helper` configuration file.  
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls.
If the number of results is too high, we recommend to use a `data perimeter helper` query tied to an AWS service (example: `s3` queries for [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)).
    
### Query results filtering

Below filters are applied:
- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.
- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
- Remove API calls made by service-linked roles in the selected account.
- Remove API calls with errors.
- Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    useragent,
    eventsource,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
    AND COALESCE(NOT regexp_like(sourceipaddress, ':'), True)
    -- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
    {network_perimeter_expected_public_cidr}
    -- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator
    {remove_selected_account_vpce}
    -- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
    {network_perimeter_expected_vpc_endpoint}
    -- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
    {network_perimeter_trusted_account}
    -- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
    {network_perimeter_trusted_principal_arn}
    {network_perimeter_trusted_principal_id}
    -- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
    AND useridentity.principalid != 'AWSService'
    -- Remove API calls made by service-linked roles in the selected account
    AND COALESCE(NOT regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)'), True)
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    useragent,
    eventsource,
    vpcendpointid,
    sourceipaddress
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `vpcId`, `vpceAccountId`, `isAssumableBy`, `isServiceRole`.
- Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.
</details>



# Query name: common_only_denied

### Query description

List AWS API calls with an access denied error code.
You can use this query to troubleshoot access denied error messages while developing your data perimeter controls or after deploying them.
    
### Query results filtering

Below filters are applied:
- Keep only API calls with access denied error code.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    errorcode,
    errormessage,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Keep only API calls with access denied error code.
    AND errorcode in ('Client.UnauthorizedOperation', 'Client.InvalidPermission.NotFound', 'Client.OperationNotPermitted', 'AccessDenied')
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    errorcode,
    errormessage,
    sourceipaddress,
    vpcendpointid
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `isAssumableBy`, `isServiceRole`, `isServiceLinkedRole`.
</details>



# Query name: common_service_linked_roles

### Query description

List AWS API calls made by service-linked roles (SLRs).   
You can use this query to review the API calls performed by your service-linked roles.
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) and [**identity perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls.
    
### Query results filtering

Below filters are applied:
- Keep only API calls made by service-linked roles in the selected account - `useridentity.sessioncontext.sessionissuer.arn` field in CloudTrail log contains `:role/aws-service-role/`. For cross-account API calls, the field `useridentity.sessioncontext.sessionissuer.arn` is `NULL`, therefore, you need to run this query in each account you would like to analyze.
- Remove API calls with errors.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Keep only API calls made by service-linked roles in the selected account - `useridentity.sessioncontext.sessionissuer.arn` field in CloudTrail log contains `:role/aws-service-role/`. For cross-account API calls, the field `useridentity.sessioncontext.sessionissuer.arn` is NULL, therefore, you need to run this query in each account you would like to analyze.
    AND regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)')
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress
```
</details>



# Query name: common_service_role_from_aws

### Query description

List AWS API calls made by service roles from AWS service networks.   
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls.
    
### Query results filtering

Below filters are applied:
- Keep only API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.
- Keep only API calls performed by assumed roles.
- Remove API calls made by service-linked roles in the selected account.
- Remove API calls with errors.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Keep only API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.
    AND regexp_like(sourceipaddress, '(?i)(amazonaws|Internal)')
    -- Keep only API calls performed by assumed roles
    AND useridentity.type = 'AssumedRole'
    -- Remove API calls made by service-linked roles in the selected account
    AND COALESCE(NOT regexp_like(useridentity.sessioncontext.sessionissuer.arn, '(:role/aws-service-role/)'), True)
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `isAssumableBy`, `isServiceRole`.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.
</details>



# Query name: common_through_vpc_endpoint

### Query description

List AWS API calls made through any VPC endpoints.  
You can use this query to accelerate implementation of your [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls by reviewing API calls made through through a VPC endpoint. You can then use the global condition keys [aws:SourceVpce](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-sourcevpce) or [aws:SourceVpc](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-sourcevpc) to ensure that your API calls are only made through your expected VPC endpoint IDs or VPC IDs, respectively.
    
### Query results filtering

Below filters are applied:
- Keep only API calls made through a VPC endpoint.
- Remove API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.
- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
- Remove API calls made via AWS Management Console with `S3Console` and `AWSCloudTrail` user agent - this is to manage temporary situations where the field `vpcendpointid` contains AWS owned VPC endpoint IDs.
- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
- Remove API calls with errors.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    -- Keep only API calls made through a VPC endpoint
    AND vpcendpointid IS NOT NULL
    -- Remove API calls from AWS service networks - `sourceipaddress` field in CloudTrail log equals to an AWS service domain name (example: `athena.amazonaws.com`) or contains `AWS Internal`.
    AND COALESCE(NOT regexp_like(sourceipaddress, '(?i)(amazonaws|Internal)'), True)
    -- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
    {network_perimeter_expected_vpc_endpoint}
    -- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
    {network_perimeter_expected_public_cidr}
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    eventsource,
    eventname,
    sourceipaddress,
    vpcendpointid
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `vpcId`, `vpceAccountId`, `isAssumableBy`, `isServiceRole`.
</details>

