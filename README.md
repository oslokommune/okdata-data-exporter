# Data exporter

Get a list of presigned S3 URLs from a dataset ID

## Setup

1. [Install Serverless Framework](https://serverless.com/framework/docs/getting-started/)
2. Install dependencies
```
make init
```

## Running tests

Tests are run using [tox](https://pypi.org/project/tox/).

```
$ make test
```

## Deploy

Deploy to dev is automatic via GitHub Actions, while deploy to prod can be triggered with GitHub Actions via dispatch. You can alternatively deploy from local machine (requires `saml2aws`) with: `make deploy` or `make deploy-prod`.

## Code fromatting

Format code with

```
$ make format
```
