## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

from aws_cdk import (
    core,
    custom_resources as cust_resource,
    aws_lambda as awslambda
)

from lib.greengrass_setup import GreengrassSetup
from lib.greengrass_ec2_deploy import EC2GreengrassDeploy

class IotGreengrassStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.greengrass_setup = GreengrassSetup(self, "greengrass_setup")

        # Deploy Greengrass canary fleet
        EC2GreengrassDeploy(self, "greengrass_deploy_canary", 
            self.greengrass_setup.core_policy_name, 
            self.greengrass_setup.greengrass_group_role_arn, 
            "canary",
            self.greengrass_setup.script_bucket
        )
        # Deploy Greengrass main fleet
        EC2GreengrassDeploy(self, "greengrass_deploy_main", 
            self.greengrass_setup.core_policy_name, 
            self.greengrass_setup.greengrass_group_role_arn, 
            "main",
            self.greengrass_setup.script_bucket
        )

