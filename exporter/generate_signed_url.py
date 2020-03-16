import json
import os
import boto3

from aws_xray_sdk.core import patch_all, xray_recorder
from dataplatform.awslambda.logging import (
    logging_wrapper,
    log_add,
    log_exception,
)

from auth import SimpleAuth
from exporter.errors import (
    MetadataNotFound,
    DatasetNotFound,
    EditionNotFound,
)
from exporter.common import error_response, response

BUCKET = os.environ["BUCKET"]
METADATA_API = os.environ.get("METADATA_API")
ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false") == "true"

patch_all()


@logging_wrapper("data-exporter")
@xray_recorder.capture("generate_signed_url")
def handler(event, context):
    params = event["pathParameters"]
    dataset = params["dataset"]
    log_add(dataset_id=dataset)
    version = params["version"]
    log_add(dataset_version=version)
    edition = params["edition"]
    log_add(dataset_edition=edition)

    try:
        dataset_info = get_dataset(event, dataset)
        edition_info = get_edition(event, dataset, version, edition)

        log_add(dataset_info=dataset_info)
    except DatasetNotFound as e:
        log_exception(e)
        return error_response(404, "Could not find dataset")
    except EditionNotFound as e:
        log_exception(e)
        return error_response(404, "Could not find version/edition")
    except Exception as e:
        log_exception(e)
        return error_response(400, "Could not complete request, please try again later")

    if not has_distributions(event, edition_info):
        return response(404, f"Missing data for {edition_info['Id']}")

    # Anyone with a logged in user can download green datasets
    if dataset_info["confidentiality"] == "green":
        signed_url = generate_signed_url(
            BUCKET, edition=edition_info, dataset=dataset_info
        )
        return response(200, json.dumps(signed_url))

    # Only owner can download non-green datasets
    if ENABLE_AUTH and not SimpleAuth().is_owner(event, dataset):
        log_add(is_owner=False)
        return error_response(403, "Forbidden")

    signed_url = generate_signed_url(BUCKET, edition=edition_info, dataset=dataset_info)
    return response(200, json.dumps(signed_url))


def has_distributions(event, edition):
    url = f"{METADATA_API}{edition['_links']['self']['href']}/distributions"
    distributions = get_metadata(event, "distributions", url)
    return bool(distributions)


def get_edition(event, dataset, version, edition):
    url = f"{METADATA_API}/datasets/{dataset}/versions/{version}/editions/{edition}"
    try:
        return get_metadata(event, "edition", url)
    except MetadataNotFound:
        raise EditionNotFound


def get_dataset(event, dataset):
    url = f"{METADATA_API}/datasets/{dataset}"
    try:
        return get_metadata(event, "dataset", url)
    except MetadataNotFound:
        raise DatasetNotFound


def get_metadata(event, type, url):
    access_token = event["headers"]["Authorization"].split(" ")[-1]
    req = SimpleAuth().poor_mans_delegation(access_token)
    response = req.get(url)
    if response.status_code == 404:
        raise MetadataNotFound(f"Could not find {type}")
    if response.status_code != 200:
        response.raise_for_status()
    data = response.json()
    return data


def generate_signed_url(bucket, dataset, edition):
    confidentiality = dataset["confidentiality"]
    log_add(dataset_confidentiality=confidentiality)
    (dataset_id, version, edition_id) = edition["Id"].split("/")
    common_prefix = f"processed/{confidentiality}/"
    dataset_prefix = f"{dataset_id}/version={version}/edition={edition_id}/"

    if "parent_id" in dataset and dataset["parent_id"]:
        parent_id = dataset["parent_id"]
        dataset_prefix = f"{parent_id}/{dataset_prefix}"

    prefix = common_prefix + dataset_prefix

    session = boto3.Session()
    s3 = session.client("s3")
    log_add(s3_bucket=bucket)
    log_add(s3_prefix=prefix)
    resp = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

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
