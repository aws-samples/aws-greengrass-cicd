export CDK_DEFAULT_ACCOUNT = $(shell aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION ?= $(shell aws configure get region)
export PARAMETER_FILE = deploy_params.json
export GROUP_CONFIG_FILE = gg_group_config.json
SHELL := /bin/bash

init: 
	@echo Deploy Account is $(CDK_DEFAULT_ACCOUNT)
	@echo Deploy Region is $(CDK_DEFAULT_REGION)
	npm install cdk@1.59.0 -y
	python3 -m venv venv/
	venv/bin/python3 --version
	venv/bin/pip install -r requirements.txt

initial-push:
	$(MAKE) -C . init
	source venv/bin/activate; \
	git add .; \
	git commit -a -m "added workshop source to repo"; \
	git push -u origin master; \

list: 
	@echo Deploy Account is $(CDK_DEFAULT_ACCOUNT)
	@echo Deploy Region is $(CDK_DEFAULT_REGION)
	npx cdk list

deploy-function:
	npx cdk deploy iot-gg-cicd-workshop-function  --require-approval never

deploy-prod-alias:
	npx cdk deploy iot-gg-cicd-workshop-function-prod-alias  --require-approval never

deploy-greengrass-canary:
	venv/bin/python3 lib/deployment_targets.py canary
	npx cdk deploy iot-gg-cicd-workshop-core-group-definition-versions-canary --require-approval never --parameters lambdaFunctionArn=$(shell aws ssm get-parameter --name "/iot-gg-cicd-workshop/function/canary_version_arn" --with-decryption --query 'Parameter.Value' --output text)
	cp $(GROUP_CONFIG_FILE) $(PARAMETER_FILE) 
	venv/bin/python3 lib/deploy.py

prepare-greengrass-prod:
	venv/bin/python3 lib/deployment_targets.py main
	cp $(GROUP_CONFIG_FILE) $(PARAMETER_FILE) 

deploy-greengrass-prod:
	venv/bin/python3 lib/deployment_targets.py main
	npx cdk deploy iot-gg-cicd-workshop-core-group-definition-versions-main --require-approval never --parameters lambdaFunctionArn=$(shell aws ssm get-parameter --name "/iot-gg-cicd-workshop/function/prod_version_arn" --with-decryption --query 'Parameter.Value' --output text)
	venv/bin/python3 lib/deploy.py

run-test:
	cd test; \
	../venv/bin/python3 -m unittest test.py

destroy-deployments:
	npx cdk destroy iot-gg-cicd-workshop-core-group-definition-versions-canary -f
	npx cdk destroy iot-gg-cicd-workshop-core-group-definition-versions-main -f
	npx cdk destroy iot-gg-cicd-workshop-function-prod-alias -f
	npx cdk destroy iot-gg-cicd-workshop-function  -f

clean:	
	rm -rf dist || true
	rm -rf out || true
	rm -rf venv || true
	rm -rf node_modules || true
	rm -rf lib/*.egg-info || true
	rm -rf cdk.out || true
	rm cdk.context.json || true

all: clean init deploy-cicd-pipeline setup-workspace