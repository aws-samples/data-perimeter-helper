# Change Log

All notable changes to this project will be documented in this file.

## [Unreleased]

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
