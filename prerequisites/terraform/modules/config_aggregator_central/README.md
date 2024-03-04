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
| [aws_config_configuration_aggregator.central_aggregator](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/config_configuration_aggregator) | resource |
| [aws_iam_role.role_config_aggregator_organization](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_role) | resource |
| [aws_iam_policy_document.assume_role_by_config](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/iam_policy_document) | data source |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_aggregator_regions"></a> [aggregator\_regions](#input\_aggregator\_regions) | List of source regions being aggregated | `list(string)` | `[]` | no |
| <a name="input_all_regions"></a> [all\_regions](#input\_all\_regions) | If true, aggregate existing AWS Config regions and future regions | `bool` | `false` | no |
| <a name="input_deployment_uuid"></a> [deployment\_uuid](#input\_deployment\_uuid) | n/a | `string` | n/a | yes |
| <a name="input_is_organization_aggregator"></a> [is\_organization\_aggregator](#input\_is\_organization\_aggregator) | If true deploys an organizational aggregator, else deploys a local | `bool` | n/a | yes |
| <a name="input_prefix"></a> [prefix](#input\_prefix) | Prefix value added to the name of deployed resources to ease identification | `string` | n/a | yes |
| <a name="input_with_invitation_list_account_id"></a> [with\_invitation\_list\_account\_id](#input\_with\_invitation\_list\_account\_id) | List of accounts ID to invite - only relevant if is\_organization\_aggregator=False | `list(string)` | `[]` | no |

## Outputs

No outputs.
<!-- END_TF_DOCS -->