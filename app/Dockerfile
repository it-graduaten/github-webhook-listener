FROM python:3.10.0-alpine
WORKDIR /code
EXPOSE 8000
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["uvicorn", "app.randomizer:app", "--host", "0.0.0.0", "--port", "8000"]