.PHONY: init
init:
	python3 -m pip install tox black pip-tools
	pip-compile

.PHONY: format
format: init
	python3 -m black main.py test_lambda_handler.py setup.py --line-length 160

.PHONY: deploy
deploy: format test
	sls deploy

.PHONY: deploy-prod
deploy-prod: format test
	sls deploy --stage prod && \
	sls --stage prod downloadDocumentation --outputFileName swagger.yaml

.PHONY: test
test:
	python3 -m tox -p auto