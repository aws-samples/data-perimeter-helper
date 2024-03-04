# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
resource "aws_cloudtrail" "trail" {
  #checkov:skip=CKV_AWS_252:Notification with SNS is not relevant here
  #checkov:skip=CKV2_AWS_10:CloudWatch Logs integration is not relevant here
  name                          = var.cloudtrail_trail_name
  s3_bucket_name                = var.cloudtrail_logs_bucket_name
  kms_key_id                    = var.cloudtrail_logs_kms_key_arn
  enable_log_file_validation    = true
  include_global_service_events = true
  is_multi_region_trail         = true
  is_organization_trail         = var.is_organization_trail
  dynamic "advanced_event_selector" {
    for_each = var.enable_management_event ? [1] : []
    content {
      name = "Management events"
      field_selector {
        field  = "eventCategory"
        equals = ["Management"]
      }
    }
  }
  dynamic "advanced_event_selector" {
    for_each = var.enable_s3_data_event ? [1] : []
    content {
      name = "S3 Data Events"
      field_selector {
        field  = "eventCategory"
        equals = ["Data"]
      }
      field_selector {
        field  = "resources.type"
        equals = ["AWS::S3::Object"]
      }
      dynamic "field_selector" {
        for_each = length(var.s3_data_event_exclude_bucket_arn) > 0 ? [1] : []
        content {
          field           = "resources.ARN"
          not_starts_with = local.s3_data_event_exclude_bucket_arn
          # example: "arn:${data.aws_partition.current.id}:s3:::${var.cloudtrail_logs_bucket_name}/"
        }
      }
    }
  }
  dynamic "advanced_event_selector" {
    for_each = var.enable_lambda_data_event ? [1] : []
    content {
      name = "Lambda Data Events"
      field_selector {
        field  = "eventCategory"
        equals = ["Data"]
      }
      field_selector {
        field  = "resources.type"
        equals = ["AWS::Lambda::Function"]
      }
    }
  }
}
