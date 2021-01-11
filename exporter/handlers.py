import json
import os


import requests
from aws_xray_sdk.core import patch_all, xray_recorder
from okdata.aws.logging import log_add, log_exception, logging_wrapper

from exporter.common import (
    APIClient,
    error_response,
    generate_signed_urls,
    response,
)

BUCKET = os.environ["BUCKET"]
ENABLE_AUTH = os.environ.get("ENABLE_AUTH", "false") == "true"

patch_all()


def _dataset_components_from_event(event):
    pp = event["pathParameters"]
    dataset_id, version_id, edition_id = pp["dataset"], pp["version"], pp["edition"]
    log_add(dataset_id=dataset_id, version_id=version_id, edition_id=edition_id)
    return dataset_id, version_id, edition_id


@logging_wrapper
@xray_recorder.capture("generate_signed_url")
def generate_signed_url(event, context):
    dataset_id, version_id, edition_id = _dataset_components_from_event(event)
    client = APIClient.with_access_token_from_event(event)

    if not client:
        return error_response(403, "Forbidden")

    try:
        dataset = client.get_dataset(dataset_id)
        edition = client.get_edition(dataset_id, version_id, edition_id)
        log_add(dataset=dataset)
    except requests.HTTPError as e:
        log_exception(e)
        return error_response(e.response.status_code, e.response.json())
    except Exception as e:
        log_exception(e)
        return error_response(500, "Could not complete request, please try again later")

    if not client.has_distributions(edition):
        return error_response(404, f"Missing data for {edition['Id']}")

    # Only owner can download non-public datasets.
    if (
        dataset["accessRights"] != "public"
        and ENABLE_AUTH
        and not client.is_dataset_owner(dataset_id)
    ):
        log_add(is_owner=False)
        return error_response(403, "Forbidden")

    signed_urls = generate_signed_urls(BUCKET, edition=edition, dataset=dataset)
    return response(200, json.dumps(signed_urls))


@logging_wrapper
@xray_recorder.capture("generate_signed_url_public")
def generate_signed_url_public(event, context):
    dataset_id, version_id, edition_id = _dataset_components_from_event(event)
    client = APIClient()

    try:
        dataset = client.get_dataset(dataset_id)
        edition = client.get_edition(dataset_id, version_id, edition_id)
        log_add(dataset=dataset)
    except requests.HTTPError as e:
        log_exception(e)
        return error_response(e.response.status_code, e.response.json())
    except Exception as e:
        log_exception(e)
        return error_response(500, "Could not complete request, please try again later")

    if not client.has_distributions(edition):
        return error_response(404, f"Missing data for {edition['Id']}")

    if dataset["accessRights"] != "public":
        return error_response(403, "Forbidden")

    signed_urls = generate_signed_urls(BUCKET, edition=edition, dataset=dataset)
    return response(200, json.dumps(signed_urls))
