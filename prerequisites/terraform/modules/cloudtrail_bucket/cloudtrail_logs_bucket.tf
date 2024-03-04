# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
resource "aws_s3_bucket" "cloudtrail_bucket" { # nosemgrep: aws-s3-bucket-versioning-not-enabled
  #checkov:skip=CKV_AWS_144:Cross-region replication to be added as customization if relevant
  #checkov:skip=CKV_AWS_18:Access logs to be added as customization if relevant
  #checkov:skip=CKV2_AWS_62:Ensure S3 buckets should have event notifications enabled:Event notification to be added as customization if relevant
  bucket        = local.s3_bucket_name
  force_destroy = var.force_destroy
}

// All public access is blocked
resource "aws_s3_bucket_public_access_block" "cloudtrail_bucket" {
  bucket                  = aws_s3_bucket.cloudtrail_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

// Enable encryption with AWS KMS CMK
resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail_bucket" {
  bucket = aws_s3_bucket.cloudtrail_bucket.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.cloudtrail_bucket.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

// Disable ACL
resource "aws_s3_bucket_ownership_controls" "cloudtrail_bucket" {
  bucket = aws_s3_bucket.cloudtrail_bucket.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

// Enable versioning
resource "aws_s3_bucket_versioning" "cloudtrail_bucket" {
  bucket = aws_s3_bucket.cloudtrail_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

// Bucket policy
resource "aws_s3_bucket_policy" "cloudtrail_bucket" {
  bucket = aws_s3_bucket.cloudtrail_bucket.id
  policy = data.aws_iam_policy_document.bucket_policy_cloudtrail_bucket.json
}

/*
Bucket policy content for CloudTrail logs' bucket
Enforce least privilege principle
*/
data "aws_iam_policy_document" "bucket_policy_cloudtrail_bucket" {
  # Statements with SourceArn
  dynamic "statement" {
    for_each = length(var.resource_policy_aws_source_arn_cloudtrail_arn) > 0 ? [1] : []
    content {
      sid = "CloudTrailGetBucketAclSourceArn"
      principals {
        type = "Service"
        identifiers = [
          "cloudtrail.amazonaws.com"
        ]
      }
      actions = [
        "s3:GetBucketAcl"
      ]
      resources = [
        aws_s3_bucket.cloudtrail_bucket.arn
      ]
      condition {
        test     = "ArnEquals"
        variable = "aws:SourceArn"
        values   = var.resource_policy_aws_source_arn_cloudtrail_arn
      }
    }
  }
  dynamic "statement" {
    for_each = length(var.resource_policy_aws_source_arn_cloudtrail_arn) > 0 ? [1] : []
    content {
      sid = "CloudTrailPutObjectSourceArn"
      principals {
        type = "Service"
        identifiers = [
          "cloudtrail.amazonaws.com"
        ]
      }
      actions = [
        "s3:PutObject"
      ]
      resources = local.bucket_policy_resource_field
      condition {
        test     = "StringEquals"
        variable = "s3:x-amz-acl"
        values = [
          "bucket-owner-full-control"
        ]
      }
      condition {
        test     = "ArnEquals"
        variable = "aws:SourceArn"
        values   = var.resource_policy_aws_source_arn_cloudtrail_arn
      }
    }
  }
  # Statements with SourceAccount
  dynamic "statement" {
    for_each = length(var.resource_policy_aws_source_account_cloudtrail) > 0 ? [1] : []
    content {
      sid = "CloudTrailGetBucketAclSourceAccount"
      principals {
        type = "Service"
        identifiers = [
          "cloudtrail.amazonaws.com"
        ]
      }
      actions = [
        "s3:GetBucketAcl"
      ]
      resources = [
        aws_s3_bucket.cloudtrail_bucket.arn
      ]
      condition {
        test     = "StringEquals"
        variable = "aws:SourceAccount"
        values   = var.resource_policy_aws_source_account_cloudtrail
      }
    }
  }
  dynamic "statement" {
    for_each = length(var.resource_policy_aws_source_account_cloudtrail) > 0 ? [1] : []
    content {
      sid = "CloudTrailPutObjectSourceAccount"
      principals {
        type = "Service"
        identifiers = [
          "cloudtrail.amazonaws.com"
        ]
      }
      actions = [
        "s3:PutObject"
      ]
      resources = local.bucket_policy_resource_field
      condition {
        test     = "StringEquals"
        variable = "s3:x-amz-acl"
        values = [
          "bucket-owner-full-control"
        ]
      }
      condition {
        test     = "StringEquals"
        variable = "aws:SourceAccount"
        values   = var.resource_policy_aws_source_account_cloudtrail
      }
    }
  }
  # Data Protection controls
  statement {
    effect = "Deny"
    sid    = "DenyNotEncryptedCloudTrailLogs"
    principals {
      type = "*"
      identifiers = [
        "*"
      ]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      # If local trail: /AWSLogs/<ACCOUNT_ID>/CloudTrail/<REGION>/...
      "${aws_s3_bucket.cloudtrail_bucket.arn}/AWSLogs/*/CloudTrail/*",
      # If organizational trail: /AWSLogs/<ORG_ID>/<ACCOUNT_ID>/CloudTrail/<REGION>/...
      "${aws_s3_bucket.cloudtrail_bucket.arn}/AWSLogs/*/*/CloudTrail/*"
    ]
    condition {
      test     = "StringNotEquals"
      variable = "s3:x-amz-server-side-encryption"
      values = [
        "aws:kms"
      ]
    }
  }
  statement {
    effect = "Deny"
    sid    = "DenyNotEncryptedCloudTrailDigest"
    principals {
      type = "*"
      identifiers = [
        "*"
      ]
    }
    actions = [
      "s3:PutObject"
    ]
    resources = [
      # If local trail: /AWSLogs/<ACCOUNT_ID>/CloudTrail-Digest/<REGION>/...
      "${aws_s3_bucket.cloudtrail_bucket.arn}/AWSLogs/*/CloudTrail-Digest/*",
      # If organizational trail: /AWSLogs/<ORG_ID>/<ACCOUNT_ID>/CloudTrail-Digest/<REGION>/...
      "${aws_s3_bucket.cloudtrail_bucket.arn}/AWSLogs/*/*/CloudTrail-Digest/*"
    ]
    condition {
      test     = "StringNotEquals"
      variable = "s3:x-amz-server-side-encryption"
      values = [
        "AES256"
      ]
    }
  }
  statement {
    effect = "Deny"
    sid    = "DenyNoEncryptionInTransit"
    principals {
      type = "*"
      identifiers = [
        "*"
      ]
    }
    actions = [
      "*"
    ]
    resources = [
      aws_s3_bucket.cloudtrail_bucket.arn,
      "${aws_s3_bucket.cloudtrail_bucket.arn}/*"
    ]
    condition {
      test     = "NumericLessThan"
      variable = "s3:TlsVersion"
      values = [
        "1.2"
      ]
    }
  }
}

/*
CloudTrail logs are smaller than 128Kb, no need to apply storage class transition
However expiration is applied to comply with data retention requirements
Resource:
  - https://docs.aws.amazon.com/AmazonS3/latest/userguide/lifecycle-transition-general-considerations.html
*/

resource "aws_s3_bucket_lifecycle_configuration" "cloudtrail_logs" {
  count  = local.enable_lifecycle_configuration ? 1 : 0
  bucket = aws_s3_bucket.cloudtrail_bucket.id

  rule {
    id     = "Expire current version after ${var.lifecycle_configuration_current_version_expire_after_days} days"
    status = "Enabled"
    expiration {
      days = var.lifecycle_configuration_current_version_expire_after_days
    }
  }

  rule {
    id     = "Delete expired version after ${var.lifecycle_configuration_expired_version_remove_after_days} days"
    status = "Enabled"
    noncurrent_version_expiration {
      noncurrent_days = var.lifecycle_configuration_expired_version_remove_after_days
    }
    expiration {
      expired_object_delete_marker = true
    }
  }

  rule {
    id     = "Perform cleansing each 90 days"
    status = "Enabled"
    abort_incomplete_multipart_upload {
      days_after_initiation = 90
    }
  }
}
