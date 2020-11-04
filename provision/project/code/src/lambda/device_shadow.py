## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import os
import json
import greengrasssdk
from datetime import datetime

client = greengrasssdk.client('iot-data')

def handler(event, context):
    '''Update shadow'''   
    message = {"state":{"reported":{"param": event['message'], "timestamp": str(datetime.now())}}}
    client.update_thing_shadow(
        thingName=os.environ['DEVICE_NAME'],
        payload=json.dumps(message)
    )