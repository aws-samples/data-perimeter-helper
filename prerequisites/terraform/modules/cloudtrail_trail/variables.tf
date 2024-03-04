# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
variable "cloudtrail_trail_name" {
  description = "Name of the expected trail to be deployed"
  type        = string
}

variable "cloudtrail_logs_bucket_name" {
  description = "Name of the Amazon S3 bucket that will store AWS CloudTrail logs file"
  type        = string
}

variable "cloudtrail_logs_kms_key_arn" {
  description = "ARN of the Amazon KMS key used to encrypt AWS CloudTrail log files in Amazon S3"
  type        = string
}

variable "is_organization_trail" {
  description = "If true, creates an organization trail"
  type        = bool
}

variable "enable_management_event" {
  description = "If true, enables CloudTrail management event"
  type        = bool
}

variable "enable_s3_data_event" {
  description = "If true, enables Amazon S3 Data events"
  type        = bool
  default     = false
}

variable "enable_lambda_data_event" {
  description = "If true, enables AWS Lambda data events"
  type        = bool
  default     = false
}

variable "s3_data_event_exclude_bucket_arn" {
  description = "List of Amazon S3 bucket ARN to exclude from data event recording"
  type        = list(string)
  default     = []
}

variable "read_write_type" {
  description = "Type of evens to logs. Valid values are ReadOnly, WriteOnly, All"
  type        = string
  default     = "All"
}
