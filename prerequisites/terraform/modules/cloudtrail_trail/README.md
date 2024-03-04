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
| [aws_cloudtrail.trail](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudtrail) | resource |
| [aws_partition.current](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/partition) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_cloudtrail_logs_bucket_name"></a> [cloudtrail\_logs\_bucket\_name](#input\_cloudtrail\_logs\_bucket\_name) | Name of the s3 bucket that will store CloudTrail logs file | `string` | n/a | yes |
| <a name="input_cloudtrail_logs_kms_key_arn"></a> [cloudtrail\_logs\_kms\_key\_arn](#input\_cloudtrail\_logs\_kms\_key\_arn) | ARN of the KMS key used to encrypt CloudTrail log files in s3 | `string` | n/a | yes |
| <a name="input_cloudtrail_trail_name"></a> [cloudtrail\_trail\_name](#input\_cloudtrail\_trail\_name) | Name of the expected trail to be deployed | `string` | n/a | yes |
| <a name="input_enable_lambda_data_event"></a> [enable\_lambda\_data\_event](#input\_enable\_lambda\_data\_event) | If true, enables Lambda Data events | `bool` | `false` | no |
| <a name="input_enable_management_event"></a> [enable\_management\_event](#input\_enable\_management\_event) | If true, enables CloudTrail management event | `bool` | n/a | yes |
| <a name="input_enable_s3_data_event"></a> [enable\_s3\_data\_event](#input\_enable\_s3\_data\_event) | If true, enables S3 Data events | `bool` | `false` | no |
| <a name="input_is_organization_trail"></a> [is\_organization\_trail](#input\_is\_organization\_trail) | If true, creates an organization trail | `bool` | n/a | yes |
| <a name="input_read_write_type"></a> [read\_write\_type](#input\_read\_write\_type) | Type of evens to logs. Valid values are ReadOnly, WriteOnly, All | `string` | `"All"` | no |
| <a name="input_s3_data_event_exclude_bucket_arn"></a> [s3\_data\_event\_exclude\_bucket\_arn](#input\_s3\_data\_event\_exclude\_bucket\_arn) | List of S3 bucket ARN to exclude from data event recording | `list(string)` | `[]` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->