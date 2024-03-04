# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# KMS Key to encrypt Athena outputs
resource "aws_kms_key" "athena_db" {
  description             = "KMS key for Athena ouputs"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.key_policy_athena_db.json
}

resource "aws_kms_alias" "athena_db" {
  name          = "alias/athena/${var.prefix}-outputs-encryption-${var.deployment_uuid}"
  target_key_id = aws_kms_key.athena_db.key_id
}

data "aws_iam_policy_document" "key_policy_athena_db" {
  #checkov:skip=CKV_AWS_109:Wildcard reviewed for this KMS key policy
  #checkov:skip=CKV_AWS_111:Wildcard reviewed for this KMS key policy
  #checkov:skip=CKV_AWS_356:Ensure no IAM policies documents allow "*" as a statement's resource for restrictable actions:Wildcard reviewed for this KMS key policy
  statement {
    effect = "Allow"
    sid    = "DelegateAllToIAMForAdmin"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.id}:root"]
    }
    actions = [
      "kms:*"
    ]
    resources = [
      "*"
    ]
    condition {
      test     = "ArnEquals"
      variable = "aws:PrincipalArn"
      values = concat(
        [
          data.aws_iam_session_context.current.issuer_arn
        ],
        var.list_additionnal_key_admins_roles_arn
      )
    }
  }
  statement {
    effect = "Allow"
    sid    = "DelegateToIamUsage"
    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.id}:root"]
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = [
      "*"
    ]
  }
  statement {
    effect = "Allow"
    sid    = "DelegateToIamReadOnly"
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
