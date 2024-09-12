# Change Log

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.0.5] - 2024/09/12

### Added
- You can now use the following queries:
    - `cw_logs_scp_resource_perimeter` to list AWS API call `PutSubscriptionFilter` made by principals in the selected account on Amazon CloudWatch Logs destinations not owned by accounts in the same organization as the selected account.
    - `dynamodb_scp_resource_perimeter` to list AWS API calls made by principals in the selected account on Amazon DynamoDB tables not owned by accounts in the same organization as the selected account.
    - `ecr_scp_resource_perimeter` to list AWS API calls made by principals in the selected account on Amazon ECR repositories not owned by accounts in the same organization as the selected account.
    - `events_scp_resource_perimeter` to list AWS API calls made by principals in the selected account on Amazon EventBridge buses not owned by accounts in the same organization as the selected account.
    - `kms_scp_resource_perimeter` to list AWS API calls made by principals in the selected account on AWS KMS keys not owned by accounts in the same organization as the selected account.
    - `secretsmanager_scp_resource_perimeter` to list AWS API calls made by principals in the selected account on AWS Secrets Manager secrets not owned by accounts in the same organization as the selected account
    - `sns_scp_resource_perimeter` to list AWS API calls made by principals in the selected account on Amazon SNS topics not owned by accounts in the same organization as the selected account.
    - `sqs_scp_resource_perimeter` to list AWS API calls made by principals in the selected account on Amazon SQS queues not owned by accounts in the same organization as the selected account.
    - `sts_scp_resource_perimeter` to list AWS API calls `AssumeRole` made by principals in the selected account on AWS Identity and Access Management (IAM) roles not owned by accounts in the same organization as the selected account.


### Updated
- Previously, organizational unit (OU) boundaries applied only to accounts directly attached to an OU without any nested OUs beneath it. Now, you can set boundaries for accounts attached to OUs that have subsequent nested OUs within their hierarchy.
- Bump dependencies versions.


## [1.0.4] - 2024/07/02

### Added
- You can now use the query `common_identity_perimeter_org_boundary` to list AWS API calls made on the resources in the selected account by principals that do **NOT** belong to the same AWS organization, filtering out calls that align with your definition of trusted identities. Use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your resources at the organization level.
- When you apply queries against more than two accounts, queries' results are exported to one file per account - each file names prefixed with the targeted account ID. Now, to ease results review across multiple accounts, results are merged to a single file prefixed with `all`.

### Updated
- Timestamps are now used to manage cache expiration. When the tools import from cache it now displays the date on which it was cached.
- The function `perf_counter` is now only used to measure execution time.


## [1.0.3a] - 2024/06/21

### Updated
- The CLI parameters `-la/-lo` are no more mandatory for `findings` queries.
- The queries that list external access findings and rely on `list_regions` to discover available regions and analyzers can now be performed from the management account. However, the recommendation is to [use the management account only for tasks that require the management account](https://docs.aws.amazon.com/organizations/latest/userguide/orgs_best-practices_mgmt-acct.html#bp_mgmt-acct_use-mgmt). Data perimeter helper shall be used from a [`security tooling` account](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/architecture.html).
- Upgrade of requirements' versions.
- Minor code lint.

## [1.0.3] - 2024/05/06

### Added
- You can now enable caching for the referential items. The following new [variables](./data_perimeter_helper/variables.yaml) are introduced:
    - `cache_referential` (boolean): denotes if caching is enabled.
    - `cache_expire_after_interval` (str): interval of time after which the cache expires. The expected format is "<value> <unit>" where <value> is an integer and <unit> is equal to `minute`, `hour`, `day`, or `month`.
    - `list_resource_type_to_cache` (list[str]): list of resource types to cache. If not set, all resource types are cached. Otherwise, only the set resource types are cached.
- You can now use a new custom resource type `AWS::Organizations::Tree`. This resource type provides the account IDs, names, list of account's parents and organizational unit (OU) boundaries. This enables to discover the organization tree structure when relevant - notably for queries with the boundary at the OU scope.
- You can now use the query `referential_vpce` to list your Amazon Virtual Private Cloud (VPC) endpoints across your organization. The query provides fields to help you discover VPC endpoints that use in their policy the [AWS global condition context keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html) aws:PrincipalOrgId/PrincipalOrgPaths/PrincipalAccount and aws:ResourceOrgId/ResourceOrgPaths/ResourceAccount.
- You can now use the query `referential_scp` to list your service control policies (SCPs). The query provides fields to help you discover policies that use the [AWS global condition context keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html) aws:ResourceOrgId/ResourceOrgPaths/ResourceAccount, aws:SourceVPC, aws:SourceVPCe, and aws:SourceIP. The query exports the SCPs to readable JSON files under a subfolder `scp` of your configured output folder.
- The CLI parameter `--list-ou/-lo` supports organizational unit names.
- Unit tests for CLI parameters.

### Updated
- The resource type `AWS::Organizations::Account` only provides the list of account IDs and names. The list of parents and organizational unit (OU) boundaries are moved to the new resource type `AWS::Organizations::Tree`.
- The queries at the OU boundary have been updated to add as a dependency the resource type `AWS::Organizations::Tree`.
- Minor documentation updates.


## [1.0.2] - 2024/04/26

### Added
- You can now document your human role for your network perimeter objectives using the parameter `network_perimeter_human_role_arn` in the `data perimeter helper` configuration file.
    - This helps detect situations where an AWS service uses [forward access sessions (FAS)](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_forward_access_sessions.html) and performs calls from an AWS service network.
    - The detected API calls can then be excluded from results of the network perimeter queries if they are managed via the global condition key [`aws:ViaAWSService`](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-viaawsservice).
- New queries: [referential_glue_job](./data_perimeter_helper/queries/referential/README.md) and [referential_sagemaker_notebook](./data_perimeter_helper/queries/referential/README.md).
- New console logs to provide visibility on the organization structure discovery.


### Updated
- Previously the number of threads used for AWS Organizations API calls was tied to the number of available CPUs. Now, the number of threads is set to `3` to manage throttling quotas of AWS Organizations APIs.
- Previously the backoff strategy for AWS Organizations API calls allowed up to `4` retries. Now, this limit is set to `15`.
- Findings queries are now standalone queries, executed only once even if multiple account IDs are submitted.
- Improved the documentation.
- Bumped requirements versions.

### Removed
- The CLI parameter `--list-ou/-lo` does no more support organizational unit names.


## [1.0.1] - 2024/04/16
### Added
- You can now run queries against your organization by setting the CLI parameter `--list-account/-la` to `all`.
- The CLI parameter `--list-account/-la` now supports account names.
- You can use a new CLI parameter `--list-ou/lo` to run your queries against organizational units. This parameter supports both organizational unit IDs and organizational unit names.
- New data source: AWS IAM Access Analyzer external access findings.
- New queries: findings_iam_aa_external_access_org_boundary, findings_sh_external_access_org_boundary and s3_external_access_org_boundary.

## [1.0.0] - 2024/03/04
### Added
- Initial commmit
