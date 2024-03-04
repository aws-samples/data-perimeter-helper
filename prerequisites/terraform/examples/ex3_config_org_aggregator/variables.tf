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
  default     = "data-perimeter-helper"
}

variable "main_region" {
  description = "AWS Region where resources are deployed"
  type        = string
}

variable "profile_name_security_tooling" {
  description = "AWS Profile to be used to deploy to security tooling account"
  type        = string
}