import json
import os
import urllib

import boto3

S3_BUCKET = "ok-origo-dataplatform-{}".format(os.environ["STAGE"])


def lambda_handler(event, context):
    params = event["pathParameters"]
    requested_key = urllib.parse.unquote_plus(params["key"])
    return {
        "statusCode": 200,
        "body": json.dumps(generate_signed_url(S3_BUCKET, requested_key)),
    }


def generate_signed_url(bucket, key):
    # Check authz: Can user (Authorization header)
    session = boto3.Session()
    s3 = session.client("s3")

    resp = s3.list_objects_v2(Bucket=bucket, Prefix=key)

    signed_urls = [
        {
            "key": obj["Key"],
            "url": s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": obj["Key"]},
                ExpiresIn=60 * 5,
            ),
        }
        for obj in resp["Contents"]
    ]

    return signed_urls
