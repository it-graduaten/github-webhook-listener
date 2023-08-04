#!/bin/python

from datetime import datetime, timedelta
from typing import Final
from git import Repo
from custom_types import ClassroomRoster
from test_runner import TestRunner
from file_operations import FileOperations
from github_helper import GithubHelper
from canvas_helper import CanvasManager
import pytz
import argparse
import concurrent.futures
from typing import List
from custom_types import TestRunResult
from log_helper import LogHelper


class RepoResource(object):
    """
    Clone a repository from GitHub and close it when done.
    """
    repo_name: Final[str]
    repo_destination_path: Final[str]
    repo: Repo

    def __init__(self, repo_name: str, repo_destination_path: str, file_ops: FileOperations,
                 github_helper: GithubHelper, remove_on_close: bool = True):
        self.repo_name = repo_name
        self.repo_destination_path = repo_destination_path
        self.file_ops = file_ops
        self.github_helper = github_helper
        self.remove_on_close = remove_on_close

    def __enter__(self) -> Repo:
        # Remove the repo if it already exists
        self.file_ops.rmtree(self.repo_destination_path)
        # Create a folder for the repo
        self.file_ops.mkdir(self.repo_destination_path)
        # Clone the repo
        self.repo = self.github_helper.clone_repo(self.repo_name, self.repo_destination_path)
        return self.repo

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.repo.close()

        if (self.remove_on_close):
            # Remove the repository from the filesystem.
            self.file_ops.rmtree(self.repo_destination_path)


class SubmissionRunner:
    kSolution_repo_path: Final[str] = f'solution-repo'

    def __init__(self, course_config):
        # Init classes
        self.course_config = course_config
        self.logger = LogHelper()
        self.test_runner = TestRunner(self.logger)
        self.file_ops = FileOperations(self.logger)
        self.github_helper = GithubHelper(self.logger)
        self.canvas_manager = CanvasManager(self.logger, course_config['canvas_course_id'])
        self.utc = pytz.UTC

    def get_classroom_roster(self):
        """
        Read the classroom roster to get a link between the student identifier and the GitHub username and convert it to
        a dict so that we have O(1) lookup based on the students GitHub username.
        """
        classroom_roster = self.file_ops.get_classroom_roster()
        if classroom_roster is None:
            self.logger.debug("Classroom roster not found")
            exit()

        return {student['github_username']: student for student in classroom_roster}

    def fetch_solution_repo(self, solution_repo_name) -> None:
        with RepoResource(solution_repo_name, self.kSolution_repo_path + '/' + solution_repo_name, self.file_ops,
                          self.github_helper, False) as solution_repo:
            return

    def get_all_folders_in_solution_repo(self) -> List[str]:
        """
        Get all the folders in the solution repo.
        """
        return self.file_ops.get_all_folders_in_dir(self.kSolution_repo_path)

    def run_tests_for_student(self, repo_name: str, changed_exercises) -> None:
        """
        Run test for a given student.

        Parameters
        ----------
        repo_name : str
            The name of the repository where the update was pushed to.
        changed_exercises : list[str]
            A list of exercises that were changed in the repo.
        """
        # Get the current timestamp
        utcn_timestamp = datetime.utcnow().replace(tzinfo=self.utc).timestamp()
        # Get github_username of the repo, which is all parts after the first '-',
        # because GitHub classroom appends the github_username to the repo name
        github_username = repo_name.split('-')[1]

        # Get the classroom roster
        classroom_roster = self.get_classroom_roster()

        # Get the student identifier based on the github_username
        # If the student is not found, skip the repo
        if github_username not in classroom_roster:
            self.logger.debug(f"Student with github_username {github_username} not found")
            exit()

        student = classroom_roster[github_username]
        student_identifier = student['identifier']

        kTest_repo_path = f'./student-repos/{repo_name}-{utcn_timestamp}'

        with RepoResource(repo_name, kTest_repo_path, self.file_ops, self.github_helper, True) as current_repo:
            heads = current_repo.heads
            main = heads.main
            all_commits = list(current_repo.iter_commits(main))
            all_results: List[TestRunResult] = []

            """ Get a list of the exercises that should be graded """
            all_exercises = self.canvas_manager.get_all_exercises_in_assignment_group(
                assignment_group_name="Permanente evaluatie")
            all_exercises_with_name_and_utc_due_date = self.canvas_manager.manipulate_exercises(all_exercises)
            # Filter only exercises that have been changed
            all_exercises_with_name_and_utc_due_date = [exercise for exercise in
                                                        all_exercises_with_name_and_utc_due_date if
                                                        exercise['name'] in changed_exercises]

            self.logger.debug(f"Found {len(all_exercises_with_name_and_utc_due_date)} exercises to grade")

            for exercise in all_exercises_with_name_and_utc_due_date:
                # Get exercise name
                exc_name = exercise['name']

                # Get exercise due date
                exc_due_date = exercise['due_at']

                # Get the current timestamp
                utcn = datetime.utcnow().replace(tzinfo=self.utc)

                # If the due date is None, skip the exercise
                if exc_due_date is None:
                    self.logger.debug(f"Due date for {exc_name} is None, skipping exercise")
                    continue
                # If the due date is longer than 1 day in the past, skip the exercise
                if exc_due_date < utcn - timedelta(days=1):
                    self.logger.debug(f"Due date for {exc_name} is in the past, skipping exercise")
                    continue

                try:
                    # If the due date is in the future, checkout the latest commit
                    if exc_due_date > utcn:
                        self.github_helper.checkout_repo_at_specific_commit(current_repo, all_commits[0])
                    # If the due date is in the past, checkout the commit that was made before the due date
                    elif exc_due_date < utcn:
                        # Find the commit that was made before the due date
                        for commit in all_commits:
                            if commit.committed_date < exc_due_date.timestamp():
                                # Checkout the commit
                                self.github_helper.checkout_repo_at_specific_commit(current_repo, commit)
                                break
                    # Split exercise in chapter and number
                    chapter, number = exc_name.split('_')
                    # Copy the unit tests to the repo to be tested
                    unit_test_source_path = f'{self.kSolution_repo_path}/{self.course_config["solution_repo_name"]}/{chapter}/{exc_name}/test'
                    self.file_ops.copy_dir(unit_test_source_path, f'./{kTest_repo_path}/{chapter}/{exc_name}/test',
                                           True)
                    # Run the tests
                    self.test_runner.run_tests(f'./{kTest_repo_path}/{chapter}/{exc_name}/test')
                    # Get results from the test
                    test_run_result_dict: TestRunResult = self.test_runner.get_test_run_result(
                        f'./{kTest_repo_path}/{chapter}/{exc_name}/test')
                    test_run_result_dict['assignment'] = exc_name
                    test_run_result_dict['run_at_utc_datetime'] = str(utcn)
                    all_results.append(test_run_result_dict)
                except Exception as e:
                    self.logger.error(f"Error: {e}")

            print(all_results)

            """ Upload results into Canvas """
            self.canvas_manager.upload_results(student_identifier, all_results)
