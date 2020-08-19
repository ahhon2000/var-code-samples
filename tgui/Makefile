.PHONY: nothing deploy_debug deploy_integration deploy_production deploy_all

nothing:
	echo "made nothing"

deploy_debug:
	./.deploy_debug.sh

deploy_production:
	./.deploy_production.sh

deploy_integration:
	./.deploy_integration.sh

deploy_all: deploy_debug deploy_production deploy_integration
