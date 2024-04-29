<!-- # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0 -->
# Description

You can use `sns` queries to analyze activity in your AWS organization against data perimeter objectives while focusing exclusively [Amazon SNS](https://docs.aws.amazon.com/sns/latest/dg/welcome.html) API calls.    

The `sns` queries are prefixed with the keyword `sns`.

## List of queries

* [Query name: sns_network_perimeter_ipv4](#query-name-sns_network_perimeter_ipv4)

# Query name: sns_network_perimeter_ipv4

### Query description


List SNS API calls filtering out calls that align with your definition of expected networks.
You can use this query to accelerate implementation of the [**network perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls using your SNS topic policies or service control policies (SCPs).
    
### Query results filtering

Below filters are applied:
- Keep only SNS API calls.
- Remove API calls from IPv6 addresses - `sourceipaddress` field in CloudTrail log contains `:`.
- Remove API calls made from expected public CIDR ranges - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_public_cidr` parameter).
- Remove API calls made through VPC endpoints in the selected account - retrieved from AWS Config aggregator.
- Remove API calls made through expected VPC endpoints - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc_endpoint` parameter).
- Remove API calls made by principals belonging to network perimeter trusted AWS accounts - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_account` parameter).
- Remove API calls made by network perimeter trusted identities - retrieved from the `data perimeter helper` configuration file (`network_perimeter_trusted_principal` parameter).
- Remove API calls made by AWS service principals - `useridentity.principalid` field in CloudTrail log equals `AWSService`.
- Remove API calls made by service-linked roles in the selected account.
- Remove API calls with errors.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
- Remove API calls from expected VPCs - retrieved from the `data perimeter helper` configuration file (`network_perimeter_expected_vpc` parameter).
- Remove a subset of API calls made by an AWS service using [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html):
  - API calls made from an AWS service network by using a service role and where the `sourceipaddress` field in the CloudTrail record is populated with the service's DNS name that does not match the ones specified in the role's trust policy.
  - API calls made from an AWS service network by network perimeter human roles - retrieved from the `data perimeter helper` configuration file (`network_perimeter_human_role_arn` parameter).


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
    COALESCE(
        JSON_EXTRACT_SCALAR(requestparameters, '$.topicArn'),
        JSON_EXTRACT_SCALAR(requestparameters, '$.resourceArn'),
        JSON_EXTRACT_SCALAR(responseelements, '$.topicArn')
    ) AS topicArn,
    sourceipaddress,
    vpcendpointid,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 'sns.amazonaws.com'
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
    eventname,
    COALESCE(
        JSON_EXTRACT_SCALAR(requestparameters, '$.topicArn'),
        JSON_EXTRACT_SCALAR(requestparameters, '$.resourceArn'),
        JSON_EXTRACT_SCALAR(responseelements, '$.topicArn')
    ),
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
  - API calls made from an AWS service network by network perimeter human roles - retrieved from the `data perimeter helper` configuration file (`network_perimeter_human_role_arn` parameter).
</details>



