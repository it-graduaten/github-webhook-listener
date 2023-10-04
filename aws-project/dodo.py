def build_grader_image_cmd():
    return 'cd ./functions/grader-function && docker build . -t local-grader'
    
def task_start_api():
    """Build the container and start the api"""
    yield {
        'name': 'start_api',
        'actions': [
            build_grader_image_cmd(),
            'docker pull public.ecr.aws/sam/build-python3.11:latest-x86_64'
            'sam build --use-container --cached'
            'sam local start-api -p 3030'    
        ]
    }
    
def task_invoke_grader():
    """Invokes the grader function with a test event"""
    yield {
        'name': 'invoke_grader',
        'actions': [
            build_grader_image_cmd(),
            'sam local invoke GraderFunction -e ./events/grade-student-project.json'
        ]
    }