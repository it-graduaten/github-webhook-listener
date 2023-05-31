from fastapi import BackgroundTasks, FastAPI
from custom_types import GithubPushPayload, WebhookResponse
import logging
import re
import time
from submission_runner import SubmissionRunner

logging.basicConfig(filename='record.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get('/')
async def root():
    return 'Hello World!'

@app.get('/update-solutions')
async def update_solutions(background_tasks: BackgroundTasks):
    submission_runner = SubmissionRunner(logger)
    background_tasks.add_task(submission_runner.fetch_solution_repo)
    return 'Solutions will be updated!'


@app.post('/oop')
async def oop_root(payload: GithubPushPayload, background_tasks: BackgroundTasks):
    # Get the repo name
    repo_name = payload.repository.name
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
    output = f"Received push event from {repo_name}"
    submission_runner = SubmissionRunner(logger)
    logger.info(output)
    background_tasks.add_task(submission_runner.run_tests_for_student, repo_name, changed_exercises)
    return WebhookResponse(message=output, changed_exercises=list(changed_exercises))
