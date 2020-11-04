## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import boto3
from botocore.exceptions import ClientError

greengrass = boto3.client("greengrass")
iam = boto3.client("iam")

def verify_service_role(event):
    # On create of this stack we want to ensure that there is a greengrass 
    # service role associated with the account in that region

    # Check if there is a service role already attached to the account
    try:
        greengrass.get_service_role_for_account()
    except ClientError as e:
    # Role is not attached so let see if it exists otherwise create it
        try:
            role = iam.get_role(
                RoleName="Greengrass_ServiceRole"
            )
        except ClientError as e:
        # Create role
            role = iam.create_role( 
                RoleName="Greengrass_ServiceRole",
                AssumeRolePolicyDocument='{"Version": "2012-10-17","Statement": [{"Effect": "Allow","Principal": {"Service": "greengrass.amazonaws.com"},"Action": "sts:AssumeRole"}]}',
                Description="Service Role for Greengrass",
            )
            iam.attach_role_policy(
                RoleName="Greengrass_ServiceRole",
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSGreengrassResourceAccessRolePolicy",
            )
        greengrass.associate_service_role_to_account(RoleArn=role["Role"]["Arn"])

def handler(event, context):
    request_type = event['RequestType']
    if request_type == 'Create': return verify_service_role(event)
