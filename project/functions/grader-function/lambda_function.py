# Custom imports
from src.mustache_report_helper import create_html_report, transform_to_mustache_dotnet_data
from src.xmlresult_helper import transform_xml_to_unittest_result
from src.github_helper import download_folder_from_repo, get_student_identifier_from_classroom_assignment, \
    get_last_commit_time_for_folder
from src.canvas_manager import CanvasAPIManager
from src.config import AppConfig, BotoSessionConfig, ParameterStoreConfig

# Standard library imports
from os import path
from awsiot_credentialhelper.boto3_session import Boto3SessionProvider
import json
import shutil
import stat
import git
import os
import subprocess
import time
from datetime import datetime
import pytz

# Get all configuration
boto_session_config = BotoSessionConfig.from_environ(environ=os.environ)
parameter_store_config = ParameterStoreConfig.from_environ(environ=os.environ)

# Create boto3 session object
boto3_session = Boto3SessionProvider(
    endpoint=boto_session_config.endpoint,
    role_alias=boto_session_config.role_alias,
    certificate=boto_session_config.certificate,
    private_key=boto_session_config.private_key,
    thing_name=boto_session_config.thing_name,
).get_session()

sqs = boto3_session.client('sqs')
ssm = boto3_session.client('ssm')
s3 = boto3_session.client('s3')

secret_response = ssm.get_parameter(
    Name=parameter_store_config.secret_name,
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
    message_id = record["MessageId"]
    # Convert the record to a JSON object
    payload = json.loads(record["Body"])
    # Create canvas credentials
    canvas_credentials = {'api_key': CANVAS_API_KEY, 'api_url': CANVAS_API_URL}
    # Create a canvas api manager
    canvas_api_manager = CanvasAPIManager(canvas_credentials, payload['canvas_course_id'])
    # Download the report templates from the config repo
    download_autograder_config()
    # Get the student identifier
    student_identifier = get_student_identifier_from_classroom_assignment(
        token=GITHUB_ACCESS_TOKEN,
        github_username=payload['student_github_username'],
        classroom_assignment_id=payload['classroom_assignment_id']
    )
    # If student identifier is None, the student is not in the classroom and nothing should happen
    if student_identifier is None or student_identifier == '':
        print(f"Student {payload['student_github_username']} is not in the classroom. Nothing to do")
        return
    # Get the push timestamp
    push_timestamp = payload['push_timestamp']
    # Get all unique assignments to grade
    assignments_to_grade = get_unique_assignments_to_grade(payload)
    # Clone the student repo
    student_repo_path = os.path.join(TMP_FOLDER, "student_repo")
    student_repo = clone_git_repo(
        repo_full_name=payload['student_repo_full_name'],
        destination_folder=student_repo_path
    )
    # Clone the solution repo
    solution_repo_path = os.path.join(TMP_FOLDER, "solution_repo")
    solution_repo = clone_git_repo(
        repo_full_name=payload['solution_repo_full_name'],
        destination_folder=solution_repo_path
    )

    for assignment_to_grade in assignments_to_grade:
        chapter = assignment_to_grade['chapter']
        assignment = assignment_to_grade['assignment']
        assignment_name = assignment_to_grade['assignment_name']

        try:
            # Get the according assignment from the canvas assignments
            canvas_assignment = canvas_api_manager.get_assignment_by_name(assignment_name)
            # Check if the assignment should be graded
            should_grade = check_if_should_grade(canvas_assignment, assignment_to_grade, student_repo)
            if not should_grade:
                print(f"Should not grade {assignment_name}")
                continue
            # Check the application type
            if payload['application_type'] == APPLICATION_CONSOLE:
                # TODO: Fix this later
                # grade, path_to_report = grade_console_app(
                #     message_id=message_id,
                #     assignment=assignment,
                #     assignment_folder=assignment_folder,
                #     assignment_name=assignment_name,
                #     chapter=chapter,
                #     payload=payload,
                #     push_timestamp=push_timestamp
                # )
                # Update the grade on Canvas
                canvas_api_manager.update_grade(student_identifier, canvas_assignment, grade, path_to_report)
            elif payload['application_type'] == APPLICATION_CONSOLE_WITH_MODELS:
                # Do something with console app with models
                grade, path_to_report = grade_console_app_with_models(
                    student_repo_path=student_repo_path,
                    solution_repo_path=solution_repo_path,
                    assignment_config=assignment_to_grade
                )
                # Update the grade on Canvas
                canvas_api_manager.update_grade(student_identifier, canvas_assignment, grade, path_to_report)
                pass
            else:
                # Unknown application type
                print(f"Unknown application type: {payload['application_type']}")
                continue
        except Exception as e:
            print(f"Error while processing {assignment_name}: {e}")
        finally:
            print("Cleaning up")
    print("Done")
    shutil.rmtree(TMP_FOLDER)


def check_if_should_grade(canvas_assignment, assignment_to_grade, repo):
    chapter = assignment_to_grade['chapter']
    assignment = assignment_to_grade['assignment']
    # If the assignment is not found, it can be skipped
    if canvas_assignment is None:
        print(f'Could not find assignment with name {assignment}. Skipped grading for this assignment')
        return False
    print("Getting last commit for ", f"{chapter}/{assignment}")
    # Get the moment of the last change in the assignment
    last_commit_time = get_last_commit_time_for_folder(repo, f"{chapter}/{assignment}")

    # If the due date of the assignment is before the push_timestamp, it can be skipped
    if canvas_assignment.due_at is not None:
        canvas_assignment_due_at = datetime.strptime(canvas_assignment.due_at, "%Y-%m-%dT%H:%M:%SZ")
        canvas_assignment_due_at = pytz.utc.localize(canvas_assignment_due_at)
        if canvas_assignment_due_at < last_commit_time:
            print(
                f'Assignment {assignment} was due before the push timestamp, skipping')
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


def grade_console_app(message_id, assignment, assignment_folder, assignment_name, chapter, payload, push_timestamp):
    # try:
    #     # Download the solution folder
    #     download_folder_from_repo(GITHUB_ACCESS_TOKEN, repo_full_name=payload['solution_repo_full_name'],
    #                               branch="main",
    #                               folder_to_download=f"{chapter}/{assignment}",
    #                               destination_folder=f"{assignment_folder}/solution")
    #     # Download the students submission
    #     download_folder_from_repo(GITHUB_ACCESS_TOKEN, repo_full_name=payload['student_repo_full_name'],
    #                               branch="main",
    #                               folder_to_download=f"{chapter}/{assignment}",
    #                               destination_folder=f"{assignment_folder}/student")
    #     # Remove the 'Program.cs' file from the solution
    #     os.remove(os.path.join(assignment_folder, "solution",
    #                            chapter, assignment, "consoleapp", "Program.cs"))
    #     # Copy the Program.cs file from the student to the solution
    #     shutil.copy(os.path.join(assignment_folder, "student", chapter, assignment, "consoleapp", "Program.cs"),
    #                 os.path.join(assignment_folder, "solution", chapter, assignment, "consoleapp",
    #                              "Program.cs"))
    #     # Run the tests
    #     test_command = f"dotnet test {assignment_folder}/solution/{chapter}/{assignment}/test/test.csproj -l:\"trx;LogFileName=result.xml\" --blame-hang-timeout 10m --blame-hang-dump-type mini --blame-hang"
    #     rc, output = run_command(test_command)
    #     # Write the log to s3
    #     log_filename = f"{message_id}_{assignment_name}.log"
    #     write_log_to_s3(output, log_filename)
    #     path_to_result_xml = f"{assignment_folder}/solution/{chapter}/{assignment}/test/TestResults/result.xml"
    #     # Create a report
    #     data = get_mustache_data(path_to_result_xml, assignment_name)
    #     path_to_report = create_html_report(
    #         path_to_template=os.path.join(TMP_FOLDER, "tm-autograder-config", "report-templates", "console_app.html"),
    #         output_path=f"{assignment_folder}/grader-report-{push_timestamp}.html",
    #         data=data)
    #     return data.grade, path_to_report
    # except Exception as e:
    #     print(f"Error while processing {assignment_name}: {e}")
    pass


def grade_console_app_with_models(student_repo_path, solution_repo_path, assignment_config):
    chapter = assignment_config['chapter']
    assignment = assignment_config['assignment']
    assignment_name = assignment_config['assignment_name']
    path_to_student_assignment = os.path.join(student_repo_path, chapter, assignment)
    path_to_solution_assignment = os.path.join(solution_repo_path, chapter, assignment)

    try:
        # Remove the 'Program.cs' file from the solution
        os.remove(os.path.join(path_to_solution_assignment, "consoleapp", "Program.cs"))
        # Copy the Program.cs file from the student to the solution
        shutil.copy(os.path.join(path_to_student_assignment, "consoleapp", "Program.cs"),
                    os.path.join(path_to_solution_assignment, "consoleapp", "Program.cs"))
        # Remove the Models folder from the solution, even if it is not empty
        shutil.rmtree(os.path.join(path_to_solution_assignment, "consoleapp", "Models"))
        # Copy the Models folder from the student to the solution
        shutil.copytree(os.path.join(path_to_student_assignment, "consoleapp", "Models"),
                        os.path.join(path_to_solution_assignment, "consoleapp", "Models"))
        # Run the tests
        test_command = f"dotnet test {path_to_solution_assignment}/test/test.csproj -l:\"trx;LogFileName=result.xml\" --blame-hang-timeout 10m --blame-hang-dump-type mini --blame-hang"
        rc, output = run_command(test_command)
        path_to_result_xml = f"{path_to_solution_assignment}/test/TestResults/result.xml"
        # Create a report
        unittest_result_obj = transform_xml_to_unittest_result(path_to_result_xml)
        mustache_data = transform_to_mustache_dotnet_data(unittest_result_obj)
        print(mustache_data.to_json())
        # Get the current timestamp as a string
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        path_to_report = create_html_report(
            template_path=os.path.join(TMP_FOLDER, "tm-autograder-config", "report-templates",
                                       "console_app_with_models.html"),
            output_path=f"{TMP_FOLDER}/report-{timestamp}.html",
            data=mustache_data.to_dict())
        return mustache_data.grade, path_to_report
    except Exception as e:
        print(f"Error while processing {assignment_name}: {e}")


def download_autograder_config():
    clone_git_repo(repo_full_name="it-graduaten/tm-autograder-config",
                   destination_folder=os.path.join(TMP_FOLDER, "tm-autograder-config"))


def write_log_to_s3(log, log_filename):
    new_file = s3.put_object(Body=log, Bucket='tm-autograder-log-bucket', Key=log_filename)
    print("File created", new_file)


def clone_git_repo(repo_full_name, destination_folder):
    """
    Clones a git repo using GitPython
    @param repo_full_name: the full name of the repo, e.g. it-graduaten/tm-autograder
    @param destination_folder: the folder where the repo should be cloned to
    @return: the repo object
    """
    print("Cloning repo", repo_full_name)
    # Remove the repo if it exists
    if path.exists(destination_folder):
        for root, dirs, files in os.walk(destination_folder):
            for dir in dirs:
                os.chmod(path.join(root, dir), stat.S_IRWXU)
            for file in files:
                os.chmod(path.join(root, file), stat.S_IRWXU)
        shutil.rmtree(destination_folder)

    # Clone the repo using GitPython
    repo = git.Repo.clone_from(
        f'https://JorenSynaeveTM:{GITHUB_ACCESS_TOKEN}@github.com/{repo_full_name}.git',
        destination_folder)
    print("Cloned repo to", destination_folder)
    return repo


def run_command(command):
    process = subprocess.Popen(command.split(" "), stdout=subprocess.PIPE)
    full_output = ""
    while True:
        try:
            output = process.stdout.readline().decode('utf-8')
            if not output:
                break
            print(f"[CMD] {output.strip()}")
            full_output += output
        except Exception as e:
            print(f"Error: {e}")
            break

        time.sleep(0.1)

    rc = process.poll()
    return rc, full_output


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
