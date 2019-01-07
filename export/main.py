import json
import boto3


def lambda_handler(event, context):
    # TODO: implement proper authz
    if event['requestContext']['authorizer']['principalId'] == "test-dataplatform":
        body = json.loads(event['body'])
        response = {
            "url": generate_signed_url(body['bucket'], body['key'])
        }
        return {
            "isBase64Encoded": False,
            'statusCode': 200,
            'body': json.dumps(response)
        }
    else:
        return {
            "isBase64Encoded": False,
            'statusCode': 403,
            'body': 'Forbidden: Only the test user can do this'
        }


def generate_signed_url(bucket, key):
    # Check authz: Can user (Authorization header)
    session = boto3.Session()
    s3 = session.client('s3')
    # Print out bucket names
    params = {
        'Bucket': bucket,
        'Key': key
    }

    return s3.generate_presigned_url('get_object', Params=params, ExpiresIn=60 * 5)
