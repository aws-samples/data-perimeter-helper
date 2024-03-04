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
| [aws_athena_named_query.cloudtrail_create_table_local](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/athena_named_query) | resource |
| [aws_athena_named_query.cloudtrail_create_table_org](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/athena_named_query) | resource |
| [aws_athena_workgroup.this](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/athena_workgroup) | resource |
| [aws_kms_alias.athena_db](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_alias) | resource |
| [aws_kms_key.athena_db](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/kms_key) | resource |
| [aws_s3_bucket.athena_output](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket) | resource |
| [aws_s3_bucket_lifecycle_configuration.athena_outputs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_lifecycle_configuration) | resource |
| [aws_s3_bucket_ownership_controls.athena_output](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_ownership_controls) | resource |
| [aws_s3_bucket_policy.athena_output](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_policy) | resource |
| [aws_s3_bucket_public_access_block.athena_output](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_public_access_block) | resource |
| [aws_s3_bucket_server_side_encryption_configuration.athena_output](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_server_side_encryption_configuration) | resource |
| [aws_s3_bucket_versioning.athena_output](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket_versioning) | resource |
| [aws_caller_identity.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/caller_identity) | data source |
| [aws_iam_policy_document.bucket_policy_athena_output](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_policy_document.key_policy_athena_db](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |
| [aws_iam_session_context.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_session_context) | data source |
| [aws_organizations_organization.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/organizations_organization) | data source |
| [aws_region.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cloudtrail_bucket_name"></a> [cloudtrail\_bucket\_name](#input\_cloudtrail\_bucket\_name) | n/a | `string` | n/a | yes |
| <a name="input_deployment_uuid"></a> [deployment\_uuid](#input\_deployment\_uuid) | The unique id added in the resources' names | `string` | n/a | yes |
| <a name="input_force_destroy"></a> [force\_destroy](#input\_force\_destroy) | If true, force destroy of S3 bucket with Athena outputs | `bool` | `false` | no |
| <a name="input_generate_athena_sql_create_table_local_trail"></a> [generate\_athena\_sql\_create\_table\_local\_trail](#input\_generate\_athena\_sql\_create\_table\_local\_trail) | n/a | `bool` | `false` | no |
| <a name="input_generate_athena_sql_create_table_organizational_trail"></a> [generate\_athena\_sql\_create\_table\_organizational\_trail](#input\_generate\_athena\_sql\_create\_table\_organizational\_trail) | n/a | `bool` | `false` | no |
| <a name="input_lifecycle_configuration_current_version_expire_after_days"></a> [lifecycle\_configuration\_current\_version\_expire\_after\_days](#input\_lifecycle\_configuration\_current\_version\_expire\_after\_days) | n/a | `number` | `0` | no |
| <a name="input_lifecycle_configuration_expired_version_remove_after_days"></a> [lifecycle\_configuration\_expired\_version\_remove\_after\_days](#input\_lifecycle\_configuration\_expired\_version\_remove\_after\_days) | n/a | `number` | `0` | no |
| <a name="input_list_additionnal_key_admins_roles_arn"></a> [list\_additionnal\_key\_admins\_roles\_arn](#input\_list\_additionnal\_key\_admins\_roles\_arn) | List of IAM roles ARN that would be granted full rights on KMS key used for CloudTrail logs encryption stored in s3 - accepts wildcards | `list(string)` | `[]` | no |
| <a name="input_list_athena_cloudtrail_enum_regions"></a> [list\_athena\_cloudtrail\_enum\_regions](#input\_list\_athena\_cloudtrail\_enum\_regions) | n/a | `list(string)` | n/a | yes |
| <a name="input_prefix"></a> [prefix](#input\_prefix) | The prefix addded to resources' names | `string` | n/a | yes |

## Outputs

No outputs.
<!-- END_TF_DOCS -->