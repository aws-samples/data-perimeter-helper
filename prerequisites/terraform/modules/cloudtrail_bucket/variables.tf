# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
variable "prefix" {
  description = "Prefix value added to the name of deployed resources to ease identification"
  type        = string
}

variable "cloudtrail_trail_name" {
  description = "Name of the trail to be deployed"
  type        = string
}

variable "list_additionnal_key_admins_roles_arn" {
  description = "List of IAM roles ARN that would be granted full rights on AWS KMS key used for AWS CloudTrail logs encryption stored in s3 - accepts wildcards"
  type        = list(string)
  default     = []
}

variable "force_destroy" {
  type        = bool
  description = "If true, force destroy of Amazon S3 bucket with AWS CloudTrail logs"
  default     = false
}

variable "deployment_uuid" {
  type = string
}

variable "resource_policy_aws_source_account_cloudtrail" {
  type    = list(string)
  default = []
}

variable "resource_policy_aws_source_arn_cloudtrail_arn" {
  type    = list(string)
  default = []
}

variable "only_organization_trail" {
  type = bool
}

variable "lifecycle_configuration_current_version_expire_after_days" {
  type    = number
  default = 0
}

variable "lifecycle_configuration_expired_version_remove_after_days" {
  type    = number
  default = 0
}
