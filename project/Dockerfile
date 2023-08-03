# pull official base image
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

# set work directory
WORKDIR /usr/src/app

# create logs directory
RUN mkdir -p /usr/src/app/logs
RUN touch /usr/src/app/logs/celery.log

# Create the 'student-repos' directory
RUN mkdir -p /usr/src/app/student-repos
# Create the 'solution-repo' directory
RUN mkdir -p /usr/src/app/solution-repo

RUN apt update 
RUN apt install wget git python3 pip -y 

# Install dotnet
RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb 
RUN dpkg -i packages-microsoft-prod.deb
RUN apt update 
RUN apt install dotnet-sdk-3.1 -y

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN python3 -m pip install --upgrade pip
COPY ./requirements.txt .
RUN python3 -m pip install -r requirements.txt

# copy project
COPY . .
