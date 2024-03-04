# Data perimeter helper - prerequisites with Terraform

# 1. Available modules

Terraform modules are available in path: [./prerequisites/terraform/modules/](./modules/).

1. Module name: `cloudtrail_bucket`:
    - This module deploys an Amazon S3 bucket to host CloudTrail logs.
    - Module is documented in [README.md](./modules/cloudtrail_bucket/README.md) file.

2. Module name: `cloudtrail_trail`:
    - This module deploys an AWS CloudTrail trail.
    - Variables are available to:
        - Deploy an organizational or local trail.
        - Toggle data events.
    - This module depends on `cloudtrail_bucket`.
    - Module is documented in [README.md](./modules/cloudtrail_trail/README.md) file.

3. Module name: `athena_workgroup`:
    - This module deploys an Amazon Athena workgroup.
    - This module depends on `cloudtrail_trail` and `cloudtrail_bucket`.
    - Module is documented in [README.md](./modules/athena_workgroup/README.md) file.

4. Module name: `config_aggregator_central`:
    - This module deploys an AWS Config aggregator at the organization scope or with invitations.
    - Module is documented in [README.md](./modules/config_aggregator_central/README.md) file.

5. Module name: `config_aggregator_invited`:
    - This module deploys AWS Config aggregator authorization, and is needed only for AWS Config aggregator with invitations
    - Module is documented in [README.md](./modules/config_aggregator_invited/README.md) file.

# 2. Available examples

Some examples of above modules combined are provided in path: [./prerequisites/terraform/examples/](./examples/).

For relevant modules, examples of expected input variables are provided in `root.auto_.tfvars` files.
By default, Terraform uses as input any tfvars file following the pattern `*.auto.tfvars`. To use the example file remove the `_` from `root.auto_.tfvars`.

## Example 1: CloudTrail organization trail + Athena workgroup

A CloudTrail organization trail sending logs to a central S3 bucket and an Athena workgroup ready for Athena queries:
> Example path: [./examples/ex1_cloudtrail_org_trail/](./examples/ex1_cloudtrail_org_trail/).

## Example 2: CloudTrail trail + Athena workgroup

Local CloudTrail trails sending logs to a central S3 bucket and an Athena workgroup ready for Athena queries:
> Example path: [./examples/ex2_cloudtrail_local_trail/](./examples/ex2_cloudtrail_local_trail/).

## Example 3: Config organization aggregator
An organization level AWS Config aggregator:
> Example path: [./examples/ex3_config_org_aggregator/](./examples/ex3_config_org_aggregator/).

## Example 4: Config aggregator with invitations
An AWS Config aggregator with invitations:
> Example path: [./examples/ex4_config_with_invit_aggregator/](./examples/ex4_config_with_invit_aggregator/).
