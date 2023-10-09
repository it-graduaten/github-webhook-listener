import sys
import json

import os
import json
import shutil

from src.github_helper import download_folder_from_repo
from src.xmlresult_helper import get_test_results_grade
from src.canvas_helper import upload_grades

TMP_FOLDER = "/tmp"

def handler(event, context):
    print(event)
    for record in event['Records']:
        print(f'working on message with ID: {record["messageId"]}')
        
        try:
            print("Processing record")
            process_record(record)
        except:
            # Handle error gracefully here ...
            print("That went wrong")
        
        
        
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": 'Hello from AWS Lambda using Python' + sys.version + '!',
        }),
    }
    
    
    
def process_record(record): 
    # payload = json.load(open(os.path.join("bak", "payload.json"), "r"))
    payload = json.loads(record['body'])

    grades = []

    # TODO: Check if this can be done asynchrously to run multiple tests at the same time
    for changed_file in payload['changed_files']:
        print("Working on file: {}".format(changed_file))
        try:
            # Split the path and get the chapter, assignment
            parts = changed_file.split("/")
            chapter = parts[0]
            assignment = parts[1]
            # Assignment folder should be in the format: <tmp>/<chapter>-<assignment>
            assignment_folder = os.path.join(TMP_FOLDER, f"{chapter}-{assignment}")
            # Download the solution folder
            download_folder_from_repo(repo_full_name=payload['solution_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}", destination_folder=f"{assignment_folder}/solution")
            # Download the students submission
            download_folder_from_repo(repo_full_name=payload['student_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}", destination_folder=f"{assignment_folder}/student")
            # Remove the 'Program.cs' file from the solution
            os.remove(os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Copy the Program.cs file from the student to the solution
            shutil.copy(os.path.join(assignment_folder, "student", chapter, assignment, "consoleapp", "Program.cs"),
                        os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Run the tests
            test_command = f"dotnet test {assignment_folder}/solution/{chapter}/{assignment}/test/test.csproj -l:\"trx;LogFileName=result.xml\""
            os.system(test_command)
            # Get a grade
            grade = get_test_results_grade(f"{assignment_folder}/solution/{chapter}/{assignment}/test/TestResults/result.xml")
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

    # Upload the grades to Canvas
    try:
        # Upload the grade to Canvas
        upload_grades(canvas_course_id=payload['canvas_course_id'],
                        student_identifier='u0142333',  # TODO: Change this to the use config
                        push_timestamp=payload['timestamp'],
                        assignments_with_grade=grades)

    except Exception as e:
        print(f"Error while uploading grades: {e}")