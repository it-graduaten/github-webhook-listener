# TM Autograder

Code for the TM Autograder application.

The grader function is a python script which polls the SQS queue for new messages.
Whenever a new message is received, the function will download the student's code from GitHub and perform the grading.

## Requirements

- An AWS environment where several components are set up
- Docker
- Docker Compose
- An environment file with the correct credentials

### Environment file

| Variable name               | Explanation                                                               | Example value                                         |
|-----------------------------|---------------------------------------------------------------------------|-------------------------------------------------------|
| APP_ENVIRONMENT             | The environment in which the app should be run. Should be 'dev' or 'prod' | dev                                                   |
| BOTO_SESSION_ENDPOINT       | The AWS endpoint that should be used                                      | your_endpoint.credentials.iot.us-west-2.amazonaws.com |
| BOTO_SESSION_ROLE_ALIAS     | AWS iot role alias name                                                   | your_aws_iot_role_alias_name                          |
| BOTO_SESSION_CERTIFICATE    | AWS iot thing certificate                                                 | iot_thing.pem                                         |
| BOTO_SESSION_PRIVATE_KEY    | AWS iot thing certificate private key                                     | iot_thing.pem.key                                     |
| BOTO_SESSION_THING_NAME     | AWS iot thing name                                                        | iot-thing                                             |
| PARAMETER_STORE_SECRET_NAME | AWS Parameter Store name                                                  | /secrets                                              |

## Running the grader function

To run the grader function, execute the following command:

```sh
$ docker-compose --env-file /path/to/file up --build
```

## Deploying to AWS
### Get creds

Create a folder in your project with the necessary certs for a IoT device to get temporary credentials:

```sh
mkdir -p ./.aws-config/certs
```

Place your device certificates in this folder to be able to execute the lambda function.

### Deploy to a specific environment

```sh
sam deploy --config-env [prod|dev]
```

Pick prod or dev depending on the deployment you want to make, dev is the default environment! Make sure to incorporate the prefix in your resource names, and if not possible add a specific resource name to the mappings.