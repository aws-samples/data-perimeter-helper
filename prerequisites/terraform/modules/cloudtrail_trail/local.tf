# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
locals {
  s3_data_event_exclude_bucket_arn = length(var.s3_data_event_exclude_bucket_arn) > 0 ? [
    for arn in var.s3_data_event_exclude_bucket_arn : endswith(arn, "/") ? arn : "${arn}/"
  ] : []
}