# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
// KMS key used to encrypt CloudTrail logs stored in s3
resource "aws_kms_key" "cloudtrail_bucket" {
  description             = "KMS key for CloudTrail logs"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.kms_policy_cloudtrail_bucket.json
}

resource "aws_kms_alias" "cloudtrail_bucket" {
  name          = "alias/s3/${var.prefix}-cloudtrail-${var.deployment_uuid}"
  target_key_id = aws_kms_key.cloudtrail_bucket.key_id
}

/*
KMS key policy for the KMS key used to encrypt CloudTrail logs in the s3 bucket
Enforce least privilege principle
*/
data "aws_iam_policy_document" "kms_policy_cloudtrail_bucket" {
  #checkov:skip=CKV_AWS_109:Wildcard reviewed for this KMS key policy
  #checkov:skip=CKV_AWS_111:Wildcard reviewed for this KMS key policy
  #checkov:skip=CKV_AWS_356:Ensure no IAM policies documents allow "*" as a statement's resource for restrictable actions:Wildcard reviewed for this KMS key policy
  statement {
    sid = "IAMDelegationForAdminRole"
    principals {
      type = "AWS"
      identifiers = [
        "arn:aws:iam::${data.aws_caller_identity.current.id}:root"
      ]
    }
    actions = [
      "kms:*"
    ]
    resources = [
      "*"
    ]
    condition {
      test     = "ArnLike"
      variable = "aws:PrincipalArn"
      values = concat(
        var.list_additionnal_key_admins_roles_arn,
        [
          data.aws_iam_session_context.current.issuer_arn
        ]
      )
    }
  }
  statement {
    sid = "CloudTrailUsage"
    principals {
      type = "Service"
      identifiers = [
        "cloudtrail.amazonaws.com"
      ]
    }
    actions = [
      "kms:DescribeKey",
      "kms:GenerateDataKey*"
    ]
    resources = [
      "*"
    ]
    dynamic "condition" {
      for_each = length(var.resource_policy_aws_source_arn_cloudtrail_arn) > 0 ? [1] : []
      content {
        test     = "ArnEquals"
        variable = "aws:SourceArn"
        values   = var.resource_policy_aws_source_arn_cloudtrail_arn
      }
    }
    dynamic "condition" {
      for_each = length(var.resource_policy_aws_source_account_cloudtrail) > 0 ? [1] : []
      content {
        test     = "StringEquals"
        variable = "aws:SourceAccount"
        values   = var.resource_policy_aws_source_account_cloudtrail
      }
    }
  }
  statement {
    effect = "Allow"
    sid    = "IAMDelegationForReadOnly"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.id}:root"]
    }
    actions = [
      "kms:DescribeKey",
      "kms:GetKeyPolicy",
      "kms:ListGrants",
      "kms:ListKeyPolicies",
      "kms:ListResourceTags"
    ]
    resources = [
      "*"
    ]
  }
}