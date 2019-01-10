.PHONY: deploy
deploy: test
	serverless deploy
	serverless downloadDocumentation --outputFileName=openapi.yaml

.PHONY: print
print:
	serverless print

.PHONY: clean_openapi
clean_openapi:
	rm -f openapi.yaml

.PHONY: test
test:
	python3 -m unittest -v export/test_*