export CDK_DEFAULT_ACCOUNT = $(shell aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION = $(shell aws configure get region)
SHELL := /bin/bash

init: 
	@echo Deploy Account is $(CDK_DEFAULT_ACCOUNT)
	@echo Deploy Region is $(CDK_DEFAULT_REGION)
	npm install cdk@1.59.0 -y
	python3 -m venv venv/
	venv/bin/python3 --version
	venv/bin/pip install git-remote-codecommit
	venv/bin/pip install -r requirements.txt
	npx cdk bootstrap aws://$(CDK_DEFAULT_ACCOUNT)/$(CDK_DEFAULT_REGION)

list: 
	npx cdk list

deploy-greengrass-infrastructure:
	npx cdk deploy iot-gg-cicd-workshop-iot-greengrass --require-approval never

destroy-greengrass:
	venv/bin/python3 lib/clean_up.py
	npx cdk destroy iot-gg-cicd-workshop-iot-greengrass -f


provision-greengrass: init deploy-greengrass-infrastructure