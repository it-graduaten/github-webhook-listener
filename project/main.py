from fastapi import Body, FastAPI, Form, Request
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
import re

from custom_types import GithubPushPayload, WebhookResponse
from worker import fetch_solution_repo, run_tests_for_student


app = FastAPI()

@app.get('/')
async def root():
    return {"message": "Hello World"}

@app.get('/update-solutions', status_code=201)
async def update_solutions():
    task = fetch_solution_repo.delay()
    return JSONResponse({"task_id": task.id})

@app.post('/oop')
async def oop_root(payload: GithubPushPayload):
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

    task = run_tests_for_student.delay(repo_name, list(changed_exercises))

    return WebhookResponse(task_id=task.id, message=output, changed_exercises=list(changed_exercises))
