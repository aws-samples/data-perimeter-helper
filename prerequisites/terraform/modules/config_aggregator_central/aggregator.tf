# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
resource "aws_config_configuration_aggregator" "central_aggregator" {
  #checkov:skip=CKV_AWS_121:Ensure AWS Config is enabled in all regions:A flag enabled config aggregator in all regions when set
  name = "${var.prefix}-config-aggregator-${var.deployment_uuid}"

  dynamic "account_aggregation_source" {
    for_each = local.is_with_invitation_aggregator && var.all_regions ? [1] : []
    content {
      account_ids = var.with_invitation_list_account_id
      all_regions = true
    }
  }

  dynamic "account_aggregation_source" {
    for_each = local.is_with_invitation_aggregator && length(var.aggregator_regions) > 0 && var.all_regions == false ? [1] : []
    content {
      account_ids = var.with_invitation_list_account_id
      regions     = var.aggregator_regions
    }
  }

  dynamic "organization_aggregation_source" {
    for_each = local.is_organization_aggregator && var.all_regions ? [1] : []
    content {
      role_arn    = aws_iam_role.role_config_aggregator_organization[0].arn
      all_regions = true
    }
  }

  dynamic "organization_aggregation_source" {
    for_each = local.is_organization_aggregator && length(var.aggregator_regions) > 0 && var.all_regions == false ? [1] : []
    content {
      role_arn = aws_iam_role.role_config_aggregator_organization[0].arn
      regions  = var.aggregator_regions
    }
  }

}
