from git import Repo
from github import Github
import os

class GithubHelper:
    def __init__(self, logger):
        self.access_token = os.getenv('GITHUB_ACCESS_TOKEN')
        self.g = Github(self.access_token)
        self.org = self.g.get_organization('it-graduaten')
        self.logger = logger
        pass

    def clone_repo(self, repo_name, destination_path):
        if (self.access_token is None):
            self.logger.debug("No access token found for github, aborting")
            return None
        self.logger.debug(f'Cloning {repo_name} to {destination_path}..')
        url = f'https://{self.access_token}@github.com/it-graduaten/{repo_name}.git'
        repo = Repo.clone_from(url, destination_path)
        self.logger.debug(f'Cloned {repo_name} to {destination_path}')
        return repo

    def get_repo_name_list(self, name):    
        self.logger.debug("Getting list of repos..")
        repos = []
        for repo in self.org.get_repos():
            if name in repo.name:
                repos.append(repo.name)
        self.logger.debug("Got list of repos")
        return repos

    def checkout_repo_at_specific_commit(self, repo, commit_sha):
        self.logger.debug(f'Checking out {commit_sha}..')
        repo.git.checkout(commit_sha)
        self.logger.debug(f'Checked out {commit_sha}')


