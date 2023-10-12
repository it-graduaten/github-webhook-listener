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

COPY ./requirements.txt .
RUN pip install -r requirements.txt && rm ./requirements.txt

COPY lambda_function.py .
COPY src ./src

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set the entrypoint to the shell script
ENTRYPOINT ["./entrypoint.sh"]