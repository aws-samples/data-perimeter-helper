# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Creates the bucket for CloudTrail logs and the KMS key to encrypt them
module "cloudtrail_bucket" {
  source = "../../modules/cloudtrail_bucket"
  providers = {
    aws = aws.logs
  }
  prefix                = var.prefix
  cloudtrail_trail_name = local.cloudtrail_trail_name
  deployment_uuid       = random_string.deployment_uuid.id
  # environment                           = var.environment
  force_destroy                         = true
  list_additionnal_key_admins_roles_arn = var.list_additionnal_key_admins_roles_arn
  only_organization_trail               = true
  resource_policy_aws_source_arn_cloudtrail_arn = [
    "arn:aws:cloudtrail:${data.aws_region.logs.name}:${data.aws_organizations_organization.logs.master_account_id}:trail/${local.cloudtrail_trail_name}"
  ]
  lifecycle_configuration_current_version_expire_after_days = 360 * 2
  lifecycle_configuration_expired_version_remove_after_days = 90
}

# Creates an organizational trail with only data event to avoid duplicate of management events
module "cloudtrail_org_trail" {
  source = "../../modules/cloudtrail_trail"
  providers = {
    aws = aws.root
  }
  depends_on = [
    module.cloudtrail_bucket
  ]
  cloudtrail_trail_name       = local.cloudtrail_trail_name
  cloudtrail_logs_bucket_name = module.cloudtrail_bucket.cloudtrail_logs_bucket_name
  cloudtrail_logs_kms_key_arn = module.cloudtrail_bucket.cloudtrail_logs_kms_key_arn
  is_organization_trail       = true
  enable_management_event     = false
  enable_s3_data_event        = true
  s3_data_event_exclude_bucket_arn = [
    module.cloudtrail_bucket.cloudtrail_logs_bucket_arn
  ]
}

# Creates the bucket for Athena outputs, the KMS key to encrypt them and the Athena workgroup along with queries to create tables and query CloudTrail logs
module "athena_workgroup" {
  source = "../../modules/athena_workgroup"
  providers = {
    aws = aws.logs
  }
  prefix                                = var.prefix
  cloudtrail_bucket_name                = module.cloudtrail_bucket.cloudtrail_logs_bucket_name
  list_additionnal_key_admins_roles_arn = var.list_additionnal_key_admins_roles_arn
  deployment_uuid                       = random_string.deployment_uuid.id
  # environment                                           = var.environment
  force_destroy                                         = true
  list_athena_cloudtrail_enum_regions                   = var.list_athena_cloudtrail_enum_regions
  generate_athena_sql_create_table_organizational_trail = true
  generate_athena_sql_create_table_local_trail          = false
}

output "cloudtrail_logs_bucket_name" {
  value = module.cloudtrail_bucket.cloudtrail_logs_bucket_name
}
