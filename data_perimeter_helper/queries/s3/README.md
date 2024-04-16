<!-- # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0 -->
# Description

You can use `s3` queries to analyze activity in your AWS organization against data perimeter objectives while focusing exclusively on [Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html) AWS API calls.    

The `s3` queries are prefixed with the keyword `s3`.

## List of queries

* [s3_bucket_policy_identity_perimeter_org_boundary](#query-name-s3_bucket_policy_identity_perimeter_org_boundary)
* [s3_bucket_policy_identity_perimeter_ou_boundary](#query-name-s3_bucket_policy_identity_perimeter_ou_boundary)
* [s3_bucket_policy_network_perimeter_ipv4](#query-name-s3_bucket_policy_network_perimeter_ipv4)
* [s3_external_access_org_boundary](#query-name-s3_external_access_org_boundary)
* [s3_scp_network_perimeter_ipv4](#query-name-s3_scp_network_perimeter_ipv4)
* [s3_scp_resource_perimeter](#query-name-s3_scp_resource_perimeter)
* [s3_vpce_policy_resource_perimeter_account_to_not_mine](#query-name-s3_vpce_policy_resource_perimeter_account_to_not_mine)
* [s3_vpce_policy_resource_perimeter_org_to_not_mine](#query-name-s3_vpce_policy_resource_perimeter_org_to_not_mine)

# Query name: s3_bucket_policy_identity_perimeter_org_boundary

### Query description

List AWS API calls made on S3 buckets in the selected account by principals that do **NOT** belong to the same AWS organization, filtering out calls that align with your definition of trusted identities.

You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your S3 buckets at the organization level. You can use the global condition key [aws:PrincipalOrgId](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) to limit access to your resources to principals belonging to your AWS organization.
    
### Query results filtering

Below filters are applied:
- Keep only S3 API calls.
- Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator.
- Remove API calls made by principals belonging to the same AWS organization as the selected account - list of account ID retrieved from AWS Organizations.
- Remove API calls made by principals belonging to identity perimeter trusted accounts - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_account` parameter).
- Remove API calls made by identity perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_principal` parameter).
- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
- Remove preflight requests which are unauthenticated and used to determine the cross-origin resource sharing (CORS) configuration.
- Remove API calls with errors.
- Remove resource specific exceptions.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator
    {keep_selected_account_s3_bucket}
    -- Remove API calls made by principals belonging to the same AWS organization as the selected account - list of account ID retrieved from AWS Organizations
    {remove_org_account_principals}
    -- Remove API calls made by principals belonging to identity perimeter trusted accounts - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_account` parameter).
    {identity_perimeter_trusted_account}
    -- Remove API calls made by identity perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_principal` parameter).
    {identity_perimeter_trusted_principal_arn}
    {identity_perimeter_trusted_principal_id}
    -- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
    -- Remove preflight requests which are unauthenticated and used to determine the cross-origin resource sharing (CORS) configuration
    AND eventname != 'PreflightRequest'
    AND useridentity.principalid != 'AWSService'
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
    vpcendpointid,
    sourceipaddress
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Remove resource specific exceptions.
</details>



# Query name: s3_bucket_policy_identity_perimeter_ou_boundary

### Query description

List AWS API calls made on S3 buckets in the selected account by principals that do **NOT** belong to the same organizational unit (OU) boundary, filtering out calls that align with your definition of trusted identities.

You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your S3 buckets at the organizational unit (OU) level. You can use the global condition key [aws:PrincipalOrgPaths](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgpaths) to limit access to your resources only to principals belonging to specific OUs.

You can declare your OU boundaries in the `data perimeter helper` configuration file (`org_unit_boundary` parameter).
OU boundaries allow you to logically regroup your accounts for analysis based on their location in your AWS organization. For example, you can declare OUs `ou-xxxxx-1111111` and `ou-xxxxx-2222222` (and all OUs contained within them) as your `production` boundary. Then you can run this query for one of the accounts in these OUs to review the API calls made by principals that do **NOT** belong to the same boundary (in this example: non-production accounts).
    
### Query results filtering

Below filters are applied:
- Keep only S3 API calls.
- Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator.
- Remove API calls from principals belonging to the same OU boundary.
- Remove API calls made by principals belonging to identity perimeter trusted accounts - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_account` parameter).
- Remove API calls made by identity perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_principal` parameter).
- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
- Remove preflight requests which are unauthenticated and used to determine the cross-origin resource sharing (CORS) configuration.
- Remove API calls with errors.
- Remove resource specific exceptions.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator
    {keep_selected_account_s3_bucket}
    -- Remove API calls from principals belonging to the same OU boundary
    {remove_selected_account_org_unit_boundary}
    -- Remove API calls made by principals belonging to identity perimeter trusted accounts - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_account` parameter).
    {identity_perimeter_trusted_account}
    -- Remove API calls made by identity perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`identity_perimeter_trusted_principal` parameter).
    {identity_perimeter_trusted_principal_arn}
    {identity_perimeter_trusted_principal_id}
    -- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
    AND useridentity.principalid != 'AWSService'
    -- Remove preflight requests which are unauthenticated and used to determine the cross-origin resource sharing (CORS) configuration
    AND eventname != 'PreflightRequest'
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
    vpcendpointid,
    sourceipaddress
```
</details>

<details>
<summary>Post-Athena data processing</summary>


- Remove resource specific exceptions.
</details>



# Query name: s3_bucket_policy_network_perimeter_ipv4

### Query description

List AWS API calls made on S3 buckets in the selected account, filtering out calls that align with your definition of expected networks.    
This query is similar to [`common_network_perimeter_ipv4`](../common/common_network_perimeter_ipv4.py) with an additional filtering to only list API calls on S3 bucket in the selected account.  
You can use this query to accelerate implementation of the [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls on your S3 buckets.
    
### Query results filtering

Below filters are applied:
- Keep only S3 API calls.
- Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator.
- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.
- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
- Remove API calls made by service-linked roles in the selected account.
- Remove API calls made via AWS Management Console with `S3Console` and `AWSCloudTrail` user agent - this is to manage temporary situations where the field `vpcendpointid` contains AWS owned VPC endpoint IDs.
- Remove API calls with errors.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.
- Remove resource specific exceptions.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep only API calls on S3 buckets in the selected account - list of S3 buckets retrieved from AWS Config aggregator.
    {keep_selected_account_s3_bucket}
    -- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator
    {remove_selected_account_vpce}
    -- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
    AND COALESCE(NOT regexp_like(sourceipaddress, ':'), True)
    -- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
    {network_perimeter_expected_public_cidr}
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
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
    vpcendpointid,
    sourceipaddress
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `vpcId`, `vpceAccountId`, `isAssumableBy`, `isServiceRole`.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.
- Remove resource specific exceptions.
</details>


# Query name: s3_external_access_org_boundary

### Query description

List active AWS IAM Access Analyzer external findings associated with Amazon S3 buckets.
You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your S3 buckets at the organization level. You can use the global condition key [aws:PrincipalOrgId](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) to limit access to your resources to principals belonging to your AWS organization.


# Query name: s3_scp_network_perimeter_ipv4

### Query description

This query is similar to [`s3_bucket_policy_network_perimeter_ipv4`](./s3_bucket_policy_network_perimeter_ipv4.py) with the following modifications:
- No filter on S3 buckets in the selected account.
- Filter on principals in the selected account.

You can use this query to accelerate implementation of the [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls using service control policies (SCPs).
    
### Query results filtering

Below filters are applied:
- Keep only S3 API calls.
- Keep only API calls made by principals in the selected account.
- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.
- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
- Remove API calls made by service-linked roles in the selected account.
- Remove API calls with errors.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.
- Remove resource specific exceptions.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep only API calls made by principals in the selected account
    {keep_selected_account_principal}
    -- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.
    {remove_selected_account_vpce}
    -- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
    AND COALESCE(NOT regexp_like(sourceipaddress, ':'), True)
    -- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
    {network_perimeter_expected_public_cidr}
    -- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
    {network_perimeter_expected_vpc_endpoint}
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
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
    sourceipaddress,
    vpcendpointid
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `vpcId`, `vpceAccountId`, `isAssumableBy`, `isServiceRole`.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by a principal that is neither a service role nor a service-linked role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name.
- Remove resource specific exceptions.
</details>



# Query name: s3_scp_resource_perimeter

### Query description

List AWS API calls made by principals in the selected account on Amazon S3 buckets not owned by accounts in the same organization as the selected account nor inventoried in a Config aggregator.
You can use this query to accelerate implementation of the [**resource perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls using service control policies (SCPs).
    
### Query results filtering

Below filters are applied:
- Keep only S3 API calls.
- Keep only API calls made by principals in the selected account.
- Remove API calls at the account scope, such API calls are not applied to resources not owned by the selected account.
- Remove API calls with the selected account ID in the request parameters (example: GetStorageLensConfiguration).
- Remove the unnested values of the `resources` field in CloudTrail with `resource.type`=`AWS::S3::Object`. Another unnested row exists with `resources.type`=`AWS::S3::Bucket` and `resources.accountid` distinct from NULL.
- Remove API calls on S3 buckets owned by accounts belonging to the same AWS organization as the selected account.
- Remove API calls made on trusted S3 buckets - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_bucket_name` parameter).
- Remove API calls made by resource perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_principal` parameter).
- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
- Remove API calls made by service-linked roles in the selected account.
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
    eventname,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    unnested_resources.accountid as bucket_accountid,
    unnested_resources.arn as bucket_arn,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
LEFT JOIN UNNEST(
    resources
) u(unnested_resources) ON TRUE
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep only API calls made by principals in the selected account
    {keep_selected_account_principal}
    -- Remove API calls at the account scope, such API calls are not applied to resources not owned by the selected account.
    {helper_s3.athena_remove_s3_event_name_at_account_scope()}
    -- Remove API calls with the selected account ID in the request parameters (example: GetStorageLensConfiguration).
    AND COALESCE(NOT regexp_like(requestparameters, ':{account_id}:storage-lens|{account_id}.s3-control'), True)
    -- Remove the unnested values of the `resources` field in CloudTrail with `resource.type`=`AWS::S3::Object`. Another unnested row exists with `resources.type`=`AWS::S3::Bucket` and `resources.accountid` distinct from NULL.
    AND unnested_resources.type IS DISTINCT FROM 'AWS::S3::Object'
    -- Remove API calls on S3 buckets owned by accounts belonging to the same AWS organization as the selected account.
    AND COALESCE(unnested_resources.accountid NOT IN ({list_all_account_id}), True)
    -- Remove API calls made on trusted S3 buckets - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_bucket_name` parameter).
    {resource_perimeter_trusted_bucket_name}
    -- Remove API calls made by resource perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_principal` parameter).
    {resource_perimeter_trusted_principal_arn}
    {resource_perimeter_trusted_principal_id}
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
    eventname,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
    unnested_resources.accountid,
    unnested_resources.arn
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `vpcId`, `isAssumableBy`, `isServiceRole`.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove API calls on S3 buckets inventoried in AWS Config aggregator.
</details>



# Query name: s3_vpce_policy_resource_perimeter_account_to_not_mine

### Query description

List S3 API calls made by principals and through S3 VPC endpoints in the selected account on S3 buckets not inventoried in the AWS Config aggregator.    
You can use this query to accelerate implementation of your [**resource perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls using VPC endpoint policies.
    
### Query results filtering

Below filters are applied:
- Keep only S3 API calls.
- Keep API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.
- Remove API calls at the account scope, such API calls are not applied to resources not owned by the selected account.
- Remove API calls with the selected account ID in the request parameters (example: GetStorageLensConfiguration).
- Remove the unnested values of the `resources` field in CloudTrail with `resource.type`=`AWS::S3::Object`. Another unnested row exists with `resources.type`=`AWS::S3::Bucket` and `resources.accountid` distinct from NULL.
- Remove API calls on S3 buckets owned by accounts belonging to the same AWS organization as the selected account.
- Remove API calls made on trusted S3 buckets - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_bucket_name` parameter).
- Remove API calls made by resource perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_principal` parameter).
- Remove API calls with errors.
- Remove API calls on S3 buckets inventoried in AWS Config aggregator.


### Query details

<details>
<summary>Athena query</summary>

```sql
SELECT
    useridentity.sessioncontext.sessionissuer.arn as principal_arn,
    useridentity.type as principal_type,
    useridentity.accountid as principal_accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName') AS bucketname,
    unnested_resources.accountid as bucket_accountid,
    unnested_resources.arn as bucket_arn,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
LEFT JOIN UNNEST(
    resources
) u(unnested_resources) ON TRUE
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 's3.amazonaws.com'
    -- Keep API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.
    {keep_selected_account_vpce}
    -- Remove API calls at the account scope, such API calls are not applied to resources not owned by the selected account.
    {helper_s3.athena_remove_s3_event_name_at_account_scope()}
    -- Remove API calls with the selected account ID in the request parameters (example: GetStorageLensConfiguration).
    AND COALESCE(NOT regexp_like(requestparameters, ':{account_id}:storage-lens|{account_id}.s3-control'), True)
    -- Remove the unnested values of the `resources` field in CloudTrail with `resource.type`=`AWS::S3::Object`. Another unnested row exists with `resources.type`=`AWS::S3::Bucket` and `resources.accountid` distinct from NULL.
    AND unnested_resources.type IS DISTINCT FROM 'AWS::S3::Object'
    -- Remove API calls on S3 buckets owned by accounts belonging to the same AWS organization as the selected account.
    AND COALESCE(unnested_resources.accountid NOT IN ({list_all_account_id}), True)
    -- Remove API calls made on trusted S3 buckets - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_bucket_name` parameter).
    {resource_perimeter_trusted_bucket_name}
    -- Remove API calls made by resource perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_principal` parameter).
    {resource_perimeter_trusted_principal_arn}
    {resource_perimeter_trusted_principal_id}
    -- Remove API calls with errors
    AND errorcode IS NULL
GROUP BY
    useridentity.sessioncontext.sessionissuer.arn,
    useridentity.type,
    useridentity.accountid,
    useridentity.principalid,
    JSON_EXTRACT_SCALAR(requestparameters, '$.bucketName'),
    unnested_resources.accountid,
    unnested_resources.arn,
    sourceipaddress,
    vpcendpointid
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `vpcId`.
- Remove API calls on S3 buckets inventoried in AWS Config aggregator.
</details>


# Query name: s3_vpce_policy_resource_perimeter_org_to_not_mine

### Query description

This query is similar to [`s3_vpce_policy_resource_perimeter_account_to_not_mine`](./s3_vpce_policy_resource_perimeter_account_to_not_mine.py) but analyzes activity at the organization level instead of the selected account level. This can be useful if principals from others AWS accounts are used in a given AWS account.      
You can use this query to accelerate implementation of the [**resource perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls using VPC endpoint policies.

> Note: this query is performed on all accounts within your organization. Depending on your organization size, this query can take several minutes to complete and generate additionnal costs.
