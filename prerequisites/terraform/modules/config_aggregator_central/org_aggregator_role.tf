# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
resource "aws_iam_role" "role_config_aggregator_organization" {
  count              = var.is_organization_aggregator ? 1 : 0
  name               = substr("${var.prefix}-AWSServiceRoleConfig-Organization-${var.deployment_uuid}", 0, 63)
  assume_role_policy = data.aws_iam_policy_document.assume_role_by_config[0].json
  path               = "/service-role/config.amazonaws.com/"
  managed_policy_arns = [
    "arn:aws:iam::aws:policy/service-role/AWSConfigRoleForOrganizations"
  ]
}

data "aws_iam_policy_document" "assume_role_by_config" {
  count = var.is_organization_aggregator ? 1 : 0
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["config.amazonaws.com"]
    }
  }
}
