def build_grader_image_cmd():
    return 'cd ./functions/grader-function && docker build . -t graderimagefunction:v1'

def pull_python_aws_runtime():
    return 'docker pull public.ecr.aws/sam/build-python3.11:latest-x86_64'
    
    
def task_start_api():
    """Build the container and start the api"""
    yield {
        'name': 'start_api',
        'actions': [
            build_grader_image_cmd(),
            'docker pull public.ecr.aws/sam/build-python3.11:latest-x86_64'
            ' && sam build --use-container --cached'
            ' && sam local start-api -p 3030'    
        ]
    }
    
def task_invoke_grader():
    """Invokes the grader function with a test event"""
    yield {
        'name': 'invoke_grader',
        'actions': [
            pull_python_aws_runtime(),
            build_grader_image_cmd(),
            "sam build --use-container --cached",
            'sam local invoke --env-vars ./env.json GraderImageFunction -e ./events/grade-student-project.json'
        ]
    }
    
def task_deploy_to_aws():
    """Deploy the stack to AWS"""
    yield {
        'name': 'deploy_to_aws',
        'actions': [
            'sam build --use-container --cached && sam deploy --config-env dev'
        ]
    }