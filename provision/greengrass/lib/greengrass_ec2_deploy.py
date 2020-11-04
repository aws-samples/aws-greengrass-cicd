## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import os.path

from aws_cdk import (
    core,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    aws_iam as iam
)

dirname = os.path.dirname(__file__)

class EC2GreengrassDeploy(core.Construct):
    def __init__(self, scope: core.Construct, id: str, core_policy_name: str, group_role_arn: str, fleet: str, script_bucket, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # VPC
        vpc = ec2.Vpc(self, "VPC",
            nat_gateways=0,
            subnet_configuration=[ec2.SubnetConfiguration(name="public",subnet_type=ec2.SubnetType.PUBLIC)]
        )

        # Instance Role and SSM Managed Policy
        role = iam.Role(self, "GreengrassInstance", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonEC2RoleforSSM"))
        role.add_to_policy(
            iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        'iot:*',
                        'greengrass:*',
                        'iam:PassRole',
                        'ssm:*',
                        's3:*'
                    ],
                    resources=['*']
                )
        )

        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )

        # Give the instance access to the S3 bucket to download the Greengrass onboarding script
        script_bucket.grant_read(role)

        with open("lib/user_data.txt", "r") as user_data_file:
            user_data = user_data_file.read()

        user_data = user_data.replace("<s3_bucket>", script_bucket.bucket_name)
        user_data = user_data.replace("<thing_policy>", core_policy_name)
        user_data = user_data.replace("<group_role_arn>", group_role_arn)
        user_data = user_data.replace("<fleet>", fleet)

        # Create an autoscaling group to make it simpler in the workshop to add new Greengrass
        # groups. Start with 2 instances
        asg = autoscaling.AutoScalingGroup(self, "ASG",
            auto_scaling_group_name="iot-gg-cicd-workshop-{}".format(fleet),
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE2, ec2.InstanceSize.MICRO),
            machine_image=amzn_linux,
            min_capacity=2,
            max_capacity=2,
            role=role
        )

        asg.user_data.add_commands(user_data)