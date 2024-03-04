# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
output "cloudtrail_logs_bucket_name" {
  value = module.cloudtrail_bucket.cloudtrail_logs_bucket_name
}
