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

deploy-pipeline:
	npx cdk deploy iot-gg-cicd-workshop-pipelines --require-approval never

initial-push:
	$(MAKE) -C . init
	source venv/bin/activate; \
	git add .; \
	git commit -a -m "added workshop source to repo"; \
	git push -u origin master; \

list: 
	npx cdk list

package:
	npx cdk synth greengrass-function-subscription -o dist

destroy-pipelines:
	npx cdk destroy iot-gg-cicd-workshop-pipelines -f

clean:	
	rm -rf dist || true
	rm -rf venv || true
	rm -rf node_modules || true
	rm -rf iot_greengrass/*.egg-info || true
	rm -rf cdk.out || true
	rm cdk.context.json || true

all: clean init deploy-pipeline