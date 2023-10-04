import sys
import json

def handler(event, context):
    print(event)
    for record in event['Records']:
        print(f'working on message with ID: {record["messageId"]}')
        body = json.loads(record['body'])
        print(body)
        
        # PUll required files based on the input gained from the record
        # Run tests
        # publish results to canvas
        # Clean up
        
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": 'Hello from AWS Lambda using Python' + sys.version + '!',
        }),
    }