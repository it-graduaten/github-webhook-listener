from pydantic import BaseModel

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