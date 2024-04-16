# Change Log

All notable changes to this project will be documented in this file.

## [Unreleased]

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
