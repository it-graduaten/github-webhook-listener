import os
import json
import shutil

from src.github_helper import download_folder_from_repo
from src.xmlresult_helper import get_test_results_grade
from src.canvas_helper import upload_grade

if __name__ == "__main__":
    # Read payload from bak folder
    payload = json.load(open(os.path.join("bak", "payload.json"), "r"))

    # TODO: Check if this can be done asynchrously to run multiple tests at the same time
    for changed_file in payload['changed_files']:
        print("Working on file: {}".format(changed_file))
        try:
            # Split the path and get the chapter, assignment
            parts = changed_file.split("/")
            chapter = parts[0]
            assignment = parts[1]
            # Download the solution folder
            download_folder_from_repo(repo_full_name=payload['solution_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}", destination_folder="tmp/solution")
            # Download the students submission
            download_folder_from_repo(repo_full_name=payload['student_repo_full_name'], branch="main",
                                      folder_to_download=f"{chapter}/{assignment}", destination_folder="tmp/student")
            # Remove the 'Program.cs' file from the solution
            os.remove(os.path.join("tmp", "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Copy the Program.cs file from the student to the solution
            shutil.copy(os.path.join("tmp", "student", chapter, assignment, "consoleapp", "Program.cs"),
                        os.path.join("tmp", "solution", chapter, assignment, "consoleapp", "Program.cs"))
            # Run the tests
            test_command = f"dotnet test tmp/solution/{chapter}/{assignment}/test/test.csproj -l:\"trx;LogFileName=result.xml\""
            os.system(test_command)
            # Get a grade
            grade = get_test_results_grade(f"tmp/solution/{chapter}/{assignment}/test/TestResults/result.xml")
            # Upload the grade to Canvas
            upload_grade(canvas_course_id=payload['canvas_course_id'],
                         student_identifier='u0142333',  # TODO: Change this to the use config
                         assignment_name=assignment,
                         grade=grade,
                         push_timestamp=payload['timestamp'])
        except Exception as e:
            print(f"Error while processing file {changed_file}: {e}")
        finally:
            # Clean up
            print("Cleaning up")
            shutil.rmtree("tmp")
