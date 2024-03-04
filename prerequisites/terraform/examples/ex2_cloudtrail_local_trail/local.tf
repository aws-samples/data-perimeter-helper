# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
locals {
  // If no value for cloudtrail_trail_name is provided, a value is auto-generated
  cloudtrail_trail_name = length(var.cloudtrail_trail_name) > 0 ? var.cloudtrail_trail_name : "${var.prefix}-local-trail-${random_string.deployment_uuid.id}"
}