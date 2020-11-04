## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import boto3
import json
import os
import sys
import time
from pathlib import Path

Path("out").mkdir(parents=True, exist_ok=True)
PARAMETER_FILE = os.environ.get('PARAMETER_FILE','deploy_params.json')
FAILURES_FILE = os.environ.get('FAILURES_FILE','out/deployment_failures.json')
tagging_client = boto3.client('resourcegroupstaggingapi')
gg_client = boto3.client('greengrass')

try:
    with open(PARAMETER_FILE, "r+") as json_file:
        deployment_parameter_sets = json.load(json_file)
except FileNotFoundError:
    deployment_parameter_sets = []

deployments = {}

for deployment_parameter_set in deployment_parameter_sets:

    group_id = deployment_parameter_set['GroupId']
    group = gg_client.get_group(GroupId=group_id)

    group_version = gg_client.get_group_version(
        GroupId=group_id,
        GroupVersionId=group['LatestVersion']
        )

    group_version_id = group_version['Version']
    deployment = gg_client.create_deployment(
        DeploymentType='NewDeployment',
        GroupId=group_id,
        GroupVersionId=group_version_id,
        )

    deployments[group_id] = deployment
    
done_deployments = []
failed = []

for i in range(100):
    for group_id, deployment in deployments.items():

        deployment_status = gg_client.get_deployment_status(
            GroupId=group_id,
            DeploymentId=deployment['DeploymentId'],
        )

        status = deployment_status['DeploymentStatus']
        print('GroupId {} Status: {}'.format(group_id,status ))

        if status == 'Success':
            done_deployments.append(group_id)

        elif status == 'Failure':
            done_deployments.append(group_id)
            failed.append(
                {group_id:
                    {
                        'ErrorMessage': deployment_status['ErrorMessage'],
                        'ErrorDetails': deployment_status['ErrorDetails'],
                    }
                })
        
    for done_deployment in done_deployments:
        del deployments[done_deployment]
    done_deployments = []
        
    if len(deployments.items()) == 0:
        break

    time.sleep(1.0)

if len(failed) > 0:
    print('Deployment Failed: {}'.format(failed))

if len(failed) == 0 and len(deployments.items()) == 0:
    print('Deployment Success')

if len(deployments.items()) > 0:
    print('Deployment timedout')
    failed.append('TIMEOUT')


f = open(FAILURES_FILE, "w+")
f.write(json.dumps(failed))
f.close()