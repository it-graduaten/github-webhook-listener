from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel
import json_helper
import github_helper
import file_helper
import codegrade_helper
import course_constants
import shutil
import os

app = FastAPI()

class GithubPushPayload(BaseModel):
    commits: list = []

@app.get('/')
async def root():
    return 'Hello World!'

def handle_payload(parent_dirs: list):
    for dir in parent_dirs:
        # Check if the parent directory contains a 'config.json' file
        is_assignment = github_helper.is_assignment_dir(dir)
        if is_assignment:
            # Get the assignment name from the config file in the dir
            assignment_name = github_helper.get_assignment_name_from_config(dir)
            # Delete all contents in the temp folder
            file_helper.delete_all_content(course_constants.TEMP_DIR)
            # Download all from github to the temp folder
            github_helper.download_dir(dir, course_constants.TEMP_DIR)
            for course_id in course_constants.CODEGRADE_COURSE_IDS:
                # Check if the assignment exists on codegrade
                assignment = codegrade_helper.check_if_codegrade_assignment_exists(assignment_name, course_id)
                if assignment is not None:
                    codegrade_helper.update_codegrade_assignment(assignment, [], os.path.join(course_constants.TEMP_DIR, dir))
            # Delete all contents in the temp folder
            file_helper.delete_all_content(course_constants.TEMP_DIR)

@app.post('/oop') 
async def oop_root(payload: GithubPushPayload, background_tasks: BackgroundTasks):
    output = ["Received push event from OOP repository"]
    updated_files = json_helper.get_changed_and_added_files(payload.commits)
    parent_dirs = json_helper.get_parent_dirs(updated_files)

    # Add updated files to output
    output.append("Updated files:")
    for file in updated_files:
        output.append(file)

    # For each 'config.json' file, get the contents and add it to the list
    background_tasks.add_task(handle_payload, parent_dirs)
             
    return output