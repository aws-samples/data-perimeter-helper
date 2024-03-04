# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
data "aws_region" "logs" {
  provider = aws.logs
}
data "aws_organizations_organization" "logs" {
  provider = aws.logs
}
