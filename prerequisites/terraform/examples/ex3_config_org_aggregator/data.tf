# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
data "aws_caller_identity" "security_tooling" {
  provider = aws.security_tooling
}
