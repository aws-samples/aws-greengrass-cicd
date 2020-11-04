## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import boto3

iot = boto3.client("iot")
greengrass = boto3.client("greengrass")

groups = greengrass.list_groups()

groups_to_delete = []
for group in groups['Groups']:
    group_info = greengrass.get_group(
        GroupId=group['Id']
    )
    if group_info.get('tags',{}).get('fleet', '') in ('canary', 'main'):
        groups_to_delete.append(group_info)
if len(groups_to_delete) == 0:
    print("No groups to delete")
else:   
    print("The following groups and things with certificates will be deleted:")
    for group_info in groups_to_delete:
        print(group_info['Name'])

    gg_uuid = []

    # Reset deployment and delete groups
    for group_info in groups_to_delete:
        print("Deleting group: {}".format(group_info['Name']))
        gg_uuid.append(group_info['Name'].split('-')[2])
        greengrass.reset_deployments(
            Force=True, 
            GroupId=group_info['Id']
        )
        greengrass.delete_group(
            GroupId=group_info['Id']
        )

    things = iot.list_things()
    certificates_to_delete = []

    # Detach all certificates delete thing
    for thing in things['things']:
        if any(t in thing['thingName'] for t in gg_uuid):
            print("Deleting thing: {}".format(thing['thingName']))
            principals = iot.list_thing_principals(
                thingName=thing['thingName']
            )

            for principal in principals["principals"]:
                cert_id = principal.split('/')[1]
                if cert_id not in certificates_to_delete:
                    certificates_to_delete.append(cert_id)

                iot.detach_thing_principal(
                    thingName=thing['thingName'],
                    principal=principal
                )

            iot.delete_thing(
                thingName=thing['thingName'],
                # expectedVersion=thing_info['version']
            )

    # Delete all certificates 
    for certificate in certificates_to_delete:
        print("Deleting certificate: {}".format(certificate))
        iot.update_certificate(
            certificateId=certificate,
            newStatus='INACTIVE'
            )

        iot.delete_certificate(
            certificateId=certificate,
            forceDelete=True
        )

    # Delete all orphan core definitions
    core_definitions = greengrass.list_core_definitions()
    for core_definition in core_definitions["Definitions"]:
        core_definition_details = greengrass.get_core_definition(
            CoreDefinitionId=core_definition['Id']
        )
        if core_definition_details.get('tags',{}).get('fleet', '') in ('canary', 'main'):
            print("Deleting core definition: {}".format(core_definition['Id']))
            greengrass.delete_core_definition(
                CoreDefinitionId=core_definition['Id']
            )
    