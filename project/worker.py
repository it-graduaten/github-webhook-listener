import os
import time

from celery import Celery
from celery.contrib import rdb


from submission_runner import SubmissionRunner


celery = Celery(__name__)
celery.conf.broker_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379")
celery.conf.result_backend = os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6379")


@celery.task(name="create_task")
def create_task(task_type):
    time.sleep(int(task_type) * 10)
    return True

@celery.task(name="fetch_solution_repo")
def fetch_solution_repo():
    print("Fetching solution repo")
    submission_runner = SubmissionRunner()
    submission_runner.fetch_solution_repo()
    return True

@celery.task(name="run_tests_for_student")
def run_tests_for_student(repo_name, changed_exercises):
    print("Running tests for student")
    submission_runner = SubmissionRunner()
    submission_runner.run_tests_for_student(repo_name, changed_exercises)
    return True