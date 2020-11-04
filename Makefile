destroy-pipelines:
	$(MAKE) -C provision/project destroy-pipelines

destroy-greengrass:
	$(MAKE) -C provision/greengrass destroy-greengrass

destroy-deployments:
	$(MAKE) -C provision/project destroy-deployments
	
provision-pipelines:
	$(MAKE) -C provision/project provision-pipelines

provision-workspace:
	$(MAKE) -C provision/project provision-workspace

provision-greengrass:
	$(MAKE) -C provision/greengrass provision-greengrass

provision-all: provision-greengrass provision-workspace 
