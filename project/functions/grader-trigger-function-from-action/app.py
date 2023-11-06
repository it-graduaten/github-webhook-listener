import json
import os
import boto3

from src.payload_helper import get_changed_files

sqs = boto3.client('sqs')
QUEUE_URL = os.environ.get("GRADER_DELIVERY_QUEUE_URL")


def lambda_handler(event, context):
    try:
        config = validate_request(event)
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": f"Error: {e}",
            }),
        }
    event_body = json.loads(event['body'])

    # Create grading request body
    grading_request_body = {
        "canvas_course_id": config['canvas_course_id'],
        "github_classroom_id": config['github_classroom_id'],
        "solution_repo_full_name": config['solution_repo_full_name'],
        "application_type": config['application_type'],
        "student_repo_full_name": event_body['repository'],
        "student_github_id": event_body['sender_id'],
        "push_timestamp": event_body['push_timestamp'],
        "changed_files": event_body['changed_files']
    }

    # Trigger message on GradingQueue with GradingRequest
    message_id = create_grading_request(grading_request_body)

    # Finish this one
    return {
        "statusCode": 200,
        "body": json.dumps({
            "status": "success",
            "message": "Grading request created",
            "message_id": message_id
            # "location": ip.text.replace("\n", "")
        }),
    }


def validate_request(request):
    """
    Validate the request body
    """
    # Check if the request has path parameters
    if 'pathParameters' not in request:
        raise Exception("No path parameters found in request body, aborting")
    path_params = request['pathParameters']
    # Check if the path parameters contain an id
    if 'id' not in path_params:
        raise Exception("No id found in path parameters, aborting")
    path_id = path_params['id']
    # Check if the id can be found in the config file, and thus matches a valid Github classroom assignment'
    # TODO: Read this JSON from actual s3 storage
    config = json.load(open(os.path.join("s3-mock", "config.json")))
    if path_id not in config:
        raise Exception("No config found for id: {}, aborting".format(path_id))
    return config[path_id]


def create_grading_request(request_body):
    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(request_body)
    )
    return response['MessageId']
