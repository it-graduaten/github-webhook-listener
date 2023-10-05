from fastapi import FastAPI
from fastapi.responses import JSONResponse
from helpers import get_changed_files_in_push, get_config_for_endpoint

from custom_types import GithubPushPayload, WebhookResponse
from worker import fetch_solution_repo, run_tests_for_student

app = FastAPI()


@app.get('/')
async def root():
    return {"message": "Hello World"}


@app.get('/update-solutions', status_code=201)
async def update_solutions(solution_repo_name: str):
    task = fetch_solution_repo.delay(solution_repo_name)
    return JSONResponse({"task_id": task.id})


@app.post('/oop')
async def oop_root(payload: GithubPushPayload):
    # Get the repo name
    repo_name = payload.repository.name
    # Get all the changed files
    changed_exercises = get_changed_files_in_push(payload)
    # Get the correct config
    config = get_config_for_endpoint('object_oriented_programming')
    # Return output
    output = f"Received push event from {repo_name}"
    task = run_tests_for_student.delay(repo_name, list(changed_exercises), config)
    return WebhookResponse(task_id=task.id, message=output, changed_exercises=list(changed_exercises))
