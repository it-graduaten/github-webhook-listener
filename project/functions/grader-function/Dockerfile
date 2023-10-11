FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

# set work directory
WORKDIR /usr/src/app

RUN apt update 
RUN apt install wget git python3 pip -y 

RUN wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb 
RUN dpkg -i packages-microsoft-prod.deb
RUN apt update 
RUN apt install dotnet-sdk-6.0 -y

RUN python3 -m pip install --upgrade pip
RUN pip3 --no-cache-dir install --upgrade awscli

COPY ./requirements.txt .
RUN pip install -r requirements.txt && rm ./requirements.txt

COPY lambda_function.py .
COPY src ./src

# TODO: Remove this line when using actual s3 bucket
COPY s3-mock ./s3-mock

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set the entrypoint to the shell script
ENTRYPOINT ["./entrypoint.sh"]