# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.1.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5.1"
    }
  }
  required_version = ">= 0.14.9"
}

// Provider for the security account
provider "aws" {
  profile = var.profile_name_security_tooling
  region  = var.main_region
  alias   = "security_tooling"
}

