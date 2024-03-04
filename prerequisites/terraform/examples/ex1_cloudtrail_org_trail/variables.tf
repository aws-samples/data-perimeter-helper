# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
resource "random_string" "deployment_uuid" {
  special = false
  upper   = false
  length  = 10
}

variable "prefix" {
  description = "Prefix value added to the name of deployed resources to ease identification"
  type        = string
}

variable "main_region" {
  description = "AWS Region where resources are deployed"
  type        = string
}

variable "profile_name_root_account" {
  description = "AWS Profile to be used to deploy to root account"
  type        = string
}

variable "profile_name_logs_account" {
  description = "AWS Profile to be used to deploy to logs account"
  type        = string
}

variable "list_additionnal_key_admins_roles_arn" {
  description = "List of IAM roles that would be granted full rights on KMS key used for CloudTrail logs encryption stored in s3 - accepts wildcards"
  type        = list(string)
  default     = []
}

variable "cloudtrail_trail_name" {
  description = "Name of the trail to be deployed - if no value supplied, a value is auto-generated"
  type        = string
  default     = ""
}

variable "list_athena_cloudtrail_enum_regions" {
  type = list(string)
}
