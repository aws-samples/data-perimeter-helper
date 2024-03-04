# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
module "org_aggregator" {
  source = "../../modules/config_aggregator_central"
  providers = {
    aws = aws.security_tooling
  }
  prefix                     = var.prefix
  deployment_uuid            = random_string.deployment_uuid.id
  is_organization_aggregator = true
  aggregator_regions         = [var.main_region]
}
