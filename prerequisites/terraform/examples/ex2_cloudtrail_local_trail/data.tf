# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
data "aws_caller_identity" "org_member_1" {
  provider = aws.org_member_1
}

data "aws_caller_identity" "org_member_2" {
  provider = aws.org_member_2
}