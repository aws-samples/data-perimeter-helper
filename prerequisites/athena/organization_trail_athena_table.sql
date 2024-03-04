/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
Example of Amazon Athena query to create a table to query Amazon CloudTrail logs recorded by your organization trail
Placeholders are between [ ]
	[TABLE_NAME]
		Name of the Athena table, example: cloudtrail_logs
	[BUCKET_NAME_WITH_PREFIX]
		Name of your Amazon S3 bucket that hosts CloudTrail logs
	[ORGANIZATION_ID]
		ID of your AWS organization 
		Example: o-xxxxxxxx
		This field is present by default for organizational trail on the S3 path, if you have a custom setup you need to adapt below rows:
			LOCATION 's3://[BUCKET_NAME_WITH_PREFIX]/AWSLogs/[ORGANIZATION_ID]/'
			'storage.location.template'='s3://[BUCKET_NAME_WITH_PREFIX]/AWSLogs/[ORGANIZATION_ID]/${p_account}/CloudTrail/${p_region}/${p_date}'
	[REGIONS]
		List of AWS regions that you use
		Add by default us-east-1 to query events on global resources, example: IAM or CloudFront
		Example: eu-west-3,us-east-1
*/
CREATE EXTERNAL TABLE IF NOT EXISTS [TABLE_NAME] (
	eventVersion STRING,
	userIdentity STRUCT<
		type: STRING,
		principalId: STRING,
		arn: STRING,
		accountId: STRING,
		invokedBy: STRING,
		accessKeyId: STRING,
		userName: STRING,
		sessionContext: STRUCT<
			attributes: STRUCT<
				mfaAuthenticated: STRING,
				creationDate: STRING>,
			sessionIssuer: STRUCT<
				type: STRING,
				principalId: STRING,
				arn: STRING,
				accountId: STRING,
				userName: STRING>,
			ec2RoleDelivery: STRING,
			webIdFederationData: MAP<STRING,STRING>>>,
	eventTime STRING,
	eventSource STRING,
	eventName STRING,
	awsRegion STRING,
	sourceIpAddress STRING,
	userAgent STRING,
	errorCode STRING,
	errorMessage STRING,
	requestParameters STRING,
	responseElements STRING,
	additionalEventData STRING,
	requestId STRING,
	eventId STRING,
	readOnly STRING,
	resources ARRAY<STRUCT<
		arn: STRING,
		accountId: STRING,
		type: STRING>>,
	eventType STRING,
	apiVersion STRING,
	recipientAccountId STRING,
	serviceEventDetails STRING,
	sharedEventID STRING,
	vpcEndpointId STRING,
	tlsDetails STRUCT<
		tlsVersion:string,
		cipherSuite:string,
		clientProvidedHostHeader:string
	>
)
PARTITIONED BY (
`p_account` string,
`p_region` string,
`p_date` string
)
ROW FORMAT SERDE 'org.apache.hive.hcatalog.data.JsonSerDe'
STORED AS INPUTFORMAT 'com.amazon.emr.cloudtrail.CloudTrailInputFormat'
OUTPUTFORMAT 'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION 's3://[BUCKET_NAME_WITH_PREFIX]/AWSLogs/[ORGANIZATION_ID]/'
TBLPROPERTIES (
	'projection.enabled'='true',
	'projection.p_date.type'='date',
	'projection.p_date.format'='yyyy/MM/dd', 
	'projection.p_date.interval'='1', 
	'projection.p_date.interval.unit'='DAYS', 
	'projection.p_date.range'='2022/01/01,NOW', 
	'projection.p_region.type'='enum',
	'projection.p_region.values'='[REGIONS]',
	'projection.p_account.type'='injected',
	'storage.location.template'='s3://[BUCKET_NAME_WITH_PREFIX]/AWSLogs/[ORGANIZATION_ID]/${p_account}/CloudTrail/${p_region}/${p_date}'
)
