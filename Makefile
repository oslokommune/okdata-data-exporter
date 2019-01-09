.PHONY: deploy
deploy: test clean_openapi openapi.yml
	serverless deploy

.PHONY: print
print:
	serverless print

openapi.yml:
	serverless openapi generate

.PHONY: clean_openapi
clean_openapi:
	rm -f openapi.yml

.PHONY: test
test:
	python3 -m unittest -v export/test_*