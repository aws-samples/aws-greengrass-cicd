## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

from aws_cdk import (
    core,
    aws_iot as iot,
    custom_resources as cust_resource,
    aws_lambda as awslambda,
    aws_iam as iam,
    aws_greengrass as greengrass,
    aws_ssm as ssm,
)

import uuid
class LambdaFunction(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.lambda_code = awslambda.Code.asset("src/lambda") 

        greengrass_lambda = awslambda.Function(
            self,
            "Lambda",
            runtime=awslambda.Runtime.PYTHON_3_7,
            code=self.lambda_code,
            handler="device_shadow.handler",
            function_name="iot-gg-cicd-workshop-function",
        )

        version = greengrass_lambda.current_version
        
        cfn_version: awslambda.CfnVersion = version.node.try_find_child("Resource")
        cfn_version.cfn_options.deletion_policy = core.CfnDeletionPolicy.RETAIN

        canary_lambda_alias = awslambda.Alias(
            self,
            "LambdaAlias",
            alias_name="CANARY",
            version=version,
        )
        ssm.StringParameter(
            self, 
            "FunctionArnParameter", 
            parameter_name="/iot-gg-cicd-workshop/function/function_arn", 
            string_value="{}:{}".format(greengrass_lambda.function_arn, version.version),
            )
        ssm.StringParameter(
            self, 
            "CanaryVersionArnParameter", 
            parameter_name="/iot-gg-cicd-workshop/function/canary_version_arn", 
            string_value=canary_lambda_alias.function_arn,
            )

class LambdaAlias(core.Stack):
    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        function_arn = ssm.StringParameter.value_for_string_parameter(
            self, 
            "/iot-gg-cicd-workshop/function/function_arn"
            )

        version = awslambda.Version.from_version_arn(self, "Version", version_arn=function_arn)

        prod_lambda_alias = awslambda.Alias(
            self,
            "LambdaAlias",
            alias_name="PROD",
            version=version,
        )
        ssm.StringParameter(
            self, 
            "ProdVersionArnParameter", 
            parameter_name="/iot-gg-cicd-workshop/function/prod_version_arn", 
            string_value=prod_lambda_alias.function_arn,
            )       

class GreengrassCoreGroupDefinitions(core.Stack):
    def __init__(self, scope: core.Construct, id: str, deployment_parameter_sets: [dict], **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        function_version_arn = core.CfnParameter(self, "lambdaFunctionArn", type="String").value_as_string

        for deployment_parameter_set in deployment_parameter_sets:
             
            group_id = deployment_parameter_set['GroupId']
            group_name = deployment_parameter_set['GroupName']
            thing_arn = deployment_parameter_set['ThingArn']
            cert_arn = deployment_parameter_set['CertificateArn']
            device_arn = str(thing_arn).replace("gg-core", "gg-device")
            device_name = device_arn.split('/')[-1]

            #####################
            #  Core Definition  #
            #####################
            greengrass_core_def = greengrass.CfnCoreDefinition(self, 'GreengrassCoreDefinition-{}'.format(group_name),
                name=group_name,
                initial_version={
                    'cores': [{
                        'id': '1',
                        'certificateArn': cert_arn,
                        'thingArn': thing_arn,
                        'syncShadow': True
                }]
                }
            )

            #######################
            #  Device Definition  #
            #######################
            greengrass_device_def = greengrass.CfnDeviceDefinition(self, 'GreengrassDeviceDefinition-{}'.format(group_name),
                name=group_name,
                initial_version={
                    'devices': [{
                        'id': '1',
                        'certificateArn': cert_arn,
                        'thingArn': device_arn,
                        'syncShadow': True
                }]
                }
            )

            ################################
            #  Lambda Function Definition  #
            ################################
            greengrass_function_def = greengrass.CfnFunctionDefinition(self, 'GreengrassFunctionDefinition-{}'.format(group_name),
                name="GreengrassFunction-{}".format(group_name),
                initial_version={
                    'defaultConfig': {
                        'execution': {
                            'isolationMode': "GreengrassContainer"
                        }
                    },
                    'functions': [{
                        'id': '1',
                        'functionArn': function_version_arn,
                        'functionConfiguration': {
                            'encodingYype': 'binary',
                            'pinned': True,
                            'executable': 'index.py',
                            'memorySize': 65536,
                            'timeout': 300,
                            'environment': {
                                'variables': {
                                    'CORE_NAME': group_name,
                                    'DEVICE_NAME': device_name
                                },
                                'execution': {
                                    'isolationMode': 'GreengrassContainer',
                                    'runAs': {
                                        'uid': 1,
                                        'gid': 10
                                    }
                                }
                            }
                        }
                    }]
                }    
            )
            ############################
            #  Subscription Definition #
            ############################
            greengrass_subscription_def = greengrass.CfnSubscriptionDefinition(self, 'GreengrassSubscriptionDefinition-{}'.format(group_name), 
                name='GreengrassSubscription',
                initial_version={
                    'subscriptions': [
                        {
                            'id': '1',
                            'source': 'cloud',
                            'subject': '{}/update'.format(device_name),
                            'target': function_version_arn
                        },
                        # {
                        #     'id': '2',
                        #     'source': function_version_arn,
                        #     'subject': '{}/telemetry'.format(device_name),
                        #     'target': 'cloud',
                        # }
                    ]
                }
            )

            greengrass_group_version = greengrass.CfnGroupVersion(self, 'GreengrassGroupVersion-{}'.format(group_name),
                group_id=group_id,
                core_definition_version_arn=greengrass_core_def.attr_latest_version_arn,
                function_definition_version_arn=greengrass_function_def.attr_latest_version_arn,
                subscription_definition_version_arn=greengrass_subscription_def.attr_latest_version_arn,
                device_definition_version_arn=greengrass_device_def.attr_latest_version_arn
            )