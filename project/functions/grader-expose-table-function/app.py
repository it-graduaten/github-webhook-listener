import datetime
import json
import os
import boto3

dynamodb = boto3.client('dynamodb')

TABLE_NAME = os.environ.get("GRADER_REQUEST_TABLE_NAME")

RECORD_DICT = {}

LAST_QUERIED_TIMESTAMP = 0


def lambda_handler(event, context):
    try:
        # Query all records where 'UpdatedAtTimestamp' is greater than LAST_QUERIED_TIMESTAMP
        response = dynamodb.query(
            TableName=TABLE_NAME,
            KeyConditionExpression='UpdatedAtTimestamp > :last_changed_timestamp',
            ExpressionAttributeValues={
                ':last_changed_timestamp': {
                    'N': str(LAST_QUERIED_TIMESTAMP)
                }
            }
        )
        # Finish this one
        return {
            "statusCode": 200,
            "body": json.dumps({
                "status": "success",
                "message": "Message received",
                "items": response['Items']
            }),
        }
    except Exception as e:
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": "error",
                "error": f"error: {e}"
            }),
        }
