import os
import base64
import shutil
import pandas as pd
from github import Github
from github import GithubException
import git
from datetime import datetime
import requests


def get_sha_for_tag(repository, tag):
    """
    Returns a commit PyGithub object for the specified repository and tag.
    """
    branches = repository.get_branches()
    matched_branches = [match for match in branches if match.name == tag]
    if matched_branches:
        return matched_branches[0].commit.sha

    tags = repository.get_tags()
    matched_tags = [match for match in tags if match.name == tag]
    if not matched_tags:
        raise ValueError('No Tag or Branch exists with that name')
    return matched_tags[0].commit.sha


def download_directory(repository, sha, server_path, destination_folder):
    """
    Download all contents at server_path with commit tag sha in
    the repository.
    """

    destination_path = os.path.join(destination_folder, server_path)

    if os.path.exists(destination_path):
        shutil.rmtree(destination_path)

    os.makedirs(destination_path)
    contents = repository.get_dir_contents(server_path, ref=sha)

    for content in contents:
        if content.type == 'dir':
            os.makedirs(os.path.join(destination_folder, content.path))
            download_directory(repository, sha, content.path, destination_folder)
        else:
            try:
                path = content.path
                file_content = repository.get_contents(path, ref=sha)
                file_data = base64.b64decode(file_content.content)
                file_out_path = os.path.join(destination_folder, content.path)
                file_out = open(file_out_path, "w+", encoding="utf-8")
                file_out.write(file_data.decode("utf-8"))
                file_out.close()
            except (GithubException, IOError) as exc:
                print('Error processing %s: %s', content.path, exc)
            except Exception as exc:
                print('Error processing %s: %s', content.path, exc)


def download_folder_from_repo(token: str, repo_full_name: str, branch: str, folder_to_download: str,
                              destination_folder: str = "/tmp"):
    # Split the repo full name into org and repo
    org, repo = repo_full_name.split("/")
    print(f'Downloading folder "{folder_to_download}" from repo "{repo}" in org "{org}" to "{destination_folder}"')
    # Create a GitHub instance
    github = Github(token)
    organization = github.get_organization(org)
    repository = organization.get_repo(repo)
    sha = get_sha_for_tag(repository, branch)
    download_directory(repository, sha, folder_to_download, destination_folder)


def get_student_identifier_from_classroom(path_to_csv, student_github_id):
    """
    Get the student identifier from the classroom roster csv file
    :param path_to_csv: The path to the classroom roster csv file
    :param student_github_id: The Github ID of the student
    :return: The student identifier
    """
    # Read all students from the classroom roster csv file
    roster = pd.read_csv(path_to_csv)
    # Get the student identifier
    roster_identifier = roster[roster['github_id'] == student_github_id]['identifier'].values
    # If no student identifier is found, return None
    if len(roster_identifier) == 0:
        print(f"No student identifier found for student with Github ID: {student_github_id}")
        return None
    # If more than one student identifier is found, return None
    if len(roster_identifier) > 1:
        print(f"More than one student identifier found: {roster_identifier}")
        return None
    # Return the student identifier
    start_index = roster_identifier[0].find("(")
    end_index = roster_identifier[0].find(")")
    student_identifier = roster_identifier[0][start_index + 1:end_index]
    print(f"Student identifier found: {student_identifier}")
    return student_identifier


def get_student_identifier_from_classroom_assignment(token, github_username, classroom_assignment_id):
    """
    Get the student identifier from the classroom roster
    @param token: The GitHub token
    @param github_username: The students GitHub username
    @param classroom_assignment_id: The id of the classroom assignment
    @return: A student identifier (example: r0123456)
    """
    # Get the classroom assignment grades
    endpoint = f"https://api.github.com/assignments/{classroom_assignment_id}/grades"
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(endpoint, headers=headers)
    # If the response is not ok, return None
    if not response.ok:
        print(f"Error getting classroom assignment grades: {response.status_code}")
        return None
    # Get the student identifier
    student_identifier = None
    for grade in response.json():
        if grade['github_username'] == github_username:
            roster_identifier = grade['roster_identifier']
            start_index = roster_identifier.find("(")
            end_index = roster_identifier.find(")")
            student_identifier = roster_identifier[start_index + 1:end_index]
            break
    # If no student identifier is found, return None
    print(f"Student identifier found: {student_identifier}. Github username: {github_username}.")
    return student_identifier


def get_last_commit_time_for_folder(repo, folder_path):
    """
    Get the last commit time for a folder
    @param repo: A git repo object
    @param folder_path: The path to the folder
    @return: The last commit time
    """
    try:
        # Get the commit that last modified the file
        last_commit = repo.git.log('-n', '1', '--format="%ai"', '--', folder_path)

        print("Last commit", last_commit)

        # Parse the commit timestamp
        commit_time = datetime.strptime(last_commit.strip('"'), "%Y-%m-%d %H:%M:%S %z")

        return commit_time

    except git.GitCommandError:
        print(f"Error: Unable to get commit information for file {folder_path}")
        return None
