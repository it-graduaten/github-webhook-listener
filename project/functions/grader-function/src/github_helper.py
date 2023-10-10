import os
import sys
import base64
import shutil
import getopt
from github import Github
from github import GithubException

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
        print("Processing %s" % content.path)
        if content.type == 'dir':
            os.makedirs(os.path.join(destination_folder, content.path))
            download_directory(repository, sha, content.path, destination_folder)
        else:
            try:
                path = content.path
                file_content = repository.get_contents(path, ref=sha)
                file_data = base64.b64decode(file_content.content)
                file_out = open(os.path.join(destination_folder, content.path), "w+", encoding="utf-8")
                file_out.write(file_data.decode("utf-8"))
                file_out.close()
            except (GithubException, IOError) as exc:
                print('Error processing %s: %s', content.path, exc)
            except Exception as exc:
                print('Error processing %s: %s', content.path, exc)

def download_folder_from_repo(token: str, repo_full_name: str, branch: str, folder_to_download: str, destination_folder: str = "tmp"):
    # Split the repo full name into org and repo
    org, repo = repo_full_name.split("/")
    print(f'Downloading folder "{folder_to_download}" from repo "{repo}" in org "{org}" to "{destination_folder}"')
    # Create a GitHub instance
    github = Github(token)
    organization = github.get_organization(org)
    repository = organization.get_repo(repo)
    sha = get_sha_for_tag(repository, branch)
    download_directory(repository, sha, folder_to_download, destination_folder)