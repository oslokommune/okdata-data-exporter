import json
import os
import boto3
import requests

from aws_xray_sdk.core import patch_all, xray_recorder
from dataplatform.awslambda.logging import (
    logging_wrapper,
    log_add,
    log_exception,
)

from requests import HTTPError

from exporter.common import error_response, response

BUCKET = os.environ["BUCKET"]
METADATA_API_URL = os.environ.get("METADATA_API_URL")
ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false") == "true"
AUTHORIZER_API = os.environ["AUTHORIZER_API"]

patch_all()


@logging_wrapper
@xray_recorder.capture("generate_signed_url")
def handler(event, context):
    params = event["pathParameters"]
    dataset = params["dataset"]
    log_add(dataset_id=dataset)
    version = params["version"]
    log_add(dataset_version=version)
    edition = params["edition"]
    log_add(dataset_edition=edition)

    auth_requests = AuthorizedRequests.from_event(event)
    if not auth_requests:
        return error_response(403, "Forbidden")

    try:
        dataset_info = auth_requests.get_dataset(dataset)
        edition_info = auth_requests.get_edition(dataset, version, edition)

        log_add(dataset_info=dataset_info)
    except HTTPError as e:
        log_exception(e)
        return error_response(e.response.status_code, e.response.json())
    except Exception as e:
        log_exception(e)
        return error_response(500, "Could not complete request, please try again later")

    if not auth_requests.has_distributions(edition_info):
        return error_response(404, f"Missing data for {edition_info['Id']}")

    # Anyone with a logged in user can download green datasets
    if dataset_info["confidentiality"] == "green":
        signed_url = generate_signed_url(
            BUCKET, edition=edition_info, dataset=dataset_info
        )
        return response(200, json.dumps(signed_url))

    # Only owner can download non-green datasets
    if ENABLE_AUTH and not auth_requests.is_dataset_owner(dataset):
        log_add(is_owner=False)
        return error_response(403, "Forbidden")

    signed_url = generate_signed_url(BUCKET, edition=edition_info, dataset=dataset_info)
    return response(200, json.dumps(signed_url))


class AuthorizedRequests:
    def __init__(self, access_token):
        self.access_token = access_token

    @classmethod
    def from_event(cls, event):
        try:
            auth_type, access_token = event["headers"]["Authorization"].split(" ")
            if auth_type.lower() == "bearer":
                return cls(access_token)
            raise ValueError(f'Expected auth type "Bearer", got "{auth_type}"')
        except ValueError as e:
            log_exception(e)
        return None

    def _get(self, url):
        return requests.get(
            url, headers={"Authorization": f"Bearer {self.access_token}"}
        )

    def _get_metadata(self, url):
        response = self._get(url)
        if response.status_code != 200:
            log_add(metadata_error_code=response.status_code)
            log_add(metadata_url=url)
            response.raise_for_status()
        data = response.json()
        return data

    def has_distributions(self, edition):
        url = f"{edition['_links']['self']['href']}/distributions"
        distributions = self._get_metadata(url)
        return bool(distributions)

    def get_edition(self, dataset, version, edition):
        url = f"{METADATA_API_URL}/datasets/{dataset}/versions/{version}/editions/{edition}"
        return self._get_metadata(url)

    def get_dataset(self, dataset):
        url = f"{METADATA_API_URL}/datasets/{dataset}"
        return self._get_metadata(url)

    def is_dataset_owner(self, dataset_id):
        result = self._get(
            f"{AUTHORIZER_API}/{dataset_id}",
        )
        result.raise_for_status()
        data = result.json()
        return "access" in data and data["access"]


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
