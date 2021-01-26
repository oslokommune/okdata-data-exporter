import json
import os

import boto3
import requests
from okdata.aws.logging import log_add, log_exception

AUTHORIZER_API = os.environ["AUTHORIZER_API"]
METADATA_API_URL = os.environ["METADATA_API_URL"]

CONFIDENTIALITY_MAP = {
    "public": "green",
    "restricted": "yellow",
    "non-public": "red",
}


def error_response(status, message):
    return {
        "isBase64Encoded": False,
        "statusCode": status,
        "body": json.dumps({"message": message}),
    }


def response(code, body):
    return {
        "statusCode": code,
        "body": body,
        "headers": {"Access-Control-Allow-Origin": "*"},
    }


class APIClient:
    def __init__(self, access_token=None):
        self.access_token = access_token

    @classmethod
    def with_access_token_from_event(cls, event):
        try:
            auth_type, access_token = event["headers"]["Authorization"].split(" ")
            if auth_type.lower() == "bearer":
                return cls(access_token)
            raise ValueError(f'Expected auth type "Bearer", got "{auth_type}"')
        except ValueError as e:
            log_exception(e)
        return None

    def _get(self, url, **kwargs):
        if self.access_token:
            kwargs["headers"] = {"Authorization": f"Bearer {self.access_token}"}

        return requests.get(url, **kwargs)

    def _get_metadata(self, url):
        response = self._get(url)
        if response.status_code != 200:
            log_add(metadata_error_code=response.status_code, metadata_url=url)
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
        return data.get("access", False)


def generate_signed_urls(bucket, dataset, edition):
    access_rights = dataset["accessRights"]
    dataset_id, version, edition_id = edition["Id"].split("/")
    confidentiality = CONFIDENTIALITY_MAP[access_rights]
    common_prefix = f"processed/{confidentiality}/"
    parent_id = dataset.get("parent_id")

    dataset_prefix = f"{dataset_id}/version={version}/edition={edition_id}/"
    if parent_id:
        dataset_prefix = f"{parent_id}/{dataset_prefix}"

    prefix = common_prefix + dataset_prefix

    log_add(
        dataset_access_rights=access_rights,
        s3_bucket=bucket,
        s3_prefix=prefix,
    )

    session = boto3.Session()
    s3 = session.client("s3")
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
