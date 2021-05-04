import json
import os
import re
from copy import deepcopy

import pytest
import responses
import requests
from aws_xray_sdk.core import xray_recorder
import boto3
from moto import mock_s3

from exporter.common import APIClient
from exporter.handlers import generate_signed_url, generate_signed_url_public

xray_recorder.begin_segment("Test")
metadata_api = re.compile(os.environ["METADATA_API_URL"] + "/.*")
bucket = "ok-origo-dataplatform-dev"
base_key = (
    "processed/green/befolkingsframskrivninger/version=1/edition=20191003T073102/"
)

dataset_info = {
    "theme": "Befolkning og samfunn",
    "frequency": None,
    "contactPoint": {
        "name": "Byrådsavdeling for finans",
        "email": "oslostatistikken@byr.oslo.kommune.no",
    },
    "Type": "Dataset",
    "publisher": "Byrådsavdeling for finans",
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
            "href": f"{os.environ['METADATA_API_URL']}/metadata/datasets/befolkingsframskrivninger/versions/1/editions/20191003T073102"
        }
    },
}


@pytest.fixture(autouse=True)
def mock_aws():
    with mock_s3():
        s3 = boto3.client("s3")
        s3.create_bucket(
            Bucket=bucket,
            CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
        )
        for number in range(0, 10):
            parsed_base_key = base_key
            s3.put_object(
                Body="contents", Bucket=bucket, Key=f"{parsed_base_key}{number}.json"
            )
        yield s3


@pytest.fixture
def mock_gets(mocker):
    mocker.patch(
        "exporter.common.APIClient.get_dataset",
        return_value=dataset_info,
    )
    mocker.patch(
        "exporter.common.APIClient.get_edition",
        return_value=edition_info,
    )
    mocker.patch(
        "exporter.common.APIClient.has_distributions",
        return_value=True,
    )


def test_generate_signed_url_handler_specific_object(mock_gets):
    result = generate_signed_url(base_event, context={})
    assert json.loads(result["body"])[0]["key"] == f"{base_key}0.json"


def test_generate_signed_url_handler_with_prefix(mock_gets):
    result = generate_signed_url(prefix_key_event, context={})
    assert json.loads(result["body"])[2]["key"] == f"{base_key}2.json"
    assert json.loads(result["body"])[9]["key"] == f"{base_key}9.json"


def test_generate_signed_url_with_non_public_access_rights(mocker):
    mocker.patch(
        "exporter.common.APIClient.get_dataset",
        return_value={"accessRights": "non-public"},
    )
    mocker.patch(
        "exporter.common.APIClient.get_edition",
        return_value=edition_info,
    )
    mocker.patch(
        "exporter.common.APIClient.has_distributions",
        return_value=True,
    )
    resource_auth_mock = mocker.patch(
        "okdata.resource_auth.ResourceAuthorizer.has_access",
        return_value=False,
    )

    result = generate_signed_url(prefix_key_event, context={})
    resource_auth_mock.assert_called_once_with(
        "blippblopp",
        scope="okdata:dataset:read",
        resource_name="okdata:dataset:befolkingsframskrivninger",
    )
    assert result["statusCode"] == 403


@responses.activate
def test_generate_signed_url_when_get_dataset_metadata_404_error():
    responses.add(
        responses.GET,
        metadata_api,
        json={"error": "not found"},
        status=404,
        content_type="application/json",
    )
    result = generate_signed_url(prefix_key_event, context={})
    assert result["statusCode"] == 404
    assert json.loads(result["body"])["message"] == {"error": "not found"}


@responses.activate
def test_generate_signed_url_when_get_dataset_metadata_500_error():
    responses.add(
        responses.GET,
        metadata_api,
        json={"error": "internal error"},
        status=500,
        content_type="application/json",
    )

    result = generate_signed_url(prefix_key_event, context={})
    assert result["statusCode"] == 500
    assert json.loads(result["body"])["message"] == {"error": "internal error"}


def test_generate_signed_url_public_with_public_dataset(mock_gets):
    event = deepcopy(base_event)
    # No need to authorize for the public endpoint
    del event["headers"]["Authorization"]
    result = generate_signed_url_public(event, context={})
    assert result["statusCode"] == 200
    assert json.loads(result["body"])[0]["key"] == f"{base_key}0.json"


@pytest.mark.parametrize("access_rights", ["restricted", "non-public"])
def test_generate_signed_url_public_with_non_public_dataset(
    mocker, mock_gets, access_rights
):
    mocker.patch(
        "exporter.common.APIClient.get_dataset",
        return_value={"accessRights": access_rights},
    )
    event = deepcopy(base_event)
    del event["headers"]["Authorization"]
    result = generate_signed_url_public(event, context={})
    assert result["statusCode"] == 403


def test_authorization_header(mocker):
    mocker.patch("requests.get")
    client = APIClient("foobar")
    client._get("https://example.com")
    requests.get.assert_called_once_with(
        "https://example.com", headers={"Authorization": "Bearer foobar"}
    )


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
        "Authorization": "Bearer blippblopp",
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
