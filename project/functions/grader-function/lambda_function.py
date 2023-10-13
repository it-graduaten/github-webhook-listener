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
APPLICATION_CONSOLE = "console"
APPLICATION_CONSOLE_WITH_MODELS = "console_with_models"

# Print the env variable
print(f"CANVAS_API_URL: {CANVAS_API_URL}")


def process_record(record):
    # Convert the record to a JSON object
    payload = json.loads(record["Body"])
    # Create canvas credentials
    canvas_credentials = {'api_key': CANVAS_API_KEY, 'api_url': CANVAS_API_URL}
    # Create a canvas api manager
    canvas_api_manager = CanvasAPIManager(canvas_credentials, payload['canvas_course_id'])
    # Download the classroom rosters from the config repo
    download_classroom_rosters()
    # Download the report templates from the config repo
    download_report_templates()
    # Get the student identifier
    student_identifier = get_student_identifier_from_classroom(
        os.path.join(TMP_FOLDER, "github-classroom-rosters", f"{payload['github_classroom_id']}.csv"),
        payload['student_github_id']
    )
    # Get the push timestamp
    push_timestamp = payload['push_timestamp']
    # Get all unique assignments to grade
    assignments_to_grade = get_unique_assignments_to_grade(payload)

    for assignment_to_grade in assignments_to_grade:
        chapter = assignment_to_grade['chapter']
        assignment = assignment_to_grade['assignment']
        assignment_name = assignment_to_grade['assignment_name']
        # Get the according assignment from the canvas assignments
        canvas_assignment = canvas_api_manager.get_assignment_by_name(assignment_name)
        # Check if the assignment should be graded
        should_grade = check_if_should_grade(canvas_assignment, push_timestamp, assignment_name)
        if not should_grade:
            print(f"Should not grade {assignment_name}")
            continue
        # Create the path to the assignment folder
        assignment_folder = os.path.join(TMP_FOLDER, f"{chapter}-{assignment}")
        # Check the application type
        if payload['application_type'] == APPLICATION_CONSOLE:
            grade, path_to_report = grade_console_app(
                assignment=assignment,
                assignment_folder=assignment_folder,
                assignment_name=assignment_name,
                chapter=chapter,
                payload=payload,
                push_timestamp=push_timestamp
            )
            # Update the grade on Canvas
            canvas_api_manager.update_grade(student_identifier, canvas_assignment, grade, path_to_report)
        elif payload['application_type'] == APPLICATION_CONSOLE_WITH_MODELS:
            # Do something with console app with models
            pass
        else:
            # Unknown application type
            print(f"Unknown application type: {payload['application_type']}")
            continue
        # Clean up
        shutil.rmtree(TMP_FOLDER)


def check_if_should_grade(canvas_assignment, push_timestamp, assignment_name):
    # If the assignment is not found, it can be skipped
    if canvas_assignment is None:
        print(f'Could not find assignment with name {assignment_name}. Skipped grading for this assignment')
        return False
    # If the due date of the assignment is before the push_timestamp, it can be skipped
    if canvas_assignment.due_at is not None:
        if canvas_assignment.due_at < push_timestamp:
            print(
                f'Assignment {assignment_name} was due before the push timestamp, skipping')
            return False
    return True


def get_unique_assignments_to_grade(payload):
    # Create a list of all individual assignments that need to be graded
    assignments_to_grade = []
    for changed_file in payload['changed_files']:
        parts = changed_file.split("/")
        chapter = parts[0]
        assignment = parts[1]
        assignment_data = {'chapter': chapter, 'assignment': assignment,
                           'assignment_name': assignment.replace("_", ".")}
        if assignment_data not in assignments_to_grade:
            assignments_to_grade.append(assignment_data)
    return assignments_to_grade


def grade_console_app(assignment, assignment_folder, assignment_name, chapter, payload, push_timestamp):
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
                    os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp",
                                 "Program.cs"))
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
            output_path=f"{assignment_folder}/grader-report-{push_timestamp}.html",
            data=data)
        return grade, path_to_report
    except Exception as e:
        print(f"Error while processing {assignment_name}: {e}")


def download_classroom_rosters():
    download_folder_from_repo(
        token=GITHUB_ACCESS_TOKEN,
        repo_full_name="it-graduaten/tm-autograder-config",
        branch="main",
        folder_to_download="github-classroom-rosters"
    )


def download_report_templates():
    download_folder_from_repo(
        token=GITHUB_ACCESS_TOKEN,
        repo_full_name="it-graduaten/tm-autograder-config",
        branch="main",
        folder_to_download="report-templates"
    )


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
