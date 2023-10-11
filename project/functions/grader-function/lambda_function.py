from src.classroom_helper import get_student_identifier
from src.canvas_helper import upload_grades, get_all_exercises_in_assignment_group
from src.xmlresult_helper import get_test_results_grade
from src.github_helper import download_folder_from_repo
from src.canvas_manager import CanvasAPIManager
import sys

import os
import json
import shutil

import subprocess
import time

from awsiot_credentialhelper.boto3_session import Boto3SessionProvider

# Create boto3 session object
boto3_session = Boto3SessionProvider(
    endpoint="c3ams71ru9zrmk.credentials.iot.eu-central-1.amazonaws.com",
    role_alias="test-role-for-grader-alias",
    certificate="/root/.aws/certs/ebdc06909aaf7de014439272ca845c59b092a3aa6d5ca884972cedcd43056e07-certificate.pem.crt",
    private_key="/root/.aws/certs/ebdc06909aaf7de014439272ca845c59b092a3aa6d5ca884972cedcd43056e07-private.pem.key",
    thing_name="grader-01",
).get_session()

sqs = boto3_session.client('sqs')
ssm = boto3_session.client('ssm')

secret_response = ssm.get_parameter(
    Name='/grader/secrets',
    WithDecryption=True
)
parsed_secret = json.loads(secret_response['Parameter']['Value'])['Parameters']

QUEUE_URL = parsed_secret["QUEUE_URL"]
CANVAS_API_URL = parsed_secret["CANVAS_API_URL"]
CANVAS_API_KEY = parsed_secret["CANVAS_API_KEY"]
GITHUB_ACCESS_TOKEN = parsed_secret["GITHUB_ACCESS_TOKEN"]
TMP_FOLDER = "/tmp"

# Print the env variable
print(f"CANVAS_API_URL: {CANVAS_API_URL}")


def process_record(record):
    # Convert the record to a JSON object
    payload = json.loads(record["Body"])
    # Create canvas credentials
    canvas_credentials = {'api_key': CANVAS_API_KEY, 'api_url': CANVAS_API_URL}
    # Create a canvas api manager
    canvas_api_manager = CanvasAPIManager(canvas_credentials, payload['canvas_course_id'])
    # Get all the assignments in the assignment group TODO: Get the assignment group from the payload
    canvas_assignments = canvas_api_manager.get_all_assignments_in_assignment_group('Permanente evaluatie')
    # Get the student identifier
    student_identifier = get_student_identifier(
        payload['github_classroom_id'], payload['student_github_id']
    )
    push_timestamp = payload['push_timestamp']

    # TODO: Check if this can be done asynchrously to run multiple tests at the same time
    for changed_file in payload['changed_files']:
        print("Working on file: {}".format(changed_file))
        # Split the path and get the chapter, assignment
        parts = changed_file.split("/")
        chapter = parts[0]
        assignment = parts[1]
        assignment_name = assignment.replace("_", ".")
        # Get the according assignment from the canvas assignments
        assignments_where_name = [item for item in canvas_assignments if assignment_name in item.name]

        if len(assignments_where_name) == 0:
            print(f'Could not find assignment with name {assignment_name}')
            return

        if len(assignments_where_name) > 1:
            print(f'Found multiple assignments with name {assignment_name}')
            return

        canvas_assignment = assignments_where_name[0]
        # If the due date of the assignment is before the push_timestamp, it can be skipped
        if canvas_assignment.due_at is not None:
            if canvas_assignment.due_at < push_timestamp:
                print(f'Assignment {canvas_assignment.name} was due before the push timestamp, skipping')
                continue

        # Assignment folder should be in the format: <tmp>/<chapter>-<assignment>
        assignment_folder = os.path.join(TMP_FOLDER, f"{chapter}-{assignment}")

        try:
            # Download the solution folder
            download_folder_from_repo(GITHUB_ACCESS_TOKEN, repo_full_name=payload['solution_repo_full_name'],
                                      branch="main",
                                      folder_to_download=f"{chapter}/{assignment}",
                                      destination_folder=f"{assignment_folder}/solution")
            # Download the students submission
            download_folder_from_repo(GITHUB_ACCESS_TOKEN, repo_full_name=payload['student_repo_full_name'],
                                      branch="main",
                                      folder_to_download=f"{chapter}/{assignment}",
                                      destination_folder=f"{assignment_folder}/student")
            # Remove the 'Program.cs' file from the solution
            os.remove(os.path.join(assignment_folder, "solution",
                                   chapter, assignment, "consoleapp", "Program.cs"))
            # Copy the Program.cs file from the student to the solution
            shutil.copy(os.path.join(assignment_folder, "student", chapter, assignment, "consoleapp", "Program.cs"),
                        os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Run the tests
            test_command = f"dotnet test {assignment_folder}/solution/{chapter}/{assignment}/test/test.csproj -l:\"trx;LogFileName=result.xml\""
            run_command(test_command)

            # Get a grade
            grade = get_test_results_grade(
                f"{assignment_folder}/solution/{chapter}/{assignment}/test/TestResults/result.xml")
            # Update the grade
            canvas_api_manager.update_grade(student_identifier, canvas_assignment, grade)
        except Exception as e:
            print(f"Error while processing file {changed_file}: {e}")
        finally:
            # Clean up
            print("Cleaning up")
            shutil.rmtree(assignment_folder)


def run_command(command):
    process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE)
    while True:
        try:
            output = process.stdout.readline().decode('utf-8')
            if not output:
                break
            print(f"[CMD] {output.strip()}")
        except Exception as e:
            print(f"Error: {e}")
            break

        time.sleep(0.1)

    rc = process.poll()
    return rc


if __name__ == "__main__":

    while True:
        time.sleep(1)
        print("Next iteration")
        try:
            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20
            )

            if not "Messages" in response:
                print("No messages found")
                continue

            for record in response['Messages']:
                print(f'working on message with ID: {record["MessageId"]}')

                response = sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=record["ReceiptHandle"]
                )

                try:
                    print("Processing record")
                    process_record(record)
                except Exception as e:
                    # Handle error gracefully here ...
                    print(f"That went wrong, {e}")
        except Exception as e:
            print(f"Loop failed, {e}")
