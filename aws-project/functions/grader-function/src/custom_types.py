from pydantic import BaseModel
from typing import TypedDict

ClassroomRoster = TypedDict('ClassroomRoster', {'identifier': str, 'github_username': str, 'github_id': str, 'name': str})

TestRunResult = TypedDict('TestRunResult', {'assignment': str, 'total': int, 'errors': int, 'grade': float, 'run_at_utc_datetime': str, 'should_update_canvas': bool})

class Repository(BaseModel):
    name: str

class GithubCommit(BaseModel):
    added: list = []
    modified: list = []
    removed: list = []

class GithubPushPayload(BaseModel):
    commits: list = []
    repository: Repository

class WebhookResponse(BaseModel):
    message: str = "Received push event from OOP repository"
    changed_exercises: list = []
    task_id: str = None