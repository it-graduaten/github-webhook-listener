import sys

import os
import json
import shutil

import subprocess
import time

from src.github_helper import download_folder_from_repo
from src.xmlresult_helper import get_test_results_grade
from src.canvas_helper import upload_grades
from src.classroom_helper import get_student_identifier

TMP_FOLDER = "/tmp"


def handler(event, context):
    print(event)
    for record in event['Records']:
        print(f'working on message with ID: {record["messageId"]}')

        try:
            print("Processing record")
            process_record(record)
        except Exception as e:
            # Handle error gracefully here ...
            print(f"That went wrong, {e}")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": 'Hello from AWS Lambda using Python' + sys.version + '!',
        }),
    }


def process_record(record):
    # Print the env variable
    print(f"CANVAS_API_URL: {os.environ.get('CANVAS_API_URL')}")
    print(f"CANVAS_API_KEY: {os.environ.get('CANVAS_API_KEY')}")
    print(f"GITHUB_ACCESS_TOKEN: {os.environ.get('GITHUB_ACCESS_TOKEN')}")

    # Convert the record to a JSON object
    payload = json.loads(record["body"])
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
            download_folder_from_repo(repo_full_name=payload['solution_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}",
                                      destination_folder=f"{assignment_folder}/solution")
            # Download the students submission
            download_folder_from_repo(repo_full_name=payload['student_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}",
                                      destination_folder=f"{assignment_folder}/student")
            # Remove the 'Program.cs' file from the solution
            os.remove(os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Copy the Program.cs file from the student to the solution
            shutil.copy(os.path.join(assignment_folder, "student", chapter, assignment, "consoleapp", "Program.cs"),
                        os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Run the tests
            test_command = f"dotnet test {assignment_folder}/solution/{chapter}/{assignment}/test/test.csproj -l:\"trx;LogFileName=result.xml\" -nodereuse:false --verbosity d"
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
        upload_grades(canvas_course_id=payload['canvas_course_id'],
                      student_identifier=student_identifier,
                      push_timestamp=payload['timestamp'],
                      assignments_with_grade=grades)
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
