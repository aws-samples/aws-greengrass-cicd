#!/usr/bin/env python3
import os
from aws_cdk import core

from lib.pipeline_stack import PipelineStack

env = core.Environment(
    account=os.environ['CDK_DEFAULT_ACCOUNT'],
    region=os.environ['CDK_DEFAULT_REGION'],
)

app = core.App()

PipelineStack(app, "iot-gg-cicd-workshop-pipelines", env=env)

app.synth()
