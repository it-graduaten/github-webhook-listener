FROM python:3.10.0-alpine
WORKDIR /code/app
EXPOSE 8000
COPY ./requirements.txt /code/requirements.txt
RUN wget https://github.com/libgit2/libgit2/archive/v0.25.0.tar.gz && \
tar xzf v0.25.0.tar.gz && \
cd libgit2-0.25.0/ && \
cmake . && \
make && \
make install
RUN pip install --no-cache-dir --upgrade pip \
  && pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY ./app /code/app
CMD ["uvicorn", "index:app", "--host", "0.0.0.0", "--port", "8000"]