<!--
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
-->

## List of queries
* [dynamodb_scp_resource_perimeter](#query-name-dynamodb_scp_resource_perimeter)

# Query name: dynamodb_scp_resource_perimeter

### Query description

List AWS API calls made by principals in the selected account on Amazon DynamoDB tables not owned by accounts in the same organization as the selected account.
You can use this query to accelerate implementation of the [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls using service control policies (SCPs).
    
### Query results filtering

Below filters are applied:
- Keep only DynamoDB API calls.
- Keep only API calls made by principals in the selected account.
- Remove API calls on resources owned by accounts belonging to the same AWS organization as the selected account.
- Remove API calls made on trusted DynamoDB tables - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_dynamodb_table_arn` parameter).
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
    unnested_resources.accountid as table_accountid,
    unnested_resources.arn as table_arn,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
LEFT JOIN UNNEST(
    resources
) u(unnested_resources) ON TRUE
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 'dynamodb.amazonaws.com'
    -- Keep only API calls made by principals in the selected account
    {keep_selected_account_principal}
    -- Remove API calls on resources owned by accounts belonging to the same AWS organization as the selected account.
    AND unnested_resources.accountid NOT IN ({list_all_account_id})
    -- Remove API calls made on trusted DynamoDB tables - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_dynamodb_table_arn` parameter).
    {resource_perimeter_trusted_dynamodb_table_arn}
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
    unnested_resources.accountid,
    unnested_resources.arn
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `isAssumableBy`, `isServiceRole`.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
</details>



