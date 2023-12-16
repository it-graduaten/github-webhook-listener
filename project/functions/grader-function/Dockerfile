FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

# set work directory
WORKDIR /usr/src/app

RUN apt update 
RUN apt install wget git python3 pip -y 

COPY ./scripts/dotnet-installer.sh .

RUN bash ./dotnet-installer.sh

RUN python3 -m pip install --upgrade pip
RUN pip3 --no-cache-dir install --upgrade awscli
RUN python3 -m pip install virtualenv

COPY ./requirements.txt .

COPY lambda_function.py .
COPY src ./src
COPY grader-html-reports ./grader-html-reports

SHELL ["/bin/bash", "-c"]
WORKDIR .

RUN python3 -m virtualenv ENV
RUN source ./ENV/bin/activate && pip install -r requirements.txt && rm ./requirements.txt

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set the entrypoint to the shell script
ENTRYPOINT ["./entrypoint.sh"]