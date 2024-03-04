Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 0.14.9 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 4.19.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_aws"></a> [aws](#provider\_aws) | >= 4.19.0 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [aws_kms_alias.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_alias) | resource |
| [aws_kms_key.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | resource |
| [aws_s3_bucket.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_lifecycle_configuration.cloudtrail_logs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration) | resource |
| [aws_s3_bucket_ownership_controls.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_ownership_controls) | resource |
| [aws_s3_bucket_policy.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) | resource |
| [aws_s3_bucket_public_access_block.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_server_side_encryption_configuration.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration) | resource |
| [aws_s3_bucket_versioning.cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.bucket_policy_cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.kms_policy_cloudtrail_bucket](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_session_context.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_session_context) | data source |
| [aws_organizations_organization.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/organizations_organization) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cloudtrail_trail_name"></a> [cloudtrail\_trail\_name](#input\_cloudtrail\_trail\_name) | Name of the trail to be deployed | `string` | n/a | yes |
| <a name="input_deployment_uuid"></a> [deployment\_uuid](#input\_deployment\_uuid) | n/a | `string` | n/a | yes |
| <a name="input_force_destroy"></a> [force\_destroy](#input\_force\_destroy) | If true, force destroy of S3 bucket with CloudTrail logs | `bool` | `false` | no |
| <a name="input_lifecycle_configuration_current_version_expire_after_days"></a> [lifecycle\_configuration\_current\_version\_expire\_after\_days](#input\_lifecycle\_configuration\_current\_version\_expire\_after\_days) | n/a | `number` | `0` | no |
| <a name="input_lifecycle_configuration_expired_version_remove_after_days"></a> [lifecycle\_configuration\_expired\_version\_remove\_after\_days](#input\_lifecycle\_configuration\_expired\_version\_remove\_after\_days) | n/a | `number` | `0` | no |
| <a name="input_list_additionnal_key_admins_roles_arn"></a> [list\_additionnal\_key\_admins\_roles\_arn](#input\_list\_additionnal\_key\_admins\_roles\_arn) | List of IAM roles ARN that would be granted full rights on KMS key used for CloudTrail logs encryption stored in s3 - accepts wildcards | `list(string)` | `[]` | no |
| <a name="input_only_organization_trail"></a> [only\_organization\_trail](#input\_only\_organization\_trail) | n/a | `bool` | n/a | yes |
| <a name="input_prefix"></a> [prefix](#input\_prefix) | Prefix value added to the name of deployed resources to ease identification | `string` | n/a | yes |
| <a name="input_resource_policy_aws_source_account_cloudtrail"></a> [resource\_policy\_aws\_source\_account\_cloudtrail](#input\_resource\_policy\_aws\_source\_account\_cloudtrail) | n/a | `list(string)` | `[]` | no |
| <a name="input_resource_policy_aws_source_arn_cloudtrail_arn"></a> [resource\_policy\_aws\_source\_arn\_cloudtrail\_arn](#input\_resource\_policy\_aws\_source\_arn\_cloudtrail\_arn) | n/a | `list(string)` | `[]` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_cloudtrail_logs_bucket_arn"></a> [cloudtrail\_logs\_bucket\_arn](#output\_cloudtrail\_logs\_bucket\_arn) | n/a |
| <a name="output_cloudtrail_logs_bucket_console_access"></a> [cloudtrail\_logs\_bucket\_console\_access](#output\_cloudtrail\_logs\_bucket\_console\_access) | n/a |
| <a name="output_cloudtrail_logs_bucket_name"></a> [cloudtrail\_logs\_bucket\_name](#output\_cloudtrail\_logs\_bucket\_name) | n/a |
| <a name="output_cloudtrail_logs_kms_key_arn"></a> [cloudtrail\_logs\_kms\_key\_arn](#output\_cloudtrail\_logs\_kms\_key\_arn) | n/a |
<!-- END_TF_DOCS -->