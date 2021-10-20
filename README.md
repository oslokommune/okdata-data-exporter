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

Deploy to both dev and prod is automatic via GitHub Actions on push to
`main`. You can alternatively deploy from local machine (requires `saml2aws`)
with: `make deploy` or `make deploy-prod`.

## Code fromatting

Format code with

```
$ make format
```
