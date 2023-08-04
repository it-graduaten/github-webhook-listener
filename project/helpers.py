import json

from custom_types import GithubPushPayload
import re


def get_changed_files_in_push(payload: GithubPushPayload):
    # Get all the changed files
    files = set()
    for commit in payload.commits:
        files.update(commit["added"], commit["modified"], commit["removed"])
    pattern = r"\d{2}/(\d{2}_\d{2})/"
    # Get all the changed exercises
    changed_exercises = set()
    for file in files:
        match = re.search(pattern, file)
        if match:
            changed_exercises.add(match.group(1))
    return changed_exercises


def get_config_for_endpoint(course_name):
    # Read the config file
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    # Get the correct config
    return config[course_name]
