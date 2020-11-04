## Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
## SPDX-License-Identifier: MIT-0

from aws_cdk import (core, aws_codebuild as codebuild,
                     aws_codecommit as codecommit,
                     aws_codepipeline as codepipeline,
                     aws_codepipeline_actions as codepipeline_actions,
                     aws_iam as iam,
                     aws_s3 as s3,
                     aws_ssm as ssm,
                     aws_lambda as awslambda)

def add_policies(code_build: codebuild.PipelineProject, policy_names: [str]):
    for policy_name in policy_names:
        code_build.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(policy_name)
            )

class PipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        code = codecommit.Repository(
            self, "CodeRepo", repository_name="iot-gg-cicd-workshop-repo")

        prod_deploy_param_bucket = s3.Bucket(self, "ProdDeployBucket",
            versioned=True,
        )

        prod_source_bucket = s3.Bucket(self, "ProdSourceBucket",
            versioned=True,
        )

        ssm.StringParameter(
            self, 
            "ProdSourceBucketParameter", 
            parameter_name="/iot-gg-cicd-workshop/s3/prod_source_bucket", 
            string_value=prod_source_bucket.bucket_name,
        )
        ssm.StringParameter(
            self, 
            "ProdDeployBucketParameter", 
            parameter_name="/iot-gg-cicd-workshop/s3/prod_deploy_param_bucket", 
            string_value=prod_deploy_param_bucket.bucket_name,
        )
        
        cdk_build = codebuild.PipelineProject(
            self,
            "Build",
            project_name="iot-gg-cicd-workshop-build",
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            environment_variables={
                "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(value=kwargs['env'].region)
            })

        add_policies(
            cdk_build, 
            [
                "AWSCloudFormationFullAccess", 
                "AmazonSSMFullAccess",
                "AmazonS3FullAccess",
                "AWSLambdaFullAccess",
                "IAMFullAccess",
            ])
        
        cdk_deploy_canary = codebuild.PipelineProject(
            self,
            "Deploy",
            project_name="iot-gg-cicd-workshop-deploy-canary",
            build_spec=codebuild.BuildSpec.from_source_filename("deployspec.yml"),
            environment_variables={
                "AWS_DEFAULT_REGION": codebuild.BuildEnvironmentVariable(value=kwargs['env'].region)
            })

        add_policies(
            cdk_deploy_canary, 
            [
                "AWSCloudFormationFullAccess", 
                "AWSGreengrassFullAccess",
                "AmazonSSMFullAccess",
                "ResourceGroupsandTagEditorReadOnlyAccess",
                "AWSLambdaFullAccess",
                "AWSIoTFullAccess"
            ])


        source_output = codepipeline.Artifact()
        cdk_build_output = codepipeline.Artifact("CdkBuildOutput")

        codepipeline.Pipeline(self,
                              "Pipeline",
                              pipeline_name="iot-gg-cicd-workshop-pipeline-canary",
                              stages=[
                                  codepipeline.StageProps(stage_name="Source",
                                                          actions=[
                                                              codepipeline_actions.CodeCommitSourceAction(
                                                                  action_name="CodeCommit_Source",
                                                                  repository=code,
                                                                  output=source_output)]),
                                  codepipeline.StageProps(stage_name="Build_Package_Deploy_Lambda",
                                                          actions=[
                                                              codepipeline_actions.CodeBuildAction(
                                                                  action_name="Build_Package_Deploy",
                                                                  project=cdk_build,
                                                                  input=source_output,
                                                                  outputs=[cdk_build_output])]),
                                  codepipeline.StageProps(stage_name="Deploy_GreenGrass_Canary",
                                                          actions=[
                                                              codepipeline_actions.CodeBuildAction(
                                                                  action_name="Deploy_Canary",
                                                                  project=cdk_deploy_canary,
                                                                  input=cdk_build_output)]),
                              ]
                              )

        cdk_deploy_prod = codebuild.PipelineProject(
            self,
            "DeployProd",
            project_name="iot-gg-cicd-workshop-deploy-main",
            build_spec=codebuild.BuildSpec.from_object(dict(
                            version="0.2",
                            phases=dict(
                                install=dict(
                                    commands=[
                                        "apt-get install zip",
                                        "PROD_SOURCE_BUCKET=$(aws ssm get-parameter --name '/iot-gg-cicd-workshop/s3/prod_source_bucket' --with-decryption --query 'Parameter.Value' --output text)",
                                        "aws s3 cp s3://$PROD_SOURCE_BUCKET/prod_deploy.zip prod_deploy.zip",
                                        "unzip -o prod_deploy.zip",
                                        "ls -la",
                                        "make clean init"
                                    ]),
                                build=dict(
                                    commands=[
                                        "ls -la",
                                        "make deploy-greengrass-prod",
                                    ])),
                                artifacts={
                                "base-directory": ".",
                                "files": [
                                    "**/*"]},
                                environment=dict(buildImage=
                                codebuild.LinuxBuildImage.STANDARD_2_0))))

        add_policies(
            cdk_deploy_prod, 
            [
                "AWSCloudFormationFullAccess", 
                "AWSGreengrassFullAccess",
                "AmazonSSMFullAccess",
                "ResourceGroupsandTagEditorReadOnlyAccess",
                "AWSLambdaFullAccess"
            ])

        prod_source_output = codepipeline.Artifact()
        codepipeline.Pipeline(self,
                              "PipelineProd",
                              pipeline_name="iot-gg-cicd-workshop-pipeline-main",
                              stages=[
                                  codepipeline.StageProps(stage_name="Source",
                                                          actions=[
                                                              codepipeline_actions.S3SourceAction(
                                                                  action_name="S3_Source",
                                                                  bucket=prod_deploy_param_bucket,
                                                                  bucket_key="deploy_params.zip",
                                                                  output=prod_source_output)]),
                                  codepipeline.StageProps(stage_name="Deploy_GreenGrass_Prod",
                                                          actions=[
                                                              codepipeline_actions.CodeBuildAction(
                                                                  action_name="Deploy_Prod",
                                                                  project=cdk_deploy_prod,
                                                                  input=prod_source_output)]),
                              ]
                              )
        prod_source_bucket.grant_read_write(cdk_deploy_canary.role)
        prod_source_bucket.grant_read(cdk_deploy_prod.role)
        prod_deploy_param_bucket.grant_read_write(cdk_deploy_canary.role)
        

