from fastapi import BackgroundTasks, FastAPI
from custom_types import GithubPushPayload, WebhookResponse
import logging
import re
import time

logging.basicConfig(filename='record.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

logger = logging.getLogger(__name__)

app = FastAPI()


@app.get('/')
async def root():
    return 'Hello World!'

def write_notification(email: str, message='This is a notification'):
    # Simulate a long running task
    time.sleep(3)
    logger.info(f"Sending notification to {email} with message: {message}")


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
    logger.info(output)
    background_tasks.add_task(write_notification, "joren@gmail.com", message="some notification")
    return WebhookResponse(message=output, changed_exercises=list(changed_exercises))
