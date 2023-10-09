FROM public.ecr.aws/lambda/python:3.11

# Install dotnet
RUN rpm -Uvh https://packages.microsoft.com/config/centos/7/packages-microsoft-prod.rpm
RUN yum install dotnet-sdk-6.0 git -y && \
    yum clean all && \
    rm -rf /var/cache/yum

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt && rm ${LAMBDA_TASK_ROOT}/requirements.txt

COPY lambda_function.py ${LAMBDA_TASK_ROOT}
COPY src ${LAMBDA_TASK_ROOT}/src

# TODO: Remove this line when using actual s3 bucket
COPY s3-mock ${LAMBDA_TASK_ROOT}/s3-mock