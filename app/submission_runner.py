#!/bin/python

from datetime import datetime, timedelta
from typing import Final
from git import Repo
from custom_types import ClassroomRoster
from test_runner import TestRunner
from file_operations import FileOperations
from github_helper import GithubHelper
from canvas_helper import CanvasManager
from logger import Logger
import pytz
import argparse
import concurrent.futures
from typing import List
from custom_types import TestRunResult

class RepoResource(object):
    """
    Clone a repository from GitHub and close it when done.
    """
    repo_name: Final[str]
    repo_destination_path: Final[str]
    repo: Repo

    def __init__(self, repo_name: str, repo_destination_path: str, file_ops: FileOperations, github_helper: GithubHelper):
        self.repo_name = repo_name
        self.repo_destination_path = repo_destination_path
        self.file_ops = file_ops
        self.github_helper = github_helper

    def __enter__(self) -> Repo:
        # Remove the repo if it already exists
        self.file_ops.rmtree(self.repo_destination_path)

        self.repo = self.github_helper.clone_repo(self.repo_name, self.repo_destination_path)
        return self.repo

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.repo.close()

        # Remove the repository from the filesystem.
        self.file_ops.rmtree(self.repo_destination_path)

class SubmissionRunner:
    kSolution_repo_name: Final[str] = 'OOP-SolutionRepo'
    kSolution_repo_path: Final[str] = f'./solution-repo'

    def __init__(self, logfile_name: str):
        # Init classes
        logfile_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + ".log"
        self.logger = Logger(logfile_name)
        self.test_runner = TestRunner(self.logger)
        self.file_ops = FileOperations(self.logger)
        self.github_helper = GithubHelper(self.logger)
        self.canvas_manager = CanvasManager(self.logger)
        self.classroom_roster = self.get_classroom_roster()  
        self.utc = pytz.UTC

    
    def get_classroom_roster(self) -> dict[str, ClassroomRoster]:
        """
        Read the classroom roster to get a link between the student identifier and the GitHub username and convert it to
        a dict so that we have O(1) lookup based on the students GitHub username.
        """
        self.classroom_roster = self.file_ops.get_classroom_roster()
        if self.classroom_roster is None:
            self.logger.write_to_log_file("Classroom roster not found")
            exit()

        return {student['github_username']: student for student in self.classroom_roster}      

    def run_tests_for_student(self, repo_name: str, changed_exercises) -> None:
        """
        Run test for a given student.

        Parameters
        ----------
        kTest_repo_path : str
            The filesystem destination path where the repo will be written to.
        test_repo : str
            The GitHub URL for the student's repository.
        student_identifier: str
            The LMS identification number for the student, typically something like r0636326.
        """

        # Get github_username of the repo, which is all parts after the first '-',
        # because GitHub classroom appends the github_username to the repo name
        github_username = repo_name.split('-')[1]

        # Get the student identifier based on the github_username
        # If the student is not found, skip the repo
        if github_username not in self.classroom_roster:
            self.logger.write_to_log_file(f"Student with github_username {github_username} not found")
            exit()

        student = self.classroom_roster[github_username]
        student_identifier = student['identifier']

        kTest_repo_path = f'./student-repos/{repo_name}'

        with RepoResource(self.kSolution_repo_name, self.kSolution_repo_path, self.file_ops, self.github_helper) as solution_repo:
            with RepoResource(repo_name, kTest_repo_path, self.file_ops, self.github_helper) as current_repo:
                heads = current_repo.heads
                main = heads.main
                all_commits = list(current_repo.iter_commits(main))
                all_results: List[TestRunResult] = []

                """ Get a list of the exercises that should be graded """
                all_exercises = self.canvas_manager.get_all_exercises_in_assignment_group(assignment_group_name="Permanente evaluatie")
                all_exercises_with_name_and_utc_due_date = self.canvas_manager.manipulate_exercises(all_exercises)
                print(all_exercises_with_name_and_utc_due_date)
                print(changed_exercises)
                # Filter only exercises that have been changed
                all_exercises_with_name_and_utc_due_date = [exercise for exercise in all_exercises_with_name_and_utc_due_date if exercise['name'] in changed_exercises]

                print(all_exercises_with_name_and_utc_due_date)

                for exercise in all_exercises_with_name_and_utc_due_date:
                    # Get exercise name
                    exc_name = exercise['name']

                    # Get exercise due date
                    exc_due_date = exercise['due_at']

                    # Get the current timestamp
                    utcn = datetime.utcnow().replace(tzinfo=self.utc)

                    # If the due date is None, skip the exercise
                    if exc_due_date is None:
                        continue
                    # If the due date is longer than 1 day in the past, skip the exercise
                    if exc_due_date < utcn - timedelta(days=1):
                        continue
                    # If the due date is longer than 8 days in the future, skip the exercise
                    if exc_due_date > utcn + timedelta(days=8):
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
                        self.file_ops.copy_dir(f'{self.kSolution_repo_path}/{chapter}/{exc_name}/test',
                                        f'./{kTest_repo_path}/{chapter}/{exc_name}/test', True)
                        # Run the tests
                        self.test_runner.run_tests(f'./{kTest_repo_path}/{chapter}/{exc_name}/test')
                        # Get results from the test
                        test_run_result_dict: TestRunResult = self.test_runner.get_test_run_result(f'./{kTest_repo_path}/{chapter}/{exc_name}/test')
                        test_run_result_dict['assignment'] = exc_name
                        test_run_result_dict['run_at_utc_datetime'] = str(utcn)
                        test_run_result_dict['should_update_canvas'] = True
                        all_results.append(test_run_result_dict)
                    except Exception as e:
                        self.logger.write_to_log_file(f"Error: {e}")

                # Save results to file
                results_with_should_update = self.file_ops.save_results_to_file(all_results, f'{student_identifier}.json')

                """ Upload results into Canvas """
                self.canvas_manager.upload_results(student_identifier, results_with_should_update)