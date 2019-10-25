import json
from unittest.mock import patch

import boto3
from moto import mock_s3

from exporter.errors import MetadataError, MetadataNotFound
from exporter.generate_signed_url import handler

bucket = "ok-origo-dataplatform-dev"
base_key = "raw/green/befolkingsframskrivninger/version=1/edition=20191003T073102/"

dataset_info = {
    "theme": "Befolkning og samfunn",
    "processing_stage": "raw",
    "frequency": None,
    "contactPoint": {
        "name": "Byrådsavdeling for finans",
        "email": "oslostatistikken@byr.oslo.kommune.no",
    },
    "Type": "Dataset",
    "publisher": "Byrådsavdeling for finans",
    "confidentiality": "green",
    "keywords": ["befolkning", "framskrivning", "prognose"],
    "objective": "Datasettet brukes som grunnlag for å generere innhold i Bydelsfakta.",
    "description": "Befolkingsframskrivninger Kilde: Statistisk Sentralbyrå",
    "Id": "befolkingsframskrivninger",
    "title": "Befolkingsframskrivninger",
    "accessRights": "public",
    "_links": {"self": {"href": "/datasets/befolkingsframskrivninger"}},
}

edition_info = {
    "startTime": "2019-01-01",
    "endTime": "2030-01-01",
    "edition": "2019-10-03T09:31:02+02:00",
    "Id": "befolkingsframskrivninger/1/20191003T073102",
    "description": "befolkningsframskrivninger",
    "Type": "Edition",
    "_links": {
        "self": {
            "href": "/datasets/befolkingsframskrivninger/versions/1/editions/20191003T073102"
        }
    },
}


def setup():
    with mock_s3():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=bucket)
        for number in range(0, 10):
            parsed_base_key = base_key
            s3.put_object(
                Body="contents", Bucket=bucket, Key=f"{parsed_base_key}{number}.json"
            )


@mock_s3
@patch("exporter.generate_signed_url.get_dataset", return_value=dataset_info)
@patch("exporter.generate_signed_url.get_edition", return_value=edition_info)
@patch("exporter.generate_signed_url.has_distributions", return_value=True)
def test_generate_signed_url_handler_specific_object(*args):
    setup()
    result = handler(base_event, context={})
    assert json.loads(result["body"])[0]["key"] == f"{base_key}0.json"


@mock_s3
@patch("exporter.generate_signed_url.get_dataset", return_value=dataset_info)
@patch("exporter.generate_signed_url.get_edition", return_value=edition_info)
@patch("exporter.generate_signed_url.has_distributions", return_value=True)
def test_generate_signed_url_handler_with_prefix(*args):
    setup()
    result = handler(prefix_key_event, context={})
    assert json.loads(result["body"])[2]["key"] == f"{base_key}2.json"
    assert json.loads(result["body"])[9]["key"] == f"{base_key}9.json"


@mock_s3
@patch(
    "exporter.generate_signed_url.get_dataset", return_value={"confidentiality": "red"}
)
@patch("exporter.generate_signed_url.get_edition", return_value=edition_info)
@patch("auth.SimpleAuth.is_owner", return_value=False)
@patch("exporter.generate_signed_url.has_distributions", return_value=True)
def test_generate_signed_url_with_red_confidentiality(*args):
    setup()
    result = handler(prefix_key_event, context={})
    assert result["statusCode"] == 403


@mock_s3
@patch("exporter.generate_signed_url.get_metadata", side_effect=MetadataNotFound)
@patch("exporter.generate_signed_url.get_edition", return_value=edition_info)
@patch("exporter.generate_signed_url.has_distributions", return_value=True)
def test_generate_signed_url_when_get_dataset_raise_not_found_error(*args):
    setup()
    result = handler(prefix_key_event, context={})
    assert result["statusCode"] == 404


@mock_s3
@patch("exporter.generate_signed_url.get_dataset", side_effect=MetadataError)
@patch("exporter.generate_signed_url.get_edition", return_value=edition_info)
@patch("exporter.generate_signed_url.has_distributions", return_value=True)
def test_generate_signed_url_when_get_dataset_raise_dataset_error(*args):
    setup()
    result = handler(prefix_key_event, context={})
    assert result["statusCode"] == 400


base_event = {
    "resource": "/{proxy+}",
    "path": "/path/to/resource",
    "httpMethod": "POST",
    "isBase64Encoded": True,
    "queryStringParameters": {"foo": "bar"},
    "pathParameters": {
        "dataset": "befolkingsframskrivninger",
        "version": "1",
        "edition": "20191003T073102",
    },
    "stageVariables": {"baz": "qux"},
    "headers": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "en-US,en;q=0.8",
        "Cache-Control": "max-age=0",
        "CloudFront-Forwarded-Proto": "https",
        "CloudFront-Is-Desktop-Viewer": "true",
        "CloudFront-Is-Mobile-Viewer": "false",
        "CloudFront-Is-SmartTV-Viewer": "false",
        "CloudFront-Is-Tablet-Viewer": "false",
        "CloudFront-Viewer-Country": "US",
        "Host": "1234567890.execute-api.eu-central-1.amazonaws.com",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Custom User Agent String",
        "Via": "1.1 08f323deadbeefa7af34d5feb414ce27.cloudfront.net (CloudFront)",
        "X-Amz-Cf-Id": "cDehVQoZnx43VYQb9j2-nvCh-9z396Uhbp027Y2JvkCPNLmGJHqlaA==",
        "X-Forwarded-For": "127.0.0.1, 127.0.0.2",
        "X-Forwarded-Port": "443",
        "X-Forwarded-Proto": "https",
        "Authorization": "token",
    },
    "requestContext": {
        "accountId": "123456789012",
        "authorizer": {"principalId": "test-dataplatform"},
        "resourceId": "123456",
        "stage": "prod",
        "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
        "requestTime": "09/Apr/2015:12:34:56 +0000",
        "requestTimeEpoch": 1428582896000,
        "identity": {
            "cognitoIdentityPoolId": None,
            "accountId": None,
            "cognitoIdentityId": None,
            "caller": None,
            "accessKey": None,
            "sourceIp": "127.0.0.1",
            "cognitoAuthenticationType": None,
            "cognitoAuthenticationProvider": None,
            "userArn": None,
            "userAgent": "Custom User Agent String",
            "user": None,
        },
        "path": "/prod/path/to/resource",
        "resourcePath": "/{proxy+}",
        "httpMethod": "POST",
        "apiId": "1234567890",
        "protocol": "HTTP/1.1",
    },
}

prefix_key_event = base_event.copy()
