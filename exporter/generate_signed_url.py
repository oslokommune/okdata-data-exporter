import json
import os
import urllib
import logging
import boto3

from auth import SimpleAuth
from exporter.errors import DatasetError, DatasetNotFoundError
from exporter.common import error_response

log = logging.getLogger()
log.setLevel(logging.INFO)

BUCKET = os.environ["BUCKET"]
METADATA_API = os.environ.get("METADATA_API")
ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false") == "true"


def handler(event, context):
    params = event["pathParameters"]
    dataset = urllib.parse.unquote_plus(params["key"])
    log.info(f"generating signed URL for dataset: {dataset}")

    try:
        datasetInfo = get_dataset(event, dataset)
        log.info(f"datasetInfo: {datasetInfo}")
    except DatasetNotFoundError:
        log.exception(f"Cannot find dataset: {dataset}")
        return error_response(404, "Could not find dataset")
    except Exception as e:
        log.exception(f"Unexpected Exception found: {e}")
        return error_response(400, "Could not complete request, please try again later")

    # Anyone with a logged in user can download green datasets
    if datasetInfo["confidentiality"] == "green":
        return {
            "statusCode": 200,
            "body": json.dumps(generate_signed_url(BUCKET, dataset)),
        }

    # Only owner can download non-green datasets
    if ENABLE_AUTH and not SimpleAuth().is_owner(event, dataset):
        log.info(f"Access denied to datasert: {dataset}")
        return error_response(403, "Forbidden")

    return {"statusCode": 200, "body": json.dumps(generate_signed_url(BUCKET, dataset))}


def get_dataset(event, dataset):
    url = f"{METADATA_API}/datasets/{dataset}"
    req = SimpleAuth().poor_mans_delegation(event)
    response = req.get(url)

    if response.status_code == 404:
        raise DatasetNotFoundError(f"Could not find dataset: {dataset}")
    if response.status_code != 200:
        raise DatasetError()
    data = response.json()
    return data


def generate_signed_url(bucket, dataset_id):
    # Check authz: Can user (Authorization header)
    session = boto3.Session()
    s3 = session.client("s3")

    resp = s3.list_objects_v2(Bucket=bucket, Prefix=dataset_id)

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
