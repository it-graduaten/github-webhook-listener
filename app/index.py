from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel
import logging

logging.basicConfig(filename='record.log', level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s')

logger = logging.getLogger(__name__)

app = FastAPI()


class GithubPushPayload(BaseModel):
    commits: list = []


@app.get('/')
async def root():
    return 'Hello World!'


@app.post('/oop')
async def oop_root(payload: GithubPushPayload, background_tasks: BackgroundTasks):
    output = ["Received push event from OOP repository"]
    
    logger.info('Received push event from OOP repository')
    return output
