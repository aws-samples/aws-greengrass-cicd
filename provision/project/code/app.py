#!/usr/bin/env python3
import os
import json
from aws_cdk import core

from lib.greengrass import LambdaFunction
from lib.greengrass import LambdaAlias
from lib.greengrass import GreengrassCoreGroupDefinitions
GROUP_CONFIG_FILE = os.environ.get('GROUP_CONFIG_FILE','gg_group_config.json')
env = core.Environment(
    account=os.environ['CDK_DEFAULT_ACCOUNT'],
    region=os.environ['CDK_DEFAULT_REGION'],
)

app = core.App()

lambda_stack = LambdaFunction(
    app, 
    id="iot-gg-cicd-workshop-function", 
    env=env
    )
prod_alias_stack = LambdaAlias(
    app, 
    id="iot-gg-cicd-workshop-function-prod-alias", 
    env=env,
    )
try:
    with open(GROUP_CONFIG_FILE, "r+") as json_file:
        deployment_parameter_sets = json.load(json_file)
except FileNotFoundError:
    deployment_parameter_sets = []


prod_core_group_definition_versions_stack = GreengrassCoreGroupDefinitions(
    app,
    id="iot-gg-cicd-workshop-core-group-definition-versions-canary",
    deployment_parameter_sets=deployment_parameter_sets,
    env=env,
)
prod_core_group_definition_versions_stack = GreengrassCoreGroupDefinitions(
    app,
    id="iot-gg-cicd-workshop-core-group-definition-versions-main",
    deployment_parameter_sets=deployment_parameter_sets,
    env=env,
)
app.synth()
