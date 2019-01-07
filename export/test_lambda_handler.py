from unittest import TestCase
from export import main
import json


class TestLambda_handler(TestCase):
    def test_lambda_handler_with_correct_user(self):
        result = main.lambda_handler(testEvent, context={})
        assert json.loads(result['body'])['url']

    def test_lambda_handler_with_wrong_user(self):
        testEvent['requestContext']['authorizer']['principalId'] = 'test-dataplatform-2'
        result = main.lambda_handler(testEvent, context={})
        assert str.startswith(result['body'], "Forbidden")





testEvent = {
  "body": '{"bucket":"ok-origo-dataplatform-testbucket","key":"data/dummy_data_uploaded.txt"}',
  "resource": "/{proxy+}",
  "path": "/path/to/resource",
  "httpMethod": "POST",
  "isBase64Encoded": True,
  "queryStringParameters": {
    "foo": "bar"
  },
  "pathParameters": {
    "proxy": "/path/to/resource"
  },
  "stageVariables": {
    "baz": "qux"
  },
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
    "X-Forwarded-Proto": "https"
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
      "user": None
    },
    "path": "/prod/path/to/resource",
    "resourcePath": "/{proxy+}",
    "httpMethod": "POST",
    "apiId": "1234567890",
    "protocol": "HTTP/1.1"
  }
}