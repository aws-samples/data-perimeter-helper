# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
output "cloudtrail_logs_bucket_name" {
  value = aws_s3_bucket.cloudtrail_bucket.id
}

output "cloudtrail_logs_bucket_arn" {
  value = aws_s3_bucket.cloudtrail_bucket.arn
}

output "cloudtrail_logs_kms_key_arn" {
  value = aws_kms_key.cloudtrail_bucket.arn
}

output "cloudtrail_logs_bucket_console_access" {
  value = "https://s3.console.aws.amazon.com/s3/buckets/${local.s3_bucket_name}?region=${data.aws_region.current.name}&tab=objects"
}