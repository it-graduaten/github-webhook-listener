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

from src.github_helper import download_folder_from_repo
from src.xmlresult_helper import get_test_results_grade
from src.canvas_helper import upload_grades
from src.classroom_helper import get_student_identifier

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
    # Get the student identifier
    student_identifier = get_student_identifier(payload['github_classroom_id'], payload['student_github_id'])
    grades = []

    # TODO: Check if this can be done asynchrously to run multiple tests at the same time
    for changed_file in payload['changed_files']:
        print("Working on file: {}".format(changed_file))
        # Split the path and get the chapter, assignment
        parts = changed_file.split("/")
        chapter = parts[0]
        assignment = parts[1]
        # Assignment folder should be in the format: <tmp>/<chapter>-<assignment>
        assignment_folder = os.path.join(TMP_FOLDER, f"{chapter}-{assignment}")

        try:
            # Download the solution folder
            download_folder_from_repo(GITHUB_ACCESS_TOKEN, repo_full_name=payload['solution_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}",
                                      destination_folder=f"{assignment_folder}/solution")
            # Download the students submission
            download_folder_from_repo(GITHUB_ACCESS_TOKEN, repo_full_name=payload['student_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}",
                                      destination_folder=f"{assignment_folder}/student")
            # Remove the 'Program.cs' file from the solution
            os.remove(os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Copy the Program.cs file from the student to the solution
            shutil.copy(os.path.join(assignment_folder, "student", chapter, assignment, "consoleapp", "Program.cs"),
                        os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Run the tests
            test_command = f"dotnet test {assignment_folder}/solution/{chapter}/{assignment}/test/test.csproj -l:\"trx;LogFileName=result.xml\""
            run_command(test_command)
            
            # Get a grade
            grade = get_test_results_grade(
                f"{assignment_folder}/solution/{chapter}/{assignment}/test/TestResults/result.xml")
            # Add the grade to the list of grades
            grades.append({
                "assignment": assignment,
                "grade": grade
            })
        except Exception as e:
            print(f"Error while processing file {changed_file}: {e}")
        finally:
            # Clean up
            print("Cleaning up")
            shutil.rmtree(assignment_folder)

    try:
        # Upload the grade to Canvas
        credentials = {'api_key': CANVAS_API_KEY, 'api_url': CANVAS_API_URL}
        upload_grades(canvas_course_id=payload['canvas_course_id'],
                      student_identifier=student_identifier,
                      push_timestamp=payload['timestamp'],
                      assignments_with_grade=grades, credentials=credentials)
    except Exception as e:
        print(f"Error while uploading grades: {e}")

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
        
        
    