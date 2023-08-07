import os
import time

from celery import Celery
from celery.contrib import rdb

from submission_runner import SubmissionRunner

celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@celery.task(name="fetch_solution_repo")
def fetch_solution_repo(solution_repo_name):
    print("Fetching solution repo")
    submission_runner = SubmissionRunner({'canvas_course_id': 0})
    submission_runner.fetch_solution_repo(solution_repo_name)
    return True


@celery.task(name="run_tests_for_student")
def run_tests_for_student(repo_name, changed_exercises, course_config):
    """
    Run tests for a given student.
    @param repo_name: The name of the repository where the update was pushed to.
    @param changed_exercises: A list of exercises that were changed in the repo.
    @param course_config: The course config
    @rtype: bool
    """
    print("Running tests for student")
    submission_runner = SubmissionRunner(course_config)
    submission_runner.run_tests_for_student(repo_name, changed_exercises)
    return True
