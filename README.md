# Asynchronous Tasks with FastAPI and Celery

Example of how to handle background processes with FastAPI, Celery, and Docker.

### Quick Start

Spin up the containers:

```sh
$ docker-compose up -d --build
```

Open your browser to [http://localhost:8004](http://localhost:8004)


# Get creds

Create a folder in your project with the necessary certs for a IoT device to get temporary credentials:

```sh
mkdir -p ./.aws-config/certs
```

Place your device certificates in this folder to be able to execute the lambda function.

## Deploy to a specific environment

```sh
sam deploy --config-env [prod|dev]
```

Pick prod or dev depending on the deployment you want to make, dev is the default environment! Make sure to incorporate the prefix in your resource names, and if not possible add a specific resource name to the mappings.
