# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Creates the bucket for CloudTrail logs and the KMS key to encrypt them
module "cloudtrail_bucket" {
  source = "../../modules/cloudtrail_bucket"
  providers = {
    aws = aws.logs
  }
  prefix                = var.prefix
  force_destroy         = true
  cloudtrail_trail_name = local.cloudtrail_trail_name
  deployment_uuid       = random_string.deployment_uuid.result

  list_additionnal_key_admins_roles_arn = var.list_additionnal_key_admins_roles_arn
  only_organization_trail               = false
  resource_policy_aws_source_account_cloudtrail = [
    data.aws_caller_identity.org_member_1.id,
    data.aws_caller_identity.org_member_2.id
  ]
  lifecycle_configuration_current_version_expire_after_days = 360 * 2
  lifecycle_configuration_expired_version_remove_after_days = 90
}

# Creates a local trail with only data event to avoid duplicate of management events
module "cloudtrail_trail_org_member_1" {
  source = "../../modules/cloudtrail_trail"
  providers = {
    aws = aws.org_member_1
  }
  depends_on = [
    module.cloudtrail_bucket
  ]
  cloudtrail_trail_name       = local.cloudtrail_trail_name
  cloudtrail_logs_bucket_name = module.cloudtrail_bucket.cloudtrail_logs_bucket_name
  cloudtrail_logs_kms_key_arn = module.cloudtrail_bucket.cloudtrail_logs_kms_key_arn
  is_organization_trail       = false
  enable_management_event     = true
  enable_s3_data_event        = true
}

# Creates a local trail with only data event to avoid duplicate of management events
module "cloudtrail_trail_org_member_2" {
  source = "../../modules/cloudtrail_trail"
  providers = {
    aws = aws.org_member_2
  }
  depends_on = [
    module.cloudtrail_bucket
  ]
  cloudtrail_trail_name       = local.cloudtrail_trail_name
  cloudtrail_logs_bucket_name = module.cloudtrail_bucket.cloudtrail_logs_bucket_name
  cloudtrail_logs_kms_key_arn = module.cloudtrail_bucket.cloudtrail_logs_kms_key_arn
  is_organization_trail       = false
  enable_management_event     = true
  enable_s3_data_event        = true
}


# Creates the bucket for Athena outputs, the KMS key to encrypt them and the Athena workgroup along with queries to create tables and query CloudTrail logs
module "athena_workgroup" {
  source = "../../modules/athena_workgroup"
  providers = {
    aws = aws.logs
  }
  prefix                                                = var.prefix
  force_destroy                                         = true
  cloudtrail_bucket_name                                = module.cloudtrail_bucket.cloudtrail_logs_bucket_name
  list_additionnal_key_admins_roles_arn                 = var.list_additionnal_key_admins_roles_arn
  deployment_uuid                                       = random_string.deployment_uuid.id
  list_athena_cloudtrail_enum_regions                   = var.list_athena_cloudtrail_enum_regions
  generate_athena_sql_create_table_organizational_trail = true
  generate_athena_sql_create_table_local_trail          = true
}
