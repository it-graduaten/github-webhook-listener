# pull official base image
FROM cicirello/pyaction:latest

# set work directory
WORKDIR /usr/src/app

RUN touch /usr/src/app/logs/celery.log

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy project
COPY . .
