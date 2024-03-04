# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
variable "prefix" {
  description = "Prefix value added to the name of deployed resources to ease identification"
  type        = string
}

variable "deployment_uuid" {
  type = string
}

variable "is_organization_aggregator" {
  description = "If true deploys an organizational aggregator, else deploys a local "
  type        = bool
}

variable "with_invitation_list_account_id" {
  description = "List of accounts ID to invite - only relevant if is_organization_aggregator=False"
  type        = list(string)
  default     = []
}

variable "aggregator_regions" {
  description = "List of source regions being aggregated"
  type        = list(string)
  default     = []
}

variable "all_regions" {
  description = "If true, aggregate existing AWS Config regions and future regions"
  type        = bool
  default     = false
}

locals {
  is_with_invitation_aggregator = (var.is_organization_aggregator == false) && length(var.with_invitation_list_account_id) > 0
  is_organization_aggregator    = var.is_organization_aggregator && (local.is_with_invitation_aggregator == false)
}