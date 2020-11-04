## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import boto3
import json
import os
import sys

deployment_fleet = sys.argv[1]
GROUP_CONFIG_FILE = os.environ.get('GROUP_CONFIG_FILE','gg_group_config.json')
tagging_client = boto3.client('resourcegroupstaggingapi')
gg_client = boto3.client('greengrass')

# Get all the Greengrass group with the specific fleet tag
results = tagging_client.get_paginator('get_resources').paginate(
    TagFilters=[
        {
            'Key': 'fleet',
            'Values': [
                deployment_fleet,
            ],
        },
    ],
    ResourceTypeFilters=['greengrass:groups'],
    PaginationConfig={
        'MaxItems': 10000,
    }
)

# Generate the configuration file
deployment_parameter_sets = []
for result in results:
    for resource in result['ResourceTagMappingList']:
        deployment_parameter_set = {}
        group_arn = resource['ResourceARN']
        group_id = group_arn.split('/')[-1]
        group = gg_client.get_group(GroupId=group_id)
        group_version = gg_client.get_group_version(
            GroupId=group_id,
            GroupVersionId=group['LatestVersion']
            )
        core_definition_version_arn = group_version['Definition']['CoreDefinitionVersionArn']
        core_definition_version_id = core_definition_version_arn.split('/')[-3]
        core_definition_version_version = core_definition_version_arn.split('/')[-1]
        core_definition_version = gg_client.get_core_definition_version(
            CoreDefinitionId=core_definition_version_id, 
            CoreDefinitionVersionId=core_definition_version_version,
            )
        deployment_parameter_set['GroupId'] = group_id
        deployment_parameter_set['GroupName'] = group['Name']
        deployment_parameter_set['ThingArn'] = core_definition_version['Definition']['Cores'][0]['ThingArn']
        deployment_parameter_set['CertificateArn'] = core_definition_version['Definition']['Cores'][0]['CertificateArn']
        deployment_parameter_sets.append(deployment_parameter_set)
f = open(GROUP_CONFIG_FILE, "w+")
f.write(json.dumps(deployment_parameter_sets))
f.close()