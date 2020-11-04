## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

import json
import time
import unittest
import uuid
import warnings
import logging
import boto3
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

def ignore_warnings(test_func):
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            test_func(self, *args, **kwargs)
    return do_test

class TestShadowUpdateFunction(unittest.TestCase):

    def setUp(self):
        PARAMETER_FILE = '../deploy_params.json'
        try:
            with open(PARAMETER_FILE, "r+") as json_file:
                deployment_parameter_sets = json.load(json_file)
                self.device_name = deployment_parameter_sets[0]['ThingArn'].split('/')[-1].replace('gg-core', 'gg-device')
        except:
            self.device_name = None
        

    @ignore_warnings
    def test_echo(self):
        if self.device_name is None:
            assert False
            
        input_topic = '{}/update'.format(self.device_name)

        iot_client = boto3.client('iot-data')

        param =  str(uuid.uuid4())

        shadow_updated = False
        for i in range(5):
            if shadow_updated:
                break
            iot_client.publish(
                topic=input_topic, 
                qos=1,
                payload=json.dumps({'message': param})
            )

            time.sleep(5)

            try:
                shadow_info = iot_client.get_thing_shadow(
                    thingName=self.device_name
                )

                shadow = json.loads(shadow_info['payload'].read())

                if 'reported' in shadow['state']:
                    if shadow['state']['reported']['param'] == param:
                        shadow_updated = True
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    logger.info('Shadow may not have been synced yet. Try again')
                else:
                    raise e

        assert shadow_updated


