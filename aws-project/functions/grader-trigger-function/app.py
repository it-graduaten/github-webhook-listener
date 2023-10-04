import json


def lambda_handler(event, context):
    # Validate request
    
    # Create Grading request aka. all the necessary information from the request (Webhook) + additional config
    # Trigger message on GradingQueue with GradingRequest

    # Finish this one

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }
