<!-- # Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0 -->
## Description

You can use `referential` queries to get insights on your resource configurations.    
The `referential` queries:
- Rely on AWS Config advanced queries and AWS Organizations API calls.
- Are prefixed with the keyword `referential` and are **not** tied to a specific AWS service nor an AWS account ID.
- Have their results exported to files prefixed with the keyword `referential`.

## List of queries

* [referential_lambda_function](#query-name-referential_lambda_function)
* [referential_service_role](#query-name-referential_service_role)

# Query name: referential_lambda_function

### Query description

List all AWS Lambda functions inventoried in your AWS Config aggregator.   
You can use this query, for example, to review your Lambda functions that are **not** connected to your Virtual Private Cloud (VPC).


# Query name: referential_service_role

### Query description

List all service roles inventoried in your AWS Config aggregator.
You can use this query, for example, to review your service roles and check if the correct tagging strategy is in place.
