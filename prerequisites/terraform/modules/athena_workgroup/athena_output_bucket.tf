# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Bucket to store Athena outputs
resource "aws_s3_bucket" "athena_output" { # nosemgrep: aws-s3-bucket-versioning-not-enabled
  #checkov:skip=CKV_AWS_144:Cross-region replication to be added as customization if relevant
  #checkov:skip=CKV_AWS_18:Access logs to be added as customization if relevant
  #checkov:skip=CKV2_AWS_62:Ensure S3 buckets should have event notifications enabled:Event notification to be added as customization if relevant
  bucket        = "${var.prefix}-athena-output-${var.deployment_uuid}"
  force_destroy = var.force_destroy
}

// All public access is blocked
resource "aws_s3_bucket_public_access_block" "athena_output" {
  bucket                  = aws_s3_bucket.athena_output.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

// Enable encryption with AWS KMS CMK
resource "aws_s3_bucket_server_side_encryption_configuration" "athena_output" {
  bucket = aws_s3_bucket.athena_output.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.athena_db.arn
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

// Disable ACL
resource "aws_s3_bucket_ownership_controls" "athena_output" {
  bucket = aws_s3_bucket.athena_output.id
  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

// Enable versioning
resource "aws_s3_bucket_versioning" "athena_output" {
  bucket = aws_s3_bucket.athena_output.id
  versioning_configuration {
    status = "Enabled"
  }
}

// Bucket policy
resource "aws_s3_bucket_policy" "athena_output" {
  bucket = aws_s3_bucket.athena_output.id
  policy = data.aws_iam_policy_document.bucket_policy_athena_output.json
}

data "aws_iam_policy_document" "bucket_policy_athena_output" {
  # Data Protection controls
  statement {
    effect = "Deny"
    sid    = "DenyNotEncryptedFiles"
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
      aws_s3_bucket.athena_output.arn,
      "${aws_s3_bucket.athena_output.arn}/*"
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
      aws_s3_bucket.athena_output.arn,
      "${aws_s3_bucket.athena_output.arn}/*"
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


resource "aws_s3_bucket_lifecycle_configuration" "athena_outputs" {
  count  = local.enable_lifecycle_configuration ? 1 : 0
  bucket = aws_s3_bucket.athena_output.id

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
