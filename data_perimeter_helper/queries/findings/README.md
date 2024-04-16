<!--
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
-->

## List of queries
* [findings_iam_aa_external_access_org_boundary](#query-name-findings_iam_aa_external_access_org_boundary)
* [findings_sh_external_access_org_boundary](#query-name-findings_sh_external_access_org_boundary)

# Query name: findings_iam_aa_external_access_org_boundary

### Query description

List all active AWS IAM Access Analyzer external access findings with the organization as zone of trust.
You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your resources. You can use the global condition key [aws:PrincipalOrgId](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) to limit access to your resources to principals belonging to your AWS organization.
    



# Query name: findings_sh_external_access_org_boundary

### Query description

This query extracts all AWS SecurityHub findings tied to IAM Access Analyzer external access findings with the organization as zone of trust.
Note that (1) IAM Access Analyzer external access findings failing in error are not sent to SecurityHub and (2) IAM Access Analyzer external access findings in SecurityHub contains only one external principal even if the resource-based policy allows multiple principals.
You can use this query to accelerate implementation of the [**identity perimeter**](https://aws.amazon.com/fr/blogs/security/establishing-a-data-perimeter-on-aws-allow-only-trusted-identities-to-access-company-data/) controls on your resources. You can use the global condition key [aws:PrincipalOrgId](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies_condition-keys.html#condition-keys-principalorgid) to limit access to your resources to principals belonging to your AWS organization.
    



