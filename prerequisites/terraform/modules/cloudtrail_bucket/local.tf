# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
locals {
  cloudtrail_trail_arn = "arn:aws:cloudtrail:${data.aws_region.current.name}:${data.aws_organizations_organization.current.master_account_id}:trail/${var.cloudtrail_trail_name}"
  s3_bucket_name       = substr("${var.prefix}-central-cloudtrail-bucket-${data.aws_caller_identity.current.id}-${var.deployment_uuid}", 0, 63)
  bucket_policy_resource_field = var.only_organization_trail ? [
    "${aws_s3_bucket.cloudtrail_bucket.arn}/AWSLogs/${data.aws_organizations_organization.current.master_account_id}/*",
    "${aws_s3_bucket.cloudtrail_bucket.arn}/AWSLogs/${data.aws_organizations_organization.current.id}/*"
    ] : [
    "${aws_s3_bucket.cloudtrail_bucket.arn}/AWSLogs/*"
  ]
  enable_lifecycle_configuration = var.lifecycle_configuration_current_version_expire_after_days > 0 && var.lifecycle_configuration_expired_version_remove_after_days > 0
}
