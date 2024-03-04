# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
resource "aws_config_aggregate_authorization" "this" {
  account_id = var.aggregator_account_id
  region     = var.aggregator_region
}