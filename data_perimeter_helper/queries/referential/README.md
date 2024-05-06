<!-- # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0 -->
## Description

You can use `referential` queries to get insights on your resource configurations.    
The `referential` queries:
- Rely on AWS Config advanced queries and AWS Organizations API calls.
- Are prefixed with the keyword `referential` and are **not** tied to a specific AWS service nor an AWS account ID.
- Have their results exported to files prefixed with the keyword `referential`.

## List of queries
* [referential_glue_job](#query-name-referential_glue_job)
* [referential_lambda_function](#query-name-referential_lambda_function)
* [referential_sagemaker_notebook](#query-name-referential_sagemaker_notebook)
* [referential_scp](#query-name-referential_scp)
* [referential_service_role](#query-name-referential_service_role)
* [referential_vpce](#query-name-referential_vpce)

# Query name: referential_glue_job

### Query description

List the AWS Glue jobs inventoried in your AWS Config aggregator.   
You can use this query, for example, to review your Glue job that do **not** have any connection nor the special job argument `--disable-proxy-v2` set.
For details on the special job parameter `disable-proxy-v2`, see [Configuring AWS calls to go through your VPC
](https://docs.aws.amazon.com/glue/latest/dg/connection-VPC-disable-proxy.html). For details on AWS Glue connection, see [Connecting to data](https://docs.aws.amazon.com/glue/latest/dg/glue-connections.html). Note that some Glue connection do not require to configure an Amazon Virtual Private Cloud (VPC).

# Query name: referential_lambda_function

### Query description

List the AWS Lambda functions inventoried in your AWS Config aggregator.   
You can use this query, for example, to review your Lambda functions that are **not** connected to your Virtual Private Cloud (VPC).

# Query name: referential_sagemaker_notebook

### Query description

List the Amazon SageMaker notebooks inventoried in your AWS Config aggregator.   
You can use this query, for example, to review your notebook instances that allow *direct internet access*.
For details on the direct internet access configuration, see [Connect a Notebook Instance in a VPC to External Resources](https://docs.aws.amazon.com/sagemaker/latest/dg/appendix-notebook-and-internet-access.html).

# Query name: referential_scp

### Query description

List the service control policies (SCPs) in your organization.
Use this query to review your SCPs and identify policies that implement resource perimeter or network perimeter controls.
The query exports the SCPs to readable JSON files under a subfolder `scp` of your configured output folder.
You can use this query to assess and accelerate the implemention of your [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) and [**network perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-access-to-company-data-only-from-expected-networks/) controls in your SCPs.

# Query name: referential_service_role

### Query description

List the service roles inventoried in your AWS Config aggregator.
You can use this query, for example, to review your service roles and check if the correct tagging strategy is in place.


# Query name: referential_vpce

### Query description

List the Amazon Virtual Private Cloud (Amazon VPC) endpoints in your Config aggregator.
Use this query to review the VPC endpoints that have a default policy or a policy that contains one of the [AWS global condition context keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html) aws:PrincipalOrgId/PrincipalOrgPaths/PrincipalAccount or aws:ResourceOrgId/ResourceOrgPaths/ResourceAccount.
You can use this query to assess and accelerate the implementation of your [**identity perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) and  [**resource perimeter**](https://aws.amazon.com/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-resources-from-my-organization/) controls on your VPC endpoints.

