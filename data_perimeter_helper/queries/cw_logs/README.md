<!--
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
-->

## List of queries
* [cw_logs_scp_resource_perimeter](#query-name-cw_logs_scp_resource_perimeter)

# Query name: cw_logs_scp_resource_perimeter

### Query description

List AWS API call `PutSubscriptionFilter` made by principals in the selected account on Amazon CloudWatch Logs destinations not owned by accounts in the same organization as the selected account.
You can use this query to accelerate implementation of the [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls using service control policies (SCPs).
    
### Query results filtering

Below filters are applied:
- Keep only CloudWatch Logs API calls.
- Keep only the `PutSubscriptionFilter` event.
- Keep only API calls made by principals in the selected account.
- Remove API calls on CloudWatch destinations owned by accounts belonging to the same AWS organization as the selected account.
- Remove API calls made on trusted CloudWatch Logs destination tables - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_ecr_repository_arn` parameter).
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
    JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn') AS destinationArn,
    TRY(SPLIT(JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'), ':')[5]) AS destinationAccountId,
    count(*) as nb_reqs
FROM "__ATHENA_TABLE_NAME_PLACEHOLDER__"
WHERE
    p_account = '{account_id}'
    AND p_date {helper.get_athena_date_partition()}
    AND eventsource = 'logs.amazonaws.com'
    AND eventname = 'PutSubscriptionFilter'
    -- Keep only API calls made by principals in the selected account
    {keep_selected_account_principal}
    -- Remove API calls on CloudWatch destinations owned by accounts belonging to the same AWS organization as the selected account.
    AND TRY(SPLIT(JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'), ':')[5]) NOT IN ({list_all_account_id})
    -- Remove API calls made on trusted CloudWatch Logs destination tables - retrieved from the `data perimeter helper` configuration file (`resource_perimeter_trusted_ecr_repository_arn` parameter).
    {resource_perimeter_trusted_logs_destination_arn}
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
    JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'),
    TRY(SPLIT(JSON_EXTRACT_SCALAR(requestparameters, '$.destinationArn'), ':')[5])
```
</details>

<details>
<summary>Post-Athena data processing</summary>

- Following columns are injected to ease analysis: `isAssumableBy`, `isServiceRole`.
- Remove API calls made by service-linked roles inventoried in AWS Config aggregator.
</details>



