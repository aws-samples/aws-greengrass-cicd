## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import os.path
from aws_cdk import (
    core,
    aws_iot as iot,
    custom_resources as cust_resource,
    aws_lambda as awslambda,
    aws_iam as iam,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy
)

dirname = os.path.dirname(__file__)

class GreengrassSetup(core.Construct):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create bucket and upload scrips 
        bucket = s3.Bucket(self, "ScriptBucket")

        self.script_bucket = bucket

        s3deploy.BucketDeployment(self, "UploadScriptsToBucket",
            sources=[s3deploy.Source.asset(os.path.join(dirname, "scripts"))],
            destination_bucket=bucket
        )

        # Greengrass Core Thing policy
        greengrass_core_policy = iot.CfnPolicy(self,
            'GreenGrassCorePolicy',
            policy_name='greengrass-demo-policy',
            policy_document={
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:Publish",
                            "iot:Subscribe",
                            "iot:Connect",
                            "iot:Receive"
                        ],
                        "Resource": [
                            "*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "iot:GetThingShadow",
                            "iot:UpdateThingShadow",
                            "iot:DeleteThingShadow"
                        ],
                        "Resource": [
                            "*"
                        ]
                    },
                    {
                        "Effect": "Allow",
                        "Action": [
                            "greengrass:*"
                        ],
                        "Resource": [
                            "*"
                        ]
                    }
                ]
            }
        )

        self.core_policy_name = greengrass_core_policy.policy_name

        # Create a Greengrass group role
        greengrass_group_role = iam.Role(self, "GroupRole",
            assumed_by=iam.ServicePrincipal("greengrass.amazonaws.com")
        )
        greengrass_group_role.add_to_policy(iam.PolicyStatement(
            resources=["arn:aws:logs:*:*:*"],
            actions=[
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ]
        ))
        greengrass_group_role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["iot:*"]
        ))
     
        self.greengrass_group_role_arn = greengrass_group_role.role_arn
        
        # A custom resource to verify that there is a service role for greengrass on the account 
        greengrass_mgmt_function = awslambda.SingletonFunction(
            self,
            "MgmttHandler",
            uuid="58854ea2-0624-4ca5-b600-fa88d4b9164e",
            runtime=awslambda.Runtime.PYTHON_3_7,
            code=awslambda.Code.asset("custom_resources"),
            handler="greengrassmgmt.handler",
        )

        greengrass_mgmt_function.add_to_role_policy(
            iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'greengrass:*',
                        'iot:*',
                        'iam:CreateRole',
                        'iam:AttachRolePolicy',
                        'iam:PassRole'
                    ],
                    resources=['*']
                )
        )

        greengrass_mgmt_provider = cust_resource.Provider(self, "MgmtProvider",
            on_event_handler=greengrass_mgmt_function
        )

        core.CustomResource(self, "MgmtCustResource", 
            service_token=greengrass_mgmt_provider.service_token
        )
        
  