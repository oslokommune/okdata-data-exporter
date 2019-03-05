import json
import urllib

import boto3
from moto import mock_s3

import main

bucket = "ok-origo-dataplatform-dev"
base_key = "processed%2Fgreen%2Fboligpriser_historic-4owcY%2Fversion%3D1-zV86jpeY%2Fedition%3DEDITION-HAkZy%2F"


def setup():
    with mock_s3():
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=bucket)
        for number in range(0, 10):
            parsed_base_key = urllib.parse.unquote_plus(base_key)
            s3.put_object(Body="contents", Bucket=bucket, Key="{}{}.json".format(parsed_base_key, number))


@mock_s3
def test_lambda_handler_specific_object():
    setup()
    result = main.lambda_handler(base_event, context={})
    assert json.loads(result["body"])[0]["key"] == "processed/green/boligpriser_historic-4owcY/version=1-zV86jpeY/edition=EDITION-HAkZy/0.json"


@mock_s3
def test_lambda_handler_with_prefix():
    setup()
    result = main.lambda_handler(prefix_key_event, context={})
    assert json.loads(result["body"])[2]["key"] == "processed/green/boligpriser_historic-4owcY/version=1-zV86jpeY/edition=EDITION-HAkZy/2.json"
    assert json.loads(result["body"])[9]["key"] == "processed/green/boligpriser_historic-4owcY/version=1-zV86jpeY/edition=EDITION-HAkZy/9.json"


base_event = {
    "resource": "/{proxy+}",
    "path": "/path/to/resource",
    "httpMethod": "POST",
    "isBase64Encoded": True,
    "queryStringParameters": {"foo": "bar"},
    "pathParameters": {"key": "{}{}.json".format(base_key, "0")},
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
prefix_key_event["pathParameters"] = {"key": "{}".format(base_key)}
