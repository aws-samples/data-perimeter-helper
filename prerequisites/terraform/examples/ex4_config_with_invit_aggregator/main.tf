# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
module "aggregator" {
  source = "../../modules/config_aggregator_central"
  providers = {
    aws = aws.security_tooling
  }
  prefix                     = var.prefix
  deployment_uuid            = random_string.deployment_uuid.id
  is_organization_aggregator = false
  with_invitation_list_account_id = [
    data.aws_caller_identity.org_member_1.id,
    data.aws_caller_identity.org_member_2.id
  ]
  aggregator_regions = [var.main_region]
}

module "org_member_1" {
  source = "../../modules/config_aggregator_invited"
  providers = {
    aws = aws.org_member_1
  }
  aggregator_account_id = data.aws_caller_identity.security_tooling.id
  aggregator_region     = var.main_region
}

module "org_member_2" {
  source = "../../modules/config_aggregator_invited"
  providers = {
    aws = aws.org_member_2
  }
  aggregator_account_id = data.aws_caller_identity.security_tooling.id
  aggregator_region     = var.main_region
}