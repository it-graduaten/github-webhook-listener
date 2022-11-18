from fastapi import FastAPI
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

@app.post('/oop') 
async def oop_root(payload: GithubPushPayload):
    output = []
    updated_files = json_helper.get_changed_and_added_files(payload.commits)
    parent_dirs = json_helper.get_parent_dirs(updated_files)

    # For each 'config.json' file, get the contents and add it to the list
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
                    output.append('Updated assignment ' + assignment_name + ' on CodeGrade in course ' + str(course_id))
                else:
                    output.append("Assignment " + assignment_name + " does not exist on Codegrade. Did not configure.")
            # Delete all contents in the temp folder
            file_helper.delete_all_content(course_constants.TEMP_DIR)
             
    return output