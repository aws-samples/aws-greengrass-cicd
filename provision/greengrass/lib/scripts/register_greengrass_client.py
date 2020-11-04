import boto3
import argparse
import json
import uuid
from zipfile import ZipFile
from botocore.exceptions import ClientError

def CreateThingAndAttachedCert(iot, thing_name, certArn):
    iot.create_thing(
        thingName=thing_name
    )
    iot.attach_thing_principal(
        thingName=thing_name,
        principal=certArn,
    )

parser = argparse.ArgumentParser(description="Create Thing, group, and certificates for Greengrass")
parser.add_argument('--thingpolicy')
parser.add_argument('--grouprole')
parser.add_argument('--fleet')
parser.add_argument('--region')
parser.add_argument('--account')
args = parser.parse_args()

gg_id = str(uuid.uuid4())[:8]
core_name = "gg-core-{}".format(gg_id)
device_name = "gg-device-{}".format(gg_id)
group_name = "gg-group-{}".format(gg_id)
policy_name = args.thingpolicy
group_role = args.grouprole
fleet = args.fleet
region = args.region
account = args.account
thing_arn = 'arn:aws:iot:{}:{}:thing/{}'.format(region, account, core_name)

iot = boto3.client('iot', region_name=region)
greengrass = boto3.client("greengrass", region_name=region)
ssm = boto3.client('ssm', region_name=region)
s3 = boto3.client('s3', region_name=region)

response = iot.create_keys_and_certificate(
    setAsActive=True
)
certId = response['certificateId']
certArn = response['certificateArn']
certPem = response['certificatePem']
privateKey = response['keyPair']['PrivateKey']

# Attach to policy that was created in the CDK stack
response = iot.attach_policy(
    policyName=policy_name,
    target=certArn
)

# Create a thing for core and device
CreateThingAndAttachedCert(iot, core_name, certArn)
CreateThingAndAttachedCert(iot, device_name, certArn)

# Save the certificate and key
certfilename = "/greengrass/certs/{}.pem".format(certId)
with open(certfilename, "w") as certfile:
    certfile.write(certPem)

keyfilename = "/greengrass/certs/{}.key".format(certId)
with open(keyfilename, "w") as keyfile:
    keyfile.write(privateKey)

# Get the iot endpoint to be used to connect to AWS IoT core
iot_endpoint = iot.describe_endpoint(endpointType='iot:Data-ATS')['endpointAddress']

with open("config_template.json", "r") as config_template_file:
            config_data = config_template_file.read()

config_data = config_data.replace("<certificateId>", certId)
config_data = config_data.replace("<certificatePem>", certPem)
config_data = config_data.replace("<privateKey>", privateKey)
config_data = config_data.replace("<region>", region)
config_data = config_data.replace("<accountId>", account)
config_data = config_data.replace("<iotEndpoint>", iot_endpoint)
config_data = config_data.replace("<thingname>", core_name)

with open("/greengrass/config/config.json", "w") as config_file:
    config_file.write(config_data)

# Create group
group_info = greengrass.create_group(
    Name=group_name,
    tags={
        'fleet' : fleet
    }
)
greengrass.associate_role_to_group(
    GroupId=group_info['Id'],
    RoleArn=group_role
)

core_def = greengrass.create_core_definition(
    Name=group_name,
    InitialVersion={
        'Cores': [
            {
                'CertificateArn': certArn,
                'Id': '1',
                'ThingArn': thing_arn,
                'SyncShadow': True,
            },
        ]
    },
    tags={
        'fleet': fleet
    }
)

response = greengrass.create_group_version(
    GroupId=group_info['Id'],
    CoreDefinitionVersionArn=core_def['LatestVersionArn']
)

deployment_parameter_sets = []
log = []
try:
    param = ssm.get_parameter(
        Name='/iot-gg-cicd-workshop/s3/prod_deploy_param_bucket',
        WithDecryption=True
    )
    bucket = param['Parameter']['Value']
    log.append(bucket)
    deployment_parameter_set = {}
    deployment_parameter_set['GroupId'] = group_info['Id']
    deployment_parameter_set['GroupName'] = group_name
    deployment_parameter_set['ThingArn'] = thing_arn
    deployment_parameter_set['CertificateArn'] = certArn
    deployment_parameter_sets.append(deployment_parameter_set)
    log.append(deployment_parameter_set)

    ZipFile('deploy_params.zip', 'w').writestr('deploy_params.json', json.dumps(deployment_parameter_sets))
    s3.upload_file('deploy_params.zip', bucket, 'deploy_params.zip')

except ClientError as e:
    if e.response['Error']['Code'] == 'ParameterNotFound':
        print("No deployment configured yet")
        log.append(e.response)
    else:
        print(e.response)
        log.append(e.response)

with open("reg_log.txt", "w") as log_file:
    log_file.write(str(log))