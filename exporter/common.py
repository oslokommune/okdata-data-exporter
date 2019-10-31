import json


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