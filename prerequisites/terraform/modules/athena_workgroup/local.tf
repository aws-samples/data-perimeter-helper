# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
locals {
  enable_lifecycle_configuration = var.lifecycle_configuration_current_version_expire_after_days > 0 && var.lifecycle_configuration_expired_version_remove_after_days > 0
}