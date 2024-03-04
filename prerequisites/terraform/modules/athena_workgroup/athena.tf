# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
# Athena workgroup to store Athena configuration (to be deployed once only)
resource "aws_athena_workgroup" "this" {
  name          = "${var.prefix}-athena-workgroup-${var.deployment_uuid}"
  force_destroy = var.force_destroy
  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = false

    result_configuration {
      output_location = "s3://${aws_s3_bucket.athena_output.bucket}/output/"

      encryption_configuration {
        encryption_option = "SSE_KMS"
        kms_key_arn       = aws_kms_key.athena_db.arn
      }
    }
  }
}

resource "aws_athena_named_query" "cloudtrail_create_table_org" {
  count     = var.generate_athena_sql_create_table_organizational_trail ? 1 : 0
  name      = "cloudtrail_create_table_org_trail"
  workgroup = aws_athena_workgroup.this.id
  database  = "default"
  query = templatefile(
    "${path.module}/athena_queries/cloudtrail_create_table_org.sql.tftpl",
    {
      tftpl_cloudtrail_bucket_name = var.cloudtrail_bucket_name
      tftpl_organization_id        = data.aws_organizations_organization.current.id
      tftpl_cloudtrail_enum_region = join(",", var.list_athena_cloudtrail_enum_regions)
    }
  )
}

resource "aws_athena_named_query" "cloudtrail_create_table_local" {
  count     = var.generate_athena_sql_create_table_local_trail ? 1 : 0
  name      = "cloudtrail_create_table_local_trail"
  workgroup = aws_athena_workgroup.this.id
  database  = "default"
  query = templatefile(
    "${path.module}/athena_queries/cloudtrail_create_table_local.sql.tftpl",
    {
      tftpl_cloudtrail_bucket_name = var.cloudtrail_bucket_name
      tftpl_cloudtrail_enum_region = join(",", var.list_athena_cloudtrail_enum_regions)
    }
  )
}