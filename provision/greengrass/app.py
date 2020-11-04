#!/usr/bin/env python3
import os
from aws_cdk import core

from lib.iot_greengrass_stack import IotGreengrassStack


env = core.Environment(
    account=os.environ['CDK_DEFAULT_ACCOUNT'],
    region=os.environ['CDK_DEFAULT_REGION'],
)

app = core.App()
iot_greengrass_stack = IotGreengrassStack(app, "iot-gg-cicd-workshop-iot-greengrass", env=env)

app.synth()
