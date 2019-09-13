import json


def error_response(status, message):
    return {
        "isBase64Encoded": False,
        "statusCode": status,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"message": message}),
    }
