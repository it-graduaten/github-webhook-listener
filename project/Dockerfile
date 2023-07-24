# pull official base image
FROM cicirello/pyaction:latest

# set work directory
WORKDIR /usr/src/app

# create logs directory
RUN mkdir -p /usr/src/app/logs
RUN touch /usr/src/app/logs/celery.log

# Create the 'student-repos' directory
RUN mkdir -p /usr/src/app/student-repos
# Create the 'solution-repo' directory
RUN mkdir -p /usr/src/app/solution-repo

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
