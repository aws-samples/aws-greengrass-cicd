export CDK_DEFAULT_ACCOUNT = $(shell aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_REGION = $(shell aws configure get region)
export WORKSPACE_PATH = ../../workspace
export REPO_NAME = iot-gg-cicd-workshop-repo
SHELL := /bin/bash

init: 
	@echo Deploy Account is $(CDK_DEFAULT_ACCOUNT)
	@echo Deploy Region is $(CDK_DEFAULT_REGION)
	npm install cdk@1.59.0 -y
	python3 -m venv venv/
	venv/bin/python3 --version
	venv/bin/pip install git-remote-codecommit
	venv/bin/pip install -r requirements.txt

deploy-pipelines:
	$(MAKE) -C pipelines all

destroy-pipelines:
	$(MAKE) -C pipelines destroy-pipelines

setup-workspace:
	rm -rf $(WORKSPACE_PATH); \
	source venv/bin/activate; \
	which python3; \
	git clone codecommit::$(CDK_DEFAULT_REGION)://$(REPO_NAME) $(WORKSPACE_PATH)/$(REPO_NAME); \
	cd code; \
	cp -r . ../$(WORKSPACE_PATH)/$(REPO_NAME); \
	cd ..; \
	$(MAKE) -C $(WORKSPACE_PATH)/$(REPO_NAME) init; \

destroy-deployments:
	$(MAKE) -C $(WORKSPACE_PATH)/$(REPO_NAME) destroy-deployments
	
clean:	
	rm -rf venv || true
	rm -rf node_modules || true
	rm -rf cdk.out || true
	rm cdk.context.json || true

provision-all: clean init deploy-pipelines setup-workspace

provision-pipelines: init deploy-pipelines

provision-workspace: init setup-workspace