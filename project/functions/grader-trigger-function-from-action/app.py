import json
import os
import boto3

sqs = boto3.client('sqs')
ssm = boto3.client('ssm')

CONFIG_DICT = {}

QUEUE_URL = os.environ.get("GRADER_DELIVERY_QUEUE_URL")


def lambda_handler(event, context):
    try:
        classroom_assignment_id, config = validate_request(event)
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
        "student_github_username": event_body['sender_github_username'],
        "push_timestamp": event_body['push_timestamp'],
        "changed_files": event_body['changed_files'],
        "classroom_assignment_id": classroom_assignment_id
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
    classroom_assignment_id = path_params['id']
    # Get the config from secret manager if it is not already cached in the global dict
    if classroom_assignment_id not in CONFIG_DICT:
        CONFIG_DICT[classroom_assignment_id] = get_config(classroom_assignment_id)
    # Return the config
    return classroom_assignment_id, CONFIG_DICT[classroom_assignment_id]


def create_grading_request(request_body):
    """
    Creates a grading request on the GradingQueue
    @param request_body:
    @return: The message id of the created message
    """
    response = sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(request_body))
    return response['MessageId']


def get_config(classroom_assignment_id):
    """
    Get the config for the given classroom assignment id from the secret manager
    """
    try:
        secret_response = ssm.get_parameter(
            Name=f'/tm-autograder/github-classroom-assignment/{classroom_assignment_id}/config', WithDecryption=True)
        return json.loads(secret_response['Parameter']['Value'])
    except Exception as e:
        raise Exception(f"Error getting config for {classroom_assignment_id}: {e}")
