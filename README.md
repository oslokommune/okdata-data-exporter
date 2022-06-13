# Data exporter

REST API to generate a list of presigned S3 URLs for downloading a dataset distribution.

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
`main`. You can alternatively deploy from local machine with: `make deploy` or
`make deploy-prod`.

## Code fromatting

Format code with

```
$ make format
```
