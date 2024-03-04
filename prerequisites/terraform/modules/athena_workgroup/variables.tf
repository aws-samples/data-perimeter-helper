# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
variable "prefix" {
  type        = string
  description = "The prefix addded to resources' names"
}

variable "deployment_uuid" {
  type        = string
  description = "The unique id added in the resources' names"
}

variable "force_destroy" {
  type        = bool
  description = "If true, force destroy of S3 bucket with Athena outputs"
  default     = false
}

variable "list_additionnal_key_admins_roles_arn" {
  description = "List of IAM roles ARN that would be granted full rights on KMS key used for CloudTrail logs encryption stored in s3 - accepts wildcards"
  type        = list(string)
  default     = []
}

variable "lifecycle_configuration_current_version_expire_after_days" {
  type    = number
  default = 0
}

variable "lifecycle_configuration_expired_version_remove_after_days" {
  type    = number
  default = 0
}

variable "cloudtrail_bucket_name" {
  type = string
}

variable "list_athena_cloudtrail_enum_regions" {
  type = list(string)
}

variable "generate_athena_sql_create_table_organizational_trail" {
  type    = bool
  default = false
}

variable "generate_athena_sql_create_table_local_trail" {
  type    = bool
  default = false
}





