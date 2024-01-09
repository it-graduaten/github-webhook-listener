import datetime
import json
import os
import boto3

sqs = boto3.client('sqs')
ssm = boto3.client('ssm')
dynamodb = boto3.client('dynamodb')

CONFIG_DICT = {}

QUEUE_URL = os.environ.get("GRADER_DELIVERY_QUEUE_URL")


def lambda_handler(event, context):
    try:
        log = []
        log.append("Received event")

        try:
            classroom_assignment_id, config = validate_request(event)
        except Exception as e:
            print(f"Error: {e}")
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "message": f"Request did not get validated. Error: {e}",
                }),
            }
        log.append("Validated request")
        event_body = json.loads(event['body'])
        log.append("Loaded event body")
        log.append(event_body)
        log.append(config)

        # Create grading request body
        grading_request_body = {
            "canvas_course_id": config['canvas_course_id'],
            "github_classroom_id": config['github_classroom_id'],
            "solution_repo_full_name": config['solution_repo_full_name'],
            "application_type": config['application_type'],
            "student_repo_full_name": event_body['repository']['full_name'],
            "student_github_id": event_body['sender']['id'],
            "student_github_username": event_body['sender']['login'],
            "push_timestamp": event_body['head_commit']['timestamp'],
            "changed_files": get_changed_files(event_body['commits']),
            "classroom_assignment_id": classroom_assignment_id
        }
        log.append("Created grading request body")

        # Trigger message on GradingQueue with GradingRequest
        message_id = create_grading_request(grading_request_body)
        log.append("Created grading request")
        create_dynamodb_entry(message_id, event_body['head_commit']['timestamp'], event_body['sender']['login'])
        log.append("Created dynamodb entry")

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
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 400,
            "body": json.dumps({
                "message": log,
                "error": f"error: {e}"
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
    @param classroom_assignment_id: The id of the classroom assignment
    """
    try:
        secret_response = ssm.get_parameter(
            Name=f'/tm-autograder/github-classroom-assignment/{classroom_assignment_id}/config', WithDecryption=True)
        return json.loads(secret_response['Parameter']['Value'])
    except Exception as e:
        raise Exception(f"Error getting config for {classroom_assignment_id}: {e}")


def get_changed_files(commits):
    files = list()

    for commit in commits:
        files.extend(commit["added"])
        files.extend(commit["modified"])
        files.extend(commit["removed"])

    return files


def create_dynamodb_entry(queue_item_id, push_timestamp, github_username):
    dynamodb.put_item(
        TableName='dev-tm-autograder-request-table',
        Item={
            # Create a unique id for the item
            'Id': {'S': queue_item_id},
            # Delete at should be the current timestamp + 5 days
            'DeleteAtTimestamp': {'N': str(datetime.datetime.utcnow().timestamp() + 432000)},
            'GithubPushTimestamp': {'S': push_timestamp},
            'GithubUsername': {'S': github_username},
            'Status': {'S': 'Requested'},
            "CreatedAtTimestamp": {'N': str(datetime.datetime.utcnow().timestamp())}
        }
    )
