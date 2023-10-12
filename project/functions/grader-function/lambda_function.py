from src.xmlresult_helper import get_test_results_grade, generate_html_report
from src.github_helper import download_folder_from_repo, get_student_identifier_from_classroom
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
    # Get the student identifier
    download_folder_from_repo(
        token=GITHUB_ACCESS_TOKEN,
        repo_full_name="it-graduaten/tm-autograder-config",
        branch="main",
        folder_to_download="github-classroom-rosters"
    )
    student_identifier = get_student_identifier_from_classroom(
        os.path.join(TMP_FOLDER, "github-classroom-rosters", f"{payload['github_classroom_id']}.csv"),
        payload['student_github_id']
    )
    push_timestamp = payload['push_timestamp']

    # Download the report templates
    download_folder_from_repo(
        token=GITHUB_ACCESS_TOKEN,
        repo_full_name="it-graduaten/tm-autograder-config",
        branch="main",
        folder_to_download="report-templates"
    )

    # TODO: Check if this can be done asynchrously to run multiple tests at the same time
    for changed_file in payload['changed_files']:
        print("Working on file: {}".format(changed_file))
        # Split the path and get the chapter, assignment
        parts = changed_file.split("/")
        chapter = parts[0]
        assignment = parts[1]
        assignment_name = assignment.replace("_", ".")
        # Get the according assignment from the canvas assignments
        canvas_assignment = canvas_api_manager.get_assignment_by_name(assignment_name)

        # If the assignment is not found, it can be skipped
        if canvas_assignment is None:
            print(f'Could not find assignment with name {assignment_name}. Skipped grading for this assignment')
            continue

        # If the due date of the assignment is before the push_timestamp, it can be skipped
        if canvas_assignment.due_at is not None:
            if canvas_assignment.due_at < push_timestamp:
                print(
                    f'Assignment {canvas_assignment.name} was due before the push timestamp, skipping')
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
            path_to_result_xml = f"{assignment_folder}/solution/{chapter}/{assignment}/test/TestResults/result.xml"

            # Get a grade
            grade = get_test_results_grade(path_to_result_xml)
            # Create a report
            data = {'assignment': assignment_name, 'grade': grade}
            path_to_report = generate_html_report(
                template_path=os.path.join(TMP_FOLDER, "report-templates", "console_app.html"),
                output_path=f"{assignment_folder}/report.html",
                data=data)
            # Update the grade
            canvas_api_manager.update_grade(
                student_identifier, canvas_assignment, grade, path_to_report)
        except Exception as e:
            print(f"Error while processing file {changed_file}: {e}")
        finally:
            # Clean up
            print("Cleaning up")
            shutil.rmtree(TMP_FOLDER)


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
